import platform
import socket
import psutil
from typing import Any, Dict, List

from .base import Tool


class SystemInfoTool(Tool):
    name = "system_info"
    description = "Gets system information like CPU, RAM, disk, IP"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_system_info",
                "description": "Obtiene informacion del sistema: CPU, RAM, disco, SO, IP",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_top_processes",
                "description": "Muestra los procesos que mas recursos consumen",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sort_by": {"type": "string", "description": "Ordenar por 'cpu' o 'memory'. Default: memory"},
                        "count": {"type": "integer", "description": "Cantidad de procesos. Default: 10"},
                    },
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "get_system_info":
            try:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory()
                disk = psutil.disk_usage("C:\\")
                uname = platform.uname()
                ip = socket.gethostbyname(socket.gethostname())
                return (
                    "SO: " + uname.system + " " + uname.release + " " + uname.version
                    + "\nPC: " + uname.node
                    + "\nCPU: " + uname.processor
                    + "\nUso CPU: " + str(cpu) + "%"
                    + "\nRAM total: " + str(round(ram.total / (1024**3), 1)) + " GB"
                    + "\nRAM usada: " + str(round(ram.used / (1024**3), 1)) + " GB (" + str(ram.percent) + "%)"
                    + "\nRAM libre: " + str(round(ram.available / (1024**3), 1)) + " GB"
                    + "\nDisco C: total: " + str(round(disk.total / (1024**3), 1)) + " GB"
                    + "\nDisco C: usado: " + str(round(disk.used / (1024**3), 1)) + " GB (" + str(disk.percent) + "%)"
                    + "\nDisco C: libre: " + str(round(disk.free / (1024**3), 1)) + " GB"
                    + "\nIP local: " + ip
                )
            except Exception as e:
                return "Error: " + str(e)

        elif function_name == "get_top_processes":
            try:
                sort_by = arguments.get("sort_by", "memory")
                count = arguments.get("count", 10)
                procs = []
                for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                    try:
                        info = p.info
                        procs.append(info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                key = "memory_percent" if sort_by == "memory" else "cpu_percent"
                procs.sort(key=lambda x: x.get(key, 0) or 0, reverse=True)
                lines = []
                for p in procs[:count]:
                    lines.append(
                        str(p["pid"]) + " | " + str(p["name"])
                        + " | CPU: " + str(round(p.get("cpu_percent", 0) or 0, 1)) + "%"
                        + " | RAM: " + str(round(p.get("memory_percent", 0) or 0, 1)) + "%"
                    )
                return "Top " + str(count) + " por " + sort_by + ":\n" + "\n".join(lines)
            except Exception as e:
                return "Error: " + str(e)

        return "Funcion no encontrada"
