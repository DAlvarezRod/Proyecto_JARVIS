"""Speech-to-text support using OpenAI Whisper locally."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import whisper

from logger import get_logger


class SpeechToText:
    """Transcribe audio files with a local Whisper model."""

    def __init__(self, model_name: str = "base"):
        self.logger = get_logger("speech.stt")
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self.logger.info("Loading Whisper model: %s", self.model_name)
            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe_file(self, audio_path: str, language: Optional[str] = None) -> str:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(path)
        options = {"fp16": False}
        if language:
            options["language"] = language
        result = self.model.transcribe(str(path), **options)
        return str(result.get("text", "")).strip()
