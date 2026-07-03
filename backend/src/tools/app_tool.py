import subprocess
from typing import Any, Dict, List

from .base import Tool

APP_SHORTCUTS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "navegador": "chrome",
    "browser": "chrome",
    "notepad": "notepad",
    "bloc de notas": "notepad",
    "calculadora": "calc",
    "calculator": "calc",
    "explorador": "explorer",
    "explorer": "explorer",
    "archivos": "explorer",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "paint": "mspaint",
    "spotify": "spotify",
    "discord": "discord",
    "code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "terminal": "wt",
    "cmd": "cmd",
    "powershell": "powershell",
    "steam": "steam",
    "telegram": "telegram",
    "whatsapp": r"explorer shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "configuracion": "ms-settings:",
    "settings": "ms-settings:",
    "task manager": "taskmgr",
    "administrador de tareas": "taskmgr",
}


class AppTool(Tool):
    name = "apps"
    description = "Open and close applications"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "open_app",
                "description": "Abre una aplicacion en el computador del usuario",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Nombre de la aplicacion a abrir (ej: chrome, spotify, vscode, discord, word)"},
                    },
                    "required": ["app_name"],
                },
            },
            {
                "name": "close_app",
                "description": "Cierra una aplicacion que este corriendo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Nombre de la aplicacion a cerrar"},
                    },
                    "required": ["app_name"],
                },
            },
            {
                "name": "list_running_apps",
                "description": "Lista las aplicaciones que estan corriendo actualmente",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "open_app":
            app = arguments.get("app_name", "").lower().strip()
            if not app:
                return "Error: nombre de app vacio"
            cmd = APP_SHORTCUTS.get(app, app)
            try:
                subprocess.Popen(
                    ["cmd", "/c", "start", "", cmd],
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return "Aplicacion abierta: " + app
            except Exception as e:
                return "Error abriendo " + app + ": " + str(e)

        elif function_name == "close_app":
            app = arguments.get("app_name", "").lower().strip()
            if not app:
                return "Error: nombre de app vacio"
            process_map = {
                "chrome": "chrome.exe",
                "google chrome": "chrome.exe",
                "navegador": "chrome.exe",
                "notepad": "notepad.exe",
                "bloc de notas": "notepad.exe",
                "spotify": "spotify.exe",
                "discord": "discord.exe",
                "code": "code.exe",
                "vscode": "code.exe",
                "word": "winword.exe",
                "excel": "excel.exe",
                "steam": "steam.exe",
                "telegram": "telegram.exe",
                "paint": "mspaint.exe",
                "explorer": "explorer.exe",
            }
            proc = process_map.get(app, app if app.endswith(".exe") else app + ".exe")
            try:
                result = subprocess.run(
                    ["taskkill", "/f", "/im", proc],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return "Aplicacion cerrada: " + app
                return "No se pudo cerrar " + app + ": " + result.stderr.strip()
            except Exception as e:
                return "Error cerrando " + app + ": " + str(e)

        elif function_name == "list_running_apps":
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-Process | Where-Object {.MainWindowTitle -ne ''} | Select-Object ProcessName, MainWindowTitle | Format-Table -AutoSize"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return result.stdout.strip() if result.stdout.strip() else "No hay aplicaciones con ventana abierta"
            except Exception as e:
                return "Error: " + str(e)

        return "Funcion no encontrada"
