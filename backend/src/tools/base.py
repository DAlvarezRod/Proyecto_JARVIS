from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def get_definitions(self) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def execute(self, function_name: str, arguments: Dict[str, Any]) -> str:
        ...
