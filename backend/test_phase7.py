"""
Phase 7 Checkpoint Test
Verify end-to-end integration, persistent memory, and runtime metrics.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.server import create_app


def _write_config(config_path: Path, devices_path: Path, memory_path: Path, log_path: Path) -> None:
    config_path.write_text(
        f"""
jarvis:
  name: "JARVIS"
  version: "1.0.0"
  nlu:
    confidence_threshold: 0.7
    max_context_history: 10
  api:
    timeout: 3
  storage:
    conversation_db: "{memory_path.as_posix()}"
    device_state_file: "{devices_path.as_posix()}"
logging:
  level: ERROR
  file: "{log_path.as_posix()}"
  max_size_mb: 10
  backup_count: 1
skills:
  enabled:
    - greeting
    - time
    - smart_home
    - calculator
    - weather
    - news
  greeting:
    enabled: true
  time:
    enabled: true
    timezone: America/Bogota
  smart_home:
    enabled: true
  calculator:
    enabled: true
  weather:
    enabled: true
  news:
    enabled: true
""",
        encoding="utf-8",
    )


def run_phase7_tests():
    print("\n" + "=" * 70)
    print("PHASE 7 CHECKPOINT TEST - INTEGRATION & ADVANCED FEATURES")
    print("=" * 70 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_path = temp_path / "config.yaml"
        devices_path = temp_path / "devices.json"
        memory_path = temp_path / "conversations.db"
        log_path = temp_path / "jarvis.log"
        _write_config(config_path, devices_path, memory_path, log_path)

        app, _socketio = create_app(str(config_path))
        client = app.test_client()

        print("[Test 1] Running end-to-end chat through API...")
        response = client.post("/api/chat", json={"message": "Calculate 8 times 7"})
        payload = response.get_json()
        assert response.status_code == 200
        assert "56" in payload["response"]
        assert payload["status"]["performance"]["last_response_ms"] is not None
        print("✓ Chat routes through API, NLU, skill execution, and performance metrics")

        print("\n[Test 2] Persisting conversation memory...")
        response = client.get("/api/memory")
        memory = response.get_json()
        assert response.status_code == 200
        assert memory["count"] >= 2
        assert any(message["speaker"] == "assistant" for message in memory["messages"])
        print("✓ Conversation memory is persisted in SQLite")

        print("\n[Test 3] Reloading JARVIS with existing memory...")
        app_reloaded, _socketio_reloaded = create_app(str(config_path))
        reloaded_client = app_reloaded.test_client()
        response = reloaded_client.get("/api/history")
        history = response.get_json()
        assert response.status_code == 200
        assert len(history) >= 2
        assert any("56" in message["text"] for message in history)
        print("✓ Recent conversation history survives app restart")

        print("\n[Test 4] Running integration health check...")
        response = reloaded_client.get("/api/integration-check")
        integration = response.get_json()
        assert response.status_code == 200
        assert integration["ok"] is True
        assert all(integration["checks"].values())
        print("✓ Integration check validates core, skills, smart home, memory, and metrics")

        print("\n[Test 5] Clearing persistent history...")
        response = reloaded_client.delete("/api/history")
        assert response.status_code == 200
        response = reloaded_client.get("/api/memory")
        assert response.get_json()["count"] == 0
        print("✓ History clear resets RAM and SQLite memory")

    print("\n" + "=" * 70)
    print("PHASE 7 CHECKPOINT - ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nReady for Phase 8: Wake Word & Voice Activation")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_phase7_tests()
