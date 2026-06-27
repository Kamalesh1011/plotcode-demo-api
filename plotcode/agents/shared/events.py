"""
In-memory EventBus for WebSocket broadcasting.

Agents publish events after every state change.
The FastAPI WebSocket handler delivers them to connected dashboard clients.

For single-instance deployments (the standard case for this system), this
in-memory bus is sufficient. A Redis pub/sub adapter can be swapped in for
multi-instance deployments without changing the publisher/subscriber contract.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """A single system event."""
    type: str               # e.g. "request.status_changed", "agent.completed"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self))


# ─── Event Type Constants ─────────────────────────────────────────────────────

class EventTypes:
    REQUEST_CREATED       = "request.created"
    REQUEST_UPDATED       = "request.updated"
    REQUEST_APPROVED      = "request.approved"
    REQUEST_REJECTED      = "request.rejected"
    PLAN_GENERATED        = "agent.plan_generated"
    PLAN_APPROVED         = "request.plan_approved"
    CODE_APPLIED          = "agent.code_applied"
    CI_STARTED            = "ci.started"
    CI_PASSED             = "ci.passed"
    CI_FAILED             = "ci.failed"
    CI_FIX_APPLIED        = "agent.ci_fix_applied"
    PR_CREATED            = "agent.pr_created"
    PR_MERGED             = "request.pr_merged"
    QA_DEPLOYED           = "deploy.qa_deployed"
    QA_APPROVED           = "request.qa_approved"
    QA_FAILED             = "request.qa_failed"
    PROD_APPROVED         = "request.prod_approved"
    PROD_DEPLOYED         = "deploy.prod_deployed"
    REQUEST_CLOSED        = "request.closed"
    SLA_BREACHED          = "sla.breached"
    AGENT_ERROR           = "agent.error"
    HEALTH_CHECK          = "monitoring.health_check"


# ─── EventBus ─────────────────────────────────────────────────────────────────

class EventBus:
    """
    Async in-memory pub/sub bus.

    Usage:
        # Publisher (from sync agent code):
        event_bus.publish_sync(EventTypes.REQUEST_CREATED, {"request_id": "..."})

        # Subscriber (FastAPI WebSocket):
        async with event_bus.subscribe() as queue:
            event = await queue.get()
            await ws.send_text(event.to_json())
    """

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Async publish — use inside async FastAPI code."""
        event = Event(type=event_type, payload=payload)
        dead: List[asyncio.Queue] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(queue)
        for q in dead:
            self._subscribers.discard(q)
        logger.debug(f"[EventBus] Published {event_type} to {len(self._subscribers)} subscribers")

    def publish_sync(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Sync publish — safe to call from agent background threads.
        Finds the running event loop and schedules the coroutine.
        Falls back to a no-op if no event loop is running.
        """
        event = Event(type=event_type, payload=payload)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(self._put_to_all, event)
            else:
                logger.debug(f"[EventBus] No running loop — event {event_type} dropped")
        except RuntimeError:
            pass

    def _put_to_all(self, event: Event) -> None:
        """Called in event loop thread via call_soon_threadsafe."""
        dead: List[asyncio.Queue] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(queue)
        for q in dead:
            self._subscribers.discard(q)

    async def subscribe(self) -> asyncio.Queue:
        """
        Add a subscriber queue. Caller is responsible for removing it.
        Returns the queue to receive events from.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


# ─── Singleton ────────────────────────────────────────────────────────────────

_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
