from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core.autonomous_runtime import AutonomousRuntime, PolicyEngine, Task
import json
from pathlib import Path

app = FastAPI(title="Autonomous Industrial Core API", version="0.1.0")
policy = json.loads(Path("core/config/default_policy.json").read_text())
runtime = AutonomousRuntime(PolicyEngine(policy["allowed_actions"]))

class TaskRequest(BaseModel):
    task_id: str
    agent: str
    action: str
    risk: str = Field(default="low", pattern="^(low|medium|high|critical)$")
    parameters: dict = Field(default_factory=dict)

@app.get("/health")
def health():
    return {"status": "ok", "mode": policy["default_mode"]}

@app.get("/agents")
def agents():
    data = json.loads(Path("core/agent_registry.json").read_text())
    return data

@app.get("/audit")
def audit():
    return {"events": runtime.audit.events}

@app.post("/tasks/authorize")
def authorize(request: TaskRequest):
    task = Task(**request.model_dump())
    decision = runtime.authorize(task)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    return {"allowed": True, "reason": decision.reason, "task_id": task.task_id}
