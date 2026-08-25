from time import time
from uuid import uuid4

_jobs: dict[str, dict] = {}


def create_job(kind: str, payload: dict) -> dict:
    job_id = str(uuid4())
    job = {
        "job_id": job_id,
        "kind": kind,
        "status": "queued",
        "created_at": time(),
        "payload": payload,
    }
    _jobs[job_id] = job
    return job


def update_job(job_id: str, **changes) -> dict | None:
    job = _jobs.get(job_id)
    if job is None:
        return None
    job.update(changes)
    return job


def get_job(job_id: str) -> dict | None:
    return _jobs.get(job_id)


def list_jobs() -> list[dict]:
    return list(_jobs.values())
