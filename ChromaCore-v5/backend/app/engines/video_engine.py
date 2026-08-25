import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def inspect_video(data: bytes, filename: str = "input.bin") -> dict:
    """FFprobe-backed video inspection. Does not transcode unless an output operation is added."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {"engine": "ffprobe", "available": False, "status": "dependency_missing"}
    suffix = Path(filename).suffix or ".bin"
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / f"input{suffix}"
        src.write_bytes(data)
        proc = subprocess.run([ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(src)], capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return {"engine": "ffprobe", "available": True, "status": "invalid_media", "error": proc.stderr[-500:]}
        return {"engine": "ffprobe", "available": True, "status": "inspected", "media": json.loads(proc.stdout)}
