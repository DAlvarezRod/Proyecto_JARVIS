"""Skill de manejo de archivos para Illo."""

import os
import shutil
from pathlib import Path


BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".ps1", ".sys", ".dll"}
BLOCKED_PATHS = {"C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)"}


def _is_blocked(path: str) -> str | None:
    resolved = str(Path(path).resolve())
    for bp in BLOCKED_PATHS:
        if resolved.lower().startswith(bp.lower()):
            return f"Acceso bloqueado a ruta protegida: {bp}"
    ext = Path(path).suffix.lower()
    if ext in BLOCKED_EXTENSIONS:
        return f"Extensión bloqueada por seguridad: {ext}"
    return None


def list_files(directory: str) -> dict:
    blocked = _is_blocked(directory)
    if blocked:
        return {"ok": False, "error": blocked}
    try:
        p = Path(directory)
        if not p.exists():
            return {"ok": False, "error": f"No existe: {directory}"}
        if not p.is_dir():
            return {"ok": False, "error": f"No es una carpeta: {directory}"}
        items = []
        for item in sorted(p.iterdir()):
            items.append({
                "name": item.name,
                "type": "folder" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {"ok": True, "path": str(p.resolve()), "items": items}
    except PermissionError:
        return {"ok": False, "error": f"Sin permisos para acceder a: {directory}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read_file(filepath: str) -> dict:
    blocked = _is_blocked(filepath)
    if blocked:
        return {"ok": False, "error": blocked}
    try:
        p = Path(filepath)
        if not p.exists():
            return {"ok": False, "error": f"No existe: {filepath}"}
        if not p.is_file():
            return {"ok": False, "error": f"No es un archivo: {filepath}"}
        if p.stat().st_size > 1_000_000:
            return {"ok": False, "error": "Archivo demasiado grande (máx 1MB)"}
        content = p.read_text(encoding="utf-8", errors="replace")
        return {"ok": True, "path": str(p.resolve()), "content": content}
    except PermissionError:
        return {"ok": False, "error": f"Sin permisos: {filepath}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_file(filepath: str, content: str = "") -> dict:
    blocked = _is_blocked(filepath)
    if blocked:
        return {"ok": False, "error": blocked}
    try:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(p.resolve()), "action": "created"}
    except PermissionError:
        return {"ok": False, "error": f"Sin permisos: {filepath}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_folder(directory: str) -> dict:
    blocked = _is_blocked(directory)
    if blocked:
        return {"ok": False, "error": blocked}
    try:
        p = Path(directory)
        p.mkdir(parents=True, exist_ok=True)
        return {"ok": True, "path": str(p.resolve()), "action": "created"}
    except PermissionError:
        return {"ok": False, "error": f"Sin permisos: {directory}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def move_file(source: str, destination: str) -> dict:
    for path in (source, destination):
        blocked = _is_blocked(path)
        if blocked:
            return {"ok": False, "error": blocked}
    try:
        src = Path(source)
        if not src.exists():
            return {"ok": False, "error": f"No existe: {source}"}
        dst = Path(destination)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return {"ok": True, "from": str(src.resolve()), "to": str(dst.resolve()), "action": "moved"}
    except PermissionError:
        return {"ok": False, "error": "Sin permisos para mover"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_file(filepath: str, confirm: bool = False) -> dict:
    if not confirm:
        return {
            "ok": False,
            "error": "Confirmación requerida",
            "message": f"¿Seguro que quieres eliminar '{filepath}'? Responde 'sí' para confirmar.",
        }
    blocked = _is_blocked(filepath)
    if blocked:
        return {"ok": False, "error": blocked}
    try:
        p = Path(filepath)
        if not p.exists():
            return {"ok": False, "error": f"No existe: {filepath}"}
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return {"ok": True, "path": str(p.resolve()), "action": "deleted"}
    except PermissionError:
        return {"ok": False, "error": f"Sin permisos: {filepath}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}