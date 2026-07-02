"""Abstract port defining memory operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MemoryPort(ABC):
    """Contract for any memory implementation."""

    @abstractmethod
    def store(self, speaker: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a conversation entry."""

    @abstractmethod
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent conversation entries."""

    @abstractmethod
    def count(self) -> int:
        """Return total stored entries."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries."""