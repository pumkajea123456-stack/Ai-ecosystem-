import base64
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

# 1x1 transparent PNG; keeps the API test independent of external files.
PNG_1X1=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')

def test_health():
    r=client.get('/health'); assert r.status_code==200; assert r.json()['status']=='ok'

def test_account():
    r=client.get('/v5/account'); assert r.status_code==200; assert r.json()['status']=='active'

def test_preset():
    r=client.post('/v5/generate-preset',json={'name':'web','target':'image'}); assert r.status_code==200; assert r.json()['name']=='web'

def test_batch_and_job_status():
    r=client.post('/v5/batch-process',json={'items':['a','b']}); assert r.status_code==200
    job=r.json(); assert job['count']==2
    status=client.get(f"/v5/jobs/{job['job_id']}"); assert status.status_code==200; assert status.json()['status']=='queued'

def test_process_image_and_storage_reference():
    r=client.post('/v5/process-image',files={'file':('sample.png',PNG_1X1,'image/png')}); assert r.status_code==200
    body=r.json(); assert body['kind']=='image'; assert body['status']=='queued'; assert body['bytes']==len(PNG_1X1); assert body['input_ref']

def test_missing_job():
    assert client.get('/v5/jobs/does-not-exist').status_code==404
