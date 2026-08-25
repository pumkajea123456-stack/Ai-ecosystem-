import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def inspect_video(data: bytes, filename: str = 'input.bin') -> dict:
    ffprobe = shutil.which('ffprobe')
    if not ffprobe:
        return {'engine':'ffprobe','available':False,'status':'dependency_missing'}
    suffix=Path(filename).suffix or '.bin'
    with tempfile.TemporaryDirectory() as td:
        src=Path(td)/f'input{suffix}'; src.write_bytes(data)
        proc=subprocess.run([ffprobe,'-v','error','-show_format','-show_streams','-of','json',str(src)],capture_output=True,text=True,timeout=30)
        if proc.returncode != 0:
            return {'engine':'ffprobe','available':True,'status':'invalid_media','error':proc.stderr[-500:]}
        return {'engine':'ffprobe','available':True,'status':'inspected','media':json.loads(proc.stdout)}


def transcode_video(data: bytes, filename: str='input.bin', output_format: str='mp4', video_codec: str='libx264', audio_codec: str='aac') -> dict:
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg: return {'engine':'ffmpeg','available':False,'status':'dependency_missing'}
    if output_format not in {'mp4','webm','mkv'}: return {'engine':'ffmpeg','status':'invalid_format','format':output_format}
    if video_codec not in {'libx264','libvpx-vp9','libx265'}: return {'engine':'ffmpeg','status':'invalid_video_codec','video_codec':video_codec}
    if audio_codec not in {'aac','libopus'}: return {'engine':'ffmpeg','status':'invalid_audio_codec','audio_codec':audio_codec}
    suffix=Path(filename).suffix or '.bin'
    with tempfile.TemporaryDirectory() as td:
        src=Path(td)/f'input{suffix}'; out=Path(td)/f'output.{output_format}'; src.write_bytes(data)
        cmd=[ffmpeg,'-y','-i',str(src),'-c:v',video_codec,'-c:a',audio_codec,str(out)]
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        if proc.returncode != 0:
            return {'engine':'ffmpeg','available':True,'status':'transcode_failed','error':proc.stderr[-1000:]}
        return {'engine':'ffmpeg','available':True,'status':'transcoded','format':output_format,'video_codec':video_codec,'audio_codec':audio_codec,'bytes':out.stat().st_size}
