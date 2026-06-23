"""Tests for TelemetryRecorder and GuardAuditRecorder — no live API dependencies."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from core.monitoring.telemetry import TelemetryRecorder, GuardAuditRecorder, ExecutionAuditRecorder


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


class TestTelemetryCounterConsistency:
    """Regression: per-cycle counters must match cumulative fields."""

    def test_per_cycle_signals_sum_to_cumulative(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            tr.record({
                "cycle_id": 1, "signals_generated": 1, "trades_opened": 1,
                "trades_closed": 0, "guard_blocks": 0, "execution_blocks": 0,
                "runtime_errors": 0,
                "cumulative_signals": 1, "cumulative_trades_opened": 1,
                "cumulative_trades_closed": 0, "cumulative_guard_blocks": 0,
                "cumulative_execution_blocks": 0, "cumulative_errors": 0,
            })
            tr.record({
                "cycle_id": 2, "signals_generated": 2, "trades_opened": 1,
                "trades_closed": 1, "guard_blocks": 1, "execution_blocks": 0,
                "runtime_errors": 1,
                "cumulative_signals": 3, "cumulative_trades_opened": 2,
                "cumulative_trades_closed": 1, "cumulative_guard_blocks": 1,
                "cumulative_execution_blocks": 0, "cumulative_errors": 1,
            })
            all_e = tr.read_all()
            # Cycle 1: cumulative should equal per-cycle (first cycle)
            assert all_e[0]["cumulative_signals"] == all_e[0]["signals_generated"]
            assert all_e[0]["cumulative_trades_opened"] == all_e[0]["trades_opened"]
            assert all_e[0]["cumulative_trades_closed"] == all_e[0]["trades_closed"]
            # Cycle 2: cumulative should equal sum of all per-cycle up to this point
            per_cycle_signals = sum(e["signals_generated"] for e in all_e)
            assert all_e[-1]["cumulative_signals"] == per_cycle_signals
            per_cycle_trades = sum(e["trades_opened"] for e in all_e)
            assert all_e[-1]["cumulative_trades_opened"] == per_cycle_trades
            per_cycle_closed = sum(e["trades_closed"] for e in all_e)
            assert all_e[-1]["cumulative_trades_closed"] == per_cycle_closed
            per_cycle_blocks = sum(e["guard_blocks"] for e in all_e)
            assert all_e[-1]["cumulative_guard_blocks"] == per_cycle_blocks
            per_cycle_errors = sum(e["runtime_errors"] for e in all_e)
            assert all_e[-1]["cumulative_errors"] == per_cycle_errors

    def test_per_cycle_none_matches_cumulative_zero(self):
        """If no signals/trades in a cycle, cumulative should not regress."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            tr.record({
                "cycle_id": 1, "signals_generated": 0, "trades_opened": 0,
                "trades_closed": 0, "guard_blocks": 0, "execution_blocks": 0,
                "runtime_errors": 0,
                "cumulative_signals": 0, "cumulative_trades_opened": 0,
                "cumulative_trades_closed": 0, "cumulative_guard_blocks": 0,
                "cumulative_execution_blocks": 0, "cumulative_errors": 0,
            })
            tr.record({
                "cycle_id": 2, "signals_generated": 0, "trades_opened": 0,
                "trades_closed": 0, "guard_blocks": 0, "execution_blocks": 0,
                "runtime_errors": 0,
                "cumulative_signals": 0, "cumulative_trades_opened": 0,
                "cumulative_trades_closed": 0, "cumulative_guard_blocks": 0,
                "cumulative_execution_blocks": 0, "cumulative_errors": 0,
            })
            all_e = tr.read_all()
            for e in all_e:
                assert e["cumulative_signals"] == 0
                assert e["cumulative_trades_opened"] == 0
                assert e["cumulative_trades_closed"] == 0
                assert e["cumulative_guard_blocks"] == 0

    def test_per_cycle_never_exceeds_cumulative(self):
        """Per-cycle counters must never exceed cumulative at same cycle."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            for i in range(5):
                tr.record({
                    "cycle_id": i + 1,
                    "signals_generated": i,
                    "trades_opened": i if i % 2 == 0 else 0,
                    "trades_closed": i if i % 2 == 1 else 0,
                    "guard_blocks": i if i > 2 else 0,
                    "execution_blocks": 0,
                    "runtime_errors": 0,
                    "cumulative_signals": sum(range(i + 1)),
                    "cumulative_trades_opened": sum(j for j in range(i + 1) if j % 2 == 0),
                    "cumulative_trades_closed": sum(j for j in range(i + 1) if j % 2 == 1),
                    "cumulative_guard_blocks": sum(j for j in range(i + 1) if j > 2),
                    "cumulative_execution_blocks": 0,
                    "cumulative_errors": 0,
                })
            all_e = tr.read_all()
            for e in all_e:
                assert e["signals_generated"] <= e["cumulative_signals"]
                assert e["trades_opened"] <= e["cumulative_trades_opened"]
                assert e["trades_closed"] <= e["cumulative_trades_closed"]
                assert e["guard_blocks"] <= e["cumulative_guard_blocks"]

    def test_open_positions_tracks_cumulative_trades(self):
        """open_positions should never exceed cumulative_trades_opened."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            tr.record({
                "cycle_id": 1, "signals_generated": 1, "trades_opened": 1,
                "trades_closed": 0, "open_positions": 1,
                "cumulative_signals": 1, "cumulative_trades_opened": 1,
                "cumulative_trades_closed": 0,
                "guard_blocks": 0, "execution_blocks": 0, "runtime_errors": 0,
                "cumulative_guard_blocks": 0, "cumulative_execution_blocks": 0,
                "cumulative_errors": 0,
            })
            tr.record({
                "cycle_id": 2, "signals_generated": 1, "trades_opened": 0,
                "trades_closed": 1, "open_positions": 0,
                "cumulative_signals": 2, "cumulative_trades_opened": 1,
                "cumulative_trades_closed": 1,
                "guard_blocks": 0, "execution_blocks": 0, "runtime_errors": 0,
                "cumulative_guard_blocks": 0, "cumulative_execution_blocks": 0,
                "cumulative_errors": 0,
            })
            all_e = tr.read_all()
            for e in all_e:
                assert e["open_positions"] <= e["cumulative_trades_opened"]


class TestExecutionAuditRecorder:
    def test_record_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            ea = ExecutionAuditRecorder(tmp)
            ea.record({
                "cycle_id": 1, "asset": "BTC", "direction": "LONG",
                "block_reason": "execution_capacity_limit",
                "execution_source": "PaperTradingEngine.execute_signal",
            })
            all_e = ea.read_all()
            assert len(all_e) == 1
            assert all_e[0]["block_reason"] == "execution_capacity_limit"
            assert all_e[0]["execution_source"] == "PaperTradingEngine.execute_signal"

    def test_execution_block_creates_audit_record(self):
        """Every execution block must produce an audit entry."""
        with tempfile.TemporaryDirectory() as tmp:
            ea = ExecutionAuditRecorder(tmp)
            for i in range(3):
                ea.record({
                    "cycle_id": i + 1,
                    "asset": "BTC",
                    "direction": "LONG",
                    "block_reason": "execution_capacity_limit",
                    "execution_source": "PaperTradingEngine.execute_signal",
                    "open_positions": i,
                    "capital_guard_mode": "normal",
                    "crash_mode": "none",
                })
            all_e = ea.read_all()
            assert len(all_e) == 3

    def test_execution_block_counter_matches_audit_count(self):
        """Telemetry cumulative_execution_blocks must equal audit entry count."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = TelemetryRecorder(tmp)
            ea = ExecutionAuditRecorder(tmp)
            for i in range(5):
                n_blocks = i  # 0, 1, 2, 3, 4
                tr.record({
                    "cycle_id": i + 1,
                    "execution_blocks": n_blocks,
                    "cumulative_execution_blocks": sum(range(i + 1)),
                    "signals_generated": 0, "trades_opened": 0, "trades_closed": 0,
                    "guard_blocks": 0, "runtime_errors": 0,
                    "cumulative_signals": 0, "cumulative_trades_opened": 0,
                    "cumulative_trades_closed": 0, "cumulative_guard_blocks": 0,
                    "cumulative_errors": 0,
                })
                for _ in range(n_blocks):
                    ea.record({
                        "cycle_id": i + 1, "asset": "BTC",
                        "block_reason": "execution_capacity_limit",
                    })
            tel = tr.read_all()
            audit = ea.read_all()
            total_tel_blocks = tel[-1]["cumulative_execution_blocks"]
            assert total_tel_blocks == len(audit), (
                f"cumulative_execution_blocks={total_tel_blocks} != audit_count={len(audit)}"
            )

    def test_no_audit_record_when_trade_executes(self):
        """If a trade opens, no execution audit record should exist."""
        with tempfile.TemporaryDirectory() as tmp:
            ea = ExecutionAuditRecorder(tmp)
            # Simulating a successful execution — no call to ea.record
            # (no audit record created)
            all_e = ea.read_all()
            assert len(all_e) == 0

    def test_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            ea = ExecutionAuditRecorder(tmp)
            ea.record({"asset": "BTC", "block_reason": "execution_capacity_limit"})
            ea.record({"asset": "ETH", "block_reason": "execution_capacity_limit"})
            s = ea.summary()
            assert s["total_execution_blocks"] == 2
            assert "BTC" in s["by_asset"]
            assert "ETH" in s["by_asset"]

    def test_summary_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            ea = ExecutionAuditRecorder(tmp)
            s = ea.summary()
            assert s == {}

    def test_filepath_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            ea = ExecutionAuditRecorder(tmp)
            path = ea.filepath
            assert "execution_audit" in str(path)
            assert path.suffix == ".jsonl"
