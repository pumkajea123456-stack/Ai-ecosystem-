import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
queue = redis.Redis.from_url(REDIS_URL, decode_responses=True)

QUEUE_NAME = "chromacore:jobs"

def enqueue(job_id: str):
    queue.rpush(QUEUE_NAME, job_id)

def dequeue(timeout: int = 5):
    item = queue.blpop(QUEUE_NAME, timeout=timeout)
    return item[1] if item else None

def redis_up() -> bool:
    try:
        return bool(queue.ping())
    except Exception:
        return False

if __name__ == "__main__":
    from app.db import init_db, get_job, put_job
    init_db()
    while True:
        job_id = dequeue()
        if not job_id:
            continue
        job = get_job(job_id)
        if job:
            put_job(job_id, job["kind"], "processing", job.get("input_ref"), job.get("metadata"))
            put_job(job_id, job["kind"], "completed", job.get("input_ref"), job.get("metadata"))
