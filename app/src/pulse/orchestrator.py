"""WS Pilot pipeline orchestrator.

Integrates the event queue, PII masking, latency tracking, caching,
and the Pulse agent pipeline. Processes financial events into
personalized recommendations.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.pulse.models import (
    EventType, MarketEvent, Portfolio, PulseProcessingResult,
    Recommendation, RecommendationStatus,
)
from src.pulse.data.portfolio_generator import generate_portfolios
from src.pulse.data.market_event_generator import generate_events
from src.pulse.agents.graph import run_pulse_pipeline
from src.shared.pii import pii_masker
from src.shared.queue import event_queue, Priority, EventStatus
from src.shared.latency import latency_tracker
from src.cache.manager import cache
from src.observability.langfuse_setup import trace_store


PRIORITY_MAP = {
    "high": Priority.HIGH,
    "medium": Priority.MEDIUM,
    "low": Priority.LOW,
}


@dataclass
class PulseOrchestrator:
    """Orchestrates the full Pulse event processing pipeline."""

    portfolios: list[Portfolio] = field(default_factory=list)
    portfolio_map: dict[str, Portfolio] = field(default_factory=dict)
    events: list[MarketEvent] = field(default_factory=list)
    results: list[PulseProcessingResult] = field(default_factory=list)
    _rag_engine: Any = None

    def __post_init__(self):
        if not self.portfolios:
            self.portfolios = generate_portfolios()
        self.portfolio_map = {p.user_id: p for p in self.portfolios}
        if not self.events:
            self.events = generate_events(self.portfolios)

    def _get_rag_engine(self):
        if self._rag_engine is None:
            try:
                from src.rag.retriever import get_rag_engine
                self._rag_engine = get_rag_engine()
            except Exception:
                self._rag_engine = None
        return self._rag_engine

    def process_event(self, event: MarketEvent, user_id: str) -> PulseProcessingResult | None:
        portfolio = self.portfolio_map.get(user_id)
        if not portfolio:
            return None

        pipeline_start = time.perf_counter()

        trace = trace_store.start_trace(
            name="pulse_event_processing",
            alert_id=event.event_id,
            client_id=user_id,
        )

        cache_key = f"pulse:{event.event_id}:{user_id}"
        cached = cache.get("investigation", cache_key)
        if cached is not None:
            latency_tracker.record("cache_lookup", 0.1)
            result = cached
            result.cache_hit = True
            trace_store.end_trace(trace)
            return result

        masked_data = pii_masker.mask_record(
            {
                "user_id": user_id,
                "display_name": portfolio.display_name,
                "province": portfolio.province,
                "event_type": event.event_type.value,
            },
            purpose="pulse_pipeline",
            component="pulse_orchestrator",
        )

        queue_event = event_queue.enqueue(
            event_type=f"pulse:{event.event_type.value}",
            payload={
                "event_id": event.event_id,
                "user_id": masked_data.get("user_id", user_id),
                "priority": event.priority.value,
            },
            priority=PRIORITY_MAP.get(event.priority.value, Priority.MEDIUM),
        )

        rag_engine = self._get_rag_engine()

        result = run_pulse_pipeline(
            event=event,
            portfolio=portfolio,
            all_portfolios=self.portfolio_map,
            rag_engine=rag_engine,
        )

        result.pii_tokens_masked = len(masked_data)

        cache.set("investigation", cache_key, result)

        if queue_event:
            processing_ms = (time.perf_counter() - pipeline_start) * 1000
            event_queue.ack(queue_event, processing_ms)

        trace.metadata["event_type"] = event.event_type.value
        trace.metadata["user_id"] = user_id
        trace.metadata["processing_time_ms"] = result.processing_time_ms
        if result.recommendation:
            trace.metadata["recommendation_action"] = result.recommendation.action.value
            trace.metadata["recommendation_confidence"] = result.recommendation.confidence
        trace_store.end_trace(trace)

        self.results.append(result)
        return result

    def process_all_events(self, max_events: int | None = None) -> list[PulseProcessingResult]:
        events_to_process = self.events[:max_events] if max_events else self.events
        all_results: list[PulseProcessingResult] = []

        for event in events_to_process:
            for user_id in event.affected_users:
                if user_id not in self.portfolio_map:
                    continue
                result = self.process_event(event, user_id)
                if result:
                    all_results.append(result)

        return all_results

    def get_recommendations_by_user(self, user_id: str) -> list[Recommendation]:
        recs = []
        for r in self.results:
            if r.user_id == user_id and r.recommendation:
                recs.append(r.recommendation)
        return sorted(recs, key=lambda x: x.created_at or datetime.min, reverse=True)

    def get_event_feed(self, limit: int = 20) -> list[dict[str, Any]]:
        feed = []
        for r in self.results[-limit:]:
            entry = {
                "event_id": r.event.event_id,
                "event_type": r.event.event_type.value,
                "title": r.event.title,
                "priority": r.event.priority.value,
                "user_id": r.user_id,
                "user_name": self.portfolio_map.get(r.user_id, None),
                "processing_time_ms": r.processing_time_ms,
                "cache_hit": r.cache_hit,
                "timestamp": r.event.timestamp.isoformat() if r.event.timestamp else "",
            }
            if r.recommendation:
                entry["recommendation"] = {
                    "action": r.recommendation.action.value,
                    "title": r.recommendation.title,
                    "confidence": r.recommendation.confidence,
                    "status": r.recommendation.status.value,
                    "estimated_value": r.recommendation.estimated_value_cad,
                }
            feed.append(entry)
        return list(reversed(feed))

    @property
    def stats(self) -> dict[str, Any]:
        total = len(self.results)
        if total == 0:
            return {"total_processed": 0}

        by_type: dict[str, int] = {}
        by_action: dict[str, int] = {}
        total_value = 0.0
        total_time = 0.0
        cache_hits = 0

        for r in self.results:
            et = r.event.event_type.value
            by_type[et] = by_type.get(et, 0) + 1
            total_time += r.processing_time_ms
            if r.cache_hit:
                cache_hits += 1
            if r.recommendation:
                act = r.recommendation.action.value
                by_action[act] = by_action.get(act, 0) + 1
                total_value += r.recommendation.estimated_value_cad

        return {
            "total_processed": total,
            "by_event_type": by_type,
            "by_recommendation_action": by_action,
            "total_estimated_value_cad": round(total_value, 2),
            "avg_processing_time_ms": round(total_time / total, 2),
            "cache_hit_rate": round(cache_hits / total * 100, 1),
            "unique_users": len(set(r.user_id for r in self.results)),
        }
