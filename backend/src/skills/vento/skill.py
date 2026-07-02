"""VentoSkill: exposes VentoClient operations as a Jarvis Skill.

Intents:
- `vento_list_devices`: list boards (read-only, no approval required).
- `vento_read_state`: read a card/device state (read-only, no approval).
- `vento_send_action`: send an action to an actuator (requires explicit
  approval via `AuthorizationService`, since it can control physical
  hardware -- same "approve: <action>" convention used elsewhere).
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from skills.base import Intent, Skill, SkillResponse

from src.security.audit import AuditLogger
from src.security.authorization import AuthorizationService

from .client import VentoClient, VentoClientError

VENTO_INTENT_TYPES = {"vento_list_devices", "vento_read_state", "vento_send_action"}
VENTO_KEYWORDS = [
    "vento", "list boards", "listar boards", "list devices", "listar dispositivos",
    "read sensor", "leer sensor", "send action", "enviar accion", "enviar acción",
]


class VentoSkill(Skill):
    def __init__(
        self,
        vento_client: VentoClient,
        security: AuthorizationService,
        audit: AuditLogger,
    ):
        super().__init__("vento", "Integration with the Vento AI control network platform")
        self.client = vento_client
        self.security = security
        self.audit = audit
        self.keywords = VENTO_KEYWORDS
        self.example_intents = [
            "List Vento boards",
            "Read sensor state on board X",
            "Send action to actuator Y",
        ]

    def can_handle(self, intent: Intent) -> bool:
        if intent.intent_type in VENTO_INTENT_TYPES:
            return True
        normalized = intent.original_text.lower()
        return any(keyword in normalized for keyword in self.keywords)

    def execute(self, intent: Intent) -> SkillResponse:
        try:
            if intent.intent_type == "vento_read_state":
                return asyncio.run(self._read_state(intent))
            if intent.intent_type == "vento_send_action":
                return asyncio.run(self._send_action(intent))
            return asyncio.run(self._list_devices())
        except VentoClientError as exc:
            return SkillResponse(str(exc), success=False)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("VentoSkill failed")
            return SkillResponse(f"Vento skill failed: {exc}", success=False)

    async def _list_devices(self) -> SkillResponse:
        boards = await self.client.list_boards()
        self.audit.record("vento_list_devices", {"count": len(boards)})
        names = ", ".join(str(b.get("name", b.get("id", "?"))) for b in boards) or "none"
        return SkillResponse(f"Vento boards: {names}", data={"boards": boards})

    async def _read_state(self, intent: Intent) -> SkillResponse:
        board_id = intent.entities.get("board_id") or intent.parameters.get("board_id")
        card_id = intent.entities.get("card_id") or intent.parameters.get("card_id")
        if not board_id or not card_id:
            return SkillResponse(
                "vento_read_state requires 'board_id' and 'card_id' entities.", success=False
            )
        state = await self.client.read_state(board_id, card_id)
        self.audit.record("vento_state_read", {"board_id": board_id, "card_id": card_id})
        return SkillResponse(f"State for {board_id}/{card_id}: {state}", data={"state": state})

    async def _send_action(self, intent: Intent) -> SkillResponse:
        board_id = intent.entities.get("board_id") or intent.parameters.get("board_id")
        card_id = intent.entities.get("card_id") or intent.parameters.get("card_id")
        payload: Dict[str, Any] = intent.entities.get("payload") or intent.parameters.get("payload") or {}
        approval_text = intent.entities.get("approval_text") or intent.parameters.get("approval_text")

        if not board_id or not card_id:
            return SkillResponse(
                "vento_send_action requires 'board_id' and 'card_id' entities.", success=False
            )

        action = f"vento_send_action:{board_id}:{card_id}"
        decision = self.security.check(action, approval_text)
        if not decision.allowed:
            return SkillResponse(
                f"Sending an action to a physical actuator requires explicit approval. "
                f"Reply with: 'approve: {action}'",
                success=False,
                data={"approval_required": True, "action": action},
            )

        result = await self.client.send_action(board_id, card_id, payload)
        self.audit.record(
            "vento_action_sent", {"board_id": board_id, "card_id": card_id, "payload": payload}
        )
        return SkillResponse(f"Action sent to {board_id}/{card_id}: {result}", data={"result": result})
