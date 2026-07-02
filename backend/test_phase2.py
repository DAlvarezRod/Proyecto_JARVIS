"""
Phase 2 Checkpoint Test
Verify smart home devices, hub, parser, and persistence.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from smart_home import CommandParser, SmartHomeHub, create_default_hub
from smart_home.devices import Door, Light, Thermostat


def run_phase2_tests():
    print("\n" + "=" * 70)
    print("PHASE 2 CHECKPOINT TEST - SMART HOME SIMULATION")
    print("=" * 70 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        state_file = str(Path(temp_dir) / "devices.json")

        print("[Test 1] Creating default smart home hub...")
        hub = create_default_hub(state_file=state_file, load_existing=False)
        assert len(hub.devices) == 7
        print(f"✓ Default devices registered: {len(hub.devices)}")

        print("\n[Test 2] Controlling lights...")
        result = hub.execute_command("turn_on", device_type="light", location="kitchen")
        assert result["success"] is True
        kitchen_light = hub.get_device("light_kitchen")
        assert kitchen_light.is_on is True
        hub.execute_command("set_brightness", device_type="light", location="kitchen", value=35)
        assert kitchen_light.brightness == 35
        print("✓ Kitchen light turned on and dimmed to 35%")

        print("\n[Test 3] Controlling thermostat...")
        result = hub.execute_command("set_temperature", device_type="thermostat", value=24)
        assert result["success"] is True
        thermostat = hub.get_device("thermostat_hallway")
        assert thermostat.target_temperature == 24
        print("✓ Thermostat target temperature set to 24C")

        print("\n[Test 4] Controlling door locks...")
        door = hub.get_device("door_front")
        assert door.is_locked is True
        hub.execute_command("unlock", device_type="door")
        hub.execute_command("open", device_type="door")
        assert door.is_locked is False
        assert door.is_open is True
        print("✓ Front door unlocked and opened")

        print("\n[Test 5] Parsing smart home commands...")
        parser = CommandParser()
        command = parser.parse("Turn on the living room lights")
        assert command.action == "turn_on"
        assert command.device_type == "light"
        assert command.location == "living room"
        command = parser.parse("Set the thermostat to 23 degrees")
        assert command.action == "set_temperature"
        assert command.value == 23
        print("✓ Command parser recognizes actions, devices, locations, and values")

        print("\n[Test 6] Persisting and restoring state...")
        hub.save_state()
        restored = SmartHomeHub(state_file=state_file, auto_save=False)
        restored.register_devices([
            Light("light_kitchen", "Kitchen Light", "kitchen"),
            Thermostat("thermostat_hallway", "Main Thermostat", "hallway"),
            Door("door_front", "Front Door", "entry"),
        ])
        restored.load_state()
        assert restored.get_device("light_kitchen").brightness == 35
        assert restored.get_device("door_front").is_open is True
        print("✓ Device state saved and restored from JSON")

        print("\n[Test 7] Reporting smart home status...")
        status = hub.get_status(device_type="light")
        assert status["device_count"] == 3
        assert len(status["summary"]) == 3
        print("✓ Hub reports filtered device status")

    print("\n" + "=" * 70)
    print("PHASE 2 CHECKPOINT - ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nReady for Phase 3: NLP Engine")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_phase2_tests()
