import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from .base import BrainProvider


class OpenRouterProvider(BrainProvider):
    name = "openrouter"

    def __init__(self, api_key, model="openai/gpt-4o-mini", max_tokens=1024, router=None):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.router = router
        self.system_prompt = (
            "Eres Illo, un asistente de IA avanzado creado por David Alvarez. "
            "Respondes siempre en espanol. Eres util, preciso y amigable. "
            "Tienes herramientas para interactuar con el computador del usuario. "
            "Usa las herramientas cuando sea necesario. "
            "Cuando pregunten la fecha u hora, usa get_current_datetime. "
            "Cuando pidan ver archivos, usa list_files. "
            "Antes de eliminar, pide confirmacion."
            "Cuando una herramienta devuelve 'CONFIRMACION REQUERIDA', "
            "debes preguntar al usuario si desea continuar. "
            "Solo ejecuta la accion de nuevo cuando el usuario confirme."
            "Tienes memoria persistente. Cuando el usuario te pida recordar algo, usa memory_save. "
            "Cuando pregunte si recuerdas algo, usa memory_search. "
            "Guarda automaticamente datos importantes como nombres, preferencias y proyectos del usuario."
            "Cuando pregunten por resultados deportivos, noticias, clima, o cualquier informacion actual, usa web_search. "
            "Para resultados deportivos en vivo, clima actual, o noticias del momento, usa web_search_news. "
        )
        self.conversation_history = []
        self.tool_manager = None

    def _call_api(self, messages, tools=None):
        if self.router:
            return self.router.chat(messages, tools, self.max_tokens)

        body = {"model": self.model, "messages": messages, "max_tokens": self.max_tokens}
        if tools:
            body["tools"] = tools
        payload = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
                "HTTP-Referer": "https://github.com/DAlvarezRod/Proyecto_JARVIS",
                "X-Title": "Illo AI Assistant",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def think(self, prompt, context=None):
        print("[ILLO-THINK] prompt: " + prompt[:60], flush=True)
        self.conversation_history.append({"role": "user", "content": prompt})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        messages = [{"role": "system", "content": self.system_prompt}] + list(self.conversation_history)

        tools = None
        if self.tool_manager:
            tools = self.tool_manager.get_definitions()
            print("[ILLO-THINK] tools count: " + str(len(tools)), flush=True)

        try:
            for iteration in range(10):
                print("[ILLO-THINK] calling API iteration " + str(iteration), flush=True)
                data = self._call_api(messages, tools)
                print("[ILLO-THINK] response keys: " + str(list(data.keys())), flush=True)

                if "error" in data:
                    err = data["error"]
                    msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                    return "[Illo error]: " + msg

                if "choices" not in data or not data["choices"]:
                    print("[ILLO-THINK] no choices in response: " + json.dumps(data)[:300], flush=True)
                    return "[Illo]: El modelo no respondio. Intenta de nuevo."

                message = data["choices"][0]["message"]
                tool_calls = message.get("tool_calls")

                if tool_calls and self.tool_manager:
                    print("[ILLO-THINK] tool calls: " + str(len(tool_calls)), flush=True)
                    messages.append(message)
                    for tc in tool_calls:
                        fn_name = tc["function"]["name"]
                        try:
                            fn_args = json.loads(tc["function"]["arguments"])
                        except json.JSONDecodeError:
                            fn_args = {}
                        print("[ILLO-THINK] executing tool: " + fn_name, flush=True)
                        result = self.tool_manager.execute(fn_name, fn_args)
                        messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
                    continue

                reply = message.get("content", "")
                self.conversation_history.append({"role": "assistant", "content": reply})
                return reply

            return "[Illo]: Demasiadas iteraciones."

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print("[ILLO-THINK] HTTP error: " + str(e.code) + " " + body[:200], flush=True)
            return "[Illo HTTP error " + str(e.code) + "]: " + body[:200]
        except Exception as e:
            print("[ILLO-THINK] exception: " + str(e), flush=True)
            return "[Illo exception]: " + str(e)