"""
Phase 11 Checkpoint Test
Verify Windows backend autostart management and API integration.
"""

import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))

from api.server import create_app
from system_startup import AUTOSTART_FILE_NAME, AUTOSTART_MARKER, StartupManager


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
logging:
  level: ERROR
  file: "{(temp_path / 'jarvis.log').as_posix()}"
  max_size_mb: 10
  backup_count: 1
skills:
  enabled:
    - greeting
  greeting:
    enabled: true
""",
        encoding="utf-8",
    )


def run_phase11_tests():
    print("\n" + "=" * 70)
    print("PHASE 11 CHECKPOINT TEST - WINDOWS AUTOSTART MANAGEMENT")
    print("=" * 70 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        startup_dir = temp_path / "startup"
        manager = StartupManager(
            backend_dir=Path(__file__).parent,
            startup_dir=startup_dir,
            python_executable=sys.executable,
        )

        print("[Test 1] Non-Windows platforms are explicit not-supported...")
        with mock.patch("system_startup.sys.platform", "linux"):
            status = manager.status()
            assert status["success"] is False
            assert status["error"]["code"] == "not-supported"
        print("OK - Not-supported response is explicit and safe")

        print("\n[Test 2] Enabling/disabling managed startup entry on Windows...")
        with mock.patch("system_startup.sys.platform", "win32"):
            status = manager.status()
            assert status["success"] is True
            assert status["enabled"] is False

            enabled = manager.enable()
            assert enabled["success"] is True
            assert enabled["enabled"] is True
            autostart_file = startup_dir / AUTOSTART_FILE_NAME
            assert autostart_file.exists()
            assert AUTOSTART_MARKER in autostart_file.read_text(encoding="utf-8")

            disabled = manager.disable()
            assert disabled["success"] is True
            assert disabled["enabled"] is False
        print("OK - Managed Startup entry can be enabled and disabled")

        print("\n[Test 3] Refusing to overwrite unmanaged startup entry...")
        unmanaged_file = startup_dir / AUTOSTART_FILE_NAME
        startup_dir.mkdir(parents=True, exist_ok=True)
        unmanaged_file.write_text("@echo off\nREM external file\n", encoding="utf-8")
        with mock.patch("system_startup.sys.platform", "win32"):
            result = manager.enable()
            assert result["success"] is False
            assert result["error"]["code"] == "startup-entry-conflict"
        print("OK - Safety guard prevents silent overwrite of unmanaged entries")

        print("\n[Test 4] API endpoints expose startup status/actions...")
        unmanaged_file.unlink()
        config_path = temp_path / "config.yaml"
        _write_config(config_path, temp_path)
        with mock.patch("system_startup.sys.platform", "win32"):
            app, _socketio = create_app(str(config_path), startup_manager=manager)
            client = app.test_client()
            status_response = client.get("/api/system/startup")
            assert status_response.status_code == 200
            assert status_response.get_json()["action"] == "status"
            enable_response = client.post("/api/system/startup/enable")
            assert enable_response.status_code == 200
            assert enable_response.get_json()["enabled"] is True
            disable_response = client.post("/api/system/startup/disable")
            assert disable_response.status_code == 200
            assert disable_response.get_json()["enabled"] is False
        print("OK - API routes are integrated and return structured payloads")

    print("\n" + "=" * 70)
    print("PHASE 11 CHECKPOINT - ALL TESTS PASSED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_phase11_tests()
