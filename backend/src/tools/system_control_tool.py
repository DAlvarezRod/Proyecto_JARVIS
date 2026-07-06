import subprocess
import os
from typing import Any, Dict, List

from .base import Tool


class SystemControlTool(Tool):
    name = "system_control"
    description = "Control system volume, power, screen, and monitor performance"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "volume_up",
                "description": "Sube el volumen del computador.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "steps": {"type": "integer", "description": "Cuantos pasos subir (cada paso ~2%%). Default: 5 (~10%%)"},
                    },
                },
            },
            {
                "name": "volume_down",
                "description": "Baja el volumen del computador.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "steps": {"type": "integer", "description": "Cuantos pasos bajar (cada paso ~2%%). Default: 5 (~10%%)"},
                    },
                },
            },
            {
                "name": "volume_set",
                "description": "Pone el volumen del computador en un nivel especifico.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "integer", "description": "Nivel de volumen de 0 a 100"},
                    },
                    "required": ["level"],
                },
            },
            {
                "name": "volume_mute",
                "description": "Silencia o des-silencia el volumen del computador.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "lock_screen",
                "description": "Bloquea la pantalla del computador.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "sleep_pc",
                "description": "Pone el computador en modo suspension (sleep).",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "shutdown_pc",
                "description": "Apaga el computador. Puede programar el apagado en X minutos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "minutes": {"type": "integer", "description": "Minutos para apagar. 0 = inmediato. Default: 0"},
                    },
                },
            },
            {
                "name": "restart_pc",
                "description": "Reinicia el computador.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "minutes": {"type": "integer", "description": "Minutos para reiniciar. 0 = inmediato. Default: 0"},
                    },
                },
            },
            {
                "name": "cancel_shutdown",
                "description": "Cancela un apagado o reinicio programado.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "system_stats",
                "description": "Muestra el uso actual de CPU, RAM y disco del computador.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "brightness_set",
                "description": "Ajusta el brillo de la pantalla (0-100).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "integer", "description": "Nivel de brillo de 0 a 100"},
                    },
                    "required": ["level"],
                },
            },
            {
                "name": "brightness_get",
                "description": "Muestra el nivel actual de brillo de la pantalla.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "wifi_toggle",
                "description": "Activa o desactiva el WiFi.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean", "description": "true para activar, false para desactivar"},
                    },
                    "required": ["enabled"],
                },
            },
            {
                "name": "network_info",
                "description": "Muestra info de la red: WiFi conectado, IP, señal.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "battery_info",
                "description": "Muestra info detallada de la bateria del portatil.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "power_plan",
                "description": "Muestra o cambia el plan de energia (balanced, powersaver, performance).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plan": {"type": "string", "description": "Plan a activar: balanced, powersaver o performance. Si no se da, muestra el actual."},
                    },
                },
            },
            {
                "name": "bluetooth_toggle",
                "description": "Activa o desactiva el Bluetooth.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean", "description": "true para activar, false para desactivar"},
                    },
                    "required": ["enabled"],
                },
            },
        ]

    def _ps(self, command, timeout=10):
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True, text=True, timeout=timeout,
            )
            return r.stdout.strip(), None
        except Exception as e:
            return None, str(e)

    def execute(self, function_name, arguments):
        if function_name == "volume_up":
            return self._volume_change("up", arguments.get("steps", 5))
        elif function_name == "volume_down":
            return self._volume_change("down", arguments.get("steps", 5))
        elif function_name == "volume_set":
            return self._volume_set(arguments.get("level", 50))
        elif function_name == "volume_mute":
            return self._volume_mute()
        elif function_name == "lock_screen":
            return self._lock()
        elif function_name == "sleep_pc":
            return self._sleep()
        elif function_name == "shutdown_pc":
            return self._shutdown(arguments.get("minutes", 0))
        elif function_name == "restart_pc":
            return self._restart(arguments.get("minutes", 0))
        elif function_name == "cancel_shutdown":
            return self._cancel_shutdown()
        elif function_name == "system_stats":
            return self._stats()
        elif function_name == "brightness_set":
            return self._brightness_set(arguments.get("level", 50))
        elif function_name == "brightness_get":
            return self._brightness_get()
        elif function_name == "wifi_toggle":
            return self._wifi_toggle(arguments.get("enabled", True))
        elif function_name == "network_info":
            return self._network_info()
        elif function_name == "battery_info":
            return self._battery_info()
        elif function_name == "power_plan":
            return self._power_plan(arguments.get("plan", ""))
        elif function_name == "bluetooth_toggle":
            return self._bluetooth_toggle(arguments.get("enabled", True))
        return "Funcion no encontrada"

    def _volume_change(self, direction, steps):
        steps = max(1, min(25, steps))
        key = "175" if direction == "up" else "174"
        ps = "$s=New-Object -ComObject WScript.Shell;for($i=0;$i -lt " + str(steps) + ";$i++){$s.SendKeys([char]" + key + ")}"
        out, err = self._ps(ps)
        if err:
            return "Error: " + err
        word = "subido" if direction == "up" else "bajado"
        return "Volumen " + word + " (~" + str(steps * 2) + "%)"

    def _volume_set(self, level):
        level = max(0, min(100, level))
        up_steps = level // 2
        ps = (
            "$s=New-Object -ComObject WScript.Shell;"
            "for($i=0;$i -lt 50;$i++){$s.SendKeys([char]174)};"
            "for($i=0;$i -lt " + str(up_steps) + ";$i++){$s.SendKeys([char]175)}"
        )
        out, err = self._ps(ps, timeout=15)
        if err:
            return "Error: " + err
        return "Volumen ajustado a ~" + str(level) + "%"

    def _volume_mute(self):
        ps = "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
        out, err = self._ps(ps)
        if err:
            return "Error: " + err
        return "Volumen silenciado/des-silenciado"

    def _lock(self):
        try:
            subprocess.run(["rundll32", "user32.dll,LockWorkStation"], timeout=5)
            return "Pantalla bloqueada"
        except Exception as e:
            return "Error: " + str(e)

    def _sleep(self):
        try:
            subprocess.run(
                ["rundll32", "powrprof.dll,SetSuspendState", "0,1,0"],
                timeout=5,
            )
            return "Computador en suspension"
        except Exception as e:
            return "Error: " + str(e)

    def _shutdown(self, minutes):
        minutes = max(0, minutes)
        seconds = minutes * 60
        try:
            subprocess.run(
                ["shutdown", "/s", "/t", str(seconds)],
                capture_output=True, timeout=5,
            )
            if minutes == 0:
                return "Apagando el computador..."
            return "Computador se apagara en " + str(minutes) + " minutos"
        except Exception as e:
            return "Error: " + str(e)

    def _restart(self, minutes):
        minutes = max(0, minutes)
        seconds = minutes * 60
        try:
            subprocess.run(
                ["shutdown", "/r", "/t", str(seconds)],
                capture_output=True, timeout=5,
            )
            if minutes == 0:
                return "Reiniciando el computador..."
            return "Computador se reiniciara en " + str(minutes) + " minutos"
        except Exception as e:
            return "Error: " + str(e)

    def _cancel_shutdown(self):
        try:
            subprocess.run(
                ["shutdown", "/a"],
                capture_output=True, timeout=5,
            )
            return "Apagado/reinicio cancelado"
        except Exception as e:
            return "Error: " + str(e)

    def _stats(self):
        ps = (
            "$cpu = (Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average;"
            "$os = Get-WmiObject Win32_OperatingSystem;"
            "$totalRAM = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1);"
            "$freeRAM = [math]::Round($os.FreePhysicalMemory / 1MB, 1);"
            "$usedRAM = $totalRAM - $freeRAM;"
            "$disks = Get-WmiObject Win32_LogicalDisk -Filter 'DriveType=3' | "
            "ForEach-Object { $_.DeviceID + ' ' + [math]::Round($_.FreeSpace/1GB,1).ToString() + 'GB libres de ' + [math]::Round($_.Size/1GB,1).ToString() + 'GB' };"
            "Write-Output \"CPU: ${cpu}%\";"
            "Write-Output \"RAM: ${usedRAM}GB / ${totalRAM}GB\";"
            "Write-Output ($disks -join \"`n\")"
        )
        out, err = self._ps(ps)
        if err:
            return "Error: " + err
        return out if out else "No se pudo obtener info del sistema"
    def _brightness_set(self, level):
        level = max(0, min(100, level))
        ps = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1," + str(level) + ")"
        out, err = self._ps(ps)
        if err:
            return "No se pudo ajustar el brillo. Tu monitor puede no soportar esta funcion."
        return "Brillo ajustado a " + str(level) + "%"

    def _brightness_get(self):
        ps = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"
        out, err = self._ps(ps)
        if err or not out:
            return "No se pudo obtener el brillo."
        return "Brillo actual: " + out + "%"

    def _wifi_toggle(self, enabled):
        action = "enable" if enabled else "disable"
        ps = "netsh interface set interface 'Wi-Fi' admin=" + action
        out, err = self._ps(ps)
        if err:
            return "Error: " + err
        word = "activado" if enabled else "desactivado"
        return "WiFi " + word

    def _network_info(self):
        ps = (
            "$profiles = Get-NetConnectionProfile;"
            "$adapters = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'};"
            "$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.*'});"
            "foreach($p in $profiles){"
            "Write-Output \"Red: $($p.Name)\";"
            "Write-Output \"Interfaz: $($p.InterfaceAlias)\";"
            "};"
            "foreach($a in $adapters){"
            "Write-Output \"Adaptador: $($a.Name) - $($a.LinkSpeed)\";"
            "};"
            "foreach($i in $ip){"
            "Write-Output \"IP: $($i.IPAddress) ($($i.InterfaceAlias))\";"
            "}"
        )
        out, err = self._ps(ps)
        if err:
            return "Error: " + err
        return out if out else "No se pudo obtener info de red"

    def _battery_info(self):
        ps = (
            "$b = Get-WmiObject Win32_Battery;"
            "$status = switch($b.BatteryStatus){"
            "1{'Descargando'} 2{'Cargando (AC)'} 3{'Carga completa'} 4{'Baja'} 5{'Critica'} "
            "6{'Cargando'} 7{'Cargando y alta'} 8{'Cargando y baja'} 9{'Cargando y critica'} "
            "default{'Desconocido'}};"
            "$time = if($b.EstimatedRunTime -and $b.EstimatedRunTime -lt 71582788){"
            "[math]::Floor($b.EstimatedRunTime/60).ToString() + 'h ' + ($b.EstimatedRunTime%60).ToString() + 'min'"
            "} else {'Calculando...'};"
            "Write-Output \"Bateria: $($b.EstimatedChargeRemaining)%\";"
            "Write-Output \"Estado: $status\";"
            "Write-Output \"Tiempo restante: $time\""
        )
        out, err = self._ps(ps)
        if err:
            return "Error: " + err
        return out if out else "No se encontro bateria"

    def _power_plan(self, plan):
        if not plan:
            ps = "powercfg /getactivescheme"
            out, err = self._ps(ps)
            if err:
                return "Error: " + err
            return "Plan actual: " + out
        plans = {
            "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
            "powersaver": "a1841308-3541-4fab-bc81-f71556f20b4a",
            "performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        }
        guid = plans.get(plan.lower())
        if not guid:
            return "Plan no reconocido. Usa: balanced, powersaver o performance"
        ps = "powercfg /setactive " + guid
        out, err = self._ps(ps)
        if err:
            return "Error: " + err
        return "Plan de energia cambiado a: " + plan

    def _bluetooth_toggle(self, enabled):
        if enabled:
            ps = "Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Enable-PnpDevice -Confirm:$false -ErrorAction SilentlyContinue"
        else:
            ps = "Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Disable-PnpDevice -Confirm:$false -ErrorAction SilentlyContinue"
        out, err = self._ps(ps)
        if err:
            return "Error. Puede requerir ejecutar como administrador."
        word = "activado" if enabled else "desactivado"
        return "Bluetooth " + word