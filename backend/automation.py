"""Automation rules and background task runner for JARVIS."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from logger import get_logger


def _now() -> datetime:
    return datetime.now()


@dataclass
class AutomationRule:
    name: str
    trigger: Dict[str, Any]
    action: Dict[str, Any]
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    cooldown_seconds: float = 0
    last_triggered: Optional[str] = None
    run_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationRule":
        return cls(
            rule_id=str(data.get("rule_id") or data.get("id") or uuid.uuid4()),
            name=str(data.get("name", "Automation")),
            enabled=bool(data.get("enabled", True)),
            trigger=dict(data.get("trigger", {})),
            action=dict(data.get("action", {})),
            cooldown_seconds=float(data.get("cooldown_seconds", 0)),
            last_triggered=data.get("last_triggered"),
            run_count=int(data.get("run_count", 0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "enabled": self.enabled,
            "trigger": self.trigger,
            "action": self.action,
            "cooldown_seconds": self.cooldown_seconds,
            "last_triggered": self.last_triggered,
            "run_count": self.run_count,
        }


class AutomationManager:
    """Persist, evaluate, and run automation rules."""

    def __init__(
        self,
        rules_file: str = "data/automations.json",
        action_executor: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        poll_interval: float = 1.0,
    ):
        self.path = Path(rules_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.action_executor = action_executor
        self.poll_interval = poll_interval
        self.logger = get_logger("automation")
        self.rules: Dict[str, AutomationRule] = {}
        self.executions: List[Dict[str, Any]] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.rules = {}
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        rules = [AutomationRule.from_dict(item) for item in payload.get("rules", [])]
        self.rules = {rule.rule_id: rule for rule in rules}

    def save(self) -> None:
        payload = {"rules": [rule.to_dict() for rule in self.rules.values()]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        rule = AutomationRule.from_dict(data)
        self.rules[rule.rule_id] = rule
        self.save()
        return rule.to_dict()

    def update_rule(self, rule_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        rule = self.rules.get(rule_id)
        if not rule:
            return None
        merged = rule.to_dict()
        merged.update(data)
        self.rules[rule_id] = AutomationRule.from_dict(merged)
        self.save()
        return self.rules[rule_id].to_dict()

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id not in self.rules:
            return False
        del self.rules[rule_id]
        self.save()
        return True

    def list_rules(self) -> List[Dict[str, Any]]:
        return [rule.to_dict() for rule in self.rules.values()]

    def evaluate_device_event(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        executions: List[Dict[str, Any]] = []
        for rule in self.rules.values():
            if not rule.enabled or rule.trigger.get("type") != "device_state":
                continue
            for device in devices:
                if self._device_matches(rule.trigger, device) and self._ready(rule):
                    executions.append(self._execute(rule, {"device": device}))
                    break
        if executions:
            self.save()
        return executions

    def run_pending(self) -> List[Dict[str, Any]]:
        executions: List[Dict[str, Any]] = []
        for rule in self.rules.values():
            if not rule.enabled or rule.trigger.get("type") != "schedule":
                continue
            interval = float(rule.trigger.get("interval_seconds", 0))
            if interval > 0 and self._schedule_due(rule, interval) and self._ready(rule):
                executions.append(self._execute(rule, {"trigger": "schedule"}))
        if executions:
            self.save()
        return executions

    def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="jarvis-automation", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def get_status(self) -> Dict[str, Any]:
        return {
            "rules": len(self.rules),
            "enabled_rules": len([rule for rule in self.rules.values() if rule.enabled]),
            "background_active": self.is_running,
            "executions": len(self.executions),
            "recent_executions": self.executions[-10:],
        }

    def _run_loop(self) -> None:
        while not self._stop_event.wait(self.poll_interval):
            try:
                self.run_pending()
            except Exception as exc:
                self.logger.warning("Automation loop failed: %s", exc)

    def _device_matches(self, trigger: Dict[str, Any], device: Dict[str, Any]) -> bool:
        for key in ("device_id", "device_type", "location"):
            expected = trigger.get(key)
            if expected and str(device.get(key, "")).lower() != str(expected).lower():
                return False
        prop = trigger.get("property")
        if prop is None:
            return True
        return device.get(prop) == trigger.get("equals")

    def _schedule_due(self, rule: AutomationRule, interval_seconds: float) -> bool:
        if not rule.last_triggered:
            return True
        return _now() - datetime.fromisoformat(rule.last_triggered) >= timedelta(seconds=interval_seconds)

    def _ready(self, rule: AutomationRule) -> bool:
        if not rule.last_triggered or rule.cooldown_seconds <= 0:
            return True
        return _now() - datetime.fromisoformat(rule.last_triggered) >= timedelta(seconds=rule.cooldown_seconds)

    def _execute(self, rule: AutomationRule, context: Dict[str, Any]) -> Dict[str, Any]:
        result = {"success": False, "message": "No automation executor configured."}
        if self.action_executor:
            result = self.action_executor(rule.action)
        rule.last_triggered = _now().isoformat()
        rule.run_count += 1
        execution = {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "timestamp": rule.last_triggered,
            "context": context,
            "action": rule.action,
            "result": result,
        }
        self.executions.append(execution)
        self.executions = self.executions[-100:]
        return execution
