"""
Phase 9 Checkpoint Test
Verify automation rules, scheduled background logic, and API integration.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.server import create_app


def _write_config(config_path: Path, temp_path: Path) -> None:
    config_path.write_text(
        f"""
jarvis:
  name: "JARVIS"
  version: "1.0.0"
  nlu:
    confidence_threshold: 0.7
    max_context_history: 10
  storage:
    conversation_db: "{(temp_path / 'conversations.db').as_posix()}"
    device_state_file: "{(temp_path / 'devices.json').as_posix()}"
    automation_rules_file: "{(temp_path / 'automations.json').as_posix()}"
  automation:
    background_enabled: false
    poll_interval: 0.1
logging:
  level: ERROR
  file: "{(temp_path / 'jarvis.log').as_posix()}"
  max_size_mb: 10
  backup_count: 1
skills:
  enabled:
    - greeting
    - smart_home
    - calculator
  greeting:
    enabled: true
  smart_home:
    enabled: true
  calculator:
    enabled: true
""",
        encoding="utf-8",
    )


def run_phase9_tests():
    print("\n" + "=" * 70)
    print("PHASE 9 CHECKPOINT TEST - AUTOMATION RULES & BACKGROUND TASKS")
    print("=" * 70 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_path = temp_path / "config.yaml"
        _write_config(config_path, temp_path)

        app, _socketio = create_app(str(config_path))
        client = app.test_client()

        print("[Test 1] Creating device-state automation rule...")
        response = client.post("/api/automations", json={
            "name": "Kitchen light turns on bedroom",
            "trigger": {
                "type": "device_state",
                "device_id": "light_kitchen",
                "property": "is_on",
                "equals": True,
            },
            "action": {
                "type": "smart_home",
                "action": "turn_on",
                "device_id": "light_bedroom",
            },
        })
        payload = response.get_json()
        assert response.status_code == 201
        rule_id = payload["rule"]["rule_id"]
        assert payload["status"]["rules"] == 1
        print("✓ Automation rule can be created through the API")

        print("\n[Test 2] Triggering automation from smart home event...")
        response = client.post("/api/devices/command", json={
            "action": "turn_on",
            "device_id": "light_kitchen",
        })
        assert response.status_code == 200
        devices = response.get_json()["devices"]
        bedroom = [device for device in devices if device["device_id"] == "light_bedroom"][0]
        assert bedroom["is_on"] is True
        status = client.get("/api/status").get_json()
        assert status["automation"]["executions"] >= 1
        print("✓ Device-state rule executes an automation action")

        print("\n[Test 3] Running scheduled automation manually...")
        response = client.post("/api/automations", json={
            "name": "Scheduled bedroom off",
            "trigger": {
                "type": "schedule",
                "interval_seconds": 1,
            },
            "action": {
                "type": "smart_home",
                "action": "turn_off",
                "device_id": "light_bedroom",
            },
        })
        assert response.status_code == 201
        response = client.post("/api/automations/run-pending")
        payload = response.get_json()
        assert response.status_code == 200
        assert payload["executions"]
        bedroom = [device for device in payload["devices"] if device["device_id"] == "light_bedroom"][0]
        assert bedroom["is_on"] is False
        print("✓ Scheduled rule can be evaluated by the background-task runner")

        print("\n[Test 4] Persisting and reloading rules...")
        app_reloaded, _socketio_reloaded = create_app(str(config_path))
        reloaded_client = app_reloaded.test_client()
        response = reloaded_client.get("/api/automations")
        payload = response.get_json()
        assert response.status_code == 200
        assert payload["status"]["rules"] == 2
        print("✓ Automation rules persist to JSON and reload")

        print("\n[Test 5] Updating and deleting rules...")
        response = reloaded_client.patch(f"/api/automations/{rule_id}", json={"enabled": False})
        assert response.status_code == 200
        assert response.get_json()["rule"]["enabled"] is False
        response = reloaded_client.delete(f"/api/automations/{rule_id}")
        assert response.status_code == 200
        assert response.get_json()["status"]["rules"] == 1
        print("✓ Automation rules can be disabled and deleted")

    print("\n" + "=" * 70)
    print("PHASE 9 CHECKPOINT - ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nReady for Phase 10: Plugin Marketplace & Custom Skills")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_phase9_tests()
