"""Abstract port defining skill operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class SkillPort(ABC):
    """Contract for any skill registry implementation."""

    @abstractmethod
    def list_skills(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered skills."""

    @abstractmethod
    def process(self, text: str, intent: Optional[str] = None) -> Optional[str]:
        """Route text to the appropriate skill and return the response."""

    @abstractmethod
    def reload(self) -> List[str]:
        """Reload dynamic/custom skills. Return list of loaded names."""