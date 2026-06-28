"""Tests for cleanup_pre_guard_artifacts.py"""
import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from scripts.cleanup_pre_guard_artifacts import (
    identify_artifacts,
    compute_summary,
    build_sql_preview,
    perform_delete,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OPPORTUNITY_SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY, event_id TEXT, title TEXT, description TEXT,
    opportunity_type TEXT, asset_class TEXT, assets TEXT, score REAL,
    conviction REAL, priority TEXT, action_suggested TEXT, risk_level TEXT,
    timestamp TEXT, expires_at TEXT, status TEXT DEFAULT 'active'
)
"""


def _make_db(opps):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute(OPPORTUNITY_SCHEMA)
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
                opp.get("timestamp", "2026-06-27T00:00:00"),
                opp.get("status", "active"),
            )
        )
    conn.commit()
    conn.close()
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIdentifyArtifacts:

    def test_empty_db(self):
        path = _make_db([])
        arts = identify_artifacts(path)
        assert arts == []
        os.unlink(path)

    def test_no_artifacts(self):
        path = _make_db([
            {"id": "o1", "score": 75.0, "priority": "HIGH", "description": "Normal trade +5%"},
        ])
        arts = identify_artifacts(path)
        assert len(arts) == 0
        os.unlink(path)

    def test_score_100_identified(self):
        path = _make_db([
            {"id": "o1", "score": 100.0, "priority": "CRITICAL", "description": "AAPL price movement"},
        ])
        arts = identify_artifacts(path)
        assert len(arts) == 1
        assert arts[0]["score"] == 100.0
        os.unlink(path)

    def test_minus_100_in_description(self):
        path = _make_db([
            {"id": "o2", "score": 100.0, "description": "Return -100.00% for AAPL"},
        ])
        arts = identify_artifacts(path)
        assert len(arts) == 1
        os.unlink(path)

    def test_price_zero_in_description(self):
        path = _make_db([
            {"id": "o3", "score": 100.0, "description": "Price $0.00 for BTC"},
        ])
        arts = identify_artifacts(path)
        assert len(arts) == 1
        os.unlink(path)

    def test_data_quality_title(self):
        path = _make_db([
            {"id": "o4", "title": "[DATA_QUALITY] AAPL $0.00", "description": "Bad data"},
        ])
        arts = identify_artifacts(path)
        assert len(arts) == 1
        os.unlink(path)

    def test_mixed_db(self):
        path = _make_db([
            {"id": "o1", "score": 100.0, "priority": "CRITICAL", "description": "-100.00%"},
            {"id": "o2", "score": 75.0, "priority": "HIGH", "description": "Normal +3%"},
            {"id": "o3", "score": 50.0, "priority": "MEDIUM", "description": "Watchlist item"},
            {"id": "o4", "score": 100.0, "priority": "CRITICAL", "description": "Price $0.00"},
        ])
        arts = identify_artifacts(path)
        assert len(arts) == 2
        os.unlink(path)

    def test_missing_db(self):
        arts = identify_artifacts("/nonexistent/db.sqlite")
        assert arts == []


class TestComputeSummary:

    def test_basic_summary(self):
        artifacts = [
            {"score": 100, "description": "AAPL -100.00% -- $0.00", "title": "", "priority": "CRITICAL", "opportunity_type": "SHORT_SETUP", "timestamp": "2026-06-27"},
            {"score": 100, "description": "Return -100.00%", "title": "", "priority": "CRITICAL", "opportunity_type": "SHORT_SETUP", "timestamp": "2026-06-27"},
        ]
        s = compute_summary(artifacts)
        assert s["total_artifacts"] == 2
        assert s["score_100_count"] == 2
        assert s["negative_100_count"] == 2
        assert s["price_zero_count"] == 1

    def test_empty(self):
        s = compute_summary([])
        assert s["total_artifacts"] == 0


class TestBuildSQLPreview:

    def test_contains_keywords(self):
        preview = build_sql_preview("test.db")
        assert "DELETE FROM opportunities" in preview
        assert "BEGIN TRANSACTION" in preview
        assert "COMMIT" in preview
        assert "--execute" in preview


class TestPerformDelete:

    def test_deletes_artifacts(self):
        path = _make_db([
            {"id": "o1", "score": 100.0, "description": "Bad -100%"},
            {"id": "o2", "score": 75.0, "description": "Good"},
            {"id": "o3", "score": 100.0, "description": "Price $0.00"},
        ])
        deleted = perform_delete(path)
        assert deleted == 2

        conn = sqlite3.connect(path)
        remaining = conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
        conn.close()
        assert remaining == 1
        os.unlink(path)

    def test_no_artifacts(self):
        path = _make_db([
            {"id": "o1", "score": 75.0, "description": "Normal"},
        ])
        deleted = perform_delete(path)
        assert deleted == 0

        conn = sqlite3.connect(path)
        remaining = conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
        conn.close()
        assert remaining == 1
        os.unlink(path)
