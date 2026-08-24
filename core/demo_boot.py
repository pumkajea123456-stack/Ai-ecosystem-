"""Safe local demonstration of the autonomous control loop.

This demo performs read-only/recommendation actions only. It does not connect
to external services, spend money, deploy production code, or control machinery.
"""
import json
from pathlib import Path
from core.autonomous_runtime import AutonomousRuntime, PolicyEngine, Task


def main():
    policy = json.loads(Path("core/config/default_policy.json").read_text())
    runtime = AutonomousRuntime(PolicyEngine(policy["allowed_actions"]))

    tasks = [
        Task("demo-001", "research", "market.read"),
        Task("demo-002", "operations", "inventory.read"),
        Task("demo-003", "engineering", "code.test"),
    ]

    for task in tasks:
        decision = runtime.authorize(task)
        print(task.task_id, task.action, decision.allowed, decision.reason)

    print("audit_events=", len(runtime.audit.events))
    print("mode=observe_and_recommend")


if __name__ == "__main__":
    main()
