from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_account():
    r = client.get("/v5/account")
    assert r.status_code == 200
    assert r.json()["status"] == "active"


def test_preset():
    r = client.post("/v5/generate-preset", json={"name": "web", "target": "image"})
    assert r.status_code == 200
    assert r.json()["name"] == "web"


def test_batch_and_job_status():
    r = client.post("/v5/batch-process", json={"items": ["a", "b"]})
    assert r.status_code == 200
    job = r.json()
    assert job["count"] == 2
    status = client.get(f"/v5/jobs/{job['job_id']}")
    assert status.status_code == 200
    assert status.json()["status"] == "queued"


def test_process_image_and_storage_reference():
    r = client.post(
        "/v5/process-image",
        files={"file": ("sample.txt", b"chromacore-test", "text/plain")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "image"
    assert body["status"] == "processed"
    assert body["bytes"] == len(b"chromacore-test")
    assert body["input_ref"]


def test_missing_job():
    r = client.get("/v5/jobs/does-not-exist")
    assert r.status_code == 404
