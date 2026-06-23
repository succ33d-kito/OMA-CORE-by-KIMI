"""Test Kill Switch — Simulate catastrophic drawdown, verify HALT mode.
Tests CapitalGuard at 35%, 40%, 50% drawdown thresholds.
"""
import pytest
from core.execution.capital_guard import CapitalGuard, GuardMode


class TestKillSwitchDrawdownThresholds:
    def test_35_percent_drawdown_triggers_halt(self):
        g = CapitalGuard(initial_capital=10000.0,
                         emergency_dd_threshold=20.0,
                         halt_dd_threshold=35.0)
        g.update_equity(10000.0)  # peak = 10000
        # Simulate losses to 6500 (35% drawdown)
        g.record_trade_result(-500.0)
        g.record_trade_result(-500.0)
        g.record_trade_result(-500.0)
        g.record_trade_result(-500.0)
        g.record_trade_result(-500.0)
        g.record_trade_result(-500.0)
        g.record_trade_result(-500.0)
        current = 10000.0 + sum(g._daily_pnls.get(list(g._daily_pnls.keys())[0], []))
        current = 6500.0
        g._equity_peak = 10000.0  # ensure peak stays
        dd = g.drawdown_pct(current)
        assert dd >= 34.0, f"Drawdown should be ~35%, got {dd:.1f}%"
        assert g.guard_mode(current) == GuardMode.HALT

    def test_40_percent_drawdown_halt(self):
        g = CapitalGuard(initial_capital=10000.0,
                         emergency_dd_threshold=20.0,
                         halt_dd_threshold=35.0)
        g.update_equity(10000.0)
        current = 6000.0
        g._equity_peak = 10000.0
        dd = g.drawdown_pct(current)
        assert dd >= 39.0
        assert g.guard_mode(current) == GuardMode.HALT

    def test_50_percent_drawdown_halt(self):
        g = CapitalGuard(initial_capital=10000.0,
                         emergency_dd_threshold=20.0,
                         halt_dd_threshold=35.0)
        g.update_equity(10000.0)
        current = 5000.0
        g._equity_peak = 10000.0
        dd = g.drawdown_pct(current)
        assert dd >= 49.0
        assert g.guard_mode(current) == GuardMode.HALT


class TestKillSwitchBehavior:
    def test_halt_mode_blocks_new_positions(self):
        g = CapitalGuard(initial_capital=10000.0,
                         emergency_dd_threshold=20.0,
                         halt_dd_threshold=35.0)
        g.update_equity(10000.0)
        current = 6000.0
        g._equity_peak = 10000.0
        assert g.guard_mode(current) == GuardMode.HALT
        assert g.can_enter_new_position(current) is False
        assert g.is_trading_allowed() is True  # kill_switch_active not set, but mode is halt
        assert g.should_reduce_size(current) == 0.0

    def test_kill_switch_active_blocks_everything(self):
        g = CapitalGuard(initial_capital=10000.0)
        g.activate_kill_switch()
        assert g.guard_mode(10000) == GuardMode.HALT
        assert g.is_trading_allowed() is False
        assert g.can_enter_new_position(10000) is False
        assert g.should_reduce_size(10000) == 0.0

    def test_kill_switch_deactivation_restores_trading(self):
        g = CapitalGuard(initial_capital=10000.0)
        g.activate_kill_switch()
        assert g.is_trading_allowed() is False
        g.deactivate_kill_switch()
        assert g.is_trading_allowed() is True

    def test_emergency_before_halt(self):
        """At 25% DD, should be EMERGENCY, not HALT."""
        g = CapitalGuard(initial_capital=10000.0,
                         emergency_dd_threshold=20.0,
                         halt_dd_threshold=35.0)
        g.update_equity(10000.0)
        current = 7500.0
        g._equity_peak = 10000.0
        assert g.guard_mode(current) == GuardMode.EMERGENCY
        assert g.can_enter_new_position(current) is False
        assert g.should_reduce_size(current) == 0.25

    def test_drawdown_transitions(self):
        """Test the full progression: NORMAL → EMERGENCY → HALT."""
        g = CapitalGuard(initial_capital=10000.0,
                         emergency_dd_threshold=20.0,
                         halt_dd_threshold=35.0)
        g.update_equity(10000.0)

        # 5% DD → NORMAL
        g._equity_peak = 10000.0
        assert g.guard_mode(9500.0) == GuardMode.NORMAL

        # 25% DD → EMERGENCY
        g._equity_peak = 10000.0
        assert g.guard_mode(7500.0) == GuardMode.EMERGENCY

        # 40% DD → HALT
        g._equity_peak = 10000.0
        assert g.guard_mode(6000.0) == GuardMode.HALT


class TestKillSwitchEdgeCases:
    def test_no_false_halt_at_small_drawdown(self):
        g = CapitalGuard(initial_capital=10000.0,
                         halt_dd_threshold=35.0)
        g.update_equity(10000.0)
        assert g.guard_mode(9800.0) != GuardMode.HALT
        assert g.guard_mode(9200.0) != GuardMode.HALT
        assert g.guard_mode(8500.0) != GuardMode.HALT

    def test_recovery_after_drawdown(self):
        """After recovery above halt threshold, mode should improve."""
        g = CapitalGuard(initial_capital=10000.0,
                         emergency_dd_threshold=20.0,
                         halt_dd_threshold=35.0)
        g.update_equity(10000.0)
        g._equity_peak = 10000.0

        # Deep drawdown
        assert g.guard_mode(6000.0) == GuardMode.HALT

        # Recovery above halt but still in emergency
        g._equity_peak = 10000.0  # peak hasn't been exceeded
        assert g.guard_mode(8000.0) == GuardMode.EMERGENCY  # 20% DD

    def test_summary_includes_kill_switch_state(self):
        g = CapitalGuard(initial_capital=10000.0)
        s = g.summary()
        assert "mode" in s
        assert "kill_switch" in s
        assert "can_enter" in s
        assert "trading_allowed" in s
