import subprocess
from typing import Any, Dict, List

from .base import Tool

APP_SHORTCUTS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "navegador": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "brave": "brave",
    "opera": "opera",
    "notepad": "notepad",
    "bloc de notas": "notepad",
    "calculadora": "calc",
    "calculator": "calc",
    "paint": "mspaint",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "teams": "msteams",
    "discord": "discord",
    "telegram": "telegram",
    "whatsapp": "whatsapp:",
    "spotify": "spotify",
    "steam": "steam",
    "epic games": "com.epicgames.launcher:",
    "vscode": "code",
    "visual studio code": "code",
    "terminal": "wt",
    "windows terminal": "wt",
    "cmd": "cmd",
    "powershell": "powershell",
    "explorador": "explorer",
    "explorer": "explorer",
    "archivos": "explorer",
    "task manager": "taskmgr",
    "administrador de tareas": "taskmgr",
    "configuracion": "ms-settings:",
    "settings": "ms-settings:",
    "control panel": "control",
    "panel de control": "control",
    "obs": "obs64",
    "obs studio": "obs64",
    "vlc": "vlc",
    "gimp": "gimp",
    "photoshop": "photoshop",
    "premiere": "premiere",
    "blender": "blender",
    "unity": "unity",
    "unreal engine": "UnrealEditor",
    "codex": "cmd /k codex",
}

STEAM_GAMES = {
    "counter-strike 2": "730",
    "cs2": "730",
    "counter strike 2": "730",
    "counter-strike": "730",
    "csgo": "730",
    "dota 2": "570",
    "dota": "570",
    "gta v": "271590",
    "gta 5": "271590",
    "grand theft auto v": "271590",
    "terraria": "105600",
    "rust": "252490",
    "pubg": "578080",
    "apex legends": "1172470",
    "apex": "1172470",
    "rocket league": "252950",
    "valheim": "892970",
    "the witcher 3": "292030",
    "witcher 3": "292030",
    "cyberpunk 2077": "1091500",
    "cyberpunk": "1091500",
    "elden ring": "1245620",
    "among us": "945360",
    "fall guys": "1097150",
    "left 4 dead 2": "550",
    "l4d2": "550",
    "portal 2": "620",
    "garry's mod": "4000",
    "gmod": "4000",
    "minecraft": "minecraft",
    "fortnite": "fortnite",
    "valorant": "valorant",
    "league of legends": "league",
    "lol": "league",
}


class AppTool(Tool):
    name = "apps"
    description = "Open, close, and list applications"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "open_app",
                "description": "Abre una aplicacion o juego en Windows. Soporta apps comunes, juegos de Steam por nombre, y busqueda automatica en el menu de inicio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre de la app o juego a abrir"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "close_app",
                "description": "Cierra una aplicacion por nombre de proceso",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre de la app a cerrar"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "list_running_apps",
                "description": "Lista las aplicaciones con ventana visible actualmente abiertas",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    def _search_start_menu(self, name):
        ps = (
            '$dirs = @('
            '"$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs",'
            '"C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs"'
            '); '
            '$results = @(); '
            'foreach ($d in $dirs) { '
            '$results += Get-ChildItem -Path $d -Recurse -Filter "*.lnk" '
            '-ErrorAction SilentlyContinue '
            '| Where-Object { $_.BaseName -like "*' + name + '*" } '
            '| Select-Object -First 3 -ExpandProperty FullName '
            '}; '
            '$results | Select-Object -First 1'
        )
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=10,
            )
            path = r.stdout.strip()
            if path and path.endswith(".lnk"):
                return path
        except Exception:
            pass
        return None

    def execute(self, function_name, arguments):
        if function_name == "open_app":
            name = arguments.get("name", "").strip()
            if not name:
                return "Error: nombre requerido"
            name_lower = name.lower()

            steam_id = STEAM_GAMES.get(name_lower)
            if not steam_id:
                for key, sid in STEAM_GAMES.items():
                    if name_lower in key or key in name_lower:
                        steam_id = sid
                        break
            if steam_id:
                if steam_id in ("minecraft", "fortnite", "valorant", "league"):
                    try:
                        subprocess.Popen(
                            ["cmd", "/c", "start", "", steam_id],
                            shell=False,
                        )
                        return "Abriendo " + name
                    except Exception as e:
                        return "Error: " + str(e)
                try:
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", "steam://rungameid/" + steam_id],
                        shell=False,
                    )
                    return "Abriendo " + name + " via Steam"
                except Exception as e:
                    return "Error: " + str(e)

            cmd = APP_SHORTCUTS.get(name_lower)
            if cmd:
                try:
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", cmd],
                        shell=False,
                    )
                    return "Abriendo " + name
                except Exception as e:
                    return "Error: " + str(e)

            shortcut = self._search_start_menu(name)
            if shortcut:
                try:
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", shortcut],
                        shell=False,
                    )
                    return "Abriendo " + name + " (encontrado en menu de inicio)"
                except Exception as e:
                    return "Error: " + str(e)

            try:
                subprocess.Popen(
                    ["cmd", "/c", "start", "", name],
                    shell=False,
                )
                return "Intentando abrir " + name
            except Exception as e:
                return "Error abriendo " + name + ": " + str(e)

        elif function_name == "close_app":
            name = arguments.get("name", "").strip()
            if not name:
                return "Error: nombre requerido"
            try:
                r = subprocess.run(
                    ["taskkill", "/IM", name + ".exe", "/F"],
                    capture_output=True, text=True, timeout=10,
                )
                if r.returncode == 0:
                    return "Cerrado: " + name
                r2 = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-Process | Where-Object {$_.MainWindowTitle -like '*" + name + "*'} | Stop-Process -Force"],
                    capture_output=True, text=True, timeout=10,
                )
                if r2.returncode == 0:
                    return "Cerrado: " + name
                return "No se encontro proceso: " + name
            except Exception as e:
                return "Error: " + str(e)

        elif function_name == "list_running_apps":
            try:
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object -Property ProcessName,MainWindowTitle | Format-Table -AutoSize"],
                    capture_output=True, text=True, timeout=10,
                )
                return r.stdout.strip() if r.stdout.strip() else "No hay apps con ventana visible"
            except Exception as e:
                return "Error: " + str(e)

        return "Funcion no encontrada"