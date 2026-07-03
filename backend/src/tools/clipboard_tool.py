import subprocess
from typing import Any, Dict, List

from .base import Tool


class ClipboardTool(Tool):
    name = "clipboard"
    description = "Read and write clipboard content"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "read_clipboard",
                "description": "Lee el contenido actual del portapapeles (lo que el usuario tiene copiado)",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "write_clipboard",
                "description": "Escribe texto al portapapeles para que el usuario pueda pegarlo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Texto a copiar al portapapeles"},
                    },
                    "required": ["text"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "read_clipboard":
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                    capture_output=True, text=True, timeout=5,
                )
                content = result.stdout.strip()
                return content if content else "(portapapeles vacio)"
            except Exception as e:
                return "Error: " + str(e)

        elif function_name == "write_clipboard":
            text = arguments.get("text", "")
            if not text:
                return "Error: texto vacio"
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value "],
                    input=text, capture_output=True, text=True, timeout=5,
                )
                return "Texto copiado al portapapeles (" + str(len(text)) + " caracteres)"
            except Exception as e:
                return "Error: " + str(e)

        return "Funcion no encontrada"
