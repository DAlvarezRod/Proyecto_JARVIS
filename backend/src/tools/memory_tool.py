import os
import json
from datetime import datetime
from typing import Any, Dict, List

from .base import Tool

MEMORY_DIR = r"C:\Proyectos\Jarvis\backend\data\memory"
MEMORY_FILE = os.path.join(MEMORY_DIR, "memories.json")


class MemoryTool(Tool):
    name = "memory"
    description = "Persistent memory across sessions"

    def __init__(self):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        if not os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load(self):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, memories):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "memory_save",
                "description": "Guarda informacion en la memoria persistente para recordarla en futuras conversaciones. Usar para preferencias, datos importantes, notas, o cualquier cosa que el usuario pida recordar.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Categoria: preferencia, nota, dato, persona, proyecto, recordatorio"},
                        "content": {"type": "string", "description": "Contenido a recordar"},
                        "tags": {"type": "string", "description": "Tags separados por coma para buscar despues. Opcional."},
                    },
                    "required": ["category", "content"],
                },
            },
            {
                "name": "memory_search",
                "description": "Busca en la memoria persistente. Usar cuando el usuario pregunte si recuerdas algo, o cuando necesites contexto de conversaciones anteriores.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Texto a buscar en las memorias"},
                        "category": {"type": "string", "description": "Filtrar por categoria. Opcional."},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "memory_list",
                "description": "Lista todas las memorias guardadas o las de una categoria especifica",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Filtrar por categoria. Opcional."},
                        "limit": {"type": "integer", "description": "Cantidad maxima de resultados. Default: 20"},
                    },
                },
            },
            {
                "name": "memory_delete",
                "description": "Elimina una memoria por su ID. Usar cuando el usuario pida olvidar algo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "integer", "description": "ID de la memoria a eliminar"},
                    },
                    "required": ["memory_id"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "memory_save":
            category = arguments.get("category", "nota")
            content = arguments.get("content", "")
            tags = arguments.get("tags", "")
            if not content:
                return "Error: contenido vacio"
            memories = self._load()
            entry = {
                "id": len(memories) + 1,
                "category": category,
                "content": content,
                "tags": [t.strip() for t in tags.split(",") if t.strip()] if tags else [],
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            memories.append(entry)
            self._save(memories)
            return "Memoria guardada (ID " + str(entry["id"]) + "): " + content[:80]

        elif function_name == "memory_search":
            query = arguments.get("query", "").lower()
            category = arguments.get("category", "")
            if not query:
                return "Error: query vacia"
            memories = self._load()
            results = []
            for m in memories:
                if category and m.get("category") != category:
                    continue
                searchable = (m.get("content", "") + " " + " ".join(m.get("tags", []))).lower()
                if query in searchable:
                    results.append(m)
            if not results:
                return "No encontre memorias sobre: " + query
            lines = []
            for m in results[:10]:
                lines.append(
                    "[" + str(m["id"]) + "] (" + m["category"] + ") " + m["content"]
                    + " | " + m["created"]
                )
            return "Memorias encontradas (" + str(len(results)) + "):\n" + "\n".join(lines)

        elif function_name == "memory_list":
            category = arguments.get("category", "")
            limit = arguments.get("limit", 20)
            memories = self._load()
            if category:
                memories = [m for m in memories if m.get("category") == category]
            if not memories:
                return "No hay memorias guardadas" + (" en categoria: " + category if category else "")
            lines = []
            for m in memories[-limit:]:
                lines.append(
                    "[" + str(m["id"]) + "] (" + m["category"] + ") " + m["content"][:100]
                    + " | " + m["created"]
                )
            return "Memorias (" + str(len(memories)) + " total):\n" + "\n".join(lines)

        elif function_name == "memory_delete":
            memory_id = arguments.get("memory_id")
            if memory_id is None:
                return "Error: ID requerido"
            memories = self._load()
            found = None
            for i, m in enumerate(memories):
                if m.get("id") == memory_id:
                    found = memories.pop(i)
                    break
            if not found:
                return "No existe memoria con ID " + str(memory_id)
            self._save(memories)
            return "Memoria eliminada: " + found["content"][:80]

        return "Funcion no encontrada"
