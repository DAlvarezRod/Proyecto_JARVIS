"""
Phase 3 Checkpoint Test
Verify NLP intent recognition, entity extraction, context, and core routing.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core import initialize_jarvis
from nlu import NLUEngine


async def run_phase3_tests():
    print("\n" + "=" * 70)
    print("PHASE 3 CHECKPOINT TEST - NLP ENGINE")
    print("=" * 70 + "\n")

    print("[Test 1] Loading NLP engine...")
    nlu = NLUEngine()
    assert nlu.nlp is not None
    print(f"✓ Loaded spaCy model: {nlu.model_name}")

    print("\n[Test 2] Recognizing smart home control intent...")
    intent = nlu.parse("Turn on the kitchen light")
    assert intent.intent_type == "smart_home_control"
    assert intent.entities["device_type"] == "light"
    assert intent.entities["location"] == "kitchen"
    assert intent.confidence >= 0.7
    print(f"✓ Intent recognized: {intent}")

    print("\n[Test 3] Extracting numeric entity...")
    intent = nlu.parse("Set the thermostat to 23 degrees")
    assert intent.intent_type == "smart_home_control"
    assert intent.entities["device_type"] == "thermostat"
    assert intent.entities["value"] == 23
    print("✓ Temperature value extracted")

    print("\n[Test 4] Recognizing status intent...")
    intent = nlu.parse("What is the status of the front door?")
    assert intent.intent_type == "smart_home_status"
    assert intent.entities["device_type"] == "door"
    print("✓ Smart home status intent recognized")

    print("\n[Test 5] Tracking NLP context...")
    assert len(nlu.context) >= 3
    assert nlu.context[-1]["intent_type"] == "smart_home_status"
    print(f"✓ Context entries retained: {len(nlu.context)}")

    print("\n[Test 6] Routing NLP through JARVIS core...")
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
  storage:
    device_state_file: "{devices_path.as_posix()}"
logging:
  level: ERROR
  file: "{(Path(temp_dir) / 'jarvis.log').as_posix()}"
  max_size_mb: 10
  backup_count: 1
""",
            encoding="utf-8",
        )
        jarvis = initialize_jarvis(str(config_path))
        response = await jarvis.process_user_input("Turn on the kitchen light")
        assert "Kitchen Light" in response
        assert jarvis.smart_home.get_device("light_kitchen").is_on is True
        response = await jarvis.process_user_input("What is the status of the kitchen light?")
        assert "Kitchen Light" in response
        assert "on" in response
        print("✓ JARVIS routes recognized smart home intents to the hub")

    print("\n" + "=" * 70)
    print("PHASE 3 CHECKPOINT - ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nReady for Phase 4: Speech Processing")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_phase3_tests())
