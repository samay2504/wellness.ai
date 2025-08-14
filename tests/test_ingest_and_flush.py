import os, json, uuid
from backend.app import app, db, storage_manager
from backend.models import BlinkEvent

def setup_module(module):
    with app.app_context():
        db.create_all()

def test_anonymous_ingest_and_queue(tmp_path):
    os.environ['ALLOW_ANONYMOUS_INGEST'] = 'true'
    os.environ['CLOUD_PROVIDER'] = 'local'
    with app.app_context():
        db.create_all()
        client = app.test_client()
        resp = client.post('/api/blink-data', json={'count':1,'device_id':'dev1','session_id':str(uuid.uuid4())})
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'event_id' in data
    with app.app_context():
        ev = BlinkEvent.query.filter_by(id=data['event_id']).first()
        assert ev is not None

def test_sync_flush_blocked_without_client():
    # Force provider gcs with missing creds
    os.environ['CLOUD_PROVIDER'] = 'gcs'
    summary = storage_manager.sync_flush()
    assert 'status' in summary
