"""Synthetic Slice 1 acceptance: no market files, prices or policy execution."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pytest

from core.scientific import nuisance_pilot_contracts as c
from core.scientific.nuisance_pilot_store import (
    ConflictError, OpportunityStore, DatasetManifest, ManifestEntry,
    StaticMetadata, validate_isolation,
)

T = datetime(2020, 1, 1, tzinfo=timezone.utc)
OP = c.EligibleDecisionOpportunity.identity("OMA-PNEP-1.0", "event", "SYNTH", "SIM", "TEST", "slot")


def assessment(kind=c.InputType.EVENT, **changes):
    data = dict(opportunity_id=OP, input_type=kind, input_key=kind.value,
                source="SYNTHETIC", instrument="SYNTH", venue="SIM", product="TEST",
                decision_at=T, assessed_at=T, status=c.InputStatus.VALID,
                received_at=T, available_at=T, receipt_ids=("synthetic-receipt",),
                value_hash="synthetic-value", provenance_hash="synthetic-proof", validator_version="fixture-v1")
    data.update(changes)
    return c.InputAvailabilityRecord(**data)


def opportunity(**changes):
    data = dict(protocol_id="OMA-PNEP-1.0", protocol_hash="synthetic-protocol", run_id="synthetic-run",
                dataset_role=c.DatasetRole.PILOT, population_rule_hash="synthetic-population",
                event_id="event", event_cluster_id="cluster", cluster_rule_version="fixture-v1",
                cluster_evidence_hash="synthetic-cluster", instrument="SYNTH", venue="SIM", product="TEST",
                decision_slot_id="slot", decision_at=T, inputs=tuple(assessment(k) for k in c.InputType))
    data.update(changes)
    return c.EligibleDecisionOpportunity(**data)


def entry(suffix="a", **changes):
    data = dict(opportunity_id="op-" + suffix, event_id="event-" + suffix,
                event_cluster_id="cluster-" + suffix, economic_observation_hash="econ-" + suffix,
                content_hash="content-" + suffix, outcome_domain="universe-" + suffix,
                outcome_start=T, outcome_end=T + timedelta(hours=1))
    data.update(changes)
    return ManifestEntry(**data)


def pair(a, b, role=c.DatasetRole.CONFIRMATION):
    return (DatasetManifest(c.DatasetRole.PILOT, (a,)), DatasetManifest(role, (b,)))


@pytest.mark.parametrize("enum", [c.DatasetRole, c.InputStatus, c.PolicyID, c.PolicyDisposition,
    c.InputType, c.PilotState, c.OutcomeIntegrity, c.EvidenceType, c.AccessClass,
    c.ExecutionScenario, c.ValuationMode, c.CostComponent, c.CostBasis, c.Direction, c.LatencyKind])
def test_unknown_enum_fails_closed(enum):
    with pytest.raises(ValueError):
        enum("UNRECOGNIZED")


def test_future_information_not_valid():
    with pytest.raises(ValueError):
        assessment(available_at=T + timedelta(seconds=1))
    assert assessment(available_at=T + timedelta(seconds=1), status=c.InputStatus.LATE,
                      reason_codes=("AFTER_CUT",)).status is c.InputStatus.LATE


def test_unknown_missing_and_conflict_are_explicit():
    assert assessment(provenance_hash=None, status=c.InputStatus.UNKNOWN,
                      reason_codes=("NO_PROOF",)).status is not c.InputStatus.VALID
    assert assessment(value_hash=None, status=c.InputStatus.MISSING,
                      reason_codes=("NO_VALUE",)).status is c.InputStatus.MISSING
    with pytest.raises(ValueError):
        assessment(conflict=True)
    assert assessment(conflict=True, status=c.InputStatus.CONFLICT,
                      reason_codes=("CONFLICT",)).status is c.InputStatus.CONFLICT


def test_precedence():
    ordered = c.STATUS_PRECEDENCE
    for n, expected in enumerate(ordered):
        assert c.worst_status(reversed(ordered[n:])) is expected


def test_mutable_proof_and_string_enum_rejected():
    with pytest.raises(TypeError):
        assessment(provenance_hash={"untrusted": "proof"})
    with pytest.raises(TypeError):
        assessment(status="VALID")
    with pytest.raises(TypeError):
        assessment(receipt_ids=["receipt"])


def test_duplicate_idempotent_and_conflict_no_overwrite():
    store = OpportunityStore()
    record = opportunity()
    assert store.append(record) is True
    assert store.append(replace(record)) is False
    with pytest.raises(ConflictError):
        store.append(replace(record, run_id="incompatible-run"))
    assert store.population() == (record,)


def test_role_does_not_change_identity_or_escape_store():
    a = opportunity()
    b = replace(a, dataset_role=c.DatasetRole.CONFIRMATION)
    assert a.opportunity_id == b.opportunity_id
    store = OpportunityStore()
    store.append(a)
    with pytest.raises(ConflictError):
        store.append(b)


def test_ineligible_retained_not_abstention_and_no_kernel():
    missing = assessment(c.InputType.PRICE, value_hash=None, status=c.InputStatus.MISSING, reason_codes=("NO_VALUE",))
    record = opportunity(inputs=tuple(missing if k is c.InputType.PRICE else assessment(k) for k in c.InputType))
    store = OpportunityStore()
    store.append(record)
    assert store.population() == (record,)
    for policy in c.PolicyID:
        assert record.input_disposition(policy) is c.PolicyDisposition.INPUT_INELIGIBLE
    assert c.PolicyDisposition.INPUT_INELIGIBLE.value != c.PolicyDisposition.POLICY_ABSTAIN.value
    assert opportunity().input_disposition(c.PolicyID.P0) is None
    assert opportunity().input_disposition(c.PolicyID.PRM) is c.PolicyDisposition.INPUT_INELIGIBLE


def test_later_arrival_cannot_repair_original_assessment():
    unknown = assessment(provenance_hash=None, status=c.InputStatus.UNKNOWN, reason_codes=("NO_PROOF",))
    original = opportunity(inputs=(unknown,) + tuple(assessment(k) for k in c.InputType if k is not c.InputType.EVENT))
    store = OpportunityStore()
    store.append(original)
    with pytest.raises(ConflictError):
        store.append(opportunity())
    assert store.population()[0].inputs[0].status is c.InputStatus.UNKNOWN
    with pytest.raises(ValueError):
        assessment(assessed_at=T + timedelta(seconds=1))


@pytest.mark.parametrize("status", [c.InputStatus.UNKNOWN, c.InputStatus.MISSING, c.InputStatus.CONFLICT, c.InputStatus.LATE])
def test_invalid_dependency_never_valid(status):
    changes = {c.InputStatus.UNKNOWN: dict(provenance_hash=None), c.InputStatus.MISSING: dict(value_hash=None),
               c.InputStatus.CONFLICT: dict(conflict=True), c.InputStatus.LATE: dict(available_at=T + timedelta(seconds=1))}[status]
    dependency = assessment(status=status, reason_codes=("SYNTHETIC_REASON",), **changes)
    with pytest.raises(ValueError):
        assessment(c.InputType.REGIME, dependencies=(dependency,), computed_at=T,
                   available_at=max(T, dependency.available_at))


def test_derived_maximum_and_receipt_semantics():
    dependency = assessment(received_at=T - timedelta(seconds=3), available_at=T - timedelta(seconds=2))
    derived = assessment(c.InputType.REGIME, dependencies=(dependency,), computed_at=T - timedelta(seconds=1),
                         received_at=None, available_at=T - timedelta(seconds=1))
    assert derived.status is c.InputStatus.VALID
    assert derived.dependency_ids == (dependency.record_id,)
    with pytest.raises(ValueError):
        replace(derived, available_at=T - timedelta(seconds=2))
    with pytest.raises(ValueError):
        assessment(received_at=T + timedelta(seconds=1))
    with pytest.raises(ValueError):
        assessment(decision_at=T.replace(tzinfo=None))


def test_derived_input_cannot_precede_its_declared_receipt():
    with pytest.raises(ValueError, match="availability precedes receipt"):
        assessment(c.InputType.REGIME, dependencies=(assessment(),), computed_at=T,
                   available_at=T, received_at=T + timedelta(seconds=1))


@pytest.mark.parametrize("key", ["opportunity_id", "event_id", "event_cluster_id", "economic_observation_hash", "content_hash"])
@pytest.mark.parametrize("role", [c.DatasetRole.DISCOVERY, c.DatasetRole.CONFIRMATION])
def test_cross_role_identity_collisions(key, role):
    a = entry()
    with pytest.raises(ConflictError, match=key):
        validate_isolation(pair(a, entry("b", **{key: getattr(a, key)}), role))


def test_overlap_and_boundary_and_receipts():
    a = entry()
    with pytest.raises(ConflictError, match="overlap"):
        validate_isolation(pair(a, entry("b", outcome_domain=a.outcome_domain)))
    assert validate_isolation(pair(a, entry("b", outcome_domain=a.outcome_domain,
        outcome_start=a.outcome_end, outcome_end=a.outcome_end + timedelta(hours=1))))
    with pytest.raises(ConflictError, match="receipt"):
        validate_isolation(pair(replace(a, dynamic_receipt_ids=("receipt",)), entry("b", dynamic_receipt_ids=("receipt",))))


def test_shareable_static_metadata_and_no_relabeling():
    static = StaticMetadata("static-hash", "PRODUCT_METADATA", True)
    left, right = pair(entry(), entry("b"))
    assert validate_isolation((replace(left, static_metadata=(static,)), replace(right, static_metadata=(static,))))
    with pytest.raises(ValueError):
        StaticMetadata("hash", "OUTCOME", True)
    with pytest.raises(ConflictError):
        validate_isolation((left, replace(right, static_metadata=(replace(static, content_hash=left.entries[0].content_hash),))))


def test_invalid_terminal_and_parameter_ready_unreachable():
    run = c.PilotRun()
    run.transition(c.PilotState.COLLECTING)
    run.transition(c.PilotState.INSUFFICIENT_INFORMATION)
    run.transition(c.PilotState.COLLECTING)
    with pytest.raises(ValueError):
        run.transition(c.PilotState.PARAMETER_READY)
    run.transition(c.PilotState.INVALID)
    for state in c.PilotState:
        with pytest.raises(ValueError):
            run.transition(state)
    with pytest.raises(TypeError):
        run.transition(c.PilotState.PARAMETER_READY, pnl=1)
    assert run.state is c.PilotState.INVALID
