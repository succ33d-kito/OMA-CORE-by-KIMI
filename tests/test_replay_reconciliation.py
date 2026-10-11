from dataclasses import replace
from datetime import timedelta
import sqlite3
import pytest
from core.scientific import replay_reconciliation as reconciliation
from core.scientific.funding_rate_observation import append_verified_funding_rate_observation
from tests.test_causal_replay import prepare_ledger
from tests.test_metrics_continuity import state, S
from tests import test_funding_rate_observation as funding_fixture


def run(ledger, **kwargs):
    return reconciliation.reconcile_causal_replay(ledger,instrument='BTCUSDT',
                                                 as_of=S+timedelta(minutes=5),**kwargs)


def test_independent_replays_match_deterministically_without_ledger_writes(state,tmp_path,monkeypatch):
    ledger=prepare_ledger(state,tmp_path); before=ledger.read_bytes(); paths=[]
    original=reconciliation.replay_causal_state
    def recording(ledger,path,**kwargs):
        assert not path.exists()
        paths.append(path)
        return original(ledger,path,**kwargs)
    monkeypatch.setattr(reconciliation,'replay_causal_state',recording)
    a=run(ledger); b=run(ledger)
    assert len(set(paths))==4 and all(not p.exists() for p in paths)
    assert a==b and a.reconciliation_id==b.reconciliation_id
    assert a.require_match() is a and a.status=='MATCH'
    assert a.to_dict()['different_fields']==[] and ledger.read_bytes()==before
    exported=a.to_dict(); exported['status']='MISMATCH'
    assert a.status=='MATCH'


@pytest.mark.parametrize('field,value',[
    ('subgraph_sha256','different'),('missing_features',('different',)),
    ('latent_unknown_axes',('different',)),('unconsumed_features',('different',)),
    ('snapshot_id','different'),('market_state_id','different')])
def test_mismatch_preserves_diagnostics_and_blocks_success(state,tmp_path,monkeypatch,field,value):
    ledger=prepare_ledger(state,tmp_path); original=reconciliation.replay_causal_state; calls=0
    def altered(*args,**kwargs):
        nonlocal calls
        calls+=1
        result=original(*args,**kwargs)
        return replace(result,**{field:value}) if calls==2 else result
    monkeypatch.setattr(reconciliation,'replay_causal_state',altered)
    result=run(ledger)
    assert result.status=='MISMATCH'
    assert field in result.to_dict()['different_fields']
    assert 'replay_id' in result.to_dict()['different_fields']
    with pytest.raises(ValueError,match='MISMATCH'): result.require_match()


def test_verified_later_evidence_preserves_historical_certificate(state,tmp_path,monkeypatch):
    ledger=prepare_ledger(state,tmp_path); first=run(ledger)
    monkeypatch.setattr(funding_fixture,'T',S+timedelta(minutes=6))
    root,*_=funding_fixture.verified_capture(tmp_path)
    append_verified_funding_rate_observation(ledger,root,clock=lambda:S+timedelta(minutes=7))
    assert run(ledger)==first


def test_corrupt_chain_produces_no_certificate(state,tmp_path):
    ledger=prepare_ledger(state,tmp_path)
    with sqlite3.connect(ledger) as con:
        con.execute('DROP TRIGGER observations_v2_no_update')
        con.execute("UPDATE observations_v2 SET receipt_hash='bad' WHERE seq=1")
    with pytest.raises(ValueError,match='integrity'): run(ledger)


def test_feature_iterator_is_frozen_for_both_replays(state,tmp_path):
    ledger=prepare_ledger(state,tmp_path)
    features=('MarketMetrics/OpenInterest',)
    assert run(ledger,features=iter(features))==run(ledger,features=features)
