"""
Base Skill class for JARVIS
All skills inherit from this to implement the skill interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

from logger import get_logger

logger = get_logger(__name__)


class SkillResponse:
    """Response object returned by skill execution"""
    
    def __init__(self, text: str, success: bool = True, 
                 data: Optional[Dict[str, Any]] = None, 
                 confidence: float = 1.0):
        """
        Args:
            text: Response text to be spoken/displayed
            success: Whether skill execution succeeded
            data: Optional dict with additional data
            confidence: Confidence score (0-1)
        """
        self.text = text
        self.success = success
        self.data = data or {}
        self.confidence = confidence
        
    def __repr__(self):
        return f"SkillResponse(text='{self.text}', success={self.success}, confidence={self.confidence})"


@dataclass
class Intent:
    """Represents a parsed user intent"""
    
    intent_type: str  # e.g., "control_light", "get_weather"
    entities: Dict[str, Any] = field(default_factory=dict)  # Extracted entities
    original_text: str = ""  # User's original input
    confidence: float = 0.0  # Confidence score (0-1)
    skill_name: str = ""  # Which skill will handle this
    parameters: Dict[str, Any] = field(default_factory=dict)  # Additional params
    context_data: Dict[str, Any] = field(default_factory=dict)  # Conversation context
    
    def __repr__(self):
        return f"Intent(type='{self.intent_type}', conf={self.confidence}, skill='{self.skill_name}')"


class Skill(ABC):
    """
    Abstract base class for all JARVIS skills.
    
    Subclasses must implement:
    - can_handle(intent: Intent) -> bool
    - execute(intent: Intent) -> SkillResponse
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a skill
        
        Args:
            name: Unique skill name (e.g., "weather", "lights")
            description: Human-readable description
        """
        self.name = name
        self.description = description
        self.logger = get_logger(f'skill.{name}')
        self.enabled = True
        self.keywords = []  # Keywords that trigger this skill
        self.example_intents = []  # Example utterances
        
        self.logger.debug(f"Skill '{name}' initialized")
    
    @abstractmethod
    def can_handle(self, intent: Intent) -> bool:
        """
        Check if this skill can handle the given intent
        
        Args:
            intent: The Intent to check
            
        Returns:
            bool: True if this skill can handle this intent
        """
        pass
    
    @abstractmethod
    def execute(self, intent: Intent) -> SkillResponse:
        """
        Execute the skill with the given intent
        
        Args:
            intent: The Intent to execute
            
        Returns:
            SkillResponse: Response from skill execution
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this skill for the registry
        
        Returns:
            Dict with skill information
        """
        return {
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'keywords': self.keywords,
            'example_intents': self.example_intents,
        }
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"


class SkillRegistry:
    """Registry for managing and discovering skills"""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.logger = get_logger('skill_registry')
    
    def register(self, skill: Skill) -> None:
        """
        Register a skill
        
        Args:
            skill: Skill instance to register
        """
        if skill.name in self.skills:
            self.logger.warning(f"Overwriting existing skill: {skill.name}")
        
        self.skills[skill.name] = skill
        self.logger.debug(f"Registered skill: {skill.name}")
    
    def unregister(self, skill_name: str) -> None:
        """Unregister a skill by name"""
        if skill_name in self.skills:
            del self.skills[skill_name]
            self.logger.debug(f"Unregistered skill: {skill_name}")
        else:
            self.logger.warning(f"Skill not found: {skill_name}")
    
    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill by name"""
        return self.skills.get(skill_name)
    
    def find_skills_for_intent(self, intent: Intent) -> List[Skill]:
        """
        Find all skills that can handle an intent
        
        Args:
            intent: The Intent to find handlers for
            
        Returns:
            List of matching skills
        """
        matching = []
        for skill in self.skills.values():
            if skill.enabled and skill.can_handle(intent):
                matching.append(skill)
        
        return sorted(matching, key=lambda s: intent.confidence, reverse=True)
    
    def list_skills(self) -> Dict[str, Dict[str, Any]]:
        """Get metadata for all registered skills"""
        return {name: skill.get_metadata() for name, skill in self.skills.items()}
    
    def __repr__(self):
        return f"SkillRegistry({len(self.skills)} skills registered)"
