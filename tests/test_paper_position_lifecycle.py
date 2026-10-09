"""Synthetic observation assessments, never execution or economic evidence."""
import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from core.scientific import execution_position_plane as e
from core.scientific import paper_execution as paper
from core.scientific import paper_position as positions
from core.scientific import paper_position_lifecycle as lifecycle
from tests.test_paper_execution import paper_request, quote
from tests.test_execution_position_plane import rebuild_with_theses, gate


@pytest.fixture
def opened(paper_request):
    return positions.PaperOpenPosition(paper.SimulatedPaperFill(paper_request, quote(paper_request)))


def later_world(opened, *, missing=False, entry=False, bid='90', ask='91'):
    original = opened.intent.plan.decision.world
    book = opened.fill.quote if entry else quote(opened.fill.request, offset=10, bid=bid, ask=ask)
    at = book.available_at
    return replace(original, as_of=at,
        markets=tuple(replace(m, book=None if missing else book, book_age_seconds=None if missing else 2)
                      if m.symbol == opened.instrument else m for m in original.markets),
        book_quality=replace(original.book_quality, assessed_at=at),
        premium_quality=replace(original.premium_quality, assessed_at=at))


def test_tracked_deterministic_immutable_and_no_mutation(opened):
    before = replace(opened)
    pending = replace(opened.fill.request.pending_position)
    world = later_world(opened)
    a = lifecycle.PaperPositionLifecycle(opened, world, world.as_of)
    assert a.state is lifecycle.PaperLifecycleState.TRACKED
    assert a.reason == 'TRACKED_NO_SUPPORTED_INVALIDATION_EVALUATOR'
    assert replace(a) == lifecycle.PaperPositionLifecycle(opened, world, world.as_of)
    assert replace(a, assessed_at=world.as_of.astimezone(timezone(timedelta(hours=1)))) == a
    assert replace(a, assessed_at=world.as_of+timedelta(seconds=1)).assessment_id != a.assessment_id
    assert opened == before and opened.fill.request.pending_position == pending
    assert opened.phase is positions.PaperPositionPhase.PAPER_OPEN
    assert pending.phase is e.PositionPhase.PENDING_EXECUTION
    with pytest.raises(FrozenInstanceError): a.reason = 'EXIT'
    with pytest.raises(TypeError): replace(a, pnl=Decimal('1'))
    with pytest.raises(TypeError): e.ExitIntent(a)
    with pytest.raises(TypeError): e.ThesisLifecycle(opened, world, world.as_of)


def test_missing_book(opened):
    world = later_world(opened, missing=True)
    a = lifecycle.PaperPositionLifecycle(opened, world, world.as_of)
    assert a.state is lifecycle.PaperLifecycleState.OBSERVATION_RISK
    assert a.reason == 'MISSING_CAUSAL_BOOK'


@pytest.mark.parametrize('missing', [False, True])
@pytest.mark.parametrize('offset', [-1, 0, 1])
def test_expiry_boundary_and_precedence(paper_request, missing, offset):
    d = paper_request.pending_position.intent.plan.decision
    expiry = d.available_at + timedelta(seconds=30)
    d = rebuild_with_theses(d, tuple(replace(t, expiry=expiry) for t in d.theses))
    plan = e.ExecutionPlan(d, paper_request.quality_gate.candidate_id, e.Mode.PAPER)
    pending = e.PositionState(e.OrderIntent(plan), d.available_at, d.available_at)
    request = paper.PaperExecutionRequest(pending, gate(plan), d.available_at)
    opened = positions.PaperOpenPosition(paper.SimulatedPaperFill(request, quote(request)))
    world = later_world(opened, missing=missing)
    a = lifecycle.PaperPositionLifecycle(opened, world, expiry+timedelta(seconds=offset))
    expected = lifecycle.PaperLifecycleState.TIMEOUT if offset >= 0 else (
        lifecycle.PaperLifecycleState.OBSERVATION_RISK if missing else lifecycle.PaperLifecycleState.TRACKED)
    assert a.state is expected
    if offset >= 0: assert a.reason == 'EXPLICIT_THESIS_EXPIRY'
    assert opened.phase is positions.PaperPositionPhase.PAPER_OPEN


def test_causal_boundaries_and_entry_world(opened):
    world = later_world(opened)
    for w, at in ((opened.intent.plan.decision.world, world.as_of),
                  (world, world.as_of-timedelta(microseconds=1)),
                  (world, world.as_of.replace(tzinfo=None))):
        with pytest.raises(ValueError): lifecycle.PaperPositionLifecycle(opened, w, at)
    entry = later_world(opened, entry=True)
    assert entry.as_of == opened.available_at
    assert lifecycle.PaperPositionLifecycle(opened, entry, entry.as_of).state is lifecycle.PaperLifecycleState.TRACKED


def test_wrong_types_scope_and_population(opened):
    world = later_world(opened)
    for wrong in (opened.fill, opened.fill.request.pending_position, opened.intent, None):
        with pytest.raises(TypeError): lifecycle.PaperPositionLifecycle(wrong, world, world.as_of)
    with pytest.raises(TypeError): lifecycle.PaperPositionLifecycle(opened, {}, world.as_of)
    with pytest.raises(ValueError):
        lifecycle.PaperPositionLifecycle(opened, replace(world, universe_id='f'*64), world.as_of)
    for name, value in (('role', 'CONFIRMATION'), ('markets', world.markets[1:]),
                        ('markets', world.markets+(world.markets[0],))):
        bad = replace(world)
        object.__setattr__(bad, name, value)
        with pytest.raises(ValueError): lifecycle.PaperPositionLifecycle(opened, bad, world.as_of)


@pytest.mark.parametrize('target', ['position', 'fill', 'request', 'thesis', 'instrument', 'world', 'book'])
def test_tampered_chain_fails_closed(opened, target):
    world = later_world(opened)
    obj, name, value = {
        'position': (opened, 'position_id', 'f'*64),
        'fill': (opened.fill, 'filled_quantity_base', Decimal('999')),
        'request': (opened.fill.request, 'request_id', 'f'*64),
        'thesis': (opened, 'thesis_id', 'f'*64),
        'instrument': (opened.intent, 'instrument', 'UNKNOWN'),
        'world': (world, 'world_state_id', 'f'*64),
        'book': (next(m.book for m in world.markets if m.symbol == opened.instrument), 'bid', Decimal('999')),
    }[target]
    object.__setattr__(obj, name, value)
    with pytest.raises(ValueError): lifecycle.PaperPositionLifecycle(opened, world, world.as_of)


def test_resealed_world_with_invalid_book_rejected(opened):
    world = later_world(opened)
    bad = replace(world, markets=tuple(replace(m, book=replace(m.book, bid=Decimal('89')))
        if m.symbol == opened.instrument else m for m in world.markets))
    with pytest.raises(ValueError, match='source wire'):
        lifecycle.PaperPositionLifecycle(opened, bad, bad.as_of)


@pytest.mark.parametrize('name', ['state', 'reason', 'assessment_id'])
def test_derived_fields_cannot_be_injected_or_forged(opened, name):
    world = later_world(opened)
    a = lifecycle.PaperPositionLifecycle(opened, world, world.as_of)
    with pytest.raises(TypeError): lifecycle.PaperPositionLifecycle(opened, world, world.as_of, **{name: 'forged'})
    with pytest.raises(ValueError): replace(a, **{name: 'forged'})
    object.__setattr__(a, name, 'forged')
    with pytest.raises(ValueError): e.verify(a, lifecycle.PaperPositionLifecycle)


def test_price_direction_does_not_select_state(opened):
    for bid, ask in (('1', '2'), ('10000', '10001')):
        world = later_world(opened, bid=bid, ask=ask)
        assert lifecycle.PaperPositionLifecycle(opened, world, world.as_of).state is lifecycle.PaperLifecycleState.TRACKED


def test_no_economic_exit_or_legacy_authority():
    tree = ast.parse(Path(lifecycle.__file__).read_text())
    forbidden = ('outcome', 'learning', 'criterion', 'knowledge', 'paper_trading', 'slippage', 'executionresult')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names = [n.name for n in node.names]
        elif isinstance(node, ast.ImportFrom): names = [node.module or '']+[n.name for n in node.names]
        else: continue
        assert not any(term in name.lower() for name in names for term in forbidden)
    assert not hasattr(lifecycle, 'PaperExitIntent')
    assert {f.name for f in fields(lifecycle.PaperPositionLifecycle) if f.init} == {'position', 'world', 'assessed_at'}
    assert tuple(e.PositionPhase) == (e.PositionPhase.PENDING_EXECUTION,)
