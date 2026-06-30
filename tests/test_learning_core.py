"""Tests for Learning Core Stage 5 — Minimal Schemas

Tests OutcomeComparison, Knowledge, CriterionDelta schemas,
their lifecycle definitions, serialization, and exports.
Schema-level tests only — no database, no lifecycle functions.
"""
import pytest
from datetime import datetime, timezone, timedelta
from dataclasses import fields
from core.schemas.outcome_comparison_schema import (
    OutcomeComparison, Verdict, ErrorType, ComparisonType,
    OUTCOME_COMPARISON_TABLE_SCHEMA,
)
from core.schemas.knowledge_schema import (
    Knowledge, KnowledgeStatus, VALID_TRANSITIONS,
    KNOWLEDGE_TABLE_SCHEMA,
)
from core.schemas.criterion_delta_schema import (
    CriterionDelta, DeltaStatus, VALID_TRANSITIONS as DELTA_VALID_TRANSITIONS,
    CRITERION_DELTA_TABLE_SCHEMA,
)
from core.schemas import (
    OutcomeComparison, Verdict, ErrorType, ComparisonType,
    OUTCOME_COMPARISON_TABLE_SCHEMA,
    Knowledge, KnowledgeStatus, KNOWLEDGE_TABLE_SCHEMA,
    CriterionDelta, DeltaStatus, CRITERION_DELTA_TABLE_SCHEMA,
)
from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
from core.schemas.evidence_schema import Evidence, EvidenceDirection, EvidenceStatus


NOW = datetime.now(timezone.utc)


# ─────────────────────────────────────────────
# OutcomeComparison Tests
# ─────────────────────────────────────────────

class TestOutcomeComparisonCreation:
    def test_create_minimal(self):
        oc = OutcomeComparison(
            id="OC-001",
            hypothesis_id="H-001",
            verdict=Verdict.CONFIRMED,
            comparison_type=ComparisonType.EXECUTED,
            predicted_consequence="BTC up 2-5% in 5 days",
            actual_outcome="BTC up 3.2% in 4 days",
            comparison_confidence=0.92,
            compared_at=NOW,
        )
        assert oc.id == "OC-001"
        assert oc.verdict == Verdict.CONFIRMED

    def test_create_with_all_fields(self):
        oc = OutcomeComparison(
            id="OC-002",
            hypothesis_id="H-002",
            decision_id="D-001",
            outcome_id="O-001",
            verdict=Verdict.REJECTED,
            error_type=ErrorType.WRONG_HYPOTHESIS,
            comparison_type=ComparisonType.MISSED_OPPORTUNITY,
            predicted_consequence="Gold up 3%",
            actual_outcome="Gold down 1%",
            tolerance_applied={"magnitude": 0.3, "timing": 0.5},
            comparison_confidence=0.75,
            error_detail="Direction was completely wrong",
            knowledge_triggered=True,
            compared_at=NOW,
        )
        assert oc.decision_id == "D-001"
        assert oc.error_type == ErrorType.WRONG_HYPOTHESIS
        assert oc.knowledge_triggered is True

    def test_default_field_values(self):
        oc = OutcomeComparison(
            id="OC-003",
            hypothesis_id="H-003",
            verdict=Verdict.INCONCLUSIVE,
            comparison_type=ComparisonType.EXECUTED,
            predicted_consequence="X",
            actual_outcome="Y",
            comparison_confidence=0.5,
            compared_at=NOW,
        )
        assert oc.decision_id is None
        assert oc.outcome_id is None
        assert oc.error_type is None
        assert oc.error_detail is None
        assert oc.tolerance_applied is None
        assert oc.knowledge_triggered is False

    def test_confidence_range(self):
        for conf in [0.0, 0.3, 0.5, 0.7, 1.0]:
            oc = OutcomeComparison(
                id=f"OC-{conf}", hypothesis_id="H-001",
                verdict=Verdict.CONFIRMED, comparison_type=ComparisonType.EXECUTED,
                predicted_consequence="X", actual_outcome="X",
                comparison_confidence=conf, compared_at=NOW,
            )
            assert 0.0 <= oc.comparison_confidence <= 1.0


class TestOutcomeComparisonEnums:
    def test_all_verdict_values(self):
        assert Verdict.CONFIRMED.value == "confirmed"
        assert Verdict.REJECTED.value == "rejected"
        assert Verdict.INCONCLUSIVE.value == "inconclusive"
        assert Verdict.CORRECT_BLOCK.value == "correct_block"
        assert Verdict.INCORRECT_BLOCK.value == "incorrect_block"
        assert Verdict.UNKNOWN.value == "unknown"
        assert len(Verdict) == 7  # confirmed, partially_confirmed, rejected, inconclusive, correct_block, incorrect_block, unknown

    def test_all_error_types(self):
        assert ErrorType.WRONG_HYPOTHESIS.value == "wrong_hypothesis"
        assert ErrorType.WRONG_TIMING.value == "wrong_timing"
        assert ErrorType.POOR_EXECUTION.value == "poor_execution"
        assert ErrorType.INSUFFICIENT_EVIDENCE.value == "insufficient_evidence"
        assert ErrorType.EXTERNAL_SHOCK.value == "external_shock"
        assert ErrorType.CORRECT_DECISION_BAD_OUTCOME.value == "correct_decision_bad_outcome"
        assert ErrorType.BAD_DECISION_GOOD_OUTCOME.value == "bad_decision_good_outcome"
        assert len(ErrorType) == 7

    def test_all_comparison_types(self):
        assert ComparisonType.EXECUTED.value == "executed"
        assert ComparisonType.MISSED_OPPORTUNITY.value == "missed_opportunity"
        assert len(ComparisonType) == 2


class TestOutcomeComparisonSerialization:
    def test_to_dict(self):
        oc = OutcomeComparison(
            id="OC-010", hypothesis_id="H-010",
            verdict=Verdict.CONFIRMED, comparison_type=ComparisonType.EXECUTED,
            predicted_consequence="Prediction", actual_outcome="Result",
            comparison_confidence=0.85, compared_at=NOW,
        )
        d = oc.to_dict()
        assert d["id"] == "OC-010"
        assert d["verdict"] == "confirmed"
        assert d["comparison_confidence"] == 0.85

    def test_from_dict_roundtrip(self):
        oc = OutcomeComparison(
            id="OC-011", hypothesis_id="H-011",
            decision_id="D-002", outcome_id="O-002",
            verdict=Verdict.REJECTED,
            error_type=ErrorType.WRONG_TIMING,
            comparison_type=ComparisonType.EXECUTED,
            predicted_consequence="Rally in 5d", actual_outcome="Rally in 9d",
            tolerance_applied={"magnitude": 0.3, "timing": 0.5},
            comparison_confidence=0.65,
            error_detail="Timing was off by 4 days",
            knowledge_triggered=True,
            compared_at=NOW,
        )
        d = oc.to_dict()
        oc2 = OutcomeComparison.from_dict(d)
        assert oc2.id == oc.id
        assert oc2.verdict == oc.verdict
        assert oc2.error_type == oc.error_type
        assert oc2.comparison_type == oc.comparison_type
        assert oc2.tolerance_applied == oc.tolerance_applied
        assert oc2.knowledge_triggered == oc.knowledge_triggered

    def test_from_dict_minimal(self):
        d = {
            "id": "OC-012", "hypothesis_id": "H-012",
            "verdict": "inconclusive", "comparison_type": "missed_opportunity",
            "predicted_consequence": "P", "actual_outcome": "A",
            "comparison_confidence": 0.4, "compared_at": NOW.isoformat(),
        }
        oc = OutcomeComparison.from_dict(d)
        assert oc.verdict == Verdict.INCONCLUSIVE
        assert oc.comparison_type == ComparisonType.MISSED_OPPORTUNITY
        assert oc.error_type is None


class TestOutcomeComparisonVerdictValidation:
    def test_executed_verdicts(self):
        for v in [Verdict.CONFIRMED, Verdict.REJECTED, Verdict.INCONCLUSIVE, Verdict.UNKNOWN]:
            oc = OutcomeComparison(
                id=f"OC-V-{v.value}", hypothesis_id="H-001",
                verdict=v, comparison_type=ComparisonType.EXECUTED,
                predicted_consequence="X", actual_outcome="X",
                comparison_confidence=0.5, compared_at=NOW,
            )
            assert oc.verdict == v

    def test_missed_opportunity_verdicts(self):
        for v in [Verdict.CORRECT_BLOCK, Verdict.INCORRECT_BLOCK, Verdict.INCONCLUSIVE, Verdict.UNKNOWN]:
            oc = OutcomeComparison(
                id=f"OC-V-{v.value}", hypothesis_id="H-001",
                verdict=v, comparison_type=ComparisonType.MISSED_OPPORTUNITY,
                predicted_consequence="X", actual_outcome="X",
                comparison_confidence=0.5, compared_at=NOW,
            )
            assert oc.verdict == v


class TestOutcomeComparisonSchemaSQL:
    def test_table_schema_string(self):
        assert isinstance(OUTCOME_COMPARISON_TABLE_SCHEMA, str)
        assert "CREATE TABLE IF NOT EXISTS outcome_comparisons" in OUTCOME_COMPARISON_TABLE_SCHEMA

    def test_table_has_required_columns(self):
        required = ["id", "hypothesis_id", "verdict", "comparison_type",
                     "predicted_consequence", "actual_outcome",
                     "comparison_confidence", "compared_at"]
        for col in required:
            assert col in OUTCOME_COMPARISON_TABLE_SCHEMA, f"Missing column: {col}"

    def test_table_has_indexes(self):
        assert "idx_outcome_comparisons_hypothesis" in OUTCOME_COMPARISON_TABLE_SCHEMA
        assert "idx_outcome_comparisons_verdict" in OUTCOME_COMPARISON_TABLE_SCHEMA
        assert "idx_outcome_comparisons_compared_at" in OUTCOME_COMPARISON_TABLE_SCHEMA
        count = OUTCOME_COMPARISON_TABLE_SCHEMA.count("CREATE INDEX")
        assert count == 3

    def test_foreign_key_references_hypotheses(self):
        assert "FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)" in OUTCOME_COMPARISON_TABLE_SCHEMA


# ─────────────────────────────────────────────
# Knowledge Tests
# ─────────────────────────────────────────────

class TestKnowledgeCreation:
    def test_create_minimal(self):
        k = Knowledge(
            id="K-001",
            statement="Under low vol regimes, BTC 20d MA crossovers predict short-term targets within 1 week",
            hypothesis_ids=["H-001"],
            outcome_ids=["OC-001"],
            evidence_summary="Confirmed across 3 crossovers in low vol",
            confidence=0.65,
            conditions="Low volatility regime, crypto markets",
            scope="crypto",
            time_horizon="swing",
            status=KnowledgeStatus.EXTRACTED,
            created_at=NOW,
            updated_at=NOW,
        )
        assert k.id == "K-001"
        assert k.status == KnowledgeStatus.EXTRACTED

    def test_create_with_all_fields(self):
        k = Knowledge(
            id="K-002",
            statement="If BTC above 20d MA for 3 days, test next resistance within 1 week",
            hypothesis_ids=["H-001", "H-002"],
            outcome_ids=["OC-001", "OC-002"],
            missed_opportunity_ids=["MO-001"],
            evidence_summary="Strong pattern across 5 instances",
            confidence=0.72,
            conditions="Low volatility, trending",
            scope="crypto",
            time_horizon="swing (3-10d)",
            replication_count=5,
            replication_conditions=[{"asset": "BTC", "regime": "low_vol"}],
            contrary_evidence_count=1,
            last_validated_at=NOW - timedelta(days=30),
            expires_at=NOW + timedelta(days=150),
            status=KnowledgeStatus.VALIDATED,
            provenance={"source": "OutcomeBridge", "version": "1.0"},
            revision_history=[],
            created_at=NOW - timedelta(days=60),
            updated_at=NOW,
        )
        assert k.replication_count == 5
        assert k.contrary_evidence_count == 1
        assert k.last_validated_at is not None
        assert k.expires_at is not None

    def test_default_field_values(self):
        k = Knowledge(
            id="K-003",
            statement="Test knowledge",
            hypothesis_ids=["H-001"],
            outcome_ids=["OC-001"],
            evidence_summary="Summary",
            confidence=0.3,
            conditions="All markets",
            scope="general",
            time_horizon="swing",
            status=KnowledgeStatus.EXTRACTED,
            created_at=NOW,
            updated_at=NOW,
        )
        assert k.missed_opportunity_ids == []
        assert k.replication_count == 0
        assert k.replication_conditions == []
        assert k.contrary_evidence_count == 0
        assert k.last_validated_at is None
        assert k.expires_at is None
        assert k.provenance == {}
        assert k.revision_history == []

    def test_has_20_attributes(self):
        k = Knowledge(
            id="K-004", statement="S", hypothesis_ids=[], outcome_ids=[],
            evidence_summary="S", confidence=0.5, conditions="C",
            scope="S", time_horizon="T", status=KnowledgeStatus.EXTRACTED,
            created_at=NOW, updated_at=NOW,
        )
        f = fields(k)
        assert len(f) == 20
        names = {fi.name for fi in f}
        expected = {
            "id", "statement", "hypothesis_ids", "outcome_ids",
            "missed_opportunity_ids", "evidence_summary", "confidence",
            "conditions", "scope", "time_horizon", "replication_count",
            "replication_conditions", "contrary_evidence_count",
            "last_validated_at", "expires_at", "status", "provenance",
            "revision_history", "created_at", "updated_at",
        }
        assert names == expected


class TestKnowledgeStatusEnum:
    def test_all_status_values(self):
        assert KnowledgeStatus.EXTRACTED.value == "extracted"
        assert KnowledgeStatus.PROVISIONAL.value == "provisional"
        assert KnowledgeStatus.VALIDATED.value == "validated"
        assert KnowledgeStatus.REVISED.value == "revised"
        assert KnowledgeStatus.INVALIDATED.value == "invalidated"
        assert KnowledgeStatus.ARCHIVED.value == "archived"
        assert len(KnowledgeStatus) == 6


class TestKnowledgeLifecycleTransitions:
    def test_valid_transitions_from_extracted(self):
        valid = VALID_TRANSITIONS[KnowledgeStatus.EXTRACTED]
        assert KnowledgeStatus.PROVISIONAL in valid
        assert KnowledgeStatus.ARCHIVED in valid

    def test_valid_transitions_from_provisional(self):
        valid = VALID_TRANSITIONS[KnowledgeStatus.PROVISIONAL]
        assert KnowledgeStatus.VALIDATED in valid
        assert KnowledgeStatus.REVISED in valid
        assert KnowledgeStatus.INVALIDATED in valid
        assert KnowledgeStatus.ARCHIVED in valid
        assert len(valid) == 4

    def test_valid_transitions_from_validated(self):
        valid = VALID_TRANSITIONS[KnowledgeStatus.VALIDATED]
        assert KnowledgeStatus.REVISED in valid
        assert KnowledgeStatus.INVALIDATED in valid
        assert KnowledgeStatus.ARCHIVED in valid

    def test_valid_transitions_from_revised(self):
        valid = VALID_TRANSITIONS[KnowledgeStatus.REVISED]
        assert KnowledgeStatus.VALIDATED in valid
        assert KnowledgeStatus.INVALIDATED in valid
        assert KnowledgeStatus.ARCHIVED in valid

    def test_valid_transitions_from_invalidated(self):
        valid = VALID_TRANSITIONS[KnowledgeStatus.INVALIDATED]
        assert KnowledgeStatus.ARCHIVED in valid
        assert len(valid) == 1

    def test_valid_transitions_from_archived(self):
        valid = VALID_TRANSITIONS[KnowledgeStatus.ARCHIVED]
        assert valid == []

    def test_invalid_transitions_extracted_skip_to_validated(self):
        assert KnowledgeStatus.VALIDATED not in VALID_TRANSITIONS[KnowledgeStatus.EXTRACTED]
        assert KnowledgeStatus.INVALIDATED not in VALID_TRANSITIONS[KnowledgeStatus.EXTRACTED]

    def test_invalid_transitions_archived_to_any(self):
        assert KnowledgeStatus.PROVISIONAL not in VALID_TRANSITIONS[KnowledgeStatus.ARCHIVED]
        assert KnowledgeStatus.VALIDATED not in VALID_TRANSITIONS[KnowledgeStatus.ARCHIVED]
        assert KnowledgeStatus.REVISED not in VALID_TRANSITIONS[KnowledgeStatus.ARCHIVED]

    def test_all_statuses_have_entry_in_transitions(self):
        for status in KnowledgeStatus:
            assert status in VALID_TRANSITIONS, f"Missing transition entry for {status}"


class TestKnowledgeSerialization:
    def test_to_dict(self):
        k = Knowledge(
            id="K-010", statement="Test", hypothesis_ids=["H-001"],
            outcome_ids=["OC-001"], evidence_summary="Sum",
            confidence=0.5, conditions="C", scope="S", time_horizon="T",
            status=KnowledgeStatus.PROVISIONAL,
            created_at=NOW, updated_at=NOW,
        )
        d = k.to_dict()
        assert d["id"] == "K-010"
        assert d["status"] == "provisional"
        assert d["confidence"] == 0.5

    def test_from_dict_roundtrip_minimal(self):
        k = Knowledge(
            id="K-011", statement="Test K", hypothesis_ids=["H-001"],
            outcome_ids=["OC-001"], evidence_summary="Evidence",
            confidence=0.5, conditions="Low vol", scope="crypto",
            time_horizon="swing", status=KnowledgeStatus.EXTRACTED,
            created_at=NOW, updated_at=NOW,
        )
        d = k.to_dict()
        k2 = Knowledge.from_dict(d)
        assert k2.id == k.id
        assert k2.statement == k.statement
        assert k2.status == k.status
        assert k2.confidence == k.confidence

    def test_from_dict_roundtrip_full(self):
        k = Knowledge(
            id="K-012", statement="Full test", hypothesis_ids=["H-001", "H-002"],
            outcome_ids=["OC-001", "OC-002"],
            missed_opportunity_ids=["MO-001"],
            evidence_summary="Full summary",
            confidence=0.72, conditions="Low vol, trending",
            scope="crypto", time_horizon="swing (3-10d)",
            replication_count=5,
            replication_conditions=[{"asset": "BTC", "regime": "low_vol"}],
            contrary_evidence_count=1,
            last_validated_at=NOW - timedelta(days=30),
            expires_at=NOW + timedelta(days=150),
            status=KnowledgeStatus.VALIDATED,
            provenance={"source": "OutcomeBridge", "version": "1.0"},
            revision_history=[{"date": "2026-01-01", "prev": "old statement"}],
            created_at=NOW - timedelta(days=60),
            updated_at=NOW,
        )
        d = k.to_dict()
        k2 = Knowledge.from_dict(d)
        assert k2.hypothesis_ids == k.hypothesis_ids
        assert k2.replication_count == k.replication_count
        assert k2.contrary_evidence_count == k.contrary_evidence_count
        assert k2.last_validated_at is not None
        assert k2.expires_at is not None
        assert k2.provenance == k.provenance
        assert k2.revision_history == k.revision_history
        assert k2.missed_opportunity_ids == k.missed_opportunity_ids


class TestKnowledgeExpirationFields:
    def test_decay_fields_present(self):
        k = Knowledge(
            id="K-020", statement="S", hypothesis_ids=[], outcome_ids=[],
            evidence_summary="S", confidence=0.5, conditions="C",
            scope="S", time_horizon="T", status=KnowledgeStatus.VALIDATED,
            created_at=NOW, updated_at=NOW,
        )
        assert hasattr(k, "expires_at")
        assert hasattr(k, "last_validated_at")

    def test_confidence_range(self):
        for conf in [0.0, 0.3, 0.5, 0.72, 1.0]:
            k = Knowledge(
                id=f"K-C-{conf}", statement="S", hypothesis_ids=[],
                outcome_ids=[], evidence_summary="S", confidence=conf,
                conditions="C", scope="S", time_horizon="T",
                status=KnowledgeStatus.PROVISIONAL, created_at=NOW, updated_at=NOW,
            )
            assert 0.0 <= k.confidence <= 1.0


class TestKnowledgeSchemaSQL:
    def test_table_schema_string(self):
        assert isinstance(KNOWLEDGE_TABLE_SCHEMA, str)
        assert "CREATE TABLE IF NOT EXISTS knowledge" in KNOWLEDGE_TABLE_SCHEMA

    def test_table_has_required_columns(self):
        required = ["id", "statement", "hypothesis_ids", "outcome_ids",
                     "evidence_summary", "confidence", "conditions",
                     "scope", "time_horizon", "replication_count",
                     "contrary_evidence_count", "status",
                     "created_at", "updated_at"]
        for col in required:
            assert col in KNOWLEDGE_TABLE_SCHEMA, f"Missing column: {col}"

    def test_table_has_optional_columns(self):
        optional = ["missed_opportunity_ids", "replication_conditions",
                     "last_validated_at", "expires_at", "provenance",
                     "revision_history"]
        for col in optional:
            assert col in KNOWLEDGE_TABLE_SCHEMA, f"Missing column: {col}"

    def test_table_has_indexes(self):
        assert "idx_knowledge_status" in KNOWLEDGE_TABLE_SCHEMA
        assert "idx_knowledge_confidence" in KNOWLEDGE_TABLE_SCHEMA
        assert "idx_knowledge_created" in KNOWLEDGE_TABLE_SCHEMA
        assert "idx_knowledge_expires" in KNOWLEDGE_TABLE_SCHEMA
        count = KNOWLEDGE_TABLE_SCHEMA.count("CREATE INDEX")
        assert count == 4


# ─────────────────────────────────────────────
# CriterionDelta Tests
# ─────────────────────────────────────────────

class TestCriterionDeltaCreation:
    def test_create_minimal(self):
        cd = CriterionDelta(
            id="CD-001",
            proposed_by="Criterion Evolution System",
            source_evidence={
                "knowledge_ids": ["K-001"],
                "hypothesis_ids": ["H-001"],
                "outcome_ids": ["OC-001"],
            },
            dimension="error_recurrence",
            change="Lower tolerance for WRONG_TIMING errors from 30% to 20%",
            confidence=0.72,
            status=DeltaStatus.PENDING_REVIEW,
            created_at=NOW,
        )
        assert cd.id == "CD-001"
        assert cd.status == DeltaStatus.PENDING_REVIEW

    def test_create_with_all_fields(self):
        cd = CriterionDelta(
            id="CD-002",
            proposed_by="Criterion Evolution System",
            source_evidence={
                "knowledge_ids": ["K-001", "K-002"],
                "hypothesis_ids": ["H-001", "H-002", "H-003"],
                "outcome_ids": ["OC-001", "OC-002", "OC-003"],
            },
            dimension="calibration",
            change="Adjust confidence baseline by -0.05",
            confidence=0.65,
            status=DeltaStatus.APPLIED,
            created_at=NOW - timedelta(days=10),
            applied_at=NOW,
            outcome_tracking={"brier_score_before": 0.35, "brier_score_after": 0.28},
        )
        assert cd.applied_at is not None
        assert cd.outcome_tracking is not None
        assert cd.status == DeltaStatus.APPLIED

    def test_default_field_values(self):
        cd = CriterionDelta(
            id="CD-003",
            proposed_by="System",
            source_evidence={"knowledge_ids": [], "hypothesis_ids": [], "outcome_ids": []},
            dimension="hypothesis_quality",
            change="Increase minimum specificity score",
            confidence=0.5,
            status=DeltaStatus.PENDING_REVIEW,
            created_at=NOW,
        )
        assert cd.applied_at is None
        assert cd.outcome_tracking is None


class TestCriterionDeltaStatusEnum:
    def test_all_status_values(self):
        assert DeltaStatus.PENDING_REVIEW.value == "pending_review"
        assert DeltaStatus.APPLIED.value == "applied"
        assert DeltaStatus.REJECTED.value == "rejected"
        assert len(DeltaStatus) == 3


class TestCriterionDeltaLifecycleTransitions:
    def test_valid_transitions_from_pending_review(self):
        valid = DELTA_VALID_TRANSITIONS[DeltaStatus.PENDING_REVIEW]
        assert DeltaStatus.APPLIED in valid
        assert DeltaStatus.REJECTED in valid

    def test_valid_transitions_from_applied(self):
        valid = DELTA_VALID_TRANSITIONS[DeltaStatus.APPLIED]
        assert valid == []

    def test_valid_transitions_from_rejected(self):
        valid = DELTA_VALID_TRANSITIONS[DeltaStatus.REJECTED]
        assert valid == []


class TestCriterionDeltaSerialization:
    def test_to_dict(self):
        cd = CriterionDelta(
            id="CD-010", proposed_by="System",
            source_evidence={"knowledge_ids": ["K-001"], "hypothesis_ids": [], "outcome_ids": []},
            dimension="error_recurrence", change="Reduce tolerance",
            confidence=0.6, status=DeltaStatus.PENDING_REVIEW,
            created_at=NOW,
        )
        d = cd.to_dict()
        assert d["id"] == "CD-010"
        assert d["dimension"] == "error_recurrence"
        assert d["status"] == "pending_review"

    def test_from_dict_roundtrip(self):
        cd = CriterionDelta(
            id="CD-011", proposed_by="System",
            source_evidence={
                "knowledge_ids": ["K-001", "K-002"],
                "hypothesis_ids": ["H-001"],
                "outcome_ids": ["OC-001", "OC-002"],
            },
            dimension="calibration", change="Adjust baseline",
            confidence=0.68, status=DeltaStatus.APPLIED,
            created_at=NOW - timedelta(days=5),
            applied_at=NOW,
            outcome_tracking={"brier_before": 0.3, "brier_after": 0.25},
        )
        d = cd.to_dict()
        cd2 = CriterionDelta.from_dict(d)
        assert cd2.id == cd.id
        assert cd2.dimension == cd.dimension
        assert cd2.status == cd.status
        assert cd2.source_evidence == cd.source_evidence
        assert cd2.applied_at is not None
        assert cd2.outcome_tracking == cd.outcome_tracking

    def test_from_dict_minimal(self):
        d = {
            "id": "CD-012",
            "proposed_by": "System",
            "source_evidence": '{"knowledge_ids": [], "hypothesis_ids": [], "outcome_ids": []}',
            "dimension": "hypothesis_quality",
            "change": "Increase threshold",
            "confidence": 0.55,
            "status": "rejected",
            "created_at": NOW.isoformat(),
        }
        cd = CriterionDelta.from_dict(d)
        assert cd.status == DeltaStatus.REJECTED
        assert cd.applied_at is None
        assert cd.outcome_tracking is None


class TestCriterionDeltaSchemaSQL:
    def test_table_schema_string(self):
        assert isinstance(CRITERION_DELTA_TABLE_SCHEMA, str)
        assert "CREATE TABLE IF NOT EXISTS criterion_deltas" in CRITERION_DELTA_TABLE_SCHEMA

    def test_table_has_required_columns(self):
        required = ["id", "proposed_by", "source_evidence", "dimension",
                     "change", "confidence", "status", "created_at"]
        for col in required:
            assert col in CRITERION_DELTA_TABLE_SCHEMA, f"Missing column: {col}"

    def test_table_has_indexes(self):
        assert "idx_criterion_deltas_dimension" in CRITERION_DELTA_TABLE_SCHEMA
        assert "idx_criterion_deltas_status" in CRITERION_DELTA_TABLE_SCHEMA
        assert "idx_criterion_deltas_created" in CRITERION_DELTA_TABLE_SCHEMA
        count = CRITERION_DELTA_TABLE_SCHEMA.count("CREATE INDEX")
        assert count == 3


# ─────────────────────────────────────────────
# Schema Exports (core/schemas/__init__.py)
# ─────────────────────────────────────────────

class TestSchemaExports:
    def test_outcome_comparison_exported(self):
        assert OutcomeComparison is not None
        assert Verdict is not None
        assert ErrorType is not None
        assert ComparisonType is not None
        assert OUTCOME_COMPARISON_TABLE_SCHEMA is not None

    def test_knowledge_exported(self):
        assert Knowledge is not None
        assert KnowledgeStatus is not None
        assert KNOWLEDGE_TABLE_SCHEMA is not None

    def test_criterion_delta_exported(self):
        assert CriterionDelta is not None
        assert DeltaStatus is not None
        assert CRITERION_DELTA_TABLE_SCHEMA is not None


# ─────────────────────────────────────────────
# Regression: Existing Schemas Unchanged
# ─────────────────────────────────────────────

class TestRegression:
    def test_hypothesis_schema_still_works(self):
        h = Hypothesis(
            id="H-REGRESSION", title="Reg test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X", confidence=0.5,
            status=HypothesisStatus.FORMULATED,
            created_at=NOW, updated_at=NOW,
        )
        assert h.status == HypothesisStatus.FORMULATED
        d = h.to_dict()
        h2 = Hypothesis.from_dict(d)
        assert h2.title == h.title
        assert h2.confidence == h.confidence

    def test_evidence_schema_still_works(self):
        e = Evidence(
            id="E-REGRESSION", hypothesis_id="H-001",
            direction=EvidenceDirection.SUPPORTS, weight=0.8,
            content="Supporting evidence", source_id="test",
            source_reliability=0.9, collected_at=NOW,
            independence_score=0.7,
        )
        assert e.direction == EvidenceDirection.SUPPORTS
        d = e.to_dict()
        e2 = Evidence.from_dict(d)
        assert e2.weight == e.weight
        assert e2.direction == e.direction

    def test_existing_enums_unchanged(self):
        assert HypothesisStatus.FORMULATED.value == "formulated"
        assert HypothesisStatus.ACTIVE.value == "active"
        assert HypothesisStatus.EVALUATED.value == "evaluated"
        assert HypothesisStatus.ARCHIVED.value == "archived"
        assert EvidenceDirection.SUPPORTS.value == "supports"
        assert EvidenceDirection.CONTRADICTS.value == "contradicts"

    def test_existing_schema_imports(self):
        import core.schemas.event_schema
        import core.schemas.agent_schema
        import core.schemas.trade_schema
        assert True

    def test_no_new_database_created(self):
        import os
        assert not os.path.exists("test_learning_core.db")
        assert not os.path.exists("test_oma_core.db")
