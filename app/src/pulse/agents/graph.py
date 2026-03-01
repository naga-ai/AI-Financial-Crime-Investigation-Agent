"""LangGraph state machine for the WS Pilot event processing pipeline.

Pipeline: detect -> analyze -> RAG retrieve -> recommend
Each step is PII-masked, latency-tracked, and traced.
"""

from __future__ import annotations

import time
from typing import Any, TypedDict

from src.pulse.models import (
    EventType, MarketEvent, Portfolio, PulseProcessingResult, Recommendation,
)
from src.pulse.agents.event_detector import detect_and_classify
from src.pulse.agents.portfolio_analyzer import analyze_portfolio_impact
from src.pulse.agents.recommender import generate_recommendation
from src.shared.latency import latency_tracker


class PulseState(TypedDict, total=False):
    event: dict[str, Any]
    user_id: str
    portfolio: dict[str, Any]
    detection: dict[str, Any]
    impact_analysis: dict[str, Any]
    rag_context: dict[str, Any]
    recommendation: dict[str, Any]
    steps_taken: list[dict[str, Any]]
    total_time_ms: float
    error: str | None


def run_pulse_pipeline(
    event: MarketEvent,
    portfolio: Portfolio,
    all_portfolios: dict[str, Portfolio],
    rag_engine: Any = None,
) -> PulseProcessingResult:
    """Execute the full Pulse pipeline for a single event + user."""

    pipeline_start = time.perf_counter()
    steps: list[dict[str, Any]] = []

    # Step 1: Event Detection & Classification
    step_start = time.perf_counter()
    detection = detect_and_classify(event, all_portfolios)
    step_ms = (time.perf_counter() - step_start) * 1000
    steps.append({
        "step": "event_detection",
        "duration_ms": round(step_ms, 3),
        "output_summary": f"Classified as {detection['event_type']} with {detection['classification_confidence']:.0%} confidence",
    })

    # Step 2: Portfolio Impact Analysis
    step_start = time.perf_counter()
    impact = analyze_portfolio_impact(event, portfolio, detection)
    step_ms = (time.perf_counter() - step_start) * 1000
    steps.append({
        "step": "portfolio_analysis",
        "duration_ms": round(step_ms, 3),
        "output_summary": f"Analyzed impact on {portfolio.display_name}'s ${portfolio.total_value:,.0f} portfolio",
    })

    # Step 3: RAG Financial Guidance
    rag_context: dict[str, Any] = {}
    step_start = time.perf_counter()
    if rag_engine is not None:
        try:
            query = _build_rag_query(event, impact)
            rag_result = rag_engine.retrieve(query, top_k=3)
            rag_context = {
                "query": query,
                "results": [
                    {"title": r.title, "content": r.content[:200], "score": r.relevance_score}
                    for r in rag_result.results
                ],
                "method": rag_result.method,
                "retrieval_time_ms": rag_result.retrieval_time_ms,
            }
        except Exception:
            rag_context = {"error": "RAG retrieval failed", "results": []}
    step_ms = (time.perf_counter() - step_start) * 1000
    latency_tracker.record("rag_retrieval", step_ms)
    steps.append({
        "step": "rag_retrieval",
        "duration_ms": round(step_ms, 3),
        "output_summary": f"Retrieved {len(rag_context.get('results', []))} guidance documents",
    })

    # Step 4: Generate Recommendation
    step_start = time.perf_counter()
    recommendation = generate_recommendation(
        event_type=event.event_type,
        portfolio=portfolio,
        impact_analysis=impact,
        rag_context=rag_context if rag_context.get("results") else None,
        event_id=event.event_id,
    )
    step_ms = (time.perf_counter() - step_start) * 1000
    steps.append({
        "step": "recommendation",
        "duration_ms": round(step_ms, 3),
        "output_summary": f"Generated: {recommendation.title}",
    })

    total_ms = (time.perf_counter() - pipeline_start) * 1000
    latency_tracker.record("pulse_pipeline", total_ms)

    return PulseProcessingResult(
        event=event,
        user_id=portfolio.user_id,
        portfolio_snapshot={
            "total_value": portfolio.total_value,
            "account_count": len(portfolio.accounts),
            "holding_count": len(portfolio.all_holdings),
            "risk_profile": portfolio.goals.risk_profile.value,
        },
        impact_analysis=impact,
        rag_context=rag_context,
        recommendation=recommendation,
        processing_time_ms=round(total_ms, 3),
    )


def _build_rag_query(event: MarketEvent, impact: dict[str, Any]) -> str:
    if event.event_type == EventType.PAYCHECK:
        return "TFSA RRSP contribution room tax optimization paycheck allocation Canadian"
    elif event.event_type == EventType.EARNINGS_REPORT:
        tickers = ", ".join(event.affected_tickers)
        return f"earnings report impact portfolio concentration risk rebalancing {tickers}"
    elif event.event_type == EventType.MARKET_DROP:
        return "market decline portfolio strategy tax loss harvesting buying opportunity risk management"
    elif event.event_type == EventType.BOC_RATE_DECISION:
        return "Bank of Canada interest rate bond portfolio impact fixed income strategy"
    elif event.event_type == EventType.DIVIDEND_PAYMENT:
        return "dividend reinvestment DRIP eligible Canadian dividend tax credit"
    else:
        return "financial planning investment strategy portfolio management"
