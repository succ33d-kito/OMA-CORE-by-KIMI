"""Tests for audit_conviction.py"""
import io
import json
import os
import sqlite3
import sys
import tempfile

import pytest

from scripts.audit_conviction import (
    audit_conviction,
    print_report,
    spearman_rank_correlation,
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


class TestSpearmanCorrelation:

    def test_perfect_correlation(self):
        assert spearman_rank_correlation([1, 2, 3], [10, 20, 30]) == 1.0

    def test_no_correlation(self):
        # With n < 3, returns 0.0
        pass

    def test_negative_correlation(self):
        n = 5
        xs = [1, 2, 3, 4, 5]
        ys = [5, 4, 3, 2, 1]
        corr = spearman_rank_correlation(xs, ys)
        assert corr == -1.0

    def test_small_sample(self):
        corr = spearman_rank_correlation([1, 2], [10, 20])
        assert corr == 0.0

    def test_no_variance(self):
        corr = spearman_rank_correlation([5, 5, 5], [10, 10, 10])
        assert corr == 0.0


class TestAuditConviction:

    def test_empty_db(self):
        path = _make_db([])
        result = audit_conviction(path)
        assert "error" in result
        os.unlink(path)

    def test_single_opportunity(self):
        path = _make_db([
            {"id": "o1", "score": 75.0, "conviction": 80.0, "priority": "HIGH",
             "opportunity_type": "WATCHLIST_ADD", "risk_level": "medium"},
        ])
        result = audit_conviction(path)
        assert result["total_opportunities"] == 1
        assert result["conviction_distribution"]["mean"] == 80.0
        assert result["conviction_distribution"]["unique_values"] == 1
        os.unlink(path)

    def test_varied_convictions(self):
        path = _make_db([
            {"id": "o1", "score": 90, "conviction": 80, "priority": "CRITICAL",
             "opportunity_type": "SHORT_SETUP", "risk_level": "high"},
            {"id": "o2", "score": 70, "conviction": 60, "priority": "HIGH",
             "opportunity_type": "WATCHLIST_ADD", "risk_level": "medium"},
            {"id": "o3", "score": 50, "conviction": 40, "priority": "MEDIUM",
             "opportunity_type": "NEWS_DRIVEN", "risk_level": "medium"},
            {"id": "o4", "score": 50, "conviction": 55, "priority": "MEDIUM",
             "opportunity_type": "NEWS_DRIVEN", "risk_level": "low"},
        ])
        result = audit_conviction(path)
        assert result["total_opportunities"] == 4
        assert result["conviction_distribution"]["mean"] == 58.75
        assert result["score_conviction_correlation"] is not None
        assert len(result["conviction_by_priority"]) == 3
        assert len(result["conviction_by_type"]) == 3
        os.unlink(path)

    def test_missing_db(self):
        result = audit_conviction("/nonexistent/db.sqlite")
        assert "error" in result

    def test_static_type_detected(self):
        path = _make_db([
            {"id": f"o{i}", "score": 95, "conviction": 84.0, "priority": "CRITICAL",
             "opportunity_type": "SHORT_SETUP", "risk_level": "high"}
            for i in range(5)
        ])
        result = audit_conviction(path)
        static = result.get("static_conviction_types", {})
        assert "SHORT_SETUP" in static
        assert static["SHORT_SETUP"]["unique_conviction_values"] == 1
        os.unlink(path)


class TestPrintReport:

    def test_does_not_crash(self):
        result = {
            "database": "test.db",
            "total_opportunities": 3,
            "conviction_distribution": {
                "mean": 60.0, "median": 60.0, "min": 40, "max": 80,
                "histogram": {"40-50": 1, "50-60": 1, "60-70": 0, "70-80": 1},
                "unique_values": 3, "total_values": 3, "value_repeat_ratio": 100.0,
                "most_repeated_values": {},
            },
            "score_conviction_correlation": 0.5,
            "conviction_by_priority": {"MEDIUM": {"mean": 50, "min": 40, "max": 60, "count": 2}},
            "conviction_by_type": {"SHORT_SETUP": {"mean": 80, "min": 80, "max": 80, "count": 1}},
            "conviction_by_risk": {"medium": {"mean": 60, "min": 40, "max": 80, "count": 3}},
            "static_conviction_types": {},
        }
        captured = io.StringIO()
        old = sys.stdout
        sys.stdout = captured
        try:
            print_report(result)
        finally:
            sys.stdout = old
        output = captured.getvalue()
        assert "Conviction Audit" in output
