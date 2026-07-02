"""Time and date skill."""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from skills.base import Intent, Skill, SkillResponse


class TimeSkill(Skill):
    def __init__(self, timezone: str = "America/Bogota"):
        super().__init__("time", "Current time and date")
        self.timezone = timezone
        self.keywords = ["time", "date", "day"]
        self.example_intents = ["What time is it?", "What is today's date?"]

    def can_handle(self, intent: Intent) -> bool:
        return intent.intent_type in {"get_time", "get_date"}

    def execute(self, intent: Intent) -> SkillResponse:
        try:
            now = datetime.now(ZoneInfo(self.timezone))
            timezone = self.timezone
        except ZoneInfoNotFoundError:
            now = datetime.now().astimezone()
            timezone = str(now.tzinfo)
        if intent.intent_type == "get_date":
            text = now.strftime("Today is %A, %B %d, %Y.")
        else:
            text = now.strftime("It is %I:%M %p.")
        return SkillResponse(text, data={"timezone": timezone, "iso": now.isoformat()})
