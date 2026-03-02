"""Langfuse observability integration.

Provides tracing decorators and utilities for monitoring every step
of the AML investigation pipeline: triage classifications, tool calls,
investigation state transitions, report generation, and cost tracking.

When LANGFUSE_SECRET_KEY is not set, falls back to a local logger
that captures the same trace structure for demo purposes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL


_langfuse_client = None
_use_langfuse = False


def init_langfuse() -> bool:
    """Initialize Langfuse client if credentials are available."""
    global _langfuse_client, _use_langfuse

    if LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY:
        try:
            from langfuse import Langfuse
            _langfuse_client = Langfuse(
                public_key=LANGFUSE_PUBLIC_KEY,
                secret_key=LANGFUSE_SECRET_KEY,
                host=LANGFUSE_BASE_URL,
            )
            if _langfuse_client.auth_check():
                _use_langfuse = True
                print("Langfuse connected successfully")
                return True
        except Exception as e:
            print(f"Langfuse init failed: {e}")

    print("Langfuse not configured -- using local trace logger")
    return False


# ---------------------------------------------------------------------------
# Local trace store (fallback when Langfuse is not configured)
# ---------------------------------------------------------------------------

@dataclass
class TraceSpan:
    span_id: str
    name: str
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    status: str = "ok"
    cost_usd: float = 0.0
    children: list[TraceSpan] = field(default_factory=list)


@dataclass
class TraceRecord:
    trace_id: str
    name: str
    alert_id: str = ""
    client_id: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    spans: list[TraceSpan] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: TraceSpan) -> None:
        self.spans.append(span)
        self.total_cost_usd += span.cost_usd
        self.total_duration_ms += span.duration_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "alert_id": self.alert_id,
            "client_id": self.client_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_duration_ms": round(self.total_duration_ms, 2),
            "span_count": len(self.spans),
            "spans": [
                {
                    "name": s.name,
                    "duration_ms": round(s.duration_ms, 2),
                    "status": s.status,
                    "cost_usd": round(s.cost_usd, 6),
                }
                for s in self.spans
            ],
            "metadata": self.metadata,
        }


class TraceStore:
    """In-memory trace store for local observability."""

    def __init__(self) -> None:
        self.traces: list[TraceRecord] = []
        self._active_trace: TraceRecord | None = None

    def start_trace(self, name: str, alert_id: str = "", client_id: str = "") -> TraceRecord:
        trace = TraceRecord(
            trace_id=f"trace-{uuid.uuid4().hex[:12]}",
            name=name,
            alert_id=alert_id,
            client_id=client_id,
        )
        self._active_trace = trace
        return trace

    def end_trace(self, trace: TraceRecord) -> None:
        trace.end_time = datetime.now()
        self.traces.append(trace)
        if self._active_trace == trace:
            self._active_trace = None

    @property
    def active_trace(self) -> TraceRecord | None:
        return self._active_trace

    def get_stats(self) -> dict[str, Any]:
        if not self.traces:
            return {"total_traces": 0}

        costs = [t.total_cost_usd for t in self.traces]
        durations = [t.total_duration_ms for t in self.traces]
        return {
            "total_traces": len(self.traces),
            "total_cost_usd": round(sum(costs), 4),
            "avg_cost_usd": round(sum(costs) / len(costs), 6),
            "avg_duration_ms": round(sum(durations) / len(durations), 1),
            "max_duration_ms": round(max(durations), 1),
            "total_spans": sum(len(t.spans) for t in self.traces),
        }

    def get_recent(self, n: int = 20) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.traces[-n:]]


trace_store = TraceStore()


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

LLM_COST_PER_1K_INPUT = 0.00015   # GPT-4o-mini input
LLM_COST_PER_1K_OUTPUT = 0.0006   # GPT-4o-mini output
TRIAGE_COST_PER_CALL = 0.000001   # XGBoost inference is essentially free
TOOL_COST_PER_CALL = 0.00001      # simulated data lookup


def estimate_cost(
    input_tokens: int = 0,
    output_tokens: int = 0,
    tool_calls: int = 0,
    triage_calls: int = 0,
) -> float:
    """Estimate the cost of an operation in USD."""
    cost = (
        (input_tokens / 1000) * LLM_COST_PER_1K_INPUT
        + (output_tokens / 1000) * LLM_COST_PER_1K_OUTPUT
        + tool_calls * TOOL_COST_PER_CALL
        + triage_calls * TRIAGE_COST_PER_CALL
    )
    return cost
