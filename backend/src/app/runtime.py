"""Composes modular architecture while preserving current behavior."""

from __future__ import annotations

from typing import Optional

from core import initialize_jarvis
from logger import get_logger

from src.brain import BrainManager
from src.brain.providers import LegacyCoreProvider
from src.heartbeat import EventBus, HeartbeatScheduler
from src.interfaces import InterfaceHub
from src.security import AuditLogger, AuthorizationService

_runtime_instance: Optional["JarvisRuntime"] = None


class JarvisRuntime:
    """Facade that wires modular services around existing core."""

    def __init__(self, config_path: str = "config.yaml"):
        self.logger = get_logger("src.app.runtime")
        self.core = initialize_jarvis(config_path)

        self.brain = BrainManager(
            default_provider=self.core.config.get("jarvis.brain.default_provider", "legacy_core"),
            routing=self.core.config.get("jarvis.brain.routing", {}),
        )
        self.brain.register_provider(LegacyCoreProvider(self.core))

        self.security = AuthorizationService(
            require_explicit_approval=self.core.config.get(
                "jarvis.security.require_explicit_approval",
                True,
            ),
            approval_prefix=self.core.config.get(
                "jarvis.security.approval_prefix",
                "approve:",
            ),
        )
        self.audit = AuditLogger(
            path=self.core.config.get("jarvis.security.audit_log_file", "logs/audit.log")
        )
        self.interfaces = InterfaceHub()
        self.events = EventBus()
        self.heartbeat = HeartbeatScheduler(self.events)

    async def process_text(self, text: str, task_type: str = "default") -> str:
        response = await self.brain.think(text, task_type=task_type)
        self.audit.record(
            "text_processed",
            {"task_type": task_type, "text_size": len(text)},
        )
        return response


def initialize_runtime(config_path: str = "config.yaml") -> JarvisRuntime:
    global _runtime_instance
    _runtime_instance = JarvisRuntime(config_path)
    return _runtime_instance

