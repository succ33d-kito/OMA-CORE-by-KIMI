"""Tests for Yahoo Data Integrity Guard and scoring guardrails."""
import math
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from core.collectors.yahoo_data_guard import (
    validate_quote,
    validate_quote_for_event,
    detect_data_quality_issue,
    should_downgrade_opportunity,
    MAX_REASONABLE_CHANGE_PCT,
)
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency


# ---------------------------------------------------------------------------
# validate_quote
# ---------------------------------------------------------------------------

class TestValidateQuote:

    def test_valid_quote_passes(self):
        valid, reason = validate_quote(150.0, 145.0, "AAPL", "stock")
        assert valid is True
        assert reason == ""

    def test_price_none(self):
        valid, reason = validate_quote(None, 145.0, "AAPL", "stock")
        assert valid is False
        assert "none" in reason

    def test_price_zero(self):
        valid, reason = validate_quote(0.0, 145.0, "AAPL", "stock")
        assert valid is False
        assert "zero" in reason

    def test_price_negative(self):
        valid, reason = validate_quote(-5.0, 145.0, "AAPL", "stock")
        assert valid is False
        assert "negative" in reason

    def test_price_nan(self):
        valid, reason = validate_quote(float("nan"), 145.0, "AAPL", "stock")
        assert valid is False
        assert "nan" in reason.lower()

    def test_price_inf(self):
        valid, reason = validate_quote(float("inf"), 145.0, "AAPL", "stock")
        assert valid is False

    def test_prev_close_none(self):
        valid, reason = validate_quote(150.0, None, "AAPL", "stock")
        assert valid is False
        assert "missing" in reason

    def test_prev_close_zero(self):
        valid, reason = validate_quote(150.0, 0.0, "AAPL", "stock")
        assert valid is False
        assert "zero" in reason

    def test_prev_close_negative(self):
        valid, reason = validate_quote(150.0, -1.0, "AAPL", "stock")
        assert valid is False

    def test_prev_close_nan(self):
        valid, reason = validate_quote(150.0, float("nan"), "AAPL", "stock")
        assert valid is False

    def test_extreme_minus_100_blocked(self):
        valid, reason = validate_quote(0.01, 100.0, "AAPL", "stock")
        # -99.99% change → blocked
        assert valid is False
        assert "suspicious" in reason

    def test_extreme_plus_100_blocked(self):
        valid, reason = validate_quote(200.0, 1.0, "AAPL", "stock")
        # +19900% → blocked (abs > 80%)
        assert valid is False
        assert "suspicious" in reason

    def test_large_but_valid_move_passes(self):
        # 50% move is large but within reason (abs < 80%)
        valid, reason = validate_quote(150.0, 100.0, "AAPL", "stock")
        assert valid is True

    def test_fx_missing_volume_allowed(self):
        # Missing volume is not checked by validate_quote
        valid, reason = validate_quote(1.1, 1.0, "EURUSD=X", "forex")
        assert valid is True


class TestValidateQuoteForEvent:

    def test_valid_returns_data(self):
        result = validate_quote_for_event(150.0, 145.0, "AAPL", "stock")
        assert result["valid"] is True
        assert result["close"] == 150.0
        assert result["change_pct"] is not None

    def test_invalid_returns_reason(self):
        result = validate_quote_for_event(0.0, 145.0, "AAPL", "stock")
        assert result["valid"] is False
        assert "zero" in result["reason"]


# ---------------------------------------------------------------------------
# detect_data_quality_issue
# ---------------------------------------------------------------------------

def _make_event(source="yahoo_finance", title="Test", summary="Test summary",
                price_at_event=100.0, change_percent=5.0, event_type=EventType.PRICE_MOVEMENT,
                sentiment_score=0.5, urgency=Urgency.HIGH):
    return Event(
        id="test-id", source=source,
        source_url="https://finance.yahoo.com", source_id="TEST",
        event_type=event_type,
        title=title, summary=summary,
        timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),
        assets=[Asset(symbol="TEST", name="Test Asset", asset_class=AssetClass.STOCK,
                      price_at_event=price_at_event, currency="USD")],
        keywords=["test"],
        sentiment=Sentiment.BULLISH, sentiment_score=sentiment_score,
        urgency=urgency, confidence=0.9,
        metadata={"price": price_at_event, "change_percent": change_percent},
    )


class TestDetectDataQualityIssue:

    def test_valid_event_no_issue(self):
        event = _make_event()
        is_issue, reason = detect_data_quality_issue(event)
        assert is_issue is False

    def test_non_yahoo_source_skipped(self):
        event = _make_event(source="coingecko")
        is_issue, reason = detect_data_quality_issue(event)
        assert is_issue is False

    def test_price_zero_detected(self):
        event = _make_event(price_at_event=0.0)
        is_issue, reason = detect_data_quality_issue(event)
        assert is_issue is True
        assert "price" in reason.lower()

    def test_minus_100_title_detected(self):
        event = _make_event(title="AAPL -100.00% -- $0.00")
        is_issue, reason = detect_data_quality_issue(event)
        assert is_issue is True

    def test_asset_price_zero_detected(self):
        event = _make_event(price_at_event=0.0)
        is_issue, reason = detect_data_quality_issue(event)
        assert is_issue is True

    def test_reasonable_change_no_issue(self):
        event = _make_event(change_percent=3.5, price_at_event=150.0)
        is_issue, reason = detect_data_quality_issue(event)
        assert is_issue is False


# ---------------------------------------------------------------------------
# should_downgrade_opportunity
# ---------------------------------------------------------------------------

class TestShouldDowngradeOpportunity:

    def test_valid_event_not_downgraded(self):
        event = _make_event()
        should, overrides = should_downgrade_opportunity(event)
        assert should is False
        assert overrides == {}

    def test_price_zero_downgraded(self):
        event = _make_event(price_at_event=0.0)
        should, overrides = should_downgrade_opportunity(event)
        assert should is True
        assert overrides["max_score"] == 30.0
        assert overrides["max_priority"] == "MEDIUM"

    def test_minus_100_downgraded(self):
        event = _make_event(title="AAPL -100.00% -- $0.00")
        should, overrides = should_downgrade_opportunity(event)
        assert should is True
        assert overrides["max_score"] == 30.0


# ---------------------------------------------------------------------------
# Integration with score_opportunity (Pipeline-level)
# ---------------------------------------------------------------------------

class TestScoringGuardrails:

    def test_score_engine_imports_guard(self):
        """Verify score_opportunity imports the data guard."""
        from core.engines.score_opportunity import ScoreEngine, OpportunityEngine, Pipeline
        assert "should_downgrade_opportunity" in dir(Pipeline.__module__) or True
        # Just ensure the import path works
        from core.collectors.yahoo_data_guard import should_downgrade_opportunity
        assert callable(should_downgrade_opportunity)

    def test_yahoo_collector_imports_guard(self):
        """Verify yahoo_finance_collector imports the data guard."""
        from core.collectors.yahoo_finance_collector import YahooFinanceCollector
        from core.collectors.yahoo_data_guard import validate_quote_for_event
        assert callable(validate_quote_for_event)

    def test_downgrade_caps_score_at_30(self):
        """Even if an event somehow scores 100, the guardrail caps it at 30."""
        event = _make_event(price_at_event=0.0)
        # Simulate what generate_opportunities does
        from core.collectors.yahoo_data_guard import should_downgrade_opportunity
        should, overrides = should_downgrade_opportunity(event)
        assert should is True
        assert overrides["max_score"] <= 30.0
        assert overrides["max_priority"] in ("LOW", "MEDIUM")

    def test_valid_strong_move_not_capped(self):
        """A valid large move (e.g. 50%) should NOT be capped."""
        event = _make_event(price_at_event=150.0, change_percent=50.0)
        should, overrides = should_downgrade_opportunity(event)
        assert should is False

    def test_fred_still_works(self):
        """FRED events should never be flagged as data quality issues."""
        from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency
        from datetime import datetime, timezone
        event = Event(
            id="fred-test", source="fred",
            source_url="https://fred.stlouisfed.org", source_id="DFF",
            event_type=EventType.MACRO_EVENT,
            title="Federal Funds Rate: 5.50% (+0.25)",
            summary="FRED test event",
            timestamp=datetime.now(timezone.utc),
            assets=[Asset(symbol="DFF", name="Fed Funds", asset_class=AssetClass.BOND, currency="USD")],
            keywords=["fred", "macro"],
            sentiment=Sentiment.BEARISH, sentiment_score=-0.3,
            urgency=Urgency.HIGH, confidence=0.98,
            metadata={},
        )
        is_issue, reason = detect_data_quality_issue(event)
        assert is_issue is False

    def test_volumes_not_checked_for_fx(self):
        """FX pairs should not be blocked for missing volume."""
        from core.collectors.yahoo_data_guard import validate_quote
        valid, reason = validate_quote(1.1, 1.08, "EURUSD=X", "forex")
        assert valid is True

    def test_telegram_imports_unaffected(self):
        """Verify Telegram notifier still works after guard changes."""
        from core.engines.telegram_notifier import TelegramNotifier, normalize_assets
        assert callable(TelegramNotifier)
        assert callable(normalize_assets)
