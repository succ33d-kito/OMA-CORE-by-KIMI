from datetime import datetime, timedelta, timezone
from pathlib import Path
import ast
import json
import socket
import pytest
from core.scientific import experiment51_readiness as r
from core.scientific import experiment51_preparation as h
from tests.test_price_role_h1_runner import env, S, REPO
from tests.test_metrics_continuity import state, capture, snapshot

T = datetime(2026,10,12,tzinfo=timezone.utc)


def row(n, status='VALID', **changes):
    t=T+timedelta(hours=n)
    return dict(slot=t.isoformat(), status=status, role='PILOT', available_at=(t+timedelta(minutes=3)).isoformat(), **changes)


def test_total_is_not_suffix_missing_slot_breaks():
    result=r.summarize([row(0),row(1),row(3)])
    assert result['total_valid_h1']==3 and result['consecutive_valid_h1']==1
    assert result['gaps']==[(T+timedelta(hours=2)).isoformat()]
    assert r.summarize([row(0),row(1,'FAILED')])['consecutive_valid_h1']==0


@pytest.mark.parametrize('status',['UNKNOWN','MISSING','LATE','CONFLICT','FAILED','INVALID','INCOMPLETE'])
def test_no_nonvalid_promoted(status):
    result=r.intersection({'price':[row(0)],'metrics':[row(0,status)]})
    assert result['total_valid_h1']==0
    assert result['exclusion_counts']=={'METRICS:'+status:1}


def test_exact_intersection_order_role_future():
    streams={'price':[row(0),row(1),row(2)],'metrics':[row(2),row(0)]}
    a=r.intersection(streams)
    assert a==r.intersection(dict(reversed(list(streams.items()))))
    assert a['total_valid_h1']==2 and a['consecutive_valid_h1']==1
    for field,value in [('role','CONFIRMATION'),('available_at',(T+timedelta(minutes=6)).isoformat()),('available_at',None)]:
        bad=dict(row(0),**{field:value})
        assert r.intersection({'price':[row(0)],'metrics':[bad]})['total_valid_h1']==0


def test_invalid_identities():
    with pytest.raises(ValueError): r.summarize([row(0),row(0)])
    with pytest.raises(ValueError): r.utc(T.replace(tzinfo=None))
    with pytest.raises(ValueError): r.summarize([dict(row(0),slot=(T+timedelta(seconds=1)).isoformat())])


def test_price_actual_pair_readonly_no_network(env,monkeypatch):
    assert env.run()['status']=='SUCCESS'
    before=snapshot(env.root)
    monkeypatch.setattr(socket.socket,'connect',lambda *a:pytest.fail('network forbidden'))
    result=r._price(env.root,REPO,S+timedelta(minutes=5),S)
    assert result['total_valid_h1']==result['consecutive_valid_h1']==1
    assert result['regime_input_slots']==[]
    assert snapshot(env.root)==before


def test_failed_price_excluded_even_with_pair(env):
    env.run()
    from core.scientific import price_role_h1_runner as p
    p._record(env.root,env.config,S,'CAPTURE_FAILED',env.t,reason='fixture conflict')
    assert r._price(env.root,REPO,S+timedelta(minutes=5),S)['total_valid_h1']==0


def test_missing_attestation_excluded(env):
    env.run()
    from core.scientific import price_role_h1_runner as p
    # Altered read snapshot is a fixture, never a real ledger rewrite.
    known=p._rows(env.root)
    known={k:v for k,v in known.items() if v['feature']=='Price/OHLCV'}
    from unittest.mock import patch
    with patch.object(p,'_rows',return_value=known):
        result=r._price(env.root,REPO,S+timedelta(minutes=5),S)
    assert result['total_valid_h1']==0


@pytest.mark.skipif(__import__('os').name!='nt',reason='Metrics fixture activation is an existing Windows-only contract')
def test_atomic_metrics_and_corruption_readonly(state):
    from tests.test_metrics_continuity import S as MS
    capture(state)
    before=snapshot(state[0])
    assert r._metrics(*state,MS+timedelta(minutes=5),MS)['total_valid_h1']==1
    assert snapshot(state[0])==before
    (state[0]/'attempts'/MS.strftime('%Y%m%dT%H0000Z')/'capture'/'raw'/'oi.json').write_text('{}')
    before=snapshot(state[0])
    assert r._metrics(*state,MS+timedelta(minutes=5),MS)['total_valid_h1']==0
    assert snapshot(state[0])==before


def test_missing_states_no_initialization(tmp_path,monkeypatch):
    monkeypatch.setattr(socket.socket,'connect',lambda *a:pytest.fail('network forbidden'))
    before=snapshot(tmp_path)
    result=r.check_readiness(price_state=tmp_path/'price-role-h1-v1',metrics_state=tmp_path/'metrics-h1-v1',
                            funding_state=tmp_path/'funding-h1-v1',repo_root=REPO,checked_at=T)
    assert not result['experiment_51_ready'] and not result['mechanics_input_ready']
    assert snapshot(tmp_path)==before
    assert 'aggressor_flow' in result['unknown_mechanics_dimensions']


def test_readiness_source_no_predictive_dependencies():
    source=Path(r.__file__).read_text(encoding='utf-8-sig')
    tree=ast.parse(source)
    imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any(any(word in x.lower() for word in ('outcome','pnl','backtest','preparation')) for x in imports)
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('write_text','write_bytes','mkdir','unlink','append_observation','attempt_slot') for n in ast.walk(tree))


def test_prereg_exante_horizons_hash():
    p=h.load_protocol()
    assert p['primary_horizon_hours']==4 and p['secondary_horizons_hours']==[1,8]
    assert p['PRIMARY_HORIZON_SELECTED_EX_ANTE'] is True
    assert p['PRIMARY_HORIZON_SELECTED_FROM_RESULTS'] is False
    assert p['PRIMARY_HORIZON_INHERITED_AUTOMATICALLY'] is False
    assert p['uncertainty']['block_hours']==168
    assert h.commitment(p)==h.commitment(dict(reversed(list(p.items()))))


def test_same_population_required():
    with pytest.raises(ValueError): h._paired(('a',),{'P0':{'a':1},'PR':{},'PM':{'a':2},'PRM':{'a':2}})
    with pytest.raises(ValueError): h._paired(('a','a'),{})


def test_existing_kernel_support_reused():
    from tests.test_common_support import opportunity, controls, form
    from core.scientific.common_support import CommonSupportRegistry
    reg=CommonSupportRegistry(); op=opportunity()
    reg.register(op,controls(),form(op))
    frozen,ids=h.bind_support(reg)
    assert ids==(op.opportunity_id,) and len(frozen)==64
    with pytest.raises(TypeError): h.bind_support({'cs4':True})


def test_synthetic_receipt_deterministic_no_real_claim():
    first=h.synthetic_smoke(); second=h.synthetic_smoke()
    assert first==second and first.receipt_id==second.receipt_id
    body=json.loads(first.canonical_json)
    assert body['real_experiment'] is False and body['policy_winner'] is None
    assert body['research_verdict']=='NOT_EVALUATED_SYNTHETIC'
    with pytest.raises(TypeError): h.synthetic_smoke(outcomes=[1])


def test_block_degeneracy_not_pass():
    p=h.load_protocol()['uncertainty']
    assert h._basic_intervals(tuple(((0,0,0),) for _ in range(168)),p)==(None,None,None)


def test_even_complete_capture_cannot_authorize_experiment(monkeypatch):
    def reader(*args):
        return dict(r.summarize([row(0)]),regime_input_slots=[T.isoformat()])
    for name in ('_price','_metrics','_funding'): monkeypatch.setattr(r,name,reader)
    result=r.check_readiness(price_state='unused',metrics_state='unused',funding_state='unused',repo_root=REPO,checked_at=T+timedelta(minutes=5))
    assert result['regime_input_ready'] and result['mechanics_capture_input_ready']
    assert not result['mechanics_input_ready'] and not result['experiment_51_ready']
    assert result['blockers']


def test_pending_slot_not_called_missing(monkeypatch):
    seen=[]
    def reader(state,repo,now,end):
        seen.append(end)
        return r.summarize([])
    for name in ('_price','_metrics','_funding'): monkeypatch.setattr(r,name,reader)
    r.check_readiness(price_state='x',metrics_state='y',funding_state='z',repo_root=REPO,checked_at=T+timedelta(seconds=299))
    assert seen==[T-timedelta(hours=1)]*3


def test_price_success_schema_fails_closed(env):
    env.run()
    from core.scientific import price_role_h1_runner as p
    path=p._directory(env.root,S)/'SUCCESS.json'
    body=json.loads(path.read_bytes());body['status']='UNKNOWN';body.pop('record_id')
    body['record_id']=p.observation_hash(body)
    path.write_bytes(p.roles._canonical(body))
    before=snapshot(env.root)
    assert r._price(env.root,REPO,S+timedelta(minutes=5),S)['total_valid_h1']==0
    assert snapshot(env.root)==before


def test_corrupt_ledger_reported_fail_closed(tmp_path,monkeypatch):
    import sqlite3
    def broken(*args): raise sqlite3.DatabaseError('fixture')
    monkeypatch.setattr(r,'_price',broken)
    result=r.check_readiness(price_state=tmp_path,metrics_state=tmp_path/'metrics-h1-v1',funding_state=tmp_path/'funding-h1-v1',repo_root=REPO,checked_at=T)
    assert result['price']['verification']=='FAILED_CLOSED'
    assert not result['regime_input_ready']


def test_funding_role_rate_and_future_availability(tmp_path,monkeypatch):
    from core.scientific import funding_h1_runner as runner, funding_continuity as fc, premium_index_capture as capture_module
    from types import SimpleNamespace
    monkeypatch.setattr(runner,'load_config',lambda state:{'activation_slot':T.isoformat()})
    monkeypatch.setattr(fc,'status',lambda *a:dict(records=[dict(slot=T.isoformat(),status='SUCCESS')],structural_invalid=[],integrity='PASS'))
    monkeypatch.setattr(fc,'_read_json',lambda path:{'completed_at':(T+timedelta(minutes=7)).isoformat()})
    monkeypatch.setattr(capture_module,'load_premium',lambda path:SimpleNamespace(receipts=[SimpleNamespace(available_at=T+timedelta(minutes=6))]))
    report=r._funding(tmp_path,REPO,T+timedelta(minutes=8),T)
    assert report['total_valid_h1']==0
    assert report['semantics']=='PUBLISHED_RATE_NOT_REALIZED_PAYMENT'
    assert 'PILOT' in report['role_authority']
