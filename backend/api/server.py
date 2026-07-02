"""Flask/Socket.IO API for JARVIS."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core import initialize_jarvis
from logger import get_logger
from system_startup import StartupManager

logger = get_logger("api.server")


def create_app(
    config_path: str = "config.yaml",
    startup_manager: StartupManager | None = None,
) -> tuple[Flask, SocketIO]:
    """Create the Flask app and Socket.IO server."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "jarvis-dev"
    CORS(app, resources={r"/*": {"origins": "*"}})
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
    jarvis = initialize_jarvis(config_path)
    startup_manager = startup_manager or StartupManager(backend_dir=BACKEND_DIR)

    def device_payload() -> list[Dict[str, Any]]:
        return jarvis.smart_home.list_devices()

    def emit_state() -> None:
        socketio.emit("devices:update", device_payload())
        socketio.emit("status:update", jarvis.get_status())

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "status": jarvis.get_status()})

    @app.get("/api/status")
    def status():
        return jsonify(jarvis.get_status())

    @app.get("/api/skills")
    def skills():
        return jsonify({
            "skills": jarvis.skill_registry.list_skills(),
            "custom_manifests": jarvis.custom_skill_loader.discover(),
            "status": jarvis.get_status(),
        })

    @app.post("/api/skills/reload")
    def reload_skills():
        loaded = jarvis.reload_custom_skills()
        emit_state()
        return jsonify({
            "loaded": loaded,
            "skills": jarvis.skill_registry.list_skills(),
            "status": jarvis.get_status(),
        })

    @app.get("/api/devices")
    def devices():
        return jsonify(device_payload())

    @app.post("/api/chat")
    def chat():
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("message", "")).strip()
        if not text:
            return jsonify({"error": "message is required"}), 400
        response = asyncio.run(jarvis.process_user_input(text))
        result = {
            "message": text,
            "response": response,
            "history": jarvis.get_conversation_history(limit=20),
            "status": jarvis.get_status(),
            "devices": device_payload(),
        }
        emit_state()
        socketio.emit("chat:message", result)
        return jsonify(result)

    @app.post("/api/devices/command")
    def device_command():
        payload = request.get_json(silent=True) or {}
        action = payload.get("action")
        if not action:
            return jsonify({"error": "action is required"}), 400
        result = jarvis.execute_smart_home_command(
            action=str(action),
            device_id=payload.get("device_id"),
            device_type=payload.get("device_type"),
            location=payload.get("location"),
            value=payload.get("value"),
        )
        emit_state()
        return jsonify({"result": result, "devices": device_payload()})

    @app.get("/api/automations")
    def list_automations():
        return jsonify({
            "rules": jarvis.automation.list_rules(),
            "status": jarvis.automation.get_status(),
        })

    @app.post("/api/automations")
    def create_automation():
        payload = request.get_json(silent=True) or {}
        if not payload.get("name") or not payload.get("trigger") or not payload.get("action"):
            return jsonify({"error": "name, trigger, and action are required"}), 400
        rule = jarvis.automation.add_rule(payload)
        emit_state()
        return jsonify({"rule": rule, "status": jarvis.automation.get_status()}), 201

    @app.patch("/api/automations/<rule_id>")
    def update_automation(rule_id):
        payload = request.get_json(silent=True) or {}
        rule = jarvis.automation.update_rule(rule_id, payload)
        if not rule:
            return jsonify({"error": "automation rule not found"}), 404
        emit_state()
        return jsonify({"rule": rule, "status": jarvis.automation.get_status()})

    @app.delete("/api/automations/<rule_id>")
    def delete_automation(rule_id):
        if not jarvis.automation.remove_rule(rule_id):
            return jsonify({"error": "automation rule not found"}), 404
        emit_state()
        return jsonify({"ok": True, "status": jarvis.automation.get_status()})

    @app.post("/api/automations/run-pending")
    def run_pending_automations():
        executions = jarvis.automation.run_pending()
        emit_state()
        return jsonify({
            "executions": executions,
            "status": jarvis.automation.get_status(),
            "devices": device_payload(),
        })

    @app.get("/api/history")
    def history():
        limit = request.args.get("limit", default=20, type=int)
        return jsonify(jarvis.get_conversation_history(limit=limit))

    @app.delete("/api/history")
    def clear_history():
        jarvis.clear_conversation_history()
        emit_state()
        socketio.emit("history:update", [])
        return jsonify({"ok": True, "history": []})

    @app.get("/api/memory")
    def memory():
        limit = request.args.get("limit", default=20, type=int)
        return jsonify({
            "count": jarvis.memory.count(),
            "messages": jarvis.memory.get_recent(limit=limit),
        })

    @app.get("/api/integration-check")
    def integration_check():
        skills = jarvis.skill_registry.list_skills()
        status_payload = jarvis.get_status()
        devices_payload = device_payload()
        checks = {
            "core": status_payload["status"] == "running",
            "skills": len(skills) >= 6,
            "smart_home": len(devices_payload) >= 1,
            "memory": jarvis.memory.count() >= len(jarvis.get_conversation_history()),
            "performance": "average_response_ms" in status_payload["performance"],
            "automation": "rules" in status_payload["automation"],
        }
        return jsonify({
            "ok": all(checks.values()),
            "checks": checks,
            "status": status_payload,
            "skills": list(skills.keys()),
            "devices": len(devices_payload),
        })

    def startup_http_code(payload: Dict[str, Any]) -> int:
        if payload.get("success"):
            return 200
        error_code = ((payload.get("error") or {}).get("code") or "").strip()
        if error_code == "not-supported":
            return 501
        if error_code == "startup-entry-conflict":
            return 409
        return 500

    @app.get("/api/system/startup")
    def startup_status():
        payload = startup_manager.status()
        return jsonify(payload), startup_http_code(payload)

    @app.post("/api/system/startup/enable")
    def startup_enable():
        payload = startup_manager.enable()
        return jsonify(payload), startup_http_code(payload)

    @app.post("/api/system/startup/disable")
    def startup_disable():
        payload = startup_manager.disable()
        return jsonify(payload), startup_http_code(payload)

    @socketio.on("connect")
    def on_connect():
        emit("status:update", jarvis.get_status())
        emit("devices:update", device_payload())
        emit("history:update", jarvis.get_conversation_history(limit=20))

    @socketio.on("chat:send")
    def on_chat_send(payload):
        text = str((payload or {}).get("message", "")).strip()
        if not text:
            emit("chat:error", {"error": "message is required"})
            return
        response = asyncio.run(jarvis.process_user_input(text))
        result = {
            "message": text,
            "response": response,
            "history": jarvis.get_conversation_history(limit=20),
            "status": jarvis.get_status(),
            "devices": device_payload(),
        }
        emit("chat:message", result)
        socketio.emit("devices:update", result["devices"])
        socketio.emit("status:update", result["status"])

    return app, socketio


app, socketio = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )
