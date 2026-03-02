"""
FastAPI backend server for the WS Intelligence Platform.

Exposes the Python ML pipeline (XGBoost triage, LangGraph investigation,
Pattern Discovery, Observability) via a clean REST API consumed by the
Next.js frontend.
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.observability.telemetry import telemetry_bus, EventType


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init Langfuse if configured. Shutdown: no-op."""
    from src.observability.langfuse_setup import init_langfuse
    init_langfuse()
    yield


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="WS Intelligence Platform API",
    description="AI-Native AML & Client Intelligence for Wealthsimple",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened to the frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Lazy singletons - loaded once on first request to keep startup fast
# ---------------------------------------------------------------------------
_pipeline = None
_pulse = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from src.agents.orchestrator import InvestigationPipeline
        _pipeline = InvestigationPipeline()
    return _pipeline


def get_pulse():
    global _pulse
    if _pulse is None:
        from src.pulse.orchestrator import PulseOrchestrator
        _pulse = PulseOrchestrator()
    return _pulse


# ---------------------------------------------------------------------------
# In-memory session store (mirrors Streamlit session_state)
# ---------------------------------------------------------------------------
_session: dict[str, Any] = {
    "pipeline_results": [],
    "reports": {},
    "decisions": {},
    "processed": False,
    "pattern_results": None,
    "run_timestamp": None,
    "pulse_results": [],
    "pulse_processed": False,
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ProcessRequest(BaseModel):
    limit: int = 315


class DecisionRequest(BaseModel):
    decision: str  # APPROVED | REJECTED | ESCALATED


class PatternRequest(BaseModel):
    method: str = "kmeans"
    n_clusters: int = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _result_to_dict(r) -> dict:
    inv = r.investigation or {}
    report = None
    if r.report:
        report = {
            "report_id": r.report.report_id,
            "risk_score": r.report.risk_score,
            "recommended_filing": r.report.recommended_filing,
            "narrative": r.report.narrative,
            "risk_indicators": r.report.risk_indicators,
            "suspicion_type": r.report.suspicion_type.value,
            "subject_info": r.report.subject_info,
        }

    triage = None
    if r.triage:
        triage = {
            "priority": r.triage.priority,
            "confidence": r.triage.confidence,
            "should_investigate": r.triage.should_investigate,
            "classification_time_ms": r.triage.classification_time_ms,
            "risk_factors": r.triage.risk_factors,
        }

    return {
        "alert_id": r.alert_id,
        "client_id": r.client_id,
        "alert_type": r.alert_type,
        "status": r.status,
        "total_pipeline_time_ms": r.total_pipeline_time_ms,
        "triage": triage,
        "investigation": {
            "risk_score": inv.get("risk_score", 0),
            "risk_level": inv.get("risk_level", "unknown"),
            "confidence": inv.get("confidence", 0),
            "recommended_action": inv.get("recommended_action", "close"),
            "risk_factors": inv.get("risk_factors", []),
            "steps_taken": inv.get("steps_taken", []),
            "typology_matches": inv.get("typology_matches", []),
            "client_profile": inv.get("client_profile", {}),
            "transaction_history": inv.get("transaction_history", []),
        } if r.investigation else None,
        "report": report,
    }


# ---------------------------------------------------------------------------
# Routes — Overview
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/overview")
def overview():
    """Return dataset overview before pipeline is run."""
    p = get_pipeline()
    tp = sum(1 for a in p.alerts if a.is_true_positive)
    alert_types: dict[str, int] = {}
    for a in p.alerts:
        t = a.alert_type.value
        alert_types[t] = alert_types.get(t, 0) + 1
    return {
        "n_clients": len(p.clients),
        "n_transactions": len(p.transactions),
        "n_alerts": len(p.alerts),
        "true_positives": tp,
        "false_positives": len(p.alerts) - tp,
        "alert_types": alert_types,
        "processed": _session["processed"],
        "run_timestamp": _session["run_timestamp"],
    }


# ---------------------------------------------------------------------------
# Routes — Pipeline
# ---------------------------------------------------------------------------
@app.post("/api/alerts/process")
def process_alerts(req: ProcessRequest):
    """Trigger the full investigation pipeline."""
    pipeline = get_pipeline()
    alerts = pipeline.alerts[: req.limit]
    results = []
    for alert in alerts:
        result = pipeline.process_alert(alert)
        results.append(result)

    _session["pipeline_results"] = results
    _session["processed"] = True
    _session["run_timestamp"] = datetime.utcnow().isoformat()

    for r in results:
        if r.report:
            _session["reports"][r.alert_id] = r.report
    for r in results:
        if r.alert_id not in _session["decisions"] and r.report:
            _session["decisions"][r.alert_id] = "PENDING"

    return {"processed": len(results), "timestamp": _session["run_timestamp"]}


@app.get("/api/alerts/results")
def get_results():
    """Return all processed pipeline results."""
    if not _session["processed"]:
        return {"processed": False, "results": []}

    results = _session["pipeline_results"]
    return {
        "processed": True,
        "run_timestamp": _session["run_timestamp"],
        "results": [_result_to_dict(r) for r in results],
    }


@app.get("/api/alerts/stats")
def get_stats():
    """Aggregated statistics for the executive summary."""
    if not _session["processed"]:
        raise HTTPException(status_code=404, detail="Pipeline not run yet")

    results = _session["pipeline_results"]
    n = len(results)
    auto = sum(1 for r in results if r.status == "auto_closed")
    investigated = [r for r in results if r.investigation]
    pending_str = sum(1 for r in results if r.status == "pending_str_review")
    escalated = sum(1 for r in results if r.status == "escalated")
    reports_done = len(_session["reports"])
    decisions_made = sum(1 for v in _session["decisions"].values() if v != "PENDING")
    avg_ms = sum(r.total_pipeline_time_ms for r in results) / max(n, 1)

    status_counts: dict[str, int] = {}
    for r in results:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1

    type_counts: dict[str, int] = {}
    for r in results:
        type_counts[r.alert_type] = type_counts.get(r.alert_type, 0) + 1

    risk_data = []
    for r in investigated:
        inv = r.investigation
        risk_data.append({
            "risk_score": inv.get("risk_score", 0),
            "risk_level": inv.get("risk_level", "unknown"),
            "alert_type": r.alert_type,
            "action": inv.get("recommended_action", "close"),
            "pipeline_ms": r.total_pipeline_time_ms,
        })

    return {
        "n": n,
        "auto_closed": auto,
        "auto_rate": auto / max(n, 1),
        "investigated": len(investigated),
        "pending_str": pending_str,
        "escalated": escalated,
        "reports": reports_done,
        "decisions_made": decisions_made,
        "avg_latency_ms": avg_ms,
        "status_breakdown": status_counts,
        "type_breakdown": type_counts,
        "risk_data": risk_data,
    }


# ---------------------------------------------------------------------------
# Routes — Reports & Decisions
# ---------------------------------------------------------------------------
@app.get("/api/reports")
def get_reports():
    """Return all STR reports with their decisions."""
    reports = _session["reports"]
    decisions = _session["decisions"]
    out = []
    for aid, rep in reports.items():
        out.append({
            "alert_id": aid,
            "report_id": rep.report_id,
            "risk_score": rep.risk_score,
            "recommended_filing": rep.recommended_filing,
            "narrative": rep.narrative,
            "risk_indicators": rep.risk_indicators,
            "suspicion_type": rep.suspicion_type.value,
            "subject_info": rep.subject_info,
            "decision": decisions.get(aid, "PENDING"),
        })
    return {"reports": out}


@app.post("/api/reports/{alert_id}/decision")
def make_decision(alert_id: str, req: DecisionRequest):
    """Record a compliance officer decision for an STR report."""
    if alert_id not in _session["reports"]:
        raise HTTPException(status_code=404, detail="Report not found")
    valid = {"APPROVED", "REJECTED", "ESCALATED"}
    if req.decision.upper() not in valid:
        raise HTTPException(status_code=400, detail=f"Decision must be one of {valid}")
    _session["decisions"][alert_id] = req.decision.upper()
    telemetry_bus.emit(
        EventType.HUMAN_DECISION,
        metadata={"alert_id": alert_id, "decision": req.decision.upper()},
        component="api",
    )
    return {"alert_id": alert_id, "decision": req.decision.upper()}


# ---------------------------------------------------------------------------
# Routes — Pattern Discovery
# ---------------------------------------------------------------------------
@app.post("/api/patterns/discover")
def discover_patterns(req: PatternRequest):
    """Run unsupervised clustering on completed investigations."""
    from src.agents.pattern_discovery.clustering import discover_patterns as dp
    investigations = [
        r.investigation
        for r in _session["pipeline_results"]
        if r.investigation
    ]
    if len(investigations) < 5:
        raise HTTPException(status_code=400, detail="Need at least 5 investigations")
    result = dp(investigations, method=req.method, n_clusters=req.n_clusters)
    _session["pattern_results"] = result
    return result


@app.get("/api/patterns/results")
def get_pattern_results():
    if not _session["pattern_results"]:
        raise HTTPException(status_code=404, detail="No pattern results. Run discovery first.")
    return _session["pattern_results"]


# ---------------------------------------------------------------------------
# Routes — Observability
# ---------------------------------------------------------------------------
@app.get("/api/observability/stats")
def observability_stats():
    from src.observability.langfuse_setup import trace_store
    return trace_store.get_stats()


@app.get("/api/observability/traces")
def observability_traces(limit: int = 50):
    from src.observability.langfuse_setup import trace_store
    return {"traces": trace_store.get_recent(limit)}


# ---------------------------------------------------------------------------
# Routes — Model Intelligence
# ---------------------------------------------------------------------------
@app.get("/api/model/metrics")
def model_metrics():
    metrics_path = Path("src/agents/triage/triage_metrics.json")
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Model not trained yet")
    with open(metrics_path) as f:
        return json.load(f)


@app.post("/api/model/train")
def model_train():
    """Train the XGBoost triage model, save to disk, and hot-reload the pipeline."""
    from src.agents.triage.classifier import train_triage_model, TriageClassifier
    _, result = train_triage_model(save=True)
    pipeline = get_pipeline()
    pipeline.triage = TriageClassifier()
    return result


# ---------------------------------------------------------------------------
# Routes — Cache
# ---------------------------------------------------------------------------
@app.get("/api/cache/stats")
def cache_stats():
    from src.cache.manager import cache
    return cache.summary


# ---------------------------------------------------------------------------
# Routes — Pulse (WS Pilot)
# ---------------------------------------------------------------------------
@app.post("/api/pulse/process")
def process_pulse(max_events: int = 15):
    pulse = get_pulse()
    results = pulse.process_all_events(max_events=max_events)
    _session["pulse_results"] = [
        {
            "user_id": r.user_id,
            "event_type": r.event.event_type.value,
            "processing_time_ms": r.processing_time_ms,
            "cache_hit": r.cache_hit,
            "recommendation": {
                "title": r.recommendation.title,
                "priority": r.recommendation.priority.value,
                "action": r.recommendation.action.value,
                "confidence": r.recommendation.confidence,
                "estimated_value_cad": r.recommendation.estimated_value_cad,
                "summary": r.recommendation.impact_summary or r.recommendation.narrative,
            } if r.recommendation else None,
        }
        for r in results
    ]
    _session["pulse_processed"] = True
    return {"processed": len(results)}


@app.get("/api/pulse/results")
def get_pulse_results():
    return {"results": _session["pulse_results"]}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
