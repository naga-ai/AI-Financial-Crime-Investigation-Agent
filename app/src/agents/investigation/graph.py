"""LangGraph investigation state machine.

Orchestrates a multi-step AML investigation following the same workflow
a Level 2 analyst uses: gather context -> analyze transactions ->
screen watchlists -> match typologies -> assess risk.

Conditional routing adds deeper analysis for crypto and network cases.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from langgraph.graph import END, StateGraph

from src.agents.investigation.state import InvestigationState
from src.agents.investigation.tools import (
    analyze_transaction_velocity,
    check_watchlist,
    get_account_summary,
    get_behavioral_baseline,
    get_client_profile,
    get_crypto_flow,
    get_entity_relationships,
    get_transaction_history,
    match_typology,
)


def _record_step(
    state: InvestigationState,
    step_name: str,
    tool: str,
    result: dict | list,
    start_time: float,
) -> None:
    from src.observability.langfuse_setup import trace_store, TraceSpan, estimate_cost

    duration_ms = round((time.time() - start_time) * 1000, 2)

    steps = state.get("steps_taken", [])
    steps.append({
        "step_name": step_name,
        "tool_called": tool,
        "duration_ms": duration_ms,
        "timestamp": datetime.now().isoformat(),
        "output_summary": str(result)[:200] if result else "empty",
    })
    state["steps_taken"] = steps

    active = trace_store.active_trace
    if active:
        span = TraceSpan(
            span_id=f"span-{step_name[:8]}",
            name=f"tool:{tool}",
            start_time=start_time,
            end_time=time.time(),
            duration_ms=duration_ms,
            cost_usd=estimate_cost(tool_calls=1),
            status="ok",
        )
        active.add_span(span)


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def gather_context(state: InvestigationState) -> InvestigationState:
    """Step 1: Pull client profile and account summary."""
    t0 = time.time()
    client_id = state["client_id"]

    profile = get_client_profile(client_id)
    state["client_profile"] = profile
    _record_step(state, "Gather Client Profile", "get_client_profile", profile, t0)

    t1 = time.time()
    summary = get_account_summary(client_id)
    state["account_summary"] = summary
    _record_step(state, "Gather Account Summary", "get_account_summary", summary, t1)

    has_crypto = any(
        a.get("type") == "crypto" for a in profile.get("accounts", [])
    )
    state["has_crypto"] = has_crypto

    return state


def analyze_transactions(state: InvestigationState) -> InvestigationState:
    """Step 2: Pull transaction history and analyze velocity patterns."""
    client_id = state["client_id"]

    t0 = time.time()
    history = get_transaction_history(client_id, days=90)
    state["transaction_history"] = history
    _record_step(state, "Pull Transaction History", "get_transaction_history", {"count": len(history)}, t0)

    t1 = time.time()
    velocity = analyze_transaction_velocity(client_id)
    state["velocity_analysis"] = velocity
    _record_step(state, "Analyze Transaction Velocity", "analyze_transaction_velocity", velocity, t1)

    t2 = time.time()
    baseline = get_behavioral_baseline(client_id)
    state["behavioral_baseline"] = baseline
    _record_step(state, "Compute Behavioral Baseline", "get_behavioral_baseline", baseline, t2)

    return state


def screen_watchlists(state: InvestigationState) -> InvestigationState:
    """Step 3: Screen client against sanctions, PEP, and adverse media lists."""
    t0 = time.time()
    results = check_watchlist(state["client_id"])
    state["watchlist_results"] = results
    _record_step(state, "Screen Watchlists", "check_watchlist", results, t0)
    return state


def match_typologies(state: InvestigationState) -> InvestigationState:
    """Step 4: Compare patterns against known ML/TF typologies."""
    t0 = time.time()
    matches = match_typology(state["client_id"], state.get("alert_type", ""))
    state["typology_matches"] = matches
    _record_step(state, "Match Known Typologies", "match_typology", {"matches": len(matches)}, t0)

    entity = get_entity_relationships(state["client_id"])
    state["entity_network"] = entity
    state["has_network"] = entity.get("network_size", 0) > 2
    _record_step(state, "Map Entity Network", "get_entity_relationships", entity, t0)

    return state


def retrieve_regulatory_context(state: InvestigationState) -> InvestigationState:
    """Step 4b: RAG retrieval of relevant FINTRAC regulatory guidance.

    Enriches the investigation with specific regulatory context --
    the exact FINTRAC indicators, typology descriptions, and compliance
    requirements relevant to this alert type. This grounds the final
    risk assessment and report generation in actual regulatory language.
    """
    t0 = time.time()
    try:
        from src.rag.retriever import get_rag_engine

        rag = get_rag_engine()
        alert_type = state.get("alert_type", "")

        risk_factors = state.get("risk_factors", [])
        extra_context = " ".join(risk_factors[:3]) if risk_factors else ""

        rag_context = rag.retrieve_for_alert(alert_type, additional_context=extra_context)

        state["rag_context"] = {
            "query": rag_context.query,
            "method": rag_context.method,
            "retrieval_time_ms": rag_context.retrieval_time_ms,
            "num_results": len(rag_context.results),
            "sources": rag_context.source_citations,
            "context_text": rag_context.context_text,
            "token_estimate": rag_context.token_estimate,
        }

        _record_step(
            state, "RAG: Retrieve Regulatory Context", "rag_retrieve",
            {"results": len(rag_context.results), "method": rag_context.method},
            t0,
        )
    except Exception as e:
        state["rag_context"] = {"error": str(e), "num_results": 0}
        _record_step(state, "RAG: Retrieve Regulatory Context", "rag_retrieve", {"error": str(e)}, t0)

    return state


def deep_crypto_analysis(state: InvestigationState) -> InvestigationState:
    """Step 4a (conditional): Deep-dive crypto chain analysis for crypto-involved cases."""
    t0 = time.time()
    crypto = get_crypto_flow(state["client_id"])
    state["crypto_analysis"] = crypto
    _record_step(state, "Deep Crypto Analysis", "get_crypto_flow", crypto, t0)
    return state


def assess_risk(state: InvestigationState) -> InvestigationState:
    """Step 5: Compute final risk score and recommended action.

    Synthesizes all evidence gathered across previous steps into
    a risk assessment that mirrors how a senior AML analyst would
    weigh the factors before making a filing recommendation.
    """
    risk_score = 0.0
    risk_factors: list[str] = []
    confidence_components: list[float] = []

    # --- Watchlist signals (heaviest weight) ---
    watchlist = state.get("watchlist_results", {})
    if watchlist.get("total_matches", 0) > 0:
        for match in watchlist.get("matches", []):
            if match.get("type") == "PEP":
                risk_score += 25
                risk_factors.append(f"PEP match: {match.get('details', '')}")
                confidence_components.append(0.9)
            elif match.get("type") == "KYC_FLAG":
                risk_score += 15
                risk_factors.append("KYC verification flagged")
                confidence_components.append(0.8)

    # --- Typology matches ---
    typology_matches = state.get("typology_matches", [])
    for tm in typology_matches:
        score = tm.get("match_score", 0)
        if score >= 0.7:
            risk_score += 20
            risk_factors.append(f"Strong typology match: {tm['typology_name']} ({score:.0%})")
            confidence_components.append(score)
        elif score >= 0.4:
            risk_score += 10
            risk_factors.append(f"Partial typology match: {tm['typology_name']} ({score:.0%})")
            confidence_components.append(score * 0.7)

    # --- Velocity anomalies ---
    velocity = state.get("velocity_analysis", {})
    if velocity.get("anomaly_detected"):
        risk_score += 15
        risk_factors.append(velocity.get("anomaly_description", "Velocity anomaly detected"))
        confidence_components.append(0.7)

    # --- Crypto risk indicators ---
    crypto = state.get("crypto_analysis", {})
    if crypto.get("risk_level") == "high":
        risk_score += 20
        for indicator in crypto.get("risk_indicators", [])[:3]:
            risk_factors.append(indicator)
        confidence_components.append(0.85)
    elif crypto.get("risk_level") == "medium":
        risk_score += 10
        confidence_components.append(0.6)

    # --- Network complexity ---
    network = state.get("entity_network", {})
    if network.get("network_size", 0) > 3:
        risk_score += 10
        risk_factors.append(f"Connected to {network['network_size']} other entities")
        confidence_components.append(0.5)

    # --- Amount vs profile ---
    profile = state.get("client_profile", {})
    summary = state.get("account_summary", {})
    max_txn = summary.get("amount_statistics", {}).get("max_transaction_cad", 0)
    income_map = {
        "0-25k": 12_500, "25k-50k": 37_500, "50k-75k": 62_500,
        "75k-100k": 87_500, "100k-150k": 125_000, "150k-200k": 175_000,
        "200k-300k": 250_000, "300k+": 400_000,
    }
    income = income_map.get(profile.get("income_range", ""), 62_500)
    if max_txn > income * 1.5:
        risk_score += 10
        risk_factors.append(
            f"Max transaction ${max_txn:,.0f} exceeds {max_txn/income:.1f}x declared income"
        )
        confidence_components.append(0.6)

    # --- Severity from original alert ---
    alert_severity = state.get("severity_score", 50)
    risk_score += alert_severity * 0.1

    # Cap at 100
    risk_score = min(round(risk_score, 1), 100.0)

    # Confidence: average of component confidences
    confidence = round(float(sum(confidence_components) / max(len(confidence_components), 1)), 2)

    # Risk level and recommendation
    if risk_score >= 75:
        risk_level = "critical"
        recommended_action = "file_str"
    elif risk_score >= 50:
        risk_level = "high"
        recommended_action = "file_str"
    elif risk_score >= 30:
        risk_level = "medium"
        recommended_action = "escalate"
    else:
        risk_level = "low"
        recommended_action = "close"

    if not risk_factors:
        risk_factors.append("No significant risk indicators identified")

    state["risk_score"] = risk_score
    state["risk_level"] = risk_level
    state["confidence"] = confidence
    state["recommended_action"] = recommended_action
    state["risk_factors"] = risk_factors

    steps = state.get("steps_taken", [])
    steps.append({
        "step_name": "Final Risk Assessment",
        "tool_called": "assess_risk",
        "duration_ms": 0,
        "timestamp": datetime.now().isoformat(),
        "output_summary": f"Risk: {risk_score} ({risk_level}), Action: {recommended_action}",
    })
    state["steps_taken"] = steps

    return state


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def should_analyze_crypto(state: InvestigationState) -> str:
    """Route to deep crypto analysis if the client has crypto accounts."""
    if state.get("has_crypto", False):
        return "deep_crypto_analysis"
    return "assess_risk"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_investigation_graph() -> StateGraph:
    """Construct the LangGraph investigation state machine.

    Flow:
        gather_context -> analyze_transactions -> screen_watchlists
        -> match_typologies -> [if crypto: deep_crypto_analysis]
        -> retrieve_regulatory_context (RAG) -> assess_risk
    """
    graph = StateGraph(InvestigationState)

    graph.add_node("gather_context", gather_context)
    graph.add_node("analyze_transactions", analyze_transactions)
    graph.add_node("screen_watchlists", screen_watchlists)
    graph.add_node("match_typologies", match_typologies)
    graph.add_node("deep_crypto_analysis", deep_crypto_analysis)
    graph.add_node("retrieve_regulatory_context", retrieve_regulatory_context)
    graph.add_node("assess_risk", assess_risk)

    graph.set_entry_point("gather_context")
    graph.add_edge("gather_context", "analyze_transactions")
    graph.add_edge("analyze_transactions", "screen_watchlists")
    graph.add_edge("screen_watchlists", "match_typologies")
    graph.add_conditional_edges(
        "match_typologies",
        should_analyze_crypto,
        {"deep_crypto_analysis": "deep_crypto_analysis", "assess_risk": "retrieve_regulatory_context"},
    )
    graph.add_edge("deep_crypto_analysis", "retrieve_regulatory_context")
    graph.add_edge("retrieve_regulatory_context", "assess_risk")
    graph.add_edge("assess_risk", END)

    return graph


_compiled_graph = None


def get_investigation_graph():
    """Return the compiled investigation graph (singleton)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_investigation_graph().compile()
    return _compiled_graph


def run_investigation(
    alert_id: str,
    client_id: str,
    alert_type: str,
    triggered_transaction_ids: list[str],
    severity_score: float,
) -> InvestigationState:
    """Run a full investigation for an alert. Returns the completed state."""
    from src.observability.langfuse_setup import trace_store

    trace = trace_store.start_trace(
        name="aml_investigation",
        alert_id=alert_id,
        client_id=client_id,
    )

    graph = get_investigation_graph()

    initial_state: InvestigationState = {
        "alert_id": alert_id,
        "client_id": client_id,
        "alert_type": alert_type,
        "triggered_transaction_ids": triggered_transaction_ids,
        "severity_score": severity_score,
        "steps_taken": [],
        "errors": [],
        "total_cost_usd": 0.0,
    }

    result = graph.invoke(initial_state)

    trace.metadata["risk_score"] = result.get("risk_score", 0)
    trace.metadata["recommended_action"] = result.get("recommended_action", "unknown")
    trace.metadata["risk_level"] = result.get("risk_level", "unknown")
    trace.metadata["steps_count"] = len(result.get("steps_taken", []))
    trace_store.end_trace(trace)

    return result
