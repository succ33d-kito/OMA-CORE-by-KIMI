from dataclasses import replace
from decimal import Decimal
import pytest
from core.scientific import execution_position_plane as e
from core.scientific.shadow_execution_intent_runner import run_shadow_intents
from tests.test_execution_position_plane import plan, notional_plan, gate
from core.scientific import trading_decision_plane as t


def test_opt_in_replay_no_order_and_immutable_decision(tmp_path,monkeypatch):
    p = plan(tmp_path/'inputs',monkeypatch)
    output = tmp_path/'output'
    with pytest.raises(ValueError): run_shadow_intents(p.decision,gate(p).policy,output)
    assert not output.exists()
    before = p.decision.decision_id
    first = run_shadow_intents(p.decision,gate(p).policy,output,enabled=True)
    assert all(r['status']=='NO_ORDER' for r in first['payload']['rows'])
    assert all(r['position_id'] is None for r in first['payload']['rows'])
    path = output/(first['run_id']+'.json')
    timestamp = path.stat().st_mtime_ns
    assert run_shadow_intents(p.decision,gate(p).policy,output,enabled=True)==first
    assert path.stat().st_mtime_ns==timestamp and p.decision.decision_id==before
    path.write_bytes(b'incomplete')
    with pytest.raises(ValueError): run_shadow_intents(p.decision,gate(p).policy,output,enabled=True)
    assert path.read_bytes()==b'incomplete'


@pytest.mark.parametrize('limit,status',[(None,'DEFER'),(Decimal('0'),'REJECT'),(Decimal('1'),'NO_ORDER')])
def test_gate_controls_runner_without_fabricating_fill(tmp_path,monkeypatch,limit,status):
    p = notional_plan(tmp_path/'inputs',monkeypatch)
    result = run_shadow_intents(p.decision,gate(p,max_relative_spread=limit).policy,tmp_path/'out',enabled=True)
    assert all(r['status']==status for r in result['payload']['rows'])
    assert all(r['position_id'] is None and r['lifecycle_assessment_id'] is None for r in result['payload']['rows'])
    for row in result['payload']['rows']:
        if row['intent'] is not None: assert row['intent']['actionable'] is False
    assert result['payload']['mode']=='SHADOW'


@pytest.mark.parametrize('kind,expected',[('halt','HALTED'),('unknown','DEFERRED'),('cash','WOULD_ABSTAIN'),('reject','RISK_REJECTED')])
def test_runner_preserves_upstream_nonallocation(tmp_path,monkeypatch,kind,expected):
    p = plan(tmp_path/'input',monkeypatch)
    old = p.decision.allocation
    auths = tuple(t.authorize_risk(a.candidate,a.world,a.portfolio,a.request,
        replace(a.policy,max_positions=0) if kind=='reject' else a.policy,
        kill_switch=True if kind=='halt' else None if kind=='unknown' else False,
        available_at=a.available_at) for a in old.authorizations)
    budget = replace(old.budget,value=Decimal('0')) if kind=='cash' else old.budget
    allocation = t.allocate_capital(old.ranking,old.portfolio,auths,budget,old.policy,available_at=old.available_at)
    decision = replace(p.decision,allocation=allocation)
    result = run_shadow_intents(decision,gate(p).policy,tmp_path/'out',enabled=True)
    assert result['payload']['upstream_state']==expected
    assert all(row['intent'] is None for row in result['payload']['rows'])
    assert {row['reason'] for row in result['payload']['rows']}=={row.reason for row in allocation.rows}
