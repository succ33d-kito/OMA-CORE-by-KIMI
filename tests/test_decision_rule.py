"""Synthetic contract fixtures only; no operational gate is lifted by production code."""
from dataclasses import replace, FrozenInstanceError, fields
from datetime import timedelta
from pathlib import Path
import ast
import importlib.util
import inspect
import os
import subprocess
import sys
import pytest

from core.scientific import decision_rule as d
from core.scientific.policy_kernel import PolicyKernel, families
from core.scientific.nuisance_pilot_contracts import InputType, InputStatus, DatasetRole

_spec = importlib.util.spec_from_file_location("_rule_fixtures", Path(__file__).with_name("test_policy_kernel.py"))
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)


def fixture():
    signals = tuple(d.ReferenceSignal(f, vote) for f, vote in zip(InputType, (1, 0, -1, -1)))
    original = _fixtures.opportunity()
    hashes = {x.family: x.commitment for x in signals}
    op = replace(original, inputs=tuple(replace(i, value_hash=hashes[i.input_type]) for i in original.inputs))
    return op, PolicyKernel().form(op, _fixtures.controls()), signals


def eligible_fixture():
    # Hypothetical unexecuted, eligible decisions to test all four interfaces.
    # The real kernel's PR/PM/PRM remain INPUT_INELIGIBLE (tested separately).
    op, decisions, signals = fixture()
    return op, tuple(replace(x, disposition=None) for x in decisions), signals


def allowed(decision, signals):
    return tuple(x for x in signals if x.family in families(decision.information_set.policy))


def intents(rule=None):
    _, decisions, signals = eligible_fixture()
    rule = rule or d.ReferenceRule("1", 1)
    return tuple(d.decide_reference(x, rule, allowed(x, signals)) for x in decisions)


def test_same_function_parameters_different_information_can_change_actions():
    result = intents()
    assert tuple(x.action for x in result) == (d.IntentAction.LONG, d.IntentAction.ABSTAIN,
                                             d.IntentAction.ABSTAIN, d.IntentAction.SHORT)
    assert len({x.rule.identity for x in result}) == 1
    assert len({x.controls_commitment for x in result}) == 1
    assert all(x.reference_only and x.dataset_role is DatasetRole.PILOT for x in result)
    assert d.require_same_rule_experiment(result)
    assert result == intents()


def test_actual_kernel_operational_gates_remain_closed():
    _, decisions, signals = fixture()
    assert d.decide_reference(decisions[0], d.ReferenceRule("1", 1), allowed(decisions[0], signals))
    for decision in decisions[1:]:
        with pytest.raises(ValueError, match="ineligible"):
            d.decide_reference(decision, d.ReferenceRule("1", 1), allowed(decision, signals))


@pytest.mark.parametrize("index,family", [(0, InputType.REGIME), (0, InputType.MECHANICS),
                                         (1, InputType.MECHANICS), (2, InputType.REGIME)])
def test_forbidden_families_rejected(index, family):
    _, decisions, signals = eligible_fixture()
    decision = decisions[index]
    extra = next(x for x in signals if x.family is family)
    with pytest.raises(PermissionError):
        d.decide_reference(decision, d.ReferenceRule("1", 1), allowed(decision, signals) + (extra,))


@pytest.mark.parametrize("status,changes", [
    (InputStatus.MISSING, {"value_hash": None}),
    (InputStatus.UNKNOWN, {"provenance_hash": None}),
    (InputStatus.LATE, {"available_at": _fixtures.T + timedelta(seconds=1)}),
])
def test_noncausal_input_never_falls_back(status, changes):
    op, _, signals = fixture()
    op = replace(op, inputs=(replace(op.inputs[0], status=status, reason_codes=("FIXTURE",), **changes),) + op.inputs[1:])
    decision = PolicyKernel().form(op, _fixtures.controls())[0]
    with pytest.raises(ValueError, match="ineligible"):
        d.decide_reference(decision, d.ReferenceRule("1", 1), signals[:2])


def test_transitive_mechanics_in_price_rejected_upstream():
    op, _, signals = fixture()
    price = replace(op.inputs[1], dependencies=(op.inputs[3],), computed_at=_fixtures.T)
    op = replace(op, inputs=(op.inputs[0], price) + op.inputs[2:])
    decision = PolicyKernel().form(op, _fixtures.controls())[0]
    assert not decision.information_set.causal_eligible
    with pytest.raises(ValueError, match="ineligible"):
        d.decide_reference(decision, d.ReferenceRule("1", 1), signals[:2])


def test_missing_duplicate_forged_and_mutable_signals_rejected():
    _, decisions, signals = fixture()
    decision, rule = decisions[0], d.ReferenceRule("1", 1)
    with pytest.raises(ValueError, match="missing"):
        d.decide_reference(decision, rule, signals[:1])
    with pytest.raises(ValueError, match="duplicate"):
        d.decide_reference(decision, rule, signals[:2] + signals[:1])
    with pytest.raises(ValueError, match="committed"):
        d.decide_reference(decision, rule, (replace(signals[0], vote=-1), signals[1]))
    with pytest.raises(TypeError):
        d.decide_reference(decision, rule, list(signals[:2]))
    with pytest.raises(TypeError):
        d.ReferenceSignal(InputType.PRICE, 1, metadata={"mechanics": 1})


def test_rule_version_parameters_controls_and_role_are_not_interchangeable():
    first = intents()
    changed = intents(d.ReferenceRule("1", 2))
    assert first[0].intent_id != changed[0].intent_id
    with pytest.raises(ValueError, match="incompatible"):
        d.require_same_rule_experiment((first[0], changed[1]))
    with pytest.raises(ValueError, match="version"):
        d.ReferenceRule("2", 1)
    _, decisions, signals = eligible_fixture()
    changes = ({"controls": replace(_fixtures.controls(), outcome_horizon_seconds=7200)},
               {"dataset_role": DatasetRole.CONFIRMATION}, {"opportunity_id": "other"})
    for change in changes:
        other = d.decide_reference(replace(decisions[1], **change), d.ReferenceRule("1", 1), allowed(decisions[1], signals))
        with pytest.raises(ValueError, match="incompatible"):
            d.require_same_rule_experiment((first[0], other))


def test_immutability_order_and_no_controls_change():
    _, decisions, signals = fixture()
    rule = d.ReferenceRule("1", 1)
    decision = decisions[0]
    before = decision.controls.identity
    first = d.decide_reference(decision, rule, signals[:2])
    assert d.decide_reference(decision, rule, tuple(reversed(signals[:2]))) == first
    for obj, field, value in ((signals[0], "vote", -1), (rule, "minimum_absolute_votes", 2),
                              (first, "action", d.IntentAction.SHORT)):
        with pytest.raises(FrozenInstanceError):
            setattr(obj, field, value)
    assert decision.controls.identity == before == first.controls_commitment


def test_direct_intent_mutable_aliases_and_shared_input_conflict():
    result = intents()
    with pytest.raises(TypeError):
        replace(result[0], value_commitments=list(result[0].value_commitments))
    pairs = result[1].value_commitments
    forged = replace(result[1], value_commitments=((pairs[0][0], "different"),) + pairs[1:])
    with pytest.raises(ValueError, match="shared input"):
        d.require_same_rule_experiment((result[0], forged))


@pytest.mark.parametrize("name", ["outcome", "pnl", "ranking", "future_price", "metadata"])
def test_outcome_arguments_rejected(name):
    _, decisions, signals = fixture()
    with pytest.raises(TypeError):
        d.decide_reference(decisions[0], d.ReferenceRule("1", 1), signals[:2], **{name: "forbidden"})
    assert name not in {f.name for f in fields(d.ActionIntent)}


def test_algorithm_cannot_branch_on_policy_or_context():
    assert tuple(inspect.signature(d._reference_action).parameters) == ("votes", "minimum_absolute_votes")
    source = inspect.getsource(d._reference_action)
    names = {node.id for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Name)}
    assert names <= {"votes", "minimum_absolute_votes", "total", "sum", "abs", "IntentAction"}
    for votes, expected in (((1, 0), d.IntentAction.LONG), ((1, -1), d.IntentAction.ABSTAIN),
                            ((1, -1, -1), d.IntentAction.SHORT)):
        assert d._reference_action(votes, 1) is expected


def test_process_independent_identity_and_compile():
    script = ("import sys;sys.path.insert(0,'tests');import test_decision_rule as t;"
              "_,ds,vs=t.eligible_fixture();vs=vs[::-1] if sys.argv[1]=='reverse' else vs;"
              "print(tuple(t.d.decide_reference(x,t.d.ReferenceRule('1',1),t.allowed(x,vs)).intent_id for x in ds))")
    results = [subprocess.check_output([sys.executable, "-B", "-c", script, order], text=True,
        cwd=Path(__file__).resolve().parents[1], env={**os.environ, "PYTHONHASHSEED": seed,
        "PYTHONDONTWRITEBYTECODE": "1"}) for order, seed in (("forward", "13"), ("reverse", "79"))]
    assert results[0] == results[1]
    source = Path(d.__file__).read_text(encoding="utf-8")
    compile(source, d.__file__, "exec")
    for node in ast.walk(ast.parse(source)):
        assert not isinstance(node, ast.Import)
        if isinstance(node, ast.ImportFrom):
            assert node.module in {"dataclasses", "datetime", "enum", "nuisance_pilot_contracts", "policy_kernel"}
