"""Base interface for replaceable reasoning providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BrainProvider(ABC):
    """Interface for any model/provider used by the brain manager."""

    name: str

    @abstractmethod
    def think(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Return a response for the given prompt/context."""
        raise NotImplementedError