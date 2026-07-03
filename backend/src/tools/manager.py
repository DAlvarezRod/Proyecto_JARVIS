from typing import Any, Dict, List

from .base import Tool


class ToolManager:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get_definitions(self) -> List[Dict[str, Any]]:
        defs = []
        for tool in self._tools.values():
            for fn_def in tool.get_definitions():
                defs.append({"type": "function", "function": fn_def})
        return defs

    def execute(self, function_name: str, arguments: Dict[str, Any]) -> str:
        for tool in self._tools.values():
            for fn_def in tool.get_definitions():
                if fn_def["name"] == function_name:
                    return tool.execute(function_name, arguments)
        return "Error: tool not found"
