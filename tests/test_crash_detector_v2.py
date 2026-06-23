"""Test CrashDetector v2 — Multi-window drawdown velocity detection.
Verifies both FAST and SLOW crash detection.
"""
import pytest
from core.execution.crash_detector import CrashDetector, CrashMode


class TestCrashDetectorV2Indicators:
    def test_6h_velocity_fast_crash(self):
        d = CrashDetector()
        # 6 prices with a 10% drop → fast crash
        prices = [100.0, 99.0, 97.0, 95.0, 92.0, 90.0]
        for p in prices:
            d.update_price(p)
        assert d.drawdown_velocity_6h() > 9.0
        assert d.crash_score() >= 15  # at minimum fast velocity threshold hit

    def test_24h_velocity_medium_crash(self):
        d = CrashDetector()
        # 24 prices with sustained 12% drop
        prices = [100.0 * (1 - 0.005 * i) for i in range(25)]
        for p in prices:
            d.update_price(p)
        v24 = d.drawdown_velocity_24h()
        assert v24 > 10.0  # ~11.5% drop
        assert d.crash_score() >= 12  # medium velocity contributes

    def test_72h_velocity_slow_crash(self):
        d = CrashDetector()
        # 72 prices with 20% persistent decline
        prices = [100.0 * (1 - 0.003 * i) for i in range(73)]
        for p in prices:
            d.update_price(p)
        v72 = d.drawdown_velocity_72h()
        assert v72 > 15.0  # ~18% drop
        score = d.crash_score()
        assert score >= 15  # slow velocity contributes

    def test_drawdown_acceleration(self):
        d = CrashDetector()
        # Stable then accelerating drop
        for i in range(18):
            d.update_price(100.0)
        for i in range(6):
            d.update_price(100.0 * (1 - 0.03 * (i + 1)))
        accel = d.drawdown_acceleration()
        assert accel > 0

    def test_no_acceleration_in_stable_market(self):
        d = CrashDetector()
        for i in range(30):
            d.update_price(100.0)
        accel = d.drawdown_acceleration()
        assert abs(accel) < 1.0

    def test_atr_expansion(self):
        d = CrashDetector()
        # Quiet then volatile
        for i in range(28):
            d.update_price(100.0)
        for i in range(14):
            d.update_price(100.0 + (i % 2 - 0.5) * 5)
        assert d.atr_expansion() > 1.0

    def test_volume_ratio(self):
        d = CrashDetector()
        for i in range(20):
            d.update_price(100.0, volume=1000)
        d.update_price(99.0, volume=5000)
        assert d.volume_ratio() > 3.0

    def test_volatility_regime(self):
        d = CrashDetector()
        # High volatility
        for i in range(20):
            d.update_price(100.0 + (i % 2 - 0.5) * 8)
        assert d.volatility_regime() in ("extreme", "elevated")

        # Low volatility
        d2 = CrashDetector()
        for i in range(20):
            d2.update_price(100.0 + (i % 2 - 0.5) * 0.5)
        assert d2.volatility_regime() == "normal"


class TestCrashDetectorV2Modes:
    def test_normal_mode(self):
        d = CrashDetector()
        for i in range(50):
            d.update_price(100.0 + (i % 5 - 2))
        assert d.crash_mode(10000) == CrashMode.NONE

    def test_warning_mode_from_score(self):
        d = CrashDetector()
        for i in range(30):
            d.update_price(100.0 * (1 - 0.01 * i))
        mode = d.crash_mode(10000)
        assert mode in (CrashMode.WARNING, CrashMode.EMERGENCY)

    def test_panic_mode_from_score(self):
        d = CrashDetector()
        # Stable prices first so 24h/72h windows have context
        for i in range(72):
            d.update_price(100.0)
        # Fast crash over 24 periods triggers all windows
        for i in range(24):
            d.update_price(100.0 * (1 - 0.04 * (i + 1)))
        score = d.crash_score()
        assert score >= 70
        assert d.crash_mode(10000) == CrashMode.PANIC

    def test_panic_mode_from_drawdown(self):
        d = CrashDetector()
        d._peak_equity = 10000.0
        # Simulate 35% drawdown
        d.update_equity(6500.0)
        assert d.crash_mode(6500.0) == CrashMode.PANIC

    def test_emergency_mode_from_drawdown(self):
        d = CrashDetector()
        d._peak_equity = 10000.0
        d.update_equity(7800.0)
        assert d.crash_mode(7800.0) == CrashMode.EMERGENCY


class TestCrashDetectorV2MultiWindow:
    def test_fast_crash_only(self):
        """Fast flash crash — 6h velocity high, 72h velocity diluted."""
        d = CrashDetector()
        for i in range(66):
            d.update_price(100.0)
        # Flash crash in last 6 periods
        for i in range(6):
            d.update_price(100.0 * (1 - 0.05 * (i + 1)))
        assert d.drawdown_velocity_6h() > 20.0
        v72 = d.drawdown_velocity_72h()
        assert v72 < 50.0  # diluted by 66 stable periods
        assert d.crash_mode(10000) in (CrashMode.EMERGENCY, CrashMode.PANIC)

    def test_slow_crash_only(self):
        """Slow multi-day crash — 72h high, 6h low."""
        d = CrashDetector()
        for i in range(73):
            d.update_price(100.0 * (1 - 0.003 * (i + 1)))
        assert d.drawdown_velocity_6h() < 3.0  # slow per 6h
        assert d.drawdown_velocity_72h() > 15.0  # sustained decline
        mode = d.crash_mode(10000)
        assert mode != CrashMode.NONE  # must detect slow crash
        assert d.crash_score() >= 15

    def test_mixed_crash_all_windows_trigger(self):
        """Cascading crash — all windows trigger simultaneously."""
        d = CrashDetector()
        for i in range(73):
            d.update_price(100.0 * (1 - 0.01 * (i + 1)))
        assert d.drawdown_velocity_6h() > 3.0
        assert d.drawdown_velocity_24h() > 10.0
        assert d.drawdown_velocity_72h() > 30.0
        assert d.crash_mode(10000) in (CrashMode.EMERGENCY, CrashMode.PANIC)

    def test_covid_style_replay(self):
        """Simulate COVID-style crash: slow grind down over 40 days with
        one acceleration phase. Should trigger WARNING or higher."""
        d = CrashDetector()
        max_score = 0

        price = 10000.0
        daily_drops = [-0.01, -0.02, -0.03, -0.05, -0.02, -0.01,
                       -0.01, -0.03, -0.03, -0.02, -0.01, -0.01,
                       -0.02, -0.01, -0.03, -0.04, -0.02, -0.01,
                       -0.01, -0.02, -0.02, -0.01, -0.03, -0.02,
                       -0.01, -0.01, -0.02, -0.01, -0.01, -0.02,
                       -0.02, -0.01, -0.02, -0.01, -0.01, -0.01,
                       -0.02, -0.01, -0.01, -0.01]

        for drop in daily_drops:
            for i in range(24):
                noise = ((i * 7) % 5 - 2) / 1000 * price
                price *= (1 + drop / 24)
                price += noise
                vol = 1000 * (1 + abs(drop) * 10)
                d.update_price(price, vol)
            max_score = max(max_score, d.crash_score())

        assert max_score >= 25, f"COVID-style crash must trigger. max_score={max_score}"

    def test_no_false_positive_in_bull_market(self):
        d = CrashDetector()
        for i in range(100):
            d.update_price(100.0 * (1 + 0.002 * (i % 20 - 10)))
        assert d.crash_mode(10000) == CrashMode.NONE


class TestCrashDetectorV2Integration:
    def test_position_size_multiplier(self):
        d = CrashDetector()
        assert d.position_size_multiplier(10000) == 1.0
        d.update_equity(7500.0)
        assert d.position_size_multiplier(7500.0) == 0.25  # EMERGENCY
        d.update_equity(6000.0)
        assert d.position_size_multiplier(6000.0) == 0.0  # PANIC

    def test_trade_results_losses(self):
        d = CrashDetector()
        d.update_price(100.0)
        d.record_trade_result(-2.0)
        d.record_trade_result(-3.0)
        d.record_trade_result(-1.0)
        d.record_trade_result(-4.0)
        d.record_trade_result(-2.0)
        assert d._consecutive_losses == 5

    def test_summary_keys(self):
        d = CrashDetector()
        for i in range(50):
            d.update_price(100.0 + (i % 5 - 2))
        s = d.summary()
        assert "crash_score" in s
        assert "drawdown_velocity_6h" in s
        assert "drawdown_velocity_24h" in s
        assert "drawdown_velocity_72h" in s
        assert "drawdown_acceleration" in s
        assert "volatility_regime" in s
        assert "mode" in s
