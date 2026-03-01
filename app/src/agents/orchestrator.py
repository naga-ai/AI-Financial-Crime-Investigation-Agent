"""Main pipeline orchestrator: Alert -> Triage -> Investigate -> Report.

This is the entry point for processing AML alerts through the full
AI-native investigation pipeline. Coordinates all agents and maintains
audit trail for regulatory compliance.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.agents.triage.classifier import TriageClassifier, TriageResult
from src.agents.triage.features import _build_indices, _load_data
from src.agents.investigation.graph import run_investigation
from src.agents.investigation.state import InvestigationState
from src.agents.report.generator import generate_str_report
from src.cache.manager import cache
from src.config import DATA_DIR
from src.data.models import AMLAlert, AlertStatus, STRReport
from src.observability.langfuse_setup import trace_store, TraceSpan
from src.observability.telemetry import telemetry_bus, EventType, Severity


@dataclass
class PipelineResult:
    """Complete result of processing a single alert through the pipeline."""
    alert_id: str
    client_id: str
    alert_type: str
    triage: TriageResult | None = None
    investigation: InvestigationState | None = None
    report: STRReport | None = None
    total_pipeline_time_ms: float = 0.0
    status: str = "pending"
    timestamp: str = ""

    def summary(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "alert_id": self.alert_id,
            "client_id": self.client_id,
            "alert_type": self.alert_type,
            "status": self.status,
            "pipeline_time_ms": round(self.total_pipeline_time_ms, 1),
        }
        if self.triage:
            result["triage"] = {
                "priority": self.triage.priority,
                "confidence": round(self.triage.confidence, 3),
                "should_investigate": self.triage.should_investigate,
                "risk_factors": self.triage.risk_factors,
                "classification_time_ms": round(self.triage.classification_time_ms, 1),
                "cache_hit": self.triage.cache_hit,
            }
        if self.investigation:
            result["investigation"] = {
                "risk_score": self.investigation.get("risk_score", 0),
                "risk_level": self.investigation.get("risk_level", "unknown"),
                "confidence": self.investigation.get("confidence", 0),
                "recommended_action": self.investigation.get("recommended_action", "unknown"),
                "risk_factors": self.investigation.get("risk_factors", []),
                "steps_count": len(self.investigation.get("steps_taken", [])),
            }
        return result


class InvestigationPipeline:
    """Orchestrates the full AML investigation pipeline."""

    def __init__(self) -> None:
        self.clients, self.transactions, self.alerts = _load_data()
        self.client_map, self.client_txns, self.txn_map = _build_indices(
            self.clients, self.transactions,
        )
        self.triage = TriageClassifier()
        self.results: list[PipelineResult] = []

    def process_alert(self, alert: AMLAlert) -> PipelineResult:
        """Process a single alert through the full pipeline."""
        start = time.time()
        result = PipelineResult(
            alert_id=alert.alert_id,
            client_id=alert.client_id,
            alert_type=alert.alert_type.value,
            timestamp=datetime.now().isoformat(),
        )

        # Step 1: Triage
        triage_result = self.triage.classify(
            alert, self.client_map, self.client_txns, self.txn_map,
        )
        result.triage = triage_result

        telemetry_bus.emit(
            EventType.ALERT_TRIAGED,
            metadata={
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "priority": triage_result.priority,
                "confidence": round(triage_result.confidence, 3),
                "cache_hit": triage_result.cache_hit,
                "should_investigate": triage_result.should_investigate,
            },
            component="triage_classifier",
            duration_ms=triage_result.classification_time_ms,
        )

        if not triage_result.should_investigate:
            result.status = "auto_closed"
            result.total_pipeline_time_ms = (time.time() - start) * 1000
            self.results.append(result)
            telemetry_bus.emit(
                EventType.ALERT_AUTO_CLOSED,
                metadata={"alert_id": alert.alert_id, "alert_type": alert.alert_type.value},
                component="pipeline",
            )
            return result

        # Step 2: Full investigation
        inv_start = time.time()
        investigation_state = run_investigation(
            alert_id=alert.alert_id,
            client_id=alert.client_id,
            alert_type=alert.alert_type.value,
            triggered_transaction_ids=alert.triggered_transactions,
            severity_score=alert.severity_score,
        )
        inv_ms = (time.time() - inv_start) * 1000
        result.investigation = investigation_state

        action = investigation_state.get("recommended_action", "close")
        if action == "file_str":
            result.status = "pending_str_review"
        elif action == "escalate":
            result.status = "escalated"
        else:
            result.status = "closed_after_investigation"

        telemetry_bus.emit(
            EventType.INVESTIGATION_COMPLETE,
            metadata={
                "alert_id": alert.alert_id,
                "risk_score": investigation_state.get("risk_score", 0),
                "risk_level": investigation_state.get("risk_level", "unknown"),
                "recommended_action": action,
                "steps_count": len(investigation_state.get("steps_taken", [])),
                "status": result.status,
            },
            component="investigation_agent",
            duration_ms=inv_ms,
        )

        # Step 3: Generate STR report for cases that need review
        if result.status in ("pending_str_review", "escalated"):
            rpt_start = time.time()
            report = generate_str_report(investigation_state, use_llm=False)
            result.report = report
            telemetry_bus.emit(
                EventType.REPORT_GENERATED,
                metadata={
                    "alert_id": alert.alert_id,
                    "report_id": report.report_id if report else None,
                    "status": result.status,
                },
                component="report_generator",
                duration_ms=(time.time() - rpt_start) * 1000,
            )

        # Step 4: Index completed case in RAG for future precedent retrieval
        try:
            from src.rag.retriever import get_rag_engine
            get_rag_engine().index_completed_case(investigation_state)
        except Exception:
            pass

        result.total_pipeline_time_ms = (time.time() - start) * 1000
        self.results.append(result)
        return result

    def process_batch(
        self,
        alerts: list[AMLAlert] | None = None,
        limit: int | None = None,
    ) -> list[PipelineResult]:
        """Process a batch of alerts through the pipeline."""
        target = alerts or self.alerts
        if limit:
            target = target[:limit]

        batch_start = time.time()
        telemetry_bus.emit(
            EventType.PIPELINE_START,
            metadata={"batch_size": len(target)},
            component="pipeline",
        )

        results = []
        for i, alert in enumerate(target):
            result = self.process_alert(alert)
            results.append(result)
            print(
                f"  [{i+1}/{len(target)}] {alert.alert_id} | "
                f"{alert.alert_type.value:25s} | "
                f"Triage: {result.triage.priority if result.triage else 'N/A':6s} | "
                f"Status: {result.status}"
            )

        auto_closed = sum(1 for r in results if r.status == "auto_closed")
        investigated = sum(1 for r in results if r.investigation)
        telemetry_bus.emit(
            EventType.PIPELINE_COMPLETE,
            metadata={
                "batch_size": len(results),
                "auto_closed": auto_closed,
                "investigated": investigated,
                "pending_str": sum(1 for r in results if r.status == "pending_str_review"),
            },
            component="pipeline",
            duration_ms=(time.time() - batch_start) * 1000,
        )

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Pipeline performance statistics."""
        if not self.results:
            return {"error": "No results yet"}

        statuses = {}
        for r in self.results:
            statuses[r.status] = statuses.get(r.status, 0) + 1

        times = [r.total_pipeline_time_ms for r in self.results]
        investigated = [r for r in self.results if r.investigation]
        auto_closed = [r for r in self.results if r.status == "auto_closed"]

        stats = {
            "total_processed": len(self.results),
            "status_breakdown": statuses,
            "auto_close_rate": f"{len(auto_closed)/max(len(self.results),1)*100:.1f}%",
            "investigated": len(investigated),
            "pending_str_review": statuses.get("pending_str_review", 0),
            "timing": {
                "avg_pipeline_ms": round(sum(times) / max(len(times), 1), 1),
                "avg_triage_ms": round(
                    sum(r.triage.classification_time_ms for r in self.results if r.triage)
                    / max(len(self.results), 1), 1
                ),
            },
            "cache_stats": cache.stats,
        }
        return stats
