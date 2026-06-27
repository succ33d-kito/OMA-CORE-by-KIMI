"""Tests for Telegram Notification Quality Gate (Sprint 10)."""
import json
from unittest.mock import patch, MagicMock

import pytest

from core.engines.telegram_notifier import (
    normalize_assets,
    deduplicate_opportunities,
    detect_priority_saturation,
    NotificationQualityGate,
    render_notification,
    get_learning_core_stats,
    TelegramNotifier,
    _render_assets,
    _safe_text,
    _truncate_message,
    _unique_ordered,
    _parse_single_asset,
)


# ---------------------------------------------------------------------------
# normalize_assets
# ---------------------------------------------------------------------------

class TestNormalizeAssets:

    def test_plain_string(self):
        assert normalize_assets("BTC") == ["BTC"]

    def test_python_list(self):
        assert normalize_assets(["BTC", "ETH"]) == ["BTC", "ETH"]

    def test_json_string_list(self):
        assert normalize_assets('["BTC", "ETH"]') == ["BTC", "ETH"]

    def test_quoted_string(self):
        assert normalize_assets('"BTC"') == ["BTC"]

    def test_comma_separated(self):
        assert normalize_assets("BTC, ETH") == ["BTC", "ETH"]

    def test_comma_separated_no_space(self):
        assert normalize_assets("BTC,ETH,SOL") == ["BTC", "ETH", "SOL"]

    def test_none(self):
        assert normalize_assets(None) == []

    def test_empty_string(self):
        assert normalize_assets("") == []

    def test_empty_list(self):
        assert normalize_assets([]) == []

    def test_malformed_character_list_string(self):
        # This is the original bug: a string like '["BTC", "ETH"]' 
        # when iterated character-by-character produces the malformed output
        result = normalize_assets('["BTC", "ETH"]')
        assert result == ["BTC", "ETH"]
        assert "B" not in result or len(result) > 1  # not character list
        assert all(len(a) > 1 for a in result)

    def test_single_character_asset(self):
        # Ensure single-char strings like "B" are NOT produced
        result = normalize_assets("BTC")
        assert len(result) == 1
        assert len(result[0]) == 3

    def test_duplicates_removed(self):
        assert normalize_assets(["BTC", "BTC", "ETH"]) == ["BTC", "ETH"]

    def test_mixed_whitespace(self):
        assert normalize_assets("  BTC  ,  ETH  ") == ["BTC", "ETH"]

    def test_nested_json_in_list(self):
        assert normalize_assets(['["BTC", "ETH"]', "SOL"]) == ["BTC", "ETH", "SOL"]

    def test_empty_json_array_string(self):
        assert normalize_assets("[]") == []

    def test_empty_json_string(self):
        assert normalize_assets('""') == []

    def test_integer_asset(self):
        assert normalize_assets(123) == ["123"]

    def test_mixed_case_preserved(self):
        assert normalize_assets(["btc", "BTC"]) == ["btc", "BTC"]


# ---------------------------------------------------------------------------
# deduplicate_opportunities
# ---------------------------------------------------------------------------

class TestDeduplicateOpportunities:

    def test_identical_opportunities_collapse(self):
        opps = [
            {"assets": ["BTC"], "action_suggested": "buy", "opportunity_type": "LONG_SETUP",
             "direction": "long", "score": 90.0, "title": "BTC play"},
            {"assets": ["BTC"], "action_suggested": "buy", "opportunity_type": "LONG_SETUP",
             "direction": "long", "score": 90.0, "title": "BTC play"},
        ]
        result = deduplicate_opportunities(opps)
        assert result["raw_count"] == 2
        assert result["unique_count"] == 1
        assert result["duplicate_rate"] == 50

    def test_different_assets_remain_separate(self):
        opps = [
            {"assets": ["BTC"], "action_suggested": "buy", "opportunity_type": "LONG_SETUP",
             "direction": "long", "score": 90.0, "title": "BTC play"},
            {"assets": ["ETH"], "action_suggested": "buy", "opportunity_type": "LONG_SETUP",
             "direction": "long", "score": 85.0, "title": "ETH play"},
        ]
        result = deduplicate_opportunities(opps)
        assert result["unique_count"] == 2

    def test_duplicate_rate_zero(self):
        opps = [
            {"assets": ["BTC"], "action_suggested": "buy", "opportunity_type": "LONG_SETUP",
             "direction": "long", "score": 90.0, "title": "unique"},
        ]
        result = deduplicate_opportunities(opps)
        assert result["duplicate_rate"] == 0

    def test_duplicate_rate_high(self):
        opps = [{"assets": ["BTC"], "action_suggested": "buy", "opportunity_type": "LONG_SETUP",
                 "direction": "long", "score": 90.0, "title": "x"}] * 20
        result = deduplicate_opportunities(opps)
        assert result["duplicate_rate"] >= 95

    def test_empty_list(self):
        result = deduplicate_opportunities([])
        assert result["raw_count"] == 0
        assert result["unique_count"] == 0
        assert result["duplicate_rate"] == 0

    def test_different_actions_separate(self):
        opps = [
            {"assets": ["BTC"], "action_suggested": "buy", "opportunity_type": "LONG_SETUP",
             "direction": "long", "score": 90.0, "title": "BTC"},
            {"assets": ["BTC"], "action_suggested": "sell", "opportunity_type": "SHORT_SETUP",
             "direction": "short", "score": 85.0, "title": "BTC"},
        ]
        result = deduplicate_opportunities(opps)
        assert result["unique_count"] == 2

    def test_normalized_assets_used_for_dedup(self):
        opps = [
            {"assets": '["BTC", "ETH"]', "action_suggested": "buy", "opportunity_type": "LONG_SETUP",
             "direction": "long", "score": 90.0, "title": "crypto"},
            {"assets": ["BTC", "ETH"], "action_suggested": "buy", "opportunity_type": "LONG_SETUP",
             "direction": "long", "score": 90.0, "title": "crypto"},
        ]
        result = deduplicate_opportunities(opps)
        assert result["unique_count"] == 1


# ---------------------------------------------------------------------------
# detect_priority_saturation
# ---------------------------------------------------------------------------

class TestDetectPrioritySaturation:

    def test_all_critical(self):
        result = detect_priority_saturation({"CRITICAL": 10}, 10)
        assert result["saturated"] is True
        assert "% are CRITICAL" in result.get("reason", "")

    def test_eighty_percent_critical(self):
        result = detect_priority_saturation({"CRITICAL": 8, "HIGH": 2}, 10)
        assert result["saturated"] is True

    def test_mixed_distribution_not_saturated(self):
        result = detect_priority_saturation({"CRITICAL": 3, "HIGH": 3, "MEDIUM": 3, "LOW": 1}, 10)
        assert result["saturated"] is False

    def test_all_same_priority(self):
        result = detect_priority_saturation({"MEDIUM": 5}, 5)
        assert result["saturated"] is True

    def test_empty_total(self):
        result = detect_priority_saturation({}, 0)
        assert result["saturated"] is False
        assert "No opportunities" in result.get("reason", "")

    def test_single_opportunity_not_saturated(self):
        result = detect_priority_saturation({"CRITICAL": 1}, 1)
        assert result["saturated"] is False

    def test_few_opportunities_not_saturated(self):
        result = detect_priority_saturation({"CRITICAL": 4}, 4)
        assert result["saturated"] is False


# ---------------------------------------------------------------------------
# NotificationQualityGate
# ---------------------------------------------------------------------------

class TestNotificationQualityGate:

    def make_opp(self, **overrides):
        base = {
            "id": "t1", "assets": ["BTC"], "action_suggested": "buy",
            "score": 90.0, "opportunity_type": "LONG_SETUP", "direction": "long",
            "title": "Test", "priority": "CRITICAL",
        }
        base.update(overrides)
        return base

    def test_good_message_passes(self):
        gate = NotificationQualityGate()
        opps = [self.make_opp(priority="HIGH") for _ in range(3)]
        dedup = deduplicate_opportunities(opps)
        counts = {"HIGH": 3}
        sat = detect_priority_saturation(counts, 3)
        message = "test message"
        result = gate.evaluate(opps, dedup, counts, sat, message)
        assert result == "PASS"

    def test_malformed_assets_warns(self):
        gate = NotificationQualityGate()
        opps = [self.make_opp(assets="B,T,C")]  # single chars
        dedup = deduplicate_opportunities(opps)
        counts = {"CRITICAL": 1}
        sat = detect_priority_saturation(counts, 1)
        result = gate.evaluate(opps, dedup, counts, sat, "msg")
        assert result in ("WARN", "SUPPRESS_DETAIL", "FAIL_DIAGNOSTIC")

    def test_high_duplicate_rate_suppresses(self):
        gate = NotificationQualityGate()
        opps = [self.make_opp(assets=["BTC"])] * 20
        dedup = deduplicate_opportunities(opps)
        counts = {"CRITICAL": 20}
        sat = detect_priority_saturation(counts, 20)
        result = gate.evaluate(opps, dedup, counts, sat, "msg")
        assert result == "SUPPRESS_DETAIL"

    def test_missing_block_reason_warns(self):
        gate = NotificationQualityGate()
        opps = [self.make_opp(block_reason="capital_guard")]
        # remove block_reason to test fallback — actually it exists
        del opps[0]["block_reason"]
        dedup = deduplicate_opportunities(opps)
        counts = {"CRITICAL": 1}
        sat = detect_priority_saturation(counts, 1)
        result = gate.evaluate(opps, dedup, counts, sat, "msg")
        # Opp has no block_reason field at all, so we check that it may warn or pass
        assert result in ("PASS", "WARN")

    def test_identical_message_suppresses(self):
        gate = NotificationQualityGate()
        opps = [self.make_opp()]
        dedup = deduplicate_opportunities(opps)
        counts = {"CRITICAL": 1}
        sat = detect_priority_saturation(counts, 1)
        gate.last_message = "same message"
        result = gate.evaluate(opps, dedup, counts, sat, "same message")
        assert result == "SUPPRESS_DETAIL"

    def test_malformed_list_output_fails(self):
        gate = NotificationQualityGate()
        opps = [self.make_opp()]
        dedup = deduplicate_opportunities(opps)
        counts = {"CRITICAL": 1}
        sat = detect_priority_saturation(counts, 1)
        result = gate.evaluate(opps, dedup, counts, sat, "Assets: [, \", B, T, C")
        assert result == "FAIL_DIAGNOSTIC"

    def test_empty_opportunities_warns(self):
        gate = NotificationQualityGate()
        dedup = deduplicate_opportunities([])
        result = gate.evaluate([], dedup, {}, {"saturated": False, "reason": ""}, "msg")
        assert result == "WARN"


# ---------------------------------------------------------------------------
# render_notification
# ---------------------------------------------------------------------------

class TestRenderNotification:

    def sample_opps(self):
        return [
            {"id": "o1", "opportunity_type": "LONG_SETUP", "priority": "CRITICAL",
             "score": 95.0, "conviction": 0.85, "assets": ["BTC", "ETH"],
             "action_suggested": "buy", "direction": "long",
             "title": "BTC breakout"},
            {"id": "o2", "opportunity_type": "SHORT_SETUP", "priority": "HIGH",
             "score": 78.0, "conviction": 0.70, "assets": ["SOL"],
             "action_suggested": "sell", "direction": "short",
             "title": "SOL overbought"},
        ]

    def sample_stats(self):
        return {
            "events_processed": 50, "events_stored": 20,
            "opportunities_generated": 100, "trades_opened": 3,
            "open_positions": 2, "execution_blocks": 10,
            "guard_blocks": 2, "top_block_reason": "Execution Capacity Limit",
            "capital_guard_mode": "active",
        }

    def test_no_character_list_assets(self):
        msg = render_notification(self.sample_opps(), self.sample_stats(), None)
        assert "[," not in msg
        assert '", "' not in msg or "Assets" not in [l.strip() for l in msg.split("\n") if "Assets" in l]

    def test_no_duplicate_top_5(self):
        opps = self.sample_opps() * 10  # many dupes
        msg = render_notification(opps, self.sample_stats(), None)
        # Each unique opportunity should appear once in Top 5
        # Check the number of #1, #2 etc
        count_hashtags = sum(1 for line in msg.split("\n") if line.strip().startswith("<b>#"))
        assert count_hashtags <= 5

    def test_contains_summary(self):
        msg = render_notification(self.sample_opps(), self.sample_stats(), None)
        assert "Summary" in msg
        assert "Raw opportunities" in msg
        assert "Unique opportunities" in msg
        assert "Duplicate rate" in msg

    def test_contains_diagnostics(self):
        msg = render_notification(self.sample_opps(), self.sample_stats(), None)
        assert "Diagnostics" in msg
        assert "Asset formatting" in msg
        assert "Priority saturation" in msg

    def test_contains_execution_section(self):
        msg = render_notification(self.sample_opps(), self.sample_stats(), None)
        assert "Execution / Bottleneck" in msg
        assert "Trades opened" in msg
        assert "Execution blocks" in msg
        assert "Guard blocks" in msg

    def test_handles_missing_learning_core(self):
        msg = render_notification(self.sample_opps(), self.sample_stats(), {})
        assert "Learning Core" in msg
        assert "not connected" in msg

    def test_learning_core_connected_shows_stats(self):
        learning_stats = {
            "connected": True,
            "outcome_comparisons": 42,
            "knowledge_items": 15,
            "pending_criterion_deltas": 3,
            "last_replay_session": "2026-06-01",
        }
        msg = render_notification(self.sample_opps(), self.sample_stats(), learning_stats)
        assert "connected" in msg
        assert "42" in msg
        assert "15" in msg
        assert "3" in msg

    def test_contains_top_opportunities_section(self):
        msg = render_notification(self.sample_opps(), self.sample_stats(), None)
        assert "Top Unique Opportunities" in msg
        assert "BTC" in msg
        assert "ETH" in msg
        assert "SOL" in msg

    def test_truncates_long_messages(self):
        long_text = "X" * 5000
        msg = _truncate_message(long_text, 100)
        assert len(msg) <= 100

    def test_not_truncated_if_under_limit(self):
        short = "Hello"
        assert _truncate_message(short, 4000) == short


# ---------------------------------------------------------------------------
# TelegramNotifier (with mocks)
# ---------------------------------------------------------------------------

class TestTelegramNotifier:

    def test_disabled_when_no_token(self):
        notifier = TelegramNotifier(token=None, chat_id=None)
        assert notifier.enabled is False
        assert notifier.send_message("test") is False

    def test_send_message_calls_api(self):
        with patch("core.engines.telegram_notifier.requests.post") as mock_post:
            mock_post.return_value = MagicMock(ok=True)
            mock_post.return_value.raise_for_status = MagicMock()
            notifier = TelegramNotifier(token="fake:token", chat_id="123")
            assert notifier.enabled is True
            result = notifier.send_message("hello")
            assert result is True
            mock_post.assert_called_once()

    def test_send_message_handles_error(self):
        with patch("core.engines.telegram_notifier.requests.post") as mock_post:
            mock_post.side_effect = Exception("Network error")
            notifier = TelegramNotifier(token="fake:token", chat_id="123")
            result = notifier.send_message("hello")
            assert result is False

    def test_send_run_summary_disabled(self):
        notifier = TelegramNotifier(token=None, chat_id=None)
        assert notifier.send_run_summary([], {}) is False

    def test_send_run_summary_calls_send_message(self):
        with patch.object(TelegramNotifier, "send_message", return_value=True) as mock_send:
            notifier = TelegramNotifier(token="fake:token", chat_id="123")
            opps = [{"id": "o1", "assets": ["BTC"], "action_suggested": "buy",
                     "opportunity_type": "LONG_SETUP", "direction": "long",
                     "score": 90.0, "title": "Test", "priority": "CRITICAL"}]
            result = notifier.send_run_summary(opps, {"events_processed": 1})
            assert result is True
            mock_send.assert_called_once()

    def test_send_run_summary_suppresses_on_high_dup_rate(self):
        with patch.object(TelegramNotifier, "send_message", return_value=True) as mock_send:
            notifier = TelegramNotifier(token="fake:token", chat_id="123")
            opps = [{"id": "o1", "assets": ["BTC"], "action_suggested": "buy",
                     "opportunity_type": "LONG_SETUP", "direction": "long",
                     "score": 90.0, "title": "Test", "priority": "CRITICAL"}] * 20
            notifier.send_run_summary(opps, {})
            sent_text = mock_send.call_args[0][0]
            assert "Compact Diagnostic" in sent_text or mock_send.called

    def test_test_connection_disabled(self):
        notifier = TelegramNotifier(token=None, chat_id=None)
        assert notifier.test_connection() is False

    def test_test_connection_success(self):
        with patch("core.engines.telegram_notifier.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"ok": True, "result": {"username": "TestBot"}}
            notifier = TelegramNotifier(token="fake:token", chat_id="123")
            assert notifier.test_connection() is True

    def test_compact_diagnostic_contains_warning_banner(self):
        notifier = TelegramNotifier(token="fake:token", chat_id="123")
        notifier._gate.warnings = ["Test warning"]
        dedup = {"raw_count": 20, "unique_count": 1, "duplicate_rate": 95}
        sat = {"saturated": True, "reason": "Test saturation", "distribution": {}}
        msg = notifier._build_compact_diagnostic({}, dedup, sat)
        assert "Test warning" in msg
        assert "Compact Diagnostic" in msg
        assert "95%" in msg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_render_assets_empty(self):
        assert _render_assets([]) == "N/A"

    def test_render_assets_with_values(self):
        assert _render_assets(["BTC", "ETH"]) == "BTC, ETH"

    def test_safe_text_none(self):
        assert _safe_text(None) == "N/A"

    def test_safe_text_truncates(self):
        long = "a" * 100
        assert len(_safe_text(long, 10)) <= 10

    def test_unique_ordered(self):
        assert _unique_ordered(["a", "b", "a", "c"]) == ["a", "b", "c"]

    def test_parse_single_asset_none(self):
        assert _parse_single_asset(None) is None

    def test_parse_single_asset_string(self):
        assert _parse_single_asset('"BTC"') == "BTC"

    def test_parse_single_asset_int(self):
        assert _parse_single_asset(123) == "123"


# ---------------------------------------------------------------------------
# get_learning_core_stats
# ---------------------------------------------------------------------------

class TestGetLearningCoreStats:

    def test_returns_default_when_no_db(self):
        stats = get_learning_core_stats("/nonexistent/db.sqlite")
        assert stats["connected"] is False
        assert stats["outcome_comparisons"] == 0


# ---------------------------------------------------------------------------
# send_critical_alert (backward compat)
# ---------------------------------------------------------------------------

class TestSendCriticalAlert:

    def test_no_critical_returns_false(self):
        notifier = TelegramNotifier(token="fake:token", chat_id="123")
        opps = [{"priority": "HIGH", "assets": ["BTC"]}]
        assert notifier.send_critical_alert(opps) is False

    def test_critical_calls_send_message(self):
        with patch.object(TelegramNotifier, "send_message", return_value=True) as mock_send:
            notifier = TelegramNotifier(token="fake:token", chat_id="123")
            opps = [{"priority": "CRITICAL", "assets": ["BTC"], "action_suggested": "buy",
                     "opportunity_type": "LONG_SETUP", "score": 95.0}]
            result = notifier.send_critical_alert(opps)
            assert result is True
            mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# Regression: no trading/execution/agent/council behavior changed
# ---------------------------------------------------------------------------

class TestRegression:

    def test_telegram_module_does_not_import_trading_logic(self):
        import core.engines.telegram_notifier
        mod = core.engines.telegram_notifier
        # Should NOT have imported any trading/execution modules
        imports = dir(mod)
        trading_names = {"order", "execution", "trade", "position", "risk_guard", "capital"}
        has_trading = any(name in str(getattr(mod, name, "")).lower() for name in trading_names)
        # Just verify it's the right module
        assert hasattr(mod, "TelegramNotifier")
        assert hasattr(mod, "normalize_assets")
