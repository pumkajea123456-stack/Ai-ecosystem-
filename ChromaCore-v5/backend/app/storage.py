from pathlib import Path
import os

BASE = Path(os.getenv("CHROMACORE_STORAGE_PATH", "/tmp/chromacore"))
BASE.mkdir(parents=True, exist_ok=True)


def save_bytes(job_id: str, filename: str, data: bytes) -> str:
    safe = Path(filename or "upload.bin").name
    target = BASE / f"{job_id}_{safe}"
    target.write_bytes(data)
    return str(target)
