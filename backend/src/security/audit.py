"""Structured security audit logging."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from logger import get_logger


class AuditLogger:
    """Append-only JSONL audit log for sensitive operations."""

    def __init__(self, path: str = "logs/audit.log"):
        self.logger = get_logger("src.security.audit")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, payload: Dict[str, Any]) -> None:
        safe_payload = dict(payload)
        safe_payload.pop("password", None)
        safe_payload.pop("token", None)
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "payload": safe_payload,
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=True) + "\n")
        self.logger.debug("Audit event recorded: %s", event_type)

