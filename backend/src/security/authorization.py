"""Centralized authorization checks for high-impact actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthorizationDecision:
    allowed: bool
    reason: str


class AuthorizationService:
    """Minimal policy engine for approval-gated operations."""

    def __init__(
        self,
        require_explicit_approval: bool = True,
        approval_prefix: str = "approve:",
    ):
        self.require_explicit_approval = require_explicit_approval
        self.approval_prefix = approval_prefix.lower().strip()

    def check(self, action: str, approval_text: Optional[str] = None) -> AuthorizationDecision:
        if not self.require_explicit_approval:
            return AuthorizationDecision(allowed=True, reason="approval-not-required")
        if not approval_text:
            return AuthorizationDecision(
                allowed=False,
                reason="missing-explicit-approval",
            )
        normalized = approval_text.lower().strip()
        expected = f"{self.approval_prefix} {action.lower().strip()}"
        if normalized == expected:
            return AuthorizationDecision(allowed=True, reason="approval-validated")
        return AuthorizationDecision(allowed=False, reason="approval-mismatch")

