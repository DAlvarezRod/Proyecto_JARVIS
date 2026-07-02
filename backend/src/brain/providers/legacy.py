"""Provider bridge for the current core JARVIS engine."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BrainProvider


class LegacyCoreProvider(BrainProvider):
    """Wrap current `core.JARVIS` while the architecture migrates."""

    name = "legacy_core"

    def __init__(self, jarvis_core):
        self.jarvis_core = jarvis_core

    async def think(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        _context: Dict[str, Any] = context or {}
        return await self.jarvis_core.process_user_input(prompt)

