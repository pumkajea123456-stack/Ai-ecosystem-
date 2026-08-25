import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://chromacore:chromacore_dev@postgres:5432/chromacore")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

CREATE_JOBS = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    input_ref TEXT,
    output_ref TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
)
"""

def init_db():
    with engine.begin() as conn:
        conn.execute(text(CREATE_JOBS))

def db_up() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

def put_job(job_id: str, kind: str, status: str, input_ref: str | None = None, metadata: dict | None = None):
    with engine.begin() as conn:
        conn.execute(text("""INSERT INTO jobs(id,kind,status,input_ref,metadata) VALUES (:id,:kind,:status,:input_ref,:metadata::jsonb)
        ON CONFLICT(id) DO UPDATE SET status=:status, updated_at=NOW()"""), {
            "id": job_id, "kind": kind, "status": status, "input_ref": input_ref,
            "metadata": __import__('json').dumps(metadata or {})
        })

def get_job(job_id: str):
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id,kind,status,created_at,updated_at,input_ref,output_ref,metadata FROM jobs WHERE id=:id"), {"id": job_id}).mappings().first()
        return dict(row) if row else None
