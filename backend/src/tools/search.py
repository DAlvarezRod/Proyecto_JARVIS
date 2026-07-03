import os
from pathlib import Path
from typing import Any, Dict, List

from .base import Tool


class SearchTool(Tool):
    name = "search"
    description = "Searches for text patterns in files"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "search_in_files",
                "description": "Busca un texto o patron dentro de archivos en un directorio",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Texto a buscar"},
                        "path": {"type": "string", "description": "Directorio donde buscar"},
                        "extension": {"type": "string", "description": "Extension de archivo (ej: .py, .txt). Opcional."},
                    },
                    "required": ["query", "path"],
                },
            }
        ]

    def execute(self, function_name, arguments):
        query = arguments.get("query", "")
        path = arguments.get("path", ".")
        extension = arguments.get("extension", "")

        if not query:
            return "Error: query vacia"

        try:
            p = Path(path)
            if not p.exists():
                return "No existe: " + path
            if not p.is_dir():
                return "No es directorio: " + path

            results = []
            count = 0
            max_results = 30

            for root, dirs, files in os.walk(str(p)):
                dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "node_modules", "venv", ".venv"}]
                for fname in files:
                    if extension and not fname.endswith(extension):
                        continue
                    filepath = os.path.join(root, fname)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            for line_num, line in enumerate(f, 1):
                                if query.lower() in line.lower():
                                    rel = os.path.relpath(filepath, str(p))
                                    results.append(rel + ":" + str(line_num) + ": " + line.strip()[:120])
                                    count += 1
                                    if count >= max_results:
                                        break
                        if count >= max_results:
                            break
                    except Exception:
                        continue
                if count >= max_results:
                    break

            if not results:
                return "No se encontro '" + query + "' en " + path
            return "Resultados (" + str(len(results)) + "):\n" + "\n".join(results)
        except Exception as e:
            return "Error: " + str(e)
