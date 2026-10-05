import json
from pathlib import Path
import pytest


def test_system_get_never_initializes_legacy_or_mutates(tmp_path,monkeypatch):
    from dashboard import app as module
    monkeypatch.setattr(module,'legacy_db',lambda:pytest.fail('legacy DB initialization'))
    monkeypatch.setitem(module.app.config,'OMA_RUNTIME_CONFIG',None)
    monkeypatch.chdir(tmp_path)
    with module.app.test_client() as client:
        result=client.get('/api/system')
        assert result.status_code==200
        data=result.get_json()
        assert data['mode']=='UNKNOWN'
        assert data['execution']['execution_claim']=='NO_EXECUTION_EVIDENCE'
        assert data['science']['edge']=='NOT DEMONSTRATED'
        assert client.post('/api/system',json={'trade':True}).status_code==405
    assert list(tmp_path.iterdir())==[]


def test_api_corrupt_config_is_invalid_not_empty_success(tmp_path,monkeypatch):
    from dashboard import app as module
    path=tmp_path/'runtime.json'; path.write_text('{broken')
    monkeypatch.setitem(module.app.config,'OMA_RUNTIME_CONFIG',str(path))
    with module.app.test_client() as client:
        response=client.get('/api/system')
        assert response.status_code==503 and response.get_json()['status']=='INVALID'
        assert str(path) not in response.get_data(as_text=True)
