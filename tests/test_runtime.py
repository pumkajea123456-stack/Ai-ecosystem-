from core.autonomous_runtime import AutonomousRuntime, PolicyEngine, Task


def test_allowed_action_executes_and_is_audited():
    runtime = AutonomousRuntime(PolicyEngine(["telemetry.read"]))
    task = Task("t-1", "research", "telemetry.read")
    result = runtime.execute(task, lambda _: {"status": "ok"})
    assert result["status"] == "ok"
    assert runtime.audit.events[-1]["allowed"] is True


def test_unlisted_action_is_denied():
    runtime = AutonomousRuntime(PolicyEngine(["telemetry.read"]))
    task = Task("t-2", "research", "credential.export")
    try:
        runtime.execute(task, lambda _: None)
        assert False, "restricted action should be denied"
    except PermissionError as exc:
        assert str(exc) == "action_not_allowed_by_policy"
