"""Synthetic support invariants; reuse the policy kernel's synthetic fixtures."""
from dataclasses import replace, FrozenInstanceError
from datetime import timedelta
from pathlib import Path
import ast
import importlib.util
import os
import subprocess
import sys
import pytest

_spec = importlib.util.spec_from_file_location("_support_kernel_fixtures", Path(__file__).with_name("test_policy_kernel.py"))
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
opportunity, controls, with_input, T = (_fixtures.opportunity, _fixtures.controls, _fixtures.with_input, _fixtures.T)
from core.scientific.policy_kernel import PolicyKernel
from core.scientific.nuisance_pilot_contracts import PolicyID, DatasetRole, InputStatus, EligibleDecisionOpportunity
from core.scientific import common_support as cs


def form(op=None):
    return PolicyKernel().form(op or opportunity(), controls())


def test_cs4_partial_missing_and_empty_are_retained():
    op, decisions = opportunity(), form()
    for selected, support in ((decisions, tuple(PolicyID)), (decisions[:2], (PolicyID.P0, PolicyID.PR)),
                              (decisions[:3], (PolicyID.P0, PolicyID.PR, PolicyID.PM)), ((), ())):
        registry = cs.CommonSupportRegistry()
        record = registry.register(op, controls(), selected)
        assert record.eligible_policies == support
        assert record.cs4 is (len(support) == 4)
        assert registry.records() == (record,)
        assert len(record.decision_commitments) == len(selected)
        assert all(x.reasons == (cs.ExclusionReason.MISSING_DECISION,) for x in record.exclusions)
        assert record.supports((PolicyID.P0, PolicyID.PR)) is (PolicyID.PR in support)


@pytest.mark.parametrize("status,changes,reason", [
    (InputStatus.MISSING, {"value_hash": None}, cs.ExclusionReason.MISSING_REQUIRED_INFORMATION),
    (InputStatus.UNKNOWN, {"provenance_hash": None}, cs.ExclusionReason.UNKNOWN_AVAILABILITY),
    (InputStatus.LATE, {"available_at": T + timedelta(seconds=1)}, cs.ExclusionReason.LATE_INFORMATION),
    (InputStatus.CONFLICT, {"conflict": True}, cs.ExclusionReason.CONFLICT),
])
def test_ineligible_mechanics_preserves_other_support(status, changes, reason):
    op = opportunity()
    op = with_input(op, replace(op.inputs[3], status=status, reason_codes=("FIXTURE",), **changes))
    decisions = form(op)
    before = tuple(d.decision_id for d in decisions)
    record = cs.CommonSupportRegistry().register(op, controls(), decisions)
    assert record.eligible_policies == (PolicyID.P0, PolicyID.PR)
    assert not record.cs4
    assert {x.policy for x in record.exclusions} == {PolicyID.PM, PolicyID.PRM}
    assert all(x.reasons == (reason,) for x in record.exclusions)
    assert before == tuple(d.decision_id for d in decisions)
    assert op.inputs[3].status is status


@pytest.mark.parametrize("changes,reason", [
    ({"opportunity_id": "different"}, "OPPORTUNITY_MISMATCH"),
    ({"dataset_role": DatasetRole.CONFIRMATION}, "ROLE_MISMATCH"),
    ({"instrument": "ETHUSDT"}, "CONTROL_MISMATCH"),
    ({"decision_at": T + timedelta(seconds=1)}, "CONTROL_MISMATCH"),
    ({"opportunity_commitment": "forged"}, "PROVENANCE_OR_IDENTITY_CONFLICT"),
])
def test_incompatible_decisions_fail_atomically(changes, reason):
    registry = cs.CommonSupportRegistry()
    decisions = form()
    with pytest.raises(ValueError, match=reason):
        registry.register(opportunity(), controls(), (decisions[0], replace(decisions[1], **changes)))
    assert registry.records() == ()


def test_controls_duplicate_and_mutable_input_rejected():
    decisions = form()
    registry = cs.CommonSupportRegistry()
    with pytest.raises(ValueError, match="CONTROL_MISMATCH"):
        registry.register(opportunity(), controls(), (replace(decisions[0], controls=replace(controls(), outcome_horizon_seconds=7200)),))
    with pytest.raises(ValueError, match="DUPLICATE"):
        registry.register(opportunity(), controls(), (decisions[0], decisions[0]))
    with pytest.raises(TypeError):
        registry.register(opportunity(), controls(), list(decisions))
    record = registry.register(opportunity(), controls(), decisions)
    with pytest.raises(FrozenInstanceError):
        record.eligible_policies = ()


def test_order_replay_and_no_retrospective_support_expansion():
    op, decisions, registry = opportunity(), form(), cs.CommonSupportRegistry()
    first = registry.register(op, controls(), decisions)
    assert registry.register(op, controls(), tuple(reversed(decisions))) is first
    assert cs.CommonSupportRegistry().register(op, controls(), tuple(reversed(decisions))) == first
    other = cs.CommonSupportRegistry()
    partial = other.register(op, controls(), decisions[:2])
    assert partial.support_id != first.support_id
    with pytest.raises(ValueError, match="SUPPORT_SNAPSHOT_CONFLICT"):
        other.register(op, controls(), decisions)
    assert other.records() == (partial,)


def test_changed_eligibility_changes_id_but_cannot_repair_history():
    op = opportunity()
    missing = with_input(op, replace(op.inputs[2], status=InputStatus.MISSING, value_hash=None, reason_codes=("MISSING",)))
    registry = cs.CommonSupportRegistry()
    first = registry.register(missing, controls(), form(missing))
    full = cs.CommonSupportRegistry().register(op, controls(), form())
    assert first.support_id != full.support_id
    with pytest.raises(ValueError):
        registry.register(op, controls(), form())


def test_input_order_and_absent_vs_ineligible_identity():
    op = opportunity()
    op = with_input(op, replace(op.inputs[3], status=InputStatus.MISSING, value_hash=None, reason_codes=("MISSING",)))
    decisions = form(op)
    full = cs.CommonSupportRegistry().register(op, controls(), decisions)
    reordered = replace(op, inputs=tuple(reversed(op.inputs)))
    assert cs.CommonSupportRegistry().register(reordered, controls(), form(reordered)) == full
    absent = cs.CommonSupportRegistry().register(op, controls(), decisions[:2])
    assert absent.eligible_policies == full.eligible_policies
    assert absent.support_id != full.support_id
    assert all(x.reasons == (cs.ExclusionReason.MISSING_DECISION,) for x in absent.exclusions)
    assert all(x.reasons == (cs.ExclusionReason.MISSING_REQUIRED_INFORMATION,) for x in full.exclusions)


def test_same_cluster_cannot_cross_roles_with_new_opportunity():
    op, registry = opportunity(), cs.CommonSupportRegistry()
    registry.register(op, controls(), form())
    identity = EligibleDecisionOpportunity.identity(op.protocol_id, "other-event", op.instrument, op.venue, op.product, op.decision_slot_id)
    other = replace(op, event_id="other-event", dataset_role=DatasetRole.CONFIRMATION,
                    inputs=tuple(replace(i, opportunity_id=identity) for i in op.inputs))
    with pytest.raises(ValueError, match="cross-role"):
        registry.register(other, controls(), form(other))
    assert len(registry.records()) == 1


def test_forged_usability_cannot_shrink_support_despite_copied_hash():
    decisions = form()
    view = decisions[0].information_set
    evidence = replace(view.evidence[0], usable=False, value_hash=None, reason="INPUT_OR_DEPENDENCY_INELIGIBLE")
    forged = replace(decisions[0], information_set=replace(view, evidence=(evidence, view.evidence[1])))
    with pytest.raises(ValueError, match="PROVENANCE_OR_IDENTITY_CONFLICT"):
        cs.CommonSupportRegistry().register(opportunity(), controls(), (forged,))


@pytest.mark.parametrize("name", ["outcome", "future_price", "performance", "metadata"])
def test_outcome_payload_not_accepted(name):
    with pytest.raises(TypeError):
        cs.CommonSupportRegistry().register(opportunity(), controls(), form(), **{name: {"nested": "forbidden"}})


def test_two_independent_processes_and_different_policy_order():
    script = ("import sys;sys.path.insert(0,'tests');from test_common_support import *;"
              "d=form();d=tuple(reversed(d)) if sys.argv[1]=='reverse' else d;"
              "print(cs.CommonSupportRegistry().register(opportunity(),controls(),d).support_id)")
    result = [subprocess.check_output([sys.executable, "-B", "-c", script, order], text=True,
              cwd=Path(__file__).resolve().parents[1],
              env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"})
              for order, seed in (("forward", "13"), ("reverse", "79"))]
    assert result[0] == result[1]


def test_compile_and_import_boundary():
    source = Path(cs.__file__).read_text(encoding="utf-8")
    compile(source, str(cs.__file__), "exec")
    for node in ast.walk(ast.parse(source)):
        assert not isinstance(node, ast.Import)
        if isinstance(node, ast.ImportFrom):
            assert node.module in {"dataclasses", "datetime", "enum", "nuisance_pilot_contracts", "policy_kernel"}
