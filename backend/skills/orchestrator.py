"""Safe personal assistant orchestrator skill."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from skills.base import Intent, Skill, SkillResponse


@dataclass
class MockAccountTask:
    title: str
    status: str
    next_step: str


class MockAccountAdapter:
    """Local adapter for account-task visibility (no privileged execution)."""

    def get_account_tasks(self) -> List[MockAccountTask]:
        return [
            MockAccountTask("Review login alerts", "pending", "Open account security page and review unknown locations."),
            MockAccountTask("Enable MFA where missing", "in_progress", "Turn on app-based MFA for remaining services."),
            MockAccountTask("Backup recovery codes", "pending", "Store recovery codes in your password manager."),
        ]


class MockPeripheralAdapter:
    """Local adapter for peripheral checks."""

    def run_health_check(self) -> List[Dict[str, str]]:
        return [
            {"device": "USB Headset", "status": "connected", "next_step": "Run a short microphone test."},
            {"device": "Bluetooth Keyboard", "status": "low_battery", "next_step": "Charge in the next 2 hours."},
            {"device": "Webcam", "status": "connected", "next_step": "Verify privacy shutter is open when needed."},
        ]


class MockPhoneAdapter:
    """Local adapter for phone planning artifacts."""

    def __init__(self):
        self._drafts: List[Dict[str, Any]] = []

    def create_action_draft(self, request_text: str) -> Dict[str, Any]:
        draft = {
            "draft_id": f"phone-draft-{len(self._drafts) + 1}",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "summary": "Prepared a mobile action checklist (local draft only).",
            "request": request_text,
            "next_steps": [
                "Review contact and message content on your phone.",
                "Confirm recipient and timing before sending anything.",
                "Execute manually after explicit approval.",
            ],
        }
        self._drafts.append(draft)
        return draft


class PersonalAssistantOrchestratorSkill(Skill):
    def __init__(
        self,
        enabled: bool = True,
        require_explicit_approval: bool = True,
        privileged_keywords: List[str] | None = None,
        disclose_limitations: bool = True,
    ):
        super().__init__("orchestrator", "Safe orchestration for account/peripheral/phone task planning")
        self.enabled = enabled
        self.require_explicit_approval = require_explicit_approval
        self.privileged_keywords = [word.lower() for word in (privileged_keywords or [])]
        self.disclose_limitations = disclose_limitations
        self.account_adapter = MockAccountAdapter()
        self.peripheral_adapter = MockPeripheralAdapter()
        self.phone_adapter = MockPhoneAdapter()
        self.keywords = [
            "manage account",
            "check account tasks",
            "manage peripherals",
            "manage phone",
            "phone tasks",
        ]
        self.example_intents = [
            "Manage account tasks",
            "Check account tasks",
            "Manage peripherals",
            "Manage phone",
        ]

    def can_handle(self, intent: Intent) -> bool:
        if intent.intent_type in {
            "orchestrator_accounts",
            "orchestrator_peripherals",
            "orchestrator_phone",
        }:
            return True
        normalized = intent.original_text.lower()
        return any(keyword in normalized for keyword in self.keywords)

    def execute(self, intent: Intent) -> SkillResponse:
        if not self.enabled:
            return SkillResponse("Personal orchestrator is disabled by configuration.", success=False)

        normalized = intent.original_text.lower()
        domain = self._resolve_domain(intent.intent_type, normalized)
        if not domain:
            return SkillResponse(
                self._limitations_text("I can help with account, peripheral, or phone orchestration only."),
                success=False,
            )

        if self.require_explicit_approval and self._is_privileged_request(normalized):
            next_step = self._approval_prompt(domain)
            return SkillResponse(
                self._limitations_text(
                    f"I prepared a plan for {domain}, but this action is privileged and I will not execute it automatically. {next_step}"
                ),
                data={"domain": domain, "approval_required": True, "next_step": next_step},
            )

        if domain == "accounts":
            tasks = self.account_adapter.get_account_tasks()
            headline = "Account task check complete."
            detail = " ".join([f"- {task.title} ({task.status}): {task.next_step}" for task in tasks])
            next_step = "Tell me which account task you want to prioritize and I will break it into steps."
            return SkillResponse(
                self._limitations_text(f"{headline} {detail} Next step: {next_step}"),
                data={"domain": domain, "tasks": [task.__dict__ for task in tasks], "approval_required": False},
            )

        if domain == "peripherals":
            devices = self.peripheral_adapter.run_health_check()
            detail = " ".join([f"- {item['device']}: {item['status']} ({item['next_step']})" for item in devices])
            next_step = "Confirm if you want a guided checklist for any specific peripheral."
            return SkillResponse(
                self._limitations_text(f"Peripheral check complete. {detail} Next step: {next_step}"),
                data={"domain": domain, "devices": devices, "approval_required": False},
            )

        draft = self.phone_adapter.create_action_draft(intent.original_text)
        return SkillResponse(
            self._limitations_text(
                f"Phone planning draft created ({draft['draft_id']}). {draft['summary']} Next step: review and explicitly approve before any send/call action."
            ),
            data={"domain": "phone", "draft": draft, "approval_required": False},
        )

    def _resolve_domain(self, intent_type: str, normalized_text: str) -> str:
        if intent_type == "orchestrator_accounts" or "account" in normalized_text:
            return "accounts"
        if intent_type == "orchestrator_peripherals" or "peripheral" in normalized_text:
            return "peripherals"
        if intent_type == "orchestrator_phone" or "phone" in normalized_text or "mobile" in normalized_text:
            return "phone"
        return ""

    def _is_privileged_request(self, normalized_text: str) -> bool:
        return any(keyword in normalized_text for keyword in self.privileged_keywords)

    def _approval_prompt(self, domain: str) -> str:
        return (
            f"If you want to continue with {domain}, reply with an explicit approval like: "
            f"'Approve orchestrator {domain} action: <exact action>'."
        )

    def _limitations_text(self, message: str) -> str:
        if not self.disclose_limitations:
            return message
        return (
            f"{message} Limitation: I provide local planning/checks and cannot autonomously control all accounts or devices."
        )
