"""Weather skill using the public Open-Meteo API."""

from __future__ import annotations

from typing import Any, Dict

import requests

from skills.base import Intent, Skill, SkillResponse


class WeatherSkill(Skill):
    CITY_COORDS = {
        "bogota": (4.711, -74.0721),
        "medellin": (6.2442, -75.5812),
        "cali": (3.4516, -76.532),
        "new york": (40.7128, -74.006),
        "london": (51.5072, -0.1276),
    }

    def __init__(self, timeout: int = 5):
        super().__init__("weather", "Current weather from Open-Meteo")
        self.timeout = timeout
        self.keywords = ["weather", "temperature", "forecast"]
        self.example_intents = ["What's the weather in Bogota?", "Temperature in London"]

    def can_handle(self, intent: Intent) -> bool:
        return intent.intent_type == "get_weather"

    def execute(self, intent: Intent) -> SkillResponse:
        location = str(intent.entities.get("location") or "bogota").lower()
        lat, lon = self.CITY_COORDS.get(location, self.CITY_COORDS["bogota"])
        try:
            data = self._fetch_weather(lat, lon)
        except Exception as exc:
            return SkillResponse(f"I could not fetch weather right now: {exc}", success=False)

        current = data["current"]
        city = location.title()
        text = (
            f"Current weather in {city}: {current['temperature_2m']}C, "
            f"wind {current['wind_speed_10m']} km/h."
        )
        return SkillResponse(text, data={"location": location, "weather": current})

    def _fetch_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,wind_speed_10m",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
