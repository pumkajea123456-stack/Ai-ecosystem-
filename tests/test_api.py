from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_authorize_allowed_action():
    response = client.post("/tasks/authorize", json={
        "task_id": "api-1",
        "agent": "research",
        "action": "market.read",
        "risk": "low"
    })
    assert response.status_code == 200
    assert response.json()["allowed"] is True


def test_authorize_restricted_action():
    response = client.post("/tasks/authorize", json={
        "task_id": "api-2",
        "agent": "unknown",
        "action": "credential.export",
        "risk": "critical"
    })
    assert response.status_code == 403
