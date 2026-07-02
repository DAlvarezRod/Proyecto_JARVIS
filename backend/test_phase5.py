"""
Phase 5 Checkpoint Test
Verify Flask API and Socket.IO app wiring.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.server import create_app


def run_phase5_tests():
    print("\n" + "=" * 70)
    print("PHASE 5 CHECKPOINT TEST - API & REAL-TIME SERVER")
    print("=" * 70 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "config.yaml"
        devices_path = Path(temp_dir) / "devices.json"
        config_path.write_text(
            f"""
jarvis:
  name: "JARVIS"
  version: "1.0.0"
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
        app, _socketio = create_app(str(config_path))
        client = app.test_client()

        print("[Test 1] Checking health endpoint...")
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.get_json()["ok"] is True
        print("✓ /api/health returns ok")

        print("\n[Test 2] Listing devices...")
        response = client.get("/api/devices")
        devices = response.get_json()
        assert response.status_code == 200
        assert len(devices) == 7
        print("✓ /api/devices returns default smart home devices")

        print("\n[Test 3] Sending chat command through API...")
        response = client.post("/api/chat", json={"message": "Turn on the kitchen light"})
        payload = response.get_json()
        assert response.status_code == 200
        assert "Kitchen Light" in payload["response"]
        kitchen = [d for d in payload["devices"] if d["device_id"] == "light_kitchen"][0]
        assert kitchen["is_on"] is True
        print("✓ /api/chat routes text through JARVIS NLP and Smart Home")

        print("\n[Test 4] Executing direct device command...")
        response = client.post("/api/devices/command", json={
            "action": "turn_off",
            "device_id": "light_kitchen",
        })
        payload = response.get_json()
        assert response.status_code == 200
        assert payload["result"]["success"] is True
        print("✓ /api/devices/command controls devices")

        print("\n[Test 5] Reading conversation history...")
        response = client.get("/api/history")
        history = response.get_json()
        assert response.status_code == 200
        assert len(history) >= 2
        print("✓ /api/history returns recent chat messages")

    print("\n" + "=" * 70)
    print("PHASE 5 CHECKPOINT - ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nReady for Phase 6: Skill System & API Integration")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_phase5_tests()
