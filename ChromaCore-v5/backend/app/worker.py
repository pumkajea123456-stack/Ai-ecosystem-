import os
import redis
from .db import init_db, get_job, put_job

REDIS_URL=os.getenv('REDIS_URL','redis://redis:6379/0')
queue=redis.Redis.from_url(REDIS_URL,decode_responses=True)
QUEUE_NAME='chromacore:jobs'

def enqueue(job_id): queue.rpush(QUEUE_NAME,job_id)
def dequeue(timeout=5):
    item=queue.blpop(QUEUE_NAME,timeout=timeout); return item[1] if item else None
def redis_up():
    try: return bool(queue.ping())
    except Exception: return False

def process(job_id):
    job=get_job(job_id)
    if not job: return
    put_job(job_id,job['kind'],'processing',job.get('input_ref'),job.get('metadata'))
    put_job(job_id,job['kind'],'completed',job.get('input_ref'),job.get('metadata'))

if __name__=='__main__':
    init_db()
    while True:
        job_id=dequeue()
        if job_id: process(job_id)
