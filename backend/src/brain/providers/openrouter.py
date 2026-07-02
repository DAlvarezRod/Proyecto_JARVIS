"""OpenRouter provider — connects Illo to real LLM models."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from .base import BrainProvider


class OpenRouterProvider(BrainProvider):
    """Sends prompts to OpenRouter API and returns LLM responses."""

    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/nemotron-3-ultra-550b-a55b:free",
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or (
            "You are Illo, an advanced AI assistant. "
            "You are helpful, precise, and speak with a professional but friendly tone. "
            "You can assist with smart home control, general questions, calculations, "
            "weather, news, and more. Keep responses concise and useful. "
            "If the user speaks Spanish, respond in Spanish. "
            "Your creator is David Alvarez."
        )
        self.conversation_history: List[Dict[str, str]] = []

    async def think(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        self.conversation_history.append({"role": "user", "content": prompt})

        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
        ] + self.conversation_history

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/DAlvarezRod/Proyecto_JARVIS",
                "X-Title": "Illo AI Assistant",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"]
                self.conversation_history.append({"role": "assistant", "content": reply})
                return reply
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return f"[OpenRouter error {e.code}]: {body[:200]}"
        except Exception as e:
            return f"[OpenRouter connection error]: {str(e)}"