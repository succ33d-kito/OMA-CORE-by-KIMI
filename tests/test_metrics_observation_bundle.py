from dataclasses import FrozenInstanceError
from datetime import timedelta
import json
import pytest
from core.scientific import metrics_observation_bundle as projection
from tests.test_metrics_continuity import state, capture, snapshot, S


def load(state):
    return projection.load_verified_bundle(state[0],S,repo_root=state[1],now=S+timedelta(minutes=5))


def test_complete_projection_deterministic_and_no_admission(state):
    capture(state); before=snapshot(state[0])
    first=load(state); second=load(state)
    assert first==second and first.bundle_id==second.bundle_id
    body=json.loads(first.canonical_json)
    assert len(body['values'])==6
    assert body['dataset_role']=='PILOT'
    assert body['ledger_available_at'] is None and body['admission_status']=='NOT_ADMITTED'
    assert body['derived'] is False and body['dependencies']==[]
    assert body['received_at']<=body['capture_available_at']
    assert snapshot(state[0])==before
    with pytest.raises(FrozenInstanceError): first.canonical_json='{}'
    body['values'].clear()
    assert len(json.loads(first.canonical_json)['values'])==6


@pytest.mark.parametrize('file',['result.json','capture/available.json','capture/raw/oi.json'])
def test_missing_member_never_partial_projection(state,file):
    capture(state); (state[0]/'attempts'/'20261011T130000Z'/file).unlink()
    with pytest.raises((ValueError,FileNotFoundError)): load(state)


def test_corrupt_member_never_projects(state):
    capture(state)
    (state[0]/'attempts'/'20261011T130000Z'/'capture'/'raw'/'taker.json').write_bytes(b'[]')
    with pytest.raises(ValueError): load(state)


def test_future_evidence_not_projected(state):
    capture(state)
    with pytest.raises(ValueError):
        projection.load_verified_bundle(state[0],S,repo_root=state[1],now=S)


def test_mutation_during_verification_rejected(state,monkeypatch):
    capture(state); original=projection.continuity.verify_slot
    def changing(*args,**kwargs):
        result=original(*args,**kwargs)
        (state[0]/'attempts'/'20261011T130000Z'/'capture'/'raw'/'oi.json').write_bytes(b'[]')
        return result
    monkeypatch.setattr(projection.continuity,'verify_slot',changing)
    with pytest.raises(ValueError,match='changed'): load(state)
