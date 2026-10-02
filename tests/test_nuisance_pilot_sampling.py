"""Synthetic contract fixtures only; no collectors, data files or network."""
import ast
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.scientific import nuisance_pilot_sampling as s
from core.scientific.nuisance_pilot_contracts import DatasetRole, InputStatus, InputType
from core.scientific.nuisance_pilot_store import ConflictError, DatasetManifest, ManifestEntry, validate_isolation

T = datetime(2020, 1, 1, 10, 23, tzinfo=timezone.utc)
CUT = T.replace(hour=11, minute=0)


def envelope(**changes):
    data = dict(source="synthetic-feed", source_version="fixture-v1", document_id="doc-1",
                revision_id="revision-1", content_hash="synthetic-content", receipt_id="receipt-1",
                received_at=T, processed_at=T, available_at=T, assets=("BTC",),
                binding_unambiguous=True, announcement_count=1,
                shock_evidence=s.ShockEvidence.OFFICIAL_ANNOUNCEMENT,
                shock_namespace="synthetic-issuer", shock_key="announcement-1",
                evidence_hash="synthetic-evidence", receipt_verified=True,
                integrity_verified=True, provenance_hash="synthetic-provenance")
    data.update(changes)
    return s.SyntheticEventEnvelope(**data)


def sampler():
    return s.SyntheticSampler((s.SourceConfig("synthetic-feed", "fixture-v1", T - timedelta(days=1)),))


def run(e=None, role=DatasetRole.PILOT):
    registry = sampler()
    registry.register(e or envelope(), role=role)
    registry.close(CUT)
    return registry


@pytest.mark.parametrize("at,expected", [
    (T, CUT), (T.replace(minute=59, second=59), CUT), (CUT, CUT + timedelta(hours=1))])
def test_strict_h1_boundary(at, expected):
    assert s.decision_slot(at) == (expected, "H1:" + expected.strftime("%Y-%m-%dT%H:%M:%SZ"))


def test_identity_processing_role_and_revision():
    e = envelope()
    assert e.event_id == replace(e, processed_at=T + timedelta(seconds=1), available_at=T + timedelta(seconds=1)).event_id
    assert e.event_id != replace(e, revision_id="revision-2").event_id
    a, b = run(), run(role=DatasetRole.CONFIRMATION)
    assert a.population()[0].opportunity_id == b.population()[0].opportunity_id
    assert a.population()[0].event_id == b.population()[0].event_id
    registry = sampler()
    registry.register(e)
    with pytest.raises(ConflictError):
        registry.register(replace(e, receipt_id="receipt-2", content_hash="incompatible"))
    with pytest.raises(ConflictError):
        registry.register(replace(e, receipt_id="receipt-2", source_version="drift"))


@pytest.mark.parametrize("field", ["received_at", "processed_at", "available_at", "event_time", "published_at"])
def test_naive_time_rejected(field):
    with pytest.raises(ValueError):
        envelope(**{field: T.replace(tzinfo=None)})


def test_inconsistent_availability_rejected():
    with pytest.raises(ValueError):
        envelope(received_at=T + timedelta(seconds=1))
    with pytest.raises(ValueError):
        envelope(processed_at=T + timedelta(seconds=1))


@pytest.mark.parametrize("changes", [
    {"received_at": None, "published_at": T}, {"receipt_id": None},
    {"receipt_verified": False}, {"integrity_verified": False}, {"provenance_hash": None},
    {"source": "unauthorized"}, {"source_version": "unknown"},
    {"assets": ()}, {"assets": ("CRYPTO",)}, {"assets": ("MACRO",)}, {"assets": ("ETH",)},
    {"binding_unambiguous": False}, {"announcement_count": 2},
    {"shock_evidence": s.ShockEvidence.UNKNOWN}, {"evidence_hash": None},
    {"processed_at": None}, {"available_at": None},
])
def test_fail_closed_admission(changes):
    assert run(envelope(**changes)).population() == ()


def test_authorization_must_precede_receipt():
    registry = s.SyntheticSampler((s.SourceConfig("synthetic-feed", "fixture-v1", T),))
    registry.register(envelope())
    assert registry.close(CUT) == ()


def test_late_admission_has_no_rollover_or_processing_slot_change():
    e = envelope(processed_at=CUT + timedelta(seconds=1), available_at=CUT + timedelta(seconds=1))
    registry = sampler()
    candidate = registry.register(e)
    reservation = registry.reservations()[0]
    assert reservation.decision_at == CUT
    assert not registry.sampling_eligible(candidate.reservation_id, CUT)
    first = registry.close(CUT)
    assert first[0].reasons == ("ADMISSION_LATE_NO_ROLLOVER",)
    registry.register(replace(e, document_id="doc-2", receipt_id="receipt-2",
                              received_at=CUT + timedelta(minutes=2),
                              processed_at=CUT + timedelta(minutes=2), available_at=CUT + timedelta(minutes=2)))
    assert registry.close(CUT + timedelta(hours=2)) == first
    assert registry.reservations() == (reservation,)
    assert not registry.population()
    with pytest.raises(ValueError):
        registry.sampling_eligible(candidate.reservation_id, CUT + timedelta(hours=1))


def test_duplicate_counters_and_full_replay_idempotence():
    first = envelope()
    second = replace(first, receipt_id="receipt-2", received_at=T + timedelta(seconds=1),
                     processed_at=T + timedelta(seconds=1), available_at=T + timedelta(seconds=1))
    a, b = sampler(), sampler()
    for registry in (a, b):
        registry.register(first)
        registry.register(second)
        registry.close(CUT)
        before = registry.counts()
        registry.register(first)
        registry.register(second)
        registry.close(CUT)
        assert registry.counts() == before
    assert a.reservations() == b.reservations()
    assert a.population() == b.population()
    assert a.counts() == s.SamplingCounts(2, 1, 1, 1, 1)
    assert a.candidates()[1].relation is s.Relation.DUPLICATE


@pytest.mark.parametrize("relation", [s.Relation.UPDATE, s.Relation.CORRECTION, s.Relation.SAME_CLUSTER_NEW_REPORT])
def test_explicit_relations_after_cut_preserve_history(relation):
    registry = run()
    before = registry.population()
    event = envelope()
    at = CUT + timedelta(minutes=1)
    follow = replace(event, receipt_id="receipt-2", revision_id="revision-2", content_hash="new-content",
                     document_id="doc-2" if relation is s.Relation.SAME_CLUSTER_NEW_REPORT else event.document_id,
                     received_at=at, processed_at=at, available_at=at,
                     relation=relation, prior_event_id=event.event_id,
                     shock_evidence=s.ShockEvidence.EXPLICIT_RELATION, shock_key=None, shock_namespace=None)
    candidate = registry.register(follow)
    assert candidate.relation is relation
    assert candidate.cluster_id == before[0].event_cluster_id
    registry.close(CUT + timedelta(hours=1))
    assert registry.population() == before
    assert len(registry.reservations()) == 1


def test_same_shock_new_report_and_new_announcement():
    registry = sampler()
    first = registry.register(envelope())
    report = registry.register(envelope(document_id="doc-2", receipt_id="receipt-2"))
    assert report.relation is s.Relation.SAME_CLUSTER_NEW_REPORT
    assert report.reservation_id == first.reservation_id
    registry.register(envelope(document_id="doc-3", receipt_id="receipt-3", shock_key="announcement-2"))
    registry.close(CUT)
    assert registry.counts() == s.SamplingCounts(3, 3, 2, 2, 2)


def test_unknown_followup_and_pre_cut_correction():
    e = envelope()
    registry = sampler()
    registry.register(e)
    correction = replace(e, revision_id="revision-2", receipt_id="receipt-2", content_hash="corrected",
                         relation=s.Relation.CORRECTION, prior_event_id=e.event_id,
                         shock_evidence=s.ShockEvidence.EXPLICIT_RELATION)
    registry.register(correction)
    assert registry.close(CUT)[0].reasons == ("CORRECTION_AT_CUTOFF",)
    other = run(replace(correction, prior_event_id="unknown"))
    assert not other.population()


@pytest.mark.parametrize("changes", [{"processed_at": None}, {"normalization_version": "unverified-version"}])
def test_unavailable_correction_cannot_change_admission(changes):
    registry = sampler()
    original = envelope()
    registry.register(original)
    registry.register(replace(original, revision_id="correction", receipt_id="correction-receipt",
                              content_hash="correction-content", relation=s.Relation.CORRECTION,
                              prior_event_id=original.event_id,
                              shock_evidence=s.ShockEvidence.EXPLICIT_RELATION, **changes))
    assert registry.close(CUT)[0].admitted


def test_role_crossing_and_first_receipt_ownership():
    registry = sampler()
    original = registry.register(envelope())
    for e in (envelope(receipt_id="receipt-2"), envelope(document_id="doc-2", receipt_id="receipt-2")):
        with pytest.raises(ConflictError):
            registry.register(e, role=DatasetRole.CONFIRMATION)
    assert registry.reservations()[0].event_id == original.envelope.event_id
    registry.close(CUT)
    with pytest.raises(ConflictError):
        registry.register(envelope(receipt_id="backdated", document_id="backdated"))


def test_shock_reservation_blocks_distinct_content_and_role_before_materialization():
    registry = sampler()
    original = registry.register(envelope())
    reserved = registry.reservations()
    report = envelope(document_id="other-document", receipt_id="other-receipt", content_hash="other-content")
    with pytest.raises(ConflictError, match="cross-role shock reuse"):
        registry.register(report, role=DatasetRole.CONFIRMATION)
    same_role = registry.register(report)
    assert same_role.envelope.event_id != original.envelope.event_id
    assert same_role.reservation_id == original.reservation_id
    assert registry.reservations() == reserved
    assert not registry.population()
    registry.close(CUT)
    assert len(registry.population()) == 1


def test_first_accredited_receipt_wins_not_unverifiable_observation():
    registry = sampler()
    registry.register(envelope(receipt_id="unverified", receipt_verified=False))
    first = registry.register(envelope(received_at=T + timedelta(seconds=1),
                                       processed_at=T + timedelta(seconds=1), available_at=T + timedelta(seconds=1)))
    registry.close(CUT)
    assert registry.population()[0].inputs[0].receipt_ids == (first.envelope.receipt_id,)
    assert registry.counts() == s.SamplingCounts(2, 1, 1, 1, 1)


def test_cross_role_content_cannot_be_renamed_into_new_shock():
    registry = sampler()
    registry.register(envelope())
    with pytest.raises(ConflictError):
        registry.register(envelope(document_id="renamed", receipt_id="new-receipt", shock_key="renamed-shock"),
                          role=DatasetRole.CONFIRMATION)


def test_fixed_universe_and_missing_inputs_preserve_population():
    registry = run(envelope(assets=("BTC", "ETH")))
    opportunity = registry.population()[0]
    assert (opportunity.instrument, opportunity.venue, opportunity.product) == ("BTCUSDT", "Binance USDⓈ-M", "linear perpetual")
    assert opportunity.decision_slot_id.startswith("H1:")
    assert {i.input_type for i in opportunity.inputs if i.status is InputStatus.MISSING} == {
        InputType.PRICE, InputType.REGIME, InputType.MECHANICS}
    assert registry.counts().N_opportunities == 1


@pytest.mark.parametrize("field", ["venue", "product", "operational_event_id", "sentiment", "title",
                                   "category", "future_price", "performance", "outcome", "pnl"])
def test_sampler_cannot_use_uncontracted_information(field):
    with pytest.raises(TypeError):
        envelope(**{field: "forbidden"})


def test_structural_counts_and_import_boundary():
    assert {f.name for f in fields(s.SamplingCounts)} == {
        "N_raw_events", "N_unique_events", "N_sampling_eligible_events", "N_event_clusters", "N_opportunities"}
    tree = ast.parse(Path(s.__file__).read_text(encoding="utf-8"))
    allowed = {"dataclasses", "datetime", "enum", "nuisance_pilot_contracts", "nuisance_pilot_store"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module in allowed
        assert not isinstance(node, ast.Import)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "eval", "exec", "__import__"}


def test_existing_manifest_half_open_semantics():
    a = ManifestEntry("op-a", "event-a", "cluster-a", "econ-a", "hash-a", "BTC", CUT, CUT + timedelta(hours=1))
    b = ManifestEntry("op-b", "event-b", "cluster-b", "econ-b", "hash-b", "BTC", a.outcome_end, a.outcome_end + timedelta(hours=1))
    assert validate_isolation((DatasetManifest(DatasetRole.PILOT, (a,)), DatasetManifest(DatasetRole.CONFIRMATION, (b,))))
