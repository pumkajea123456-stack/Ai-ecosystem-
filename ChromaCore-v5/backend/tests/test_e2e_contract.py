import io
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def png_bytes():
    b=io.BytesIO(); Image.new('RGB',(2,2),'white').save(b,format='PNG'); return b.getvalue()

def test_image_to_job_e2e_contract():
    r=client.post('/v5/process-image',files={'file':('e2e.png',png_bytes(),'image/png')})
    assert r.status_code==200
    body=r.json()
    assert body['kind']=='image'
    assert body['status']=='queued'
    assert body['input_ref']
    status=client.get('/v5/jobs/'+body['job_id'])
    assert status.status_code==200

def test_scene_analysis_contract_without_model_is_explicit():
    r=client.post('/v5/analyze-scene',files={'file':('e2e.png',png_bytes(),'image/png')})
    assert r.status_code in (200,503)
    if r.status_code==200:
        assert 'status' in r.json()

def test_video_transcode_contract_requires_real_input_or_reports_dependency():
    r=client.post('/v5/transcode-video',files={'file':('sample.mp4',b'not-a-real-video','video/mp4')})
    assert r.status_code in (400,415,422,500,503)
