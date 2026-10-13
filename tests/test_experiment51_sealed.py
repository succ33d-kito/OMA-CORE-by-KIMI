from datetime import timedelta
from dataclasses import replace
from pathlib import Path
import json
import pytest
from core.scientific import experiment51_sealed as s
from core.scientific import event_direction_operator as operator
from core.scientific import real_event_receipt as ev
from core.scientific.nuisance_pilot_contracts import DatasetRole,digest
from tests.test_real_event_receipt import setup_store,T
from tests.test_event_direction_v1 import controls


@pytest.fixture
def phase(tmp_path,monkeypatch):
    store,clock=setup_store(tmp_path,monkeypatch)
    root=tmp_path/'authority'
    operator.activate(root,tmp_path/'events.sqlite',role=DatasetRole.DISCOVERY)
    path=tmp_path/'phase.sqlite'
    config=s.activate_phase(path,operator_root=root,ledger=tmp_path/'ledger',controls=controls(),owner_authorization='SYNTHETIC OWNER FIXTURE')
    return path,clock,config


def test_prospective_phase_fixed_and_no_reactivation(phase):
    path,clock,p=phase
    assert s._utc(p['start'])>clock['now']
    assert s._utc(p['end'])-s._utc(p['start'])==2160*s.HOUR
    with pytest.raises(FileExistsError): s.activate_phase(path,operator_root=p['operator_root'],ledger=p['ledger'],controls=controls(),owner_authorization='again')
    with pytest.raises(TypeError): s.activate_phase(path,operator_root=p['operator_root'],ledger=p['ledger'],controls=controls(),owner_authorization='x',start=T)


def test_no_discovery_from_pilot(tmp_path,monkeypatch):
    store,clock=setup_store(tmp_path,monkeypatch)
    root=tmp_path/'authority';operator.activate(root,tmp_path/'events.sqlite',role=DatasetRole.PILOT)
    with pytest.raises(ValueError): s.activate_phase(tmp_path/'phase',operator_root=root,ledger=tmp_path/'none',controls=controls(),owner_authorization='fixture')
    assert not (tmp_path/'phase').exists()


def test_no_implicit_authorization(tmp_path):
    with pytest.raises(ValueError): s.activate_phase(tmp_path/'phase',operator_root=tmp_path/'a',ledger=tmp_path/'l',controls=controls(),owner_authorization='')
    assert not (tmp_path/'phase').exists()


def test_real_missing_binding_firewall_and_readonly(phase):
    path,clock,p=phase;before=path.read_bytes();calls=[]
    result=s.readiness(path,controls())
    assert result['experiment_51_ready'] is False
    with pytest.raises(ValueError): s.run(path,controls(),outcome_loader=lambda *a:calls.append(a))
    assert calls==[] and path.read_bytes()==before


@pytest.mark.parametrize('field,value',[('prereg','bad'),('rules',[]),('role','PILOT'),('family','bad'),('authority_id','bad'),('activation_id','bad'),('controls_id','bad'),('end',T.isoformat())])
def test_phase_mismatch_firewall_even_with_rehashed_content(phase,field,value):
    import sqlite3
    path,clock,p=phase
    with sqlite3.connect(path) as con:
        row=json.loads(con.execute('SELECT body FROM event_journal WHERE seq=1').fetchone()[0])
        row['data'][field]=value;body=ev._json(row)
        con.execute('UPDATE event_journal SET body=?,hash=? WHERE seq=1',(body,digest(('0'*64,body))))
    calls=[]
    with pytest.raises((ValueError,KeyError)): s.run(path,controls(),outcome_loader=lambda *a:calls.append(a))
    assert calls==[]


@pytest.mark.parametrize('reason',['READINESS_FALSE','COMMON_SUPPORT_MISMATCH','POPULATION_MISMATCH','EVENT_BINDING_MISMATCH','DERIVED_INPUT_MISMATCH','TAMPERED_INPUT'])
def test_gateway_never_invokes_loader_after_gate_rejection(phase,monkeypatch,reason):
    path,_,_=phase;calls=[]
    def reject(*args): raise ValueError(reason)
    monkeypatch.setattr(s,'_gates',reject)
    with pytest.raises(ValueError,match=reason): s.run(path,controls(),outcome_loader=lambda *a:calls.append(a))
    assert calls==[]


def test_authorization_is_durable_before_injected_loader(phase,monkeypatch):
    path,clock,p=phase
    ev.RealEventStore(path)._append('binding',{'synthetic_firewall_fixture':True},lambda rows,at:None)
    rows=ev.RealEventStore(path,read_only=True)._rows()
    monkeypatch.setattr(s,'_gates',lambda *a:(rows,p,[],True))
    monkeypatch.setattr(s,'_analyze',lambda *a:{'fixture':True})
    def loader(*args):
        assert ev.RealEventStore(path,read_only=True)._rows()[-1]['kind']=='authorized_run'
        return {}
    assert s.run(path,controls(),outcome_loader=loader)['evidence_kind']=='INJECTED_NOT_REAL'
    # Concurrent-state check stops a retry even if a caller supplies stale gate state.
    with pytest.raises(ValueError): s.run(path,controls(),outcome_loader=loader)


def test_boundary_purge_half_open(phase):
    from types import SimpleNamespace
    _,_,p=phase;start=s._utc(p['start']);end=s._utc(p['end'])
    assert s._member(p,SimpleNamespace(decision_at=start))
    assert s._member(p,SimpleNamespace(decision_at=end-9*s.HOUR))
    assert not s._member(p,SimpleNamespace(decision_at=end-8*s.HOUR))
    assert not s._member(p,SimpleNamespace(decision_at=start-s.HOUR))


@pytest.mark.skipif(__import__('os').name!='nt',reason='Existing atomic Metrics activation fixture is Windows-only')
def test_real_binding_reconstructs_every_gate_before_loader(tmp_path,monkeypatch):
    import tests.test_price_role_attestation as pf
    from tests.test_role_price_window import window
    from tests.test_metrics_continuity import S
    from tests.test_causal_latent_context import admit_metrics
    from tests.test_real_event_receipt import evidence
    from tests.test_event_direction_v1 import claim
    from core.scientific.metrics_h1_activation import activate
    from core.scientific.role_price_window import certify_role_price_window
    from core.scientific.causal_regime import append_causal_regime
    from core.scientific.causal_mechanics import append_causal_mechanics
    original=pf.create_activation
    monkeypatch.setattr(pf,'create_activation',lambda *a,**kw:original(*a,**{**kw,'role':'DISCOVERY'}))
    monkeypatch.setattr(pf,'T',S-timedelta(hours=80))
    ledger,ids,cutoff,_=window.__wrapped__(tmp_path,monkeypatch)
    cert=certify_role_price_window(ledger,receipt_ids=ids,dataset_role='DISCOVERY',cutoff=cutoff)
    regime=append_causal_regime(ledger,cert,clock=lambda:cutoff+timedelta(seconds=1))
    repo=tmp_path/'metricsrepo';repo.mkdir();metrics=tmp_path/'metrics-h1-v1'
    activate(metrics,repo_root=repo,now=S-timedelta(minutes=20),dataset_role='DISCOVERY')
    admit_metrics((metrics,repo),ledger)
    mech=append_causal_mechanics(ledger,dataset_role='DISCOVERY',cutoff=S+timedelta(minutes=5),clock=lambda:S+timedelta(minutes=5))
    store,clock=setup_store(tmp_path,monkeypatch);D=S+timedelta(hours=1)
    clock['now']=D-timedelta(minutes=40)
    root=tmp_path/'eventauthority';operator.activate(root,tmp_path/'events.sqlite',role=DatasetRole.DISCOVERY)
    phase=tmp_path/'realphase.sqlite'
    config=s.activate_phase(phase,operator_root=root,ledger=ledger,controls=controls(),owner_authorization='SYNTHETIC TEST ONLY')
    clock['now']=D-timedelta(minutes=20);clock['raw']=b'Bitcoin announcement. Actor commits to Bitcoin action.'
    receipt=store.capture('official','v1',DatasetRole.DISCOVERY);store.admit(receipt.receipt_id,evidence())
    operator.attest(root,receipt.receipt_id,claim(),role=DatasetRole.DISCOVERY)
    clock['now']=D;store.close(D)
    decision=s.record_opportunity(phase,controls(),receipt.receipt_id,regime_id=regime['id'],mechanics_id=mech['id'])
    assert decision==s.record_opportunity(phase,controls(),receipt.receipt_id,regime_id=regime['id'],mechanics_id=mech['id'])
    clock['now']=s._utc(config['end']);store.close(clock['now'])
    s.bind_experiment(phase,controls())
    clock['now']+=8*s.HOUR
    before={str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    status=s.readiness(phase,controls())
    assert status['common_support_count']==1 and not status['experiment_51_ready']
    calls=[]
    with pytest.raises(ValueError,match='READINESS_FALSE'): s.run(phase,controls(),outcome_loader=lambda *a:calls.append(a))
    assert calls==[]
    assert before=={str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    # Corrupt actual official manifest; integrity failure cannot become innocent abstention.
    manifest=Path(str(phase)+'.official')/'manifest.json';manifest.write_text('{}')
    with pytest.raises(ValueError): s.run(phase,controls(),outcome_loader=lambda *a:calls.append(a))
    assert calls==[]



def test_statistics_frozen_cost_and_secondary_no_rescue(monkeypatch):
    from types import SimpleNamespace
    from core.scientific.experiment51_preparation import load_protocol
    op=SimpleNamespace(opportunity_id='fixture',decision_at=T)
    bodies=tuple(dict(policy=name,action=action) for name,action in zip(('P0','PR','PM','PRM'),('LONG','ABSTAIN','SHORT','LONG')))
    selected=[(op,None,None,bodies)];calls=[]
    def intervals(calendar,spec):
        assert spec==load_protocol()['uncertainty']
        calls.append(calendar[0][0])
        return ((-3,1),)*3 if len(calls)==1 else ((3,5),)*3
    monkeypatch.setattr(s,'_basic_intervals',intervals)
    result=s._analyze({'start':T.isoformat()},selected,{'fixture':{1:.001,4:.001,8:.001}},'synthetic')
    # P0: 10-10=0, PR abstain=0, PM: -10-10=-20, PRM=0.
    assert calls[0]==(0,-20,0)
    assert all(v['verdict']=='FAIL' for v in result['primary'].values())
    assert all(v['verdict']=='PASS' for v in result['exploratory'][1].values())
    assert result['policy_winner'] is None and result['confirmation_required']


def test_readiness_wrong_phase_is_false_without_writes(tmp_path):
    path=tmp_path/'absent'
    assert s.readiness(path,controls())['experiment_51_ready'] is False
    assert not path.exists()



def test_outcome_reader_requires_private_authorization_before_io(tmp_path):
    with pytest.raises(ValueError,match='OUTCOME_ACCESS_NOT_AUTHORIZED'):
        s._load_labels(tmp_path/'does-not-exist',(),(1,4,8))
    with pytest.raises(ValueError): s._OutcomePermit(object())
    assert not (tmp_path/'does-not-exist').exists()
