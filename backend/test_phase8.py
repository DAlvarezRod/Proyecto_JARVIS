"""
Phase 8 Checkpoint Test
Verify wake word detection and continuous voice activation flow.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core import initialize_jarvis
from speech import SpeechPipeline, WakeWordDetector, WakeWordListener


async def run_phase8_tests():
    print("\n" + "=" * 70)
    print("PHASE 8 CHECKPOINT TEST - WAKE WORD & VOICE ACTIVATION")
    print("=" * 70 + "\n")

    print("[Test 1] Detecting wake word in transcripts...")
    detector = WakeWordDetector(["jarvis", "hey jarvis"])
    match = detector.detect("Jarvis, calculate 8 times 7")
    assert match.activated is True
    assert match.wake_word == "jarvis"
    assert match.command == "calculate 8 times 7"
    assert detector.detect("calculate 8 times 7").activated is False
    print("✓ WakeWordDetector extracts activation and command text")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_path = temp_path / "config.yaml"
        devices_path = temp_path / "devices.json"
        memory_path = temp_path / "conversations.db"
        config_path.write_text(
            f"""
jarvis:
  name: "JARVIS"
  version: "1.0.0"
  wake_word: "jarvis"
  voice:
    rate: 150
    volume: 0.8
    wake_detection:
      enabled: true
      wake_words:
        - jarvis
      listen_timeout: 1
      phrase_time_limit: 2
      poll_delay: 0
  nlu:
    confidence_threshold: 0.7
    max_context_history: 10
  storage:
    conversation_db: "{memory_path.as_posix()}"
    device_state_file: "{devices_path.as_posix()}"
logging:
  level: ERROR
  file: "{(temp_path / 'jarvis.log').as_posix()}"
  max_size_mb: 10
  backup_count: 1
skills:
  enabled:
    - greeting
    - time
    - smart_home
    - calculator
  greeting:
    enabled: true
  time:
    enabled: true
    timezone: America/Bogota
  smart_home:
    enabled: true
  calculator:
    enabled: true
""",
            encoding="utf-8",
        )
        jarvis = initialize_jarvis(str(config_path))
        pipeline = SpeechPipeline(jarvis, whisper_model="tiny", tts_rate=150, tts_volume=0.5)
        listener = WakeWordListener(pipeline, wake_words=["jarvis"], poll_delay=0)

        transcripts = iter([
            "random room noise",
            "Jarvis calculate 8 times 7",
            "Jarvis turn on the kitchen light",
        ])

        print("\n[Test 2] Running wake loop with simulated transcripts...")
        stats = await listener.run(
            speak_response=False,
            max_cycles=3,
            transcript_provider=lambda: next(transcripts),
        )
        assert stats["active"] is False
        assert stats["cycles"] == 3
        assert stats["ignored_transcripts"] == 1
        assert stats["activations"] == 2
        assert "Kitchen Light" in stats["last_response"]
        print("✓ Wake loop ignores non-wake audio and processes activated commands")

        print("\n[Test 3] Verifying wake-triggered commands update systems...")
        assert jarvis.smart_home.get_device("light_kitchen").is_on is True
        history = jarvis.get_conversation_history()
        assert any("calculate 8 times 7" in message["text"] for message in history)
        assert jarvis.memory.count() >= 4
        print("✓ Wake activation routes through JARVIS, skills, smart home, and memory")

        print("\n[Test 4] Handling empty wake command...")
        transcripts = iter(["Jarvis"])
        stats = await listener.run(
            speak_response=False,
            max_cycles=1,
            transcript_provider=lambda: next(transcripts),
        )
        assert stats["last_command"] == "health diagnostics"
        assert "JARVIS is running" in stats["last_response"]
        print("✓ Empty wake activation falls back to system status")

    print("\n" + "=" * 70)
    print("PHASE 8 CHECKPOINT - ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nReady for Phase 9: Automation Rules & Background Tasks")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_phase8_tests())
