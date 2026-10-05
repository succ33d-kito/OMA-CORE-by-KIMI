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


def notional_plan(tmp_path, monkeypatch, *, incumbent=False):
    d = shadow(tmp_path, monkeypatch)
    old = d.allocation
    port = replace(old.portfolio, available_risk_budget=t.CapitalAmount(t.CapitalUnit.USD_NOTIONAL, Decimal('10')))
    if incumbent:
        exposure = replace(old.authorizations[0].request,risk=t.CapitalAmount(t.CapitalUnit.USD_NOTIONAL,Decimal('1')))
        port = replace(port,positions=(exposure,))
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
    assert intent.side is e.Side.BUY
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


def test_exit_intent_does_not_close_position(tmp_path, monkeypatch):
    p = position(tmp_path,monkeypatch)
    w = p.intent.plan.decision.world
    with pytest.raises(ValueError): e.ExitIntent(e.ThesisLifecycle(p,w,w.as_of))
    missing = replace(w,markets=tuple(replace(m,book=None,book_age_seconds=None) if m.symbol==p.instrument else m for m in w.markets))
    assessment = e.ThesisLifecycle(p,missing,missing.as_of)
    assert assessment.state is e.ThesisState.EXECUTION_RISK
    intent = e.ExitIntent(assessment)
    assert not intent.actionable and intent.position == p
    assert p.phase is e.PositionPhase.PENDING_EXECUTION and p.entry_execution_ref is None
    assert intent.reason == 'MISSING_CAUSAL_BOOK' and replace(intent) == intent
    with pytest.raises(TypeError): replace(intent,fill_price=Decimal('1'))


def test_reallocation_reauthorizes_and_stale_risk_cannot_trade(tmp_path, monkeypatch):
    p = plan(tmp_path,monkeypatch)
    a = e.Reallocation(p.decision,p.available_at)
    assert a.state is e.ReallocationState.REAUTHORIZED_ADDITIONS_ONLY
    t.verify_allocation(a.allocation)
    assert a.opportunity_cost_usd is None
    stale = replace(a,available_at=p.available_at+timedelta(seconds=20000))
    assert all(r.amount.value == 0 for r in stale.allocation.rows)
    assert stale.allocation.unallocated == p.decision.allocation.budget
    with pytest.raises(ValueError): replace(a,available_at=p.available_at-timedelta(seconds=1))
    with pytest.raises(TypeError): replace(a,expected_pnl=Decimal('10'))


def test_reallocation_matching_incumbent_id_is_not_comparable_basis(tmp_path, monkeypatch):
    p = notional_plan(tmp_path,monkeypatch,incumbent=True)
    a = e.Reallocation(p.decision,p.available_at)
    assert a.state is e.ReallocationState.DEFER and a.allocation is None
    assert a.reason == 'MISSING_COMMON_INCUMBENT_COMPARISON_BASIS'
    assert a.opportunity_cost_usd is None


def test_attribution_schema_unknown_is_not_zero_or_learning(tmp_path, monkeypatch):
    p = plan(tmp_path,monkeypatch)
    parts = tuple(e.AttributionComponent(k,None,(),None) for k in e.ContributionKind)
    schema = e.AttributionSchema(p.plan_id,p.available_at,parts)
    assert all(c.value_usd is None for c in schema.components)
    assert 'UNVERIFIED_NOT_EDGE' in schema.status
    assert replace(schema,components=parts[::-1]) == schema
    with pytest.raises(ValueError): replace(schema,components=parts[:-1])
    with pytest.raises(ValueError): replace(parts[0],value_usd=Decimal('0'))
    with pytest.raises(TypeError): e.ExecutionPlan(schema,p.candidate_id,e.Mode.SHADOW)


def test_adversarial_book_future_materialized_quote_and_naive(tmp_path, monkeypatch):
    p = plan(tmp_path,monkeypatch)
    book = next(m.book for m in p.decision.world.markets if m.book is not None)
    e.check_book(book,p.available_at)
    with pytest.raises(ValueError): e.check_book(replace(book,bid=book.bid+Decimal('1')),p.available_at)
    with pytest.raises(ValueError): e.check_book(replace(book,received_at=p.available_at+timedelta(seconds=1)),p.available_at)
    with pytest.raises(ValueError): e.check_book(replace(book,available_at=p.available_at+timedelta(seconds=1)),p.available_at)
    with pytest.raises(ValueError): e.check_book(replace(book,received_at=book.received_at.replace(tzinfo=None)),p.available_at)
    with pytest.raises(TypeError): e.check_book(e.ExecutionEstimate(gate(p)),p.available_at)


def test_adversarial_forged_cap_and_intent_as_position(tmp_path, monkeypatch):
    p = notional_plan(tmp_path,monkeypatch)
    intent = e.OrderIntent(p)
    with pytest.raises(TypeError): e.PositionState(p,p.available_at,p.available_at)
    with pytest.raises(TypeError): replace(intent,mode='LIVE')
    with pytest.raises(TypeError): replace(p,outcome='profit')
    row = p.decision.allocation.rows[0]
    badrow = replace(row,amount=t.CapitalAmount(t.CapitalUnit.USD_NOTIONAL,Decimal('999')))
    with pytest.raises(ValueError): replace(p.decision,allocation=replace(p.decision.allocation,rows=(badrow,)+p.decision.allocation.rows[1:]))
    object.__setattr__(intent,'actionable',True)
    with pytest.raises(ValueError): e.PositionState(intent,p.available_at,p.available_at)


def test_no_legacy_or_learning_imports():
    import ast
    from pathlib import Path
    forbidden = ('paper_trading','slippage','criterion','knowledge','outcome','council')
    for filename in ('execution_position_plane.py','shadow_execution_intent_runner.py'):
        tree = ast.parse((Path(e.__file__).parent/filename).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): names = [n.name for n in node.names]
            elif isinstance(node,ast.ImportFrom): names = [node.module or '']+[n.name for n in node.names]
            else: continue
            assert not any(term in name.lower() for name in names for term in forbidden)


def rebuild_with_theses(d, theses, radar=None):
    radar = d.radar if radar is None else radar
    forecasts = tuple(replace(f,thesis=th) for f,th in zip(d.forecasts,theses))
    old = d.allocation
    ranking = t.GlobalOpportunityRanker._rank(d.world,radar,old.ranking.policy,theses=theses,forecasts=forecasts,available_at=d.available_at)
    auths = tuple(t.authorize_risk(c,d.world,old.portfolio,
        replace(a.request,reference_id=c.candidate_id,family=c.family,legs=tuple(t.ExposureLeg(s,t.Direction.LONG) for s in c.markets)),
        a.policy,kill_switch=a.kill_switch,available_at=d.available_at)
        for c,a in zip(radar.candidates,old.authorizations))
    alloc = t.allocate_capital(ranking,old.portfolio,auths,old.budget,old.policy,available_at=d.available_at)
    return replace(d,radar=radar,theses=theses,forecasts=forecasts,allocation=alloc)


def test_explicit_expiry_yields_exit_not_close(tmp_path,monkeypatch):
    p = notional_plan(tmp_path,monkeypatch)
    d = p.decision
    expiry = d.available_at+timedelta(seconds=1)
    d = rebuild_with_theses(d,tuple(replace(th,expiry=expiry) for th in d.theses))
    p = e.ExecutionPlan(d,d.allocation.rows[0].candidate_id,e.Mode.PAPER)
    pending = e.PositionState(e.OrderIntent(p),p.available_at,p.available_at)
    assessment = e.ThesisLifecycle(pending,d.world,expiry)
    assert assessment.state is e.ThesisState.TIMEOUT
    assert e.ExitIntent(assessment).position.phase is e.PositionPhase.PENDING_EXECUTION
    assert e.Reallocation(d,expiry).state is e.ReallocationState.DEFER


def test_multileg_cannot_be_fabricated_from_notional(tmp_path,monkeypatch):
    d = notional_plan(tmp_path,monkeypatch).decision
    candidates = tuple(replace(c,markets=tuple(sorted(set(c.markets)|{'BTCUSDT','ETHUSDT'})),family=t.CandidateFamily.CROSS_MARKET) for c in d.radar.candidates)
    radar = replace(d.radar,candidates=candidates)
    theses = tuple(replace(th,candidate=c) for th,c in zip(d.theses,candidates))
    d = rebuild_with_theses(d,theses,radar)
    positive = next(row for row in d.allocation.rows if row.amount.value>0)
    p = e.ExecutionPlan(d,positive.candidate_id,e.Mode.SHADOW)
    assert p.state is e.PlanState.NO_ORDER and p.reason=='UNSUPPORTED_MULTILEG_EXPRESSION'
    with pytest.raises(ValueError): e.OrderIntent(p)
