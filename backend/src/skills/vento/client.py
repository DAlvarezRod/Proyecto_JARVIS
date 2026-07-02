"""Async client for the Vento platform (https://vento.build).

IMPORTANT — inference disclaimer
---------------------------------
There is no public official REST API documentation for Vento. This client was
built by inspecting the open-source monorepo `Protofy-xyz/Vento` (branch
`ai_assistants`) on GitHub:

- `apps/api` mounts an Express server with `global.defaultRoute = '/api/v1'`
  and auto-generates CRUD routes per "bundle" object (`packages/app/bundles`),
  which is why boards/cards are assumed reachable under `/api/v1/boards`.
- `apps/core/src/mqtt.ts` starts an Aedes MQTT broker on TCP port 1883 and a
  WebSocket transport on port 3003.

None of the exact paths, payload shapes, or auth scheme could be confirmed
without access to a running instance or official docs. Every path and the
auth scheme are therefore fully configurable, and every method raises
`VentoClientError` with a message reminding the caller to verify against a
real deployment. Treat this as a foundation to validate/adjust once real
credentials or docs are available, not as a verified integration.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import aiohttp

from logger import get_logger

DEFAULT_BASE_URL = "http://localhost:3001/api/v1"
DEFAULT_BOARDS_PATH = "/boards"
DEFAULT_BOARD_DETAIL_PATH = "/boards/{board_id}"
DEFAULT_ACTION_PATH = "/boards/{board_id}/actions/{card_id}"
DEFAULT_STATE_PATH = "/boards/{board_id}/cards/{card_id}"
DEFAULT_MQTT_HOST = "localhost"
DEFAULT_MQTT_PORT = 1883


class VentoClientError(RuntimeError):
    """Raised when the Vento API cannot be reached or returns an error.

    Message always hints that the endpoint may not match the real API since
    it was inferred from source code, not verified documentation.
    """


class VentoClient:
    """Thin async wrapper around the (inferred) Vento REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        auth_header: str = "Authorization",
        auth_scheme: str = "Bearer",
        boards_path: str = DEFAULT_BOARDS_PATH,
        board_detail_path: str = DEFAULT_BOARD_DETAIL_PATH,
        action_path: str = DEFAULT_ACTION_PATH,
        state_path: str = DEFAULT_STATE_PATH,
        timeout: float = 15.0,
    ):
        self.logger = get_logger("src.skills.vento.client")
        self.base_url = (base_url or os.getenv("VENTO_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.api_key = api_key or os.getenv("VENTO_API_KEY")
        self.auth_header = auth_header
        self.auth_scheme = auth_scheme
        self.boards_path = boards_path
        self.board_detail_path = board_detail_path
        self.action_path = action_path
        self.state_path = state_path
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "VentoClient":
        return cls(
            base_url=os.getenv("VENTO_BASE_URL", DEFAULT_BASE_URL),
            api_key=os.getenv("VENTO_API_KEY"),
        )

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            value = f"{self.auth_scheme} {self.api_key}".strip()
            headers[self.auth_header] = value
        return headers

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(method, url, headers=self._headers(), **kwargs) as response:
                    text = await response.text()
                    if response.status >= 400:
                        raise VentoClientError(
                            f"Vento API returned HTTP {response.status} for {method} {url}: {text}. "
                            "This endpoint is inferred from source code and was not verified against "
                            "a real Vento instance -- check paths/auth before trusting this error."
                        )
                    if response.content_type == "application/json":
                        return await response.json()
                    return text
        except aiohttp.ClientError as exc:
            raise VentoClientError(
                f"Could not reach Vento API at {url}: {exc}. Verify VENTO_BASE_URL "
                "and network connectivity against a real Vento instance."
            ) from exc

    async def list_boards(self) -> List[Dict[str, Any]]:
        """List available boards. Path inferred as `/boards` -- verify against a real instance."""
        result = await self._request("GET", self.boards_path)
        return result if isinstance(result, list) else result.get("data", [])

    async def get_board(self, board_id: str) -> Dict[str, Any]:
        """Get a single board's definition. Path inferred -- verify against a real instance."""
        path = self.board_detail_path.format(board_id=board_id)
        return await self._request("GET", path)

    async def read_state(self, board_id: str, card_id: str) -> Any:
        """Read a card/device's current state. Path inferred -- verify against a real instance."""
        path = self.state_path.format(board_id=board_id, card_id=card_id)
        return await self._request("GET", path)

    async def send_action(self, board_id: str, card_id: str, payload: Dict[str, Any]) -> Any:
        """Send an action/command to an actuator. Path inferred -- verify against a real instance."""
        path = self.action_path.format(board_id=board_id, card_id=card_id)
        return await self._request("POST", path, json=payload)

    async def subscribe_mqtt(self, topic: str, callback) -> None:
        """Subscribe to a Vento MQTT topic (best-effort, optional dependency).

        Vento's core service (`apps/core/src/mqtt.ts`) runs an Aedes broker,
        default TCP port 1883. This uses `paho-mqtt` only if installed; the
        topic layout is NOT confirmed and must be validated against a real
        deployment.
        """
        try:
            import paho.mqtt.client as mqtt  # type: ignore
        except ImportError as exc:
            raise NotImplementedError(
                "MQTT subscription requires the optional 'paho-mqtt' package "
                "(not in requirements.txt). Install it to use subscribe_mqtt()."
            ) from exc

        host = os.getenv("VENTO_MQTT_HOST", DEFAULT_MQTT_HOST)
        port = int(os.getenv("VENTO_MQTT_PORT", str(DEFAULT_MQTT_PORT)))

        client = mqtt.Client()

        def _on_message(_client, _userdata, message):
            callback(message.topic, message.payload)

        client.on_message = _on_message
        client.connect(host, port)
        client.subscribe(topic)
        client.loop_start()
