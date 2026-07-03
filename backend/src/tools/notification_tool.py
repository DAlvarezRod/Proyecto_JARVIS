from typing import Any, Dict, List

from .base import Tool


class NotificationTool(Tool):
    name = "notification"
    description = "Send Windows desktop notifications"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "send_notification",
                "description": "Envia una notificacion emergente de Windows al usuario",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Titulo de la notificacion. Default: Illo"},
                        "message": {"type": "string", "description": "Mensaje de la notificacion"},
                    },
                    "required": ["message"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "send_notification":
            title = arguments.get("title", "Illo")
            message = arguments.get("message", "")
            if not message:
                return "Error: mensaje vacio"
            try:
                from plyer import notification as plyer_notify

                plyer_notify.notify(
                    title=title,
                    message=message,
                    app_name="Illo",
                    timeout=10,
                )
                return "Notificacion enviada: " + title + " - " + message[:50]
            except Exception as e:
                return "Error: " + str(e)

        return "Funcion no encontrada"
