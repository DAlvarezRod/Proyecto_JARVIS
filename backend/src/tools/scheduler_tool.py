import threading
import subprocess
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List


class SchedulerTool:
    name = "scheduler"
    description = "Schedule recurring and one-time tasks and reminders"

    def __init__(self):
        self.tasks = {}
        self.task_counter = 0
        self.running = True
        self.lock = threading.Lock()
        self.checker = threading.Thread(target=self._check_loop, daemon=True)
        self.checker.start()

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "schedule_task",
                "description": "Programa un recordatorio o tarea. Puede ser una sola vez, cada cierto intervalo, o diario a una hora fija.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Mensaje del recordatorio"},
                        "time": {"type": "string", "description": "Hora en formato HH:MM (24h). Ej: 07:00, 14:30"},
                        "daily": {"type": "boolean", "description": "Si true, se repite todos los dias a la hora indicada"},
                        "interval_minutes": {"type": "integer", "description": "Repetir cada X minutos"},
                        "delay_minutes": {"type": "integer", "description": "Ejecutar una sola vez en X minutos"},
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "list_scheduled_tasks",
                "description": "Lista todas las tareas y recordatorios programados activos",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "cancel_scheduled_task",
                "description": "Cancela una tarea programada por su ID o nombre",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "ID numerico o texto del nombre de la tarea"},
                    },
                    "required": ["task_id"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "schedule_task":
            return self._schedule(arguments)
        elif function_name == "list_scheduled_tasks":
            return self._list_tasks()
        elif function_name == "cancel_scheduled_task":
            return self._cancel_task(arguments)
        return "Funcion no encontrada"

    def _schedule(self, params):
        message = params.get("message", "")
        time_str = params.get("time", "")
        daily = params.get("daily", False)
        interval = params.get("interval_minutes", 0)
        delay = params.get("delay_minutes", 0)

        if not message:
            return "Error: mensaje requerido"

        self.task_counter += 1
        task_id = str(self.task_counter)
        now = datetime.now()

        if delay > 0:
            next_run = now + timedelta(minutes=delay)
            task = {
                "id": task_id,
                "message": message,
                "next_run": next_run,
                "recurring": False,
                "type": "delay",
                "delay_minutes": delay,
            }
        elif interval > 0:
            next_run = now + timedelta(minutes=interval)
            task = {
                "id": task_id,
                "message": message,
                "next_run": next_run,
                "recurring": True,
                "type": "interval",
                "interval_minutes": interval,
            }
        elif time_str:
            try:
                hour, minute = map(int, time_str.split(":"))
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                task = {
                    "id": task_id,
                    "message": message,
                    "next_run": target,
                    "recurring": daily,
                    "type": "daily" if daily else "once",
                    "time": time_str,
                }
            except ValueError:
                return "Error: formato de hora invalido. Usa HH:MM (ej: 07:00)"
        else:
            return "Error: indica delay_minutes, interval_minutes, o time"

        with self.lock:
            self.tasks[task_id] = task

        if task["type"] == "delay":
            desc = "en " + str(delay) + " minutos"
        elif task["type"] == "interval":
            if interval >= 60:
                desc = "cada " + str(interval // 60) + " hora(s)"
            else:
                desc = "cada " + str(interval) + " minutos"
        elif task["type"] == "daily":
            desc = "todos los dias a las " + time_str
        else:
            desc = "una vez a las " + time_str

        return "Tarea #" + task_id + " programada: '" + message + "' — " + desc + ". Proxima ejecucion: " + task["next_run"].strftime("%Y-%m-%d %H:%M")

    def _list_tasks(self):
        with self.lock:
            if not self.tasks:
                return "No hay tareas programadas"
            lines = []
            for tid, t in self.tasks.items():
                icon = "[repetir]" if t["recurring"] else "[una vez]"
                remaining = t["next_run"] - datetime.now()
                mins = max(0, int(remaining.total_seconds() / 60))
                if mins >= 60:
                    time_left = str(mins // 60) + "h " + str(mins % 60) + "m"
                else:
                    time_left = str(mins) + " min"
                lines.append(icon + " #" + tid + ": " + t["message"] + " — Proxima: " + t["next_run"].strftime("%H:%M") + " (en " + time_left + ")")
            return "Tareas programadas:\n" + "\n".join(lines)

    def _cancel_task(self, params):
        task_id = str(params.get("task_id", ""))
        with self.lock:
            if task_id in self.tasks:
                name = self.tasks[task_id]["message"]
                del self.tasks[task_id]
                return "Tarea #" + task_id + " cancelada: '" + name + "'"
            for tid, t in list(self.tasks.items()):
                if task_id.lower() in t["message"].lower():
                    del self.tasks[tid]
                    return "Tarea #" + tid + " cancelada: '" + t["message"] + "'"
        return "No se encontro tarea con ID o nombre '" + task_id + "'"

    def _check_loop(self):
        while self.running:
            now = datetime.now()
            with self.lock:
                for task_id, task in list(self.tasks.items()):
                    if now >= task["next_run"]:
                        threading.Thread(target=self._notify, args=(task["message"],), daemon=True).start()
                        if task["recurring"]:
                            if task["type"] == "interval":
                                task["next_run"] = now + timedelta(minutes=task["interval_minutes"])
                            elif task["type"] == "daily":
                                task["next_run"] = now + timedelta(days=1)
                        else:
                            del self.tasks[task_id]
            time.sleep(30)

    def _sanitize(self, text):
        return text.replace('"', "'").replace("$", "").replace("`", "").replace(";", ",")

    def _notify(self, message):
        safe_msg = self._sanitize(message)
        try:
            sound = r"C:\Windows\Media\Alarm01.wav"
            ps = (
                'Add-Type -AssemblyName System.Windows.Forms;'
                'Add-Type -AssemblyName PresentationCore;'
                '$p = New-Object System.Windows.Media.MediaPlayer;'
                '$p.Open([Uri]"' + sound + '");'
                '$p.Play(); Start-Sleep -Seconds 2;'
                '$p.Play(); Start-Sleep -Seconds 2;'
                '[System.Windows.Forms.MessageBox]::Show("' + safe_msg + '", "Illo - Recordatorio", "OK", "Information")'
            )
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps],
                creationflags=0x08000000
            )
        except Exception:
            pass