"""Unified caching layer with Redis backend and in-memory fallback.

Supports typed cache regions with independent TTLs for different
data freshness requirements. Automatically falls back to in-memory
when Redis is unavailable, making local dev frictionless while
production runs at full performance.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import time
from dataclasses import dataclass, field
from typing import Any

from src.config import REDIS_URL


# ---------------------------------------------------------------------------
# In-memory backend
# ---------------------------------------------------------------------------

@dataclass
class CacheEntry:
    value: Any
    created_at: float
    ttl_seconds: float
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds


class MemoryBackend:
    """Dict-backed cache for local development."""

    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> tuple[Any | None, bool]:
        entry = self._store.get(key)
        if entry is None:
            return None, False
        if entry.is_expired:
            del self._store[key]
            return None, False
        entry.hits += 1
        return entry.value, True

    def set(self, key: str, value: Any, ttl: float) -> None:
        self._store[key] = CacheEntry(
            value=value, created_at=time.time(), ttl_seconds=ttl,
        )

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)


# ---------------------------------------------------------------------------
# Redis backend
# ---------------------------------------------------------------------------

class RedisBackend:
    """Redis-backed cache for production deployment."""

    def __init__(self, url: str) -> None:
        import redis
        self._client = redis.from_url(url, decode_responses=False)
        self._prefix = "aml:"
        self._connected = False
        try:
            self._client.ping()
            self._connected = True
        except Exception:
            pass

    @property
    def connected(self) -> bool:
        return self._connected

    def get(self, key: str) -> tuple[Any | None, bool]:
        try:
            raw = self._client.get(self._prefix + key)
            if raw is None:
                return None, False
            return pickle.loads(raw), True
        except Exception:
            return None, False

    def set(self, key: str, value: Any, ttl: float) -> None:
        try:
            self._client.setex(
                self._prefix + key,
                int(ttl),
                pickle.dumps(value),
            )
        except Exception:
            pass

    def delete(self, key: str) -> None:
        try:
            self._client.delete(self._prefix + key)
        except Exception:
            pass

    def clear(self) -> None:
        try:
            keys = self._client.keys(self._prefix + "*")
            if keys:
                self._client.delete(*keys)
        except Exception:
            pass

    def size(self) -> int:
        try:
            return len(self._client.keys(self._prefix + "*"))
        except Exception:
            return 0

    def info(self) -> dict[str, Any]:
        try:
            raw = self._client.info()
            return {
                "used_memory_human": raw.get("used_memory_human", "N/A"),
                "connected_clients": raw.get("connected_clients", 0),
                "total_commands_processed": raw.get("total_commands_processed", 0),
                "keyspace_hits": raw.get("keyspace_hits", 0),
                "keyspace_misses": raw.get("keyspace_misses", 0),
                "uptime_seconds": raw.get("uptime_in_seconds", 0),
            }
        except Exception:
            return {}


# ---------------------------------------------------------------------------
# Cache region
# ---------------------------------------------------------------------------

class CacheRegion:
    """A named cache region with its own TTL policy and counters."""

    def __init__(self, name: str, ttl_seconds: float, backend: Any) -> None:
        self.name = name
        self.ttl_seconds = ttl_seconds
        self._backend = backend
        self.total_hits = 0
        self.total_misses = 0
        self.total_sets = 0
        self._latency_saved_ms: list[float] = []

    def _region_key(self, key: str) -> str:
        return f"{self.name}:{key}"

    def get(self, key: str) -> Any | None:
        t0 = time.time()
        value, hit = self._backend.get(self._region_key(key))
        elapsed_ms = (time.time() - t0) * 1000
        if hit:
            self.total_hits += 1
            self._latency_saved_ms.append(elapsed_ms)
            return value
        self.total_misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        self._backend.set(self._region_key(key), value, self.ttl_seconds)
        self.total_sets += 1

    def invalidate(self, key: str) -> None:
        self._backend.delete(self._region_key(key))

    def clear(self) -> None:
        self._backend.clear()

    @property
    def stats(self) -> dict[str, Any]:
        total = self.total_hits + self.total_misses
        return {
            "region": self.name,
            "hits": self.total_hits,
            "misses": self.total_misses,
            "sets": self.total_sets,
            "hit_rate": round(self.total_hits / max(total, 1), 3),
            "total_requests": total,
            "ttl_seconds": self.ttl_seconds,
            "avg_latency_ms": round(
                sum(self._latency_saved_ms) / max(len(self._latency_saved_ms), 1), 3
            ),
        }


# ---------------------------------------------------------------------------
# Cache manager
# ---------------------------------------------------------------------------

class CacheManager:
    """Central cache manager with named regions and dual-backend support.

    Regions and their TTLs:
      - triage:          1 hour   (classification results for similar patterns)
      - watchlist:       24 hours (sanctions/PEP lists update daily)
      - entity_graph:    1 hour   (relationship graphs evolve slowly)
      - behavioral:      4 hours  (baselines shift over trading day)
      - report_template: 7 days   (templates rarely change)
    """

    DEFAULT_REGIONS = {
        "triage": 3600,
        "watchlist": 86400,
        "entity_graph": 3600,
        "behavioral": 14400,
        "report_template": 604800,
    }

    def __init__(self) -> None:
        self.backend_type = "memory"
        self._redis_backend: RedisBackend | None = None

        if REDIS_URL:
            try:
                rb = RedisBackend(REDIS_URL)
                if rb.connected:
                    self._backend = rb
                    self._redis_backend = rb
                    self.backend_type = "redis"
                    print(f"Cache: Redis connected ({REDIS_URL})")
                else:
                    self._backend = MemoryBackend()
                    print("Cache: Redis unavailable, using in-memory")
            except Exception:
                self._backend = MemoryBackend()
                print("Cache: Redis import failed, using in-memory")
        else:
            self._backend = MemoryBackend()

        self.regions: dict[str, CacheRegion] = {}
        for name, ttl in self.DEFAULT_REGIONS.items():
            self.regions[name] = CacheRegion(name, ttl, self._backend)

    def get(self, region: str, key: str) -> Any | None:
        r = self.regions.get(region)
        if r is None:
            return None
        return r.get(key)

    def set(self, region: str, key: str, value: Any) -> None:
        r = self.regions.get(region)
        if r is None:
            self.regions[region] = CacheRegion(region, 3600, self._backend)
            r = self.regions[region]
        r.set(key, value)

    def make_key(self, *parts: Any) -> str:
        raw = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @property
    def stats(self) -> list[dict[str, Any]]:
        return [r.stats for r in self.regions.values()]

    @property
    def summary(self) -> dict[str, Any]:
        all_stats = self.stats
        total_hits = sum(s["hits"] for s in all_stats)
        total_misses = sum(s["misses"] for s in all_stats)
        total = total_hits + total_misses
        return {
            "backend": self.backend_type,
            "regions": len(self.regions),
            "total_hits": total_hits,
            "total_misses": total_misses,
            "overall_hit_rate": round(total_hits / max(total, 1), 3),
            "total_requests": total,
            "redis_info": self._redis_backend.info() if self._redis_backend else None,
        }

    def clear_all(self) -> None:
        for r in self.regions.values():
            r.clear()


cache = CacheManager()
