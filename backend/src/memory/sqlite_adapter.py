"""Adapter that wraps the existing SQLite memory behind MemoryPort."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .port import MemoryPort


class SqliteMemoryAdapter(MemoryPort):
    """Wraps legacy memory.ConversationMemory to satisfy MemoryPort."""

    def __init__(self, legacy_memory):
        self._legacy = legacy_memory

    def store(self, speaker: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self._legacy.add(speaker, text)

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._legacy.get_recent(limit)

    def count(self) -> int:
        return self._legacy.count()

    def clear(self) -> None:
        self._legacy.clear()