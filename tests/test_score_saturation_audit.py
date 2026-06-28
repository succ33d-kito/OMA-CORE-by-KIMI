"""Tests for score saturation audit script."""
import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from scripts.audit_score_saturation import (
    query_opportunities,
    query_events,
    parse_assets,
    compute_priority_distribution,
    compute_score_distribution,
    detect_asset_anomalies,
    compute_source_breakdown,
    compute_type_breakdown,
    detect_suspicious_patterns,
    build_hypotheses,
    run_audit,
    print_terminal_report,
    save_reports,
)


def _make_db(opps, events=None):
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY, source TEXT, source_url TEXT, source_id TEXT,
            event_type TEXT, category TEXT, title TEXT, summary TEXT,
            raw_content TEXT, timestamp TEXT, detected_at TEXT, assets TEXT,
            keywords TEXT, entities TEXT, regions TEXT, sentiment TEXT,
            sentiment_score REAL, urgency TEXT, confidence REAL,
            impact_score REAL, relevance_score REAL, language TEXT,
            metadata TEXT, processed INTEGER, enriched INTEGER
        )
    """)
    for opp in opps:
        conn.execute(
            "INSERT INTO opportunities (id, event_id, title, description, opportunity_type, "
            "asset_class, assets, score, conviction, priority, action_suggested, risk_level, "
            "timestamp, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                opp.get("id", "test"), opp.get("event_id", "evt1"),
                opp.get("title", "Test"), opp.get("description", ""),
                opp.get("opportunity_type", "LONG_SETUP"),
                opp.get("asset_class", "crypto"),
                json.dumps(opp.get("assets", [])),
                opp.get("score", 50.0), opp.get("conviction", 50.0),
                opp.get("priority", "MEDIUM"), opp.get("action_suggested", "watch"),
                opp.get("risk_level", "medium"), opp.get("timestamp", "now"),
                opp.get("status", "active"),
            )
        )
    if events:
        for ev in events:
            conn.execute(
                "INSERT INTO events (id, source, event_type, title, timestamp) VALUES (?, ?, ?, ?, ?)",
                (ev.get("id"), ev.get("source"), ev.get("event_type"),
                 ev.get("title"), ev.get("timestamp"))
            )
    conn.commit()
    conn.close()
    return path


class TestQueryFunctions:

    def test_query_empty_db(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "empty.db")
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id TEXT PRIMARY KEY, event_id TEXT, title TEXT, description TEXT,
                    opportunity_type TEXT, asset_class TEXT, assets TEXT, score REAL,
                    conviction REAL, priority TEXT, action_suggested TEXT, risk_level TEXT,
                    timestamp TEXT, expires_at TEXT, status TEXT
                )
            """)
            conn.commit()
            conn.close()
            opps = query_opportunities(db_path)
            assert opps == []

    def test_query_one_opportunity(self):
        path = _make_db([{"id": "o1", "score": 95.0, "priority": "CRITICAL", "assets": ["BTC"]}])
        opps = query_opportunities(path)
        assert len(opps) == 1
        assert opps[0]["score"] == 95.0
        os.unlink(path)

    def test_query_missing_db(self):
        opps = query_opportunities("/nonexistent/db.sqlite")
        assert opps == []


class TestParseAssets:

    def test_none(self):
        assert parse_assets(None) == []

    def test_list(self):
        assert parse_assets(["BTC", "ETH"]) == ["BTC", "ETH"]

    def test_json_string(self):
        assert parse_assets('["BTC", "ETH"]') == ["BTC", "ETH"]

    def test_plain_string(self):
        assert parse_assets("BTC") == ["BTC"]


class TestPriorityDistribution:

    def test_all_critical(self):
        opps = [{"priority": "CRITICAL"}] * 10
        result = compute_priority_distribution(opps)
        assert result["total"] == 10
        assert result["counts"]["CRITICAL"] == 10
        assert result["critical_percentage"] == 100.0
        assert result["saturated"] is True

    def test_mixed_no_saturation(self):
        opps = [{"priority": "CRITICAL"}] * 3 + [{"priority": "HIGH"}] * 2
        result = compute_priority_distribution(opps)
        assert result["critical_percentage"] == 60.0
        assert result["saturated"] is False

    def test_empty(self):
        result = compute_priority_distribution([])
        assert result["total"] == 0
        assert result["critical_percentage"] == 0


class TestScoreDistribution:

    def test_all_same_score(self):
        opps = [{"score": 100}] * 5
        result = compute_score_distribution(opps)
        assert result["min"] == 100
        assert result["max"] == 100
        assert result["mean"] == 100
        assert result["at_100"] == 5
        assert result["pct_at_100"] == 100.0

    def test_varied_scores(self):
        opps = [{"score": i * 10} for i in range(1, 11)]
        result = compute_score_distribution(opps)
        assert result["min"] == 10
        assert result["max"] == 100
        assert result["mean"] == 55.0
        assert result["at_100"] == 1

    def test_empty(self):
        result = compute_score_distribution([])
        assert result["count"] == 0

    def test_repeated_scores(self):
        opps = [{"score": 90}] * 3 + [{"score": 50}] * 2 + [{"score": 100}]
        result = compute_score_distribution(opps)
        assert "90" in result.get("repeated_scores", {})
        assert "50" in result.get("repeated_scores", {})


class TestAssetAnomalies:

    def test_price_zero_detected(self):
        opps = [{"description": "Price $0.00 for BTC", "assets": '["BTC"]'}]
        anomalies = detect_asset_anomalies(opps)
        assert anomalies["price_zero"] >= 1

    def test_negative_100_detected(self):
        opps = [{"description": "Return -100.00% for ETH", "assets": '["ETH"]'}]
        anomalies = detect_asset_anomalies(opps)
        assert anomalies["pct_negative_100"] >= 1

    def test_malformed_assets_detected(self):
        opps = [{"assets": '["B", "T", "C"]', "description": "test"}]
        anomalies = detect_asset_anomalies(opps)
        assert anomalies["malformed_assets"] >= 1

    def test_no_anomalies(self):
        opps = [{"description": "Normal trade", "assets": '["BTC"]'}]
        anomalies = detect_asset_anomalies(opps)
        assert anomalies["price_zero"] == 0


class TestSourceBreakdown:

    def test_sources_counted(self):
        events = [
            {"source": "yahoo_finance", "id": "1", "event_type": "price", "title": "t1", "timestamp": "now"},
            {"source": "yahoo_finance", "id": "2", "event_type": "price", "title": "t2", "timestamp": "now"},
            {"source": "coingecko", "id": "3", "event_type": "price", "title": "t3", "timestamp": "now"},
        ]
        result = compute_source_breakdown(events)
        assert result["yahoo_finance"] == 2
        assert result["coingecko"] == 1


class TestTypeBreakdown:

    def test_types_counted(self):
        opps = [
            {"opportunity_type": "LONG_SETUP"},
            {"opportunity_type": "SHORT_SETUP"},
            {"opportunity_type": "LONG_SETUP"},
        ]
        result = compute_type_breakdown(opps)
        assert result["LONG_SETUP"] == 2
        assert result["SHORT_SETUP"] == 1


class TestSuspiciousPatterns:

    def test_score_100_and_price_zero(self):
        opps = [{"id": "o1", "score": 100, "description": "Price $0.00 for BTC", "title": "Bad"}]
        patterns = detect_suspicious_patterns(opps)
        assert any(p["pattern"] == "score_100_plus_price_zero" for p in patterns)

    def test_negative_100_detected(self):
        opps = [{"id": "o2", "score": 95, "description": "Return -100.00%", "title": "Crash"}]
        patterns = detect_suspicious_patterns(opps)
        assert any(p["pattern"] == "negative_100_percent" for p in patterns)


class TestBuildHypotheses:

    def test_price_zero_hypothesis(self):
        anomalies = {"price_zero": 5, "pct_negative_100": 0, "missing_price": 0,
                     "missing_return": 0, "malformed_assets": 0, "asset_examples": []}
        priority = {"saturated": False, "critical_percentage": 30, "total": 10, "counts": {}}
        scores = {"pct_at_100": 5, "at_100": 0}
        h = build_hypotheses(anomalies, priority, scores, {}, [])
        assert any("Missing price" in h for h in h)

    def test_saturation_hypothesis(self):
        anomalies = {"price_zero": 0, "pct_negative_100": 0, "missing_price": 0,
                     "missing_return": 0, "malformed_assets": 0, "asset_examples": []}
        priority = {"saturated": True, "critical_percentage": 95, "total": 100, "counts": {}}
        scores = {"pct_at_100": 10, "at_100": 10}
        h = build_hypotheses(anomalies, priority, scores, {}, [])
        assert any("saturation" in h.lower() for h in h)


class TestSaveReports:

    def test_save_json_and_md(self):
        result = {
            "timestamp": "2026-01-01T00:00:00",
            "database": "test.db",
            "total_opportunities": 5,
            "total_events": 3,
            "priority_distribution": {"total": 5, "counts": {"CRITICAL": 3, "HIGH": 2},
                                       "critical_percentage": 60.0, "saturated": False},
            "score_distribution": {"count": 5, "min": 50, "max": 100, "mean": 80,
                                    "median": 85, "at_100": 1, "pct_at_100": 20,
                                    "repeated_scores": {}},
            "asset_anomalies": {"price_zero": 0, "pct_negative_100": 0, "missing_price": 0,
                                 "missing_return": 0, "malformed_assets": 0, "asset_examples": []},
            "source_breakdown": {"yahoo": 2, "fred": 1},
            "type_breakdown": {"LONG_SETUP": 3, "SHORT_SETUP": 2},
            "suspicious_patterns": [],
            "hypotheses": ["No significant anomalies detected."],
        }
        with tempfile.TemporaryDirectory() as td:
            orig = Path("_project-memory")
            try:
                os.environ["REPORT_DIR"] = td
                # Monkey-patch REPORT_DIR
                import scripts.audit_score_saturation as mod
                old_dir = mod.REPORT_DIR
                mod.REPORT_DIR = Path(td)
                mod.save_reports(result)
                files = list(Path(td).iterdir())
                json_files = [f for f in files if f.suffix == ".json"]
                md_files = [f for f in files if f.suffix == ".md"]
                assert len(json_files) >= 1
                assert len(md_files) >= 1
                mod.REPORT_DIR = old_dir
            finally:
                pass

    def test_terminal_report_does_not_crash(self):
        result = {
            "timestamp": "2026-01-01T00:00:00",
            "database": "test.db",
            "total_opportunities": 0,
            "total_events": 0,
            "priority_distribution": {"total": 0, "counts": {}, "critical_percentage": 0, "saturated": False},
            "score_distribution": {"count": 0, "min": None, "max": None, "mean": None,
                                    "median": None, "at_100": 0, "pct_at_100": 0,
                                    "repeated_scores": {}, "conviction_mean": None},
            "asset_anomalies": {"price_zero": 0, "pct_negative_100": 0, "missing_price": 0,
                                 "missing_return": 0, "malformed_assets": 0, "asset_examples": []},
            "source_breakdown": {},
            "type_breakdown": {},
            "suspicious_patterns": [],
            "hypotheses": ["No data to analyze."],
        }
        import io
        import sys
        captured = io.StringIO()
        old = sys.stdout
        sys.stdout = captured
        try:
            print_terminal_report(result)
        finally:
            sys.stdout = old
        output = captured.getvalue()
        assert "Score Saturation Audit Report" in output


class TestRunAudit:

    def test_run_audit_with_real_db(self):
        path = _make_db(
            [{"id": "o1", "score": 100, "priority": "CRITICAL", "assets": ["BTC"],
              "opportunity_type": "LONG_SETUP", "description": "Great trade"},
             {"id": "o2", "score": 50, "priority": "MEDIUM", "assets": ["ETH"],
              "opportunity_type": "WATCHLIST_ADD", "description": "Watch ETH"}],
            [{"id": "e1", "source": "yahoo_finance", "event_type": "price", "title": "t1", "timestamp": "now"}],
        )
        result = run_audit(path)
        assert result["total_opportunities"] == 2
        assert result["total_events"] == 1
        assert result["priority_distribution"]["counts"]["CRITICAL"] == 1
        assert result["score_distribution"]["max"] == 100
        os.unlink(path)

    def test_run_audit_empty_db(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "empty.db")
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id TEXT PRIMARY KEY, event_id TEXT, title TEXT, description TEXT,
                    opportunity_type TEXT, asset_class TEXT, assets TEXT, score REAL,
                    conviction REAL, priority TEXT, action_suggested TEXT, risk_level TEXT,
                    timestamp TEXT, expires_at TEXT, status TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY, source TEXT, source_url TEXT, source_id TEXT,
                    event_type TEXT, category TEXT, title TEXT, summary TEXT,
                    raw_content TEXT, timestamp TEXT, detected_at TEXT, assets TEXT,
                    keywords TEXT, entities TEXT, regions TEXT, sentiment TEXT,
                    sentiment_score REAL, urgency TEXT, confidence REAL,
                    impact_score REAL, relevance_score REAL, language TEXT,
                    metadata TEXT, processed INTEGER, enriched INTEGER
                )
            """)
            conn.commit()
            conn.close()
            result = run_audit(db_path)
            assert result["total_opportunities"] == 0
            assert result["total_events"] == 0
