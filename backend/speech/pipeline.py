"""Speech I/O pipeline that connects microphone, STT, JARVIS, and TTS."""

from __future__ import annotations

from typing import Optional

from core import JARVIS
from logger import get_logger
from speech.audio_io import MicrophoneManager
from speech.stt import SpeechToText
from speech.tts import TextToSpeech


class SpeechPipeline:
    """High-level voice pipeline for one-shot voice interactions."""

    def __init__(
        self,
        jarvis: JARVIS,
        whisper_model: str = "base",
        tts_rate: int = 150,
        tts_volume: float = 0.8,
    ):
        self.logger = get_logger("speech.pipeline")
        self.jarvis = jarvis
        self.microphones = MicrophoneManager()
        self.stt = SpeechToText(model_name=whisper_model)
        self.tts = TextToSpeech(rate=tts_rate, volume=tts_volume)

    async def listen_process_respond(
        self,
        device_index: Optional[int] = None,
        preferred_device_name: Optional[str] = None,
        speak_response: bool = True,
        timeout: Optional[float] = 5,
        phrase_time_limit: Optional[float] = 8,
    ) -> str:
        """Record from the selected/default microphone, process text, and optionally speak."""
        text = self.listen_and_transcribe(
            device_index=device_index,
            preferred_device_name=preferred_device_name,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
        )
        return await self.process_text(text, speak_response=speak_response)

    def listen_and_transcribe(
        self,
        device_index: Optional[int] = None,
        preferred_device_name: Optional[str] = None,
        timeout: Optional[float] = 5,
        phrase_time_limit: Optional[float] = 8,
    ) -> str:
        """Capture microphone audio and return transcribed text."""
        if preferred_device_name:
            device = self.microphones.find_input_device(preferred_device_name)
            if device:
                device_index = device.index

        wav_path = self.microphones.record_to_wav(
            device_index=device_index,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
        )
        return self.stt.transcribe_file(str(wav_path))

    async def process_text(self, text: str, speak_response: bool = True) -> str:
        """Process already-transcribed text through JARVIS and optional TTS."""
        response = await self.jarvis.process_user_input(text)
        if speak_response:
            self.tts.speak(response)
        return response
