import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Tool

BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".ps1", ".sys", ".dll"}
BLOCKED_PATHS = {"C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)"}


def _is_blocked(path):
    resolved = str(Path(path).resolve())
    for bp in BLOCKED_PATHS:
        if resolved.lower().startswith(bp.lower()):
            return "Ruta protegida: " + bp
    ext = Path(path).suffix.lower()
    if ext in BLOCKED_EXTENSIONS:
        return "Extension bloqueada: " + ext
    return None


class FilesystemTool(Tool):
    name = "filesystem"
    description = "Manages files and folders on the local computer"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {"name": "list_files", "description": "Lista archivos y carpetas en un directorio", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Ruta del directorio"}}, "required": ["path"]}},
            {"name": "read_file", "description": "Lee el contenido de un archivo", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Ruta del archivo"}}, "required": ["path"]}},
            {"name": "create_file", "description": "Crea un archivo con contenido", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Ruta"}, "content": {"type": "string", "description": "Contenido"}}, "required": ["path", "content"]}},
            {"name": "create_folder", "description": "Crea una carpeta", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Ruta"}}, "required": ["path"]}},
            {"name": "delete_file", "description": "Elimina un archivo o carpeta", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Ruta"}}, "required": ["path"]}},
        ]

    def execute(self, function_name, arguments):
        handlers = {"list_files": self._list, "read_file": self._read, "create_file": self._create, "create_folder": self._mkdir, "delete_file": self._delete}
        h = handlers.get(function_name)
        if not h:
            return "Funcion no encontrada"
        return h(arguments)

    def _list(self, args):
        path = args.get("path", ".")
        b = _is_blocked(path)
        if b: return b
        try:
            p = Path(path)
            if not p.exists(): return "No existe: " + path
            if not p.is_dir(): return "No es carpeta: " + path
            items = []
            for item in sorted(p.iterdir()):
                if item.is_dir():
                    items.append("[carpeta] " + item.name)
                else:
                    items.append("[archivo] " + item.name + " (" + str(item.stat().st_size) + " bytes)")
            return "Contenido de " + str(p.resolve()) + ":\n" + "\n".join(items) if items else "Carpeta vacia"
        except Exception as e:
            return str(e)

    def _read(self, args):
        path = args.get("path", "")
        b = _is_blocked(path)
        if b: return b
        try:
            p = Path(path)
            if not p.exists(): return "No existe: " + path
            if p.stat().st_size > 1000000: return "Archivo muy grande"
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return str(e)

    def _create(self, args):
        path = args.get("path", "")
        content = args.get("content", "")
        b = _is_blocked(path)
        if b: return b
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return "Archivo creado: " + str(p.resolve())
        except Exception as e:
            return str(e)

    def _mkdir(self, args):
        path = args.get("path", "")
        b = _is_blocked(path)
        if b: return b
        try:
            p = Path(path)
            p.mkdir(parents=True, exist_ok=True)
            return "Carpeta creada: " + str(p.resolve())
        except Exception as e:
            return str(e)

    def _delete(self, args):
        path = args.get("path", "")
        b = _is_blocked(path)
        if b: return b
        try:
            p = Path(path)
            if not p.exists(): return "No existe: " + path
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return "Eliminado: " + str(p.resolve())
        except Exception as e:
            return str(e)
