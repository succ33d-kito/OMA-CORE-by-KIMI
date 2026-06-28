"""Tests for audit_pipeline_backlog.py"""
import io
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone, timedelta

import pytest

from scripts.audit_pipeline_backlog import (
    audit_backlog,
    print_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(events=None, opps=None):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY, source TEXT, event_type TEXT, title TEXT,
            summary TEXT, timestamp TEXT, processed INTEGER DEFAULT 0,
            source_id TEXT, urgency INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY, event_id TEXT, title TEXT, description TEXT,
            opportunity_type TEXT, score REAL, conviction REAL, priority TEXT,
            timestamp TEXT, status TEXT DEFAULT 'active'
        )
    """)
    if events:
        for i, ev in enumerate(events):
            conn.execute(
                "INSERT INTO events (id, source, event_type, title, timestamp, processed, source_id, urgency) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ev.get("id", f"e{i}"),
                    ev.get("source", "test"),
                    ev.get("event_type", "news"),
                    ev.get("title", "Test event"),
                    ev.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    ev.get("processed", 0),
                    ev.get("source_id", f"sid{i}"),
                    ev.get("urgency", 2),
                )
            )
    if opps:
        for i, opp in enumerate(opps):
            conn.execute(
                "INSERT INTO opportunities (id, event_id, title, opportunity_type, score, conviction, priority, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    opp.get("id", f"opp{i}"),
                    opp.get("event_id", f"e{i}"),
                    opp.get("title", "Test opp"),
                    opp.get("opportunity_type", "WATCHLIST_ADD"),
                    opp.get("score", 50.0),
                    opp.get("conviction", 50.0),
                    opp.get("priority", "MEDIUM"),
                    opp.get("timestamp", datetime.now(timezone.utc).isoformat()),
                )
            )
    conn.commit()
    conn.close()
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAuditBacklog:

    def test_empty_db(self):
        path = _make_db()
        result = audit_backlog(path)
        assert result["total_events"] == 0
        assert result["processed_events"] == 0
        assert result["unprocessed_events"] == 0
        os.unlink(path)

    def test_basic_counts(self):
        now = datetime.now(timezone.utc)
        events = [
            {"id": "e1", "source": "yahoo_finance", "processed": 1, "timestamp": now.isoformat()},
            {"id": "e2", "source": "rss_cnbc", "processed": 0, "timestamp": now.isoformat()},
            {"id": "e3", "source": "coingecko", "processed": 0, "timestamp": now.isoformat()},
        ]
        path = _make_db(events=events)
        result = audit_backlog(path)
        assert result["total_events"] == 3
        assert result["processed_events"] == 1
        assert result["unprocessed_events"] == 2
        assert result["backlog_pct"] == 66.7
        os.unlink(path)

    def test_duplicate_detection(self):
        now = datetime.now(timezone.utc)
        events = [
            {"id": "e1", "source": "yahoo_finance", "source_id": "dup1", "processed": 1, "timestamp": now.isoformat()},
            {"id": "e2", "source": "yahoo_finance", "source_id": "dup1", "processed": 0, "timestamp": now.isoformat()},
            {"id": "e3", "source": "rss_cnbc", "source_id": "unique", "processed": 0, "timestamp": now.isoformat()},
        ]
        path = _make_db(events=events)
        result = audit_backlog(path)
        assert result["duplicate_events"] == 1
        os.unlink(path)

    def test_expired_events(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        fresh = (datetime.now(timezone.utc)).isoformat()
        events = [
            {"id": "e1", "source": "test", "processed": 0, "timestamp": old},
            {"id": "e2", "source": "test", "processed": 0, "timestamp": fresh},
            {"id": "e3", "source": "test", "processed": 1, "timestamp": old},
        ]
        path = _make_db(events=events)
        result = audit_backlog(path)
        assert result["expired_events_unprocessed"] == 1
        os.unlink(path)

    def test_events_by_source(self):
        now = datetime.now(timezone.utc).isoformat()
        events = [
            {"id": "e1", "source": "yahoo_finance", "timestamp": now},
            {"id": "e2", "source": "yahoo_finance", "timestamp": now},
            {"id": "e3", "source": "coingecko", "timestamp": now},
        ]
        path = _make_db(events=events)
        result = audit_backlog(path)
        assert result["events_by_source"]["yahoo_finance"] == 2
        assert result["events_by_source"]["coingecko"] == 1
        os.unlink(path)

    def test_missing_db(self):
        result = audit_backlog("/nonexistent/db.sqlite")
        assert "error" in result


class TestPrintReport:

    def test_does_not_crash(self):
        result = {
            "database": "test.db",
            "timestamp": "2026-01-01T00:00:00",
            "total_events": 100,
            "processed_events": 30,
            "unprocessed_events": 70,
            "backlog_pct": 70.0,
            "first_event_timestamp": "2026-01-01",
            "last_event_timestamp": "2026-06-01",
            "events_per_day": 30.0,
            "events_last_7_days": 50,
            "collection_rate_per_day": 7.1,
            "events_by_source": {"yahoo": 50, "fred": 30},
            "unprocessed_by_source": {"yahoo": 40},
            "events_by_urgency": {1: 30, 2: 30, 3: 20, 4: 20},
            "events_by_type": {"news": 60, "price_movement": 40},
            "pipeline_metrics": {
                "typical_batch_size": 200,
                "opportunities_per_run": 35,
                "recent_runs_opp_counts": [31, 32],
                "estimated_runs_per_day": 4,
            },
            "backlog_clearance": {
                "runs_needed": 2,
                "hours_to_clear_at_current_rate": 12,
                "estimated_clear_by": "2026-06-02T00:00:00",
            },
            "duplicate_events": 5,
            "expired_events_unprocessed": 10,
            "opportunities_total": 63,
        }
        captured = io.StringIO()
        old = sys.stdout
        sys.stdout = captured
        try:
            print_report(result)
        finally:
            sys.stdout = old
        output = captured.getvalue()
        assert "Pipeline Backlog Audit" in output
