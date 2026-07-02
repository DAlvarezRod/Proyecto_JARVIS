"""Text-to-speech support for JARVIS."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pyttsx3

from logger import get_logger


class TextToSpeech:
    """Speak text through the active Windows audio output."""

    def __init__(self, rate: int = 150, volume: float = 0.8, voice_name: Optional[str] = None):
        self.logger = get_logger("speech.tts")
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)
        if voice_name:
            self.set_voice(voice_name)

    def list_voices(self):
        return self.engine.getProperty("voices")

    def set_voice(self, voice_name: str) -> bool:
        needle = voice_name.lower()
        for voice in self.list_voices():
            if needle in voice.name.lower() or needle in voice.id.lower():
                self.engine.setProperty("voice", voice.id)
                return True
        return False

    def speak(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()

    def save_to_file(self, text: str, output_path: str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.engine.save_to_file(text, str(path))
        self.engine.runAndWait()
        return path
