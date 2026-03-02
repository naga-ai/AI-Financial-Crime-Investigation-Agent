"""Unified event telemetry bus for the WS Intelligence Platform.

Captures every significant system action -- page views, pipeline events,
human decisions, cache hits/misses, SLA violations, errors -- into a
ring-buffered in-memory store. In production this would flush to an
observability backend (Datadog, Grafana Loki, OpenTelemetry Collector).

Usage:
    from src.observability.telemetry import telemetry_bus, EventType

    telemetry_bus.emit(EventType.PAGE_VIEW, {"page": "Executive Summary"})
"""

from __future__ import annotations

import enum
import time
import traceback
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class EventType(str, enum.Enum):
    PAGE_VIEW              = "page_view"
    PIPELINE_START         = "pipeline_start"
    PIPELINE_COMPLETE      = "pipeline_complete"
    ALERT_TRIAGED          = "alert_triaged"
    ALERT_AUTO_CLOSED      = "alert_auto_closed"
    INVESTIGATION_COMPLETE = "investigation_complete"
    REPORT_GENERATED       = "report_generated"
    HUMAN_DECISION         = "human_decision"
    CACHE_HIT              = "cache_hit"
    CACHE_MISS             = "cache_miss"
    SLA_VIOLATION          = "sla_violation"
    ERROR                  = "error"
    SYSTEM_HEALTH_CHECK    = "system_health_check"
    PULSE_EVENT            = "pulse_event"
    PULSE_COMPLETE         = "pulse_complete"
    RAG_QUERY              = "rag_query"
    QUEUE_ENQUEUE          = "queue_enqueue"
    QUEUE_PROCESS          = "queue_process"
    QUEUE_DLQ              = "queue_dlq"
    CIRCUIT_BREAKER_OPEN   = "circuit_breaker_open"
    CIRCUIT_BREAKER_CLOSE  = "circuit_breaker_close"


# Severity levels
class Severity(str, enum.Enum):
    DEBUG   = "debug"
    INFO    = "info"
    WARNING = "warning"
    ERROR   = "error"
    CRITICAL = "critical"


@dataclass
class TelemetryEvent:
    event_id:    str
    event_type:  EventType
    timestamp:   str
    metadata:    dict[str, Any]
    component:   str        = ""
    severity:    Severity   = Severity.INFO
    duration_ms: float | None = None
    error:       str | None = None
    session_id:  str        = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id":    self.event_id,
            "event_type":  self.event_type.value,
            "timestamp":   self.timestamp,
            "component":   self.component,
            "severity":    self.severity.value,
            "duration_ms": self.duration_ms,
            "error":       self.error,
            "session_id":  self.session_id,
            **self.metadata,
        }


class TelemetryBus:
    """In-memory ring-buffered event bus.

    Thread-safe for single-process apps (Streamlit). In production, swap
    the deque for an async queue that flushes to an OTLP endpoint.
    """

    MAX_EVENTS = 10_000

    def __init__(self) -> None:
        self._events: deque[TelemetryEvent] = deque(maxlen=self.MAX_EVENTS)
        self._counters: dict[str, int] = {}
        self._error_count: int = 0
        self._start_time: float = time.time()
        self._session_id: str = str(uuid.uuid4())[:8]

    def emit(
        self,
        event_type: EventType,
        metadata: dict[str, Any] | None = None,
        component: str = "",
        severity: Severity = Severity.INFO,
        duration_ms: float | None = None,
        error: str | None = None,
    ) -> TelemetryEvent:
        """Thread-safe ring-buffer ingestion; drops oldest event when buffer is full."""
        event = TelemetryEvent(
            event_id   = str(uuid.uuid4())[:12],
            event_type = event_type,
            timestamp  = datetime.now(timezone.utc).isoformat(),
            metadata   = metadata or {},
            component  = component,
            severity   = severity,
            duration_ms = duration_ms,
            error      = error,
            session_id = self._session_id,
        )
        self._events.append(event)
        key = event_type.value
        self._counters[key] = self._counters.get(key, 0) + 1
        if severity in (Severity.ERROR, Severity.CRITICAL):
            self._error_count += 1
        return event

    def get_events(
        self,
        limit: int = 100,
        event_type: EventType | None = None,
        since_seconds: float | None = None,
        severity: Severity | None = None,
    ) -> list[TelemetryEvent]:
        events = list(self._events)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if severity:
            events = [e for e in events if e.severity == severity]
        if since_seconds:
            cutoff = datetime.now(timezone.utc).timestamp() - since_seconds
            events = [
                e for e in events
                if datetime.fromisoformat(e.timestamp).timestamp() >= cutoff
            ]
        return events[-limit:]

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the N most recent events as dicts for UI display."""
        events = list(self._events)[-limit:]
        return [e.to_dict() for e in reversed(events)]

    def get_stats(self) -> dict[str, Any]:
        uptime = time.time() - self._start_time
        total = sum(self._counters.values())
        return {
            "total_events":    total,
            "error_count":     self._error_count,
            "error_rate":      round(self._error_count / max(total, 1), 4),
            "uptime_seconds":  round(uptime),
            "events_per_min":  round(total / max(uptime / 60, 0.01), 1),
            "by_type":         dict(self._counters),
            "session_id":      self._session_id,
            "buffer_used":     len(self._events),
            "buffer_capacity": self.MAX_EVENTS,
        }

    def get_error_rate(self, window_seconds: float = 300) -> float:
        """Rolling error rate over the last N seconds."""
        recent = self.get_events(since_seconds=window_seconds)
        if not recent:
            return 0.0
        errors = sum(
            1 for e in recent
            if e.severity in (Severity.ERROR, Severity.CRITICAL)
        )
        return round(errors / max(len(recent), 1), 4)

    def get_throughput(self, event_type: EventType, window_seconds: float = 60) -> float:
        """Events of a given type per minute over the last window."""
        recent = self.get_events(event_type=event_type, since_seconds=window_seconds)
        return round(len(recent) / max(window_seconds / 60, 0.01), 1)

    def clear(self) -> None:
        self._events.clear()
        self._counters.clear()
        self._error_count = 0


# Module-level singleton
telemetry_bus = TelemetryBus()
