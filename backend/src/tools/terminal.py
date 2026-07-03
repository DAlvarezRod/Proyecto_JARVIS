import subprocess
from typing import Any, Dict, List

from .base import Tool

BLOCKED_COMMANDS = ["format", "del /s", "rd /s", "rm -rf", "shutdown", "restart", "taskkill"]


class TerminalTool(Tool):
    name = "terminal"
    description = "Executes commands on the local terminal"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "run_command",
                "description": "Ejecuta un comando en PowerShell y devuelve el resultado. Usar para cualquier operacion del sistema.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Comando a ejecutar en PowerShell"}
                    },
                    "required": ["command"],
                },
            }
        ]

    def execute(self, function_name, arguments):
        command = arguments.get("command", "")
        if not command:
            return "Error: comando vacio"

        cmd_lower = command.lower()
        for blocked in BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return "Comando bloqueado por seguridad: " + blocked

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30,
                cwd="C:\\Users",
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += "\n[STDERR] " + result.stderr
            if result.returncode != 0:
                output += "\n[EXIT CODE] " + str(result.returncode)
            return output.strip() if output.strip() else "(comando ejecutado sin salida)"
        except subprocess.TimeoutExpired:
            return "Error: el comando tardo mas de 30 segundos"
        except Exception as e:
            return "Error: " + str(e)
