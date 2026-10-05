"""Synthetic fixtures only: these tests are not prospective execution evidence."""
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from datetime import timedelta
import pytest
from core.scientific import execution_position_plane as e
from core.scientific import trading_decision_plane as t
from tests.test_trading_decision_plane import shadow


def plan(tmp_path, monkeypatch):
    d = shadow(tmp_path, monkeypatch)
    return e.ExecutionPlan(d, d.allocation.rows[0].candidate_id, e.Mode.SHADOW)


def test_plan_missing_conversion_is_not_zero(tmp_path, monkeypatch):
    p = plan(tmp_path, monkeypatch)
    assert p.state is e.PlanState.NO_ORDER
    assert p.notional_usd is None
    assert p.reason == 'MISSING_FACTUAL_RISK_TO_NOTIONAL_CONVERSION'
    assert replace(p) == p
    assert p.role == p.decision.role
    with pytest.raises(FrozenInstanceError): p.reason = 'executed'


def test_plan_rejects_tamper_live_and_foreign_candidate(tmp_path, monkeypatch):
    p = plan(tmp_path, monkeypatch)
    with pytest.raises(TypeError): replace(p, mode='LIVE')
    with pytest.raises(ValueError): replace(p, candidate_id='unknown')
    object.__setattr__(p.decision, 'decision_id', 'f'*64)
    with pytest.raises(ValueError): replace(p)


def notional_plan(tmp_path, monkeypatch):
    d = shadow(tmp_path, monkeypatch)
    old = d.allocation
    port = replace(old.portfolio, available_risk_budget=t.CapitalAmount(t.CapitalUnit.USD_NOTIONAL, Decimal('10')))
    auths = tuple(t.authorize_risk(a.candidate,a.world,port,
        replace(a.request,risk=t.CapitalAmount(t.CapitalUnit.USD_NOTIONAL,Decimal('3'))),
        replace(a.policy,unit=t.CapitalUnit.USD_NOTIONAL),kill_switch=False,available_at=d.available_at)
        for a in old.authorizations)
    alloc = t.allocate_capital(old.ranking,port,auths,t.CapitalAmount(t.CapitalUnit.USD_NOTIONAL,Decimal('3')),old.policy,available_at=d.available_at)
    d = replace(d,allocation=alloc)
    return e.ExecutionPlan(d,d.allocation.rows[0].candidate_id,e.Mode.SHADOW)


def test_notional_is_not_venue_quantity(tmp_path, monkeypatch):
    p = notional_plan(tmp_path, monkeypatch)
    assert p.state is e.PlanState.READY and p.notional_usd == Decimal('2')
    assert p.reason == 'AUTHORIZED_NOTIONAL_ONLY_NOT_VENUE_QUANTITY'
    assert replace(p,mode=e.Mode.PAPER).plan_id != p.plan_id


def test_intent_cannot_invent_venue_parameters_or_fill(tmp_path, monkeypatch):
    p = notional_plan(tmp_path, monkeypatch)
    intent = e.OrderIntent(p)
    assert intent.quantity_unit == 'USD_NOTIONAL' and intent.quantity == p.notional_usd
    assert not intent.actionable and intent.direction is t.Direction.LONG
    assert intent.mode is e.Mode.SHADOW and replace(intent) == intent
    with pytest.raises(TypeError): replace(intent, fill_price=Decimal('1'))
    with pytest.raises(ValueError): replace(intent, actionable=True)
    with pytest.raises(ValueError): e.OrderIntent(plan(tmp_path/'risk', monkeypatch))


def gate(p, **changes):
    args = dict(registered_at=p.decision.world.as_of,max_book_age_seconds=Decimal('10000'),max_relative_spread=Decimal('1'))
    args.update(changes)
    return e.ExecutionQualityGate(p.decision,p.candidate_id,e.QualityPolicy(**args))


def test_quality_causal_limits_unknown_and_rejection(tmp_path, monkeypatch):
    p = plan(tmp_path, monkeypatch)
    assert gate(p).state is e.QualityState.PASS
    assert gate(p,max_relative_spread=None).state is e.QualityState.DEFER
    assert gate(p,max_relative_spread=Decimal('0')).state is e.QualityState.REJECT
    with pytest.raises(ValueError): gate(p,registered_at=p.available_at+timedelta(seconds=1))
    with pytest.raises(TypeError): replace(gate(p),pnl=1)
    assert replace(gate(p)) == gate(p)


def test_estimate_unknowns_never_become_zero_or_funding_payment(tmp_path, monkeypatch):
    p = plan(tmp_path, monkeypatch)
    estimate = e.ExecutionEstimate(gate(p))
    assert estimate.reference_quote_usdt_per_base > 0
    assert estimate.spread_usdt_per_base > 0
    for name in ('slippage_usdt_per_base','fee_usdt','funding_cashflow_usdt','latency_seconds','depth_base'):
        assert getattr(estimate,name) is None
        with pytest.raises(ValueError): replace(estimate,**{name:Decimal('0')})
    assert e.ExecutionEstimate(gate(p,max_relative_spread=None)).reference_quote_usdt_per_base is None
    with pytest.raises(TypeError): replace(estimate,realized_pnl=1)
    assert replace(estimate) == estimate


def position(tmp_path, monkeypatch, mode=e.Mode.SHADOW):
    p = replace(notional_plan(tmp_path,monkeypatch),mode=mode)
    return e.PositionState(e.OrderIntent(p),p.available_at,p.available_at)


@pytest.mark.parametrize('mode', list(e.Mode))
def test_position_is_pending_not_filled_in_either_mode(tmp_path, monkeypatch, mode):
    p = position(tmp_path,monkeypatch,mode)
    assert p.phase is e.PositionPhase.PENDING_EXECUTION
    assert p.filled_quantity_base is None and p.entry_execution_ref is None
    assert p.entry_price_usdt_per_base is None and p.mode is mode
    assert p.thesis_id in {t.thesis_id for t in p.intent.plan.decision.theses}
    with pytest.raises(ValueError): replace(p,filled_quantity_base=Decimal('1'))
    with pytest.raises(TypeError): replace(p,intent=e.ExecutionEstimate(gate(p.intent.plan)))
    with pytest.raises(ValueError): replace(p,created_at=p.created_at-timedelta(seconds=1))
    assert replace(p) == p


def test_lifecycle_causal_role_bound_and_not_performance(tmp_path, monkeypatch):
    p = position(tmp_path,monkeypatch)
    w = p.intent.plan.decision.world
    a = e.ThesisLifecycle(p,w,w.as_of)
    assert a.state is e.ThesisState.ACTIVE and replace(a) == a
    assert 'NO_SUPPORTED_INVALIDATION' in a.reason
    with pytest.raises(ValueError): replace(a,assessed_at=w.as_of-timedelta(seconds=1))
    with pytest.raises(TypeError): replace(a,pnl=100)
    with pytest.raises(ValueError): replace(a,world=replace(w,universe_id='f'*64))
    assert set(e.ThesisState) == {e.ThesisState.ACTIVE,e.ThesisState.EXECUTION_RISK,e.ThesisState.TIMEOUT}
