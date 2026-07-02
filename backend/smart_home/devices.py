"""
Smart home device models.

Phase 2 keeps devices in memory, with JSON-friendly state so the hub can
persist and restore the simulated home.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


def _timestamp() -> str:
    return datetime.now().isoformat()


@dataclass
class Device:
    """Base class for all smart home devices."""

    device_id: str
    name: str
    location: str
    device_type: str
    is_on: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = field(default_factory=_timestamp)

    def turn_on(self) -> None:
        self.is_on = True
        self.touch()

    def turn_off(self) -> None:
        self.is_on = False
        self.touch()

    def toggle(self) -> None:
        self.is_on = not self.is_on
        self.touch()

    def touch(self) -> None:
        self.last_updated = _timestamp()

    def get_state(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "location": self.location,
            "device_type": self.device_type,
            "is_on": self.is_on,
            "metadata": self.metadata,
            "last_updated": self.last_updated,
        }

    def update_from_state(self, state: Dict[str, Any]) -> None:
        self.is_on = bool(state.get("is_on", self.is_on))
        self.metadata = dict(state.get("metadata", self.metadata))
        self.last_updated = state.get("last_updated", self.last_updated)

    def status_text(self) -> str:
        state = "on" if self.is_on else "off"
        return f"{self.name} in {self.location} is {state}"


@dataclass
class Light(Device):
    """Dimmable light device."""

    brightness: int = 100
    color: str = "white"

    def __init__(self, device_id: str, name: str, location: str):
        super().__init__(device_id, name, location, "light")
        self.brightness = 100
        self.color = "white"

    def set_brightness(self, value: int) -> None:
        self.brightness = max(0, min(100, int(value)))
        self.is_on = self.brightness > 0
        self.touch()

    def set_color(self, color: str) -> None:
        self.color = color
        self.touch()

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state.update({"brightness": self.brightness, "color": self.color})
        return state

    def update_from_state(self, state: Dict[str, Any]) -> None:
        super().update_from_state(state)
        self.brightness = int(state.get("brightness", self.brightness))
        self.color = state.get("color", self.color)

    def status_text(self) -> str:
        state = "on" if self.is_on else "off"
        return f"{self.name} in {self.location} is {state} at {self.brightness}%"


@dataclass
class Thermostat(Device):
    """Thermostat with target temperature and HVAC mode."""

    current_temperature: float = 21.0
    target_temperature: float = 22.0
    mode: str = "auto"

    def __init__(self, device_id: str, name: str, location: str):
        super().__init__(device_id, name, location, "thermostat", is_on=True)
        self.current_temperature = 21.0
        self.target_temperature = 22.0
        self.mode = "auto"

    def set_temperature(self, value: float) -> None:
        self.target_temperature = float(value)
        self.is_on = True
        self.touch()

    def set_mode(self, mode: str) -> None:
        allowed = {"auto", "heat", "cool", "off"}
        if mode not in allowed:
            raise ValueError(f"Unsupported thermostat mode: {mode}")
        self.mode = mode
        self.is_on = mode != "off"
        self.touch()

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state.update({
            "current_temperature": self.current_temperature,
            "target_temperature": self.target_temperature,
            "mode": self.mode,
        })
        return state

    def update_from_state(self, state: Dict[str, Any]) -> None:
        super().update_from_state(state)
        self.current_temperature = float(state.get("current_temperature", self.current_temperature))
        self.target_temperature = float(state.get("target_temperature", self.target_temperature))
        self.mode = state.get("mode", self.mode)

    def status_text(self) -> str:
        return (
            f"{self.name} in {self.location} is set to "
            f"{self.target_temperature:g}C ({self.mode})"
        )


@dataclass
class Door(Device):
    """Door lock/open simulation."""

    is_open: bool = False
    is_locked: bool = True

    def __init__(self, device_id: str, name: str, location: str):
        super().__init__(device_id, name, location, "door")
        self.is_open = False
        self.is_locked = True

    def lock(self) -> None:
        self.is_locked = True
        self.is_open = False
        self.touch()

    def unlock(self) -> None:
        self.is_locked = False
        self.touch()

    def open(self) -> None:
        if self.is_locked:
            raise ValueError(f"{self.name} is locked")
        self.is_open = True
        self.touch()

    def close(self) -> None:
        self.is_open = False
        self.touch()

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state.update({"is_open": self.is_open, "is_locked": self.is_locked})
        return state

    def update_from_state(self, state: Dict[str, Any]) -> None:
        super().update_from_state(state)
        self.is_open = bool(state.get("is_open", self.is_open))
        self.is_locked = bool(state.get("is_locked", self.is_locked))

    def status_text(self) -> str:
        open_state = "open" if self.is_open else "closed"
        lock_state = "locked" if self.is_locked else "unlocked"
        return f"{self.name} in {self.location} is {open_state} and {lock_state}"


@dataclass
class SecuritySystem(Device):
    """Home security system simulation."""

    is_armed: bool = False
    mode: str = "disarmed"
    alarm_triggered: bool = False

    def __init__(self, device_id: str, name: str, location: str = "home"):
        super().__init__(device_id, name, location, "security")
        self.is_armed = False
        self.mode = "disarmed"
        self.alarm_triggered = False

    def arm(self, mode: str = "away") -> None:
        allowed = {"home", "away", "night"}
        if mode not in allowed:
            raise ValueError(f"Unsupported security mode: {mode}")
        self.is_on = True
        self.is_armed = True
        self.mode = mode
        self.touch()

    def disarm(self) -> None:
        self.is_on = False
        self.is_armed = False
        self.mode = "disarmed"
        self.alarm_triggered = False
        self.touch()

    def trigger_alarm(self) -> None:
        if self.is_armed:
            self.alarm_triggered = True
            self.touch()

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state.update({
            "is_armed": self.is_armed,
            "mode": self.mode,
            "alarm_triggered": self.alarm_triggered,
        })
        return state

    def update_from_state(self, state: Dict[str, Any]) -> None:
        super().update_from_state(state)
        self.is_armed = bool(state.get("is_armed", self.is_armed))
        self.mode = state.get("mode", self.mode)
        self.alarm_triggered = bool(state.get("alarm_triggered", self.alarm_triggered))

    def status_text(self) -> str:
        alarm = " alarm triggered" if self.alarm_triggered else ""
        return f"{self.name} is {self.mode}{alarm}"


@dataclass
class Camera(Device):
    """Security camera simulation."""

    is_recording: bool = False
    is_streaming: bool = False
    motion_detected: bool = False

    def __init__(self, device_id: str, name: str, location: str):
        super().__init__(device_id, name, location, "camera")
        self.is_recording = False
        self.is_streaming = False
        self.motion_detected = False

    def start_recording(self) -> None:
        self.is_on = True
        self.is_recording = True
        self.touch()

    def stop_recording(self) -> None:
        self.is_recording = False
        self.is_on = self.is_streaming
        self.touch()

    def start_streaming(self) -> None:
        self.is_on = True
        self.is_streaming = True
        self.touch()

    def stop_streaming(self) -> None:
        self.is_streaming = False
        self.is_on = self.is_recording
        self.touch()

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state.update({
            "is_recording": self.is_recording,
            "is_streaming": self.is_streaming,
            "motion_detected": self.motion_detected,
        })
        return state

    def update_from_state(self, state: Dict[str, Any]) -> None:
        super().update_from_state(state)
        self.is_recording = bool(state.get("is_recording", self.is_recording))
        self.is_streaming = bool(state.get("is_streaming", self.is_streaming))
        self.motion_detected = bool(state.get("motion_detected", self.motion_detected))

    def status_text(self) -> str:
        state = "recording" if self.is_recording else "idle"
        return f"{self.name} in {self.location} is {state}"
