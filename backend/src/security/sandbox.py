"""Sandboxed command execution for agentic skills (e.g. the coder agent).

Design goals (confirmed requirements):
- `cwd` is restricted to a configurable allow-list of directories.
- Commands are classified as safe / destructive / unknown via patterns.
- Only destructive/unknown commands require explicit approval
  (`AuthorizationService`, same "approve: <action>" convention already used
  by `skills/orchestrator.py`).
- Execution never touches the user's interactive shell: it always spawns an
  isolated subprocess via `asyncio.create_subprocess_exec` (`shell=False`).
- Every invocation is recorded through `AuditLogger`.
"""

from __future__ import annotations

import asyncio
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional

from logger import get_logger

from .audit import AuditLogger
from .authorization import AuthorizationService

CommandClass = Literal["safe", "destructive", "unknown"]

DEFAULT_ALLOWED_DIRS = ["C:\\Proyectos"]

DEFAULT_SAFE_PREFIXES = [
    "python", "python3", "py",
    "pip", "pip3",
    "pytest",
    "git status", "git diff", "git log", "git show", "git branch",
    "npm test", "npm run", "npm install", "npm ci",
    "node",
    "dir", "ls", "type", "cat",
    "echo",
]

DEFAULT_DESTRUCTIVE_PATTERNS = [
    "rm -rf", "rm -r", "rmdir /s", "del /s", "del /f",
    "format ", "mkfs", "dd if=", "dd of=",
    "shutdown", "restart-computer",
    ">:", "diskpart",
    "git push --force", "git reset --hard",
    ":(){:|:&};:",
]


class SandboxViolation(RuntimeError):
    """Raised when a command/cwd is rejected before execution."""


@dataclass
class SandboxResult:
    command: str
    cwd: str
    classification: CommandClass
    approved: bool
    return_code: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool = False


class SandboxExecutor:
    """Runs shell commands in an isolated subprocess with guardrails."""

    def __init__(
        self,
        allowed_dirs: Optional[List[str]] = None,
        safe_prefixes: Optional[List[str]] = None,
        destructive_patterns: Optional[List[str]] = None,
        default_timeout: int = 60,
        security: Optional[AuthorizationService] = None,
        audit: Optional[AuditLogger] = None,
    ):
        self.logger = get_logger("src.security.sandbox")
        raw_dirs = allowed_dirs if allowed_dirs is not None else DEFAULT_ALLOWED_DIRS
        self.allowed_dirs = [Path(d).resolve() for d in raw_dirs if d]
        self.safe_prefixes = [p.lower() for p in (safe_prefixes or DEFAULT_SAFE_PREFIXES)]
        self.destructive_patterns = [
            p.lower() for p in (destructive_patterns or DEFAULT_DESTRUCTIVE_PATTERNS)
        ]
        self.default_timeout = default_timeout
        self.security = security or AuthorizationService()
        self.audit = audit

    @classmethod
    def from_env(
        cls,
        env_var: str = "AGENT_ALLOWED_DIRS",
        default_timeout: int = 60,
        security: Optional[AuthorizationService] = None,
        audit: Optional[AuditLogger] = None,
    ) -> "SandboxExecutor":
        raw = os.getenv(env_var, "")
        dirs = [d.strip() for d in raw.split(",") if d.strip()] or DEFAULT_ALLOWED_DIRS
        return cls(
            allowed_dirs=dirs,
            default_timeout=default_timeout,
            security=security,
            audit=audit,
        )

    def is_path_allowed(self, path: str) -> bool:
        try:
            resolved = Path(path).resolve()
        except OSError:
            return False
        return any(
            resolved == allowed or allowed in resolved.parents
            for allowed in self.allowed_dirs
        )

    def classify_command(self, command: str) -> CommandClass:
        normalized = command.strip().lower()
        if any(pattern in normalized for pattern in self.destructive_patterns):
            return "destructive"
        if any(normalized.startswith(prefix) for prefix in self.safe_prefixes):
            return "safe"
        return "unknown"

    async def run(
        self,
        command: str,
        cwd: str,
        approval_text: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> SandboxResult:
        if not self.is_path_allowed(cwd):
            self._audit("sandbox_rejected", command, cwd, reason="cwd-not-allowed")
            raise SandboxViolation(
                f"Working directory '{cwd}' is outside the allowed directories: "
                f"{[str(d) for d in self.allowed_dirs]}"
            )

        classification = self.classify_command(command)
        approved = classification == "safe"
        if not approved:
            action = f"run_command: {command}"
            decision = self.security.check(action, approval_text)
            if not decision.allowed:
                self._audit(
                    "sandbox_rejected",
                    command,
                    cwd,
                    reason=f"{classification}-not-approved:{decision.reason}",
                )
                raise SandboxViolation(
                    f"Command classified as '{classification}' requires explicit approval. "
                    f"Reply with: 'approve: {action}'"
                )
            approved = True

        try:
            argv = shlex.split(command, posix=False)
        except ValueError as exc:
            raise SandboxViolation(f"Could not parse command: {exc}") from exc
        if not argv:
            raise SandboxViolation("Empty command")

        effective_timeout = timeout or self.default_timeout
        timed_out = False
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=effective_timeout
                )
            except asyncio.TimeoutError:
                timed_out = True
                process.kill()
                stdout_bytes, stderr_bytes = await process.communicate()
        except (OSError, FileNotFoundError) as exc:
            self._audit("sandbox_error", command, cwd, reason=str(exc))
            raise SandboxViolation(f"Failed to execute command: {exc}") from exc

        result = SandboxResult(
            command=command,
            cwd=cwd,
            classification=classification,
            approved=approved,
            return_code=process.returncode,
            stdout=stdout_bytes.decode(errors="replace"),
            stderr=stderr_bytes.decode(errors="replace"),
            timed_out=timed_out,
        )
        self._audit(
            "sandbox_command",
            command,
            cwd,
            classification=classification,
            approved=approved,
            return_code=result.return_code,
            timed_out=timed_out,
        )
        return result

    def _audit(self, event_type: str, command: str, cwd: str, **extra) -> None:
        if not self.audit:
            return
        payload = {"command": command, "cwd": cwd}
        payload.update(extra)
        self.audit.record(event_type, payload)
