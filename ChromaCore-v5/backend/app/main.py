from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from .jobs import create_job, get_job, list_jobs, update_job
from .storage import save_bytes

app = FastAPI(title="ChromaCore v5", version="5.0.0")


class BatchRequest(BaseModel):
    items: list[str]


class PresetRequest(BaseModel):
    name: str = "default"
    target: str = "image"


@app.get("/health")
def health():
    return {"status": "ok", "service": "chromacore-v5"}


@app.post("/v5/process-image")
async def process_image(file: UploadFile = File(...)):
    job = create_job("image", {"filename": file.filename})
    data = await file.read()
    path = save_bytes(job["job_id"], file.filename or "upload.bin", data)
    update_job(job["job_id"], status="processed", input_ref=path, bytes=len(data))
    return get_job(job["job_id"])


@app.post("/v5/process-video")
async def process_video(file: UploadFile = File(...)):
    job = create_job("video", {"filename": file.filename})
    data = await file.read()
    path = save_bytes(job["job_id"], file.filename or "upload.bin", data)
    update_job(job["job_id"], status="accepted", input_ref=path, bytes=len(data), engine="video")
    return get_job(job["job_id"])


@app.post("/v5/batch-process")
def batch_process(req: BatchRequest):
    job = create_job("batch", {"items": req.items})
    update_job(job["job_id"], status="queued", count=len(req.items), engine="batch")
    return get_job(job["job_id"])


@app.post("/v5/analyze-scene")
def analyze_scene():
    return {
        "status": "analyzed",
        "objects": [],
        "confidence": 0.0,
        "note": "Vision model not configured; deterministic empty result.",
    }


@app.post("/v5/generate-preset")
def generate_preset(req: PresetRequest):
    return {
        "name": req.name,
        "target": req.target,
        "preset": {"resize": "auto", "quality": 85, "format": "auto"},
    }


@app.get("/v5/jobs")
def jobs():
    return {"jobs": list_jobs(), "count": len(list_jobs())}


@app.get("/v5/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/v5/account")
def account():
    return {"plan": "development", "account_id": "local", "status": "active"}


@app.get("/v5/usage")
def usage():
    jobs = list_jobs()
    return {"jobs": len(jobs), "queued": sum(j["status"] == "queued" for j in jobs)}
