import os
import subprocess
from typing import Any, Dict, List

from .base import Tool


class CodeTool(Tool):
    name = "coding"
    description = "Write code files and open them in VSCode"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "write_code",
                "description": "Escribe codigo en un archivo y lo abre en VSCode. Usa esto cuando el usuario pida programar, crear un script, hacer una pagina web, o cualquier tarea de codigo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Nombre del archivo con extension (ej: app.py, index.html, script.js)"},
                        "code": {"type": "string", "description": "El codigo completo a escribir"},
                        "folder": {"type": "string", "description": "Carpeta donde guardar. Si no se da, usa el Desktop."},
                    },
                    "required": ["filename", "code"],
                },
            },
            {
                "name": "edit_file_vscode",
                "description": "Abre un archivo existente en VSCode para verlo o editarlo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del archivo a abrir"},
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "open_project_vscode",
                "description": "Abre una carpeta o proyecto completo en VSCode.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta de la carpeta del proyecto"},
                    },
                    "required": ["path"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "write_code":
            return self._write_code(arguments)
        elif function_name == "edit_file_vscode":
            return self._edit_file(arguments)
        elif function_name == "open_project_vscode":
            return self._open_project(arguments)
        return "Funcion no encontrada"

    def _write_code(self, arguments):
        filename = arguments.get("filename", "").strip()
        code = arguments.get("code", "")
        folder = arguments.get("folder", "").strip()

        if not filename or not code:
            return "Error: filename y code son requeridos"

        if not folder:
            folder = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")

        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            return "Error escribiendo archivo: " + str(e)

        try:
            subprocess.Popen(["cmd", "/c", "code", filepath], shell=False)
        except Exception:
            pass

        return "Codigo guardado en " + filepath + " y abierto en VSCode"

    def _edit_file(self, arguments):
        path = arguments.get("path", "").strip()
        if not path:
            return "Error: path requerido"

        if not os.path.isfile(path):
            return "No se encontro el archivo: " + path

        try:
            subprocess.Popen(["cmd", "/c", "code", path], shell=False)
            return "Abierto en VSCode: " + path
        except Exception as e:
            return "Error: " + str(e)

    def _open_project(self, arguments):
        path = arguments.get("path", "").strip()
        if not path:
            return "Error: path requerido"

        if not os.path.isdir(path):
            return "No se encontro la carpeta: " + path

        try:
            subprocess.Popen(["cmd", "/c", "code", path], shell=False)
            return "Proyecto abierto en VSCode: " + path
        except Exception as e:
            return "Error: " + str(e)