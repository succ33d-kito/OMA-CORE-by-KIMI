"""Synthetic fixtures only: these tests are not prospective execution evidence."""
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
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
