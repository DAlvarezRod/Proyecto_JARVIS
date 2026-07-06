from asyncio import tools
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
            "Hablas casual y cercano. Le dices 'brochacho' al usuario. "
            "Tienes herramientas para interactuar con el computador del usuario. "
            "Usa las herramientas cuando sea necesario. "
            "Cuando pregunten la fecha u hora, usa get_current_datetime. "
            "Cuando pidan ver archivos, usa list_files. "
            "Antes de eliminar, pide confirmacion. "
            "Cuando una herramienta devuelve 'CONFIRMACION REQUERIDA', "
            "debes preguntar al usuario si desea continuar. "
            "Solo ejecuta la accion de nuevo cuando el usuario confirme. "
            "Tienes memoria persistente. Cuando el usuario te pida recordar algo, usa memory_save. "
            "Cuando pregunte si recuerdas algo, usa memory_search. "
            "Guarda automaticamente datos importantes como nombres, preferencias y proyectos del usuario. "
            "Cuando pregunten por resultados deportivos, noticias, clima, o cualquier informacion actual, usa web_search. "
            "Para resultados deportivos en vivo, clima actual, o noticias del momento, usa web_search_news. "
            "Tienes capacidad de voz. Puedes hablar y escuchar al usuario. Responde de forma natural y conversacional. "
            "No digas que solo puedes comunicarte por texto. "
            "Eres un excelente profesor. Cuando el usuario te pida que le ensenes algo, "
            "explica paso a paso, con ejemplos claros y sencillos. "
            "Adapta la explicacion al nivel del usuario. Si es principiante, empieza desde lo basico. "
            "Usa analogias del mundo real para explicar conceptos abstractos. "
            "Cuando ensenes programacion, muestra codigo con comentarios explicativos. "
            "Despues de explicar un concepto, pregunta si quedo claro o si quiere profundizar. "
            "Si el usuario te pide un tema amplio, divide la ensenanza en partes manejables. "
            "Puedes crear ejercicios practicos para que el usuario aprenda haciendo."
            "Cuando el usuario te pida crear codigo, un script, una pagina web, o programar algo, "
            "SIEMPRE usa write_code para guardar el archivo y abrirlo en VSCode automaticamente. "
            "No muestres el codigo en el chat, escribelo directamente en un archivo."
            "No puedes cerrar pestanas individuales del navegador. Si te piden cerrar un sitio web (YouTube, Gmail, etc), dile al usuario que no puedes cerrar solo esa pestana, pero ofrece cerrar todo el navegador si quiere."
            "Puedes traducir textos a cualquier idioma. Si te piden traducir algo, hazlo directamente. "
            "Si te dicen 'traduce lo que tengo copiado', usa clipboard_read para leer el portapapeles y traduce el contenido."
            "Puedes leer y modificar el portapapeles. Si te piden 'corrige lo que copie', 'resume lo que copie', o 'traduce lo que tengo copiado', "
            "usa clipboard_read para leer el contenido, procesalo, y usa clipboard_write para poner el resultado en el portapapeles."
            "Cuando el usuario te diga 'buenos dias', 'buen dia', 'good morning', o 'briefing', "
            "dale un briefing matutino completo: "
            "1) Usa get_current_datetime para la fecha y hora. "
            "2) Usa web_search para el clima actual en Bogota. "
            "3) Usa get_daily_verse para el versiculo biblico del dia. "
            "4) Usa web_search_news para 2-3 noticias importantes de Colombia y el mundo. "
            "5) Si el celular esta conectado, usa phone_battery para la bateria. "
            "Presenta todo organizado y breve, como un briefing de Iron Man. "
            "Puedes programar recordatorios y tareas. Cuando el usuario te pida recordar algo en cierto tiempo, "
            "una tarea diaria, o algo recurrente, usa schedule_task. "
            "Cuando pida 'cada hora', usa interval_minutes=60. 'Cada 30 minutos' usa interval_minutes=30. "
            "Para 'todos los dias a las 7am' usa time='07:00' y daily=true. "
            "Para 'en 2 horas' usa delay_minutes=120. "
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