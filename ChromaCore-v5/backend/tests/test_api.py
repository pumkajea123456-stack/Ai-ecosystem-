from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_account():
    r = client.get('/v5/account')
    assert r.status_code == 200
    assert r.json()['status'] == 'active'

def test_preset():
    r = client.post('/v5/generate-preset', json={'name': 'web', 'target': 'image'})
    assert r.status_code == 200
    assert r.json()['name'] == 'web'

def test_batch():
    r = client.post('/v5/batch-process', json={'items': ['a', 'b']})
    assert r.status_code == 200
    assert r.json()['count'] == 2
