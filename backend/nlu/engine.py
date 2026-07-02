"""Phase 3 NLP engine for intent recognition and entity extraction."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import spacy

from logger import get_logger
from skills.base import Intent
from smart_home import CommandParser, SmartHomeCommand


class NLUEngine:
    """Convert raw user text into JARVIS intents."""

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        confidence_threshold: float = 0.7,
        max_context_history: int = 10,
    ):
        self.logger = get_logger("nlu.engine")
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.max_context_history = max_context_history
        self.command_parser = CommandParser()
        self.context: List[Dict[str, Any]] = []
        self.nlp = self._load_model(model_name)

    def parse(self, text: str) -> Intent:
        """Parse text into an Intent with entities and context."""
        doc = self.nlp(text)
        command = self.command_parser.parse(text)
        entities = self.extract_entities(doc, command)
        intent_type = self.recognize_intent(text, command)
        self._enrich_entities(text, intent_type, entities)
        confidence = self.score_intent(intent_type, command, entities)

        intent = Intent(
            intent_type=intent_type,
            entities=entities,
            original_text=text,
            confidence=confidence,
            skill_name=self._skill_for_intent(intent_type),
            parameters={**self._parameters_from_command(command), **self._parameters_from_entities(entities)},
            context_data={"recent_intents": self.context[-3:]},
        )
        self._remember(intent)
        return intent

    def extract_entities(self, doc: Any, command: SmartHomeCommand) -> Dict[str, Any]:
        """Extract entities from spaCy output and the smart home parser."""
        entities: Dict[str, Any] = {
            "spacy_entities": [
                {"text": ent.text, "label": ent.label_}
                for ent in doc.ents
            ],
            "noun_chunks": [chunk.text for chunk in doc.noun_chunks],
        }
        if command.device_type:
            entities["device_type"] = command.device_type
        if command.location:
            entities["location"] = command.location
        if command.value is not None:
            entities["value"] = command.value
        return entities

    def recognize_intent(self, text: str, command: SmartHomeCommand) -> str:
        """Recognize high-level intent type."""
        normalized = text.lower().strip()
        if command.action != "unknown":
            return "smart_home_status" if command.action == "status" else "smart_home_control"
        if any(word in normalized for word in ["hello", "hi", "hey", "good morning", "good evening"]):
            return "greeting"
        if any(word in normalized for word in ["weather", "forecast", "temperature outside"]):
            return "get_weather"
        if any(word in normalized for word in ["news", "headlines", "latest stories"]):
            return "get_news"
        if any(word in normalized for word in ["calculate", "what is", "plus", "minus", "times", "divided by"]):
            if re.search(r"\d", normalized):
                return "calculate"
        if any(word in normalized for word in ["what time", "current time", "time is it"]):
            return "get_time"
        if any(word in normalized for word in ["what date", "today's date", "current date", "what day"]):
            return "get_date"
        if any(word in normalized for word in ["manage account", "check account tasks", "account tasks"]):
            return "orchestrator_accounts"
        if any(word in normalized for word in ["manage peripherals", "check peripherals", "peripheral status"]):
            return "orchestrator_peripherals"
        if any(word in normalized for word in ["manage phone", "phone tasks", "mobile tasks"]):
            return "orchestrator_phone"
        if any(word in normalized for word in ["status", "system", "health", "diagnostics"]):
            return "system_status"
        return "unknown"

    def score_intent(
        self,
        intent_type: str,
        command: SmartHomeCommand,
        entities: Dict[str, Any],
    ) -> float:
        """Assign a simple confidence score for rule-based Phase 3 intents."""
        if intent_type.startswith("smart_home"):
            score = command.confidence
            if entities.get("device_type"):
                score += 0.05
            if entities.get("location"):
                score += 0.05
            return min(score, 0.98)
        if intent_type in {
            "greeting",
            "system_status",
            "get_time",
            "get_date",
            "calculate",
            "get_weather",
            "get_news",
            "orchestrator_accounts",
            "orchestrator_peripherals",
            "orchestrator_phone",
        }:
            return 0.85
        return 0.0

    def is_confident(self, intent: Intent) -> bool:
        return intent.confidence >= self.confidence_threshold

    def _load_model(self, model_name: str) -> Any:
        try:
            return spacy.load(model_name)
        except OSError:
            self.logger.warning("spaCy model '%s' not found; falling back to blank English model", model_name)
            return spacy.blank("en")

    def _parameters_from_command(self, command: SmartHomeCommand) -> Dict[str, Any]:
        return {
            "action": command.action,
            "device_type": command.device_type,
            "location": command.location,
            "value": command.value,
        }

    def _parameters_from_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        parameters: Dict[str, Any] = {}
        if "expression" in entities:
            parameters["expression"] = entities["expression"]
        return parameters

    def _enrich_entities(self, text: str, intent_type: str, entities: Dict[str, Any]) -> None:
        normalized = text.lower()
        if intent_type == "calculate":
            entities["expression"] = text
        if intent_type == "get_weather":
            for city in ["bogota", "medellin", "cali", "new york", "london"]:
                if city in normalized:
                    entities["location"] = city
                    break

    def _skill_for_intent(self, intent_type: str) -> str:
        if intent_type.startswith("smart_home"):
            return "smart_home"
        if intent_type == "system_status":
            return "system"
        if intent_type == "greeting":
            return "greeting"
        if intent_type in {"get_time", "get_date"}:
            return "time"
        if intent_type == "calculate":
            return "calculator"
        if intent_type == "get_weather":
            return "weather"
        if intent_type == "get_news":
            return "news"
        if intent_type.startswith("orchestrator_"):
            return "orchestrator"
        return ""

    def _remember(self, intent: Intent) -> None:
        self.context.append({
            "intent_type": intent.intent_type,
            "entities": intent.entities,
            "confidence": intent.confidence,
            "text": intent.original_text,
        })
        if len(self.context) > self.max_context_history:
            self.context = self.context[-self.max_context_history:]
