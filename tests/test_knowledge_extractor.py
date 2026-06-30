"""Tests for Knowledge Extractor (O3) — Confirmed outcomes → Knowledge."""
import os
import pytest
from datetime import datetime, timezone
from core.schemas.outcome_comparison_schema import OutcomeComparison, Verdict, ComparisonType
from core.schemas.knowledge_schema import Knowledge, KnowledgeStatus
from core.scientific.scientific_store import ScientificStore
from core.scientific.knowledge_extractor import KnowledgeExtractor


TEST_DB = "test_knowledge_extractor.db"


@pytest.fixture
def store():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    s = ScientificStore(db_path=TEST_DB)
    # Create a hypothesis
    s.create_hypothesis(
        title="Test hypothesis",
        description="Test description",
        predicted_consequence="Price will go up",
        conditions="When X happens",
        invalidation_conditions="When Y happens",
        confidence=0.6,
        hypothesis_id="hyp_kn_test_001",
    )
    # Create a confirmed comparison
    comparison = OutcomeComparison(
        id="cmp_kn_001",
        hypothesis_id="hyp_kn_test_001",
        verdict=Verdict.CONFIRMED,
        comparison_type=ComparisonType.EXECUTED,
        predicted_consequence="Price will go up",
        actual_outcome="Price went up 5%",
        comparison_confidence=0.85,
        compared_at=datetime.now(timezone.utc),
    )
    s.create_outcome_comparison(comparison)

    # Create a rejected comparison
    rejected = OutcomeComparison(
        id="cmp_kn_002",
        hypothesis_id="hyp_kn_test_001",
        verdict=Verdict.REJECTED,
        comparison_type=ComparisonType.EXECUTED,
        predicted_consequence="Price will go up",
        actual_outcome="Price went down",
        comparison_confidence=0.7,
        compared_at=datetime.now(timezone.utc),
    )
    s.create_outcome_comparison(rejected)

    # Create a partially confirmed comparison
    partial = OutcomeComparison(
        id="cmp_kn_003",
        hypothesis_id="hyp_kn_test_001",
        verdict=Verdict.PARTIALLY_CONFIRMED,
        comparison_type=ComparisonType.EXECUTED,
        predicted_consequence="Price will go up",
        actual_outcome="Price went up slightly",
        comparison_confidence=0.6,
        compared_at=datetime.now(timezone.utc),
    )
    s.create_outcome_comparison(partial)

    yield s
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture
def extractor(store):
    return KnowledgeExtractor(scientific_db=TEST_DB)


class TestExtractFromComparison:
    def test_extract_from_confirmed(self, extractor):
        result = extractor.extract_from_comparison(
            comparison_id="cmp_kn_001",
            statement="When X happens, price goes up",
            scope="crypto",
            time_horizon="swing",
        )
        assert "knowledge" in result
        assert result["knowledge"].status == KnowledgeStatus.EXTRACTED
        assert "cmp_kn_001" in result["knowledge"].outcome_ids
        assert result["knowledge"].confidence > 0.3

    def test_extract_from_rejected_returns_error(self, extractor):
        result = extractor.extract_from_comparison(
            comparison_id="cmp_kn_002",
            scope="general",
            time_horizon="swing",
        )
        assert "error" in result
        assert "rejected" in result["error"].lower()

    def test_extract_from_partially_confirmed(self, extractor):
        result = extractor.extract_from_comparison(
            comparison_id="cmp_kn_003",
            scope="general",
            time_horizon="swing",
        )
        assert "knowledge" in result
        assert result["knowledge"].status == KnowledgeStatus.EXTRACTED

    def test_extract_nonexistent_comparison(self, extractor):
        result = extractor.extract_from_comparison(
            comparison_id="nonexistent",
            scope="general",
            time_horizon="swing",
        )
        assert "error" in result

    def test_knowledge_provenance(self, extractor):
        result = extractor.extract_from_comparison(
            comparison_id="cmp_kn_001",
            scope="crypto",
            time_horizon="swing",
        )
        k = result["knowledge"]
        assert k.provenance["extractor"] == "knowledge_extractor.py"
        assert k.provenance["source_comparison"] == "cmp_kn_001"
        assert "extracted_at" in k.provenance


class TestExtractAllConfirmed:
    def test_extract_all_confirmed_dry_run(self, extractor):
        result = extractor.extract_all_confirmed(dry_run=True)
        assert result["dry_run"] is True
        assert result["confirmed_comparisons"] >= 2  # confirmed + partially

    def test_extract_all_confirmed_commit(self, extractor):
        result = extractor.extract_all_confirmed(dry_run=False)
        assert result["dry_run"] is False
        # Should have extracted at least 1
        assert result["extracted"] >= 1

    def test_extract_all_confirmed_deduplicates(self, extractor):
        # First extraction
        extractor.extract_all_confirmed(dry_run=False)
        # Second extraction should skip duplicates
        result = extractor.extract_all_confirmed(dry_run=True)
        assert result["skipped_duplicates"] >= 1


class TestGetExtractionStats:
    def test_get_stats_empty(self, extractor):
        stats = extractor.get_extraction_stats()
        assert "total_knowledge_items" in stats
        assert "confirmed_outcomes_available" in stats
        assert "remaining_to_extract" in stats

    def test_get_stats_after_extraction(self, extractor):
        extractor.extract_all_confirmed(dry_run=False)
        stats = extractor.get_extraction_stats()
        assert stats["total_knowledge_items"] >= 1
