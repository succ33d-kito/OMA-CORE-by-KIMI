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


def test_mission_control_uses_only_system_api_and_safe_text(monkeypatch):
    from dashboard import app as module
    monkeypatch.setattr(module,'legacy_db',lambda:pytest.fail('legacy initialization from root'))
    with module.app.test_client() as client:
        html=client.get('/').get_data(as_text=True)
        for name in ('SYSTEM','DATA FABRIC','WORLD STATE','OPPORTUNITY RADAR','DECISION','PORTFOLIO','EXECUTION','POSITIONS','SCIENTIFIC STATUS'):
            assert name in html
        assert 'NO EXECUTION EVIDENCE' in html and 'NOT DEMONSTRATED' in html
        js=client.get('/static/mission_control.js').get_data(as_text=True)
        assert "fetch('/api/system'" in js and 'innerHTML' not in js
        assert 'textContent' in js and "item === null ? 'UNKNOWN'" in js
        assert '/api/opportunities' not in js and "method:'GET'" in js
        assert client.get('/legacy').status_code==200
