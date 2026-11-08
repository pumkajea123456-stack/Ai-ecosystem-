from core.autonomous_runtime import AutonomousRuntime, PolicyEngine, Task
from core.persistence import CoreStore


def test_runtime_persists_task_lifecycle_and_audit(tmp_path):
    store = CoreStore(str(tmp_path / "runtime.db"))
    runtime = AutonomousRuntime(PolicyEngine(["market.read"]), store=store)
    task = Task("runtime-1", "research", "market.read")
    assert runtime.execute(task, lambda _: {"items": 2}) == {"items": 2}
    assert store.list_tasks()[0]["status"] == "completed"
    events = store.list_audit()
    assert len(events) == 2
    assert events[-1]["result"] == {"items": 2}


def test_denied_task_is_persisted(tmp_path):
    store = CoreStore(str(tmp_path / "runtime.db"))
    runtime = AutonomousRuntime(PolicyEngine([]), store=store)
    task = Task("runtime-2", "research", "credential.export")
    try:
        runtime.execute(task, lambda _: None)
        assert False, "denied task must not execute"
    except PermissionError:
        pass
    assert store.list_tasks()[0]["status"] == "denied"
    assert store.list_audit()[0]["allowed"] is False
