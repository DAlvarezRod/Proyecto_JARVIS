"""
Phase 11 Orchestrator Checkpoint Test
Verify secure personal assistant orchestrator behavior and safety gates.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core import initialize_jarvis


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
  orchestrator:
    enabled: true
    safety:
      require_explicit_approval: true
      disclose_limitations: true
      privileged_keywords:
        - send text
        - delete account
        - factory reset
logging:
  level: ERROR
  file: "{(temp_path / 'jarvis.log').as_posix()}"
  max_size_mb: 10
  backup_count: 1
skills:
  enabled:
    - greeting
    - orchestrator
  greeting:
    enabled: true
  orchestrator:
    enabled: true
""",
        encoding="utf-8",
    )


def run_phase11_orchestrator_tests():
    print("\n" + "=" * 70)
    print("PHASE 11 ORCHESTRATOR TEST - SECURE PERSONAL ORCHESTRATION")
    print("=" * 70 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_path = temp_path / "config.yaml"
        _write_config(config_path, temp_path)

        jarvis = initialize_jarvis(str(config_path))

        print("[Test 1] Registering orchestrator skill...")
        skills = jarvis.skill_registry.list_skills()
        assert "orchestrator" in skills
        print("PASS - Orchestrator skill registered from standard skill pipeline")

        print("\n[Test 2] Running safe account task check...")
        response = asyncio.run(jarvis.process_user_input("check account tasks"))
        assert "Account task check complete." in response
        assert "cannot autonomously control all accounts or devices" in response
        print("PASS - Accounts domain returns actionable plan with explicit limitations")

        print("\n[Test 3] Running safe peripherals check...")
        response = asyncio.run(jarvis.process_user_input("manage peripherals"))
        assert "Peripheral check complete." in response
        print("PASS - Peripherals domain executes safe local adapter action")

        print("\n[Test 4] Running safe phone planning action...")
        response = asyncio.run(jarvis.process_user_input("manage phone tasks for tomorrow"))
        assert "Phone planning draft created" in response
        print("PASS - Phone domain executes local draft action without claiming real control")

        print("\n[Test 5] Blocking privileged action without explicit approval...")
        response = asyncio.run(jarvis.process_user_input("manage phone and send text to Alex"))
        assert "privileged and I will not execute it automatically" in response
        assert "Approve orchestrator phone action" in response
        print("PASS - Privileged mobile action requires explicit confirmation")

    print("\n" + "=" * 70)
    print("PHASE 11 ORCHESTRATOR CHECKPOINT - ALL TESTS PASSED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_phase11_orchestrator_tests()
