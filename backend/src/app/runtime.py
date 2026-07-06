import os
from typing import Any, Dict, List, Optional

from core import initialize_jarvis
from logger import get_logger

from src.brain import BrainManager
from src.brain.providers import LegacyCoreProvider
from src.brain.providers.openrouter import OpenRouterProvider
from src.brain.model_router import create_router
from src.heartbeat import EventBus, HeartbeatScheduler
from src.interfaces import InterfaceHub
from src.security import AuditLogger, AuthorizationService
from src.memory import MemoryPort
from src.memory.sqlite_adapter import SqliteMemoryAdapter
from src.skills import SkillPort
from src.skills.legacy_adapter import LegacySkillAdapter
from src.tools import ToolManager, FilesystemTool, DateTimeTool, TerminalTool, SearchTool, GitTool, SystemInfoTool, WebTool, AppTool, ClipboardTool, ScreenshotTool, NotificationTool, MemoryTool, MediaTool, EmailTool, CalendarTool, RouterTool, CodeTool, PhoneTool, SystemControlTool, TimerTool
from src.tools.security import SecurityManager

_runtime_instance = None


class JarvisRuntime:
    def __init__(self, config_path="config.yaml"):
        self.logger = get_logger("src.app.runtime")
        self.core = initialize_jarvis(config_path)
        self.brain = BrainManager(
            default_provider="openrouter",
            routing={"default": "openrouter", "smart_home": "legacy_core"},
        )
        self.brain.register_provider(LegacyCoreProvider(self.core))

        openrouter_key = self.core.config.get("jarvis.brain.openrouter_api_key", "")
        if not openrouter_key:
            openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        if openrouter_key:
            default_model = self.core.config.get("jarvis.brain.openrouter_model", "openai/gpt-4o-mini")
            router = create_router(default_model=default_model)

            tool_manager = ToolManager()
            tool_manager.security = SecurityManager()
            tool_manager.register(FilesystemTool())
            tool_manager.register(DateTimeTool())
            tool_manager.register(TerminalTool())
            tool_manager.register(SearchTool())
            tool_manager.register(GitTool())
            tool_manager.register(SystemInfoTool())
            tool_manager.register(WebTool())
            tool_manager.register(AppTool())
            tool_manager.register(ClipboardTool())
            tool_manager.register(ScreenshotTool())
            tool_manager.register(NotificationTool())
            tool_manager.register(MemoryTool())
            tool_manager.register(MediaTool())
            tool_manager.register(EmailTool())
            tool_manager.register(CalendarTool())
            tool_manager.register(RouterTool(router))
            tool_manager.register(CodeTool())
            tool_manager.register(PhoneTool())
            tool_manager.register(SystemControlTool())
            tool_manager.register(TimerTool())

            provider = OpenRouterProvider(
                api_key=openrouter_key,
                model=default_model,
                router=router,
            )
            provider.tool_manager = tool_manager
            self.brain.register_provider(provider)
            print("[RUNTIME] OpenRouter provider with " + str(len(tool_manager.get_definitions())) + " tools", flush=True)

        telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if telegram_token:
            from src.interfaces.telegram_bot import start_telegram_bot
            start_telegram_bot(telegram_token, self)
            print("[RUNTIME] Telegram bot conectado", flush=True)

        self.security = AuthorizationService(
            require_explicit_approval=self.core.config.get("jarvis.security.require_explicit_approval", True),
            approval_prefix=self.core.config.get("jarvis.security.approval_prefix", "approve:"),
        )
        self.audit = AuditLogger(path=self.core.config.get("jarvis.security.audit_log_file", "logs/audit.log"))
        self.interfaces = InterfaceHub()
        self.events = EventBus()
        self.heartbeat = HeartbeatScheduler(self.events)
        self.memory_port = SqliteMemoryAdapter(self.core.memory)
        self.skill_port = LegacySkillAdapter(self.core)

    def get_status(self):
        return self.core.get_status()

    def process_user_input(self, text):
        response = self.core.process_user_input(text)
        if hasattr(response, '__await__'):
            import asyncio
            response = asyncio.get_event_loop().run_until_complete(response)
        response = str(response)
        self.audit.record("user_input_processed", {"text_size": len(text), "response_size": len(response)})
        return response

    def get_conversation_history(self, limit=None):
        return self.core.get_conversation_history(limit)

    def clear_conversation_history(self):
        self.core.clear_conversation_history()

    def execute_smart_home_command(self, **kwargs):
        result = self.core.execute_smart_home_command(**kwargs)
        self.audit.record("smart_home_command", kwargs)
        return result

    def reload_custom_skills(self):
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

    def get_performance_metrics(self):
        return self.core.get_performance_metrics()

    @property
    def name(self):
        return self.core.name

    @property
    def version(self):
        return self.core.version

    def chat(self, text):
        print("[RUNTIME] chat called: " + text[:60], flush=True)
        try:
            response = self.brain.think(text, task_type="default")
            self.audit.record("text_processed", {"text_size": len(text), "response_size": len(response)})
            return response
        except Exception as e:
            self.logger.error("LLM error, falling back to legacy: %s", e)
            print("[RUNTIME] FALLBACK to legacy: " + str(e), flush=True)
            return self.process_user_input(text)


def initialize_runtime(config_path="config.yaml"):
    global _runtime_instance
    _runtime_instance = JarvisRuntime(config_path)
    return _runtime_instance


def get_runtime():
    return _runtime_instance