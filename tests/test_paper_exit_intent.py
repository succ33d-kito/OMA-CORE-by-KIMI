"""Synthetic exit intentions only; no fills, inventory disposal or economics."""
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
from core.scientific import paper_exit_intent as exits
from tests.test_paper_execution import paper_request, quote
from tests.test_paper_position_lifecycle import opened, later_world
from tests.test_execution_position_plane import rebuild_with_theses, gate


@pytest.fixture(params=[e.Side.BUY, e.Side.SELL])
def timeout(paper_request, request):
    d = paper_request.pending_position.intent.plan.decision
    expiry = d.available_at + timedelta(seconds=30)
    d = rebuild_with_theses(d, tuple(replace(t, expiry=expiry) for t in d.theses))
    if request.param is e.Side.SELL:
        t = e.upstream
        a = d.allocation
        auths = tuple(t.authorize_risk(x.candidate, x.world, x.portfolio,
            replace(x.request, legs=tuple(replace(leg, direction=t.Direction.SHORT) for leg in x.request.legs)),
            x.policy, kill_switch=x.kill_switch, available_at=x.available_at) for x in a.authorizations)
        d = replace(d, allocation=t.allocate_capital(a.ranking, a.portfolio, auths, a.budget, a.policy, available_at=a.available_at))
    plan = e.ExecutionPlan(d, paper_request.quality_gate.candidate_id, e.Mode.PAPER)
    pending = e.PositionState(e.OrderIntent(plan), d.available_at, d.available_at)
    req = paper.PaperExecutionRequest(pending, gate(plan), d.available_at)
    position = positions.PaperOpenPosition(paper.SimulatedPaperFill(req, quote(req)))
    return lifecycle.PaperPositionLifecycle(position, later_world(position), expiry)


def test_timeout_exit_provenance_side_identity_and_no_mutation(timeout):
    before = replace(timeout)
    intent = exits.PaperExitIntent(timeout)
    assert intent.side is (e.Side.SELL if timeout.position.side is e.Side.BUY else e.Side.BUY)
    assert intent.reason == 'EXPLICIT_THESIS_EXPIRY'
    assert intent.mode is e.Mode.PAPER
    assert intent.kind == 'SIMULATED_PAPER_EXIT_INTENT' and intent.actionable is False
    assert intent.available_at == timeout.assessed_at
    assert intent.position_ref == timeout.position.position_id
    assert intent.lifecycle_assessment_ref == timeout.assessment_id
    assert intent.lifecycle is timeout
    assert replace(intent) == exits.PaperExitIntent(timeout)
    equivalent = replace(timeout, assessed_at=timeout.assessed_at.astimezone(timezone(timedelta(hours=2))))
    assert exits.PaperExitIntent(equivalent) == intent
    assert exits.PaperExitIntent(replace(timeout, assessed_at=timeout.assessed_at+timedelta(seconds=1))).exit_intent_id != intent.exit_intent_id
    assert timeout == before
    assert timeout.position.phase is positions.PaperPositionPhase.PAPER_OPEN
    assert timeout.position.fill.request.pending_position.phase is e.PositionPhase.PENDING_EXECUTION
    with pytest.raises(FrozenInstanceError): intent.side = e.Side.BUY
    with pytest.raises(TypeError): e.ExitIntent(timeout)
    with pytest.raises(TypeError): e.ThesisLifecycle(timeout.position, timeout.world, timeout.assessed_at)


@pytest.mark.parametrize('missing', [False, True])
def test_tracked_and_missing_observation_never_authorize_exit(opened, missing):
    world = later_world(opened, missing=missing)
    a = lifecycle.PaperPositionLifecycle(opened, world, world.as_of)
    assert a.state is (lifecycle.PaperLifecycleState.OBSERVATION_RISK if missing else lifecycle.PaperLifecycleState.TRACKED)
    if missing: assert a.reason == 'MISSING_CAUSAL_BOOK'
    with pytest.raises(ValueError): exits.PaperExitIntent(a)


def test_wrong_contracts_and_old_exit_substitution(timeout):
    pending = timeout.position.fill.request.pending_position
    old = e.ThesisLifecycle(pending, timeout.world, timeout.assessed_at)
    old_exit = e.ExitIntent(old)
    for wrong in (old, old_exit, timeout.position, timeout.position.fill, pending, None, {}):
        with pytest.raises(TypeError): exits.PaperExitIntent(wrong)
    with pytest.raises(TypeError): e.ExitIntent(timeout)


@pytest.mark.parametrize('name', [f.name for f in fields(exits.PaperExitIntent) if not f.init])
def test_derived_fields_cannot_be_injected_or_forged(timeout, name):
    intent = exits.PaperExitIntent(timeout)
    with pytest.raises(TypeError): exits.PaperExitIntent(timeout, **{name: 'forged'})
    with pytest.raises(ValueError): replace(intent, **{name: 'forged'})
    object.__setattr__(intent, name, 'forged')
    with pytest.raises(ValueError): e.verify(intent, exits.PaperExitIntent)


@pytest.mark.parametrize('name', ['price', 'quantity', 'fill', 'pnl', 'fee', 'funding', 'execution_result',
                                  'closed_at', 'broker_id', 'venue_id', 'state'])
def test_no_caller_execution_or_economic_inputs(timeout, name):
    with pytest.raises(TypeError): exits.PaperExitIntent(timeout, **{name: Decimal('1')})


@pytest.mark.parametrize('target', ['state', 'reason', 'assessment', 'position', 'fill', 'request', 'pending', 'intent', 'plan', 'decision', 'world'])
def test_tampered_chain_rejected(timeout, target):
    p = timeout.position
    pending = p.fill.request.pending_position
    obj, name, value = {
        'state': (timeout, 'state', lifecycle.PaperLifecycleState.TRACKED),
        'reason': (timeout, 'reason', 'MISSING_CAUSAL_BOOK'),
        'assessment': (timeout, 'assessment_id', 'f'*64),
        'position': (p, 'position_id', 'f'*64),
        'fill': (p.fill, 'filled_quantity_base', Decimal('999')),
        'request': (p.fill.request, 'request_id', 'f'*64),
        'pending': (pending, 'position_id', 'f'*64),
        'intent': (pending.intent, 'intent_id', 'f'*64),
        'plan': (pending.intent.plan, 'plan_id', 'f'*64),
        'decision': (pending.intent.plan.decision, 'decision_id', 'f'*64),
        'world': (timeout.world, 'world_state_id', 'f'*64),
    }[target]
    object.__setattr__(obj, name, value)
    with pytest.raises(ValueError): exits.PaperExitIntent(timeout)


def test_missing_book_still_timeout_only_when_explicit_expiry(timeout):
    a = replace(timeout, world=later_world(timeout.position, missing=True))
    assert a.state is lifecycle.PaperLifecycleState.TIMEOUT
    assert exits.PaperExitIntent(a).reason == 'EXPLICIT_THESIS_EXPIRY'


def test_exact_type_and_no_execution_authority(timeout):
    class Subclass(lifecycle.PaperPositionLifecycle):
        pass
    with pytest.raises(TypeError): exits.PaperExitIntent(Subclass(timeout.position, timeout.world, timeout.assessed_at))
    assert {f.name for f in fields(exits.PaperExitIntent) if f.init} == {'lifecycle'}
    assert {f.name for f in fields(exits.PaperExitIntent)} == {
        'lifecycle', 'position_ref', 'lifecycle_assessment_ref', 'side', 'reason', 'mode',
        'kind', 'actionable', 'available_at', 'exit_intent_id'}
    tree = ast.parse(Path(exits.__file__).read_text())
    forbidden = ('outcome', 'learning', 'criterion', 'knowledge', 'paper_trading', 'slippage', 'executionresult', 'broker')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names = [n.name for n in node.names]
        elif isinstance(node, ast.ImportFrom): names = [node.module or '']+[n.name for n in node.names]
        else: continue
        assert not any(term in name.lower() for name in names for term in forbidden)
    assert [n.name for n in tree.body if isinstance(n, ast.ClassDef)] == ['PaperExitIntent']
