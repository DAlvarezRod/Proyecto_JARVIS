"""Unified interface contracts for console/mic/discord/telegram."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

from logger import get_logger


@dataclass
class InboundMessage:
    channel: str
    user_id: str
    text: str


class ChannelAdapter(ABC):
    """Transport adapter with no business logic."""

    name: str

    @abstractmethod
    async def send(self, user_id: str, text: str) -> None:
        raise NotImplementedError


class InterfaceHub:
    """Registry and fan-out helper for channel adapters."""

    def __init__(self):
        self.logger = get_logger("src.interfaces.hub")
        self.adapters: Dict[str, ChannelAdapter] = {}

    def register(self, adapter: ChannelAdapter) -> None:
        self.adapters[adapter.name] = adapter
        self.logger.info("Registered interface adapter: %s", adapter.name)

