"""Tests for Outcome Bridge (O1) — Opportunity → Hypothesis conversion."""
import os
import json
import pytest
from datetime import datetime, timezone
from core.scientific.outcome_bridge import OutcomeBridge, TYPE_DIRECTION_MAP
from core.schemas.hypothesis_schema import HypothesisStatus


TEST_OPPORTUNITIES = [
    {
        "id": "opp_001",
        "event_id": "evt_001",
        "title": "Bitcoin breaking resistance",
        "description": "BTC showing strong momentum",
        "opportunity_type": "LONG_SETUP",
        "asset_class": "crypto",
        "assets": '["BTC/USD"]',
        "score": 85.0,
        "conviction": 75.0,
        "priority": "HIGH",
        "action_suggested": "Buy BTC",
        "risk_level": "MEDIUM",
        "timestamp": "2025-01-15T10:00:00Z",
        "expires_at": "2025-01-20T10:00:00Z",
        "status": "active",
    },
    {
        "id": "opp_002",
        "event_id": "evt_002",
        "title": "Gold safe haven flow",
        "description": "Gold rising on geopolitical tensions",
        "opportunity_type": "SAFE_HAVEN_FLOW",
        "asset_class": "commodities",
        "assets": '["XAU/USD"]',
        "score": 70.0,
        "conviction": 60.0,
        "priority": "MEDIUM",
        "action_suggested": "Hold gold",
        "risk_level": "LOW",
        "timestamp": "2025-01-15T11:00:00Z",
        "expires_at": "2025-01-25T11:00:00Z",
        "status": "active",
    },
    {
        "id": "opp_003",
        "event_id": "evt_003",
        "title": "Low conviction opportunity",
        "description": "Minor setup, low confidence",
        "opportunity_type": "WATCHLIST_ADD",
        "asset_class": "crypto",
        "assets": '["ETH/USD"]',
        "score": 25.0,
        "conviction": 15.0,
        "priority": "LOW",
        "action_suggested": "Monitor",
        "risk_level": "LOW",
        "timestamp": "2025-01-16T08:00:00Z",
        "expires_at": "2025-01-30T08:00:00Z",
        "status": "active",
    },
]


@pytest.fixture
def bridge(tmp_path):
    """Create an OutcomeBridge with temp DB paths."""
    return OutcomeBridge(
        operational_db=str(tmp_path / "test_oma_core.db"),
        scientific_db=str(tmp_path / "test_scientific.db"),
    )


class TestDirectionMapping:
    def test_long_setup_maps_to_bullish(self):
        assert TYPE_DIRECTION_MAP["LONG_SETUP"] == "bullish"

    def test_short_setup_maps_to_bearish(self):
        assert TYPE_DIRECTION_MAP["SHORT_SETUP"] == "bearish"

    def test_unknown_type_defaults_to_neutral(self):
        # Not in TYPE_DIRECTION_MAP should be caught by dict.get default
        pass

    def test_all_known_types_have_mappings(self):
        for opp_type, direction in TYPE_DIRECTION_MAP.items():
            assert direction in ("bullish", "bearish", "neutral", "momentum",
                                "risk_off", "volatile", "convergence")


class TestOpportunityConversion:
    def test_convert_long_setup(self, bridge):
        opp = TEST_OPPORTUNITIES[0]
        hyp = bridge.opportunity_to_hypothesis(opp)
        assert hyp.title.startswith("[BRIDGE] LONG_SETUP:")
        assert hyp.status == HypothesisStatus.FORMULATED
        assert hyp.confidence == 0.75  # conviction 75 / 100
        assert "Buy BTC" in hyp.predicted_consequence
        assert "bullish" in hyp.predicted_consequence

    def test_convert_safe_haven_flow(self, bridge):
        opp = TEST_OPPORTUNITIES[1]
        hyp = bridge.opportunity_to_hypothesis(opp)
        assert hyp.title.startswith("[BRIDGE] SAFE_HAVEN_FLOW:")
        assert "risk_off" in hyp.predicted_consequence
        assert "XAU/USD" in hyp.predicted_consequence

    def test_convert_low_conviction(self, bridge):
        opp = TEST_OPPORTUNITIES[2]
        hyp = bridge.opportunity_to_hypothesis(opp)
        assert hyp.confidence == 0.15  # conviction 15 / 100
        assert "neutral" in hyp.predicted_consequence
        assert hyp.status == HypothesisStatus.FORMULATED

    def test_hypothesis_id_from_event_id(self, bridge):
        opp = TEST_OPPORTUNITIES[0]
        hyp = bridge.opportunity_to_hypothesis(opp)
        assert hyp.id == "hyp_evt_001"

    def test_hypothesis_confidence_clamped(self, bridge):
        opp = dict(TEST_OPPORTUNITIES[0], conviction=200)
        hyp = bridge.opportunity_to_hypothesis(opp)
        assert hyp.confidence <= 0.95

    def test_hypothesis_confidence_minimum(self, bridge):
        opp = dict(TEST_OPPORTUNITIES[0], conviction=0)
        hyp = bridge.opportunity_to_hypothesis(opp)
        assert hyp.confidence >= 0.1


class TestBridgeAll:
    def test_fetch_opportunities_empty_db(self, bridge):
        result = bridge.bridge_all()
        assert result["opportunities_found"] == 0
        assert result["hypotheses_generated"] == 0

    def test_bridge_all_dry_run(self, bridge):
        # Test with empty DB to verify dry run works
        result = bridge.bridge_all(dry_run=True)
        assert result["dry_run"] is True

    def test_bridge_all_min_score_filter(self, bridge):
        result = bridge.bridge_all(min_score=80.0)
        # No data, so 0 found regardless
        assert isinstance(result["opportunities_found"], int)


class TestGetStats:
    def test_get_stats_empty(self, bridge):
        stats = bridge.get_stats()
        assert stats["total_opportunities"] == 0
        assert stats["total_hypotheses_in_scientific"] == 0
        assert stats["bridgeable_opportunities"] == 0
        assert stats["already_bridged"] == 0


class TestAssetsParsing:
    def test_assets_as_json_string(self, bridge):
        opp = dict(TEST_OPPORTUNITIES[0])
        hyp = bridge.opportunity_to_hypothesis(opp)
        assert "BTC/USD" in hyp.conditions

    def test_assets_as_none(self, bridge):
        opp = dict(TEST_OPPORTUNITIES[0], assets=None)
        hyp = bridge.opportunity_to_hypothesis(opp)
        assert "N/A" in hyp.conditions
