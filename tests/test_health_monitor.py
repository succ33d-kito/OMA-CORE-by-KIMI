"""Tests for the HealthMonitor — no live API dependencies."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from core.monitoring.health import HealthMonitor, HealthStatus, CheckResult


class TestHealthMonitorBasics:
    def test_process_alive(self):
        h = HealthMonitor()
        r = h.check_process_alive()
        assert r.status == HealthStatus.HEALTHY
        assert r.check_name == "process_alive"

    def test_equity_sanity_healthy(self):
        h = HealthMonitor()
        r = h.check_equity_sanity(15000.0, 10000.0)
        assert r.status == HealthStatus.HEALTHY

    def test_equity_sanity_non_positive(self):
        h = HealthMonitor()
        r = h.check_equity_sanity(0.0, 10000.0)
        assert r.status == HealthStatus.CRITICAL

    def test_equity_sanity_negative(self):
        h = HealthMonitor()
        r = h.check_equity_sanity(-500.0, 10000.0)
        assert r.status == HealthStatus.CRITICAL

    def test_equity_sanity_too_high(self):
        h = HealthMonitor()
        r = h.check_equity_sanity(200000.0, 10000.0)
        assert r.status == HealthStatus.CRITICAL

    def test_equity_sanity_ten_x_boundary(self):
        """Exactly 10x should still be CRITICAL (exceeds 10x)."""
        h = HealthMonitor()
        r = h.check_equity_sanity(100001.0, 10000.0)
        assert r.status == HealthStatus.CRITICAL


class TestHealthGuardModes:
    def test_guard_normal(self):
        h = HealthMonitor()
        r = h.check_capital_guard_mode("NORMAL")
        assert r.status == HealthStatus.HEALTHY

    def test_guard_caution(self):
        h = HealthMonitor()
        r = h.check_capital_guard_mode("CAUTION")
        assert r.status == HealthStatus.DEGRADED

    def test_guard_emergency(self):
        h = HealthMonitor()
        r = h.check_capital_guard_mode("EMERGENCY")
        assert r.status == HealthStatus.CRITICAL

    def test_guard_halt(self):
        h = HealthMonitor()
        r = h.check_capital_guard_mode("HALT")
        assert r.status == HealthStatus.CRITICAL

    def test_crash_none(self):
        h = HealthMonitor()
        r = h.check_crash_mode("NONE")
        assert r.status == HealthStatus.HEALTHY

    def test_crash_warning(self):
        h = HealthMonitor()
        r = h.check_crash_mode("WARNING")
        assert r.status == HealthStatus.DEGRADED

    def test_crash_emergency(self):
        h = HealthMonitor()
        r = h.check_crash_mode("EMERGENCY")
        assert r.status == HealthStatus.CRITICAL

    def test_crash_panic(self):
        h = HealthMonitor()
        r = h.check_crash_mode("PANIC")
        assert r.status == HealthStatus.CRITICAL


class TestHealthOpenPositions:
    def test_no_positions(self):
        h = HealthMonitor()
        r = h.check_open_positions([])
        assert r.status == HealthStatus.HEALTHY

    def test_fresh_position(self):
        h = HealthMonitor()
        trade = FakeTrade()
        r = h.check_open_positions([trade], max_holding_hours=72)
        assert r.status == HealthStatus.HEALTHY

    def test_stale_position(self):
        h = HealthMonitor()
        trade = FakeTrade()
        trade.entry_time = datetime.now(timezone.utc) - timedelta(hours=100)
        r = h.check_open_positions([trade], max_holding_hours=72)
        assert r.status == HealthStatus.CRITICAL
        assert r.details["stale_positions"][0]["age_hours"] > 72

    def test_mixed_positions(self):
        h = HealthMonitor()
        fresh = FakeTrade()
        stale = FakeTrade()
        stale.entry_time = datetime.now(timezone.utc) - timedelta(hours=200)
        r = h.check_open_positions([fresh, stale], max_holding_hours=48)
        assert r.status == HealthStatus.CRITICAL


class TestHealthPositionSizes:
    def test_all_positive(self):
        h = HealthMonitor()
        trades = [FakeTrade(size=1.5), FakeTrade(size=0.5)]
        r = h.check_negative_position_sizes(trades)
        assert r.status == HealthStatus.HEALTHY

    def test_negative_size(self):
        h = HealthMonitor()
        trades = [FakeTrade(size=-0.5)]
        r = h.check_negative_position_sizes(trades)
        assert r.status == HealthStatus.CRITICAL


class TestHealthTradeConsistency:
    def test_consistent_trades(self):
        h = HealthMonitor()
        trade = FakeTrade()
        trade.status = "CLOSED"
        trade.pnl_absolute = 100.0
        trade.entry_price_executed = 50000.0
        r = h.check_trade_consistency([trade])
        assert r.status == HealthStatus.HEALTHY

    def test_closed_trade_missing_pnl(self):
        h = HealthMonitor()
        trade = FakeTrade()
        trade.status = "CLOSED"
        trade.pnl_absolute = None
        r = h.check_trade_consistency([trade])
        assert r.status == HealthStatus.CRITICAL

    def test_open_trade_missing_entry_price(self):
        h = HealthMonitor()
        trade = FakeTrade()
        trade.status = "OPEN"
        trade.entry_price_executed = None
        r = h.check_trade_consistency([trade])
        assert r.status == HealthStatus.CRITICAL


class TestHealthCycleDiversity:
    def test_few_cycles_no_check(self):
        h = HealthMonitor()
        tel = [{"events_collected": 1, "signals_generated": 1}]
        r = h.check_repeated_cycles(tel, threshold=5)
        assert r.status == HealthStatus.HEALTHY

    def test_diverse_cycles(self):
        h = HealthMonitor()
        tel = [
            {"events_collected": 3, "signals_generated": 1},
            {"events_collected": 3, "signals_generated": 1},
            {"events_collected": 2, "signals_generated": 0},
            {"events_collected": 3, "signals_generated": 1},
            {"events_collected": 4, "signals_generated": 2},
        ]
        r = h.check_repeated_cycles(tel, threshold=3)
        assert r.status == HealthStatus.HEALTHY

    def test_repeated_identical_cycles(self):
        h = HealthMonitor()
        tel = [
            {"events_collected": 2, "signals_generated": 1},
            {"events_collected": 2, "signals_generated": 1},
            {"events_collected": 2, "signals_generated": 1},
        ]
        r = h.check_repeated_cycles(tel, threshold=3)
        assert r.status == HealthStatus.DEGRADED


class TestHealthExcessiveSkips:
    def test_no_skips(self):
        h = HealthMonitor()
        tel = [{"events_processed": 3, "runtime_errors": 0}]
        r = h.check_excessive_skips(tel, max_skips=5)
        assert r.status == HealthStatus.HEALTHY

    def test_few_skips_under_limit(self):
        h = HealthMonitor()
        tel = [{"events_processed": 0, "runtime_errors": 1}] * 3
        r = h.check_excessive_skips(tel, max_skips=5)
        assert r.status == HealthStatus.DEGRADED

    def test_many_skips_exceeds_limit(self):
        h = HealthMonitor()
        tel = [{"events_processed": 0, "runtime_errors": 1}] * 10
        r = h.check_excessive_skips(tel, max_skips=5)
        assert r.status == HealthStatus.CRITICAL


class TestHealthOverallStatus:
    def test_all_healthy(self):
        h = HealthMonitor()
        results = [
            CheckResult("a", HealthStatus.HEALTHY, "ok"),
            CheckResult("b", HealthStatus.HEALTHY, "ok"),
        ]
        assert h.overall_status(results) == HealthStatus.HEALTHY

    def test_one_degraded(self):
        h = HealthMonitor()
        results = [
            CheckResult("a", HealthStatus.HEALTHY, "ok"),
            CheckResult("b", HealthStatus.DEGRADED, "warn"),
        ]
        assert h.overall_status(results) == HealthStatus.DEGRADED

    def test_one_critical(self):
        h = HealthMonitor()
        results = [
            CheckResult("a", HealthStatus.HEALTHY, "ok"),
            CheckResult("b", HealthStatus.CRITICAL, "fail"),
        ]
        assert h.overall_status(results) == HealthStatus.CRITICAL

    def test_mixed_critical_wins(self):
        h = HealthMonitor()
        results = [
            CheckResult("a", HealthStatus.DEGRADED, "warn"),
            CheckResult("b", HealthStatus.CRITICAL, "fail"),
            CheckResult("c", HealthStatus.HEALTHY, "ok"),
        ]
        assert h.overall_status(results) == HealthStatus.CRITICAL


class TestHealthRegisterComponent:
    def test_register_and_run_all(self):
        h = HealthMonitor()
        h.register_component("test", {"name": "test"})
        assert "test" in h._checks


class FakeTrade:
    """Minimal trade mock for health checks."""
    def __init__(self, size: float = 1.0):
        self.id = "test_trade"
        self.status = "OPEN"
        self.size = size
        self.entry_time = datetime.now(timezone.utc)
        self.entry_price_executed = 50000.0
        self.exit_price = None
        self.pnl_absolute = None
        self.pnl_percent = None
