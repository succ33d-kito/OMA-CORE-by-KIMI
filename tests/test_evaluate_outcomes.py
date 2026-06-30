"""Tests for Outcome Evaluator (O2) — Hypothesis vs reality comparison."""
import os
import pytest
from datetime import datetime, timezone
from core.schemas.outcome_comparison_schema import Verdict, ErrorType, ComparisonType
from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
from core.scientific.scientific_store import ScientificStore
from core.scientific.outcome_evaluator import (
    evaluate_hypotheses,
    auto_detect_verdict,
    parse_hypothesis_id,
    compute_outcome_score,
)
from core.scientific.outcome_bridge import TYPE_DIRECTION_MAP


TEST_DB = "test_evaluate_outcomes.db"


@pytest.fixture
def store():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    s = ScientificStore(db_path=TEST_DB)
    # Create test hypotheses
    s.create_hypothesis(
        title="[BRIDGE] LONG_SETUP: BTC bullish test",
        description="BTC will rise",
        predicted_consequence="Bitcoin price increases 3-5% within 5 days (bullish)",
        conditions="Test conditions",
        invalidation_conditions="BTC drops below support",
        confidence=0.7,
        hypothesis_id="hyp_test_001",
    )
    s.create_hypothesis(
        title="[BRIDGE] SHORT_SETUP: ETH bearish test",
        description="ETH will fall",
        predicted_consequence="ETH price decreases 2-4% within 3 days (bearish)",
        conditions="Test conditions",
        invalidation_conditions="ETH breaks resistance",
        confidence=0.6,
        hypothesis_id="hyp_test_002",
    )
    yield s
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestAutoDetectVerdict:
    def test_confirmed_keyword(self):
        verdict, confidence = auto_detect_verdict("confirmed the prediction", "bullish")
        assert verdict == Verdict.CONFIRMED
        assert confidence > 0.8

    def test_rejected_keyword(self):
        verdict, confidence = auto_detect_verdict("the hypothesis was wrong", "bullish")
        assert verdict == Verdict.REJECTED
        assert confidence > 0.7

    def test_inconclusive_keyword(self):
        verdict, confidence = auto_detect_verdict("outcome is unclear", "bullish")
        assert verdict == Verdict.INCONCLUSIVE

    def test_bullish_direction_confirmed(self):
        verdict, _ = auto_detect_verdict("Bitcoin surged 5%", "bullish")
        assert verdict == Verdict.CONFIRMED

    def test_bullish_direction_rejected(self):
        verdict, _ = auto_detect_verdict("Bitcoin crashed 5%", "bullish")
        assert verdict == Verdict.REJECTED

    def test_bearish_direction_confirmed(self):
        verdict, _ = auto_detect_verdict("ETH dropped 3% as expected", "bearish")
        assert verdict == Verdict.CONFIRMED

    def test_bearish_direction_rejected(self):
        verdict, _ = auto_detect_verdict("ETH rallied 4% which was opposite", "bearish")
        assert verdict == Verdict.REJECTED

    def test_flat_outcome_inconclusive(self):
        verdict, _ = auto_detect_verdict("price remained unchanged", "bullish")
        assert verdict == Verdict.INCONCLUSIVE

    def test_neutral_direction(self):
        verdict, _ = auto_detect_verdict("market performance was nominal today", "neutral")
        assert verdict == Verdict.CONFIRMED


class TestComputeOutcomeScore:
    def test_confirmed_score(self, store):
        hyp = store.get_hypothesis("hyp_test_001")
        result = compute_outcome_score(Verdict.CONFIRMED, 0.8, "up", hyp)
        assert result["outcome_score"] == 100

    def test_rejected_score(self, store):
        hyp = store.get_hypothesis("hyp_test_001")
        result = compute_outcome_score(Verdict.REJECTED, 0.8, "down", hyp)
        assert result["outcome_score"] == 0

    def test_inconclusive_score(self, store):
        hyp = store.get_hypothesis("hyp_test_001")
        result = compute_outcome_score(Verdict.INCONCLUSIVE, 0.5, "mixed", hyp)
        assert result["outcome_score"] == 30


class TestEvaluateHypotheses:
    def test_evaluate_all_dry_run(self, store):
        result = evaluate_hypotheses(
            hypothesis_ids=[],
            actual_outcomes={"all": "Bitcoin surged 5% confirming prediction"},
            store=store,
            dry_run=True,
        )
        assert result["total_hypotheses"] == 2
        assert result["evaluated"] == 2
        assert result["dry_run"] is True

    def test_evaluate_specific_hypothesis(self, store):
        result = evaluate_hypotheses(
            hypothesis_ids=["hyp_test_001"],
            actual_outcomes={"hyp_test_001": "Price surged 5% as expected"},
            store=store,
            dry_run=True,
        )
        assert result["evaluated"] == 1
        assert result["results"][0]["hypothesis_id"] == "hyp_test_001"

    def test_evaluate_confirmed_outcome(self, store):
        result = evaluate_hypotheses(
            hypothesis_ids=["hyp_test_001"],
            actual_outcomes={"hyp_test_001": "confirmed the bullish prediction"},
            store=store,
            dry_run=True,
        )
        assert result["results"][0]["verdict"] == "confirmed"

    def test_evaluate_rejected_outcome(self, store):
        result = evaluate_hypotheses(
            hypothesis_ids=["hyp_test_001"],
            actual_outcomes={"hyp_test_001": "the hypothesis was wrong"},
            store=store,
            dry_run=True,
        )
        assert result["results"][0]["verdict"] == "rejected"
        assert result["results"][0]["error_type"] is not None

    def test_evaluate_no_match(self, store):
        result = evaluate_hypotheses(
            hypothesis_ids=["hyp_test_001"],
            actual_outcomes={"hyp_test_999": "Some outcome"},
            store=store,
            dry_run=True,
        )
        assert result["evaluated"] == 0

    def test_evaluate_commit_persists(self, store):
        result = evaluate_hypotheses(
            hypothesis_ids=["hyp_test_001"],
            actual_outcomes={"hyp_test_001": "confirmed outcome"},
            store=store,
            dry_run=False,
        )
        assert result["dry_run"] is False
        comparisons = store.list_outcome_comparisons(limit=10)
        assert len(comparisons) >= 1
        assert comparisons[0].hypothesis_id == "hyp_test_001"


class TestParseHypothesisId:
    def test_parse_all(self, store):
        assert parse_hypothesis_id("all", store) == "all"

    def test_parse_exact_match(self, store):
        assert parse_hypothesis_id("hyp_test_001", store) == "hyp_test_001"

    def test_parse_prefix_match(self, store):
        result = parse_hypothesis_id("hyp_test_001", store)
        assert result == "hyp_test_001"

    def test_parse_no_match(self, store):
        result = parse_hypothesis_id("nonexistent", store)
        assert result == "nonexistent"
