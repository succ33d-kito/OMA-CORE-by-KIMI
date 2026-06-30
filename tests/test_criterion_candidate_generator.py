"""Tests for Criterion Candidate Generator (O4) — Outcome patterns → deltas."""
import os
import pytest
from datetime import datetime, timezone
from core.schemas.outcome_comparison_schema import OutcomeComparison, Verdict, ComparisonType
from core.schemas.criterion_delta_schema import CriterionDelta, DeltaStatus
from core.scientific.scientific_store import ScientificStore
from core.scientific.criterion_candidate_generator import CriterionCandidateGenerator
from core.scientific.criterion_evolution import VALID_DIMENSIONS


TEST_DB = "test_criterion_generator.db"


@pytest.fixture
def empty_store():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    s = ScientificStore(db_path=TEST_DB)
    yield s
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture
def store_with_comparisons():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    s = ScientificStore(db_path=TEST_DB)

    # Create a hypothesis
    s.create_hypothesis(
        title="Test hypothesis",
        description="Test",
        predicted_consequence="Price goes up",
        conditions="When X",
        invalidation_conditions="When Y",
        confidence=0.6,
        hypothesis_id="hyp_cg_test_001",
    )

    # Add 5 confirmed comparisons
    for i in range(5):
        s.create_outcome_comparison(OutcomeComparison(
            id=f"cmp_cg_conf_{i}",
            hypothesis_id="hyp_cg_test_001",
            verdict=Verdict.CONFIRMED,
            comparison_type=ComparisonType.EXECUTED,
            predicted_consequence="Price goes up",
            actual_outcome=f"Price went up {i}%",
            comparison_confidence=0.8,
            compared_at=datetime.now(timezone.utc),
        ))

    # Add 1 rejected comparison
    s.create_outcome_comparison(OutcomeComparison(
        id="cmp_cg_rej_0",
        hypothesis_id="hyp_cg_test_001",
        verdict=Verdict.REJECTED,
        comparison_type=ComparisonType.EXECUTED,
        predicted_consequence="Price goes up",
        actual_outcome="Price went down",
        comparison_confidence=0.7,
        compared_at=datetime.now(timezone.utc),
    ))

    yield s
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture
def generator(store_with_comparisons):
    return CriterionCandidateGenerator(scientific_db=TEST_DB)


class TestAnalyzeRecentOutcomes:
    def test_analyze_empty_db(self, empty_store):
        gen = CriterionCandidateGenerator(scientific_db=TEST_DB)
        result = gen.analyze_recent_outcomes(limit=100)
        assert result["total_analyzed"] == 0
        assert result["recommended_deltas"] == []

    def test_analyze_with_data(self, generator):
        result = generator.analyze_recent_outcomes(limit=100)
        assert result["total_analyzed"] >= 6
        assert result["confirmed"] >= 5
        assert result["rejected"] >= 1
        assert "accuracy" in result

    def test_high_accuracy_pattern(self, generator):
        result = generator.analyze_recent_outcomes(limit=100)
        # 5 confirmed / 6 total ≈ 0.83 accuracy → high_accuracy should be True
        assert result["patterns"]["high_accuracy_confirm"] is True
        assert result["patterns"]["low_accuracy_reject"] is False

    def test_low_accuracy_pattern(self, empty_store):
        s = empty_store
        s.create_hypothesis(title="T", description="T",
                           predicted_consequence="X", conditions="Y",
                           invalidation_conditions="Z",
                           hypothesis_id="hyp_low_acc")
        for i in range(5):
            s.create_outcome_comparison(OutcomeComparison(
                id=f"cmp_low_rej_{i}", hypothesis_id="hyp_low_acc",
                verdict=Verdict.REJECTED,
                comparison_type=ComparisonType.EXECUTED,
                predicted_consequence="X", actual_outcome=f"Wrong {i}",
                comparison_confidence=0.5,
                compared_at=datetime.now(timezone.utc),
            ))
        gen = CriterionCandidateGenerator(scientific_db=TEST_DB)
        result = gen.analyze_recent_outcomes(limit=100)
        assert result["patterns"]["low_accuracy_reject"] is True
        assert result["patterns"]["high_accuracy_confirm"] is False


class TestGenerateCandidates:
    def test_no_candidates_with_empty_analysis(self, generator):
        result = generator.generate_candidates(
            {"total_analyzed": 0, "recommended_deltas": []},
            dry_run=True,
        )
        assert result["candidates_generated"] == 0

    def test_generates_candidates_for_high_accuracy(self, generator):
        analysis = generator.analyze_recent_outcomes(limit=100)
        result = generator.generate_candidates(analysis, dry_run=True)
        assert result["candidates_generated"] > 0
        assert result["dry_run"] is True

    def test_generated_candidates_are_pending_review(self, generator):
        analysis = generator.analyze_recent_outcomes(limit=100)
        result = generator.generate_candidates(analysis, dry_run=True)
        for c in result["candidates"]:
            assert c.status == DeltaStatus.PENDING_REVIEW

    def test_generated_candidates_have_valid_dimensions(self, generator):
        analysis = generator.analyze_recent_outcomes(limit=100)
        result = generator.generate_candidates(analysis, dry_run=True)
        for c in result["candidates"]:
            assert c.dimension in VALID_DIMENSIONS

    def test_commit_persists_candidates(self, generator):
        analysis = generator.analyze_recent_outcomes(limit=100)
        result = generator.generate_candidates(analysis, dry_run=False)
        assert result["dry_run"] is False
        deltas = generator.store.list_criterion_deltas(limit=10)
        assert len(deltas) >= result["candidates_generated"]


class TestRunPipeline:
    def test_run_pipeline_dry_run(self, generator):
        result = generator.run_pipeline(outcome_limit=100, dry_run=True)
        assert "analysis" in result
        assert "generation" in result
        assert result["generation"]["dry_run"] is True

    def test_run_pipeline_commit(self, generator):
        result = generator.run_pipeline(outcome_limit=100, dry_run=False)
        assert result["generation"]["dry_run"] is False


class TestGetCandidateStats:
    def test_get_stats(self, generator):
        generator.run_pipeline(outcome_limit=100, dry_run=False)
        stats = generator.get_candidate_stats()
        assert stats["total_deltas"] >= 0
        assert stats["pending_review"] >= 0
        assert "dimensions_affected" in stats
