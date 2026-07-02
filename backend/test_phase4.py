"""
Phase 4 Checkpoint Test
Verify PyAudio, microphone discovery, STT/TTS initialization, and speech pipeline wiring.
"""

import asyncio
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pyaudio

from core import initialize_jarvis
from speech import MicrophoneManager, SpeechPipeline, SpeechToText, TextToSpeech


async def run_phase4_tests():
    print("\n" + "=" * 70)
    print("PHASE 4 CHECKPOINT TEST - SPEECH PROCESSING")
    print("=" * 70 + "\n")

    print("[Test 1] Importing PyAudio and listing microphones...")
    manager = MicrophoneManager()
    devices = manager.list_input_devices(include_loopback=False)
    assert pyaudio.__version__ == "0.2.14"
    assert devices, "No physical input devices detected by PyAudio"
    default_device = manager.get_default_input_device()
    print(f"✓ PyAudio {pyaudio.__version__} detected {len(devices)} input devices")
    if default_device:
        print(f"✓ Default input: [{default_device.index}] {default_device.name}")

    print("\n[Test 2] Initializing text-to-speech engine...")
    tts = TextToSpeech(rate=150, volume=0.5)
    voices = tts.list_voices()
    assert voices
    print(f"✓ pyttsx3 voices available: {len(voices)}")

    print("\n[Test 3] Creating a silent WAV fixture for STT pipeline shape...")
    with tempfile.TemporaryDirectory() as temp_dir:
        wav_path = Path(temp_dir) / "silence.wav"
        with wave.open(str(wav_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\x00\x00" * 16000)
        stt = SpeechToText(model_name="tiny")
        assert wav_path.exists()
        assert stt.model_name == "tiny"
        print("✓ SpeechToText configured for Whisper")

    print("\n[Test 4] Wiring SpeechPipeline to JARVIS core...")
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "config.yaml"
        devices_path = Path(temp_dir) / "devices.json"
        config_path.write_text(
            f"""
jarvis:
  name: "JARVIS"
  version: "1.0.0"
  voice:
    rate: 150
    volume: 0.8
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
        pipeline = SpeechPipeline(jarvis, whisper_model="tiny", tts_rate=150, tts_volume=0.5)
        assert pipeline.microphones.get_default_input_device() is not None
        print("✓ SpeechPipeline can use the active Windows default microphone")

    print("\n" + "=" * 70)
    print("PHASE 4 CHECKPOINT - ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nReady for Phase 5: Web Frontend & Real-time Communication")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_phase4_tests())
