"""Portfolio impact analysis agent for WS Pulse.

Analyzes how a financial event affects a specific user's portfolio,
computing exposure, concentration risk, tax implications, and
personalized metrics.
"""

from __future__ import annotations

import time
from typing import Any

from src.pulse.models import (
    EventType, MarketEvent, Portfolio,
)
from src.shared.latency import latency_tracker


def analyze_portfolio_impact(
    event: MarketEvent,
    portfolio: Portfolio,
    detection_context: dict[str, Any],
) -> dict[str, Any]:
    """Analyze how a specific event impacts a user's portfolio."""

    start = time.perf_counter()
    user_id = portfolio.user_id
    relevance = detection_context.get("user_relevance", {}).get(user_id, {})

    analysis: dict[str, Any] = {
        "user_id": user_id,
        "event_id": event.event_id,
        "event_type": event.event_type.value,
        "portfolio_total_cad": portfolio.total_value,
        "impact": {},
        "context": {},
        "risk_factors": [],
    }

    if event.event_type == EventType.PAYCHECK:
        analysis["impact"] = _analyze_paycheck(portfolio, event.data)

    elif event.event_type == EventType.EARNINGS_REPORT:
        analysis["impact"] = _analyze_earnings(portfolio, event, relevance)

    elif event.event_type == EventType.MARKET_DROP:
        analysis["impact"] = _analyze_market_drop(portfolio, event, relevance)

    elif event.event_type == EventType.BOC_RATE_DECISION:
        analysis["impact"] = _analyze_rate_decision(portfolio, event, relevance)

    elif event.event_type == EventType.DIVIDEND_PAYMENT:
        analysis["impact"] = _analyze_dividend(portfolio, event, relevance)

    else:
        analysis["impact"] = {"type": "informational", "action_needed": False}

    analysis["context"] = {
        "asset_allocation": portfolio.asset_allocation,
        "concentration_risks": portfolio.concentration_risk,
        "sector_allocation": portfolio.sector_allocation,
        "risk_profile": portfolio.goals.risk_profile.value,
        "tax_bracket_pct": portfolio.goals.tax_bracket_pct,
        "has_premium": portfolio.goals.has_premium,
    }

    conc = portfolio.concentration_risk
    if conc:
        analysis["risk_factors"].append(
            f"Concentration risk: {conc[0]['ticker']} at {conc[0]['weight_pct']}% of portfolio"
        )

    emergency_gap = max(0, portfolio.goals.emergency_fund_target - portfolio.goals.emergency_fund_current)
    if emergency_gap > 0:
        analysis["risk_factors"].append(
            f"Emergency fund gap: ${emergency_gap:,.0f} below target"
        )

    duration_ms = (time.perf_counter() - start) * 1000
    latency_tracker.record("portfolio_analysis", duration_ms)
    analysis["analysis_time_ms"] = round(duration_ms, 3)

    return analysis


def _analyze_paycheck(portfolio: Portfolio, event_data: dict) -> dict[str, Any]:
    amount = event_data.get("amount", 0)
    goals = portfolio.goals

    emergency_gap = max(0, goals.emergency_fund_target - goals.emergency_fund_current)
    savings_budget = min(amount, goals.monthly_savings_target) if goals.monthly_savings_target > 0 else amount * 0.2

    allocation = {}

    if emergency_gap > 0:
        emergency_amount = min(savings_budget * 0.5, emergency_gap)
        allocation["emergency_fund"] = round(emergency_amount, 2)
        savings_budget -= emergency_amount

    rrsp_accounts = [a for a in portfolio.accounts if a.account_type.value == "rrsp"]
    has_match = any(a.employer_match_pct and a.employer_match_pct > 0 for a in rrsp_accounts)
    if has_match and savings_budget > 0:
        match_pct = max(a.employer_match_pct or 0 for a in rrsp_accounts)
        rrsp_amount = min(savings_budget * 0.4, amount * match_pct / 100)
        allocation["rrsp_employer_match"] = round(rrsp_amount, 2)
        allocation["rrsp_match_pct"] = match_pct
        savings_budget -= rrsp_amount

    if goals.tax_bracket_pct > 30 and savings_budget > 0:
        rrsp_rooms = [a.contribution_room for a in rrsp_accounts if a.contribution_room and a.contribution_room > 0]
        if rrsp_rooms:
            rrsp_extra = min(savings_budget * 0.3, max(rrsp_rooms))
            allocation["rrsp_tax_optimization"] = round(rrsp_extra, 2)
            allocation["tax_savings_estimate"] = round(rrsp_extra * goals.tax_bracket_pct / 100, 2)
            savings_budget -= rrsp_extra

    tfsa_accounts = [a for a in portfolio.accounts if a.account_type.value == "tfsa"]
    tfsa_room = sum(a.contribution_room or 0 for a in tfsa_accounts)
    if tfsa_room > 0 and savings_budget > 0:
        tfsa_amount = min(savings_budget, tfsa_room)
        allocation["tfsa"] = round(tfsa_amount, 2)
        allocation["tfsa_room_remaining"] = round(tfsa_room - tfsa_amount, 2)
        savings_budget -= tfsa_amount

    fhsa_accounts = [a for a in portfolio.accounts if a.account_type.value == "fhsa"]
    fhsa_room = sum(a.contribution_room or 0 for a in fhsa_accounts)
    if fhsa_room > 0 and savings_budget > 0:
        fhsa_amount = min(savings_budget, fhsa_room)
        allocation["fhsa"] = round(fhsa_amount, 2)
        savings_budget -= fhsa_amount

    allocation["total_allocated"] = round(sum(v for k, v in allocation.items() if isinstance(v, (int, float)) and not k.endswith("_pct") and not k.endswith("remaining") and not k.endswith("estimate")), 2)
    allocation["paycheck_amount"] = amount
    allocation["savings_rate_pct"] = round(allocation["total_allocated"] / amount * 100, 2) if amount > 0 else 0

    return allocation


def _analyze_earnings(portfolio: Portfolio, event: MarketEvent, relevance: dict) -> dict[str, Any]:
    surprise_pct = event.data.get("surprise_pct", 0)
    held_tickers = relevance.get("held_tickers", event.affected_tickers)
    exposure = relevance.get("exposure_cad", 0)
    weight = relevance.get("portfolio_weight_pct", 0)

    impact: dict[str, Any] = {
        "held_tickers": held_tickers,
        "exposure_cad": exposure,
        "portfolio_weight_pct": weight,
        "earnings_surprise_pct": surprise_pct,
    }

    if surprise_pct > 0:
        estimated_move = round(surprise_pct * 0.3, 2)
        impact["estimated_price_move_pct"] = estimated_move
        impact["estimated_gain_cad"] = round(exposure * estimated_move / 100, 2)
        impact["sentiment"] = "positive"
    else:
        estimated_move = round(surprise_pct * 0.4, 2)
        impact["estimated_price_move_pct"] = estimated_move
        impact["estimated_loss_cad"] = round(abs(exposure * estimated_move / 100), 2)
        impact["sentiment"] = "negative"

    if weight > 20:
        impact["concentration_warning"] = True
        impact["rebalance_suggested"] = True
    else:
        impact["concentration_warning"] = False
        impact["rebalance_suggested"] = False

    return impact


def _analyze_market_drop(portfolio: Portfolio, event: MarketEvent, relevance: dict) -> dict[str, Any]:
    drop_pct = abs(event.data.get("drop_pct", 0))
    exposure = relevance.get("exposure_cad", 0)
    impact_cad = relevance.get("estimated_impact_cad", 0)
    weight = relevance.get("portfolio_weight_pct", 0)

    impact: dict[str, Any] = {
        "exposure_cad": exposure,
        "estimated_impact_cad": abs(impact_cad),
        "portfolio_weight_pct": weight,
        "drop_pct": -drop_pct,
        "affected_holdings": [],
    }

    for h in portfolio.all_holdings:
        if h.ticker in event.affected_tickers:
            holding_impact = round(h.market_value * drop_pct / 100, 2)
            impact["affected_holdings"].append({
                "ticker": h.ticker,
                "name": h.name,
                "market_value": h.market_value,
                "estimated_loss_cad": holding_impact,
                "unrealized_gain_pct": h.unrealized_gain_pct,
            })

    goals = portfolio.goals
    if goals.risk_profile.value in ("aggressive", "growth"):
        cash = sum(a.cash_balance for a in portfolio.accounts)
        impact["buy_opportunity"] = cash > 500
        impact["available_cash"] = round(cash, 2)
    else:
        impact["buy_opportunity"] = False

    tax_loss_candidates = [
        ah for ah in impact["affected_holdings"]
        if ah.get("unrealized_gain_pct", 0) < -5
    ]
    impact["tax_loss_harvest_candidates"] = tax_loss_candidates

    total = portfolio.total_value
    if total > 0:
        portfolio_impact_pct = abs(impact_cad) / total * 100
        impact["portfolio_impact_pct"] = round(portfolio_impact_pct, 2)
    else:
        impact["portfolio_impact_pct"] = 0

    return impact


def _analyze_rate_decision(portfolio: Portfolio, event: MarketEvent, relevance: dict) -> dict[str, Any]:
    change_bps = event.data.get("change_bps", 0)
    bond_exposure = relevance.get("bond_exposure_cad", 0)
    bond_weight = relevance.get("bond_weight_pct", 0)

    impact: dict[str, Any] = {
        "rate_change_bps": change_bps,
        "bond_exposure_cad": bond_exposure,
        "bond_weight_pct": bond_weight,
    }

    if change_bps < 0:
        duration_estimate = 6.5
        price_change_pct = round(-change_bps / 100 * duration_estimate, 2)
        impact["estimated_bond_gain_pct"] = price_change_pct
        impact["estimated_bond_gain_cad"] = round(bond_exposure * price_change_pct / 100, 2)
        impact["mortgage_impact"] = "Potential savings on variable rate"
        impact["savings_rate_impact"] = "Lower returns on cash/GICs"
    elif change_bps > 0:
        duration_estimate = 6.5
        price_change_pct = round(-change_bps / 100 * duration_estimate, 2)
        impact["estimated_bond_loss_pct"] = abs(price_change_pct)
        impact["estimated_bond_loss_cad"] = round(abs(bond_exposure * price_change_pct / 100), 2)
        impact["savings_rate_impact"] = "Higher returns on cash/GICs"
    else:
        impact["status"] = "no_change"
        impact["market_expectation"] = "Rates held as expected"

    return impact


def _analyze_dividend(portfolio: Portfolio, event: MarketEvent, relevance: dict) -> dict[str, Any]:
    return {
        "dividend_amount_cad": relevance.get("dividend_amount_cad", 0),
        "shares_held": relevance.get("shares_held", 0),
        "yield_pct": relevance.get("yield_pct", 0),
        "tax_treatment": "eligible_dividend",
        "reinvestment_suggested": True,
    }
