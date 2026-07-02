"""Microphone discovery and audio capture helpers."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pyaudio
import speech_recognition as sr

from logger import get_logger


@dataclass
class AudioInputDevice:
    """A microphone/input device reported by PortAudio."""

    index: int
    name: str
    channels: int
    default_sample_rate: int
    host_api: int
    is_default: bool = False
    is_loopback: bool = False


class MicrophoneManager:
    """List and select active microphones using PyAudio."""

    def __init__(self):
        self.logger = get_logger("speech.microphone")

    def list_input_devices(self, include_loopback: bool = False) -> List[AudioInputDevice]:
        pa = pyaudio.PyAudio()
        devices: List[AudioInputDevice] = []
        default_index = self._default_input_index(pa)
        try:
            for index in range(pa.get_device_count()):
                raw = pa.get_device_info_by_index(index)
                channels = int(raw.get("maxInputChannels", 0))
                if channels <= 0:
                    continue
                name = str(raw.get("name", "Unknown"))
                is_loopback = "loopback" in name.lower()
                if is_loopback and not include_loopback:
                    continue
                devices.append(
                    AudioInputDevice(
                        index=index,
                        name=name,
                        channels=channels,
                        default_sample_rate=int(raw.get("defaultSampleRate", 0)),
                        host_api=int(raw.get("hostApi", -1)),
                        is_default=index == default_index,
                        is_loopback=is_loopback,
                    )
                )
        finally:
            pa.terminate()
        return devices

    def get_default_input_device(self) -> Optional[AudioInputDevice]:
        devices = self.list_input_devices(include_loopback=False)
        for device in devices:
            if device.is_default:
                return device
        return devices[0] if devices else None

    def find_input_device(self, preferred_name: str) -> Optional[AudioInputDevice]:
        needle = preferred_name.lower()
        for device in self.list_input_devices(include_loopback=False):
            if needle in device.name.lower():
                return device
        return None

    def record_to_wav(
        self,
        output_path: Optional[str] = None,
        device_index: Optional[int] = None,
        timeout: Optional[float] = 5,
        phrase_time_limit: Optional[float] = 8,
        calibrate_seconds: float = 0.5,
    ) -> Path:
        """Record a phrase from the selected/default microphone into a WAV file."""
        recognizer = sr.Recognizer()
        with sr.Microphone(device_index=device_index) as source:
            recognizer.adjust_for_ambient_noise(source, duration=calibrate_seconds)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        path = Path(output_path) if output_path else Path(tempfile.mkstemp(suffix=".wav")[1])
        path.write_bytes(audio.get_wav_data())
        self.logger.debug("Recorded microphone audio to %s", path)
        return path

    def _default_input_index(self, pa: pyaudio.PyAudio) -> Optional[int]:
        try:
            return int(pa.get_default_input_device_info()["index"])
        except Exception:
            return None
