"""News skill using Hacker News public API as a keyless source."""

from __future__ import annotations

import requests

from skills.base import Intent, Skill, SkillResponse


class NewsSkill(Skill):
    def __init__(self, timeout: int = 5):
        super().__init__("news", "Latest technology headlines")
        self.timeout = timeout
        self.keywords = ["news", "headlines", "latest"]
        self.example_intents = ["What are the latest tech headlines?", "Tell me the news"]

    def can_handle(self, intent: Intent) -> bool:
        return intent.intent_type == "get_news"

    def execute(self, intent: Intent) -> SkillResponse:
        try:
            story_ids = requests.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=self.timeout,
            ).json()[:3]
            stories = []
            for story_id in story_ids:
                story = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                    timeout=self.timeout,
                ).json()
                if story and story.get("title"):
                    stories.append(story["title"])
        except Exception as exc:
            return SkillResponse(f"I could not fetch news right now: {exc}", success=False)

        if not stories:
            return SkillResponse("I could not find headlines right now.", success=False)
        return SkillResponse("Top headlines: " + " | ".join(stories), data={"headlines": stories})
