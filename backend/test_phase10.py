"""
Phase 10 Checkpoint Test
Verify local custom skill manifests, discovery, reload, and API listing.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.server import create_app
from core import initialize_jarvis


def _write_config(config_path: Path, temp_path: Path, custom_dir: Path) -> None:
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
    custom_skills_dir: "{custom_dir.as_posix()}"
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


def _write_skill(custom_dir: Path, folder: str, name: str, keyword: str, response: str) -> None:
    skill_dir = custom_dir / folder
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "skill.json").write_text(
        json.dumps({
            "name": name,
            "description": f"{name} custom skill",
            "enabled": True,
            "keywords": [keyword],
            "examples": [keyword],
            "response": response,
        }, indent=2),
        encoding="utf-8",
    )


def run_phase10_tests():
    print("\n" + "=" * 70)
    print("PHASE 10 CHECKPOINT TEST - PLUGIN MARKETPLACE & CUSTOM SKILLS")
    print("=" * 70 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        custom_dir = temp_path / "custom_skills"
        config_path = temp_path / "config.yaml"
        _write_config(config_path, temp_path, custom_dir)
        _write_skill(custom_dir, "local_status", "local_status", "local status", "Local custom skill is online.")

        print("[Test 1] Loading manifest skill at startup...")
        jarvis = initialize_jarvis(str(config_path))
        skills = jarvis.skill_registry.list_skills()
        assert "local_status" in skills
        assert jarvis.get_status()["custom_skills"] == 1
        print("✓ Custom manifest skill is registered")

        print("\n[Test 2] Executing custom skill by keyword...")
        response = asyncio.run(jarvis.process_user_input("local status"))
        assert response == "Local custom skill is online."
        print("✓ Custom skill handles low-confidence keyword text")

        print("\n[Test 3] Listing skills through API...")
        app, _socketio = create_app(str(config_path))
        client = app.test_client()
        payload = client.get("/api/skills").get_json()
        assert "local_status" in payload["skills"]
        assert payload["status"]["custom_skills"] == 1
        assert payload["custom_manifests"]
        print("✓ API exposes registered skills and discovered manifests")

        print("\n[Test 4] Reloading newly added custom skill...")
        _write_skill(custom_dir, "local_echo", "local_echo", "local echo", "Echo custom skill loaded.")
        response = client.post("/api/skills/reload")
        payload = response.get_json()
        assert response.status_code == 200
        assert set(payload["loaded"]) == {"local_status", "local_echo"}
        assert payload["status"]["custom_skills"] == 2
        print("✓ Custom skills reload from disk without restarting the process")

        print("\n[Test 5] Executing reloaded skill through chat API...")
        response = client.post("/api/chat", json={"message": "local echo"})
        payload = response.get_json()
        assert response.status_code == 200
        assert payload["response"] == "Echo custom skill loaded."
        print("✓ Reloaded custom skill routes through normal chat")

    print("\n" + "=" * 70)
    print("PHASE 10 CHECKPOINT - ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nProject roadmap complete through Phase 10")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_phase10_tests()
