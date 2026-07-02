"""Load manifest-based custom skills for JARVIS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from logger import get_logger
from skills.base import Intent, Skill, SkillResponse


class ManifestSkill(Skill):
    """A simple custom skill defined by a JSON manifest."""

    def __init__(self, manifest: Dict[str, Any], source: str):
        super().__init__(
            str(manifest["name"]),
            str(manifest.get("description", "Custom manifest skill")),
        )
        self.source = source
        self.enabled = bool(manifest.get("enabled", True))
        self.keywords = list(manifest.get("keywords", []))
        self.example_intents = list(manifest.get("examples", []))
        self.intent_types = set(manifest.get("intent_types", []))
        self.response_text = str(manifest.get("response", "Custom skill executed."))

    def can_handle(self, intent: Intent) -> bool:
        if self.intent_types and intent.intent_type in self.intent_types:
            return True
        text = intent.original_text.lower()
        return any(keyword.lower() in text for keyword in self.keywords)

    def execute(self, intent: Intent) -> SkillResponse:
        return SkillResponse(
            self.response_text,
            data={
                "skill": self.name,
                "source": self.source,
                "original_text": intent.original_text,
            },
        )

    def get_metadata(self) -> Dict[str, Any]:
        metadata = super().get_metadata()
        metadata.update({
            "source": self.source,
            "type": "custom_manifest",
            "intent_types": sorted(self.intent_types),
        })
        return metadata


class CustomSkillLoader:
    """Discover and instantiate custom manifest skills."""

    def __init__(self, skills_dir: str = "custom_skills"):
        self.skills_dir = Path(skills_dir)
        self.logger = get_logger("custom_skill_loader")

    def discover(self) -> List[Dict[str, Any]]:
        if not self.skills_dir.exists():
            return []
        manifests: List[Dict[str, Any]] = []
        for path in sorted(self.skills_dir.glob("*/skill.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                data["_source"] = str(path)
                manifests.append(data)
            except Exception as exc:
                self.logger.warning("Could not load custom skill manifest %s: %s", path, exc)
        return manifests

    def load_skills(self) -> List[ManifestSkill]:
        skills: List[ManifestSkill] = []
        for manifest in self.discover():
            if not manifest.get("enabled", True):
                continue
            if not manifest.get("name"):
                self.logger.warning("Skipping custom skill without name: %s", manifest.get("_source"))
                continue
            skills.append(ManifestSkill(manifest, source=str(manifest.get("_source", ""))))
        return skills
