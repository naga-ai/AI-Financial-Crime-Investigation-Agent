"""Recommendation engine for WS Pulse.

Generates personalized, actionable recommendations based on event
classification, portfolio impact analysis, and RAG-retrieved
financial guidance. Produces plain-language narratives.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any

from src.pulse.models import (
    EventPriority, EventType, Portfolio,
    Recommendation, RecommendationAction,
)
from src.shared.latency import latency_tracker


def generate_recommendation(
    event_type: EventType,
    portfolio: Portfolio,
    impact_analysis: dict[str, Any],
    rag_context: dict[str, Any] | None = None,
    event_id: str = "",
) -> Recommendation:
    """Generate a personalized recommendation based on event and portfolio context."""

    start = time.perf_counter()

    if event_type == EventType.PAYCHECK:
        rec = _recommend_paycheck(portfolio, impact_analysis, rag_context)
    elif event_type == EventType.EARNINGS_REPORT:
        rec = _recommend_earnings(portfolio, impact_analysis, rag_context)
    elif event_type == EventType.MARKET_DROP:
        rec = _recommend_market_drop(portfolio, impact_analysis, rag_context)
    elif event_type == EventType.BOC_RATE_DECISION:
        rec = _recommend_rate_decision(portfolio, impact_analysis, rag_context)
    elif event_type == EventType.DIVIDEND_PAYMENT:
        rec = _recommend_dividend(portfolio, impact_analysis, rag_context)
    else:
        rec = _recommend_generic(portfolio, impact_analysis)

    rec.recommendation_id = f"REC-{uuid.uuid4().hex[:10]}"
    rec.user_id = portfolio.user_id
    rec.event_id = event_id
    rec.event_type = event_type
    rec.created_at = datetime.utcnow()

    duration_ms = (time.perf_counter() - start) * 1000
    latency_tracker.record("recommendation", duration_ms)

    return rec


def _recommend_paycheck(
    portfolio: Portfolio,
    impact: dict[str, Any],
    rag_context: dict[str, Any] | None,
) -> Recommendation:
    alloc = impact.get("impact", impact)
    amount = alloc.get("paycheck_amount", 0)
    goals = portfolio.goals

    emergency_gap = max(0, goals.emergency_fund_target - goals.emergency_fund_current)
    reasoning = []
    action = RecommendationAction.ALLOCATE_TFSA
    estimated_value = 0.0

    if emergency_gap > 0:
        emergency_alloc = alloc.get("emergency_fund", 0)
        reasoning.append(
            f"Your emergency fund is ${emergency_gap:,.0f} below your ${goals.emergency_fund_target:,.0f} target. "
            f"Allocating ${emergency_alloc:,.0f} to close this gap first."
        )
        action = RecommendationAction.BUILD_EMERGENCY
        estimated_value = emergency_alloc

    rrsp_match = alloc.get("rrsp_employer_match", 0)
    if rrsp_match > 0:
        match_pct = alloc.get("rrsp_match_pct", 0)
        reasoning.append(
            f"Your employer matches {match_pct}% of RRSP contributions -- that's free money. "
            f"Contributing ${rrsp_match:,.0f} captures the full match."
        )
        if not emergency_gap:
            action = RecommendationAction.ALLOCATE_RRSP
            estimated_value = rrsp_match * 2

    tax_opt = alloc.get("rrsp_tax_optimization", 0)
    if tax_opt > 0:
        tax_savings = alloc.get("tax_savings_estimate", 0)
        reasoning.append(
            f"At your {goals.tax_bracket_pct}% marginal rate, an additional ${tax_opt:,.0f} RRSP "
            f"contribution saves ~${tax_savings:,.0f} in taxes this year."
        )
        estimated_value += tax_savings

    tfsa_alloc = alloc.get("tfsa", 0)
    if tfsa_alloc > 0:
        tfsa_room = alloc.get("tfsa_room_remaining", 0)
        reasoning.append(
            f"Allocating ${tfsa_alloc:,.0f} to your TFSA. "
            f"${tfsa_room:,.0f} contribution room remaining for the year."
        )
        if not emergency_gap and not rrsp_match:
            action = RecommendationAction.ALLOCATE_TFSA
            estimated_value += tfsa_alloc * 0.05

    savings_rate = alloc.get("savings_rate_pct", 0)
    total_allocated = alloc.get("total_allocated", 0)

    rag_note = ""
    if rag_context and rag_context.get("results"):
        rag_note = " (based on current CRA contribution limits and tax guidance)"

    narrative = (
        f"Your ${amount:,.0f} paycheck just landed. Here's the optimal split:\n\n"
    )
    if alloc.get("emergency_fund"):
        narrative += f"- **Emergency fund**: ${alloc['emergency_fund']:,.0f}\n"
    if rrsp_match > 0:
        narrative += f"- **RRSP (employer match)**: ${rrsp_match:,.0f}\n"
    if tax_opt > 0:
        narrative += f"- **RRSP (tax optimization)**: ${tax_opt:,.0f}\n"
    if tfsa_alloc > 0:
        narrative += f"- **TFSA**: ${tfsa_alloc:,.0f}\n"
    if alloc.get("fhsa"):
        narrative += f"- **FHSA**: ${alloc['fhsa']:,.0f}\n"
    narrative += (
        f"\nTotal saved: ${total_allocated:,.0f} ({savings_rate:.0f}% of paycheck){rag_note}"
    )

    return Recommendation(
        recommendation_id="",
        user_id="",
        event_id="",
        event_type=EventType.PAYCHECK,
        action=action,
        priority=EventPriority.LOW,
        title=f"Smart allocation for your ${amount:,.0f} paycheck",
        narrative=narrative,
        reasoning=reasoning,
        impact_summary=f"${total_allocated:,.0f} optimally allocated across accounts",
        confidence=0.88,
        estimated_value_cad=round(estimated_value, 2),
    )


def _recommend_earnings(
    portfolio: Portfolio,
    impact: dict[str, Any],
    rag_context: dict[str, Any] | None,
) -> Recommendation:
    imp = impact.get("impact", impact)
    surprise = imp.get("earnings_surprise_pct", 0)
    tickers = imp.get("held_tickers", [])
    weight = imp.get("portfolio_weight_pct", 0)
    sentiment = imp.get("sentiment", "neutral")

    reasoning = []

    if sentiment == "positive":
        gain = imp.get("estimated_gain_cad", 0)
        reasoning.append(
            f"Earnings beat by {surprise:.1f}%. Estimated price impact: "
            f"+{imp.get('estimated_price_move_pct', 0):.1f}% (${gain:,.0f} on your position)."
        )
    else:
        loss = imp.get("estimated_loss_cad", 0)
        reasoning.append(
            f"Earnings missed by {abs(surprise):.1f}%. Estimated price impact: "
            f"{imp.get('estimated_price_move_pct', 0):.1f}% (-${loss:,.0f} on your position)."
        )

    action = RecommendationAction.HOLD
    if imp.get("rebalance_suggested"):
        action = RecommendationAction.REVIEW_CONCENTRATION
        reasoning.append(
            f"{', '.join(tickers)} is {weight:.1f}% of your portfolio -- above the 20% concentration threshold. "
            f"Consider rebalancing."
        )
    elif sentiment == "positive" and weight > 15:
        action = RecommendationAction.TAKE_PROFIT
        reasoning.append(
            f"Strong earnings with {weight:.1f}% portfolio concentration. "
            f"Consider taking partial profits to manage concentration risk."
        )

    ticker_str = ", ".join(tickers) if tickers else "your holdings"
    narrative = (
        f"**Earnings {'beat' if surprise > 0 else 'miss'} for {ticker_str}**\n\n"
        f"{'Strong' if surprise > 0 else 'Weaker'} results: EPS surprise of "
        f"{'+' if surprise > 0 else ''}{surprise:.1f}%. "
        f"Your exposure is ${imp.get('exposure_cad', 0):,.0f} ({weight:.1f}% of portfolio).\n\n"
        f"**Recommendation**: {action.value.replace('_', ' ').title()}"
    )

    return Recommendation(
        recommendation_id="",
        user_id="",
        event_id="",
        event_type=EventType.EARNINGS_REPORT,
        action=action,
        priority=EventPriority.MEDIUM,
        title=f"Earnings {'beat' if surprise > 0 else 'miss'}: {ticker_str}",
        narrative=narrative,
        reasoning=reasoning,
        impact_summary=f"{'Positive' if surprise > 0 else 'Negative'} earnings impact on {weight:.1f}% of portfolio",
        confidence=0.82 if abs(surprise) > 5 else 0.70,
        estimated_value_cad=abs(imp.get("estimated_gain_cad", imp.get("estimated_loss_cad", 0))),
    )


def _recommend_market_drop(
    portfolio: Portfolio,
    impact: dict[str, Any],
    rag_context: dict[str, Any] | None,
) -> Recommendation:
    imp = impact.get("impact", impact)
    drop_pct = abs(imp.get("drop_pct", 0))
    impact_cad = imp.get("estimated_impact_cad", 0)
    portfolio_impact = imp.get("portfolio_impact_pct", 0)
    buy_opportunity = imp.get("buy_opportunity", False)
    available_cash = imp.get("available_cash", 0)
    tax_loss = imp.get("tax_loss_harvest_candidates", [])

    reasoning = []
    action = RecommendationAction.HOLD

    reasoning.append(
        f"Market declined {drop_pct:.1f}%. Estimated portfolio impact: "
        f"-${impact_cad:,.0f} ({portfolio_impact:.1f}% of your portfolio)."
    )

    if portfolio.goals.risk_profile.value in ("aggressive", "growth") and buy_opportunity:
        action = RecommendationAction.BUY_DIP
        reasoning.append(
            f"Given your {portfolio.goals.risk_profile.value} risk profile and "
            f"${available_cash:,.0f} available cash, this could be a buying opportunity."
        )

    if tax_loss:
        action = RecommendationAction.TAX_LOSS_HARVEST
        tickers = [t["ticker"] for t in tax_loss]
        reasoning.append(
            f"Tax-loss harvest candidates: {', '.join(tickers)}. "
            f"Selling at a loss offsets capital gains at your {portfolio.goals.tax_bracket_pct}% rate."
        )

    affected = imp.get("affected_holdings", [])
    holdings_text = ""
    if affected:
        holdings_text = "\n".join(
            f"- **{h['ticker']}**: -${h['estimated_loss_cad']:,.0f} "
            f"(now {'up' if h['unrealized_gain_pct'] > 0 else 'down'} {abs(h['unrealized_gain_pct']):.1f}% overall)"
            for h in affected[:5]
        )

    narrative = (
        f"**Market pullback: -{drop_pct:.1f}%**\n\n"
        f"Your portfolio impact: -${impact_cad:,.0f} ({portfolio_impact:.1f}%)\n\n"
    )
    if holdings_text:
        narrative += f"**Affected holdings:**\n{holdings_text}\n\n"
    narrative += f"**Recommendation**: {action.value.replace('_', ' ').title()}"

    return Recommendation(
        recommendation_id="",
        user_id="",
        event_id="",
        event_type=EventType.MARKET_DROP,
        action=action,
        priority=EventPriority.HIGH,
        title=f"Market drop: your portfolio impact is -${impact_cad:,.0f}",
        narrative=narrative,
        reasoning=reasoning,
        impact_summary=f"-${impact_cad:,.0f} estimated impact ({portfolio_impact:.1f}% of portfolio)",
        confidence=0.78,
        estimated_value_cad=round(impact_cad, 2),
    )


def _recommend_rate_decision(
    portfolio: Portfolio,
    impact: dict[str, Any],
    rag_context: dict[str, Any] | None,
) -> Recommendation:
    imp = impact.get("impact", impact)
    change_bps = imp.get("rate_change_bps", 0)
    bond_exposure = imp.get("bond_exposure_cad", 0)
    bond_weight = imp.get("bond_weight_pct", 0)

    reasoning = []
    action = RecommendationAction.HOLD

    if change_bps < 0:
        gain = imp.get("estimated_bond_gain_cad", 0)
        reasoning.append(
            f"Rate cut of {abs(change_bps)}bps. Your bond holdings ({bond_weight:.1f}% of portfolio) "
            f"should gain ~${gain:,.0f}."
        )
        if bond_weight < 20:
            action = RecommendationAction.REBALANCE
            reasoning.append("Consider increasing bond allocation to benefit from the rate cycle.")
    elif change_bps > 0:
        loss = imp.get("estimated_bond_loss_cad", 0)
        reasoning.append(
            f"Rate hike of {change_bps}bps. Your bond holdings may lose ~${loss:,.0f}."
        )
    else:
        reasoning.append("Rates held steady. No immediate action needed.")

    narrative = (
        f"**BoC Rate {'Cut' if change_bps < 0 else 'Hike' if change_bps > 0 else 'Hold'}**\n\n"
        f"Rate {'decreased' if change_bps < 0 else 'increased' if change_bps > 0 else 'unchanged'} "
        f"by {abs(change_bps)}bps. Your bond exposure: ${bond_exposure:,.0f} ({bond_weight:.1f}%)."
    )

    return Recommendation(
        recommendation_id="",
        user_id="",
        event_id="",
        event_type=EventType.BOC_RATE_DECISION,
        action=action,
        priority=EventPriority.MEDIUM if change_bps != 0 else EventPriority.LOW,
        title=f"BoC rate {'cut' if change_bps < 0 else 'hike' if change_bps > 0 else 'hold'}: impact on your bonds",
        narrative=narrative,
        reasoning=reasoning,
        impact_summary=f"Bond portfolio impact from {abs(change_bps)}bps rate change",
        confidence=0.85,
        estimated_value_cad=abs(imp.get("estimated_bond_gain_cad", imp.get("estimated_bond_loss_cad", 0))),
    )


def _recommend_dividend(
    portfolio: Portfolio,
    impact: dict[str, Any],
    rag_context: dict[str, Any] | None,
) -> Recommendation:
    imp = impact.get("impact", impact)
    div_amount = imp.get("dividend_amount_cad", 0)
    yield_pct = imp.get("yield_pct", 0)

    reasoning = [
        f"Dividend of ${div_amount:,.2f} received (yield: {yield_pct}%).",
        "Eligible Canadian dividends receive preferential tax treatment via the dividend tax credit.",
    ]
    if imp.get("reinvestment_suggested"):
        reasoning.append("Reinvesting dividends compounds returns over time (DRIP).")

    return Recommendation(
        recommendation_id="",
        user_id="",
        event_id="",
        event_type=EventType.DIVIDEND_PAYMENT,
        action=RecommendationAction.INCREASE_CONTRIBUTION,
        priority=EventPriority.LOW,
        title=f"Dividend received: ${div_amount:,.2f}",
        narrative=(
            f"You received a ${div_amount:,.2f} dividend ({yield_pct}% yield). "
            f"Consider enabling DRIP to automatically reinvest dividends."
        ),
        reasoning=reasoning,
        impact_summary=f"${div_amount:,.2f} dividend income",
        confidence=0.92,
        estimated_value_cad=round(div_amount, 2),
    )


def _recommend_generic(
    portfolio: Portfolio,
    impact: dict[str, Any],
) -> Recommendation:
    return Recommendation(
        recommendation_id="",
        user_id="",
        event_id="",
        event_type=EventType.SUBSCRIPTION_AUDIT,
        action=RecommendationAction.HOLD,
        priority=EventPriority.LOW,
        title="Portfolio check-in",
        narrative="No immediate action needed. Your portfolio is on track.",
        reasoning=["Routine portfolio health check."],
        impact_summary="Informational -- no action required",
        confidence=0.70,
    )
