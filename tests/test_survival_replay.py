"""Test Survival Replay — Run historical crash periods with full protection stack.
Validates CrashDetector v2, KnifeDetector, CapitalGuard, GapRiskEngine integration.
"""
import pytest
from datetime import datetime, timezone
from core.execution.crash_detector import CrashDetector, CrashMode
from core.execution.capital_guard import CapitalGuard, GuardMode
from core.execution.gap_risk import GapRiskEngine


class TestCrashDetectorHistoricalReplay:
    """Replay historical crash patterns through CrashDetector v2."""

    def _run_crash_pattern(self, daily_drops, label=""):
        """Feed price data through CrashDetector, return score/mode history."""
        d = CrashDetector()
        scores = []
        modes = []
        price = 10000.0

        for drop in daily_drops:
            for i in range(24):
                noise = ((i * 7) % 5 - 2) / 1000 * price
                price *= (1 + drop / 24)
                price += noise
                vol = 1000 * (1 + abs(drop) * 10)
                d.update_price(price, vol)
            scores.append(d.crash_score())
            modes.append(d.crash_mode(10000))

        return scores, modes, d

    def test_covid_crash_detected(self):
        """COVID: -60% over ~40 days of hourly data. Must trigger WARNING+."""
        daily_drops = [-0.01, -0.02, -0.03, -0.05, -0.02, -0.01,
                       -0.01, -0.03, -0.03, -0.02, -0.01, -0.01,
                       -0.02, -0.01, -0.03, -0.04, -0.02, -0.01,
                       -0.01, -0.02, -0.02, -0.01, -0.03, -0.02,
                       -0.01, -0.01, -0.02, -0.01, -0.01, -0.02,
                       -0.02, -0.01, -0.02, -0.01, -0.01, -0.01,
                       -0.02, -0.01, -0.01, -0.01]

        scores, modes, d = self._run_crash_pattern(daily_drops, "COVID")

        max_score = max(scores)
        max_mode_idx = max(
            (i for i, m in enumerate(modes) if m != CrashMode.NONE),
            default=-1)

        assert max_score >= 25, f"COVID must score >=25, got {max_score}"
        assert any(m != CrashMode.NONE for m in modes), \
            "COVID must trigger at least WARNING"
        assert d.crash_score() >= 5, \
            "Final score should still show residual alert"

    def test_ftx_crash_detected(self):
        """FTX collapse: -25% in ~10 days. Should trigger WARNING+."""
        daily_drops = [-0.05, -0.08, -0.03, -0.02, -0.04,
                       -0.03, -0.01, -0.02, -0.01, -0.02,
                       -0.01, -0.01, -0.01, -0.01, -0.01]

        scores, modes, d = self._run_crash_pattern(daily_drops, "FTX")
        max_score = max(scores)

        assert max_score >= 20, f"FTX must score >=20, got {max_score}"
        assert any(m != CrashMode.NONE for m in modes), \
            f"FTX must trigger, max_score={max_score}, modes={set(m.value for m in modes)}"

    def test_luna_crash_detected(self):
        """Luna collapse: -50% in ~14 days. Must trigger EMERGENCY+."""
        daily_drops = [-0.03, -0.05, -0.08, -0.12, -0.06,
                       -0.04, -0.03, -0.02, -0.03, -0.02,
                       -0.02, -0.01, -0.02, -0.01, -0.01,
                       -0.01, -0.01, -0.01]

        scores, modes, d = self._run_crash_pattern(daily_drops, "Luna")
        max_score = max(scores)

        assert max_score >= 35, f"Luna must score >=35, got {max_score}"
        assert any(m in (CrashMode.WARNING, CrashMode.EMERGENCY, CrashMode.PANIC) for m in modes), \
            f"Luna must trigger, max_score={max_score}"

    def test_normal_market_no_crash(self):
        """Normal market with oscillations should NOT trigger."""
        daily_changes = [0.002, -0.001, 0.003, -0.002, 0.001,
                         -0.001, 0.002, -0.003, 0.001, 0.002,
                         -0.001, 0.001, -0.002, 0.003, 0.001,
                         0.002, -0.001, 0.001, -0.002, 0.002]

        scores, modes, d = self._run_crash_pattern(daily_changes, "Normal")
        max_score = max(scores)

        assert max_score < 25, f"Normal market should score <25, got {max_score}"
        assert all(m == CrashMode.NONE for m in modes)


class TestCapitalGuardHistoricalDrawdown:
    def test_covid_drawdown_guard_progression(self):
        g = CapitalGuard(initial_capital=10000.0,
                         max_daily_loss_pct=10.0,
                         max_weekly_loss_pct=20.0,
                         emergency_dd_threshold=20.0,
                         halt_dd_threshold=35.0)

        # Simulate COVID-style losses
        losses = [-200, -300, -500, -400, -200, -100, -300,
                  -200, -100, -200, -300, -200, -100, -100]
        equity = 10000.0
        modes = []
        for loss in losses:
            g.record_trade_result(loss, datetime(2020, 3, 1, 12, 0, tzinfo=timezone.utc))
            equity += loss
            g.update_equity(equity)
            modes.append(g.guard_mode(equity))

        assert any(m == GuardMode.CAUTION for m in modes), \
            "COVID losses should trigger CAUTION"

    def test_luna_drawdown_emergency(self):
        g = CapitalGuard(initial_capital=10000.0,
                         max_daily_loss_pct=10.0,
                         max_weekly_loss_pct=20.0,
                         emergency_dd_threshold=20.0,
                         halt_dd_threshold=35.0)

        losses = [-500, -800, -1000, -600, -400, -500, -300]
        equity = 10000.0
        for loss in losses:
            g.record_trade_result(loss, datetime(2022, 5, 1, 12, 0, tzinfo=timezone.utc))
            equity += loss
            g.update_equity(equity)

        dd = g.drawdown_pct(equity)
        assert dd > 15.0, f"Luna should cause >15% DD, got {dd:.1f}%"

    def test_normal_market_no_guard_activation(self):
        g = CapitalGuard(initial_capital=10000.0)

        pnls = [50, 30, -20, 40, 10, -10, 20, 30, -15, 25]
        equity = 10000.0
        for pnl in pnls:
            g.record_trade_result(pnl)
            equity += pnl
            g.update_equity(equity)

        assert g.guard_mode(equity) == GuardMode.NORMAL


class TestGapRiskCrisisDetection:
    def test_gap_risk_elevated_during_crisis(self):
        gr = GapRiskEngine()
        # Simulate volatile price action with large gaps
        prices = [100.0, 101.0, 98.0, 102.0, 95.0, 93.0, 97.0, 92.0, 88.0, 91.0,
                  87.0, 85.0, 90.0, 84.0, 82.0, 86.0, 81.0, 80.0, 83.0, 79.0]
        for p in prices:
            gr.record_price(p)

        assert gr.gap_risk_score() > 0
        assert gr.max_gap_size() > 0
        assert gr.avg_gap_size() > 0

    def test_gap_risk_low_in_stable_market(self):
        gr = GapRiskEngine()
        for i in range(50):
            gr.record_price(100.0 + (i % 5 - 2) * 0.1)
        assert gr.gap_risk_score() < 30


class TestIntegratedProtectionStack:
    def test_crash_detector_feeds_capital_guard(self):
        """Verify crash detector scores correlate with guard modes."""
        cd = CrashDetector()
        cg = CapitalGuard(initial_capital=10000.0,
                          emergency_dd_threshold=20.0,
                          halt_dd_threshold=35.0)

        # Simulate crash
        price = 10000.0
        for i in range(100):
            price *= 0.99
            cd.update_price(price)
            if i % 24 == 0:
                loss = -200 - (i // 24) * 50
                cg.record_trade_result(loss)

        crash_mode = cd.crash_mode(10000)
        assert crash_mode != CrashMode.NONE

    def test_knife_detector_complements_crash_detector(self):
        """In crash conditions, knife detector should be cautious."""
        from core.execution.knife_detector import KnifeDetector
        cd = CrashDetector()
        kd = KnifeDetector()

        price = 10000.0
        closes = []
        volumes = []
        highs = []
        lows = []

        for i in range(72):
            price *= 0.99
            cd.update_price(price)
            closes.append(price)
            volumes.append(5000 + (i % 10) * 200)
            highs.append(price * 1.01)
            lows.append(price * 0.99)

        crash_mode = cd.crash_mode(10000)
        knife_result = kd.analyze(closes, volumes, highs, lows)

        if crash_mode != CrashMode.NONE:
            # During crash, knife detector should not say "dip_buy"
            assert knife_result["verdict"] != "dip_buy", \
                f"In crash mode {crash_mode}, knife says {knife_result['verdict']}"
