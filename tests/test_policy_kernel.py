"""Synthetic policy fairness invariants. No outcomes or market data."""
from dataclasses import replace, FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
from pathlib import Path
import ast
import os
import subprocess
import sys
import pytest

from core.scientific.nuisance_pilot_contracts import (
    EligibleDecisionOpportunity, InputAvailabilityRecord, InputType, InputStatus,
    DatasetRole, PolicyID, PolicyDisposition,
)
from core.scientific import policy_kernel as k

T = datetime(2020, 1, 1, tzinfo=timezone.utc)


def opportunity():
    identity = EligibleDecisionOpportunity.identity("OMA-PNEP-1.0", "synthetic-event", "BTCUSDT", "Binance USDⓈ-M", "linear perpetual", "H1:2020-01-01T00:00:00Z")
    inputs = tuple(InputAvailabilityRecord(identity, kind, kind.value, "synthetic", "BTCUSDT", "Binance USDⓈ-M",
        "linear perpetual", T, T, InputStatus.VALID, received_at=T, available_at=T, receipt_ids=(kind.value,),
        value_hash="synthetic-" + kind.value, provenance_hash="synthetic-proof", validator_version="fixture") for kind in InputType)
    return EligibleDecisionOpportunity("OMA-PNEP-1.0", "protocol", "run", DatasetRole.PILOT, "population",
        "synthetic-event", "synthetic-cluster", "cluster-rule", "cluster-proof", "BTCUSDT", "Binance USDⓈ-M",
        "linear perpetual", "H1:2020-01-01T00:00:00Z", T, inputs)


def controls():
    return k.SharedControls("0" * 64, "H1", Decimal("100"), "USDT", "1" * 64, "2" * 64,
                            "3" * 64, "4" * 64, "5" * 64, 3600)


def with_input(op, item):
    return replace(op, inputs=tuple(item if x.input_type is item.input_type else x for x in op.inputs))


def test_four_masks_are_detached_and_fair():
    op = opportunity()
    decisions = k.PolicyKernel().form(op, controls())
    assert len({d.comparison_id for d in decisions}) == 1
    assert len({d.decision_id for d in decisions}) == 4
    assert k.require_comparable(decisions) == decisions[0].comparison_id
    for d in decisions:
        view = d.information_set
        assert view.causal_eligible
        assert not hasattr(view, "opportunity")
        for family in InputType:
            if family in k.families(view.policy):
                assert view.get(family).usable
            else:
                with pytest.raises(PermissionError):
                    view.get(family)
        with pytest.raises(FrozenInstanceError):
            d.dataset_role = DatasetRole.CONFIRMATION
    with pytest.raises(ValueError):
        k.PolicyInformationSet(PolicyID.P0, decisions[-1].information_set.evidence)
    assert decisions[0].disposition is None
    assert all(d.disposition is PolicyDisposition.INPUT_INELIGIBLE for d in decisions[1:])


@pytest.mark.parametrize("status,changes", [
    (InputStatus.LATE, {"available_at": T + timedelta(seconds=1)}),
    (InputStatus.UNKNOWN, {"provenance_hash": None}),
    (InputStatus.MISSING, {"value_hash": None}),
    (InputStatus.CONFLICT, {"conflict": True}),
])
def test_invalid_inputs_preserve_population_and_fail_closed(status, changes):
    op = opportunity()
    price = replace(op.inputs[1], status=status, reason_codes=("SYNTHETIC_FAILURE",), **changes)
    original = with_input(op, price)
    decisions = k.PolicyKernel().form(original, controls())
    assert all(not d.information_set.causal_eligible for d in decisions)
    assert all(d.information_set.get(InputType.PRICE).value_hash is None for d in decisions)
    assert all(d.disposition is PolicyDisposition.INPUT_INELIGIBLE for d in decisions)
    assert original.inputs[1] is price
    assert original.opportunity_id == op.opportunity_id


def test_missing_optional_family_only_affects_requiring_policies():
    op = opportunity()
    missing = replace(op.inputs[2], status=InputStatus.MISSING, value_hash=None, reason_codes=("MISSING",))
    decisions = k.PolicyKernel().form(with_input(op, missing), controls())
    assert [d.information_set.causal_eligible for d in decisions] == [True, False, True, False]


def test_replay_order_and_role_firewall():
    op, control, kernel = opportunity(), controls(), k.PolicyKernel()
    first = kernel.form(op, control)
    assert first == kernel.form(replace(op, inputs=tuple(reversed(op.inputs))), control)
    assert first == k.PolicyKernel().form(op, control)
    with pytest.raises(ValueError):
        kernel.form(replace(op, dataset_role=DatasetRole.CONFIRMATION), control)
    # New event identity cannot evade the same-shock role guard.
    other_id = EligibleDecisionOpportunity.identity(op.protocol_id, "other", op.instrument, op.venue, op.product, op.decision_slot_id)
    other = replace(op, event_id="other", dataset_role=DatasetRole.CONFIRMATION,
                    inputs=tuple(replace(x, opportunity_id=other_id) for x in op.inputs))
    with pytest.raises(ValueError, match="cross-role"):
        kernel.form(other, control)


@pytest.mark.parametrize("change", [
    {"risk_budget_quote": Decimal("200")}, {"risk_spec_hash": "a" * 64},
    {"execution_spec_hash": "b" * 64}, {"outcome_horizon_seconds": 7200},
    {"sizing_spec_hash": "c" * 64}, {"accounting_spec_hash": "d" * 64},
    {"transaction_cost_spec_hash": "e" * 64}, {"policy_contract_hash": "f" * 64},
])
def test_different_controls_cannot_appear_comparable(change):
    op = opportunity()
    kernel = k.PolicyKernel()
    first = kernel.form(op, controls())
    altered = replace(controls(), **change)
    with pytest.raises(ValueError, match="controls"):
        kernel.form(op, altered)
    second = k.PolicyKernel().form(op, altered)
    assert first[0].comparison_id != second[1].comparison_id
    with pytest.raises(ValueError):
        k.require_comparable((first[0], second[1]))


def test_provenance_and_value_changes_not_hidden_by_record_id():
    op = opportunity()
    changed = replace(op.inputs[0], value_hash="different", provenance_hash="different")
    assert changed.record_id == op.inputs[0].record_id
    kernel = k.PolicyKernel()
    first = kernel.form(op, controls())
    with pytest.raises(ValueError, match="snapshot"):
        kernel.form(with_input(op, changed), controls())
    second = k.PolicyKernel().form(with_input(op, changed), controls())
    with pytest.raises(ValueError):
        k.require_comparable((first[0], second[1]))


def test_adversarial_dependency_cannot_smuggle_regime_into_p0():
    op = opportunity()
    price = replace(op.inputs[1], dependencies=(op.inputs[2],), computed_at=T)
    decisions = k.PolicyKernel().form(with_input(op, price), controls())
    assert not decisions[0].information_set.causal_eligible
    assert not decisions[2].information_set.causal_eligible
    assert decisions[1].information_set.causal_eligible
    assert not hasattr(decisions[0].information_set.get(InputType.PRICE), "dependencies")
    assert decisions[0].information_set.get(InputType.PRICE).value_hash is None


def test_decimal_context_does_not_round_identity_and_controls_are_immutable():
    control = replace(controls(), risk_budget_quote=Decimal("123456789.123456789"))
    before = control.identity
    with localcontext() as context:
        context.prec = 4
        assert control.identity == before
    with pytest.raises(FrozenInstanceError):
        control.risk_budget_quote = Decimal("1")
    with pytest.raises(ValueError):
        replace(control, execution_spec_hash={"mutable": "spec"})


def test_equivalent_decimal_representations_have_one_identity():
    op = opportunity()
    variants = [replace(controls(), risk_budget_quote=Decimal(x)) for x in ("100", "100.00", "1E+2")]
    assert len({c.identity for c in variants}) == 1
    assert len({k.PolicyKernel().form(op, c)[0].decision_id for c in variants}) == 1


def test_dependency_order_does_not_change_evidence_identity():
    op = opportunity()
    price = replace(op.inputs[1], dependencies=(op.inputs[0], op.inputs[2]), computed_at=T)
    a = with_input(op, price)
    b = with_input(op, replace(price, dependencies=tuple(reversed(price.dependencies))))
    kernel = k.PolicyKernel()
    assert kernel.form(a, controls()) == kernel.form(b, controls())


def test_two_independent_python_processes_produce_same_ids():
    script = ("import sys,json; sys.path.insert(0,'tests'); "
              "from test_policy_kernel import opportunity,controls; "
              "from core.scientific.policy_kernel import PolicyKernel; "
              "print(json.dumps([d.decision_id for d in PolicyKernel().form(opportunity(),controls())]))")
    outputs = [subprocess.check_output([sys.executable, "-B", "-c", script],
               cwd=Path(__file__).resolve().parents[1],
               env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"}, text=True)
               for seed in ("11", "97")]
    assert outputs[0] == outputs[1]


def test_mutable_nested_inputs_rejected_and_snapshot_detached():
    op = opportunity()
    for changes in ({"value_hash": {"nested": ["forbidden"]}}, {"dependencies": [op.inputs[0]]},
                    {"receipt_ids": ["mutable"]}):
        with pytest.raises(TypeError):
            replace(op.inputs[1], **changes)
    decision = k.PolicyKernel().form(op, controls())[0]
    before = decision.decision_id
    replace(op.inputs[0], value_hash="other")
    assert decision.decision_id == before
    with pytest.raises(FrozenInstanceError):
        decision.information_set.evidence[0].value_hash = "mutated"


@pytest.mark.parametrize("offset", [-1, 0])
def test_causal_boundary_before_and_equal(offset):
    op = opportunity()
    at = T + timedelta(seconds=offset)
    price = replace(op.inputs[1], received_at=at, available_at=at)
    assert k.PolicyKernel().form(with_input(op, price), controls())[0].information_set.causal_eligible


def test_adversarial_inconsistent_evidence_and_copied_decision_metadata():
    decisions = k.PolicyKernel().form(opportunity(), controls())
    item = decisions[0].information_set.get(InputType.EVENT)
    with pytest.raises(ValueError):
        replace(item, status=InputStatus.UNKNOWN)
    altered_view = replace(decisions[1].information_set,
                           evidence=(replace(item, value_hash="incompatible-value"),) + decisions[1].information_set.evidence[1:])
    with pytest.raises(ValueError, match="shared information"):
        k.require_comparable((decisions[0], replace(decisions[1], information_set=altered_view)))
    changed = replace(decisions[0], dataset_role=DatasetRole.CONFIRMATION)
    assert changed.decision_id != decisions[0].decision_id
    with pytest.raises(ValueError):
        k.require_comparable((changed, decisions[1]))


@pytest.mark.parametrize("field", ["outcome", "pnl", "future_price", "future_funding", "ranking", "sharpe"])
def test_outcomes_not_accepted_by_formation(field):
    with pytest.raises(TypeError):
        k.PolicyKernel().form(opportunity(), controls(), **{field: "FORBIDDEN"})
    with pytest.raises(TypeError):
        replace(controls(), **{field: "FORBIDDEN"})


def test_new_module_has_no_operational_or_outcome_imports_and_compiles():
    source = Path(k.__file__).read_text(encoding="utf-8")
    compile(source, str(k.__file__), "exec")
    for node in ast.walk(ast.parse(source)):
        assert not isinstance(node, ast.Import)
        if isinstance(node, ast.ImportFrom):
            assert node.module in {"dataclasses", "datetime", "decimal", "enum", "nuisance_pilot_contracts"}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "exec", "eval", "__import__"}
