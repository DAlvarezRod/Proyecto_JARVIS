"""
Phase 13 Checkpoint Test
Coder agent (OpenRouter provider), sandboxed execution, and Vento skill
foundation -- all mocked, no real network calls.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))

from skills.base import Intent

from src.brain.manager import BrainManager
from src.brain.providers.base import BrainProvider
from src.brain.providers.openrouter import OpenRouterError, OpenRouterProvider
from src.security.audit import AuditLogger
from src.security.authorization import AuthorizationService
from src.security.sandbox import SandboxExecutor, SandboxViolation
from src.skills.coder_agent import CoderAgentSkill
from src.skills.vento.client import VentoClient, VentoClientError
from src.skills.vento.skill import VentoSkill


class FakeBrainProvider(BrainProvider):
    """Deterministic provider used to drive CoderAgentSkill's ReAct loop."""

    name = "fake_coder"

    def __init__(self, responses: List[str]):
        self._responses = list(responses)
        self.calls: List[Dict[str, Any]] = []

    async def think(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        self.calls.append({"prompt": prompt, "context": context})
        return self._responses.pop(0)


def _make_intent(text: str, **entities) -> Intent:
    return Intent(intent_type="coder_generate", original_text=text, entities=entities)


def test_openrouter_provider_think():
    print("[Test 1] OpenRouterProvider.think() with mocked aiohttp...")

    provider = OpenRouterProvider(api_key="sk-test", default_model="anthropic/claude-sonnet-4")

    mock_response_payload = {
        "choices": [{"message": {"content": "print('hello world')"}}]
    }

    class MockResponse:
        status = 200
        content_type = "application/json"

        async def json(self):
            return mock_response_payload

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    class MockSession:
        def post(self, url, headers=None, json=None):
            assert "chat/completions" in url
            assert headers["Authorization"] == "Bearer sk-test"
            return MockResponse()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    with patch("aiohttp.ClientSession", return_value=MockSession()):
        result = asyncio.run(provider.think("Write a hello world function"))

    assert result == "print('hello world')"
    print("PASS - OpenRouterProvider parses chat completion response")

    print("\n[Test 1b] OpenRouterProvider raises OpenRouterError on HTTP error...")

    class ErrorResponse(MockResponse):
        status = 401

        async def json(self):
            return {"error": {"message": "invalid api key"}}

    class ErrorSession(MockSession):
        def post(self, url, headers=None, json=None):
            return ErrorResponse()

    with patch("aiohttp.ClientSession", return_value=ErrorSession()):
        try:
            asyncio.run(provider.think("test"))
            raise AssertionError("Expected OpenRouterError")
        except OpenRouterError as exc:
            assert "invalid api key" in str(exc)
    print("PASS - OpenRouterProvider surfaces API errors as OpenRouterError")


def test_sandbox_executor():
    print("\n[Test 2] SandboxExecutor command classification and guardrails...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        audit = AuditLogger(path=str(temp_path / "audit.log"))
        security = AuthorizationService(require_explicit_approval=True)
        sandbox = SandboxExecutor(
            allowed_dirs=[str(temp_path)],
            default_timeout=10,
            security=security,
            audit=audit,
        )

        assert sandbox.classify_command("python test_phase1.py") == "safe"
        assert sandbox.classify_command("rm -rf /") == "destructive"
        assert sandbox.classify_command("some-random-tool --flag") == "unknown"
        print("PASS - classify_command distinguishes safe/destructive/unknown")

        assert sandbox.is_path_allowed(str(temp_path))
        assert not sandbox.is_path_allowed(str(temp_path.parent.parent))
        print("PASS - is_path_allowed enforces AGENT_ALLOWED_DIRS")

        try:
            asyncio.run(sandbox.run("dir", cwd=str(Path("C:/definitely/not/allowed"))))
            raise AssertionError("Expected SandboxViolation for disallowed cwd")
        except SandboxViolation:
            pass
        print("PASS - run() rejects disallowed cwd")

        try:
            asyncio.run(sandbox.run("rm -rf somefile", cwd=str(temp_path)))
            raise AssertionError("Expected SandboxViolation without approval")
        except SandboxViolation:
            pass
        print("PASS - destructive command blocked without approval")

        script_path = temp_path / "print_one.py"
        script_path.write_text("print(1)\n", encoding="utf-8")
        result = asyncio.run(
            sandbox.run(
                f"python {script_path.name}",
                cwd=str(temp_path),
            )
        )
        assert result.classification == "safe"
        assert result.approved is True
        assert result.return_code == 0
        assert "1" in result.stdout
        print("PASS - safe command executes without requiring approval")

        audit_content = (temp_path / "audit.log").read_text(encoding="utf-8")
        assert "sandbox_command" in audit_content
        assert "sandbox_rejected" in audit_content
        print("PASS - AuditLogger records sandbox events")


def test_coder_agent_skill():
    print("\n[Test 3] CoderAgentSkill ReAct loop (read_file -> final)...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        sample_file = temp_path / "sample.py"
        sample_file.write_text("print('sample')\n", encoding="utf-8")

        audit = AuditLogger(path=str(temp_path / "audit.log"))
        security = AuthorizationService(require_explicit_approval=True)
        sandbox = SandboxExecutor(
            allowed_dirs=[str(temp_path)], security=security, audit=audit
        )

        read_action = json.dumps({"action": "read_file", "params": {"path": str(sample_file)}})
        final_action = json.dumps(
            {"action": "final", "params": {"answer": "The file prints 'sample'."}}
        )
        fake_provider = FakeBrainProvider([read_action, final_action])

        brain = BrainManager(default_provider="fake_coder", routing={"coding": "fake_coder"})
        brain.register_provider(fake_provider)

        skill = CoderAgentSkill(
            brain_manager=brain, sandbox=sandbox, security=security, audit=audit
        )

        intent = _make_intent(f"Read {sample_file} and summarize it")
        response = skill.execute(intent)

        assert response.success is True
        assert "sample" in response.text
        assert len(fake_provider.calls) == 2
        assert response.data["trace"][0]["action"] == "read_file"
        print("PASS - CoderAgentSkill executes tool calls and returns final answer")

        print("\n[Test 3b] CoderAgentSkill blocks write_file without approval...")
        target_file = temp_path / "new_file.py"
        write_action = json.dumps(
            {"action": "write_file", "params": {"path": str(target_file), "content": "x = 1\n"}}
        )
        final_after_block = json.dumps({"action": "final", "params": {"answer": "done"}})
        fake_provider2 = FakeBrainProvider([write_action, final_after_block])
        brain2 = BrainManager(default_provider="fake_coder", routing={"coding": "fake_coder"})
        brain2.register_provider(fake_provider2)
        skill2 = CoderAgentSkill(
            brain_manager=brain2, sandbox=sandbox, security=security, audit=audit
        )
        intent2 = _make_intent(f"Create {target_file}")
        response2 = skill2.execute(intent2)
        assert not target_file.exists()
        assert response2.data["trace"][0]["observation"].startswith("ERROR")
        print("PASS - write_file requires explicit approval before touching disk")


def test_vento_client_and_skill():
    print("\n[Test 4] VentoClient with mocked aiohttp...")

    boards_payload = [{"id": "board-1", "name": "Living Room"}]

    class MockResponse:
        status = 200
        content_type = "application/json"

        async def json(self):
            return boards_payload

        async def text(self):
            return json.dumps(boards_payload)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    class MockSession:
        def request(self, method, url, headers=None, **kwargs):
            assert "/boards" in url
            return MockResponse()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    client = VentoClient(base_url="http://localhost:3001/api/v1", api_key="test-key")

    with patch("aiohttp.ClientSession", return_value=MockSession()):
        boards = asyncio.run(client.list_boards())

    assert boards == boards_payload
    print("PASS - VentoClient.list_boards() parses inferred /boards endpoint")

    print("\n[Test 5] VentoSkill blocks send_action without approval...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        audit = AuditLogger(path=str(temp_path / "audit.log"))
        security = AuthorizationService(require_explicit_approval=True)
        vento_skill = VentoSkill(vento_client=client, security=security, audit=audit)

        action_intent = Intent(
            intent_type="vento_send_action",
            original_text="Turn on the living room light",
            entities={"board_id": "board-1", "card_id": "light-1", "payload": {"on": True}},
        )
        response = vento_skill.execute(action_intent)
        assert response.success is False
        assert "approve:" in response.text
        print("PASS - vento_send_action requires explicit approval before acting")


def test_runtime_registers_coder_agent():
    print("\n[Test 6] JarvisRuntime registers coder_agent only when OPENROUTER_API_KEY is set...")

    from src.app import initialize_runtime

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_path = temp_path / "config.yaml"
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
      coding: openrouter
  security:
    require_explicit_approval: true
    approval_prefix: "approve:"
    audit_log_file: "{(temp_path / 'audit.log').as_posix()}"
    sandbox:
      allowed_dirs:
        - "{temp_path.as_posix()}"
      timeout: 30
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

        with patch.dict("os.environ", {}, clear=False):
            import os as _os

            _os.environ.pop("OPENROUTER_API_KEY", None)
            _os.environ.pop("VENTO_BASE_URL", None)
            runtime_without_key = initialize_runtime(str(config_path))
            assert "openrouter" not in runtime_without_key.brain.providers
            assert "coder_agent" not in runtime_without_key.core.skill_registry.skills
            print("PASS - coder_agent skipped when OPENROUTER_API_KEY is absent")

            _os.environ["OPENROUTER_API_KEY"] = "sk-test-key"
            runtime_with_key = initialize_runtime(str(config_path))
            assert "openrouter" in runtime_with_key.brain.providers
            assert "coder_agent" in runtime_with_key.core.skill_registry.skills
            print("PASS - coder_agent registered when OPENROUTER_API_KEY is present")
            _os.environ.pop("OPENROUTER_API_KEY", None)


def run_phase13_tests():
    print("\n" + "=" * 70)
    print("PHASE 13 CHECKPOINT TEST - CODER AGENT + VENTO FOUNDATION")
    print("=" * 70)

    test_openrouter_provider_think()
    test_sandbox_executor()
    test_coder_agent_skill()
    test_vento_client_and_skill()
    test_runtime_registers_coder_agent()

    print("\n" + "=" * 70)
    print("PHASE 13 CHECKPOINT - ALL TESTS PASSED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_phase13_tests()
