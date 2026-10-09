"""Synthetic fixtures only; no network, broker or factual execution claims."""
import ast
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta, timezone
from decimal import Decimal, localcontext, ROUND_DOWN
from pathlib import Path

import pytest
from core.scientific import paper_execution as paper
from core.scientific import execution_position_plane as e
from core.scientific import multi_market_capture as c
from tests.test_execution_position_plane import notional_plan, gate


@pytest.fixture
def paper_request(tmp_path, monkeypatch):
    p = replace(notional_plan(tmp_path/'fixture', monkeypatch), mode=e.Mode.PAPER)
    pending = e.PositionState(e.OrderIntent(p), p.available_at, p.available_at)
    return paper.PaperExecutionRequest(pending, gate(p), p.available_at)


def quote(paper_request, *, offset=1, bid='100', ask='101', symbol=None, role='PILOT', unknown=False):
    at = paper_request.submitted_at + timedelta(seconds=offset)
    symbol = symbol or paper_request.pending_position.instrument
    row = dict(symbol=symbol,bidPrice=bid,askPrice=ask,bidQty='10',askQty='10',lastUpdateId=1)
    if not unknown: row['time'] = int(at.timestamp()*1000)
    wire = c._json(row).decode()
    return c.MarketObservation(symbol,c.commitment((wire,at.isoformat())),c.commitment(row),wire,
        at+timedelta(seconds=1),at+timedelta(seconds=2),None if unknown else at,1,Decimal(bid),Decimal(ask),role)


def cycle(paper_request, q):
    universe = paper_request.pending_position.intent.plan.decision.world.universe_id
    slot = q.received_at-timedelta(seconds=1)
    return c.MarketCycle(c.commitment((universe,'DIAGNOSTIC',slot.isoformat())),universe,'DIAGNOSTIC',slot,slot,
        q.available_at,q.received_at,(q,),tuple(s for s in c.SYMBOLS if s!=q.symbol))


def test_buy_ask_derived_quantity_and_unchanged_pending(paper_request):
    pending = paper_request.pending_position
    fill = paper.SimulatedPaperFill(paper_request,quote(paper_request,ask='125'))
    assert fill.side is e.Side.BUY and fill.simulated_fill_price_usdt_per_base == Decimal('125')
    assert fill.filled_quantity_base == pending.intent.quantity / Decimal('125')
    assert fill.model == paper.POST_INTENT_NEXT_OBSERVED_QUOTE_V0
    assert fill.kind == 'SIMULATED_PAPER_FILL'
    assert fill.quantity_convention == 'NOMINAL_USD_EQUALS_USDT_SIMULATION_ONLY'
    assert fill.evidence_ref == fill.quote.observation_id and fill.raw_commitment_ref == fill.quote.raw_commitment
    assert fill.exchange_at == fill.quote.exchange_at and fill.available_at == fill.quote.available_at
    assert not pending.intent.actionable
    assert pending.phase is e.PositionPhase.PENDING_EXECUTION and pending.filled_quantity_base is None
    assert pending.entry_price_usdt_per_base is None and pending.entry_execution_ref is None
    assert replace(paper_request) == paper_request and replace(fill) == fill
    with pytest.raises(FrozenInstanceError): fill.kind='VENUE_FILL'


def test_sell_bid_with_risk_reauthorized(paper_request):
    t=e.upstream; d=paper_request.pending_position.intent.plan.decision; a=d.allocation
    auths=tuple(t.authorize_risk(x.candidate,x.world,x.portfolio,
        replace(x.request,legs=tuple(replace(leg,direction=t.Direction.SHORT) for leg in x.request.legs)),
        x.policy,kill_switch=x.kill_switch,available_at=x.available_at) for x in a.authorizations)
    allocation=t.allocate_capital(a.ranking,a.portfolio,auths,a.budget,a.policy,available_at=a.available_at)
    d=replace(d,allocation=allocation)
    plan=e.ExecutionPlan(d,paper_request.quality_gate.candidate_id,e.Mode.PAPER)
    pending=e.PositionState(e.OrderIntent(plan),d.available_at,d.available_at)
    sell=paper.PaperExecutionRequest(pending,gate(plan),d.available_at)
    fill=paper.SimulatedPaperFill(sell,quote(sell,bid='80',ask='120'))
    assert fill.side is e.Side.SELL and fill.simulated_fill_price_usdt_per_base==Decimal('80')
    assert fill.filled_quantity_base==Decimal('0.025')


def test_decimal_context_independence_and_offset_normalization(paper_request):
    q=quote(paper_request,ask='103')
    normal=paper.SimulatedPaperFill(paper_request,q)
    with localcontext() as ctx:
        ctx.prec=2; ctx.rounding=ROUND_DOWN
        assert paper.SimulatedPaperFill(paper_request,q)==normal
    same_instant=paper_request.submitted_at.astimezone(timezone(timedelta(hours=2)))
    assert replace(paper_request,submitted_at=same_instant)==paper_request


@pytest.mark.parametrize('mode',[e.Mode.SHADOW,'LIVE'])
def test_non_paper_rejected(paper_request,mode):
    with pytest.raises((TypeError,ValueError)):
        p=replace(paper_request.pending_position.intent.plan,mode=mode)
        pending=replace(paper_request.pending_position,intent=e.OrderIntent(p))
        replace(paper_request,pending_position=pending)


@pytest.mark.parametrize('limit',[None,Decimal('0')])
def test_nonpass_gate_rejected(paper_request,limit):
    with pytest.raises(ValueError,match='PASS'):
        replace(paper_request,quality_gate=gate(paper_request.pending_position.intent.plan,max_relative_spread=limit))


def test_mismatched_candidate_and_decision(paper_request):
    p=paper_request.pending_position.intent.plan; d=p.decision
    other=next(c.candidate_id for c in d.radar.candidates if c.candidate_id!=p.candidate_id)
    with pytest.raises(ValueError,match='mismatch'):
        replace(paper_request,quality_gate=replace(paper_request.quality_gate,candidate_id=other))
    with pytest.raises(ValueError,match='mismatch'):
        replace(paper_request,quality_gate=replace(paper_request.quality_gate,decision=replace(d,configuration_commitment='f'*64)))


@pytest.mark.parametrize('change',['naive','early'])
def test_invalid_submission_time(paper_request,change):
    value=paper_request.submitted_at.replace(tzinfo=None) if change=='naive' else paper_request.submitted_at-timedelta(seconds=1)
    with pytest.raises(ValueError): replace(paper_request,submitted_at=value)


@pytest.mark.parametrize('field',['exchange_at','received_at','available_at'])
@pytest.mark.parametrize('offset',[-1,0])
def test_no_pre_or_at_intent_timestamp(paper_request,field,offset):
    q=quote(paper_request)
    changed=paper_request.submitted_at+timedelta(seconds=offset)
    # Some independent mutations violate wire or time ordering as well; all fail closed.
    with pytest.raises(ValueError): paper.SimulatedPaperFill(paper_request,replace(q,**{field:changed}))


def test_unknown_wrong_symbol_wrong_role_no_fallback(paper_request):
    other=next(s for s in c.SYMBOLS if s!=paper_request.pending_position.instrument)
    for q in (quote(paper_request,unknown=True),quote(paper_request,symbol=other),quote(paper_request,role='CONFIRMATION'),quote(paper_request,offset=-5)):
        assert paper.select_paper_fill(paper_request,(cycle(paper_request,q),)) is None
        with pytest.raises(ValueError): paper.SimulatedPaperFill(paper_request,q)
    assert paper.select_paper_fill(paper_request,()) is None
    decision_book=next(m.book for m in paper_request.quality_gate.decision.world.markets if m.symbol==paper_request.pending_position.instrument)
    with pytest.raises(ValueError): paper.SimulatedPaperFill(paper_request,decision_book)


@pytest.mark.parametrize('bid,ask',[('0','1'),('-1','1'),('1','0'),('1','-1'),('2','1')])
def test_invalid_quotes(paper_request,bid,ask):
    with pytest.raises(ValueError): paper.SimulatedPaperFill(paper_request,quote(paper_request,bid=bid,ask=ask))


@pytest.mark.parametrize('field',['observation_id','raw_commitment'])
def test_bad_commitment(paper_request,field):
    with pytest.raises(ValueError): paper.SimulatedPaperFill(paper_request,replace(quote(paper_request),**{field:'invalid'}))


def test_wire_tamper_and_no_float_quote(paper_request):
    q=quote(paper_request)
    with pytest.raises(ValueError): paper.SimulatedPaperFill(paper_request,replace(q,bid=Decimal('99')))
    with pytest.raises(TypeError): paper.SimulatedPaperFill(paper_request,replace(q,bid=100.0))


@pytest.mark.parametrize('field',['simulated_fill_price_usdt_per_base','filled_quantity_base','model','kind'])
def test_derived_fields_not_caller_settable(paper_request,field):
    q=quote(paper_request); fill=paper.SimulatedPaperFill(paper_request,q)
    with pytest.raises(TypeError): paper.SimulatedPaperFill(paper_request,q,**{field:Decimal('1')})
    with pytest.raises(ValueError): replace(fill,**{field:Decimal('1')})


def test_wrong_types_and_tampering_fail_closed(paper_request):
    q=quote(paper_request)
    for wrong in (e.ExecutionEstimate(paper_request.quality_gate),paper_request.pending_position.intent,{'ask':'101'}):
        with pytest.raises(TypeError): paper.SimulatedPaperFill(paper_request,wrong)
    object.__setattr__(paper_request.pending_position,'filled_quantity_base',Decimal('1'))
    with pytest.raises(ValueError): paper.SimulatedPaperFill(paper_request,q)


def test_fill_and_request_identity_tamper(paper_request):
    fill=paper.SimulatedPaperFill(paper_request,quote(paper_request))
    object.__setattr__(fill,'filled_quantity_base',Decimal('999'))
    with pytest.raises(ValueError): e.verify(fill,paper.SimulatedPaperFill)
    object.__setattr__(paper_request,'request_id','f'*64)
    with pytest.raises(ValueError): paper.select_paper_fill(paper_request,())


def test_deterministic_selection_replays_and_conflicts(paper_request):
    first=quote(paper_request,offset=1); later=quote(paper_request,offset=10)
    a,b=cycle(paper_request,first),cycle(paper_request,later)
    expected=paper.SimulatedPaperFill(paper_request,first)
    assert paper.select_paper_fill(paper_request,(b,a,a))==expected
    assert paper.select_paper_fill(paper_request,(a,b))==expected
    with pytest.raises(TypeError): paper.select_paper_fill(paper_request,[a])
    with pytest.raises(ValueError): paper.select_paper_fill(paper_request,(a,replace(a,universe_id='f'*64)))
    altered=replace(a,members=(replace(first,raw_commitment='f'*64),))
    with pytest.raises(ValueError): paper.select_paper_fill(paper_request,(a,altered))


def test_selector_accepts_upstream_verified_cycle(paper_request,tmp_path,monkeypatch):
    from tests.test_multi_market_capture import transport
    at=paper_request.submitted_at+timedelta(hours=1)
    body=[dict(symbol=s,bidPrice='100',askPrice='125',time=int(at.timestamp()*1000)) for s in c.SYMBOLS]
    transport(monkeypatch,body,at)
    root=tmp_path/'post_intent'
    c.capture_cycle(root,tmp_path/'fixture'/'universe',kind='DIAGNOSTIC')
    verified=c.load_cycle(root,tmp_path/'fixture'/'universe')
    result=paper.select_paper_fill(paper_request,(verified,))
    assert result.evidence_ref==next(q.observation_id for q in verified.members if q.symbol==paper_request.pending_position.instrument)
    assert result.simulated_fill_price_usdt_per_base==Decimal('125')


@pytest.mark.parametrize('offset',[-3,-2,-1,0])
def test_consistent_wire_temporal_boundaries_produce_no_fill(paper_request,offset):
    q=quote(paper_request,offset=offset)
    assert paper.select_paper_fill(paper_request,(cycle(paper_request,q),)) is None


@pytest.mark.parametrize('dimension',['available','received','exchange','identity'])
def test_selection_lexicographic_tie_breaks(paper_request,dimension):
    at=paper_request.submitted_at
    a,b=quote(paper_request,offset=1),quote(paper_request,offset=2)
    if dimension=='available':
        a=replace(a,available_at=at+timedelta(seconds=10))
        expected=b
    elif dimension=='received':
        a=replace(a,available_at=b.available_at)
        expected=a
    elif dimension=='exchange':
        a=replace(a,received_at=b.received_at,available_at=b.available_at)
        expected=a
    else:
        b=replace(a,observation_id='2'*64)
        a=replace(a,observation_id='1'*64)
        expected=a
    cycles=[]
    for index,q in enumerate((a,b)):
        original=cycle(paper_request,q)
        slot=at+timedelta(milliseconds=index+1)
        cycles.append(replace(original,slot=slot,started_at=slot,
            cycle_id=c.commitment((original.universe_id,original.kind,slot.isoformat()))))
    assert paper.select_paper_fill(paper_request,tuple(cycles)).evidence_ref==expected.observation_id
    assert paper.select_paper_fill(paper_request,tuple(reversed(cycles))).evidence_ref==expected.observation_id


def test_no_legacy_learning_or_execution_observation_authority():
    tree=ast.parse(Path(paper.__file__).read_text())
    forbidden=('paper_trading','slippage','criterion','knowledge','outcome','learning')
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): names=[n.name for n in node.names]
        elif isinstance(node,ast.ImportFrom): names=[node.module or '']+[n.name for n in node.names]
        else: continue
        assert not any(term in name.lower() for name in names for term in forbidden)
    assert {f.name for f in fields(paper.PaperExecutionRequest) if f.init}=={'pending_position','quality_gate','submitted_at'}
    assert {f.name for f in fields(paper.SimulatedPaperFill) if f.init}=={'request','quote'}
