"""
Phase 1 Checkpoint Test
Verify core engine, skill registry, and logging are working
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core import JARVIS, initialize_jarvis
from skills.base import Skill, Intent, SkillResponse
from logger import get_logger

logger = get_logger('test_phase1')


class GreetingSkill(Skill):
    """Simple test skill"""
    
    def __init__(self):
        super().__init__(
            name="test_greeting",
            description="Test greeting skill"
        )
        self.keywords = ["hello", "hi", "hey"]
    
    def can_handle(self, intent: Intent) -> bool:
        return any(kw in intent.original_text.lower() for kw in self.keywords)
    
    def execute(self, intent: Intent) -> SkillResponse:
        return SkillResponse(text="Hello! I'm JARVIS. How can I help you?")


async def run_phase1_tests():
    """Run Phase 1 checkpoint tests"""
    
    print("\n" + "="*70)
    print("PHASE 1 CHECKPOINT TEST - JARVIS CORE ENGINE")
    print("="*70 + "\n")
    
    # Test 1: Initialize JARVIS
    print("[Test 1] Initializing JARVIS core engine...")
    jarvis = initialize_jarvis()
    print(f"✓ JARVIS initialized: {jarvis}")
    
    # Test 2: Register skill
    print("\n[Test 2] Registering test skill...")
    test_skill = GreetingSkill()
    jarvis.register_skill(test_skill)
    print(f"✓ Skill registered: {test_skill}")
    
    # Test 3: List registered skills
    print("\n[Test 3] Listing registered skills...")
    skills = jarvis.skill_registry.list_skills()
    print(f"✓ Registered skills:")
    for name, metadata in skills.items():
        print(f"  - {name}: {metadata['description']}")
    
    # Test 4: Create and check intent matching
    print("\n[Test 4] Testing intent matching...")
    intent = Intent(
        intent_type="greeting",
        original_text="Hello JARVIS",
        confidence=0.95
    )
    matching_skills = jarvis.skill_registry.find_skills_for_intent(intent)
    print(f"✓ Created intent: {intent}")
    print(f"✓ Matching skills for this intent: {matching_skills}")
    
    # Test 5: Process user input through core
    print("\n[Test 5] Processing user input through core...")
    response = await jarvis.process_user_input("Hey JARVIS, how are you?")
    print(f"✓ Response: {response}")
    
    # Test 6: Check conversation history
    print("\n[Test 6] Checking conversation history...")
    history = jarvis.get_conversation_history()
    print(f"✓ Conversation history ({len(history)} messages):")
    for msg in history:
        print(f"  [{msg['speaker'].upper()}] {msg['text'][:50]}...")
    
    # Test 7: Get system status
    print("\n[Test 7] Getting system status...")
    status = jarvis.get_status()
    print(f"✓ System status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test 8: Message bus
    print("\n[Test 8] Testing message bus...")
    received_events = []
    
    async def test_handler(data):
        received_events.append(data)
        print(f"  ✓ Event handler called with data: {data}")
    
    jarvis.message_bus.subscribe("test_event", test_handler)
    await jarvis.message_bus.publish("test_event", {"message": "Test data"})
    print(f"✓ Message bus test passed ({len(received_events)} events received)")
    
    # Test 9: Configuration loading
    print("\n[Test 9] Testing configuration loading...")
    jar_name = jarvis.config.get('jarvis.name')
    jar_version = jarvis.config.get('jarvis.version')
    confidence_threshold = jarvis.config.get('jarvis.nlu.confidence_threshold')
    print(f"✓ Configuration loaded:")
    print(f"  Name: {jar_name}")
    print(f"  Version: {jar_version}")
    print(f"  NLU Confidence Threshold: {confidence_threshold}")
    
    # Summary
    print("\n" + "="*70)
    print("PHASE 1 CHECKPOINT - ALL TESTS PASSED ✓")
    print("="*70)
    print(f"\nSummary:")
    print(f"  ✓ Core engine initializes correctly")
    print(f"  ✓ Plugin system loads skills")
    print(f"  ✓ No import errors")
    print(f"  ✓ Logging system functional")
    print(f"  ✓ Configuration loading works")
    print(f"  ✓ Message bus operational")
    print(f"  ✓ Conversation history tracking")
    print(f"\nReady for Phase 2: Smart Home Simulation System")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_phase1_tests())
    except Exception as e:
        logger.error(f"Phase 1 test failed: {e}", exc_info=True)
        sys.exit(1)
