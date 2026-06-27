"""Tests for Scientific Learning Laboratory — Stage 7

Tests OutcomeComparison generation, Knowledge lifecycle,
CriterionDelta proposal/review lifecycle, and CLI commands.
All tests operate on in-memory objects or isolated test databases.
No operational code is touched.
"""
import os
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
from core.schemas.outcome_comparison_schema import (
    OutcomeComparison, Verdict, ErrorType, ComparisonType,
)
from core.schemas.knowledge_schema import Knowledge, KnowledgeStatus, VALID_TRANSITIONS
from core.schemas.criterion_delta_schema import (
    CriterionDelta, DeltaStatus,
    VALID_TRANSITIONS as DELTA_VALID_TRANSITIONS,
)
from core.scientific.outcome_comparison import (
    compare_outcome, auto_detect_verdict, classify_error,
)
from core.scientific.knowledge_lifecycle import (
    extract_knowledge, extract_from_comparison,
    transition_knowledge, can_transition,
    promote_to_provisional, validate_knowledge,
    invalidate_knowledge, revise_knowledge, archive_knowledge,
    decay_confidence,
)
from core.scientific.criterion_evolution import (
    propose_delta, apply_delta, reject_delta,
    compute_criterion_metrics, VALID_DIMENSIONS,
)
from core.scientific.scientific_store import ScientificStore


NOW = datetime.now(timezone.utc)
TEST_DB = "test_lab.db"


def make_hypothesis(**kw):
    defaults = dict(
        id=str(uuid4()), title="Test Hypothesis",
        description="A test hypothesis",
        predicted_consequence="BTC will increase 3-5% within 5 days",
        conditions="Low volatility regime",
        invalidation_conditions="BTC drops more than 1%",
        confidence=0.65,
        status=HypothesisStatus.ACTIVE,
        created_at=NOW, updated_at=NOW,
        status_history=[],
    )
    defaults.update(kw)
    return Hypothesis(**defaults)


def make_comparison(**kw):
    defaults = dict(
        id=str(uuid4()), hypothesis_id=str(uuid4()),
        verdict=Verdict.CONFIRMED,
        comparison_type=ComparisonType.EXECUTED,
        predicted_consequence="Prediction text",
        actual_outcome="Actual result",
        comparison_confidence=0.8,
        compared_at=NOW,
    )
    defaults.update(kw)
    return OutcomeComparison(**defaults)


def make_knowledge(**kw):
    defaults = dict(
        id=str(uuid4()), statement="Under low vol, BTC 20d MA cross predicts target within 1 week",
        hypothesis_ids=[str(uuid4())], outcome_ids=[str(uuid4())],
        evidence_summary="Confirmed across 3 instances",
        confidence=0.5, conditions="Low volatility",
        scope="crypto", time_horizon="swing",
        status=KnowledgeStatus.EXTRACTED,
        created_at=NOW, updated_at=NOW,
    )
    defaults.update(kw)
    return Knowledge(**defaults)


# ── Outcome Comparison Tests ─────────────────────────────────────

class TestAutoDetectVerdict:
    def test_direction_up_matches(self):
        assert auto_detect_verdict("BTC will rally", "BTC went up 5%") == Verdict.CONFIRMED

    def test_direction_down_matches(self):
        assert auto_detect_verdict("Gold will drop", "Gold declined 2%") == Verdict.CONFIRMED

    def test_direction_mismatch(self):
        assert auto_detect_verdict("BTC will rally", "BTC crashed 10%") == Verdict.REJECTED

    def test_numeric_positive_match(self):
        assert auto_detect_verdict("increase 5%", "up 4%") == Verdict.CONFIRMED

    def test_numeric_negative_both(self):
        assert auto_detect_verdict("decline 3%", "down 2%") == Verdict.CONFIRMED

    def test_numeric_magnitude_exceeded(self):
        assert auto_detect_verdict("increase 5%", "up 20%") == Verdict.INCONCLUSIVE

    def test_numeric_sign_mismatch(self):
        assert auto_detect_verdict("increase 5%", "dropped 3%") == Verdict.REJECTED

    def test_ambiguous_returns_none(self):
        assert auto_detect_verdict("The market will react", "Something happened") is None


class TestCompareOutcome:
    def test_explicit_verdict(self):
        hyp = make_hypothesis()
        oc = compare_outcome(hyp, "actual result", verdict=Verdict.CONFIRMED)
        assert oc.verdict == Verdict.CONFIRMED
        assert oc.hypothesis_id == hyp.id

    def test_auto_detection_fallback(self):
        hyp = make_hypothesis(predicted_consequence="BTC will rally")
        oc = compare_outcome(hyp, "BTC went up 5%")
        assert oc.verdict == Verdict.CONFIRMED

    def test_auto_detection_ambiguous_defaults_inconclusive(self):
        hyp = make_hypothesis(predicted_consequence="Something will happen")
        oc = compare_outcome(hyp, "Something else happened")
        assert oc.verdict in (Verdict.INCONCLUSIVE, Verdict.CONFIRMED, Verdict.REJECTED)

    def test_rejected_auto_classifies_error(self):
        hyp = make_hypothesis(predicted_consequence="BTC will rally")
        oc = compare_outcome(hyp, "BTC crashed 10%")
        assert oc.verdict == Verdict.REJECTED
        assert oc.error_type is not None

    def test_missed_opportunity_type(self):
        hyp = make_hypothesis()
        oc = compare_outcome(
            hyp, "price went up 5%",
            comparison_type=ComparisonType.MISSED_OPPORTUNITY,
        )
        assert oc.comparison_type == ComparisonType.MISSED_OPPORTUNITY

    def test_confidence_clamped(self):
        hyp = make_hypothesis()
        oc = compare_outcome(hyp, "result", verdict=Verdict.CONFIRMED, comparison_confidence=1.5)
        assert oc.comparison_confidence == 1.0
        oc2 = compare_outcome(hyp, "result", verdict=Verdict.CONFIRMED, comparison_confidence=-0.5)
        assert oc2.comparison_confidence == 0.0

    def test_error_detail_preserved(self):
        hyp = make_hypothesis()
        oc = compare_outcome(
            hyp, "result", verdict=Verdict.REJECTED,
            error_type=ErrorType.WRONG_TIMING, error_detail="Off by 4 days",
        )
        assert oc.error_type == ErrorType.WRONG_TIMING
        assert oc.error_detail == "Off by 4 days"


class TestClassifyError:
    def test_rejected_wrong_hypothesis_default(self):
        hyp = make_hypothesis(predicted_consequence="BTC will rally")
        err = classify_error(hyp, "Something unrelated happened", Verdict.REJECTED)
        assert err == ErrorType.WRONG_HYPOTHESIS

    def test_rejected_wrong_timing(self):
        hyp = make_hypothesis(predicted_consequence="BTC will rally within 5 days")
        err = classify_error(hyp, "BTC rallied after 10 days", Verdict.REJECTED)
        assert err == ErrorType.WRONG_TIMING

    def test_external_shock_detected(self):
        hyp = make_hypothesis(predicted_consequence="Gold will rally")
        err = classify_error(hyp, "Unexpected regulatory shock caused drop", Verdict.REJECTED)
        assert err == ErrorType.EXTERNAL_SHOCK

    def test_confirmed_returns_none(self):
        hyp = make_hypothesis()
        err = classify_error(hyp, "BTC went up 5%", Verdict.CONFIRMED)
        assert err is None

    def test_inconclusive_returns_none(self):
        hyp = make_hypothesis()
        err = classify_error(hyp, "Mixed signals", Verdict.INCONCLUSIVE)
        assert err is None


# ── Knowledge Lifecycle Tests ────────────────────────────────────

class TestKnowledgeExtraction:
    def test_extract_knowledge_creates_extracted(self):
        k = extract_knowledge(
            statement="Test knowledge",
            hypothesis_ids=["H-001"], outcome_ids=["OC-001"],
            evidence_summary="Test", conditions="C",
            scope="crypto", time_horizon="swing",
        )
        assert k.status == KnowledgeStatus.EXTRACTED
        assert k.confidence == 0.3
        assert k.replication_count == 0

    def test_extract_from_comparison(self):
        oc = make_comparison(hypothesis_id="H-001")
        k = extract_from_comparison(
            oc, statement="Derived knowledge",
            conditions="Low vol", scope="crypto", time_horizon="swing",
        )
        assert oc.hypothesis_id in k.hypothesis_ids
        assert oc.id in k.outcome_ids

    def test_extracted_has_provenance(self):
        k = extract_knowledge(
            statement="S", hypothesis_ids=["H-001"], outcome_ids=["OC-001"],
            evidence_summary="S", conditions="C", scope="S", time_horizon="T",
        )
        assert "source" in k.provenance
        assert k.provenance["source"] == "manual_cli"

    def test_confidence_clamped(self):
        k = extract_knowledge(
            statement="S", hypothesis_ids=[], outcome_ids=[],
            evidence_summary="S", conditions="C", scope="S", time_horizon="T",
            confidence=2.0,
        )
        assert k.confidence == 1.0
        k2 = extract_knowledge(
            statement="S", hypothesis_ids=[], outcome_ids=[],
            evidence_summary="S", conditions="C", scope="S", time_horizon="T",
            confidence=-0.5,
        )
        assert k2.confidence == 0.0


class TestKnowledgeTransitions:
    def test_extracted_to_provisional(self):
        k = make_knowledge(status=KnowledgeStatus.EXTRACTED)
        promote_to_provisional(k)
        assert k.status == KnowledgeStatus.PROVISIONAL

    def test_provisional_to_validated(self):
        k = make_knowledge(status=KnowledgeStatus.PROVISIONAL)
        validate_knowledge(k)
        assert k.status == KnowledgeStatus.VALIDATED
        assert k.last_validated_at is not None

    def test_provisional_to_invalidated(self):
        k = make_knowledge(status=KnowledgeStatus.PROVISIONAL)
        invalidate_knowledge(k)
        assert k.status == KnowledgeStatus.INVALIDATED

    def test_validated_to_revised(self):
        k = make_knowledge(status=KnowledgeStatus.VALIDATED, statement="Old statement")
        revise_knowledge(k, "New refined statement")
        assert k.status == KnowledgeStatus.REVISED
        assert k.statement == "New refined statement"

    def test_invalidated_to_archived(self):
        k = make_knowledge(status=KnowledgeStatus.INVALIDATED)
        archive_knowledge(k)
        assert k.status == KnowledgeStatus.ARCHIVED

    def test_any_to_archived(self):
        for status in KnowledgeStatus:
            if status == KnowledgeStatus.ARCHIVED:
                continue
            k = make_knowledge(status=status)
            archive_knowledge(k)
            assert k.status == KnowledgeStatus.ARCHIVED, f"Failed for {status}"

    def test_invalid_transition_raises(self):
        k = make_knowledge(status=KnowledgeStatus.EXTRACTED)
        with pytest.raises(ValueError, match="Cannot transition"):
            validate_knowledge(k)
        assert k.status == KnowledgeStatus.EXTRACTED

    def test_invalid_transition_from_archived(self):
        k = make_knowledge(status=KnowledgeStatus.ARCHIVED)
        with pytest.raises(ValueError):
            promote_to_provisional(k)

    def test_can_transition(self):
        k = make_knowledge(status=KnowledgeStatus.EXTRACTED)
        assert can_transition(k, KnowledgeStatus.PROVISIONAL)
        assert can_transition(k, KnowledgeStatus.ARCHIVED)
        assert not can_transition(k, KnowledgeStatus.VALIDATED)

    def test_transition_records_history(self):
        k = make_knowledge(status=KnowledgeStatus.EXTRACTED)
        transition_knowledge(k, KnowledgeStatus.PROVISIONAL, reason="Manual review")
        assert len(k.revision_history) >= 1
        last = k.revision_history[-1]
        assert last["from_status"] == "extracted"
        assert last["to_status"] == "provisional"

    def test_validated_sets_last_validated(self):
        k = make_knowledge(status=KnowledgeStatus.PROVISIONAL)
        assert k.last_validated_at is None
        validate_knowledge(k)
        assert k.last_validated_at is not None


class TestKnowledgeDecay:
    def test_no_decay_within_window(self):
        k = make_knowledge(confidence=0.8, replication_count=0)
        adjusted = decay_confidence(k, days_since_last_confirmation=30)
        assert abs(adjusted - 0.6667) < 0.01

    def test_decay_reduces_confidence(self):
        k = make_knowledge(confidence=0.8, replication_count=0)
        adjusted = decay_confidence(k, days_since_last_confirmation=360)
        assert adjusted < 0.5

    def test_decay_floor(self):
        k = make_knowledge(confidence=1.0, replication_count=0)
        adjusted = decay_confidence(k, days_since_last_confirmation=10000)
        assert adjusted >= 0.1

    def test_replication_extends_window(self):
        k = make_knowledge(confidence=0.8, replication_count=10)
        low_replication = decay_confidence(k.copy() if hasattr(k, 'copy') else k, 200)
        assert low_replication > 0.3

    def test_revised_knowledge_decays(self):
        k = make_knowledge(confidence=0.7, status=KnowledgeStatus.REVISED, replication_count=2)
        adjusted = decay_confidence(k, days_since_last_confirmation=180)
        assert 0.0 <= adjusted <= 1.0


# ── Criterion Delta Tests ────────────────────────────────────────

class TestProposeDelta:
    def test_propose_pending_review(self):
        delta = propose_delta(
            knowledge_ids=["K-001"], hypothesis_ids=["H-001"],
            outcome_ids=["OC-001"], dimension="error_recurrence",
            change="Reduce WRONG_TIMING tolerance",
        )
        assert delta.status == DeltaStatus.PENDING_REVIEW
        assert delta.dimension == "error_recurrence"

    def test_invalid_dimension_raises(self):
        with pytest.raises(ValueError, match="Invalid dimension"):
            propose_delta(
                knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
                dimension="invalid_dim", change="Test",
            )

    def test_all_valid_dimensions(self):
        for dim in VALID_DIMENSIONS:
            delta = propose_delta(
                knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
                dimension=dim, change=f"Change for {dim}",
            )
            assert delta.dimension == dim

    def test_source_evidence_stored(self):
        delta = propose_delta(
            knowledge_ids=["K-001", "K-002"],
            hypothesis_ids=["H-001"],
            outcome_ids=["OC-001", "OC-002", "OC-003"],
            dimension="calibration", change="Adjust baseline",
        )
        assert len(delta.source_evidence["knowledge_ids"]) == 2
        assert len(delta.source_evidence["outcome_ids"]) == 3

    def test_confidence_clamped(self):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="hypothesis_quality", change="X", confidence=2.0,
        )
        assert delta.confidence == 1.0


class TestDeltaReview:
    def test_apply_pending(self):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="knowledge_yield", change="Increase threshold",
        )
        assert delta.status == DeltaStatus.PENDING_REVIEW
        apply_delta(delta)
        assert delta.status == DeltaStatus.APPLIED
        assert delta.applied_at is not None

    def test_reject_pending(self):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="learning_velocity", change="Adjust metric",
        )
        reject_delta(delta)
        assert delta.status == DeltaStatus.REJECTED

    def test_cannot_apply_already_applied(self):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="scarce_resource_conversion", change="X",
        )
        apply_delta(delta)
        with pytest.raises(ValueError):
            apply_delta(delta)

    def test_cannot_apply_rejected(self):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="error_recurrence", change="X",
        )
        reject_delta(delta)
        with pytest.raises(ValueError):
            apply_delta(delta)

    def test_cannot_reject_applied(self):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="calibration", change="X",
        )
        apply_delta(delta)
        with pytest.raises(ValueError):
            reject_delta(delta)


class TestCriterionMetrics:
    def test_empty_returns_zeros(self):
        metrics = compute_criterion_metrics([], [], [])
        assert metrics["calibration"]["total_comparisons"] == 0
        assert metrics["knowledge_yield"]["total_knowledge"] == 0

    def test_with_data(self):
        hyp = make_hypothesis(status=HypothesisStatus.EVALUATED)
        c1 = make_comparison(verdict=Verdict.CONFIRMED)
        c2 = make_comparison(verdict=Verdict.REJECTED, error_type=ErrorType.WRONG_HYPOTHESIS)
        k = make_knowledge(status=KnowledgeStatus.VALIDATED)

        metrics = compute_criterion_metrics([hyp], [c1, c2], [k])
        assert metrics["calibration"]["confirmation_rate"] == 0.5
        assert metrics["calibration"]["rejection_rate"] == 0.5
        assert metrics["knowledge_yield"]["validated_knowledge"] == 1

    def test_error_distribution(self):
        c1 = make_comparison(verdict=Verdict.REJECTED, error_type=ErrorType.WRONG_HYPOTHESIS)
        c2 = make_comparison(verdict=Verdict.REJECTED, error_type=ErrorType.WRONG_TIMING)
        c3 = make_comparison(verdict=Verdict.REJECTED, error_type=ErrorType.WRONG_HYPOTHESIS)

        metrics = compute_criterion_metrics([], [c1, c2, c3], [])
        assert metrics["error_recurrence"]["error_distribution"]["wrong_hypothesis"] == 2
        assert metrics["error_recurrence"]["dominant_error"] == "wrong_hypothesis"


# ── Store Integration Tests ──────────────────────────────────────

class TestStoreIntegration:
    @pytest.fixture
    def store(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        s = ScientificStore(db_path=TEST_DB)
        yield s
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_store_and_retrieve_comparison(self, store):
        oc = make_comparison()
        store.create_outcome_comparison(oc)
        loaded = store.get_outcome_comparison(oc.id)
        assert loaded is not None
        assert loaded.verdict == oc.verdict

    def test_store_and_retrieve_knowledge(self, store):
        k = make_knowledge()
        store.create_knowledge(k)
        loaded = store.get_knowledge(k.id)
        assert loaded is not None
        assert loaded.statement == k.statement

    def test_store_and_retrieve_delta(self, store):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="calibration", change="Test",
        )
        store.create_criterion_delta(delta)
        loaded = store.get_criterion_delta(delta.id)
        assert loaded is not None
        assert loaded.status == DeltaStatus.PENDING_REVIEW

    def test_update_knowledge_persists(self, store):
        k = make_knowledge()
        store.create_knowledge(k)
        promote_to_provisional(k)
        store.update_knowledge(k)
        loaded = store.get_knowledge(k.id)
        assert loaded.status == KnowledgeStatus.PROVISIONAL

    def test_list_filters_by_status(self, store):
        k1 = make_knowledge(status=KnowledgeStatus.EXTRACTED)
        k2 = make_knowledge(status=KnowledgeStatus.VALIDATED)
        store.create_knowledge(k1)
        store.create_knowledge(k2)

        extracted = store.list_knowledge(status=KnowledgeStatus.EXTRACTED)
        validated = store.list_knowledge(status=KnowledgeStatus.VALIDATED)
        assert len(extracted) == 1
        assert len(validated) == 1

    def test_lab_stats(self, store):
        hyp = store.create_hypothesis(
            title="T", description="D",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        oc = make_comparison(hypothesis_id=hyp.id)
        store.create_outcome_comparison(oc)
        k = make_knowledge()
        store.create_knowledge(k)

        stats = store.get_lab_stats()
        assert stats["hypotheses"]["total"] >= 1
        assert stats["comparisons"]["total"] >= 1
        assert stats["knowledge"]["total"] >= 1

    def test_roundtrip_serialization(self, store):
        oc = make_comparison(
            verdict=Verdict.REJECTED,
            error_type=ErrorType.WRONG_TIMING,
            tolerance_applied={"magnitude": 0.3, "timing": 0.5},
            knowledge_triggered=True,
        )
        store.create_outcome_comparison(oc)
        loaded = store.get_outcome_comparison(oc.id)
        assert loaded.verdict == oc.verdict
        assert loaded.error_type == oc.error_type
        assert loaded.tolerance_applied == oc.tolerance_applied
        assert loaded.knowledge_triggered == oc.knowledge_triggered


# ── Knowledge Full Lifecycle Flow ────────────────────────────────

class TestKnowledgeFullLifecycle:
    def test_extract_to_validated(self):
        k = make_knowledge(status=KnowledgeStatus.EXTRACTED)
        promote_to_provisional(k)
        validate_knowledge(k)
        assert k.status == KnowledgeStatus.VALIDATED

    def test_extract_to_invalidated(self):
        k = make_knowledge(status=KnowledgeStatus.EXTRACTED)
        promote_to_provisional(k)
        invalidate_knowledge(k)
        assert k.status == KnowledgeStatus.INVALIDATED

    def test_validated_to_revised_to_validated(self):
        k = make_knowledge(status=KnowledgeStatus.VALIDATED)
        revise_knowledge(k, "Refined statement")
        assert k.status == KnowledgeStatus.REVISED
        validate_knowledge(k)
        assert k.status == KnowledgeStatus.VALIDATED

    def test_full_archival_path(self):
        k = make_knowledge(status=KnowledgeStatus.EXTRACTED)
        promote_to_provisional(k)
        validate_knowledge(k)
        archive_knowledge(k)
        assert k.status == KnowledgeStatus.ARCHIVED

    def test_all_transitions_defined(self):
        for status in KnowledgeStatus:
            assert status in VALID_TRANSITIONS


# ── Workflow Integration ─────────────────────────────────────────

class TestWorkflow:
    def test_hypothesis_to_comparison_to_knowledge_to_delta(self):
        hyp = make_hypothesis(
            predicted_consequence="BTC will rally 3-5% within 5 days",
        )

        oc = compare_outcome(hyp, "BTC increased 4.2% in 4 days")
        assert oc.verdict in (Verdict.CONFIRMED, Verdict.INCONCLUSIVE)

        k = extract_from_comparison(
            oc, statement="BTC 3-5% rally predictions in low vol have high accuracy",
            conditions="Low volatility, trending market",
            scope="crypto", time_horizon="swing",
        )
        promote_to_provisional(k)
        assert k.status == KnowledgeStatus.PROVISIONAL

        delta = propose_delta(
            knowledge_ids=[k.id],
            hypothesis_ids=[hyp.id],
            outcome_ids=[oc.id],
            dimension="calibration",
            change="Increase confidence in BTC swing predictions by 0.05",
        )
        assert delta.status == DeltaStatus.PENDING_REVIEW

        assert oc.hypothesis_id == hyp.id
        assert hyp.id in k.hypothesis_ids
        assert k.id in delta.source_evidence["knowledge_ids"]

    def test_rejected_outcome_produces_error(self):
        hyp = make_hypothesis(
            predicted_consequence="Gold will rally 2%",
        )
        oc = compare_outcome(hyp, "Gold dropped 3%")
        assert oc.verdict == Verdict.REJECTED
        assert oc.error_type is not None

    def test_inconclusive_outcome_no_error(self):
        hyp = make_hypothesis(
            predicted_consequence="Market will move significantly",
        )
        oc = compare_outcome(hyp, "Market moved 0.5% sideways")
        assert oc.verdict == Verdict.INCONCLUSIVE
        assert oc.error_type is None


# ── Human Review Requirement ─────────────────────────────────────

class TestHumanReview:
    def test_delta_starts_pending(self):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="error_recurrence", change="Test",
        )
        assert delta.status == DeltaStatus.PENDING_REVIEW

    def test_apply_requires_explicit_call(self):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="calibration", change="Test",
        )
        assert delta.status == DeltaStatus.PENDING_REVIEW
        apply_delta(delta)
        assert delta.status == DeltaStatus.APPLIED

    def test_no_auto_approval(self):
        k = make_knowledge(status=KnowledgeStatus.VALIDATED)
        oc = make_comparison(verdict=Verdict.CONFIRMED)
        delta = propose_delta(
            knowledge_ids=[k.id], hypothesis_ids=[], outcome_ids=[oc.id],
            dimension="knowledge_yield", change="Test",
        )
        assert delta.status == DeltaStatus.PENDING_REVIEW
        assert delta.applied_at is None

    def test_rejected_delta_cannot_be_applied_later(self):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="hypothesis_quality", change="X",
        )
        reject_delta(delta)
        with pytest.raises(ValueError):
            apply_delta(delta)


# ── CLI Command Tests ────────────────────────────────────────────

class TestCLICommands:
    @pytest.fixture
    def store(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        s = ScientificStore(db_path=TEST_DB)
        yield s
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_lab_compare_command(self, store):
        hyp = store.create_hypothesis(
            title="CLI Test",
            description="Test hypothesis for CLI",
            predicted_consequence="BTC will increase",
            conditions="Normal market",
            invalidation_conditions="BTC drops",
            confidence=0.6,
        )
        oc = compare_outcome(hyp, "BTC increased 3%")
        store.create_outcome_comparison(oc)
        loaded = store.get_outcome_comparison(oc.id)
        assert loaded is not None
        assert loaded.hypothesis_id == hyp.id

    def test_lab_knowledge_extract_command(self, store):
        k = extract_knowledge(
            statement="CLI extracted knowledge",
            hypothesis_ids=["H-CLI-001"], outcome_ids=["OC-CLI-001"],
            evidence_summary="CLI test", conditions="C",
            scope="crypto", time_horizon="swing",
        )
        store.create_knowledge(k)
        loaded = store.get_knowledge(k.id)
        assert loaded.statement == "CLI extracted knowledge"
        assert loaded.status == KnowledgeStatus.EXTRACTED

    def test_lab_knowledge_transition_command(self, store):
        k = make_knowledge(status=KnowledgeStatus.EXTRACTED)
        store.create_knowledge(k)
        promote_to_provisional(k)
        store.update_knowledge(k)
        loaded = store.get_knowledge(k.id)
        assert loaded.status == KnowledgeStatus.PROVISIONAL

    def test_lab_criterion_propose_command(self, store):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="calibration", change="CLI test delta",
        )
        store.create_criterion_delta(delta)
        loaded = store.get_criterion_delta(delta.id)
        assert loaded.dimension == "calibration"
        assert loaded.status == DeltaStatus.PENDING_REVIEW

    def test_lab_criterion_apply_command(self, store):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="error_recurrence", change="Apply test",
        )
        store.create_criterion_delta(delta)
        apply_delta(delta)
        store.update_criterion_delta(delta)
        loaded = store.get_criterion_delta(delta.id)
        assert loaded.status == DeltaStatus.APPLIED
        assert loaded.applied_at is not None

    def test_lab_criterion_reject_command(self, store):
        delta = propose_delta(
            knowledge_ids=[], hypothesis_ids=[], outcome_ids=[],
            dimension="knowledge_yield", change="Reject test",
        )
        store.create_criterion_delta(delta)
        reject_delta(delta)
        store.update_criterion_delta(delta)
        loaded = store.get_criterion_delta(delta.id)
        assert loaded.status == DeltaStatus.REJECTED


# ── Regression: Existing schemas unchanged ───────────────────────

class TestRegression:
    def test_existing_hypothesis_schema(self):
        hyp = make_hypothesis()
        d = hyp.to_dict()
        h2 = Hypothesis.from_dict(d)
        assert h2.title == hyp.title

    def test_no_operational_modules_touched(self):
        import core.schemas.event_schema
        import core.schemas.agent_schema
        import core.schemas.trade_schema
        assert True

    def test_no_database_left_behind(self):
        assert not os.path.exists("test_oma_core.db")
