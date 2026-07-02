"""
JARVIS Core Engine
Main coordinator for all JARVIS subsystems
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime
from time import perf_counter
import yaml
import os
from dotenv import load_dotenv

from automation import AutomationManager
from custom_skill_loader import CustomSkillLoader
from logger import get_logger
from memory import ConversationMemory
from nlu import NLUEngine
from skills import (
    CalculatorSkill,
    GreetingSkill,
    NewsSkill,
    PersonalAssistantOrchestratorSkill,
    SmartHomeSkill,
    TimeSkill,
    WeatherSkill,
)
from skills.base import SkillRegistry, Skill, Intent, SkillResponse
from smart_home import create_default_hub

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class MessageBus:
    """
    Event-driven message bus for async communication between components
    Allows loose coupling between different subsystems
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = get_logger('message_bus')
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of event to listen for (e.g., "device_state_changed")
            handler: Async function to call when event occurs
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        self.logger.debug(f"Subscribed to '{event_type}': {handler.__name__}")
    
    async def publish(self, event_type: str, data: Dict[str, Any] = None) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event_type: Type of event
            data: Event data
        """
        data = data or {}
        self.logger.debug(f"Publishing event: {event_type} with data: {data}")
        
        if event_type in self.subscribers:
            tasks = [handler(data) for handler in self.subscribers[event_type]]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def __repr__(self):
        total_subs = sum(len(handlers) for handlers in self.subscribers.values())
        return f"MessageBus({total_subs} total subscriptions)"


class Configuration:
    """Load and manage JARVIS configuration"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to config.yaml
        """
        self.path = Path(config_path)
        self.config = {}
        self.load()
        logger.info(f"Configuration loaded from {config_path}")
    
    def load(self) -> None:
        """Load configuration from YAML file"""
        try:
            with open(self.path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.path}. Using defaults.")
            self.config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a config value by dot-notation path
        e.g., get("jarvis.voice.rate") -> config['jarvis']['voice']['rate']
        
        Args:
            key: Dot-separated path to config value
            default: Default value if key not found
            
        Returns:
            Config value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def __repr__(self):
        return f"Configuration(loaded={bool(self.config)})"


class JARVIS:
    """
    Main JARVIS core engine
    Coordinates all subsystems: skills, speech, NLU, device control
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize JARVIS core
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.logger = get_logger('core')
        self.config = Configuration(config_path)
        self.skill_registry = SkillRegistry()
        self.message_bus = MessageBus()
        self.smart_home = create_default_hub(
            state_file=self.config.get('jarvis.storage.device_state_file', 'data/devices.json'),
            load_existing=True,
        )
        self.nlu = NLUEngine(
            confidence_threshold=self.config.get('jarvis.nlu.confidence_threshold', 0.7),
            max_context_history=self.config.get('jarvis.nlu.max_context_history', 10),
        )
        self.memory = ConversationMemory(
            self.config.get('jarvis.storage.conversation_db', 'data/conversations.db')
        )
        self.automation = AutomationManager(
            rules_file=self.config.get('jarvis.storage.automation_rules_file', 'data/automations.json'),
            action_executor=self._execute_automation_action,
            poll_interval=self.config.get('jarvis.automation.poll_interval', 1.0),
        )
        self.custom_skill_loader = CustomSkillLoader(
            self.config.get('jarvis.storage.custom_skills_dir', '../custom_skills')
        )
        self.conversation_history: List[Dict[str, Any]] = self.memory.get_recent(
            self.config.get('jarvis.nlu.max_context_history', 10)
        )
        self.response_metrics: List[float] = []
        self.start_time = datetime.now()
        
        # Configuration values
        self.name = self.config.get('jarvis.name', 'JARVIS')
        self.version = self.config.get('jarvis.version', '1.0.0')
        
        # Create data directories
        self._setup_data_directories()
        self._register_builtin_skills()
        self.reload_custom_skills()
        if self.config.get('jarvis.automation.background_enabled', False):
            self.automation.start()
        
        self.logger.info(f"{self.name} v{self.version} initialized")
        self.logger.info(f"Configuration: {self.config}")
        self.logger.info(f"Skill Registry: {self.skill_registry}")

    def _register_builtin_skills(self) -> None:
        """Register built-in skills enabled in config.yaml."""
        enabled = set(self.config.get("skills.enabled", []))
        api_timeout = self.config.get("jarvis.api.timeout", 5)
        skill_factories = {
            "greeting": GreetingSkill,
            "time": lambda: TimeSkill(self.config.get("skills.time.timezone", "America/Bogota")),
            "smart_home": lambda: SmartHomeSkill(self.smart_home, on_command=self._handle_smart_home_result),
            "calculator": CalculatorSkill,
            "weather": lambda: WeatherSkill(timeout=api_timeout),
            "news": lambda: NewsSkill(timeout=api_timeout),
            "orchestrator": lambda: PersonalAssistantOrchestratorSkill(
                enabled=(
                    self.config.get("jarvis.orchestrator.enabled", True)
                    and self.config.get("skills.orchestrator.enabled", True)
                ),
                require_explicit_approval=self.config.get(
                    "jarvis.orchestrator.safety.require_explicit_approval",
                    True,
                ),
                privileged_keywords=self.config.get(
                    "jarvis.orchestrator.safety.privileged_keywords",
                    [],
                ),
                disclose_limitations=self.config.get(
                    "jarvis.orchestrator.safety.disclose_limitations",
                    True,
                ),
            ),
        }
        for name, factory in skill_factories.items():
            if name in enabled and self.config.get(f"skills.{name}.enabled", True):
                self.register_skill(factory())

    def reload_custom_skills(self) -> List[str]:
        """Reload manifest-based custom skills from disk."""
        for name, skill in list(self.skill_registry.skills.items()):
            if getattr(skill, "source", None):
                self.skill_registry.unregister(name)
        loaded = []
        for skill in self.custom_skill_loader.load_skills():
            self.register_skill(skill)
            loaded.append(skill.name)
        return loaded
    
    def _setup_data_directories(self) -> None:
        """Create necessary data directories"""
        directories = [
            Path("logs"),
            Path("data"),
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True, parents=True)
            self.logger.debug(f"Ensured directory exists: {directory}")
    
    def register_skill(self, skill: Skill) -> None:
        """
        Register a skill with JARVIS
        
        Args:
            skill: Skill instance to register
        """
        self.skill_registry.register(skill)
        self.logger.info(f"Registered skill: {skill.name}")
    
    def register_skills(self, skills: List[Skill]) -> None:
        """Register multiple skills"""
        for skill in skills:
            self.register_skill(skill)
    
    async def process_user_input(self, user_input: str) -> str:
        """
        Process user input through the full pipeline
        
        Args:
            user_input: Raw user input text
            
        Returns:
            JARVIS response text
        """
        self.logger.info(f"Processing input: '{user_input}'")
        started = perf_counter()
        
        # Log to conversation history
        self.add_to_history("user", user_input)

        intent = self.nlu.parse(user_input)
        response_text = self._handle_intent(intent)
        latency_ms = round((perf_counter() - started) * 1000, 2)
        self.response_metrics.append(latency_ms)
        if len(self.response_metrics) > 100:
            self.response_metrics = self.response_metrics[-100:]

        self.add_to_history(
            "assistant",
            response_text,
            intent_type=intent.intent_type,
            confidence=intent.confidence,
            latency_ms=latency_ms,
        )
        
        await self.message_bus.publish("user_input_processed", {
            "input": user_input,
            "intent": intent.intent_type,
            "confidence": intent.confidence,
            "response": response_text,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        })
        
        return response_text

    def _handle_intent(self, intent: Intent) -> str:
        """Route recognized intents to core systems or registered skills."""
        matching_skills = self.skill_registry.find_skills_for_intent(intent)
        if matching_skills:
            response = matching_skills[0].execute(intent)
            return response.text

        if not self.nlu.is_confident(intent):
            return f"I heard: '{intent.original_text}', but I am not confident enough to act on it yet."

        if intent.intent_type == "smart_home_status":
            status = self.smart_home.get_status(
                device_type=intent.parameters.get("device_type"),
                location=intent.parameters.get("location"),
            )
            if not status["summary"]:
                return "I could not find any matching smart home devices."
            return " ".join(status["summary"])

        if intent.intent_type == "smart_home_control":
            result = self.execute_smart_home_command(
                action=intent.parameters.get("action"),
                device_type=intent.parameters.get("device_type"),
                location=intent.parameters.get("location"),
                value=intent.parameters.get("value"),
            )
            return result["message"]

        if intent.intent_type == "system_status":
            status = self.get_status()
            return (
                f"{self.name} is {status['status']} with "
                f"{status['skills_registered']} skills and "
                f"{status['smart_home_devices']} smart home devices."
            )

        if intent.intent_type == "greeting":
            return f"Hello. {self.name} is online."

        return f"I heard: '{intent.original_text}', but I do not know how to handle that yet."

    def execute_smart_home_command(self, **kwargs) -> Dict[str, Any]:
        """Execute a smart home command and evaluate automation rules."""
        result = self.smart_home.execute_command(**kwargs)
        self._handle_smart_home_result(result)
        return result

    def _handle_smart_home_result(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not result.get("success"):
            return []
        devices = result.get("devices", [])
        if not devices:
            return []
        return self.automation.evaluate_device_event(devices)

    def _execute_automation_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        if action.get("type", "smart_home") != "smart_home":
            return {"success": False, "message": f"Unsupported automation action: {action.get('type')}"}
        return self.smart_home.execute_command(
            action=str(action.get("action")),
            device_id=action.get("device_id"),
            device_type=action.get("device_type"),
            location=action.get("location"),
            value=action.get("value"),
        )
    
    def add_to_history(
        self,
        speaker: str,
        text: str,
        intent_type: Optional[str] = None,
        confidence: Optional[float] = None,
        latency_ms: Optional[float] = None,
    ) -> None:
        """
        Add message to conversation history
        
        Args:
            speaker: "user" or "assistant"
            text: Message text
        """
        timestamp = datetime.now().isoformat()
        message = {
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp,
        }
        if intent_type is not None:
            message["intent_type"] = intent_type
        if confidence is not None:
            message["confidence"] = confidence
        if latency_ms is not None:
            message["latency_ms"] = latency_ms

        self.conversation_history.append(message)
        max_history = self.config.get('jarvis.nlu.max_context_history', 10) * 2
        if len(self.conversation_history) > max_history:
            self.conversation_history = self.conversation_history[-max_history:]

        self.memory.add_message(
            speaker=speaker,
            text=text,
            timestamp=timestamp,
            intent_type=intent_type,
            confidence=confidence,
            latency_ms=latency_ms,
        )
    
    def get_conversation_history(self, limit: int = None) -> List[Dict[str, str]]:
        """Get conversation history"""
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
        self.response_metrics = []
        self.memory.clear()
        self.logger.info("Conversation history cleared")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return lightweight runtime performance metrics."""
        if not self.response_metrics:
            return {
                "requests_processed": 0,
                "last_response_ms": None,
                "average_response_ms": None,
            }
        return {
            "requests_processed": len(self.response_metrics),
            "last_response_ms": self.response_metrics[-1],
            "average_response_ms": round(
                sum(self.response_metrics) / len(self.response_metrics),
                2,
            ),
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current JARVIS status
        
        Returns:
            Dict with status information
        """
        uptime = datetime.now() - self.start_time
        
        return {
            'name': self.name,
            'version': self.version,
            'status': 'running',
            'uptime_seconds': int(uptime.total_seconds()),
            'skills_registered': len(self.skill_registry.skills),
            'custom_skills': len([
                skill for skill in self.skill_registry.skills.values()
                if getattr(skill, "source", None)
            ]),
            'smart_home_devices': len(self.smart_home.devices),
            'nlu_model': self.nlu.model_name,
            'conversation_messages': len(self.conversation_history),
            'memory_messages': self.memory.count(),
            'performance': self.get_performance_metrics(),
            'wake_word': self.config.get('jarvis.wake_word', 'jarvis'),
            'voice_activation': {
                'enabled': self.config.get('jarvis.voice.wake_detection.enabled', False),
                'wake_words': self.config.get('jarvis.voice.wake_detection.wake_words', []),
            },
            'automation': self.automation.get_status(),
            'start_time': self.start_time.isoformat(),
        }
    
    def __repr__(self):
        return f"{self.name}(v{self.version}, {len(self.skill_registry.skills)} skills)"


# Global JARVIS instance (can be imported by other modules)
_jarvis_instance: Optional[JARVIS] = None


def get_jarvis() -> JARVIS:
    """Get or create the global JARVIS instance"""
    global _jarvis_instance
    if _jarvis_instance is None:
        _jarvis_instance = JARVIS()
    return _jarvis_instance


def initialize_jarvis(config_path: str = "config.yaml") -> JARVIS:
    """
    Initialize JARVIS with custom config path
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        JARVIS instance
    """
    global _jarvis_instance
    _jarvis_instance = JARVIS(config_path)
    return _jarvis_instance
