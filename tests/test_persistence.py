from core.autonomous_runtime import PolicyDecision, Task
from core.persistence import CoreStore


def test_task_and_audit_round_trip(tmp_path):
    store = CoreStore(str(tmp_path / "core.db"))
    task = Task("persist-1", "research", "market.read",
                parameters={"region": "TH"})
    store.save_task(task)
    store.record_audit({
        "timestamp": "2026-11-08T00:00:00+00:00",
        "task_id": task.task_id,
        "agent": task.agent,
        "action": task.action,
        "allowed": True,
        "reason": "policy_pass",
        "result": {"records": 3},
    })
    assert store.list_tasks()[0]["parameters"] == {"region": "TH"}
    event = store.list_audit()[0]
    assert event["task_id"] == "persist-1"
    assert event["allowed"] is True
    assert event["result"] == {"records": 3}


def test_unknown_task_status_update_fails(tmp_path):
    store = CoreStore(str(tmp_path / "core.db"))
    try:
        store.update_task_status("missing", "running")
        assert False, "expected missing task to fail"
    except KeyError:
        pass
