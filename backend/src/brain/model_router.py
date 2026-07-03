import json
import os
import urllib.request
import urllib.error


class ModelProvider:
    def __init__(self, name, base_url, api_key, model, extra_headers=None):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.extra_headers = extra_headers or {}
        self.enabled = True

    def call(self, messages, tools=None, max_tokens=1024):
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens}
        if tools:
            body["tools"] = tools
        payload = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key,
        }
        headers.update(self.extra_headers)
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=payload,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))


class ModelRouter:
    def __init__(self):
        self.providers = []
        self.last_used = None

    def add_provider(self, provider):
        self.providers.append(provider)
        print("[ROUTER] Provider: " + provider.name + " (" + provider.model + ")", flush=True)

    def chat(self, messages, tools=None, max_tokens=1024):
        active = [p for p in self.providers if p.enabled]
        if not active:
            raise Exception("No hay proveedores LLM configurados")
        errors = []
        for provider in active:
            try:
                result = provider.call(messages, tools, max_tokens)
                self.last_used = provider.name
                return result
            except Exception as e:
                msg = provider.name + ": " + str(e)
                print("[ROUTER] Fallo " + msg, flush=True)
                errors.append(msg)
        raise Exception("Todos los proveedores fallaron:\n" + "\n".join(errors))

    def list_providers(self):
        return [
            {"name": p.name, "model": p.model, "enabled": p.enabled, "active": p.name == self.last_used}
            for p in self.providers
        ]

    def set_primary(self, name):
        for i, p in enumerate(self.providers):
            if p.name.lower() == name.lower():
                self.providers.insert(0, self.providers.pop(i))
                return True
        return False

    def set_enabled(self, name, enabled):
        for p in self.providers:
            if p.name.lower() == name.lower():
                p.enabled = enabled
                return True
        return False


def create_router(default_model="openai/gpt-4o-mini"):
    router = ModelRouter()

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if openrouter_key:
        model = os.environ.get("OPENROUTER_MODEL", default_model)
        router.add_provider(ModelProvider(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model=model,
            extra_headers={
                "HTTP-Referer": "https://github.com/DAlvarezRod/Proyecto_JARVIS",
                "X-Title": "Illo AI Assistant",
            },
        ))

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        router.add_provider(ModelProvider(
            name="openai",
            base_url="https://api.openai.com/v1",
            api_key=openai_key,
            model=model,
        ))

    if os.environ.get("OLLAMA_ENABLED", "").lower() in ("true", "1", "yes"):
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "llama3.1")
        router.add_provider(ModelProvider(
            name="ollama",
            base_url=ollama_url + "/v1",
            api_key="ollama",
            model=model,
        ))

    if openrouter_key and os.environ.get("CLAUDE_FALLBACK", "").lower() in ("true", "1", "yes"):
        router.add_provider(ModelProvider(
            name="claude-fallback",
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model="anthropic/claude-sonnet-4-20250514",
            extra_headers={
                "HTTP-Referer": "https://github.com/DAlvarezRod/Proyecto_JARVIS",
                "X-Title": "Illo AI Assistant",
            },
        ))

    print("[ROUTER] " + str(len(router.providers)) + " provider(s) ready", flush=True)
    return router