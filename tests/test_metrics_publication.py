from datetime import timedelta
import pytest
from core.scientific import metrics_observation_admission as admission
from core.scientific.metrics_snapshot_gate import metrics_snapshot_available
from core.scientific.metrics_publication import observation_snapshot
from core.scientific import metrics_publication as publication
from tests.test_metrics_continuity import S, capture, state


def test_delayed_final_validation_is_unavailable_at_earlier_decision(state, tmp_path, monkeypatch):
    capture(state)
    now = [S + timedelta(minutes=4)]
    decision = S + timedelta(hours=1)
    original = admission.load_verified_bundle
    calls = []
    def delayed(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(1)
        if len(calls) == 2:
            now[0] = decision + timedelta(seconds=1)
        return result
    monkeypatch.setattr(admission, 'load_verified_bundle', delayed)
    monkeypatch.setattr(publication, '_now', lambda: now[0])
    ledger = tmp_path / 'observations.db'
    admission.admit_verified_metrics_bundle(ledger, state[0], S, repo_root=state[1],
        now=now[0], clock=lambda: now[0])
    rows, _ = observation_snapshot(ledger, read_only=True)
    assert len(rows) == 6
    assert now[0] > decision
    assert not any(metrics_snapshot_available(rows, key, decision) for key in rows)

import inspect
import json
import sqlite3
from copy import deepcopy
from core.scientific.prospective_receipts import observation_snapshot as physical_snapshot, canonical_observation, observation_hash
from core.scientific.causal_observation_snapshot import load_causal_snapshot
from core.scientific.causal_mechanics import build_causal_mechanics, append_causal_mechanics
from core.scientific.experiment51_derived import derived
from core.scientific.causal_replay import replay_causal_state


def admit(state, ledger):
    return admission.admit_verified_metrics_bundle(ledger, state[0], S,
        repo_root=state[1], now=S+timedelta(minutes=4), clock=lambda:S+timedelta(minutes=4))


@pytest.fixture
def published(state, tmp_path, monkeypatch):
    capture(state)
    ledger=tmp_path/'published.db'
    def after_commit():
        # Independent connection sees all six rows before publication clock is sampled.
        assert len(physical_snapshot(ledger, read_only=True)[0]) == 6
        return S+timedelta(minutes=4, seconds=1)
    monkeypatch.setattr(publication, '_now', after_commit)
    result=admit(state,ledger)
    return ledger,result


def test_post_commit_available_and_replay_identity(published,tmp_path):
    ledger,result=published; D=S+timedelta(minutes=5)
    rows,_=observation_snapshot(ledger)
    assert all(metrics_snapshot_available(rows,i,D) for i in rows)
    assert not any(metrics_snapshot_available(rows,i,S+timedelta(minutes=4)) for i in rows)
    assert not any(metrics_snapshot_available(dict(rows),i,D) for i in rows)
    snapshot=load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=D,dataset_role='PILOT')
    assert len(snapshot.observations)==6
    assert {o.available_at.isoformat() for o in snapshot.observations} == {result['publication']['published_at']}
    assert all(json.loads(o.provenance_json)['durable_publication']==result['publication'] for o in snapshot.observations)
    a=replay_causal_state(ledger,tmp_path/'a.db',instrument='BTCUSDT',as_of=D)
    b=replay_causal_state(ledger,tmp_path/'b.db',instrument='BTCUSDT',as_of=D)
    assert a==b
    row=append_causal_mechanics(ledger,dataset_role='PILOT',cutoff=D,clock=lambda:D)
    assert row['payload']['input_available_at']==result['publication']['published_at']
    assert derived(ledger,role='PILOT',decision_at=S+timedelta(hours=1),mechanics_id=row['id']).taker=='1.4'


def test_duplicate_is_exact_immutable_and_preserves_rows(published,state,monkeypatch):
    ledger,result=published
    before=ledger.read_bytes()
    monkeypatch.setattr(publication,'_now',lambda:pytest.fail('duplicate must not sample publication time'))
    second=admit(state,ledger)
    assert second['publication']==result['publication']
    assert ledger.read_bytes()==before
    with sqlite3.connect(ledger) as con:
        for statement in ['UPDATE metrics_publications_v1 SET body=body','DELETE FROM metrics_publications_v1']:
            with pytest.raises(sqlite3.DatabaseError,match='append-only'):
                con.execute(statement)


@pytest.mark.parametrize('mutation',['five','seven','ids','bundle','role','hash','backdate','ledger','extra'])
def test_forged_publication_rejected(published,mutation):
    ledger,result=published
    rows,prefixes=physical_snapshot(ledger,read_only=True)
    receipt=deepcopy(result['publication'])
    if mutation=='five': receipt['observation_ids'].pop()
    elif mutation=='seven': receipt['observation_ids'].append('extra')
    elif mutation=='ids': receipt['observation_ids'][0]='wrong'
    elif mutation=='bundle': receipt['bundle_id']='wrong'
    elif mutation=='role': receipt['dataset_role']='CONFIRMATION'
    elif mutation=='backdate': receipt['published_at']=S.isoformat()
    elif mutation=='ledger': receipt['ledger_commitment']='wrong'
    elif mutation=='extra': receipt['caller_supplied_available_at']=S.isoformat()
    else: receipt['publication_id']='bad'
    if mutation!='hash': receipt['publication_id']=observation_hash({k:v for k,v in receipt.items() if k!='publication_id'})
    with pytest.raises((ValueError,KeyError)):
        publication._validate(receipt,rows,prefixes)


def test_corrupt_persisted_receipt_fails_closed(published):
    ledger,_=published
    with sqlite3.connect(ledger) as con:
        con.execute('DROP TRIGGER metrics_publications_v1_no_update')
        con.execute("UPDATE metrics_publications_v1 SET body='{}'")
    with pytest.raises((ValueError,KeyError)):
        load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=S+timedelta(hours=1))


def test_conflicting_duplicate_never_overwrites(published,monkeypatch):
    ledger,result=published; before=ledger.read_bytes()
    monkeypatch.setattr(publication,'_now',lambda:S+timedelta(minutes=5))
    with pytest.raises(ValueError,match='conflicting publication'):
        publication._publish_committed(ledger,result['bundle_id'])
    assert ledger.read_bytes()==before


def test_no_timestamp_argument_and_caller_clock_cannot_backdate(published):
    ledger,result=published
    assert set(inspect.signature(publication._publish_committed).parameters)=={'path','bundle_id'}
    assert result['publication']['published_at']==(S+timedelta(minutes=4,seconds=1)).isoformat()
    with pytest.raises(TypeError):
        publication._publish_committed(ledger,result['bundle_id'],published_at=S)


def test_crash_after_commit_is_not_repaired_on_restart(state,tmp_path,monkeypatch):
    capture(state); ledger=tmp_path/'crash.db'
    with monkeypatch.context() as m:
        m.setattr(publication,'_publish_committed',lambda *a:(_ for _ in ()).throw(RuntimeError('crash')))
        with pytest.raises(RuntimeError,match='crash'): admit(state,ledger)
    before=ledger.read_bytes()
    for _ in range(2):
        rows,_=observation_snapshot(ledger)
        assert len(rows)==6
        assert not any(metrics_snapshot_available(rows,i,S+timedelta(hours=2)) for i in rows)
        assert not load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=S+timedelta(hours=2)).observations
        assert not build_causal_mechanics(ledger,dataset_role='PILOT',cutoff=S+timedelta(hours=2))['raw_values']
        with pytest.raises(ValueError,match='missing valid publication'):
            admit(state,ledger)
    assert ledger.read_bytes()==before


def test_transaction_failure_zero_rows_zero_publications(state,tmp_path,monkeypatch):
    capture(state);ledger=tmp_path/'fail.db'
    physical_snapshot(ledger)
    with sqlite3.connect(ledger) as con:
        con.execute("CREATE TRIGGER fault BEFORE INSERT ON observations_v2 WHEN (SELECT count(*) FROM observations_v2)=3 BEGIN SELECT RAISE(ABORT,'fault'); END")
    monkeypatch.setattr(publication,'_now',lambda:pytest.fail('failed transaction cannot publish'))
    with pytest.raises(sqlite3.DatabaseError,match='fault'): admit(state,ledger)
    rows,_=observation_snapshot(ledger)
    assert not rows and not rows._receipts


def test_delayed_publication_blocks_mechanics_and_pm(state,tmp_path,monkeypatch):
    capture(state);ledger=tmp_path/'late.db';D=S+timedelta(hours=1)
    monkeypatch.setattr(publication,'_now',lambda:D+timedelta(seconds=1))
    admit(state,ledger)
    assert not build_causal_mechanics(ledger,dataset_role='PILOT',cutoff=D)['raw_values']
    with pytest.raises(ValueError,match='no causal evidence'):
        append_causal_mechanics(ledger,dataset_role='PILOT',cutoff=D,clock=lambda:D)
    # Even a later valid Mechanics observation cannot satisfy the frozen S+5m raw gate.
    late=D+timedelta(seconds=2)
    mech=append_causal_mechanics(ledger,dataset_role='PILOT',cutoff=late,clock=lambda:late)
    with pytest.raises(ValueError): derived(ledger,role='PILOT',decision_at=D,mechanics_id=mech['id'])
    rows,_=observation_snapshot(ledger)
    assert not any(metrics_snapshot_available(rows,i,D) for i in rows if rows[i]['feature'].startswith('MarketMetrics/'))


def test_later_append_does_not_change_historical_eligibility(published,state,monkeypatch):
    ledger,_=published;D=S+timedelta(minutes=5)
    before=load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=D)
    capture(state,slot=S+timedelta(hours=1))
    monkeypatch.setattr(publication,'_now',lambda:S+timedelta(hours=1,minutes=4))
    admission.admit_verified_metrics_bundle(ledger,state[0],S+timedelta(hours=1),repo_root=state[1],
        now=S+timedelta(hours=1,minutes=4),clock=lambda:S+timedelta(hours=1,minutes=4))
    assert load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=D)==before


def test_historical_v1_bytes_unchanged_no_retrofit(state,tmp_path,monkeypatch):
    capture(state);ledger=tmp_path/'historical.db'
    with monkeypatch.context() as m:
        m.setattr(admission,'ADMISSION_CONTRACT','metrics-observations-v2-admission-v1')
        m.setattr(publication,'_publish_committed',lambda *a:(_ for _ in ()).throw(RuntimeError('old boundary')))
        with pytest.raises(RuntimeError): admit(state,ledger)
    before=ledger.read_bytes()
    rows,_=observation_snapshot(ledger)
    assert len(rows)==6 and not rows._receipts
    assert not any(metrics_snapshot_available(rows,i,S+timedelta(hours=2)) for i in rows)
    with pytest.raises(ValueError): admit(state,ledger)
    assert ledger.read_bytes()==before


def test_forged_publication_cannot_enter_public_gate(published):
    ledger,result=published;rows,_=observation_snapshot(ledger)
    fake=deepcopy(result['publication']);fake['published_at']=S.isoformat()
    with pytest.raises(AttributeError): rows._receipts=(canonical_observation(fake),)
    untrusted=dict(rows)
    for row in untrusted.values(): row['provenance']['durable_publication']=fake
    assert not any(metrics_snapshot_available(untrusted,i,S+timedelta(hours=1)) for i in untrusted)


def test_raw_capture_alone_never_authorizes_rows(state,tmp_path):
    capture(state)
    ledger=tmp_path/'raw-only.db'
    physical_snapshot(ledger)
    assert not load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=S+timedelta(hours=1)).observations


def test_pm_prm_enforce_raw_cutoff_even_when_mechanics_precedes_decision(state,tmp_path,monkeypatch):
    capture(state);ledger=tmp_path/'raw-cutoff.db'
    late=S+timedelta(minutes=6)
    monkeypatch.setattr(publication,'_now',lambda:late)
    admit(state,ledger)
    mech=append_causal_mechanics(ledger,dataset_role='PILOT',cutoff=late,clock=lambda:late)
    with pytest.raises(ValueError,match='INVALID_BUNDLE_ROLE_SLOT_OR_CAUSALITY'):
        derived(ledger,role='PILOT',decision_at=S+timedelta(hours=1),mechanics_id=mech['id'])
