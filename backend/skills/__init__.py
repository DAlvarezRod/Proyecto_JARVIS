"""Built-in JARVIS skills."""

from .calculator import CalculatorSkill
from .greeting import GreetingSkill
from .news import NewsSkill
from .orchestrator import PersonalAssistantOrchestratorSkill
from .smart_home_skill import SmartHomeSkill
from .time_skill import TimeSkill
from .weather import WeatherSkill

__all__ = [
    "CalculatorSkill",
    "GreetingSkill",
    "NewsSkill",
    "PersonalAssistantOrchestratorSkill",
    "SmartHomeSkill",
    "TimeSkill",
    "WeatherSkill",
]
