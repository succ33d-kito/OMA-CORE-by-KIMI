"""Synthetic pre-outcome population contract tests."""
from dataclasses import replace, FrozenInstanceError
from datetime import timedelta
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import pytest

from core.scientific import experimental_manifest as m
from core.scientific.common_support import CommonSupportRegistry
from core.scientific.policy_kernel import PolicyKernel
from core.scientific.nuisance_pilot_contracts import DatasetRole, InputStatus

_spec = importlib.util.spec_from_file_location("_manifest_fixtures", Path(__file__).with_name("test_policy_kernel.py"))
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
opportunity, controls, T = _fixtures.opportunity, _fixtures.controls, _fixtures.T


def scope():
    return m.PopulationScope("OMA-PNEP-1.0", "protocol", "run", DatasetRole.PILOT, "population", T)


def other_op():
    op = opportunity()
    identity = op.identity(op.protocol_id, "second", op.instrument, op.venue, op.product, op.decision_slot_id)
    return replace(op, event_id="second", event_cluster_id="second-cluster",
                   inputs=tuple(replace(i, opportunity_id=identity) for i in op.inputs))


def add(builder, op=None, count=4, ctl=None):
    op, ctl = op or opportunity(), ctl or controls()
    decisions = PolicyKernel().form(op, ctl)[:count]
    support = CommonSupportRegistry().register(op, ctl, decisions)
    builder.add(op, ctl, decisions, support)
    return support


def manifest(ops=None):
    builder = m.PopulationManifestBuilder(scope())
    for op in ops if ops is not None else (opportunity(), other_op()):
        add(builder, op)
    return builder.freeze(T)


def test_order_membership_and_materialization_time():
    full = manifest()
    assert manifest((other_op(), opportunity())).manifest_id == full.manifest_id
    assert manifest((opportunity(),)).manifest_id != full.manifest_id
    assert replace(full, frozen_at=T + timedelta(seconds=1)).manifest_id == full.manifest_id
    assert replace(full, frozen_at=T + timedelta(seconds=1)).artifact_id != full.artifact_id


@pytest.mark.parametrize("changes", [
    {"protocol_hash": "v2"}, {"population_rule_hash": "v2"}, {"run_id": "other"},
    {"dataset_role": DatasetRole.CONFIRMATION}, {"population_cutoff": T + timedelta(seconds=1)},
])
def test_scope_changes_identity_and_mismatches_rejected(changes):
    changed = replace(scope(), **changes)
    empty = m.PopulationManifestBuilder(scope()).freeze(T)
    new = m.PopulationManifestBuilder(changed).freeze(T + timedelta(seconds=1))
    assert empty.manifest_id != new.manifest_id
    if "population_cutoff" not in changes:
        with pytest.raises(ValueError, match="scope mismatch"):
            add(m.PopulationManifestBuilder(changed))


def test_duplicates_freeze_and_no_retroactive_expansion(tmp_path):
    builder = m.PopulationManifestBuilder(scope())
    add(builder)
    with pytest.raises(ValueError, match="duplicate"):
        add(builder)
    frozen = builder.freeze(T)
    original = frozen.to_json()
    assert builder.freeze(T) is frozen
    assert builder.state is m.ManifestState.FROZEN
    with pytest.raises(ValueError, match="FROZEN"):
        add(builder, other_op())
    with pytest.raises(ValueError, match="FROZEN"):
        builder.freeze(T + timedelta(seconds=1))
    for name, value in (("records", ()), ("scope", replace(scope(), protocol_hash="v2")), ("frozen_at", T + timedelta(seconds=1))):
        with pytest.raises(FrozenInstanceError):
            setattr(frozen, name, value)
    path = tmp_path / "manifest.json"
    frozen.write_exclusive(path)
    with pytest.raises(FileExistsError):
        frozen.write_exclusive(path)
    assert path.read_text().strip() == original == frozen.to_json()
    assert json.loads(original)["manifest_id"] == frozen.manifest_id


def test_absent_ineligible_policy_and_support_commitments():
    op = opportunity()
    missing = replace(op, inputs=tuple(replace(i, status=InputStatus.MISSING, value_hash=None,
        reason_codes=("MISSING",)) if i is op.inputs[3] else i for i in op.inputs))
    manifests = []
    for current, count, ctl in ((missing, 2, controls()), (missing, 4, controls()),
                                (op, 4, controls()), (op, 4, replace(controls(), risk_budget_quote=controls().risk_budget_quote * 2))):
        builder = m.PopulationManifestBuilder(scope())
        add(builder, current, count, ctl)
        manifests.append(builder.freeze(T))
    assert len({x.manifest_id for x in manifests}) == 4
    assert manifests[0].records[0].eligible_policies == manifests[1].records[0].eligible_policies
    assert manifests[0].records[0].exclusions != manifests[1].records[0].exclusions
    assert manifests[2].records[0].decision_commitments != manifests[3].records[0].decision_commitments


def test_support_and_policy_replacement_rejected_atomically():
    op, ctl = opportunity(), controls()
    decisions = PolicyKernel().form(op, ctl)
    support = CommonSupportRegistry().register(op, ctl, decisions[:2])
    builder = m.PopulationManifestBuilder(scope())
    with pytest.raises(ValueError, match="support commitment mismatch"):
        builder.add(op, ctl, decisions, support)
    with pytest.raises(ValueError, match="PROVENANCE"):
        builder.add(op, ctl, (replace(decisions[0], opportunity_commitment="forged"),), support)
    assert builder.freeze(T).records == ()


@pytest.mark.parametrize("field", ["received_at", "available_at", "source_event_time"])
def test_post_cutoff_evidence_cannot_enter(field):
    op = opportunity()
    changes = {field: T + timedelta(seconds=1), "status": InputStatus.MISSING,
               "value_hash": None, "reason_codes": ("MISSING",)}
    late = replace(op, inputs=(replace(op.inputs[0], **changes),) + op.inputs[1:])
    builder = m.PopulationManifestBuilder(scope())
    with pytest.raises(ValueError, match="post-cutoff"):
        add(builder, late)
    assert builder.freeze(T).records == ()


def test_temporal_boundaries_and_mutable_aliases():
    with pytest.raises(ValueError):
        replace(scope(), population_cutoff=T.replace(tzinfo=None))
    builder = m.PopulationManifestBuilder(scope())
    with pytest.raises(ValueError):
        builder.freeze(T - timedelta(seconds=1))
    add(builder)
    frozen = builder.freeze(T)
    with pytest.raises(TypeError):
        replace(frozen, records=list(frozen.records))
    with pytest.raises(TypeError):
        replace(frozen, records=(replace(frozen.records[0], eligible_policies=[]),))
    with pytest.raises(FrozenInstanceError):
        frozen.scope.population_cutoff = T + timedelta(seconds=1)
    earlier = m.PopulationManifestBuilder(replace(scope(), population_cutoff=T - timedelta(seconds=1)))
    with pytest.raises(ValueError, match="after cutoff"):
        add(earlier)


@pytest.mark.parametrize("field", ["outcome", "pnl", "performance", "winner", "future_labels", "metadata"])
def test_outcome_arguments_not_accepted(field):
    with pytest.raises(TypeError):
        m.PopulationManifestBuilder(scope(), **{field: "forbidden"})
    builder = m.PopulationManifestBuilder(scope())
    with pytest.raises(TypeError):
        builder.freeze(T, **{field: "forbidden"})


def test_process_independent_identity_and_compile():
    script = ("import sys;sys.path.insert(0,'tests');from test_experimental_manifest import *;"
              "ops=(opportunity(),other_op());ops=ops[::-1] if sys.argv[1]=='reverse' else ops;"
              "print(manifest(ops).manifest_id)")
    results = [subprocess.check_output([sys.executable, "-B", "-c", script, order], text=True,
        cwd=Path(__file__).resolve().parents[1], env={**os.environ, "PYTHONHASHSEED": seed,
        "PYTHONDONTWRITEBYTECODE": "1"}) for order, seed in (("forward", "13"), ("reverse", "79"))]
    assert results[0] == results[1]
    compile(Path(m.__file__).read_text(encoding="utf-8"), m.__file__, "exec")
