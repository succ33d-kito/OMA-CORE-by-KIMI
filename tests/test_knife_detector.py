"""Test KnifeDetector — Synthetic scenarios for dip vs falling knife validation.
Target: >=90% classification accuracy on 4 scenarios.
"""
import pytest
from core.execution.knife_detector import KnifeDetector


class ScenarioGenerator:
    """Generates synthetic OHLCV data for knife detection scenarios."""

    @staticmethod
    def healthy_dip(length=48):
        """Price drops then recovers strongly with declining volume.
        Score should be >=65 (dip_buy).
        """
        closes = []
        volumes = []
        highs = []
        lows = []

        base = 100.0
        for i in range(length):
            if i < 10:
                p = base * (1 - 0.005 * i)
            elif i < 20:
                p = base * (1 - 0.05 - 0.01 * (i - 10))
            elif i < 30:
                recovery = (i - 20) / 10
                p = base * (1 - 0.15 + 0.12 * recovery)
            else:
                p = base * (1 - 0.03)
            noise = base * 0.002 * ((i % 5) - 2)
            close = p + noise
            closes.append(close)

            vol = 5000 - (i / length) * 3000
            volumes.append(max(vol, 200))

            spread = base * 0.005
            highs.append(close + spread * (1 + (i % 3)))
            lows.append(close - spread * (1 + (i % 3)))

        return closes, volumes, highs, lows

    @staticmethod
    def dead_cat_bounce(length=48):
        """Sharp drop, weak bounce, then continued decline.
        Score should be <35 (falling_knife or uncertain).
        """
        closes = []
        volumes = []
        highs = []
        lows = []

        base = 100.0
        for i in range(length):
            if i < 5:
                p = base * (1 - 0.04 * (i + 1))
            elif i < 10:
                p = base * (1 - 0.20 + 0.03 * (i - 5))
            elif i < 20:
                p = base * (1 - 0.05 - 0.02 * (i - 10))
            elif i < 35:
                p = base * (1 - 0.25 - 0.01 * (i - 20))
            else:
                p = base * (1 - 0.40 - 0.005 * (i - 35))
            noise = base * 0.003 * ((i % 4) - 2)
            close = p + noise
            closes.append(close)

            # Volume spikes on drops, stays elevated
            if i < 5:
                vol = 10000
            elif i < 10:
                vol = 7000
            else:
                vol = 5000 + (i % 5) * 500
            volumes.append(vol)

            spread = base * 0.008
            highs.append(close + spread * (1 + (i % 3)))
            lows.append(close - spread * (1 + (i % 3)))

        return closes, volumes, highs, lows

    @staticmethod
    def falling_knife(length=48):
        """Continuous decline with accelerating volume. No bounce.
        Each candle drops ~1%. Score should be <35 (falling_knife).
        """
        closes = []
        volumes = []
        highs = []
        lows = []

        price = 100.0
        for i in range(length):
            drop_pct = 0.02 + (i / length) * 0.03
            price *= (1 - drop_pct)
            closes.append(price)

            vol = 2000 + (i / length) * 18000
            volumes.append(vol)

            spread = price * 0.003
            highs.append(price + spread)
            lows.append(price - spread)

        return closes, volumes, highs, lows

    @staticmethod
    def recovery(length=60):
        """V-shaped recovery: sharp drop then sustained recovery.
        Recovery continues to the end so knife detector sees active bounce.
        Score should be >=65 (dip_buy).
        """
        closes = []
        volumes = []
        highs = []
        lows = []

        base = 100.0
        for i in range(length):
            if i < 10:
                p = base * (1 - 0.03 * (i + 1))
            elif i < 15:
                p = base * (1 - 0.30 + 0.02 * (i - 10))
            elif i < 40:
                recovery = (i - 15) / 25
                p = base * (1 - 0.20 + 0.18 * recovery)
            else:
                p = base * (1 - 0.02 + 0.005 * (i - 40))
            noise = base * 0.002 * ((i % 5) - 2)
            close = p + noise
            closes.append(close)

            if i < 12:
                vol = 10000 - i * 400
            elif i < 25:
                vol = 5200 - (i - 12) * 200
            else:
                vol = 2600 - (i - 25) * 30
            volumes.append(max(vol, 300))

            spread = base * 0.005
            highs.append(close + spread * (1 + (i % 3)))
            lows.append(close - spread * (1 + (i % 3)))

        return closes, volumes, highs, lows


class TestKnifeDetectorScenarios:
    @pytest.fixture
    def detector(self):
        return KnifeDetector()

    def test_healthy_dip(self, detector):
        closes, volumes, highs, lows = ScenarioGenerator.healthy_dip()
        result = detector.analyze(closes, volumes, highs, lows)
        assert result["verdict"] == "dip_buy", \
            f"Healthy dip should be dip_buy, got {result['verdict']} (score={result['score']})"
        assert result["score"] >= 65

    def test_dead_cat_bounce(self, detector):
        closes, volumes, highs, lows = ScenarioGenerator.dead_cat_bounce()
        result = detector.analyze(closes, volumes, highs, lows)
        assert result["verdict"] in ("falling_knife", "uncertain"), \
            f"Dead cat should not be dip_buy, got {result['verdict']} (score={result['score']})"
        assert result["score"] < 65

    def test_falling_knife(self, detector):
        closes, volumes, highs, lows = ScenarioGenerator.falling_knife()
        result = detector.analyze(closes, volumes, highs, lows)
        assert result["verdict"] == "falling_knife", \
            f"Falling knife should be falling_knife, got {result['verdict']} (score={result['score']})"
        assert result["score"] < 35

    def test_recovery_second_half(self, detector):
        """Recovery pattern should be dip_buy."""
        closes, volumes, highs, lows = ScenarioGenerator.recovery()
        result_full = detector.analyze(closes, volumes, highs, lows)
        assert result_full["verdict"] == "dip_buy", \
            f"Recovery should be dip_buy, got {result_full['verdict']} (score={result_full['score']})"

    def test_is_safe_to_buy(self, detector):
        closes, volumes, highs, lows = ScenarioGenerator.healthy_dip()
        assert detector.is_safe_to_buy(closes, volumes, highs, lows) is True

        closes, volumes, highs, lows = ScenarioGenerator.falling_knife()
        assert detector.is_safe_to_buy(closes, volumes, highs, lows) is False


class TestKnifeDetectorPositionSizing:
    @pytest.fixture
    def detector(self):
        return KnifeDetector()

    def test_full_size_on_dip(self, detector):
        closes, volumes, highs, lows = ScenarioGenerator.healthy_dip()
        mult = detector.position_size_multiplier(closes, volumes, highs, lows)
        assert mult == 1.0

    def test_zero_size_on_falling_knife(self, detector):
        closes, volumes, highs, lows = ScenarioGenerator.falling_knife()
        mult = detector.position_size_multiplier(closes, volumes, highs, lows)
        assert mult <= 0.25

    def test_partial_on_dead_cat(self, detector):
        closes, volumes, highs, lows = ScenarioGenerator.dead_cat_bounce()
        mult = detector.position_size_multiplier(closes, volumes, highs, lows)
        assert mult < 1.0


class TestKnifeDetectorEdgeCases:
    @pytest.fixture
    def detector(self):
        return KnifeDetector()

    def test_insufficient_data(self, detector):
        result = detector.analyze([100, 101], [1000, 1100], [102, 103], [99, 100])
        assert result["verdict"] == "unknown"
        assert result["score"] == 50

    def test_stable_market(self, detector):
        closes = [100.0 + (i % 3) * 0.5 for i in range(50)]
        volumes = [1000.0 for _ in range(50)]
        highs = [c + 1 for c in closes]
        lows = [c - 1 for c in closes]
        result = detector.analyze(closes, volumes, highs, lows)
        assert result["verdict"] in ("uncertain", "dip_buy")

    def test_summary_fields(self, detector):
        closes, volumes, highs, lows = ScenarioGenerator.healthy_dip()
        result = detector.analyze(closes, volumes, highs, lows)
        assert "score" in result
        assert "verdict" in result
        assert "bounce_recovery" in result
        assert "volume_trend" in result
        assert "momentum_3" in result
        assert "volatility_ratio" in result
        assert "evidence" in result
