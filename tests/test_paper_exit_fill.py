"""Synthetic post-exit-intent quotes; no factual execution or closed inventory."""
import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from core.scientific import execution_position_plane as e
from core.scientific import multi_market_capture as c
from core.scientific import paper_exit_intent as exits
from core.scientific import paper_exit_fill as fills
from core.scientific.paper_position import PaperPositionPhase
from tests.test_paper_execution import paper_request, quote, cycle
from tests.test_paper_exit_intent import timeout


@pytest.fixture
def exit_intent(timeout):
    return exits.PaperExitIntent(timeout)


def exit_quote(intent, *, offset=1, **kwargs):
    request = intent.lifecycle.position.fill.request
    seconds = (intent.available_at-request.submitted_at).total_seconds() + offset
    return quote(request, offset=seconds, **kwargs)


def exit_cycle(intent, q):
    return cycle(intent.lifecycle.position.fill.request, q)


def test_price_quantity_provenance_identity_no_mutation(exit_intent):
    position = exit_intent.lifecycle.position
    before_id = position.position_id
    q = exit_quote(exit_intent, bid='80', ask='120')
    fill = fills.SimulatedPaperExitFill(exit_intent, q)
    assert fill.side is exit_intent.side
    assert fill.simulated_exit_price_usdt_per_base == (Decimal('80') if fill.side is e.Side.SELL else Decimal('120'))
    assert fill.exit_quantity_base == position.filled_quantity_base
    assert fill.kind == 'SIMULATED_PAPER_EXIT_FILL'
    assert fill.model == fills.POST_EXIT_INTENT_NEXT_OBSERVED_QUOTE_V0
    for field, source in (('evidence_ref', 'observation_id'), ('raw_commitment_ref', 'raw_commitment'),
                          ('exchange_at', 'exchange_at'), ('received_at', 'received_at'), ('available_at', 'available_at')):
        assert getattr(fill, field) == getattr(q, source)
    assert replace(fill) == fills.SimulatedPaperExitFill(exit_intent, q)
    assert fills.SimulatedPaperExitFill(exit_intent, exit_quote(exit_intent, offset=10)).exit_fill_id != fill.exit_fill_id
    assert position.position_id == before_id and position.phase is PaperPositionPhase.PAPER_OPEN
    e.verify(position, type(position))
    with pytest.raises(FrozenInstanceError): fill.exit_quantity_base = Decimal('1')


@pytest.mark.parametrize('dimension', ['exchange_at', 'received_at', 'available_at'])
@pytest.mark.parametrize('offset', [-1, 0])
def test_independent_strict_timestamp_boundaries(exit_intent, dimension, offset):
    # Wire remains consistent: exchange time can be at/before intent while later
    # receipt/availability are independently eligible. For receipt/availability,
    # exchange time need not precede receipt (clock skew); each boundary is checked.
    q = exit_quote(exit_intent, offset=offset if dimension == 'exchange_at' else 1)
    if dimension != 'exchange_at':
        q = replace(q, **{dimension: exit_intent.available_at+timedelta(seconds=offset)})
        if dimension == 'available_at': q = replace(q, received_at=q.available_at)
    with pytest.raises(ValueError): fills.SimulatedPaperExitFill(exit_intent, q)


def test_consistent_no_fill_and_no_entry_fallback(exit_intent):
    other = next(s for s in c.SYMBOLS if s != exit_intent.lifecycle.position.instrument)
    quotes = [exit_quote(exit_intent, unknown=True), exit_quote(exit_intent, symbol=other),
              exit_quote(exit_intent, role='CONFIRMATION'), exit_intent.lifecycle.position.fill.quote]
    quotes += [exit_quote(exit_intent, offset=i) for i in (-3, -2, -1, 0)]
    assert fills.select_paper_exit_fill(exit_intent, ()) is None
    for q in quotes:
        assert fills.select_paper_exit_fill(exit_intent, (exit_cycle(exit_intent, q),)) is None
        with pytest.raises(ValueError): fills.SimulatedPaperExitFill(exit_intent, q)


def test_invalid_quotes_and_wire(exit_intent):
    for bid, ask in (('0', '1'), ('-1', '1'), ('1', '0'), ('1', '-1'), ('2', '1')):
        with pytest.raises(ValueError): fills.SimulatedPaperExitFill(exit_intent, exit_quote(exit_intent, bid=bid, ask=ask))
    q = exit_quote(exit_intent)
    for name, value in (('bid', Decimal('99')), ('observation_id', 'invalid'), ('raw_commitment', 'invalid')):
        with pytest.raises(ValueError): fills.SimulatedPaperExitFill(exit_intent, replace(q, **{name: value}))
    with pytest.raises(TypeError): fills.SimulatedPaperExitFill(exit_intent, replace(q, bid=100.0))


def test_no_caller_fields_or_contract_substitution(exit_intent):
    q = exit_quote(exit_intent)
    fill = fills.SimulatedPaperExitFill(exit_intent, q)
    assert {f.name for f in fields(fill) if f.init} == {'exit_intent', 'quote'}
    for f in fields(fill):
        if f.init: continue
        with pytest.raises(TypeError): fills.SimulatedPaperExitFill(exit_intent, q, **{f.name: 'forged'})
        with pytest.raises(ValueError): replace(fill, **{f.name: 'forged'})
    for name in ('price', 'quantity', 'fees', 'funding', 'slippage', 'latency', 'pnl', 'execution_result', 'broker_id', 'venue_fill_id'):
        with pytest.raises(TypeError): fills.SimulatedPaperExitFill(exit_intent, q, **{name: 1})
    for wrong in (exit_intent.lifecycle, exit_intent.lifecycle.position, exit_intent.lifecycle.position.fill, {}, None):
        with pytest.raises(TypeError): fills.SimulatedPaperExitFill(wrong, q)
    with pytest.raises(TypeError): fills.SimulatedPaperExitFill(exit_intent, {})


@pytest.mark.parametrize('target', ['intent', 'position', 'fill', 'request', 'exit_fill'])
def test_tampered_chain_fails_closed(exit_intent, target):
    q = exit_quote(exit_intent)
    result = fills.SimulatedPaperExitFill(exit_intent, q)
    p = exit_intent.lifecycle.position
    obj, name, value = {
        'intent': (exit_intent, 'side', 'LIVE'),
        'position': (p, 'filled_quantity_base', Decimal('999')),
        'fill': (p.fill, 'fill_id', 'f'*64),
        'request': (p.fill.request, 'request_id', 'f'*64),
        'exit_fill': (result, 'exit_fill_id', 'f'*64),
    }[target]
    object.__setattr__(obj, name, value)
    with pytest.raises(ValueError): e.verify(result, fills.SimulatedPaperExitFill)
    if target != 'exit_fill':
        with pytest.raises(ValueError): fills.select_paper_exit_fill(exit_intent, ())


def test_selection_replay_and_identity_conflicts(exit_intent):
    a, b = exit_quote(exit_intent), exit_quote(exit_intent, offset=10)
    ca, cb = exit_cycle(exit_intent, a), exit_cycle(exit_intent, b)
    expected = fills.SimulatedPaperExitFill(exit_intent, a)
    assert fills.select_paper_exit_fill(exit_intent, (cb, ca, ca)) == expected
    assert fills.select_paper_exit_fill(exit_intent, (ca, cb)) == expected
    altered = replace(ca, members=(replace(a, raw_commitment='f'*64),))
    with pytest.raises(ValueError, match='conflicting cycle'): fills.select_paper_exit_fill(exit_intent, (ca, altered))
    # A different valid cycle slot isolates observation identity conflict.
    slot = altered.slot-timedelta(microseconds=1)
    altered = replace(altered, slot=slot, started_at=slot,
        cycle_id=c.commitment((altered.universe_id, altered.kind, slot.isoformat())))
    with pytest.raises(ValueError, match='conflicting observation'): fills.select_paper_exit_fill(exit_intent, (ca, altered))
    with pytest.raises(TypeError): fills.select_paper_exit_fill(exit_intent, [ca])
    for bad in (replace(ca, universe_id='f'*64), replace(ca, cycle_id='f'*64),
                replace(ca, missing=()), replace(ca, received_at=ca.completed_at+timedelta(seconds=1))):
        with pytest.raises(ValueError): fills.select_paper_exit_fill(exit_intent, (bad,))


@pytest.mark.parametrize('dimension', ['available', 'received', 'exchange', 'identity'])
def test_lexicographic_selection(exit_intent, dimension):
    at = exit_intent.available_at
    a, b = exit_quote(exit_intent, offset=1), exit_quote(exit_intent, offset=2)
    if dimension == 'available':
        a = replace(a, available_at=at+timedelta(seconds=10)); expected = b
    elif dimension == 'received':
        a = replace(a, available_at=b.available_at); expected = a
    elif dimension == 'exchange':
        a = replace(a, received_at=b.received_at, available_at=b.available_at); expected = a
    else:
        b = replace(a, observation_id='2'*64)
        a = replace(a, observation_id='1'*64); expected = a
    cycles = []
    for index, q in enumerate((a, b)):
        original = exit_cycle(exit_intent, q)
        slot = at+timedelta(milliseconds=index+1)
        cycles.append(replace(original, slot=slot, started_at=slot,
            cycle_id=c.commitment((original.universe_id, original.kind, slot.isoformat()))))
    assert fills.select_paper_exit_fill(exit_intent, tuple(cycles)).quote == expected
    assert fills.select_paper_exit_fill(exit_intent, tuple(reversed(cycles))).quote == expected


def test_accepts_loader_verified_cycles(exit_intent, tmp_path, monkeypatch):
    from tests.test_multi_market_capture import transport
    at = exit_intent.available_at+timedelta(hours=1)
    body = [dict(symbol=s, bidPrice='80', askPrice='120', time=int(at.timestamp()*1000)) for s in c.SYMBOLS]
    transport(monkeypatch, body, at)
    root = tmp_path/'exit_evidence'
    universe = tmp_path/'fixture'/'universe'
    c.capture_cycle(root, universe, kind='DIAGNOSTIC')
    verified = c.load_cycle(root, universe)
    result = fills.select_paper_exit_fill(exit_intent, (verified,))
    assert result.quote in verified.members
    assert result.exit_quantity_base == exit_intent.lifecycle.position.filled_quantity_base


def test_no_legacy_closed_position_or_economic_authority():
    tree = ast.parse(Path(fills.__file__).read_text())
    forbidden = ('paper_trading', 'slippage', 'outcome', 'learning', 'criterion', 'knowledge', 'executionresult', 'broker')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names = [n.name for n in node.names]
        elif isinstance(node, ast.ImportFrom): names = [node.module or '']+[n.name for n in node.names]
        else: continue
        assert not any(term in name.lower() for name in names for term in forbidden)
    assert [n.name for n in tree.body if isinstance(n, ast.ClassDef)] == ['SimulatedPaperExitFill']
    assert not hasattr(fills, 'PaperClosedPosition')
