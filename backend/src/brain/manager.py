"""Brain Manager: routes requests to replaceable providers."""

from __future__ import annotations

from typing import Dict, Optional

from logger import get_logger

from .providers.base import BrainProvider


class BrainManager:
    """Selects and invokes the best provider for each task type."""

    def __init__(
        self,
        default_provider: str,
        routing: Optional[Dict[str, str]] = None,
    ):
        self.logger = get_logger("src.brain.manager")
        self.default_provider = default_provider
        self.routing = routing or {}
        self.providers: Dict[str, BrainProvider] = {}

    def register_provider(self, provider: BrainProvider) -> None:
        self.providers[provider.name] = provider
        self.logger.info("Registered brain provider: %s", provider.name)

    def resolve_provider(self, task_type: str = "default") -> BrainProvider:
        provider_name = self.routing.get(task_type, self.default_provider)
        provider = self.providers.get(provider_name)
        if provider:
            return provider
        fallback = self.providers.get(self.default_provider)
        if fallback:
            return fallback
        raise RuntimeError("No brain providers registered")

    def think(self, prompt: str, task_type: str = "default") -> str:
        provider = self.resolve_provider(task_type=task_type)
        self.logger.debug("Routing task '%s' to provider '%s'", task_type, provider.name)
        return provider.think(prompt, context={"task_type": task_type})