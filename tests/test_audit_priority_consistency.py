"""Tests for audit_priority_consistency.py"""
import json
import os
import sqlite3
import tempfile
import io
import sys

import pytest

from scripts.audit_priority_consistency import (
    check_consistency,
    audit_consistency,
    print_report,
    EXPECTED_PRIORITY_RANGES,
    PRIORITY_LADDER,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(opps):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY, event_id TEXT, title TEXT, description TEXT,
            opportunity_type TEXT, asset_class TEXT, assets TEXT, score REAL,
            conviction REAL, priority TEXT, action_suggested TEXT, risk_level TEXT,
            timestamp TEXT, expires_at TEXT, status TEXT DEFAULT 'active'
        )
    """)
    for i, opp in enumerate(opps):
        conn.execute(
            "INSERT INTO opportunities (id, event_id, title, description, opportunity_type, "
            "asset_class, assets, score, conviction, priority, action_suggested, risk_level, "
            "timestamp, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                opp.get("id", f"o{i}"),
                opp.get("event_id", f"e{i}"),
                opp.get("title", "Test"),
                opp.get("description", ""),
                opp.get("opportunity_type", "WATCHLIST_ADD"),
                opp.get("asset_class", "stock"),
                json.dumps(opp.get("assets", [])),
                opp.get("score", 50.0),
                opp.get("conviction", 50.0),
                opp.get("priority", "MEDIUM"),
                opp.get("action_suggested", "watch"),
                opp.get("risk_level", "medium"),
                opp.get("timestamp", "now"),
                opp.get("status", "active"),
            )
        )
    conn.commit()
    conn.close()
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCheckConsistency:

    def test_watchlist_add_high_is_ok(self):
        result = check_consistency("WATCHLIST_ADD", "HIGH", 70, 60)
        assert result["consistent"] is True

    def test_watchlist_add_critical_is_over_priority(self):
        result = check_consistency("WATCHLIST_ADD", "CRITICAL", 80, 88)
        assert result["consistent"] is False
        assert result["severity"] == "over_priority"

    def test_short_setup_critical_is_ok(self):
        result = check_consistency("SHORT_SETUP", "CRITICAL", 95, 90)
        assert result["consistent"] is True

    def test_unknown_type(self):
        result = check_consistency("MYSTERY_TYPE", "CRITICAL", 95, 90)
        assert result["consistent"] is True
        assert result["severity"] == "info"

    def test_under_priority(self):
        result = check_consistency("AVOID_OR_SHORT", "LOW", 70, 60)
        assert result["consistent"] is False
        assert result["severity"] == "under_priority"

    def test_borderline_low(self):
        result = check_consistency("MONITOR_COMPLIANCE", "LOW", 30, 25)
        assert result["consistent"] is True


class TestAuditConsistency:

    def test_empty_db(self):
        path = _make_db([])
        result = audit_consistency(path)
        assert result["total_opportunities"] == 0
        assert result["consistency_pct"] == 100.0
        os.unlink(path)

    def test_all_consistent(self):
        path = _make_db([
            {"id": "o1", "priority": "HIGH", "opportunity_type": "WATCHLIST_ADD", "score": 70, "conviction": 65},
            {"id": "o2", "priority": "CRITICAL", "opportunity_type": "SHORT_SETUP", "score": 95, "conviction": 90},
            {"id": "o3", "priority": "MEDIUM", "opportunity_type": "MONITOR_MACRO", "score": 50, "conviction": 45},
        ])
        result = audit_consistency(path)
        assert result["total_opportunities"] == 3
        assert result["consistent"] == 3
        assert result["consistency_pct"] == 100.0
        os.unlink(path)

    def test_mixed_consistency(self):
        path = _make_db([
            # Over-priority: WATCHLIST_ADD should not be CRITICAL
            {"id": "o1", "priority": "CRITICAL", "opportunity_type": "WATCHLIST_ADD", "score": 80, "conviction": 88},
            # Normal
            {"id": "o2", "priority": "HIGH", "opportunity_type": "SHORT_SETUP", "score": 85, "conviction": 80},
        ])
        result = audit_consistency(path)
        assert result["total_opportunities"] == 2
        assert result["consistent"] == 1
        assert result["inconsistent"] == 1
        assert result["over_priority"] == 1
        os.unlink(path)

    def test_missing_db(self):
        result = audit_consistency("/nonexistent/db.sqlite")
        assert "error" in result


class TestPrintReport:

    def test_does_not_crash(self):
        result = {
            "database": "test.db",
            "total_opportunities": 3,
            "consistent": 2,
            "inconsistent": 1,
            "consistency_pct": 66.7,
            "over_priority": 1,
            "under_priority": 0,
            "over_priority_examples": [],
            "under_priority_examples": [],
            "type_consistency": {"WATCHLIST_ADD": {"count": 3, "consistent": 2, "inconsistent": 1, "pct": 66.7}},
            "type_priority_matrix": {"WATCHLIST_ADD": {"LOW": 0, "MEDIUM": 0, "HIGH": 1, "CRITICAL": 2}},
            "type_counts": {"WATCHLIST_ADD": 3},
        }
        captured = io.StringIO()
        old = sys.stdout
        sys.stdout = captured
        try:
            print_report(result)
        finally:
            sys.stdout = old
        output = captured.getvalue()
        assert "Priority Consistency Audit" in output
        assert "66.7%" in output


class TestExpectedRanges:

    def test_all_types_defined(self):
        """All OPPORTUNITY_TYPES from score_opportunity.py should have a mapping."""
        known_types = {
            "LONG_SETUP", "SHORT_SETUP", "MOMENTUM_PLAY", "AVOID_OR_SHORT",
            "REGULATORY_TAILWIND", "REGULATORY_HEADWIND", "MONITOR_COMPLIANCE",
            "SAFE_HAVEN_FLOW", "RISK_OFF", "MONITOR_GEO",
            "MACRO_TAILWIND", "MACRO_HEADWIND", "MONITOR_MACRO",
            "POST_EARNINGS_RUN", "POST_EARNINGS_DROP", "EARNINGS_NEUTRAL",
            "SENTIMENT_TURN_BULL", "SENTIMENT_TURN_BEAR", "SENTIMENT_WATCH",
            "VIRAL_MOMENTUM", "NEWS_DRIVEN",
            "TECHNICAL_BREAKOUT", "TECHNICAL_BREAKDOWN", "TECHNICAL_WATCH",
            "WHALE_ACCUMULATION", "WHALE_DISTRIBUTION", "WHALE_WATCH",
            "ARB_OPPORTUNITY", "WATCHLIST_ADD",
        }
        mapped = set(EXPECTED_PRIORITY_RANGES.keys())
        missing = known_types - mapped
        extra = mapped - known_types
        assert not missing, f"Types missing from EXPECTED_PRIORITY_RANGES: {missing}"
        assert not extra, f"Extra types in EXPECTED_PRIORITY_RANGES: {extra}"

    def test_all_priorities_valid(self):
        for t, (lo, hi) in EXPECTED_PRIORITY_RANGES.items():
            assert lo in PRIORITY_LADDER, f"{t}: invalid lower bound {lo}"
            assert hi in PRIORITY_LADDER, f"{t}: invalid upper bound {hi}"
            assert PRIORITY_LADDER.index(lo) <= PRIORITY_LADDER.index(hi), \
                f"{t}: lower bound {lo} > upper bound {hi}"
