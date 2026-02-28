"""Latency tracking with P50/P90/P95/P99 percentile computation.

Every pipeline component records its execution time. This module
computes rolling percentiles using reservoir sampling (bounded memory)
and checks them against defined SLA thresholds.
"""

from __future__ import annotations

import bisect
import functools
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class SLADefinition:
    component: str
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    description: str = ""


DEFAULT_SLAS: dict[str, SLADefinition] = {
    "triage": SLADefinition("triage", p50_ms=2, p90_ms=5, p95_ms=8, p99_ms=15,
                            description="XGBoost classification"),
    "investigation": SLADefinition("investigation", p50_ms=100, p90_ms=300, p95_ms=500, p99_ms=1000,
                                   description="Full LangGraph investigation"),
    "report_generation": SLADefinition("report_generation", p50_ms=50, p90_ms=150, p95_ms=250, p99_ms=500,
                                       description="STR report generation"),
    "rag_retrieval": SLADefinition("rag_retrieval", p50_ms=10, p90_ms=30, p95_ms=50, p99_ms=100,
                                   description="RAG vector search"),
    "cache_lookup": SLADefinition("cache_lookup", p50_ms=0.5, p90_ms=1, p95_ms=2, p99_ms=5,
                                  description="Redis/memory cache lookup"),
    "pii_masking": SLADefinition("pii_masking", p50_ms=0.1, p90_ms=0.5, p95_ms=1, p99_ms=2,
                                 description="PII tokenization"),
    "event_detection": SLADefinition("event_detection", p50_ms=5, p90_ms=15, p95_ms=25, p99_ms=50,
                                     description="Financial event classification"),
    "portfolio_analysis": SLADefinition("portfolio_analysis", p50_ms=20, p90_ms=60, p95_ms=100, p99_ms=200,
                                        description="Portfolio impact analysis"),
    "recommendation": SLADefinition("recommendation", p50_ms=30, p90_ms=80, p95_ms=150, p99_ms=300,
                                    description="Action recommendation generation"),
}


@dataclass
class SLACheck:
    component: str
    percentile: str
    threshold_ms: float
    actual_ms: float
    passed: bool
    samples: int


class LatencyTracker:
    """Records latencies and computes rolling percentiles per component.

    Uses a reservoir of fixed size per component to bound memory usage
    while maintaining statistically representative samples.
    """

    def __init__(self, reservoir_size: int = 2000):
        self._reservoir_size = reservoir_size
        self._samples: dict[str, list[float]] = {}
        self._counts: dict[str, int] = {}
        self._slas = dict(DEFAULT_SLAS)

    def record(self, component: str, duration_ms: float) -> None:
        if component not in self._samples:
            self._samples[component] = []
            self._counts[component] = 0

        self._counts[component] += 1
        samples = self._samples[component]

        if len(samples) < self._reservoir_size:
            bisect.insort(samples, duration_ms)
        else:
            j = random.randint(0, self._counts[component] - 1)
            if j < self._reservoir_size:
                samples[j] = duration_ms
                samples.sort()

    def percentiles(self, component: str) -> dict[str, float]:
        samples = self._samples.get(component, [])
        if not samples:
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0, "count": 0, "min": 0, "max": 0, "mean": 0}

        n = len(samples)
        return {
            "p50": round(samples[int(n * 0.50)], 3),
            "p90": round(samples[int(n * 0.90)] if n > 1 else samples[0], 3),
            "p95": round(samples[int(n * 0.95)] if n > 1 else samples[0], 3),
            "p99": round(samples[min(int(n * 0.99), n - 1)], 3),
            "count": self._counts.get(component, n),
            "min": round(samples[0], 3),
            "max": round(samples[-1], 3),
            "mean": round(sum(samples) / n, 3),
        }

    def all_percentiles(self) -> dict[str, dict[str, float]]:
        return {comp: self.percentiles(comp) for comp in sorted(self._samples)}

    def sla_status(self) -> list[SLACheck]:
        checks = []
        for component, sla in self._slas.items():
            p = self.percentiles(component)
            count = p.get("count", 0)
            if count == 0:
                continue
            for pct_name, pct_key in [("P50", "p50"), ("P90", "p90"), ("P95", "p95"), ("P99", "p99")]:
                threshold = getattr(sla, f"{pct_key}_ms")
                actual = p[pct_key]
                checks.append(SLACheck(
                    component=component,
                    percentile=pct_name,
                    threshold_ms=threshold,
                    actual_ms=actual,
                    passed=actual <= threshold,
                    samples=count,
                ))
        return checks

    def sla_summary(self) -> dict[str, Any]:
        checks = self.sla_status()
        if not checks:
            return {"total_checks": 0, "passed": 0, "failed": 0, "pass_rate": 0}
        passed = sum(1 for c in checks if c.passed)
        return {
            "total_checks": len(checks),
            "passed": passed,
            "failed": len(checks) - passed,
            "pass_rate": round(passed / len(checks) * 100, 1),
            "violations": [
                {
                    "component": c.component,
                    "percentile": c.percentile,
                    "threshold_ms": c.threshold_ms,
                    "actual_ms": c.actual_ms,
                }
                for c in checks if not c.passed
            ],
        }

    @property
    def components(self) -> list[str]:
        return sorted(self._samples.keys())

    def define_sla(self, sla: SLADefinition) -> None:
        self._slas[sla.component] = sla


def track_latency(component: str):
    """Decorator that automatically records function execution time."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                latency_tracker.record(component, duration_ms)
        return wrapper
    return decorator


latency_tracker = LatencyTracker()
