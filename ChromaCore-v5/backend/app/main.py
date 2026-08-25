from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from .jobs import create_job, get_job, list_jobs, update_job
from .storage import save_bytes
from .db import init_db, db_up, put_job, get_db_job
from .worker import enqueue, redis_up
from .engines.image_engine import inspect_image
from .engines.video_engine import inspect_video, transcode_video
from .engines.vision_engine import analyze_image

app=FastAPI(title='ChromaCore v5',version='5.0.0')
class BatchRequest(BaseModel): items:list[str]
class PresetRequest(BaseModel): name:str='default'; target:str='image'
class VideoTranscodeRequest(BaseModel): format:str='mp4'; video_codec:str='libx264'; audio_codec:str='aac'
@app.on_event('startup')
def startup():
    try: init_db()
    except Exception: pass
@app.get('/health')
def health(): return {'status':'ok','service':'chromacore-v5','postgres':db_up(),'redis':redis_up()}
@app.post('/v5/process-image')
async def process_image(file:UploadFile=File(...)):
    data=await file.read()
    try: engine_result=inspect_image(data)
    except Exception as exc: raise HTTPException(status_code=415,detail=f'unsupported image: {exc}')
    job=create_job('image',{'filename':file.filename}); path=save_bytes(job['job_id'],file.filename or 'upload.bin',data)
    update_job(job['job_id'],status='queued',input_ref=path,bytes=len(data),engine=engine_result)
    try: put_job(job['job_id'],'image','queued',path,{'filename':file.filename,'bytes':len(data),'engine':engine_result}); enqueue(job['job_id'])
    except Exception: pass
    return get_job(job['job_id'])
@app.post('/v5/process-video')
async def process_video(file:UploadFile=File(...)):
    data=await file.read(); engine_result=inspect_video(data,file.filename or 'input.bin')
    if engine_result.get('status')=='invalid_media': raise HTTPException(status_code=415,detail=engine_result)
    job=create_job('video',{'filename':file.filename}); path=save_bytes(job['job_id'],file.filename or 'upload.bin',data)
    update_job(job['job_id'],status='queued',input_ref=path,bytes=len(data),engine=engine_result)
    try: put_job(job['job_id'],'video','queued',path,{'filename':file.filename,'bytes':len(data),'engine':engine_result}); enqueue(job['job_id'])
    except Exception: pass
    return get_job(job['job_id'])
@app.post('/v5/transcode-video')
async def transcode_video_api(file:UploadFile=File(...), format:str='mp4', video_codec:str='libx264', audio_codec:str='aac'):
    data=await file.read()
    result=transcode_video(data,file.filename or 'input.bin',format,video_codec,audio_codec)
    if result.get('status') not in ('transcoded','dependency_missing'):
        raise HTTPException(status_code=422,detail=result)
    return result
@app.post('/v5/batch-process')
def batch_process(req:BatchRequest):
    job=create_job('batch',{'items':req.items}); update_job(job['job_id'],status='queued',count=len(req.items),engine='batch')
    try: put_job(job['job_id'],'batch','queued',None,{'items':req.items}); enqueue(job['job_id'])
    except Exception: pass
    return get_job(job['job_id'])
@app.post('/v5/analyze-scene')
async def analyze_scene(file:UploadFile=File(...)):
    data=await file.read()
    try: inspect_image(data)
    except Exception as exc: raise HTTPException(status_code=415,detail=f'unsupported image: {exc}')
    return analyze_image(data)
@app.post('/v5/generate-preset')
def generate_preset(req:PresetRequest): return {'name':req.name,'target':req.target,'preset':{'resize':'auto','quality':85,'format':'auto'}}
@app.get('/v5/jobs')
def jobs():
    local=list_jobs(); return {'jobs':local,'count':len(local)}
@app.get('/v5/jobs/{job_id}')
def job_status(job_id:str):
    dbjob=get_db_job(job_id)
    if dbjob is not None: return dbjob
    job=get_job(job_id)
    if job is not None: return job
    raise HTTPException(status_code=404,detail='job not found')
@app.get('/v5/account')
def account(): return {'plan':'development','account_id':'local','status':'active'}
@app.get('/v5/usage')
def usage():
    jobs=list_jobs(); return {'jobs':len(jobs),'queued':sum(j['status']=='queued' for j in jobs)}
