"""Synthetic inventory closure only; no economics, account state or learning."""
import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from core.scientific import execution_position_plane as e
from core.scientific import paper_exit_intent as exits
from core.scientific import paper_exit_fill as fills
from core.scientific import paper_closed_position as closed
from core.scientific.paper_position import PaperPositionPhase
from tests.test_paper_execution import paper_request
from tests.test_paper_exit_intent import timeout
from tests.test_paper_exit_fill import exit_intent, exit_quote


@pytest.fixture
def exit_fill(exit_intent):
    return fills.SimulatedPaperExitFill(exit_intent, exit_quote(exit_intent, bid='80', ask='120'))


def test_long_short_closed_inventory_and_exact_provenance(exit_fill):
    fill = exit_fill
    intent = fill.exit_intent
    p = intent.lifecycle.position
    snapshot = e.upstream._plain(fill)
    result = closed.PaperClosedPosition(fill)
    assert result.exit_fill is fill
    assert result.entry_side is p.side and result.exit_side is fill.side
    assert (result.entry_side, result.exit_side) in ((e.Side.BUY, e.Side.SELL), (e.Side.SELL, e.Side.BUY))
    assert result.quantity_base == fill.exit_quantity_base == p.filled_quantity_base
    assert result.entry_price_usdt_per_base == p.entry_price_usdt_per_base
    assert result.exit_price_usdt_per_base == fill.simulated_exit_price_usdt_per_base
    assert result.open_position_ref == p.position_id
    assert result.entry_fill_ref == p.fill.fill_id
    assert result.exit_intent_ref == intent.exit_intent_id
    assert result.exit_fill_ref == fill.exit_fill_id
    assert result.thesis_id == p.thesis_id and result.instrument == p.instrument
    assert result.opened_at == p.available_at
    assert result.closed_at == fill.available_at > result.opened_at
    assert all(at > intent.available_at for at in (fill.exchange_at, fill.received_at, fill.available_at))
    assert result.phase is closed.PaperClosedPositionPhase.PAPER_CLOSED
    assert result.mode is e.Mode.PAPER and not result.actionable
    assert result.kind == 'SIMULATED_PAPER_CLOSED_POSITION'
    assert e.upstream._plain(fill) == snapshot
    assert p.phase is PaperPositionPhase.PAPER_OPEN
    assert p.fill.request.pending_position.phase is e.PositionPhase.PENDING_EXECUTION
    assert replace(result) == closed.PaperClosedPosition(fill)
    with pytest.raises(FrozenInstanceError): result.quantity_base = Decimal('1')


def test_identity_replay_timezone_and_different_evidence(exit_fill):
    result = closed.PaperClosedPosition(exit_fill)
    original = exit_fill.exit_intent
    equivalent = replace(original.lifecycle, assessed_at=original.available_at.astimezone(timezone(timedelta(hours=2))))
    replay = replace(exit_fill, exit_intent=exits.PaperExitIntent(equivalent))
    assert closed.PaperClosedPosition(replay).closed_position_id == result.closed_position_id
    later = fills.SimulatedPaperExitFill(original, exit_quote(original, offset=10))
    assert closed.PaperClosedPosition(later).closed_position_id != result.closed_position_id


def test_only_exact_exit_fill_can_construct_closed_position(exit_fill):
    intent = exit_fill.exit_intent
    for wrong in (intent.lifecycle.position.fill.request.pending_position, intent.lifecycle.position,
                  intent, intent.lifecycle, intent.lifecycle.position.fill, None, {}):
        with pytest.raises(TypeError): closed.PaperClosedPosition(wrong)
    class FillSubclass(fills.SimulatedPaperExitFill):
        pass
    with pytest.raises(TypeError): closed.PaperClosedPosition(FillSubclass(intent, exit_fill.quote))
    assert {f.name for f in fields(closed.PaperClosedPosition) if f.init} == {'exit_fill'}


def test_no_caller_derived_or_economic_fields(exit_fill):
    result = closed.PaperClosedPosition(exit_fill)
    for f in fields(result):
        if f.init: continue
        with pytest.raises(TypeError): closed.PaperClosedPosition(exit_fill, **{f.name: 'forged'})
        with pytest.raises(ValueError): replace(result, **{f.name: 'forged'})
        altered = replace(result)
        object.__setattr__(altered, f.name, 'forged')
        with pytest.raises(ValueError): e.verify(altered, closed.PaperClosedPosition)
    for name in ('pnl', 'return_pct', 'win', 'loss', 'outcome', 'fee', 'funding', 'broker_id', 'venue_fill_id', 'open_position'):
        assert not hasattr(result, name)
        with pytest.raises(TypeError): closed.PaperClosedPosition(exit_fill, **{name: 1})


@pytest.mark.parametrize('target', ['exit_fill', 'quantity', 'side', 'close_time', 'exit_intent',
                                  'lifecycle', 'open_position', 'entry_fill', 'request',
                                  'pending', 'order', 'plan', 'decision', 'exit_quote'])
def test_tampering_anywhere_in_chain_fails_closed(exit_fill, target):
    intent = exit_fill.exit_intent
    p = intent.lifecycle.position
    pending = p.fill.request.pending_position
    obj, name, value = {
        'exit_fill': (exit_fill, 'exit_fill_id', 'f'*64),
        'quantity': (exit_fill, 'exit_quantity_base', Decimal('999')),
        'side': (exit_fill, 'side', p.side),
        'close_time': (exit_fill, 'available_at', p.available_at),
        'exit_intent': (intent, 'exit_intent_id', 'f'*64),
        'lifecycle': (intent.lifecycle, 'assessment_id', 'f'*64),
        'open_position': (p, 'position_id', 'f'*64),
        'entry_fill': (p.fill, 'fill_id', 'f'*64),
        'request': (p.fill.request, 'request_id', 'f'*64),
        'pending': (pending, 'position_id', 'f'*64),
        'order': (pending.intent, 'intent_id', 'f'*64),
        'plan': (pending.intent.plan, 'plan_id', 'f'*64),
        'decision': (pending.intent.plan.decision, 'decision_id', 'f'*64),
        'exit_quote': (exit_fill.quote, 'bid', Decimal('999')),
    }[target]
    object.__setattr__(obj, name, value)
    with pytest.raises(ValueError): closed.PaperClosedPosition(exit_fill)


def test_no_economic_or_execution_authority():
    tree = ast.parse(Path(closed.__file__).read_text())
    forbidden = ('outcome', 'learning', 'criterion', 'knowledge', 'paper_trading', 'slippage', 'executionresult', 'broker')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names = [n.name for n in node.names]
        elif isinstance(node, ast.ImportFrom): names = [node.module or '']+[n.name for n in node.names]
        else: continue
        assert not any(term in name.lower() for name in names for term in forbidden)
    assert {f.name for f in fields(closed.PaperClosedPosition)} == {
        'exit_fill', 'open_position_ref', 'entry_fill_ref', 'exit_intent_ref', 'exit_fill_ref',
        'thesis_id', 'instrument', 'entry_side', 'exit_side', 'quantity_base',
        'entry_price_usdt_per_base', 'exit_price_usdt_per_base', 'opened_at', 'closed_at',
        'phase', 'mode', 'kind', 'actionable', 'closed_position_id'}
    assert tuple(e.PositionPhase) == (e.PositionPhase.PENDING_EXECUTION,)
    assert tuple(PaperPositionPhase) == (PaperPositionPhase.PAPER_OPEN,)
