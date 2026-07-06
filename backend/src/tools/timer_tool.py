import threading
import subprocess
import os
import time
from typing import Any, Dict, List

from .base import Tool


class TimerTool(Tool):
    name = "timers"
    description = "Set timers, alarms, and reminders"

    def __init__(self):
        self.active_timers = {}
        self.timer_counter = 0

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "set_timer",
                "description": "Pone un temporizador que avisa cuando termine. Ejemplo: 'ponme un timer de 5 minutos'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "minutes": {"type": "number", "description": "Minutos para el timer"},
                        "label": {"type": "string", "description": "Nombre o razon del timer. Default: Timer"},
                    },
                    "required": ["minutes"],
                },
            },
            {
                "name": "set_alarm",
                "description": "Pone una alarma a una hora especifica. Ejemplo: 'despiertame a las 7:30'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hour": {"type": "integer", "description": "Hora (0-23)"},
                        "minute": {"type": "integer", "description": "Minuto (0-59)"},
                        "label": {"type": "string", "description": "Nombre de la alarma. Default: Alarma"},
                    },
                    "required": ["hour", "minute"],
                },
            },
            {
                "name": "list_timers",
                "description": "Lista todos los timers y alarmas activos.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "cancel_timer",
                "description": "Cancela un timer o alarma activo por su ID o nombre.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timer_id": {"type": "string", "description": "ID o nombre del timer a cancelar"},
                    },
                    "required": ["timer_id"],
                },
            },
        ]

    def _notify(self, label):
        try:
            sound_ps = (
                "try {"
                "$p = New-Object System.Media.SoundPlayer;"
                "$p.SoundLocation = 'C:\\Windows\\Media\\Alarm01.wav';"
                "$p.PlaySync(); $p.PlaySync(); $p.PlaySync()"
                "} catch {"
                "for($i=0;$i -lt 5;$i++){"
                "[Console]::Beep(1000,300);Start-Sleep -Milliseconds 200;"
                "[Console]::Beep(1500,300);Start-Sleep -Milliseconds 200}}"
            )
            popup_ps = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null;"
                "[System.Windows.Forms.MessageBox]::Show('" + label + " - Tiempo cumplido!', 'Illo Timer', 'OK', 'Information')"
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", sound_ps],
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", popup_ps],
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except Exception:
            pass

    def _timer_thread(self, timer_id, seconds, label):
        time.sleep(seconds)
        if timer_id in self.active_timers:
            self._notify(label)
            del self.active_timers[timer_id]

    def execute(self, function_name, arguments):
        if function_name == "set_timer":
            return self._set_timer(arguments)
        elif function_name == "set_alarm":
            return self._set_alarm(arguments)
        elif function_name == "list_timers":
            return self._list_timers()
        elif function_name == "cancel_timer":
            return self._cancel_timer(arguments)
        return "Funcion no encontrada"

    def _set_timer(self, arguments):
        minutes = arguments.get("minutes", 0)
        label = arguments.get("label", "Timer")
        if minutes <= 0:
            return "Error: los minutos deben ser mayor a 0"

        self.timer_counter += 1
        timer_id = "timer_" + str(self.timer_counter)
        seconds = int(minutes * 60)

        end_time = time.time() + seconds
        self.active_timers[timer_id] = {
            "label": label,
            "end_time": end_time,
            "minutes": minutes,
        }

        t = threading.Thread(target=self._timer_thread, args=(timer_id, seconds, label), daemon=True)
        t.start()

        if minutes >= 60:
            h = int(minutes // 60)
            m = int(minutes % 60)
            tiempo = str(h) + "h " + str(m) + "min" if m else str(h) + "h"
        else:
            tiempo = str(minutes) + " minutos"

        return "Timer '" + label + "' puesto por " + tiempo + " (ID: " + timer_id + ")"

    def _set_alarm(self, arguments):
        hour = arguments.get("hour", 0)
        minute = arguments.get("minute", 0)
        label = arguments.get("label", "Alarma")

        now = time.localtime()
        alarm_today = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, hour, minute, 0, 0, 0, -1))

        if alarm_today <= time.time():
            alarm_today += 86400

        seconds = int(alarm_today - time.time())

        self.timer_counter += 1
        timer_id = "alarm_" + str(self.timer_counter)
        self.active_timers[timer_id] = {
            "label": label,
            "end_time": alarm_today,
            "alarm_time": str(hour).zfill(2) + ":" + str(minute).zfill(2),
        }

        t = threading.Thread(target=self._timer_thread, args=(timer_id, seconds, label), daemon=True)
        t.start()

        hora_str = str(hour).zfill(2) + ":" + str(minute).zfill(2)
        return "Alarma '" + label + "' puesta para las " + hora_str + " (ID: " + timer_id + ")"

    def _list_timers(self):
        if not self.active_timers:
            return "No hay timers ni alarmas activos"
        lines = []
        for tid, info in self.active_timers.items():
            remaining = int(info["end_time"] - time.time())
            if remaining < 0:
                continue
            mins = remaining // 60
            secs = remaining % 60
            line = tid + ": " + info["label"] + " - "
            if "alarm_time" in info:
                line += "alarma a las " + info["alarm_time"] + " ("
            else:
                line += "timer ("
            line += str(mins) + "min " + str(secs) + "s restantes)"
            lines.append(line)
        if not lines:
            return "No hay timers ni alarmas activos"
        return "Timers activos:\n" + "\n".join(lines)

    def _cancel_timer(self, arguments):
        timer_id = arguments.get("timer_id", "").strip()
        if timer_id in self.active_timers:
            del self.active_timers[timer_id]
            return "Timer " + timer_id + " cancelado"
        for tid, info in list(self.active_timers.items()):
            if info["label"].lower() == timer_id.lower():
                del self.active_timers[tid]
                return "Timer '" + timer_id + "' cancelado"
        return "No se encontro timer: " + timer_id