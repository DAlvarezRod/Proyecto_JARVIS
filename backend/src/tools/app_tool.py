import subprocess
import os
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

PROCESS_NAMES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "discord": "Discord",
    "steam": "steam",
    "spotify": "Spotify",
    "telegram": "Telegram",
    "obs": "obs64",
    "obs studio": "obs64",
    "vscode": "Code",
    "visual studio code": "Code",
    "cs2": "cs2",
    "counter-strike 2": "cs2",
    "counter strike 2": "cs2",
    "teams": "ms-teams",
    "word": "WINWORD",
    "excel": "EXCEL",
    "powerpoint": "POWERPNT",
    "vlc": "vlc",
    "blender": "blender",
    "notepad": "notepad",
    "whatsapp": "WhatsApp",
    "edge": "msedge",
    "brave": "brave",
    "firefox": "firefox",
}


class AppTool(Tool):
    name = "apps"
    description = "Open, close, search apps, and find/open files and folders"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "open_app",
                "description": "Abre una aplicacion o juego en Windows. Busca automaticamente en apps instaladas, menu de inicio, registro de Windows y PATH.",
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
                "description": "Cierra una aplicacion por nombre",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre de la app a cerrar"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "open_file",
                "description": "Busca un archivo por nombre en el computador y lo abre con su programa predeterminado.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre del archivo (parcial o completo)"},
                        "folder": {"type": "string", "description": "Carpeta donde buscar. Si no se da, busca en Desktop, Documents, Downloads."},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "open_folder",
                "description": "Abre una carpeta en el explorador. Puede recibir ruta completa o buscar por nombre.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta o nombre de la carpeta"},
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "search_files",
                "description": "Busca archivos por nombre y devuelve las rutas encontradas sin abrirlos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre o parte del nombre"},
                        "folder": {"type": "string", "description": "Carpeta donde buscar"},
                        "extension": {"type": "string", "description": "Extension (ej: pdf, docx, py)"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "list_running_apps",
                "description": "Lista las aplicaciones con ventana visible actualmente abiertas",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "list_installed_apps",
                "description": "Lista todas las aplicaciones instaladas en el computador",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    def _sanitize(self, text):
        for ch in "'\"`;$|&{}()":
            text = text.replace(ch, "")
        return text

    def _search_start_menu(self, name):
        safe = self._sanitize(name)
        ps = (
            '$dirs = @('
            '"$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs",'
            '"C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs"'
            '); '
            '$results = @(); '
            'foreach ($d in $dirs) { '
            '$results += Get-ChildItem -Path $d -Recurse -Filter "*.lnk" '
            '-ErrorAction SilentlyContinue '
            '| Where-Object { $_.BaseName -like "*' + safe + '*" } '
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

    def _search_registry(self, name):
        safe = self._sanitize(name)
        ps = (
            '$paths = @('
            '"HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",'
            '"HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",'
            '"HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*"'
            '); '
            'Get-ItemProperty $paths -ErrorAction SilentlyContinue '
            '| Where-Object { $_.DisplayName -like "*' + safe + '*" -and $_.InstallLocation } '
            '| Select-Object -First 1 -ExpandProperty InstallLocation'
        )
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=10,
            )
            loc = r.stdout.strip()
            if loc and os.path.isdir(loc):
                for f in os.listdir(loc):
                    if f.lower().endswith(".exe") and not f.lower().startswith("unins"):
                        return os.path.join(loc, f)
        except Exception:
            pass
        return None

    def _find_files(self, name, folder=None, extension=None):
        safe = self._sanitize(name)
        user_profile = os.environ.get("USERPROFILE", "")

        if folder:
            dirs = [folder]
        else:
            dirs = [
                os.path.join(user_profile, "Desktop"),
                os.path.join(user_profile, "Documents"),
                os.path.join(user_profile, "Downloads"),
            ]

        pattern = "*" + safe + "*"
        if extension:
            pattern = "*" + safe + "*." + extension.lstrip(".")

        found = []
        for d in dirs:
            if not os.path.isdir(d):
                continue
            ps = (
                'Get-ChildItem -Path "' + d + '" -Recurse -Filter "' + pattern + '" '
                '-File -ErrorAction SilentlyContinue '
                '| Select-Object -First 5 -ExpandProperty FullName'
            )
            try:
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True, text=True, timeout=15,
                )
                for line in r.stdout.strip().split("\n"):
                    line = line.strip()
                    if line:
                        found.append(line)
            except Exception:
                pass
            if found:
                break
        return found

    def _find_folder(self, name):
        safe = self._sanitize(name)
        user_profile = os.environ.get("USERPROFILE", "")
        search_in = [
            (user_profile, "4"),
            ("C:\\Proyectos", "3"),
            ("C:\\", "2"),
        ]
        for d, depth in search_in:
            if not os.path.isdir(d):
                continue
            ps = (
                'Get-ChildItem -Path "' + d + '" -Recurse -Depth ' + depth + ' -Directory '
                '-Filter "*' + safe + '*" -ErrorAction SilentlyContinue '
                '| Select-Object -First 1 -ExpandProperty FullName'
            )
            try:
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True, text=True, timeout=15,
                )
                path = r.stdout.strip()
                if path:
                    return path
            except Exception:
                pass
        return None

    def execute(self, function_name, arguments):
        if function_name == "open_app":
            return self._exec_open_app(arguments)
        elif function_name == "close_app":
            return self._exec_close_app(arguments)
        elif function_name == "open_file":
            return self._exec_open_file(arguments)
        elif function_name == "open_folder":
            return self._exec_open_folder(arguments)
        elif function_name == "search_files":
            return self._exec_search_files(arguments)
        elif function_name == "list_running_apps":
            return self._exec_list_running()
        elif function_name == "list_installed_apps":
            return self._exec_list_installed()
        return "Funcion no encontrada"

    def _exec_open_app(self, arguments):
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
                    subprocess.Popen(["cmd", "/c", "start", "", steam_id], shell=False)
                    return "Abriendo " + name
                except Exception as e:
                    return "Error: " + str(e)
            try:
                subprocess.Popen(["cmd", "/c", "start", "", "steam://rungameid/" + steam_id], shell=False)
                return "Abriendo " + name + " via Steam"
            except Exception as e:
                return "Error: " + str(e)

        cmd = APP_SHORTCUTS.get(name_lower)
        if cmd:
            try:
                subprocess.Popen(["cmd", "/c", "start", "", cmd], shell=False)
                return "Abriendo " + name
            except Exception as e:
                return "Error: " + str(e)

        shortcut = self._search_start_menu(name)
        if shortcut:
            try:
                subprocess.Popen(["cmd", "/c", "start", "", shortcut], shell=False)
                return "Abriendo " + name
            except Exception as e:
                return "Error: " + str(e)

        exe_path = self._search_registry(name)
        if exe_path:
            try:
                subprocess.Popen(["cmd", "/c", "start", "", exe_path], shell=False)
                return "Abriendo " + name
            except Exception as e:
                return "Error: " + str(e)

        try:
            subprocess.Popen(["cmd", "/c", "start", "", name], shell=False)
            return "Intentando abrir " + name
        except Exception as e:
            return "No se encontro: " + name

    def _exec_close_app(self, arguments):
        name = arguments.get("name", "").strip()
        if not name:
            return "Error: nombre requerido"
        name_lower = name.lower()
        process = PROCESS_NAMES.get(name_lower, name)

        try:
            r = subprocess.run(
                ["taskkill", "/IM", process + ".exe", "/F"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                return "Cerrado: " + name
        except Exception:
            pass

        safe = self._sanitize(name)
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-Process | Where-Object {$_.MainWindowTitle -like '*" + safe + "*'} | Stop-Process -Force"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                return "Cerrado: " + name
        except Exception:
            pass

        return "No se encontro proceso: " + name

    def _exec_open_file(self, arguments):
        name = arguments.get("name", "").strip()
        folder = arguments.get("folder", "").strip() or None
        if not name:
            return "Error: nombre requerido"

        if os.path.isfile(name):
            try:
                os.startfile(name)
                return "Abriendo: " + name
            except Exception as e:
                return "Error: " + str(e)

        found = self._find_files(name, folder=folder)
        if found:
            try:
                os.startfile(found[0])
                return "Abriendo: " + found[0]
            except Exception as e:
                return "Error: " + str(e)
        return "No se encontro el archivo: " + name

    def _exec_open_folder(self, arguments):
        path = arguments.get("path", "").strip()
        if not path:
            return "Error: ruta requerida"

        if os.path.isdir(path):
            try:
                os.startfile(path)
                return "Abriendo carpeta: " + path
            except Exception as e:
                return "Error: " + str(e)

        found = self._find_folder(path)
        if found:
            try:
                os.startfile(found)
                return "Abriendo carpeta: " + found
            except Exception as e:
                return "Error: " + str(e)
        return "No se encontro la carpeta: " + path

    def _exec_search_files(self, arguments):
        name = arguments.get("name", "").strip()
        folder = arguments.get("folder", "").strip() or None
        extension = arguments.get("extension", "").strip() or None
        if not name:
            return "Error: nombre requerido"

        found = self._find_files(name, folder=folder, extension=extension)
        if found:
            lines = [str(i + 1) + ". " + f for i, f in enumerate(found)]
            return "Archivos encontrados:\n" + "\n".join(lines)
        return "No se encontraron archivos: " + name

    def _exec_list_running(self):
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} "
                 "| Select-Object -Property ProcessName,MainWindowTitle | Format-Table -AutoSize"],
                capture_output=True, text=True, timeout=10,
            )
            return r.stdout.strip() if r.stdout.strip() else "No hay apps con ventana visible"
        except Exception as e:
            return "Error: " + str(e)

    def _exec_list_installed(self):
        ps = (
            'Get-ItemProperty '
            '"HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",'
            '"HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",'
            '"HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*" '
            '-ErrorAction SilentlyContinue '
            '| Where-Object { $_.DisplayName } '
            '| Sort-Object DisplayName '
            '| Select-Object -Property DisplayName '
            '| Format-Table -AutoSize'
        )
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=15,
            )
            return r.stdout.strip() if r.stdout.strip() else "No se encontraron apps"
        except Exception as e:
            return "Error: " + str(e)