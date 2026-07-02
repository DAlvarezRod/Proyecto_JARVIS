"""Smart home hub coordinator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from logger import get_logger
from smart_home.devices import Camera, Device, Door, Light, SecuritySystem, Thermostat

logger = get_logger(__name__)


DEVICE_CLASSES = {
    "camera": Camera,
    "door": Door,
    "light": Light,
    "security": SecuritySystem,
    "thermostat": Thermostat,
}


class SmartHomeHub:
    """Coordinates simulated smart home devices and state persistence."""

    def __init__(self, state_file: str = "data/devices.json", auto_save: bool = True):
        self.state_file = Path(state_file)
        self.auto_save = auto_save
        self.devices: Dict[str, Device] = {}
        self.logger = get_logger("smart_home.hub")

    def register_device(self, device: Device) -> None:
        if device.device_id in self.devices:
            self.logger.warning("Overwriting device: %s", device.device_id)
        self.devices[device.device_id] = device
        self.logger.debug("Registered device: %s", device.device_id)
        self._save_if_needed()

    def register_devices(self, devices: Iterable[Device]) -> None:
        for device in devices:
            self.devices[device.device_id] = device
            self.logger.debug("Registered device: %s", device.device_id)
        self._save_if_needed()

    def get_device(self, device_id: str) -> Optional[Device]:
        return self.devices.get(device_id)

    def list_devices(self) -> List[Dict[str, Any]]:
        return [device.get_state() for device in self.devices.values()]

    def find_devices(
        self,
        device_type: Optional[str] = None,
        location: Optional[str] = None,
        name: Optional[str] = None,
    ) -> List[Device]:
        matches = list(self.devices.values())
        if device_type:
            matches = [d for d in matches if d.device_type == device_type]
        if location:
            normalized_location = location.lower()
            matches = [d for d in matches if normalized_location in d.location.lower()]
        if name:
            normalized_name = name.lower()
            matches = [d for d in matches if normalized_name in d.name.lower()]
        return matches

    def execute_command(
        self,
        action: str,
        device_id: Optional[str] = None,
        device_type: Optional[str] = None,
        location: Optional[str] = None,
        value: Any = None,
    ) -> Dict[str, Any]:
        targets = [self.devices[device_id]] if device_id else self.find_devices(device_type, location)
        if not targets:
            return {
                "success": False,
                "message": "No matching devices found.",
                "devices": [],
            }

        results = []
        errors = []
        for device in targets:
            try:
                self._apply_action(device, action, value)
                results.append(device.get_state())
            except Exception as exc:
                errors.append({"device_id": device.device_id, "error": str(exc)})

        if results:
            self._save_if_needed()

        return {
            "success": not errors,
            "message": self._build_message(action, targets, value, errors),
            "devices": results,
            "errors": errors,
        }

    def get_status(self, device_type: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        devices = self.find_devices(device_type=device_type, location=location)
        return {
            "device_count": len(devices),
            "devices": [device.get_state() for device in devices],
            "summary": [device.status_text() for device in devices],
        }

    def save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"devices": self.list_devices()}
        self.state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.logger.debug("Saved smart home state to %s", self.state_file)

    def load_state(self) -> None:
        if not self.state_file.exists():
            self.logger.info("No smart home state file found at %s", self.state_file)
            return

        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        for state in payload.get("devices", []):
            device = self.devices.get(state["device_id"]) or self._device_from_state(state)
            device.update_from_state(state)
            self.devices[device.device_id] = device
        self.logger.debug("Loaded smart home state from %s", self.state_file)

    def _save_if_needed(self) -> None:
        if self.auto_save:
            self.save_state()

    def _apply_action(self, device: Device, action: str, value: Any = None) -> None:
        if action == "turn_on":
            device.turn_on()
        elif action == "turn_off":
            device.turn_off()
        elif action == "toggle":
            device.toggle()
        elif action == "set_brightness" and isinstance(device, Light):
            device.set_brightness(int(value))
        elif action == "set_color" and isinstance(device, Light):
            device.set_color(str(value))
        elif action == "set_temperature" and isinstance(device, Thermostat):
            device.set_temperature(float(value))
        elif action == "set_mode" and isinstance(device, Thermostat):
            device.set_mode(str(value))
        elif action == "lock" and isinstance(device, Door):
            device.lock()
        elif action == "unlock" and isinstance(device, Door):
            device.unlock()
        elif action == "open" and isinstance(device, Door):
            device.open()
        elif action == "close" and isinstance(device, Door):
            device.close()
        elif action == "arm" and isinstance(device, SecuritySystem):
            device.arm(str(value or "away"))
        elif action == "disarm" and isinstance(device, SecuritySystem):
            device.disarm()
        elif action == "start_recording" and isinstance(device, Camera):
            device.start_recording()
        elif action == "stop_recording" and isinstance(device, Camera):
            device.stop_recording()
        else:
            raise ValueError(f"Action '{action}' is not supported for {device.device_type}")

    def _build_message(
        self,
        action: str,
        targets: List[Device],
        value: Any,
        errors: List[Dict[str, str]],
    ) -> str:
        if errors and len(errors) == len(targets):
            return "Command failed for all matching devices."

        names = ", ".join(device.name for device in targets)
        if value is not None:
            return f"Applied {action}={value} to {names}."
        return f"Applied {action} to {names}."

    def _device_from_state(self, state: Dict[str, Any]) -> Device:
        device_type = state["device_type"]
        cls = DEVICE_CLASSES.get(device_type)
        if cls is None:
            return Device(
                device_id=state["device_id"],
                name=state["name"],
                location=state["location"],
                device_type=device_type,
            )
        return cls(state["device_id"], state["name"], state["location"])


def create_default_hub(state_file: str = "data/devices.json", load_existing: bool = True) -> SmartHomeHub:
    """Create the default simulated home used during Phase 2."""
    hub = SmartHomeHub(state_file=state_file, auto_save=False)
    hub.register_devices([
        Light("light_living_room", "Living Room Light", "living room"),
        Light("light_kitchen", "Kitchen Light", "kitchen"),
        Light("light_bedroom", "Bedroom Light", "bedroom"),
        Thermostat("thermostat_hallway", "Main Thermostat", "hallway"),
        Door("door_front", "Front Door", "entry"),
        SecuritySystem("security_main", "Main Security System"),
        Camera("camera_front", "Front Camera", "entry"),
    ])
    if load_existing:
        hub.load_state()
    hub.auto_save = True
    hub.save_state()
    return hub
