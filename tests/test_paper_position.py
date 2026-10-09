"""Synthetic CP-7H inventory contracts; no factual execution claims."""
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal

import pytest

from core.scientific import execution_position_plane as e
from core.scientific import paper_execution as paper
from core.scientific import paper_position as positions
from tests.test_paper_execution import paper_request, quote


def test_open_inventory_and_provenance(paper_request):
    pending = paper_request.pending_position
    before = replace(pending)
    fill = paper.SimulatedPaperFill(paper_request, quote(paper_request, ask='125'))
    opened = positions.PaperOpenPosition(fill)
    assert opened.phase is positions.PaperPositionPhase.PAPER_OPEN
    assert opened.mode is e.Mode.PAPER
    assert opened.kind == 'SIMULATED_PAPER_POSITION' and not opened.actionable
    assert opened.filled_quantity_base == fill.filled_quantity_base
    assert opened.entry_price_usdt_per_base == Decimal('125')
    assert opened.entry_execution_ref == fill.fill_id
    assert opened.pending_position_ref == pending.position_id
    assert opened.thesis_id == pending.thesis_id
    assert opened.intent == pending.intent
    assert (opened.instrument, opened.direction, opened.role) == (pending.instrument, pending.direction, pending.role)
    assert opened.side is e.Side.BUY
    for name in ('model', 'quantity_convention', 'evidence_ref', 'raw_commitment_ref',
                 'exchange_at', 'received_at', 'available_at'):
        assert getattr(opened, name) == getattr(fill, name)
    assert opened.available_at > opened.exchange_at > paper_request.submitted_at
    assert pending == before and pending.phase is e.PositionPhase.PENDING_EXECUTION
    assert pending.filled_quantity_base is pending.entry_price_usdt_per_base is pending.entry_execution_ref is None
    assert tuple(e.PositionPhase) == (e.PositionPhase.PENDING_EXECUTION,)
    assert replace(opened) == positions.PaperOpenPosition(fill) == opened
    assert opened.position_id != pending.position_id
    later = paper.SimulatedPaperFill(paper_request, quote(paper_request, offset=10))
    assert positions.PaperOpenPosition(later).position_id != opened.position_id
    with pytest.raises(FrozenInstanceError):
        opened.fill = later


def test_sell_inventory_uses_fill_without_repricing(paper_request):
    t = e.upstream
    d = paper_request.pending_position.intent.plan.decision
    a = d.allocation
    auths = tuple(t.authorize_risk(x.candidate, x.world, x.portfolio,
        replace(x.request, legs=tuple(replace(leg, direction=t.Direction.SHORT) for leg in x.request.legs)),
        x.policy, kill_switch=x.kill_switch, available_at=x.available_at) for x in a.authorizations)
    d = replace(d, allocation=t.allocate_capital(a.ranking, a.portfolio, auths, a.budget, a.policy, available_at=a.available_at))
    plan = e.ExecutionPlan(d, paper_request.quality_gate.candidate_id, e.Mode.PAPER)
    pending = e.PositionState(e.OrderIntent(plan), d.available_at, d.available_at)
    request = paper.PaperExecutionRequest(pending, replace(paper_request.quality_gate, decision=d), d.available_at)
    fill = paper.SimulatedPaperFill(request, quote(request, bid='80', ask='120'))
    opened = positions.PaperOpenPosition(fill)
    assert opened.side is e.Side.SELL and opened.direction is t.Direction.SHORT
    assert opened.entry_price_usdt_per_base == Decimal('80')
    assert opened.filled_quantity_base == Decimal('0.025')


def test_no_fill_or_substituted_contract_cannot_open(paper_request):
    assert paper.select_paper_fill(paper_request, ()) is None
    for wrong in (None, paper_request, paper_request.pending_position,
                  paper_request.pending_position.intent, e.ExecutionEstimate(paper_request.quality_gate),
                  quote(paper_request), {'fill_id': 'f' * 64}):
        with pytest.raises(TypeError):
            positions.PaperOpenPosition(wrong)
    class FillSubclass(paper.SimulatedPaperFill):
        pass
    with pytest.raises(TypeError):
        positions.PaperOpenPosition(FillSubclass(paper_request, quote(paper_request)))


@pytest.mark.parametrize('target', ['fill', 'request', 'pending', 'quote'])
def test_tampered_source_chain_fails_closed(paper_request, target):
    fill = paper.SimulatedPaperFill(paper_request, quote(paper_request))
    obj, name, value = {
        'fill': (fill, 'filled_quantity_base', Decimal('999')),
        'request': (paper_request, 'request_id', 'f' * 64),
        'pending': (paper_request.pending_position, 'phase', 'PAPER_OPEN'),
        'quote': (fill.quote, 'ask', Decimal('999')),
    }[target]
    object.__setattr__(obj, name, value)
    with pytest.raises(ValueError):
        positions.PaperOpenPosition(fill)


@pytest.mark.parametrize('name', [f.name for f in fields(positions.PaperOpenPosition) if not f.init])
def test_derived_inventory_cannot_be_injected_or_altered(paper_request, name):
    fill = paper.SimulatedPaperFill(paper_request, quote(paper_request))
    opened = positions.PaperOpenPosition(fill)
    with pytest.raises(TypeError):
        positions.PaperOpenPosition(fill, **{name: 'forged'})
    with pytest.raises(ValueError):
        replace(opened, **{name: 'forged'})
    object.__setattr__(opened, name, 'forged')
    with pytest.raises(ValueError):
        e.verify(opened, positions.PaperOpenPosition)


def test_pending_lifecycle_and_execution_request_do_not_accept_open_position(paper_request):
    opened = positions.PaperOpenPosition(paper.SimulatedPaperFill(paper_request, quote(paper_request)))
    assert {f.name for f in fields(opened) if f.init} == {'fill'}
    with pytest.raises(TypeError):
        replace(paper_request, pending_position=opened)
    with pytest.raises(TypeError):
        e.ThesisLifecycle(opened, paper_request.quality_gate.decision.world, opened.available_at)
