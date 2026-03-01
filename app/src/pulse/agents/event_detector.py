"""Event detection and classification agent for WS Pilot.

Classifies incoming financial events into types, assigns priority levels,
and determines which users are affected based on their portfolio holdings.
"""

from __future__ import annotations

import time
from typing import Any

from src.pulse.models import (
    EventPriority, EventType, MarketEvent, Portfolio,
)
from src.shared.latency import latency_tracker


def detect_and_classify(
    event: MarketEvent,
    portfolios: dict[str, Portfolio],
) -> dict[str, Any]:
    """Classify event and compute per-user relevance scores."""

    start = time.perf_counter()

    result = {
        "event_id": event.event_id,
        "event_type": event.event_type.value,
        "priority": event.priority.value,
        "classification_confidence": 0.0,
        "affected_users": [],
        "user_relevance": {},
    }

    if event.event_type == EventType.PAYCHECK:
        result["classification_confidence"] = 0.95
        amount = event.data.get("amount", 0)
        for uid in event.affected_users:
            portfolio = portfolios.get(uid)
            if not portfolio:
                continue
            goals = portfolio.goals
            relevance = _paycheck_relevance(amount, goals.monthly_savings_target, goals.emergency_fund_current, goals.emergency_fund_target)
            result["user_relevance"][uid] = {
                "relevance_score": relevance,
                "has_tfsa_room": any(
                    a.contribution_room and a.contribution_room > 0
                    for a in portfolio.accounts
                    if a.account_type.value == "tfsa"
                ),
                "has_rrsp_room": any(
                    a.contribution_room and a.contribution_room > 0
                    for a in portfolio.accounts
                    if a.account_type.value == "rrsp"
                ),
                "emergency_fund_gap": max(0, goals.emergency_fund_target - goals.emergency_fund_current),
                "employer_match": any(
                    a.employer_match_pct and a.employer_match_pct > 0
                    for a in portfolio.accounts
                ),
            }
            result["affected_users"].append(uid)

    elif event.event_type == EventType.EARNINGS_REPORT:
        surprise = abs(event.data.get("surprise_pct", 0))
        result["classification_confidence"] = min(0.95, 0.7 + surprise / 100)
        if surprise > 15:
            result["priority"] = EventPriority.HIGH.value

        for uid in event.affected_users:
            portfolio = portfolios.get(uid)
            if not portfolio:
                continue
            held_tickers = set(h.ticker for h in portfolio.all_holdings)
            overlap = set(event.affected_tickers) & held_tickers
            if overlap:
                total_exposure = sum(
                    h.market_value for h in portfolio.all_holdings
                    if h.ticker in overlap
                )
                weight = total_exposure / portfolio.total_value * 100 if portfolio.total_value > 0 else 0
                result["user_relevance"][uid] = {
                    "relevance_score": min(1.0, weight / 20 + surprise / 50),
                    "held_tickers": list(overlap),
                    "exposure_cad": round(total_exposure, 2),
                    "portfolio_weight_pct": round(weight, 2),
                    "surprise_pct": event.data.get("surprise_pct", 0),
                }
                result["affected_users"].append(uid)

    elif event.event_type == EventType.MARKET_DROP:
        drop = abs(event.data.get("drop_pct", 0))
        result["classification_confidence"] = 0.92
        result["priority"] = EventPriority.HIGH.value if drop > 3 else EventPriority.MEDIUM.value

        for uid, portfolio in portfolios.items():
            held_tickers = set(h.ticker for h in portfolio.all_holdings)
            overlap = set(event.affected_tickers) & held_tickers
            if overlap:
                total_exposure = sum(
                    h.market_value for h in portfolio.all_holdings
                    if h.ticker in overlap
                )
                impact_cad = round(total_exposure * drop / 100, 2)
                weight = total_exposure / portfolio.total_value * 100 if portfolio.total_value > 0 else 0
                result["user_relevance"][uid] = {
                    "relevance_score": min(1.0, weight / 30 + drop / 10),
                    "held_tickers": list(overlap),
                    "exposure_cad": round(total_exposure, 2),
                    "estimated_impact_cad": impact_cad,
                    "portfolio_weight_pct": round(weight, 2),
                    "drop_pct": -drop,
                }
                result["affected_users"].append(uid)

    elif event.event_type == EventType.DIVIDEND_PAYMENT:
        result["classification_confidence"] = 0.98
        div_per_share = event.data.get("dividend_per_share", 0)
        for uid in event.affected_users:
            portfolio = portfolios.get(uid)
            if not portfolio:
                continue
            for h in portfolio.all_holdings:
                if h.ticker in event.affected_tickers:
                    div_amount = round(h.quantity * div_per_share, 2)
                    result["user_relevance"][uid] = {
                        "relevance_score": 0.6,
                        "shares_held": h.quantity,
                        "dividend_amount_cad": div_amount,
                        "yield_pct": event.data.get("yield_pct", 0),
                    }
                    result["affected_users"].append(uid)
                    break

    elif event.event_type == EventType.BOC_RATE_DECISION:
        change = abs(event.data.get("change_bps", 0))
        result["classification_confidence"] = 0.97
        result["priority"] = EventPriority.HIGH.value if change > 0 else EventPriority.MEDIUM.value
        for uid, portfolio in portfolios.items():
            bond_exposure = sum(
                h.market_value for h in portfolio.all_holdings
                if h.asset_class.value in ("fixed_income", "etf_bond")
            )
            total = portfolio.total_value
            bond_weight = bond_exposure / total * 100 if total > 0 else 0
            if bond_weight > 5 or change > 0:
                result["user_relevance"][uid] = {
                    "relevance_score": min(1.0, bond_weight / 30 + change / 50),
                    "bond_exposure_cad": round(bond_exposure, 2),
                    "bond_weight_pct": round(bond_weight, 2),
                    "rate_change_bps": event.data.get("change_bps", 0),
                }
                result["affected_users"].append(uid)

    else:
        result["classification_confidence"] = 0.90
        result["affected_users"] = list(event.affected_users)

    result["affected_users"] = list(set(result["affected_users"]))

    duration_ms = (time.perf_counter() - start) * 1000
    latency_tracker.record("event_detection", duration_ms)
    result["detection_time_ms"] = round(duration_ms, 3)

    return result


def _paycheck_relevance(
    amount: float,
    savings_target: float,
    emergency_current: float,
    emergency_target: float,
) -> float:
    score = 0.5
    if emergency_current < emergency_target:
        score += 0.2
    if savings_target > 0 and amount >= savings_target * 0.3:
        score += 0.15
    if amount > 5000:
        score += 0.1
    return min(1.0, score)
