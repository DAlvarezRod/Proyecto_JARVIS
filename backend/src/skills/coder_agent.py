"""CoderAgentSkill: an LLM-driven coding agent exposed as a Jarvis Skill.

The skill runs a small ReAct-style loop: it asks the configured
`BrainManager` (task_type="coding") for a single JSON action per turn, executes
that action against a restricted toolset (read/write/list files, run shell
commands through `SandboxExecutor`), feeds the result back, and repeats until
the model returns a `final` action or `max_steps` is reached.

All side effects go through `SandboxExecutor`, which enforces the allowed
working directories and the safe/destructive/unknown command classification,
and every tool call is recorded through `AuditLogger`.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from skills.base import Intent, Skill, SkillResponse

from src.brain.manager import BrainManager
from src.security.audit import AuditLogger
from src.security.authorization import AuthorizationService
from src.security.sandbox import SandboxExecutor, SandboxViolation

SYSTEM_PROMPT = """You are the coding agent inside the JARVIS system.
You solve programming tasks by taking ONE action per turn.

Respond with EXACTLY one JSON object, no prose, no markdown fences:
{"action": "read_file", "params": {"path": "..."}}
{"action": "write_file", "params": {"path": "...", "content": "..."}}
{"action": "list_files", "params": {"path": "..."}}
{"action": "run_command", "params": {"cmd": "...", "cwd": "..."}}
{"action": "final", "params": {"answer": "..."}}

Rules:
- Use "final" as soon as you have enough information to answer or once the
  requested change/task is complete.
- Only touch files/directories relevant to the task.
- Keep "answer" concise and written for the end user.
"""

CODER_INTENT_TYPES = {"coder_generate", "coder_read", "coder_modify", "coder_run"}
CODER_KEYWORDS = [
    "write code", "generate code", "generar código", "generar codigo",
    "modifica el archivo", "modifica el codigo", "modify the file",
    "run the tests", "corre los tests", "ejecuta el comando",
    "refactor", "fix the bug", "arregla el bug",
]


class CoderAgentSkill(Skill):
    def __init__(
        self,
        brain_manager: BrainManager,
        sandbox: SandboxExecutor,
        security: AuthorizationService,
        audit: AuditLogger,
        max_steps: int = 8,
        task_type: str = "coding",
    ):
        super().__init__("coder_agent", "LLM-driven coding agent (generate/read/modify/run)")
        self.brain_manager = brain_manager
        self.sandbox = sandbox
        self.security = security
        self.audit = audit
        self.max_steps = max_steps
        self.task_type = task_type
        self.keywords = CODER_KEYWORDS
        self.example_intents = [
            "Write a function to parse CSV files",
            "Modifica backend/skills/weather.py para agregar cache",
            "Run the tests in backend/test_phase1.py",
        ]

    def can_handle(self, intent: Intent) -> bool:
        if intent.intent_type in CODER_INTENT_TYPES:
            return True
        normalized = intent.original_text.lower()
        return any(keyword in normalized for keyword in self.keywords)

    def execute(self, intent: Intent) -> SkillResponse:
        approval_text = intent.entities.get("approval_text") or intent.parameters.get("approval_text")
        try:
            return asyncio.run(self._run_agent_loop(intent.original_text, approval_text))
        except SandboxViolation as exc:
            return SkillResponse(f"Action blocked by sandbox policy: {exc}", success=False)
        except Exception as exc:  # noqa: BLE001 - surface agent failures to the user
            self.logger.exception("CoderAgentSkill failed")
            return SkillResponse(f"Coder agent failed: {exc}", success=False)

    async def _run_agent_loop(self, task: str, approval_text: Optional[str]) -> SkillResponse:
        history: List[Dict[str, str]] = []
        trace: List[Dict[str, Any]] = []
        prompt = task

        for step in range(self.max_steps):
            context = {
                "task_type": self.task_type,
                "system_prompt": SYSTEM_PROMPT,
                "history": history,
            }
            provider = self.brain_manager.resolve_provider(task_type=self.task_type)
            raw_response = await provider.think(prompt, context=context)

            action = self._parse_action(raw_response)
            if action is None:
                return SkillResponse(
                    f"Coder agent produced an unparseable response: {raw_response[:300]}",
                    success=False,
                    data={"trace": trace},
                )

            history.append({"role": "assistant", "content": raw_response})

            action_name = action.get("action")
            params = action.get("params", {})

            if action_name == "final":
                answer = params.get("answer", "")
                self.audit.record("coder_agent_final", {"task": task, "steps": step + 1})
                return SkillResponse(answer or "Done.", data={"trace": trace})

            try:
                observation = await self._execute_tool(action_name, params, approval_text)
            except SandboxViolation as exc:
                observation = f"ERROR: {exc}"

            trace.append({"action": action_name, "params": params, "observation": observation})
            history.append({"role": "user", "content": f"Observation: {observation}"})
            prompt = "Continue with the next action given the observation above."

        return SkillResponse(
            "Coder agent stopped: reached max_steps without a final answer.",
            success=False,
            data={"trace": trace},
        )

    def _parse_action(self, raw_response: str) -> Optional[Dict[str, Any]]:
        text = raw_response.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                return None
        return None

    async def _execute_tool(
        self, action_name: str, params: Dict[str, Any], approval_text: Optional[str]
    ) -> str:
        if action_name == "read_file":
            return self._read_file(params.get("path", ""))
        if action_name == "write_file":
            return self._write_file(params.get("path", ""), params.get("content", ""), approval_text)
        if action_name == "list_files":
            return self._list_files(params.get("path", "."))
        if action_name == "run_command":
            result = await self.sandbox.run(
                command=params.get("cmd", ""),
                cwd=params.get("cwd", "."),
                approval_text=approval_text,
            )
            return (
                f"exit_code={result.return_code} timed_out={result.timed_out}\n"
                f"stdout:\n{result.stdout[-2000:]}\nstderr:\n{result.stderr[-2000:]}"
            )
        raise SandboxViolation(f"Unknown action '{action_name}'")

    def _read_file(self, path: str) -> str:
        if not self.sandbox.is_path_allowed(path):
            raise SandboxViolation(f"Path '{path}' is outside the allowed directories")
        file_path = Path(path)
        if not file_path.is_file():
            return f"ERROR: file not found: {path}"
        content = file_path.read_text(encoding="utf-8", errors="replace")
        self.audit.record("coder_agent_read_file", {"path": path})
        return content[:8000]

    def _write_file(self, path: str, content: str, approval_text: Optional[str]) -> str:
        if not self.sandbox.is_path_allowed(path):
            raise SandboxViolation(f"Path '{path}' is outside the allowed directories")
        action = f"write_file: {path}"
        decision = self.security.check(action, approval_text)
        if not decision.allowed:
            raise SandboxViolation(
                f"Writing to '{path}' requires explicit approval. Reply with: 'approve: {action}'"
            )
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        self.audit.record("coder_agent_write_file", {"path": path, "bytes": len(content)})
        return f"OK: wrote {len(content)} bytes to {path}"

    def _list_files(self, path: str) -> str:
        if not self.sandbox.is_path_allowed(path):
            raise SandboxViolation(f"Path '{path}' is outside the allowed directories")
        dir_path = Path(path)
        if not dir_path.is_dir():
            return f"ERROR: not a directory: {path}"
        entries = sorted(p.name + ("/" if p.is_dir() else "") for p in dir_path.iterdir())
        self.audit.record("coder_agent_list_files", {"path": path, "count": len(entries)})
        return "\n".join(entries[:200])
