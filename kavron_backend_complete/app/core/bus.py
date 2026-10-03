from __future__ import annotations
import asyncio
from collections import defaultdict
from typing import Any

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subscribers[topic].add(q)
        return q

    async def unsubscribe(self, topic: str, q: asyncio.Queue) -> None:
        async with self._lock:
            self._subscribers[topic].discard(q)

    async def publish(self, event: dict[str, Any]) -> None:
        topics = {"*", event.get("type", "event")}
        async with self._lock:
            targets = [q for topic in topics for q in self._subscribers.get(topic, set())]
        for q in targets:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    _ = q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    pass
