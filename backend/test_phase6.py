"""
Phase 6 Checkpoint Test
Verify built-in skills, skill registration, and API integration behavior.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core import initialize_jarvis
from skills import CalculatorSkill, GreetingSkill, SmartHomeSkill, TimeSkill
from skills.base import Intent


async def run_phase6_tests():
    print("\n" + "=" * 70)
    print("PHASE 6 CHECKPOINT TEST - SKILLS & API INTEGRATION")
    print("=" * 70 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "config.yaml"
        devices_path = Path(temp_dir) / "devices.json"
        config_path.write_text(
            f"""
jarvis:
  name: "JARVIS"
  version: "1.0.0"
  nlu:
    confidence_threshold: 0.7
    max_context_history: 10
  api:
    timeout: 3
  storage:
    device_state_file: "{devices_path.as_posix()}"
logging:
  level: ERROR
  file: "{(Path(temp_dir) / 'jarvis.log').as_posix()}"
  max_size_mb: 10
  backup_count: 1
skills:
  enabled:
    - greeting
    - time
    - smart_home
    - calculator
    - weather
    - news
  greeting:
    enabled: true
  time:
    enabled: true
    timezone: America/Bogota
  smart_home:
    enabled: true
  calculator:
    enabled: true
  weather:
    enabled: true
  news:
    enabled: true
""",
            encoding="utf-8",
        )
        jarvis = initialize_jarvis(str(config_path))

        print("[Test 1] Registering built-in skills from config...")
        skills = jarvis.skill_registry.list_skills()
        assert set(skills) >= {"greeting", "time", "smart_home", "calculator", "weather", "news"}
        print(f"✓ Registered skills: {', '.join(sorted(skills))}")

        print("\n[Test 2] Executing calculator skill...")
        response = await jarvis.process_user_input("Calculate 12 divided by 3")
        assert "4" in response
        print("✓ Calculator skill executes safely")

        print("\n[Test 3] Executing time skill...")
        response = await jarvis.process_user_input("What time is it?")
        assert "It is" in response
        print("✓ Time skill responds")

        print("\n[Test 4] Executing smart home skill...")
        response = await jarvis.process_user_input("Turn on the kitchen light")
        assert "Kitchen Light" in response
        assert jarvis.smart_home.get_device("light_kitchen").is_on is True
        print("✓ SmartHome skill controls devices")

        print("\n[Test 5] Verifying individual skill handlers...")
        assert GreetingSkill().can_handle(Intent(intent_type="greeting"))
        assert TimeSkill().can_handle(Intent(intent_type="get_date"))
        assert CalculatorSkill().execute(Intent(intent_type="calculate", original_text="2 + 2")).success
        assert SmartHomeSkill(jarvis.smart_home).can_handle(Intent(intent_type="smart_home_status"))
        print("✓ Built-in skill contracts are valid")

        print("\n[Test 6] API-backed skills fail gracefully or return data...")
        weather_response = await jarvis.process_user_input("What is the weather in Bogota?")
        news_response = await jarvis.process_user_input("Tell me the latest news")
        assert weather_response
        assert news_response
        print("✓ Weather and News skills return useful responses or graceful errors")

    print("\n" + "=" * 70)
    print("PHASE 6 CHECKPOINT - ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nReady for Phase 7: Integration & Advanced Features")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_phase6_tests())
