"""Composes modular architecture while preserving current behavior."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

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
            default_provider=self.core.config.get(
                "jarvis.brain.default_provider", "legacy_core"
            ),
            routing=self.core.config.get("jarvis.brain.routing", {}),
        )
        self.brain.register_provider(LegacyCoreProvider(self.core))

        self.security = AuthorizationService(
            require_explicit_approval=self.core.config.get(
                "jarvis.security.require_explicit_approval", True,
            ),
            approval_prefix=self.core.config.get(
                "jarvis.security.approval_prefix", "approve:",
            ),
        )
        self.audit = AuditLogger(
            path=self.core.config.get(
                "jarvis.security.audit_log_file", "logs/audit.log"
            )
        )
        self.interfaces = InterfaceHub()
        self.events = EventBus()
        self.heartbeat = HeartbeatScheduler(self.events)

    # --- Delegated API (server.py uses these instead of core directly) ---

    def get_status(self) -> Dict[str, Any]:
        return self.core.get_status()

    def process_user_input(self, text: str) -> str:
        response = self.core.process_user_input(text)
        self.audit.record(
            "user_input_processed",
            {"text_size": len(text), "response_size": len(response)},
        )
        return response

    def get_conversation_history(self, limit: int = None) -> List[Dict[str, str]]:
        return self.core.get_conversation_history(limit)

    def clear_conversation_history(self) -> None:
        self.core.clear_conversation_history()

    def execute_smart_home_command(self, **kwargs) -> Dict[str, Any]:
        result = self.core.execute_smart_home_command(**kwargs)
        self.audit.record("smart_home_command", kwargs)
        return result

    def reload_custom_skills(self) -> List[str]:
        return self.core.reload_custom_skills()

    @property
    def skill_registry(self):
        return self.core.skill_registry

    @property
    def custom_skill_loader(self):
        return self.core.custom_skill_loader

    @property
    def smart_home(self):
        return self.core.smart_home

    @property
    def memory(self):
        return self.core.memory

    @property
    def automation(self):
        return self.core.automation

    @property
    def config(self):
        return self.core.config

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


def get_runtime() -> Optional[JarvisRuntime]:
    return _runtime_instance