"""Policy-gated execution runtime for the Autonomous Industrial Core.

The runtime separates recommendations from consequential execution. Durable
storage is optional; when configured, task and audit records survive restarts.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class Task:
    task_id: str
    agent: str
    action: str
    risk: str = "low"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str


class PolicyEngine:
    def __init__(self, allowed_actions: List[str] | None = None):
        self.allowed_actions = set(allowed_actions or [])

    def evaluate(self, task: Task) -> PolicyDecision:
        if task.action not in self.allowed_actions:
            return PolicyDecision(False, "action_not_allowed_by_policy")
        if task.risk == "critical":
            return PolicyDecision(False, "critical_action_requires_explicit_authorization")
        return PolicyDecision(True, "policy_pass")


class AuditLog:
    def __init__(self, store=None):
        self.events: List[Dict[str, Any]] = []
        self.store = store

    def record(self, task: Task, decision: PolicyDecision, result: Any = None):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task.task_id,
            "agent": task.agent,
            "action": task.action,
            "allowed": decision.allowed,
            "reason": decision.reason,
            "result": result,
        }
        self.events.append(event)
        if self.store is not None:
            self.store.record_audit(event)


class AutonomousRuntime:
    def __init__(self, policy: PolicyEngine, store=None):
        self.policy = policy
        self.store = store
        self.audit = AuditLog(store=store)

    def authorize(self, task: Task) -> PolicyDecision:
        if self.store is not None:
            self.store.save_task(task, status="authorized_pending")
        decision = self.policy.evaluate(task)
        self.audit.record(task, decision)
        if self.store is not None:
            self.store.update_task_status(
                task.task_id, "authorized" if decision.allowed else "denied"
            )
        return decision

    def execute(self, task: Task, executor):
        decision = self.authorize(task)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        if self.store is not None:
            self.store.update_task_status(task.task_id, "running")
        try:
            result = executor(task)
        except Exception as exc:
            if self.store is not None:
                self.store.update_task_status(task.task_id, "failed")
            self.audit.record(task, decision, {"error": type(exc).__name__})
            raise
        if self.store is not None:
            self.store.update_task_status(task.task_id, "completed")
        self.audit.record(task, decision, result)
        return result
