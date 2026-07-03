import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .base import Tool

TOKEN_FILE = r"C:\Proyectos\Jarvis\backend\data\google_token.json"
CREDS_FILE = r"C:\Proyectos\Jarvis\backend\data\google_credentials.json"


class CalendarTool(Tool):
    name = "calendar"
    description = "Google Calendar integration"

    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service:
            return self._service
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            if not os.path.exists(TOKEN_FILE):
                return None
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
            self._service = build("calendar", "v3", credentials=creds)
            return self._service
        except Exception as e:
            print("[CALENDAR] Error: " + str(e), flush=True)
            return None

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "calendar_list_events",
                "description": "Lista los proximos eventos del calendario de Google",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Dias hacia adelante para buscar eventos. Default: 7"},
                        "count": {"type": "integer", "description": "Cantidad maxima de eventos. Default: 10"},
                    },
                },
            },
            {
                "name": "calendar_create_event",
                "description": "Crea un nuevo evento en Google Calendar",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Titulo del evento"},
                        "date": {"type": "string", "description": "Fecha en formato YYYY-MM-DD"},
                        "start_time": {"type": "string", "description": "Hora de inicio en formato HH:MM (24h). Opcional para eventos de todo el dia."},
                        "end_time": {"type": "string", "description": "Hora de fin en formato HH:MM (24h). Opcional, default: 1 hora despues del inicio."},
                        "description": {"type": "string", "description": "Descripcion del evento. Opcional."},
                        "location": {"type": "string", "description": "Ubicacion del evento. Opcional."},
                    },
                    "required": ["title", "date"],
                },
            },
            {
                "name": "calendar_search_events",
                "description": "Busca eventos en el calendario por texto",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Texto a buscar en los eventos"},
                        "count": {"type": "integer", "description": "Cantidad maxima. Default: 5"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "calendar_delete_event",
                "description": "Elimina un evento del calendario por su ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "ID del evento a eliminar"},
                    },
                    "required": ["event_id"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        service = self._get_service()
        if not service:
            return "Error: Google Calendar no autorizado. Ejecutar auth_google.py primero."

        if function_name == "calendar_list_events":
            days = arguments.get("days", 7)
            count = arguments.get("count", 10)
            try:
                now = datetime.utcnow()
                time_min = now.isoformat() + "Z"
                time_max = (now + timedelta(days=days)).isoformat() + "Z"
                result = service.events().list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=count,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()
                events = result.get("items", [])
                if not events:
                    return "No hay eventos en los proximos " + str(days) + " dias"
                lines = []
                for ev in events:
                    start = ev["start"].get("dateTime", ev["start"].get("date", ""))
                    end = ev["end"].get("dateTime", ev["end"].get("date", ""))
                    title = ev.get("summary", "(sin titulo)")
                    location = ev.get("location", "")
                    eid = ev.get("id", "")
                    line = title + "\n  Inicio: " + start + "\n  Fin: " + end
                    if location:
                        line += "\n  Lugar: " + location
                    line += "\n  ID: " + eid
                    lines.append(line)
                return "Eventos proximos (" + str(len(events)) + "):\n\n" + "\n---\n".join(lines)
            except Exception as e:
                return "Error: " + str(e)

        elif function_name == "calendar_create_event":
            title = arguments.get("title", "")
            date = arguments.get("date", "")
            start_time = arguments.get("start_time", "")
            end_time = arguments.get("end_time", "")
            description = arguments.get("description", "")
            location = arguments.get("location", "")
            if not title or not date:
                return "Error: titulo y fecha requeridos"
            try:
                if start_time:
                    start_dt = date + "T" + start_time + ":00"
                    if end_time:
                        end_dt = date + "T" + end_time + ":00"
                    else:
                        h, m = start_time.split(":")
                        end_h = str(int(h) + 1).zfill(2)
                        end_dt = date + "T" + end_h + ":" + m + ":00"
                    event = {
                        "summary": title,
                        "start": {"dateTime": start_dt, "timeZone": "America/Bogota"},
                        "end": {"dateTime": end_dt, "timeZone": "America/Bogota"},
                    }
                else:
                    event = {
                        "summary": title,
                        "start": {"date": date},
                        "end": {"date": date},
                    }
                if description:
                    event["description"] = description
                if location:
                    event["location"] = location
                created = service.events().insert(calendarId="primary", body=event).execute()
                return "Evento creado: " + title + " | " + date + (" " + start_time if start_time else " (todo el dia)") + "\nID: " + created.get("id", "")
            except Exception as e:
                return "Error creando evento: " + str(e)

        elif function_name == "calendar_search_events":
            query = arguments.get("query", "")
            count = arguments.get("count", 5)
            if not query:
                return "Error: query vacia"
            try:
                now = datetime.utcnow().isoformat() + "Z"
                result = service.events().list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=count,
                    singleEvents=True,
                    orderBy="startTime",
                    q=query,
                ).execute()
                events = result.get("items", [])
                if not events:
                    return "No se encontraron eventos con: " + query
                lines = []
                for ev in events:
                    start = ev["start"].get("dateTime", ev["start"].get("date", ""))
                    title = ev.get("summary", "(sin titulo)")
                    lines.append(title + " | " + start + " | ID: " + ev.get("id", ""))
                return "Eventos encontrados (" + str(len(events)) + "):\n" + "\n".join(lines)
            except Exception as e:
                return "Error: " + str(e)

        elif function_name == "calendar_delete_event":
            event_id = arguments.get("event_id", "")
            if not event_id:
                return "Error: ID requerido"
            try:
                service.events().delete(calendarId="primary", eventId=event_id).execute()
                return "Evento eliminado: " + event_id
            except Exception as e:
                return "Error: " + str(e)

        return "Funcion no encontrada"
