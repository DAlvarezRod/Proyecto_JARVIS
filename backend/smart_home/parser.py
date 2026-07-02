"""Simple command parser for Phase 2 smart home simulation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SmartHomeCommand:
    """Parsed smart home command."""

    action: str
    device_type: Optional[str] = None
    location: Optional[str] = None
    value: Any = None
    confidence: float = 0.0
    raw_text: str = ""


class CommandParser:
    """Rule-based parser that maps user text to smart home commands."""

    DEVICE_KEYWORDS = {
        "light": ["light", "lights", "lamp", "lamps"],
        "thermostat": ["thermostat", "temperature", "heat", "cooling", "ac"],
        "door": ["door", "doors"],
        "security": ["security", "alarm"],
        "camera": ["camera", "cameras"],
    }
    LOCATIONS = ["living room", "kitchen", "bedroom", "hallway", "entry", "front", "home"]

    def parse(self, text: str) -> SmartHomeCommand:
        normalized = text.lower().strip()
        device_type = self._detect_device_type(normalized)
        location = self._detect_location(normalized)

        temperature = self._extract_temperature(normalized)
        if temperature is not None:
            return SmartHomeCommand(
                action="set_temperature",
                device_type="thermostat",
                location=location,
                value=temperature,
                confidence=0.9,
                raw_text=text,
            )

        brightness = self._extract_brightness(normalized)
        if brightness is not None:
            return SmartHomeCommand(
                action="set_brightness",
                device_type="light",
                location=location,
                value=brightness,
                confidence=0.9,
                raw_text=text,
            )

        status_requested = (
            any(word in normalized for word in ["status", "state"])
            or (
                any(word in normalized for word in ["how is", "how are"])
                and (device_type is not None or location is not None)
            )
        )
        if status_requested:
            return SmartHomeCommand("status", device_type, location, confidence=0.8, raw_text=text)
        if any(word in normalized for word in ["turn on", "switch on", "enable"]):
            return SmartHomeCommand("turn_on", device_type, location, confidence=0.85, raw_text=text)
        if any(word in normalized for word in ["turn off", "switch off", "disable"]):
            return SmartHomeCommand("turn_off", device_type, location, confidence=0.85, raw_text=text)
        if "toggle" in normalized:
            return SmartHomeCommand("toggle", device_type, location, confidence=0.8, raw_text=text)
        if "unlock" in normalized:
            return SmartHomeCommand("unlock", "door", location, confidence=0.9, raw_text=text)
        if "lock" in normalized:
            return SmartHomeCommand("lock", "door", location, confidence=0.9, raw_text=text)
        if "open" in normalized:
            return SmartHomeCommand("open", "door", location, confidence=0.85, raw_text=text)
        if "close" in normalized:
            return SmartHomeCommand("close", "door", location, confidence=0.85, raw_text=text)
        if "disarm" in normalized:
            return SmartHomeCommand("disarm", "security", location, confidence=0.9, raw_text=text)
        if "arm" in normalized:
            mode = "night" if "night" in normalized else "home" if "home" in normalized else "away"
            return SmartHomeCommand("arm", "security", location, mode, confidence=0.9, raw_text=text)
        if "record" in normalized and any(word in normalized for word in ["start", "begin"]):
            return SmartHomeCommand("start_recording", "camera", location, confidence=0.85, raw_text=text)
        if "record" in normalized and any(word in normalized for word in ["stop", "end"]):
            return SmartHomeCommand("stop_recording", "camera", location, confidence=0.85, raw_text=text)

        return SmartHomeCommand("unknown", device_type, location, confidence=0.0, raw_text=text)

    def _detect_device_type(self, text: str) -> Optional[str]:
        for device_type, keywords in self.DEVICE_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return device_type
        return None

    def _detect_location(self, text: str) -> Optional[str]:
        for location in self.LOCATIONS:
            if location in text:
                return "entry" if location == "front" else location
        return None

    def _extract_temperature(self, text: str) -> Optional[float]:
        if not any(word in text for word in ["temperature", "thermostat", "degrees", "celsius"]):
            return None
        match = re.search(r"(\d+(?:\.\d+)?)", text)
        return float(match.group(1)) if match else None

    def _extract_brightness(self, text: str) -> Optional[int]:
        if not any(word in text for word in ["brightness", "dim", "percent", "%"]):
            return None
        match = re.search(r"(\d{1,3})\s*%?", text)
        if not match:
            return None
        return max(0, min(100, int(match.group(1))))
