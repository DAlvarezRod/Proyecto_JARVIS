"""Smart home skill wrapper around SmartHomeHub."""

from typing import Callable, Optional

from skills.base import Intent, Skill, SkillResponse


class SmartHomeSkill(Skill):
    def __init__(self, hub, on_command: Optional[Callable] = None):
        super().__init__("smart_home", "Control simulated smart home devices")
        self.hub = hub
        self.on_command = on_command
        self.keywords = ["light", "door", "thermostat", "security", "camera"]
        self.example_intents = ["Turn on the kitchen light", "Lock the front door"]

    def can_handle(self, intent: Intent) -> bool:
        return intent.intent_type in {"smart_home_control", "smart_home_status"}

    def execute(self, intent: Intent) -> SkillResponse:
        if intent.intent_type == "smart_home_status":
            status = self.hub.get_status(
                device_type=intent.parameters.get("device_type"),
                location=intent.parameters.get("location"),
            )
            if not status["summary"]:
                return SkillResponse("I could not find any matching smart home devices.", success=False)
            return SkillResponse(" ".join(status["summary"]), data=status)

        result = self.hub.execute_command(
            action=intent.parameters.get("action"),
            device_type=intent.parameters.get("device_type"),
            location=intent.parameters.get("location"),
            value=intent.parameters.get("value"),
        )
        if self.on_command:
            self.on_command(result)
        return SkillResponse(result["message"], success=result["success"], data=result)
