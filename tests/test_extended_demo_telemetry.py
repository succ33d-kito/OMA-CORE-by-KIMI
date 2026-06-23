"""Tests for TelemetryRecorder and GuardAuditRecorder — no live API dependencies."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from core.monitoring.telemetry import TelemetryRecorder, GuardAuditRecorder


class TestTelemetryRecorder:
    def test_record_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            tr.record({"cycle_id": 1, "events": 5, "signals": 2})

            all_e = tr.read_all()
            assert len(all_e) == 1
            assert all_e[0]["cycle_id"] == 1
            assert all_e[0]["events"] == 5

    def test_multiple_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            for i in range(5):
                tr.record({"cycle_id": i, "events": i * 2})
            all_e = tr.read_all()
            assert len(all_e) == 5
            assert all_e[-1]["cycle_id"] == 4

    def test_append_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            tr.record({"cycle_id": 1, "data": "first"})
            tr.record({"cycle_id": 2, "data": "second"})
            all_e = tr.read_all()
            assert len(all_e) == 2
            assert all_e[0]["data"] == "first"
            assert all_e[1]["data"] == "second"

    def test_read_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            for i in range(20):
                tr.record({"cycle_id": i})
            recent = tr.read_recent(5)
            assert len(recent) == 5
            assert recent[0]["cycle_id"] == 15
            assert recent[-1]["cycle_id"] == 19

    def test_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            tr.record({
                "cycle_id": 1, "events_collected": 3, "signals_generated": 1,
                "trades_opened": 1, "trades_closed": 0, "runtime_errors": 0,
                "guard_blocks": 0, "execution_blocks": 0,
            })
            tr.record({
                "cycle_id": 2, "events_collected": 5, "signals_generated": 2,
                "trades_opened": 1, "trades_closed": 1, "runtime_errors": 1,
                "guard_blocks": 1, "execution_blocks": 0,
            })
            s = tr.summary()
            assert s["total_cycles"] == 2
            assert s["total_events"] == 8
            assert s["total_signals"] == 3
            assert s["total_errors"] == 1
            assert s["total_guard_blocks"] == 1

    def test_summary_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            s = tr.summary()
            assert s == {}

    def test_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr1 = TelemetryRecorder(tmp)
            tr1.record({"cycle_id": 1})
            # Force new file by changing internal state
            tr1._file = None
            tr1.record({"cycle_id": 2})
            all_e = tr1.read_all()
            assert len(all_e) == 2


class TestGuardAuditRecorder:
    def test_record_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            ga = GuardAuditRecorder(tmp)
            ga.record({
                "asset": "BTC", "direction": "LONG",
                "block_reason": "crash_mode_panic",
                "guard_source": "CrashDetector",
            })
            all_e = ga.read_all()
            assert len(all_e) == 1
            assert all_e[0]["asset"] == "BTC"
            assert all_e[0]["block_reason"] == "crash_mode_panic"

    def test_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            ga = GuardAuditRecorder(tmp)
            ga.record({"asset": "BTC", "block_reason": "crash_block", "guard_source": "CrashDetector",
                        "original_size": 1.0, "adjusted_size": 0.0})
            ga.record({"asset": "ETH", "block_reason": "size_reduction", "guard_source": "CapitalGuard",
                        "original_size": 1.0, "adjusted_size": 0.5})
            s = ga.summary()
            assert s["total_interventions"] == 2
            assert s["total_blocked"] == 1
            # Both records have original > adjusted, so both count as size reductions
            assert s["total_size_reductions"] == 2

    def test_summary_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            ga = GuardAuditRecorder(tmp)
            s = ga.summary()
            assert s == {}

    def test_append_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            ga = GuardAuditRecorder(tmp)
            ga.record({"asset": "BTC", "block_reason": "test"})
            with open(ga.filepath) as f:
                content = f.read()
            lines = content.strip().split("\n")
            assert len(lines) == 1
            parsed = json.loads(lines[0])
            assert parsed["asset"] == "BTC"


class TestTelemetryDoesNotDependOnLive:
    """Verify all monitoring code works without live APIs or trading logic."""

    def test_recorder_no_live_deps(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            tr.record({"cycle_id": 1, "events": 0, "signals": 0})
            assert tr.read_all()[0]["cycle_id"] == 1

    def test_guard_recorder_no_live_deps(self):
        with tempfile.TemporaryDirectory() as tmp:
            ga = GuardAuditRecorder(tmp)
            ga.record({"asset": "TEST", "block_reason": "test"})
            assert ga.read_all()[0]["asset"] == "TEST"

    def test_filepath_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            path = tr.filepath
            assert "telemetry" in str(path)
            assert path.suffix == ".jsonl"

    def test_guard_filepath_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            ga = GuardAuditRecorder(tmp)
            path = ga.filepath
            assert "guard_audit" in str(path)
            assert path.suffix == ".jsonl"
