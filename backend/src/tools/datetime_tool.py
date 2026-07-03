from datetime import datetime
from typing import Any, Dict, List

from .base import Tool

DAYS_ES = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


class DateTimeTool(Tool):
    name = "datetime"
    description = "Gets current date and time"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_current_datetime",
                "description": "Obtiene la fecha y hora actual del sistema",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            }
        ]

    def execute(self, function_name: str, arguments: Dict[str, Any]) -> str:
        now = datetime.now()
        day_name = DAYS_ES[now.weekday()]
        month_name = MONTHS_ES[now.month - 1]
        return f"{day_name} {now.day} de {month_name} de {now.year}, {now.strftime('%H:%M:%S')}"
