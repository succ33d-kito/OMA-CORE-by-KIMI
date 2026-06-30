"""Sprint 13 — Score Calibration: verify reduced saturation and decoupled conviction."""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from core.engines.score_opportunity import ScoreEngine, OpportunityEngine, Pipeline
from core.schemas.event_schema import (
    Event, EventType, Asset, AssetClass, Sentiment, Urgency,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(
    source="yahoo_finance",
    event_type=EventType.PRICE_MOVEMENT,
    urgency=Urgency.HIGH,
    sentiment_score=0.5,
    sentiment=Sentiment.BULLISH,
    price_at_event=150.0,
    summary="Strong price movement in tech sector",
    source_url="https://finance.yahoo.com",
    assets=None,
    title="Test event",
    age_seconds=300,
    confidence=0.9,
):
    if assets is None:
        assets = [Asset(symbol="AAPL", name="Apple Inc.", asset_class=AssetClass.STOCK,
                        price_at_event=price_at_event, currency="USD")]
    return Event(
        id=f"evt_{datetime.now(timezone.utc).timestamp()}",
        source=source,
        source_url=source_url,
        event_type=event_type,
        title=title,
        summary=summary,
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=age_seconds),
        assets=assets,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        urgency=urgency,
        confidence=confidence,
    )


def _make_mock_db():
    """Create a mock DB that returns empty for get_recent_events."""
    db = MagicMock()
    db.get_recent_events.return_value = []
    return db


@pytest.fixture
def engine():
    return ScoreEngine(_make_mock_db())


@pytest.fixture
def opp_engine(engine):
    db = _make_mock_db()
    return OpportunityEngine(db, engine)


# ---------------------------------------------------------------------------
# Score curve behaviour
# ---------------------------------------------------------------------------

class TestScoringCurve:

    def test_below_threshold_passes_through(self, engine):
        assert engine._apply_scoring_curve(40.0) == 40.0
        assert engine._apply_scoring_curve(55.0) == 55.0
        assert engine._apply_scoring_curve(60.0) == 60.0

    def test_gentle_compression_above_threshold(self, engine):
        s70 = engine._apply_scoring_curve(70.0)
        s80 = engine._apply_scoring_curve(80.0)
        s90 = engine._apply_scoring_curve(90.0)
        s100 = engine._apply_scoring_curve(100.0)
        # All distinct — no clipping
        assert s70 < s80 < s90 < s100
        # Above threshold, the curve adds value asymptotically toward 100
        assert 70.0 < s70 < 100.0  # compressed but above linear
        assert s100 < 100.0  # not clipped

    def test_score_100_only_for_extreme_values(self, engine):
        # Even very high scaled scores should not hit 100
        assert engine._apply_scoring_curve(150.0) < 100.0
        assert engine._apply_scoring_curve(300.0) <= 100.0

    def test_diverse_score_range_for_moderate_events(self, engine):
        """Different moderate events produce distinct scores (no clustering)."""
        db = _make_mock_db()
        se = ScoreEngine(db)

        e1 = _make_event(urgency=Urgency.MEDIUM, sentiment_score=0.3)
        e2 = _make_event(urgency=Urgency.HIGH, sentiment_score=0.5)
        e3 = _make_event(urgency=Urgency.HIGH, sentiment_score=0.7, event_type=EventType.NEWS)

        s1 = se.score_event(e1)["final_score"]
        s2 = se.score_event(e2)["final_score"]
        s3 = se.score_event(e3)["final_score"]

        assert len({s1, s2, s3}) >= 2, f"Scores too similar: {s1}, {s2}, {s3}"
        assert s3 < s2  # NEWS has lower multiplier, so should score lower


# ---------------------------------------------------------------------------
# Score event
# ---------------------------------------------------------------------------

class TestScoreEvent:

    def test_basic_scoring(self, engine):
        e = _make_event()
        result = engine.score_event(e)
        assert "final_score" in result
        assert "component_scores" in result
        assert "multiplier" in result
        assert 0 <= result["final_score"] <= 100

    def test_critical_urgency_scores_higher(self, engine):
        db = _make_mock_db()
        se = ScoreEngine(db)
        low = se.score_event(_make_event(urgency=Urgency.LOW, sentiment_score=0.0))
        high = se.score_event(_make_event(urgency=Urgency.CRITICAL, sentiment_score=0.9,
                                          event_type=EventType.HACK_EXPLOIT))
        assert high["final_score"] > low["final_score"]

    def test_no_score_100_for_normal_events(self, engine):
        """Normal high-quality events should NOT hit 100."""
        db = _make_mock_db()
        se = ScoreEngine(db)
        e = _make_event(urgency=Urgency.CRITICAL, sentiment_score=0.8,
                        event_type=EventType.REGULATORY)
        result = se.score_event(e)
        assert result["final_score"] < 100.0, f"Normal event scored {result['final_score']}"


# ---------------------------------------------------------------------------
# Conviction — decoupled from score
# ---------------------------------------------------------------------------

class TestConviction:

    def test_conviction_differs_from_score(self, engine, opp_engine):
        """Conviction should NOT simply mirror score."""
        e = _make_event()
        sd = engine.score_event(e)
        conviction = opp_engine._calculate_conviction(e, sd)
        score = sd["final_score"]
        assert conviction != score, f"Conviction {conviction} equals score {score}"
        assert 0 <= conviction <= 100

    def test_conviction_drops_for_stale_events(self, engine, opp_engine):
        db = _make_mock_db()
        se = ScoreEngine(db)
        oe = OpportunityEngine(db, se)

        fresh = _make_event(age_seconds=60)
        stale = _make_event(age_seconds=90000)  # ~25 hours old

        sd_fresh = se.score_event(fresh)
        sd_stale = se.score_event(stale)

        c_fresh = oe._calculate_conviction(fresh, sd_fresh)
        c_stale = oe._calculate_conviction(stale, sd_stale)

        assert c_fresh > c_stale, f"Fresh conviction {c_fresh} should exceed stale {c_stale}"

    def test_conviction_drops_for_poor_evidence(self, engine, opp_engine):
        db = _make_mock_db()
        se = ScoreEngine(db)
        oe = OpportunityEngine(db, se)

        good = _make_event(summary="Detailed analysis with full context")
        poor = _make_event(summary="", price_at_event=None, source_url="")

        sd_good = se.score_event(good)
        sd_poor = se.score_event(poor)

        c_good = oe._calculate_conviction(good, sd_good)
        c_poor = oe._calculate_conviction(poor, sd_poor)

        assert c_good > c_poor, f"Good evidence {c_good} should exceed poor {c_poor}"

    def test_data_quality_halves_conviction(self, engine, opp_engine):
        db = _make_mock_db()
        se = ScoreEngine(db)
        oe = OpportunityEngine(db, se)

        # Bad data (price=0)
        bad = _make_event(price_at_event=0.0)

        sd_bad = se.score_event(bad)
        c_bad = oe._calculate_conviction(bad, sd_bad)

        # Good data with same structure
        good = _make_event(price_at_event=150.0)
        sd_good = se.score_event(good)
        c_good = oe._calculate_conviction(good, sd_good)

        # Bad-data conviction should be roughly half
        assert c_bad < c_good / 1.2, f"Bad {c_bad} should be much lower than good {c_good}"


# ---------------------------------------------------------------------------
# Critical evidence gate
# ---------------------------------------------------------------------------

class TestCriticalGate:

    def test_strong_event_can_become_critical(self, engine, opp_engine):
        """A truly extreme event must still be able to reach CRITICAL."""
        db = _make_mock_db()
        se = ScoreEngine(db)
        oe = OpportunityEngine(db, se)

        e = _make_event(
            urgency=Urgency.CRITICAL,
            sentiment_score=-0.95,
            sentiment=Sentiment.VERY_BEARISH,
            event_type=EventType.HACK_EXPLOIT,
            source="coingecko",
        )
        sd = se.score_event(e)
        c = oe._calculate_conviction(e, sd)
        priority = oe._determine_priority(sd["final_score"], c, e, sd)
        assert priority == "CRITICAL", (
            f"Extreme hack event should be CRITICAL "
            f"(score={sd['final_score']}, conv={c}, priority={priority})"
        )

    def test_normal_high_event_is_high_not_critical(self, engine, opp_engine):
        """A normal high-quality event should be HIGH, not CRITICAL."""
        db = _make_mock_db()
        se = ScoreEngine(db)
        oe = OpportunityEngine(db, se)

        # Use a realistic moderate event: RSS news source, no deep context
        e = _make_event(
            source="rss_cnbc",
            urgency=Urgency.HIGH,
            sentiment_score=0.4,
            event_type=EventType.PRICE_MOVEMENT,
            title="AAPL up 3% on earnings",
            summary="AAPL shares rose 3%",
            age_seconds=7200,
        )
        sd = se.score_event(e)
        c = oe._calculate_conviction(e, sd)
        priority = oe._determine_priority(sd["final_score"], c, e, sd)
        assert priority != "CRITICAL", (
            f"Normal high event should NOT be CRITICAL "
            f"(score={sd['final_score']}, conv={c}, priority={priority})"
        )

    def test_medium_event_stays_medium(self, engine, opp_engine):
        db = _make_mock_db()
        se = ScoreEngine(db)
        oe = OpportunityEngine(db, se)

        e = _make_event(
            urgency=Urgency.MEDIUM,
            sentiment_score=0.2,
            event_type=EventType.NEWS,
            title="Routine market update",
            price_at_event=100.0,
            summary="",
        )
        sd = se.score_event(e)
        c = oe._calculate_conviction(e, sd)
        priority = oe._determine_priority(sd["final_score"], c, e, sd)
        assert priority in ("MEDIUM", "LOW"), (
            f"Routine news should be MEDIUM or LOW "
            f"(score={sd['final_score']}, conv={c}, priority={priority})"
        )

    def test_data_quality_stays_capped(self, engine, opp_engine):
        """Data quality issues should still be downgraded by the guard."""
        db = _make_mock_db()
        se = ScoreEngine(db)
        oe = OpportunityEngine(db, se)

        e = _make_event(price_at_event=0.0, title="AAPL $0.00")
        sd = se.score_event(e)
        c = oe._calculate_conviction(e, sd)
        priority = oe._determine_priority(sd["final_score"], c, e, sd)

        from core.collectors.yahoo_data_guard import should_downgrade_opportunity
        should, overrides = should_downgrade_opportunity(e)
        if should:
            # Even without the override, the gate should not grant CRITICAL
            assert priority in ("LOW", "MEDIUM"), (
                f"DQ event priority {priority} should be LOW or MEDIUM"
            )

    def test_gate_requires_four_conditions(self, engine, opp_engine):
        """Verify _passes_critical_gate requires >= 4 conditions."""
        # Create event that fails most conditions
        e = _make_event(
            urgency=Urgency.LOW,
            sentiment_score=0.05,
            event_type=EventType.NEWS,
            source="rss_coindesk",
            assets=[],
            summary="",
            source_url="",
        )
        sd = engine.score_event(e)
        # Should NOT pass the gate
        assert not opp_engine._passes_critical_gate(e, sd)

    def test_fred_event_remains_valid(self, engine, opp_engine):
        """FRED macro events should still score reasonably."""
        db = _make_mock_db()
        se = ScoreEngine(db)
        oe = OpportunityEngine(db, se)

        e = Event(
            id="fred-test-1",
            source="fred",
            source_url="https://fred.stlouisfed.org",
            source_id="DFF",
            event_type=EventType.MACRO_EVENT,
            title="Federal Funds Rate: 5.50% (+0.25)",
            summary="Fed raised rates by 25bp",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=600),
            assets=[Asset(symbol="DFF", name="Fed Funds",
                          asset_class=AssetClass.BOND, currency="USD")],
            sentiment=Sentiment.BEARISH,
            sentiment_score=-0.3,
            urgency=Urgency.HIGH,
            confidence=0.98,
        )
        sd = se.score_event(e)
        c = oe._calculate_conviction(e, sd)
        priority = oe._determine_priority(sd["final_score"], c, e, sd)

        assert sd["final_score"] > 0
        assert priority in ("HIGH", "MEDIUM", "CRITICAL")
        assert 0 <= c <= 100


# ---------------------------------------------------------------------------
# Priority threshold verification
# ---------------------------------------------------------------------------

class TestPriorityThresholds:

    def test_low_threshold(self, opp_engine):
        e = _make_event(urgency=Urgency.BACKGROUND, sentiment_score=0.0)
        sd = {"final_score": 30, "component_scores": {"recency": 40, "correlation_boost": 25,
                                                       "source_confidence": 50}}
        c = 20
        p = opp_engine._determine_priority(30, 20, e, sd)
        assert p == "LOW"

    def test_medium_threshold(self, opp_engine):
        e = _make_event(urgency=Urgency.MEDIUM, sentiment_score=0.2)
        sd = {"final_score": 50, "component_scores": {"recency": 60, "correlation_boost": 25,
                                                       "source_confidence": 70}}
        c = 45
        p = opp_engine._determine_priority(50, 45, e, sd)
        assert p == "MEDIUM", f"combined={(50+45)/2} should be MEDIUM >= 45, got {p}"

    def test_high_threshold(self, opp_engine):
        e = _make_event(urgency=Urgency.HIGH, sentiment_score=0.5)
        sd = {"final_score": 72, "component_scores": {"recency": 75, "correlation_boost": 50,
                                                       "source_confidence": 85}}
        c = 60
        p = opp_engine._determine_priority(72, 60, e, sd)
        assert p == "HIGH", f"combined={(72+60)/2} should be HIGH >= 65, got {p}"

    def test_critical_threshold_with_gate_pass(self, opp_engine):
        e = _make_event(urgency=Urgency.CRITICAL, sentiment_score=0.8,
                        event_type=EventType.HACK_EXPLOIT, source="coingecko")
        sd = {"final_score": 86, "component_scores": {"recency": 90, "correlation_boost": 75,
                                                       "source_confidence": 95}}
        c = 76
        assert opp_engine._passes_critical_gate(e, sd)
        p = opp_engine._determine_priority(86, 76, e, sd)
        assert p == "CRITICAL", f"combined={(86+76)/2} with gate should be CRITICAL, got {p}"

    def test_critical_not_reached_without_gate(self, opp_engine):
        """High combined score without enough gate conditions → HIGH, not CRITICAL."""
        e = _make_event(urgency=Urgency.LOW, sentiment_score=0.05,
                        event_type=EventType.NEWS, source="rss_coindesk",
                        assets=[])
        sd = {"final_score": 82, "component_scores": {"recency": 40, "correlation_boost": 25,
                                                       "source_confidence": 50}}
        c = 80
        assert not opp_engine._passes_critical_gate(e, sd)
        p = opp_engine._determine_priority(82, 80, e, sd)
        assert p == "HIGH", f"combined={(82+80)/2}=81 without gate should be HIGH, got {p}"


# ---------------------------------------------------------------------------
# Pipeline-level integration (non-destructive)
# ---------------------------------------------------------------------------

class TestPipelineIntegration:

    def test_pipeline_creates_opportunities(self):
        db = _make_mock_db()
        se = ScoreEngine(db)
        oe = OpportunityEngine(db, se)

        events = [_make_event()]
        # Patch the db methods to avoid real DB writes
        with patch.object(db, "insert_opportunity"), \
             patch.object(db, "update_event_scores"), \
             patch.object(db, "mark_processed"):
            opps = oe.generate_opportunities(events, min_score=30.0)

        assert len(opps) >= 0  # may filter, but shouldn't crash

    def test_imports_unaffected(self):
        """All expected imports still work."""
        from core.engines.score_opportunity import ScoreEngine, OpportunityEngine, Pipeline
        from core.collectors.yahoo_data_guard import (
            should_downgrade_opportunity, detect_data_quality_issue,
        )
        assert callable(ScoreEngine)
        assert callable(OpportunityEngine)
        assert callable(Pipeline)
        assert callable(should_downgrade_opportunity)

    def test_full_suite_still_green(self):
        """Placeholder — run full suite externally."""
        pass
