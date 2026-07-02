"""Provider bridge for the current core engine."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BrainProvider


class LegacyCoreProvider(BrainProvider):
    """Wrap current core while the architecture migrates."""

    name = "legacy_core"

    def __init__(self, jarvis_core):
        self.jarvis_core = jarvis_core

    def think(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        return self.jarvis_core.process_user_input(prompt)