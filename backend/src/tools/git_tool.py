import subprocess
from typing import Any, Dict, List

from .base import Tool


class GitTool(Tool):
    name = "git"
    description = "Git version control operations"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "git_status",
                "description": "Muestra el estado actual del repositorio git (archivos modificados, sin seguimiento, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del repositorio. Default: C:\\Proyectos\\Jarvis"}
                    },
                },
            },
            {
                "name": "git_diff",
                "description": "Muestra las diferencias de archivos modificados en el repositorio",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del repositorio"},
                        "file": {"type": "string", "description": "Archivo especifico para ver diff. Opcional."},
                    },
                },
            },
            {
                "name": "git_log",
                "description": "Muestra el historial de commits recientes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del repositorio"},
                        "count": {"type": "integer", "description": "Cantidad de commits a mostrar. Default: 5"},
                    },
                },
            },
            {
                "name": "git_add_commit_push",
                "description": "Agrega archivos, crea un commit y hace push. SOLO usar cuando el usuario lo pida explicitamente.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del repositorio"},
                        "message": {"type": "string", "description": "Mensaje del commit"},
                        "files": {"type": "string", "description": "Archivos a agregar separados por espacio. Default: . (todos)"},
                    },
                    "required": ["message"],
                },
            },
        ]

    def _run_git(self, args, cwd):
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd,
            )
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            return output.strip() if output.strip() else "(sin salida)"
        except Exception as e:
            return "Error git: " + str(e)

    def execute(self, function_name, arguments):
        path = arguments.get("path", "C:\\Proyectos\\Jarvis")

        if function_name == "git_status":
            return self._run_git(["status"], path)

        elif function_name == "git_diff":
            cmd = ["diff"]
            f = arguments.get("file")
            if f:
                cmd.append(f)
            return self._run_git(cmd, path)

        elif function_name == "git_log":
            count = str(arguments.get("count", 5))
            return self._run_git(["log", "--oneline", "-" + count], path)

        elif function_name == "git_add_commit_push":
            message = arguments.get("message", "update")
            files = arguments.get("files", ".")
            add_result = self._run_git(["add"] + files.split(), path)
            commit_result = self._run_git(["commit", "-m", message], path)
            push_result = self._run_git(["push"], path)
            return "ADD: " + add_result + "\nCOMMIT: " + commit_result + "\nPUSH: " + push_result

        return "Funcion git no encontrada: " + function_name
