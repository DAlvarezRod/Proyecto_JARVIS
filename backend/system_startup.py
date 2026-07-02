"""Windows per-user autostart management for the JARVIS backend."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from logger import get_logger

AUTOSTART_FILE_NAME = "JARVIS Backend Autostart.cmd"
AUTOSTART_MARKER = "JARVIS_AUTOSTART_MANAGED=1"


class StartupManager:
    """Manage backend autostart using a per-user Startup folder entry."""

    def __init__(
        self,
        backend_dir: Optional[Path] = None,
        startup_dir: Optional[Path] = None,
        python_executable: Optional[str] = None,
    ) -> None:
        self.logger = get_logger("system_startup")
        self.backend_dir = Path(backend_dir or Path(__file__).resolve().parent).resolve()
        self.python_executable = Path(python_executable or sys.executable).resolve()
        self._startup_dir_override = Path(startup_dir).resolve() if startup_dir else None

    @staticmethod
    def _is_windows() -> bool:
        return sys.platform.startswith("win")

    def _resolve_startup_dir(self) -> Path:
        if self._startup_dir_override:
            return self._startup_dir_override
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

    def _autostart_file(self) -> Path:
        return self._resolve_startup_dir() / AUTOSTART_FILE_NAME

    def _preferred_python_runtime(self) -> Path:
        pythonw = self.python_executable.with_name("pythonw.exe")
        return pythonw if pythonw.exists() else self.python_executable

    def _build_autostart_script(self) -> str:
        runtime = self._preferred_python_runtime()
        server_script = (self.backend_dir / "api" / "server.py").resolve()
        return (
            "@echo off\n"
            f"REM {AUTOSTART_MARKER}\n"
            "setlocal\n"
            f'cd /d "{self.backend_dir}"\n'
            f'start "" /min "{runtime}" "{server_script}"\n'
        )

    def _is_managed_entry(self, path: Path) -> bool:
        if not path.exists():
            return False
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            raise RuntimeError(f"Unable to read autostart file: {exc}") from exc
        return AUTOSTART_MARKER in content

    def _not_supported(self, action: str) -> Dict[str, Any]:
        return {
            "action": action,
            "success": False,
            "supported": False,
            "enabled": False,
            "error": {
                "code": "not-supported",
                "message": "Autostart is only supported on Windows.",
            },
        }

    def status(self) -> Dict[str, Any]:
        if not self._is_windows():
            return self._not_supported("status")
        startup_dir = self._resolve_startup_dir()
        autostart_file = self._autostart_file()
        try:
            file_exists = autostart_file.exists()
            managed = self._is_managed_entry(autostart_file) if file_exists else False
            enabled = file_exists and managed
            state = "enabled" if enabled else ("unmanaged-conflict" if file_exists else "disabled")
            return {
                "action": "status",
                "success": True,
                "supported": True,
                "enabled": enabled,
                "managed_entry": managed,
                "state": state,
                "autostart_path": str(autostart_file),
                "startup_dir": str(startup_dir),
                "error": None,
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.logger.error("Failed to check autostart status: %s", exc)
            return {
                "action": "status",
                "success": False,
                "supported": True,
                "enabled": False,
                "error": {
                    "code": "status-check-failed",
                    "message": str(exc),
                },
            }

    def enable(self) -> Dict[str, Any]:
        if not self._is_windows():
            return self._not_supported("enable")
        startup_dir = self._resolve_startup_dir()
        autostart_file = self._autostart_file()
        try:
            startup_dir.mkdir(parents=True, exist_ok=True)
            if autostart_file.exists() and not self._is_managed_entry(autostart_file):
                return {
                    "action": "enable",
                    "success": False,
                    "supported": True,
                    "enabled": False,
                    "error": {
                        "code": "startup-entry-conflict",
                        "message": f"Autostart file already exists and is not managed: {autostart_file}",
                    },
                }
            autostart_file.write_text(self._build_autostart_script(), encoding="utf-8")
            self.logger.info("Enabled backend autostart via %s", autostart_file)
            result = self.status()
            result["action"] = "enable"
            return result
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.logger.error("Failed to enable autostart: %s", exc)
            return {
                "action": "enable",
                "success": False,
                "supported": True,
                "enabled": False,
                "error": {
                    "code": "enable-failed",
                    "message": str(exc),
                },
            }

    def disable(self) -> Dict[str, Any]:
        if not self._is_windows():
            return self._not_supported("disable")
        autostart_file = self._autostart_file()
        try:
            if not autostart_file.exists():
                status = self.status()
                status["action"] = "disable"
                status["changed"] = False
                return status
            if not self._is_managed_entry(autostart_file):
                return {
                    "action": "disable",
                    "success": False,
                    "supported": True,
                    "enabled": True,
                    "error": {
                        "code": "startup-entry-conflict",
                        "message": f"Refusing to remove unmanaged autostart file: {autostart_file}",
                    },
                }
            autostart_file.unlink()
            self.logger.info("Disabled backend autostart by removing %s", autostart_file)
            status = self.status()
            status["action"] = "disable"
            status["changed"] = True
            return status
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.logger.error("Failed to disable autostart: %s", exc)
            return {
                "action": "disable",
                "success": False,
                "supported": True,
                "enabled": True,
                "error": {
                    "code": "disable-failed",
                    "message": str(exc),
                },
            }
