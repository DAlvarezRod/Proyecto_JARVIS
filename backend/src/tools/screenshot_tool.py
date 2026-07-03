import os
from datetime import datetime
from typing import Any, Dict, List

from .base import Tool

SCREENSHOT_DIR = r"C:\Proyectos\Jarvis\screenshots"


class ScreenshotTool(Tool):
    name = "screenshot"
    description = "Take screenshots of the screen"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "take_screenshot",
                "description": "Toma una captura de pantalla completa y la guarda como imagen",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Nombre del archivo. Opcional, se genera con timestamp."},
                    },
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "take_screenshot":
            try:
                from PIL import ImageGrab

                os.makedirs(SCREENSHOT_DIR, exist_ok=True)
                filename = arguments.get("filename", "")
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = "screenshot_" + timestamp + ".png"
                if not filename.endswith(".png"):
                    filename += ".png"
                filepath = os.path.join(SCREENSHOT_DIR, filename)
                img = ImageGrab.grab()
                img.save(filepath)
                return "Screenshot guardado en: " + filepath + " (" + str(img.size[0]) + "x" + str(img.size[1]) + ")"
            except Exception as e:
                return "Error: " + str(e)

        return "Funcion no encontrada"
