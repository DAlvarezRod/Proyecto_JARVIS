from typing import Any, Dict, List

from .base import Tool


class RouterTool(Tool):
    name = "router"
    description = "Manage LLM providers"

    def __init__(self, router):
        self.router = router

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "router_list_providers",
                "description": "Lista los proveedores LLM configurados y cual esta en uso",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "router_set_primary",
                "description": "Cambia el proveedor LLM principal. Los demas quedan como fallback.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string", "description": "Nombre: openrouter, openai, ollama, claude-fallback"},
                    },
                    "required": ["provider"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "router_list_providers":
            providers = self.router.list_providers()
            if not providers:
                return "No hay proveedores configurados"
            lines = []
            for i, p in enumerate(providers):
                status = ""
                if p["active"]:
                    status = " [EN USO]"
                elif not p["enabled"]:
                    status = " [OFF]"
                lines.append(str(i + 1) + ". " + p["name"] + " (" + p["model"] + ")" + status)
            return "Proveedores LLM:\n" + "\n".join(lines)

        elif function_name == "router_set_primary":
            name = arguments.get("provider", "")
            if self.router.set_primary(name):
                return "Proveedor principal: " + name
            return "No encontrado: " + name

        return "Funcion no encontrada"