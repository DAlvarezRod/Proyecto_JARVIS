"""Event bus and lightweight scheduler foundation."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List

from logger import get_logger

Handler = Callable[[Dict[str, Any]], Awaitable[None]]


class EventBus:
    def __init__(self):
        self.logger = get_logger("src.heartbeat.bus")
        self._subs: Dict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subs[event_type].append(handler)

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        handlers = self._subs.get(event_type, [])
        if not handlers:
            return
        await asyncio.gather(*(handler(payload) for handler in handlers), return_exceptions=False)


class HeartbeatScheduler:
    """Simple periodic scheduler for future automations/events."""

    def __init__(self, bus: EventBus):
        self.logger = get_logger("src.heartbeat.scheduler")
        self.bus = bus
        self._tasks: List[asyncio.Task] = []

    def every(self, event_type: str, seconds: float, payload: Dict[str, Any]) -> None:
        async def _runner() -> None:
            while True:
                await self.bus.publish(event_type, payload)
                await asyncio.sleep(seconds)

        self._tasks.append(asyncio.create_task(_runner()))

    def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        self._tasks = []

