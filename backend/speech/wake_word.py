"""Wake word detection and continuous voice activation."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

from logger import get_logger


@dataclass
class WakeWordMatch:
    """Result of checking a transcript for a wake word."""

    activated: bool
    wake_word: Optional[str] = None
    command: str = ""
    transcript: str = ""


class WakeWordDetector:
    """Detect configured wake words in transcribed text."""

    def __init__(self, wake_words: Optional[List[str]] = None):
        words = wake_words or ["jarvis"]
        self.wake_words = [word.strip().lower() for word in words if word.strip()]

    def detect(self, transcript: str) -> WakeWordMatch:
        normalized = " ".join(transcript.strip().split())
        lowered = normalized.lower()
        for wake_word in self.wake_words:
            pattern = rf"\b{re.escape(wake_word)}\b[\s,.:;-]*"
            match = re.search(pattern, lowered)
            if not match:
                continue
            command = normalized[match.end():].strip(" ,.:;-")
            return WakeWordMatch(
                activated=True,
                wake_word=wake_word,
                command=command,
                transcript=normalized,
            )
        return WakeWordMatch(activated=False, transcript=normalized)


@dataclass
class WakeLoopStats:
    """Runtime state for the wake listener."""

    active: bool = False
    wake_word: str = "jarvis"
    cycles: int = 0
    activations: int = 0
    ignored_transcripts: int = 0
    last_transcript: str = ""
    last_command: str = ""
    last_response: str = ""
    last_error: str = ""
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    events: List[Dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "active": self.active,
            "wake_word": self.wake_word,
            "cycles": self.cycles,
            "activations": self.activations,
            "ignored_transcripts": self.ignored_transcripts,
            "last_transcript": self.last_transcript,
            "last_command": self.last_command,
            "last_response": self.last_response,
            "last_error": self.last_error,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "events": self.events[-10:],
        }


class WakeWordListener:
    """Continuously listen for a wake word, then process the command."""

    def __init__(
        self,
        pipeline,
        wake_words: Optional[List[str]] = None,
        poll_delay: float = 0.2,
    ):
        self.logger = get_logger("speech.wake_word")
        self.pipeline = pipeline
        self.detector = WakeWordDetector(wake_words)
        self.poll_delay = poll_delay
        self.stats = WakeLoopStats(wake_word=self.detector.wake_words[0])
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    async def run(
        self,
        device_index: Optional[int] = None,
        preferred_device_name: Optional[str] = None,
        speak_response: bool = True,
        timeout: Optional[float] = 4,
        phrase_time_limit: Optional[float] = 6,
        max_cycles: Optional[int] = None,
        transcript_provider: Optional[Callable[[], str | Awaitable[str]]] = None,
    ) -> Dict[str, Any]:
        """Run the wake loop until stopped or max_cycles is reached."""
        self._stop_requested = False
        self.stats.active = True
        self.stats.started_at = datetime.now().isoformat()
        self.stats.stopped_at = None
        self.stats.last_error = ""
        cycles_this_run = 0

        while not self._stop_requested:
            if max_cycles is not None and cycles_this_run >= max_cycles:
                break
            self.stats.cycles += 1
            cycles_this_run += 1

            try:
                transcript = await self._next_transcript(
                    device_index=device_index,
                    preferred_device_name=preferred_device_name,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                    transcript_provider=transcript_provider,
                )
                self.stats.last_transcript = transcript
                match = self.detector.detect(transcript)
                if not match.activated:
                    self.stats.ignored_transcripts += 1
                    self._event("ignored", transcript=transcript)
                    await asyncio.sleep(self.poll_delay)
                    continue

                command = match.command or "health diagnostics"
                self.stats.activations += 1
                self.stats.last_command = command
                response = await self.pipeline.process_text(command, speak_response=speak_response)
                self.stats.last_response = response
                self._event("activated", transcript=transcript, command=command, response=response)
            except Exception as exc:
                self.stats.last_error = str(exc)
                self._event("error", error=str(exc))
                self.logger.warning("Wake loop iteration failed: %s", exc)

            await asyncio.sleep(self.poll_delay)

        self.stats.active = False
        self.stats.stopped_at = datetime.now().isoformat()
        return self.stats.as_dict()

    async def _next_transcript(
        self,
        device_index: Optional[int],
        preferred_device_name: Optional[str],
        timeout: Optional[float],
        phrase_time_limit: Optional[float],
        transcript_provider: Optional[Callable[[], str | Awaitable[str]]],
    ) -> str:
        if transcript_provider:
            value = transcript_provider()
            if hasattr(value, "__await__"):
                value = await value
            return str(value)

        return self.pipeline.listen_and_transcribe(
            device_index=device_index,
            preferred_device_name=preferred_device_name,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
        )

    def _event(self, event_type: str, **data: Any) -> None:
        self.stats.events.append({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **data,
        })
