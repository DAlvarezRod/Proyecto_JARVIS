"""Greeting skill."""

from skills.base import Intent, Skill, SkillResponse


class GreetingSkill(Skill):
    def __init__(self):
        super().__init__("greeting", "Friendly greetings and introductions")
        self.keywords = ["hello", "hi", "hey", "good morning", "good evening"]
        self.example_intents = ["Hello JARVIS", "Hey", "Good morning"]

    def can_handle(self, intent: Intent) -> bool:
        return intent.intent_type == "greeting"

    def execute(self, intent: Intent) -> SkillResponse:
        return SkillResponse("Hello. JARVIS is online and ready.")
