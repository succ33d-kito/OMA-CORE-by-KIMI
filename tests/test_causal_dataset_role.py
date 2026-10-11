from dataclasses import replace
from datetime import timedelta
import pytest
from core.scientific.causal_observation_snapshot import load_causal_snapshot
from core.scientific.replay_reconciliation import reconcile_causal_replay
from core.scientific.funding_rate_observation import append_verified_funding_rate_observation
from tests import test_funding_rate_observation as funding_fixture
from tests.test_causal_replay import prepare_ledger
from tests.test_metrics_continuity import state,S


def snap(ledger,role):
    return load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=S+timedelta(minutes=5),dataset_role=role)


def test_role_isolation_and_empty_identity(state,tmp_path):
    ledger=prepare_ledger(state,tmp_path); before=ledger.read_bytes()
    pilot=snap(ledger,'PILOT'); discovery=snap(ledger,'DISCOVERY'); confirmation=snap(ledger,'CONFIRMATION')
    assert len(pilot.observations)==6
    assert discovery.observations==confirmation.observations==()
    assert len({x.snapshot_id for x in (pilot,discovery,confirmation)})==3
    assert pilot.to_dict()['dataset_role']=='PILOT'
    assert ledger.read_bytes()==before
    with pytest.raises(ValueError,match='role'): replace(pilot,dataset_role='DISCOVERY')


def test_role_propagates_to_both_replays(state,tmp_path):
    ledger=prepare_ledger(state,tmp_path)
    result=reconcile_causal_replay(ledger,instrument='BTCUSDT',as_of=S+timedelta(minutes=5),dataset_role='PILOT')
    assert result.status=='MATCH'
    assert result.to_dict()['left']['dataset_role']==result.to_dict()['right']['dataset_role']=='PILOT'
    other=reconcile_causal_replay(ledger,instrument='BTCUSDT',as_of=S+timedelta(minutes=5),dataset_role='DISCOVERY')
    assert result.reconciliation_id!=other.reconciliation_id


def test_missing_funding_role_is_not_inferred(tmp_path,monkeypatch):
    monkeypatch.setattr(funding_fixture,'T',S)
    root,*_=funding_fixture.verified_capture(tmp_path)
    ledger=tmp_path/'ledger.db'
    append_verified_funding_rate_observation(ledger,root,clock=lambda:S+timedelta(minutes=1))
    assert len(snap(ledger,None).observations)==1
    assert snap(ledger,'PILOT').observations==()


@pytest.mark.parametrize('role',['pilot','',False,42])
def test_invalid_role_fails_closed(state,tmp_path,role):
    ledger=prepare_ledger(state,tmp_path)
    with pytest.raises(ValueError): snap(ledger,role)


def test_cli_role_and_unscoped_compatibility(state,tmp_path):
    import json
    from scripts.reconcile_causal_replay import main
    ledger=prepare_ledger(state,tmp_path)
    unscoped=snap(ledger,None)
    assert 'dataset_role' not in unscoped.to_dict()
    output=tmp_path/'role.json'
    assert main(['--ledger',str(ledger),'--instrument','BTCUSDT',
                 '--as-of',(S+timedelta(minutes=5)).isoformat(),
                 '--output',str(output),'--role','CONFIRMATION'])==0
    result=json.loads(output.read_bytes())
    assert result['left']['dataset_role']=='CONFIRMATION'
    assert result['left']['observation_ids']==[]
