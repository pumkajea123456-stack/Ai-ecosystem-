"""Policy-gated execution runtime for the Autonomous Industrial Core.

The runtime separates AI recommendations from consequential execution. Every
job is validated against an explicit allow-list and produces an audit event.
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
    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def record(self, task: Task, decision: PolicyDecision, result: Any = None):
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task.task_id,
            "agent": task.agent,
            "action": task.action,
            "allowed": decision.allowed,
            "reason": decision.reason,
            "result": result,
        })


class AutonomousRuntime:
    def __init__(self, policy: PolicyEngine):
        self.policy = policy
        self.audit = AuditLog()

    def authorize(self, task: Task) -> PolicyDecision:
        decision = self.policy.evaluate(task)
        self.audit.record(task, decision)
        return decision

    def execute(self, task: Task, executor):
        decision = self.authorize(task)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        result = executor(task)
        self.audit.record(task, decision, result)
        return result
