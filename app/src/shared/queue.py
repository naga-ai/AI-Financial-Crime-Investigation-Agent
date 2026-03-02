"""Event queue with Redis Streams backend and in-memory fallback.

Provides priority-based queuing, consumer groups, dead letter queue,
backpressure management, and idempotency for financial event processing.
Both WS Clarity (alerts) and WS Pilot (financial events) use this.
"""

from __future__ import annotations

import enum
import hashlib
import json
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.config import REDIS_URL
from src.observability.telemetry import telemetry_bus, EventType


class Priority(str, enum.Enum):
    HIGH = "high"       # fraud alerts, market crashes
    MEDIUM = "medium"   # earnings, rate changes
    LOW = "low"         # paychecks, rebalance reminders


class EventStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DLQ = "dead_letter"


@dataclass
class QueueEvent:
    event_id: str
    event_type: str
    payload: dict[str, Any]
    priority: Priority
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = ""
    processed_at: str | None = None
    error: str | None = None
    dedup_hash: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.dedup_hash:
            content = json.dumps(self.payload, sort_keys=True, default=str)
            self.dedup_hash = hashlib.sha256(
                f"{self.event_type}:{content}".encode()
            ).hexdigest()[:16]


@dataclass
class QueueHealth:
    total_enqueued: int = 0
    total_processed: int = 0
    total_failed: int = 0
    dlq_size: int = 0
    pending_by_priority: dict[str, int] = field(default_factory=dict)
    avg_processing_time_ms: float = 0.0
    backpressure_active: bool = False
    consumer_lag: int = 0


class MemoryQueueBackend:
    """In-memory queue for local development and testing."""

    def __init__(self, max_depth: int = 10000):
        self._queues: dict[str, deque[QueueEvent]] = {
            Priority.HIGH.value: deque(),
            Priority.MEDIUM.value: deque(),
            Priority.LOW.value: deque(),
        }
        self._dlq: deque[QueueEvent] = deque()
        self._seen_hashes: set[str] = set()
        self._processing_times: list[float] = []
        self._max_depth = max_depth
        self._total_enqueued = 0
        self._total_processed = 0
        self._total_failed = 0
        self._backpressure_threshold = int(max_depth * 0.8)

    def enqueue(self, event: QueueEvent) -> bool:
        if event.dedup_hash in self._seen_hashes:
            return False

        total_depth = sum(len(q) for q in self._queues.values())
        if total_depth >= self._backpressure_threshold:
            if event.priority == Priority.LOW:
                return False

        self._queues[event.priority.value].append(event)
        self._seen_hashes.add(event.dedup_hash)
        self._total_enqueued += 1
        return True

    def dequeue(self, consumer_group: str = "default") -> QueueEvent | None:
        for priority in [Priority.HIGH.value, Priority.MEDIUM.value, Priority.LOW.value]:
            q = self._queues[priority]
            if q:
                event = q.popleft()
                event.status = EventStatus.PROCESSING
                return event
        return None

    def ack(self, event: QueueEvent, processing_time_ms: float = 0.0) -> None:
        event.status = EventStatus.COMPLETED
        event.processed_at = datetime.utcnow().isoformat()
        self._total_processed += 1
        if processing_time_ms > 0:
            self._processing_times.append(processing_time_ms)
            if len(self._processing_times) > 1000:
                self._processing_times = self._processing_times[-500:]

    def nack(self, event: QueueEvent, error: str = "", retry: bool = True) -> None:
        event.error = error
        event.retry_count += 1
        self._total_failed += 1

        if retry and event.retry_count < event.max_retries:
            event.status = EventStatus.PENDING
            self._queues[event.priority.value].appendleft(event)
        else:
            event.status = EventStatus.DLQ
            self._dlq.append(event)
            telemetry_bus.emit(
                EventType.QUEUE_DLQ,
                metadata={"event_id": event.event_id, "event_type": event.event_type, "error": error},
                component="queue",
            )

    @property
    def health(self) -> QueueHealth:
        pending = {
            p.value: len(self._queues[p.value])
            for p in Priority
        }
        total_depth = sum(pending.values())
        avg_time = (
            sum(self._processing_times) / len(self._processing_times)
            if self._processing_times else 0.0
        )
        return QueueHealth(
            total_enqueued=self._total_enqueued,
            total_processed=self._total_processed,
            total_failed=self._total_failed,
            dlq_size=len(self._dlq),
            pending_by_priority=pending,
            avg_processing_time_ms=round(avg_time, 2),
            backpressure_active=total_depth >= self._backpressure_threshold,
            consumer_lag=total_depth,
        )

    @property
    def dlq_events(self) -> list[QueueEvent]:
        return list(self._dlq)


class RedisQueueBackend:
    """Redis Streams backend for production deployment."""

    def __init__(self, url: str, stream_prefix: str = "ws:events:"):
        import redis
        self._client = redis.from_url(url, decode_responses=True)
        self._prefix = stream_prefix
        self._dlq_key = f"{stream_prefix}dlq"
        self._dedup_key = f"{stream_prefix}dedup"
        self._connected = False
        self._total_enqueued = 0
        self._total_processed = 0
        self._total_failed = 0
        self._processing_times: list[float] = []
        self._backpressure_threshold = 8000

        try:
            self._client.ping()
            self._connected = True
            for priority in Priority:
                stream_key = f"{self._prefix}{priority.value}"
                try:
                    self._client.xgroup_create(stream_key, "workers", id="0", mkstream=True)
                except Exception:
                    pass
        except Exception:
            self._connected = False

    def enqueue(self, event: QueueEvent) -> bool:
        if not self._connected:
            return False

        if self._client.sismember(self._dedup_key, event.dedup_hash):
            return False

        stream_key = f"{self._prefix}{event.priority.value}"
        data = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "payload": json.dumps(event.payload, default=str),
            "priority": event.priority.value,
            "created_at": event.created_at,
            "dedup_hash": event.dedup_hash,
        }

        self._client.xadd(stream_key, data)
        self._client.sadd(self._dedup_key, event.dedup_hash)
        self._total_enqueued += 1
        return True

    def dequeue(self, consumer_group: str = "workers") -> QueueEvent | None:
        if not self._connected:
            return None

        for priority in Priority:
            stream_key = f"{self._prefix}{priority.value}"
            try:
                messages = self._client.xreadgroup(
                    consumer_group, f"consumer-{uuid.uuid4().hex[:8]}",
                    {stream_key: ">"}, count=1, block=0,
                )
                if messages:
                    for stream, entries in messages:
                        for msg_id, data in entries:
                            return QueueEvent(
                                event_id=data.get("event_id", msg_id),
                                event_type=data.get("event_type", "unknown"),
                                payload=json.loads(data.get("payload", "{}")),
                                priority=Priority(data.get("priority", "medium")),
                                status=EventStatus.PROCESSING,
                                created_at=data.get("created_at", ""),
                                dedup_hash=data.get("dedup_hash", ""),
                            )
            except Exception:
                continue
        return None

    def ack(self, event: QueueEvent, processing_time_ms: float = 0.0) -> None:
        self._total_processed += 1
        if processing_time_ms > 0:
            self._processing_times.append(processing_time_ms)

    def nack(self, event: QueueEvent, error: str = "", retry: bool = True) -> None:
        self._total_failed += 1
        if not retry or event.retry_count >= event.max_retries:
            if self._connected:
                self._client.xadd(self._dlq_key, {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "error": error,
                    "retry_count": str(event.retry_count),
                })
            telemetry_bus.emit(
                EventType.QUEUE_DLQ,
                metadata={"event_id": event.event_id, "event_type": event.event_type, "error": error},
                component="queue",
            )

    @property
    def health(self) -> QueueHealth:
        pending: dict[str, int] = {}
        for p in Priority:
            try:
                info = self._client.xinfo_stream(f"{self._prefix}{p.value}")
                pending[p.value] = info.get("length", 0)
            except Exception:
                pending[p.value] = 0

        dlq_size = 0
        try:
            info = self._client.xinfo_stream(self._dlq_key)
            dlq_size = info.get("length", 0)
        except Exception:
            pass

        avg_time = (
            sum(self._processing_times) / len(self._processing_times)
            if self._processing_times else 0.0
        )
        return QueueHealth(
            total_enqueued=self._total_enqueued,
            total_processed=self._total_processed,
            total_failed=self._total_failed,
            dlq_size=dlq_size,
            pending_by_priority=pending,
            avg_processing_time_ms=round(avg_time, 2),
            backpressure_active=sum(pending.values()) >= self._backpressure_threshold,
            consumer_lag=sum(pending.values()),
        )


class EventQueue:
    """Unified event queue with Redis Streams or in-memory fallback."""

    def __init__(self):
        self._backend: MemoryQueueBackend | RedisQueueBackend
        if REDIS_URL:
            try:
                self._backend = RedisQueueBackend(REDIS_URL)
                if isinstance(self._backend, RedisQueueBackend) and self._backend._connected:
                    self._backend_type = "redis_streams"
                else:
                    raise ConnectionError("Redis not reachable")
            except Exception:
                self._backend = MemoryQueueBackend()
                self._backend_type = "memory"
        else:
            self._backend = MemoryQueueBackend()
            self._backend_type = "memory"

    def enqueue(
        self,
        event_type: str,
        payload: dict[str, Any],
        priority: Priority = Priority.MEDIUM,
    ) -> QueueEvent | None:
        event = QueueEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            payload=payload,
            priority=priority,
        )
        success = self._backend.enqueue(event)
        if success:
            telemetry_bus.emit(
                EventType.QUEUE_ENQUEUE,
                metadata={"event_type": event_type, "priority": priority.value},
                component="queue",
            )
        return event if success else None

    def dequeue(self, consumer_group: str = "default") -> QueueEvent | None:
        return self._backend.dequeue(consumer_group)

    def ack(self, event: QueueEvent, processing_time_ms: float = 0.0) -> None:
        self._backend.ack(event, processing_time_ms)

    def nack(self, event: QueueEvent, error: str = "", retry: bool = True) -> None:
        self._backend.nack(event, error, retry)

    @property
    def health(self) -> QueueHealth:
        return self._backend.health

    @property
    def backend_type(self) -> str:
        return self._backend_type


event_queue = EventQueue()
