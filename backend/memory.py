"""Persistent conversation memory for JARVIS."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import get_logger


class ConversationMemory:
    """SQLite-backed conversation storage."""

    def __init__(self, db_path: str = "data/conversations.db"):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("memory")
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    speaker TEXT NOT NULL,
                    text TEXT NOT NULL,
                    intent_type TEXT,
                    confidence REAL,
                    latency_ms REAL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversation_timestamp "
                "ON conversation_messages(timestamp)"
            )
            conn.commit()
        finally:
            conn.close()

    def add_message(
        self,
        speaker: str,
        text: str,
        timestamp: str,
        intent_type: Optional[str] = None,
        confidence: Optional[float] = None,
        latency_ms: Optional[float] = None,
    ) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO conversation_messages
                    (speaker, text, intent_type, confidence, latency_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (speaker, text, intent_type, confidence, latency_ms, timestamp),
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        query = (
            "SELECT speaker, text, intent_type, confidence, latency_ms, timestamp "
            "FROM conversation_messages ORDER BY id DESC"
        )
        params: tuple[Any, ...] = ()
        if limit:
            query += " LIMIT ?"
            params = (limit,)

        conn = self._connect()
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()

        messages = [dict(row) for row in rows]
        messages.reverse()
        return messages

    def count(self) -> int:
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS total FROM conversation_messages").fetchone()
        finally:
            conn.close()
        return int(row["total"])

    def clear(self) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM conversation_messages")
            conn.commit()
        finally:
            conn.close()
        self.logger.info("Conversation memory cleared")
