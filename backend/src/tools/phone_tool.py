import subprocess
import os
from typing import Any, Dict, List

from .base import Tool

PHONE_APPS = {
    "youtube": "com.google.android.youtube",
    "whatsapp": "com.whatsapp",
    "instagram": "com.instagram.android",
    "facebook": "com.facebook.katana",
    "twitter": "com.twitter.android",
    "x": "com.twitter.android",
    "tiktok": "com.zhiliaoapp.musically",
    "spotify": "com.spotify.music",
    "telegram": "org.telegram.messenger",
    "chrome": "com.android.chrome",
    "gmail": "com.google.android.gm",
    "maps": "com.google.android.apps.maps",
    "google maps": "com.google.android.apps.maps",
    "camera": "com.sec.android.app.camera",
    "camara": "com.sec.android.app.camera",
    "galeria": "com.sec.android.gallery3d",
    "gallery": "com.sec.android.gallery3d",
    "ajustes": "com.android.settings",
    "settings": "com.android.settings",
    "telefono": "com.samsung.android.dialer",
    "contactos": "com.samsung.android.contacts",
    "calculadora": "com.sec.android.app.popupcalculator",
    "reloj": "com.sec.android.app.clockpackage",
    "notas": "com.samsung.android.app.notes",
    "netflix": "com.netflix.mediaclient",
    "snapchat": "com.snapchat.android",
    "discord": "com.discord",
    "reddit": "com.reddit.frontpage",
    "rappi": "com.grability.rappi",
    "mercado libre": "com.mercadolibre",
    "uber": "com.ubercab",
}


class PhoneTool(Tool):
    name = "phone"
    description = "Control Android phone via ADB"

    def __init__(self):
        self.adb = os.environ.get(
            "ADB_PATH",
            r"C:\Users\David\Downloads\platform-tools-latest-windows\platform-tools\adb.exe",
        )

    def _get_device(self):
        try:
            r = subprocess.run([self.adb, "devices"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.strip().split("\n")[1:]:
                parts = line.strip().split("\t")
                if len(parts) == 2 and parts[1] == "device" and "emulator" not in parts[0]:
                    return parts[0]
        except Exception:
            pass
        return None

    def _run_adb(self, *args):
        device = self._get_device()
        if not device:
            return None, "No se encontro el celular. Conectalo por USB con depuracion activa."
        cmd = [self.adb, "-s", device] + list(args)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return r.stdout.strip(), None
        except Exception as e:
            return None, str(e)

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "phone_open_app",
                "description": "Abre una app en el celular Android del usuario.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre de la app (youtube, whatsapp, instagram, camera, etc)"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "phone_screenshot",
                "description": "Toma un screenshot del celular y lo guarda en el computador.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "save_path": {"type": "string", "description": "Ruta donde guardar. Default: Desktop"},
                    },
                },
            },
            {
                "name": "phone_send_sms",
                "description": "Prepara un SMS en el celular. El usuario confirma el envio en la pantalla.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "number": {"type": "string", "description": "Numero de telefono"},
                        "message": {"type": "string", "description": "Texto del mensaje"},
                    },
                    "required": ["number", "message"],
                },
            },
            {
                "name": "phone_call",
                "description": "Hace una llamada desde el celular.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "number": {"type": "string", "description": "Numero a llamar"},
                    },
                    "required": ["number"],
                },
            },
            {
                "name": "phone_file_send",
                "description": "Envia un archivo del computador al celular (carpeta Downloads).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Ruta del archivo en el PC"},
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "phone_file_get",
                "description": "Trae un archivo del celular al computador.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_path": {"type": "string", "description": "Ruta en el celular (ej: /sdcard/Download/foto.jpg)"},
                        "save_path": {"type": "string", "description": "Ruta donde guardar en el PC. Default: Desktop"},
                    },
                    "required": ["phone_path"],
                },
            },
            {
                "name": "phone_list_apps",
                "description": "Lista las apps instaladas en el celular.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "phone_battery",
                "description": "Muestra el nivel de bateria del celular.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "phone_volume",
                "description": "Sube o baja el volumen del celular.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "description": "up o down"},
                    },
                    "required": ["direction"],
                },
            },
            {
                "name": "phone_brightness",
                "description": "Ajusta el brillo de la pantalla del celular (0-255).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "integer", "description": "Nivel de brillo de 0 a 255"},
                    },
                    "required": ["level"],
                },
            },
            {
                "name": "phone_type_text",
                "description": "Escribe texto en el celular donde este el cursor activo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Texto a escribir"},
                    },
                    "required": ["text"],
                },
            },
            {
                "name": "phone_tap",
                "description": "Toca la pantalla del celular en coordenadas especificas.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "Coordenada X"},
                        "y": {"type": "integer", "description": "Coordenada Y"},
                    },
                    "required": ["x", "y"],
                },
            },
            {
                "name": "phone_swipe",
                "description": "Desliza en la pantalla del celular.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x1": {"type": "integer", "description": "X inicio"},
                        "y1": {"type": "integer", "description": "Y inicio"},
                        "x2": {"type": "integer", "description": "X final"},
                        "y2": {"type": "integer", "description": "Y final"},
                    },
                    "required": ["x1", "y1", "x2", "y2"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "phone_open_app":
            return self._open_app(arguments)
        elif function_name == "phone_screenshot":
            return self._screenshot(arguments)
        elif function_name == "phone_send_sms":
            return self._send_sms(arguments)
        elif function_name == "phone_call":
            return self._call(arguments)
        elif function_name == "phone_file_send":
            return self._file_send(arguments)
        elif function_name == "phone_file_get":
            return self._file_get(arguments)
        elif function_name == "phone_list_apps":
            return self._list_apps()
        elif function_name == "phone_battery":
            return self._battery()
        elif function_name == "phone_volume":
            return self._volume(arguments)
        elif function_name == "phone_brightness":
            return self._brightness(arguments)
        elif function_name == "phone_type_text":
            return self._type_text(arguments)
        elif function_name == "phone_tap":
            return self._tap(arguments)
        elif function_name == "phone_swipe":
            return self._swipe(arguments)
        return "Funcion no encontrada"

    def _open_app(self, arguments):
        name = arguments.get("name", "").strip()
        if not name:
            return "Error: nombre requerido"
        package = PHONE_APPS.get(name.lower())
        if not package:
            for key, pkg in PHONE_APPS.items():
                if name.lower() in key or key in name.lower():
                    package = pkg
                    break
        if not package:
            package = name
        out, err = self._run_adb("shell", "monkey", "-p", package,
                                  "-c", "android.intent.category.LAUNCHER", "1")
        if err:
            return err
        if "No activities found" in (out or ""):
            return "No se encontro la app: " + name
        return "Abriendo " + name + " en el celular"

    def _screenshot(self, arguments):
        save_path = arguments.get("save_path", "").strip()
        if not save_path:
            save_path = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "phone_screenshot.png")
        out, err = self._run_adb("shell", "screencap", "-p", "/sdcard/screenshot_temp.png")
        if err:
            return err
        device = self._get_device()
        try:
            subprocess.run([self.adb, "-s", device, "pull", "/sdcard/screenshot_temp.png", save_path],
                           capture_output=True, text=True, timeout=10)
            subprocess.run([self.adb, "-s", device, "shell", "rm", "/sdcard/screenshot_temp.png"],
                           capture_output=True, timeout=5)
            return "Screenshot guardado en: " + save_path
        except Exception as e:
            return "Error: " + str(e)

    def _send_sms(self, arguments):
        number = arguments.get("number", "").strip()
        message = arguments.get("message", "").strip()
        if not number or not message:
            return "Error: numero y mensaje requeridos"
        out, err = self._run_adb("shell", "am", "start", "-a", "android.intent.action.SENDTO",
                                  "-d", "sms:" + number, "--es", "sms_body", message)
        if err:
            return err
        return "SMS listo para enviar a " + number + ". Confirma en el celular."

    def _call(self, arguments):
        number = arguments.get("number", "").strip()
        if not number:
            return "Error: numero requerido"
        out, err = self._run_adb("shell", "am", "start", "-a", "android.intent.action.CALL",
                                  "-d", "tel:" + number)
        if err:
            return err
        return "Llamando a " + number

    def _file_send(self, arguments):
        file_path = arguments.get("file_path", "").strip()
        if not file_path or not os.path.isfile(file_path):
            return "Error: archivo no encontrado"
        filename = os.path.basename(file_path)
        device = self._get_device()
        if not device:
            return "Celular no conectado"
        try:
            r = subprocess.run([self.adb, "-s", device, "push", file_path, "/sdcard/Download/" + filename],
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return "Archivo enviado al celular: Download/" + filename
            return "Error: " + r.stderr
        except Exception as e:
            return "Error: " + str(e)

    def _file_get(self, arguments):
        phone_path = arguments.get("phone_path", "").strip()
        save_path = arguments.get("save_path", "").strip()
        if not phone_path:
            return "Error: ruta requerida"
        if not save_path:
            save_path = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", os.path.basename(phone_path))
        device = self._get_device()
        if not device:
            return "Celular no conectado"
        try:
            r = subprocess.run([self.adb, "-s", device, "pull", phone_path, save_path],
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return "Archivo guardado en: " + save_path
            return "Error: " + r.stderr
        except Exception as e:
            return "Error: " + str(e)

    def _list_apps(self):
        out, err = self._run_adb("shell", "pm", "list", "packages", "-3")
        if err:
            return err
        apps = [line.replace("package:", "") for line in out.split("\n") if line.startswith("package:")]
        return "Apps instaladas (" + str(len(apps)) + "):\n" + "\n".join(sorted(apps))

    def _battery(self):
        out, err = self._run_adb("shell", "dumpsys", "battery")
        if err:
            return err
        level = ""
        status = ""
        for line in out.split("\n"):
            line = line.strip()
            if line.startswith("level:"):
                level = line.split(":")[1].strip()
            elif line.startswith("status:"):
                s = line.split(":")[1].strip()
                status = {"1": "desconocido", "2": "cargando", "3": "descargando",
                           "4": "no cargando", "5": "completa"}.get(s, s)
        return "Bateria: " + level + "% (" + status + ")"

    def _volume(self, arguments):
        direction = arguments.get("direction", "").lower()
        key = "24" if direction == "up" else "25" if direction == "down" else None
        if not key:
            return "Error: direction debe ser 'up' o 'down'"
        out, err = self._run_adb("shell", "input", "keyevent", key)
        if err:
            return err
        return "Volumen " + ("subido" if direction == "up" else "bajado")

    def _brightness(self, arguments):
        level = max(0, min(255, arguments.get("level", 128)))
        self._run_adb("shell", "settings", "put", "system", "screen_brightness_mode", "0")
        out, err = self._run_adb("shell", "settings", "put", "system", "screen_brightness", str(level))
        if err:
            return err
        return "Brillo ajustado a " + str(level) + "/255"

    def _type_text(self, arguments):
        text = arguments.get("text", "")
        if not text:
            return "Error: texto requerido"
        safe = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        out, err = self._run_adb("shell", "input", "text", safe)
        if err:
            return err
        return "Texto escrito en el celular"

    def _tap(self, arguments):
        x = arguments.get("x", 0)
        y = arguments.get("y", 0)
        out, err = self._run_adb("shell", "input", "tap", str(x), str(y))
        if err:
            return err
        return "Tap en (" + str(x) + ", " + str(y) + ")"

    def _swipe(self, arguments):
        x1, y1 = arguments.get("x1", 0), arguments.get("y1", 0)
        x2, y2 = arguments.get("x2", 0), arguments.get("y2", 0)
        out, err = self._run_adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2))
        if err:
            return err
        return "Swipe realizado"