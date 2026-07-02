"""
Phase 12 Architecture Foundation Test
Verify the new modular runtime bridge works without breaking legacy behavior.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.app import initialize_runtime


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
  brain:
    default_provider: legacy_core
    routing:
      reasoning: legacy_core
  security:
    require_explicit_approval: true
    approval_prefix: "approve:"
    audit_log_file: "{(temp_path / 'audit.log').as_posix()}"
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


def run_phase12_architecture_tests():
    print("\n" + "=" * 70)
    print("PHASE 12 ARCHITECTURE TEST - MODULAR RUNTIME FOUNDATION")
    print("=" * 70 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_path = temp_path / "config.yaml"
        _write_config(config_path, temp_path)

        print("[Test 1] Initializing modular runtime...")
        runtime = initialize_runtime(str(config_path))
        assert runtime.brain.default_provider == "legacy_core"
        assert "legacy_core" in runtime.brain.providers
        print("PASS - Runtime initialized with brain manager and legacy provider bridge")

        print("\n[Test 2] Processing text through runtime facade...")
        response = asyncio.run(runtime.process_text("hello"))
        assert isinstance(response, str)
        assert response
        print("PASS - Runtime facade returns response through provider routing")

        print("\n[Test 3] Writing audit entries for processed requests...")
        audit_path = temp_path / "audit.log"
        assert audit_path.exists()
        content = audit_path.read_text(encoding="utf-8").strip()
        assert "text_processed" in content
        print("PASS - Security audit logger records processing events")

    print("\n" + "=" * 70)
    print("PHASE 12 ARCHITECTURE CHECKPOINT - ALL TESTS PASSED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_phase12_architecture_tests()

