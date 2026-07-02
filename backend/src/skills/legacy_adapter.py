"""Adapter that wraps the existing skill system behind SkillPort."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .port import SkillPort


class LegacySkillAdapter(SkillPort):
    """Wraps legacy core skill_registry and custom_skill_loader."""

    def __init__(self, jarvis_core):
        self._core = jarvis_core

    def list_skills(self) -> List[Dict[str, Any]]:
        built_in = self._core.skill_registry.list_skills()
        custom = self._core.custom_skill_loader.discover()
        if isinstance(built_in, dict):
            built_in = [{"name": k, **v} if isinstance(v, dict) else {"name": k, "info": v} for k, v in built_in.items()]
        if isinstance(custom, dict):
            custom = [{"name": k, **v} if isinstance(v, dict) else {"name": k, "info": v} for k, v in custom.items()]
        return built_in + custom

    def process(self, text: str, intent: Optional[str] = None) -> Optional[str]:
        return self._core.process_user_input(text)

    def reload(self) -> List[str]:
        return self._core.reload_custom_skills()