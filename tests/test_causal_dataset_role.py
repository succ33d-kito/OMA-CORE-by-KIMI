from dataclasses import replace
from datetime import timedelta
import pytest
from core.scientific.causal_observation_snapshot import load_causal_snapshot
from core.scientific.replay_reconciliation import reconcile_causal_replay
from core.scientific.funding_rate_observation import append_verified_funding_rate_observation
from core.scientific.prospective_receipts import append_observation
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


def test_authenticated_funding_role_enters_pilot_only(tmp_path,monkeypatch):
    monkeypatch.setattr(funding_fixture,'T',S)
    root,*_=funding_fixture.verified_capture(tmp_path)
    ledger=tmp_path/'ledger.db'

    row=append_verified_funding_rate_observation(
        ledger,
        root,
        clock=lambda:S+timedelta(minutes=1),
    )

    assert row['provenance']['dataset_role']=='PILOT'
    assert len(snap(ledger,None).observations)==1
    assert len(snap(ledger,'PILOT').observations)==1
    assert snap(ledger,'DISCOVERY').observations==()
    assert snap(ledger,'CONFIRMATION').observations==()


def test_historical_roleless_funding_remains_unscoped(tmp_path,monkeypatch):
    monkeypatch.setattr(funding_fixture,'T',S)
    root,*_=funding_fixture.verified_capture(tmp_path)

    source_ledger=tmp_path/'source.db'

    current=append_verified_funding_rate_observation(
        source_ledger,
        root,
        clock=lambda:S+timedelta(minutes=1),
    )

    provenance=dict(current['provenance'])
    provenance.pop('dataset_role')
    provenance.pop('dataset_role_contract')

    legacy=tmp_path/'legacy.db'

    append_observation(
        legacy,
        source=current['source'],
        instrument=current['instrument'],
        feature=current['feature'],
        event_time=current['event_time'],
        source_metric_at=current['source_metric_at'],
        received_at=current['received_at'],
        payload=current['payload'],
        provenance=provenance,
        clock=lambda:S+timedelta(minutes=2),
    )

    assert len(snap(legacy,None).observations)==1
    assert snap(legacy,'PILOT').observations==()


def test_funding_role_provenance_contract_tamper_fails_closed(tmp_path,monkeypatch):
    monkeypatch.setattr(funding_fixture,'T',S)
    root,*_=funding_fixture.verified_capture(tmp_path)

    source_ledger=tmp_path/'source-role-contract.db'

    current=append_verified_funding_rate_observation(
        source_ledger,
        root,
        clock=lambda:S+timedelta(minutes=1),
    )

    provenance=dict(current['provenance'])
    provenance['dataset_role_contract']='forged-role-contract'

    forged=tmp_path/'role-contract-forged.db'

    append_observation(
        forged,
        source=current['source'],
        instrument=current['instrument'],
        feature=current['feature'],
        event_time=current['event_time'],
        source_metric_at=current['source_metric_at'],
        received_at=current['received_at'],
        payload=current['payload'],
        provenance=provenance,
        clock=lambda:S+timedelta(minutes=2),
    )

    assert snap(forged,None).observations==()
    assert snap(forged,'PILOT').observations==()


def test_forged_funding_role_fails_closed(tmp_path,monkeypatch):
    monkeypatch.setattr(funding_fixture,'T',S)
    root,*_=funding_fixture.verified_capture(tmp_path)

    source_ledger=tmp_path/'source.db'

    current=append_verified_funding_rate_observation(
        source_ledger,
        root,
        clock=lambda:S+timedelta(minutes=1),
    )

    provenance=dict(current['provenance'])
    provenance['dataset_role']='DISCOVERY'

    forged=tmp_path/'forged.db'

    append_observation(
        forged,
        source=current['source'],
        instrument=current['instrument'],
        feature=current['feature'],
        event_time=current['event_time'],
        source_metric_at=current['source_metric_at'],
        received_at=current['received_at'],
        payload=current['payload'],
        provenance=provenance,
        clock=lambda:S+timedelta(minutes=2),
    )

    assert snap(forged,None).observations==()
    assert snap(forged,'DISCOVERY').observations==()


def test_funding_capture_identity_tamper_fails_closed(tmp_path,monkeypatch):
    monkeypatch.setattr(funding_fixture,'T',S)
    root,*_=funding_fixture.verified_capture(tmp_path)

    source_ledger=tmp_path/'source.db'

    current=append_verified_funding_rate_observation(
        source_ledger,
        root,
        clock=lambda:S+timedelta(minutes=1),
    )

    provenance=dict(current['provenance'])
    provenance['capture_identity']='f'*64

    forged=tmp_path/'identity-forged.db'

    append_observation(
        forged,
        source=current['source'],
        instrument=current['instrument'],
        feature=current['feature'],
        event_time=current['event_time'],
        source_metric_at=current['source_metric_at'],
        received_at=current['received_at'],
        payload=current['payload'],
        provenance=provenance,
        clock=lambda:S+timedelta(minutes=2),
    )

    assert snap(forged,None).observations==()
    assert snap(forged,'PILOT').observations==()


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
