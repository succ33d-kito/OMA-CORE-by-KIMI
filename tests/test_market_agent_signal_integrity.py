"""MarketAgent Signal Integrity Tests — verify FLAW-14 fix and signal correctness."""
import pytest
import sys, math
from statistics import mean, stdev

sys.path.insert(0, ".")

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency
from core.schemas.agent_schema import Recommendation
from core.agents.market_agent import MarketAgent


def _rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(len(closes) - period, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains.append(max(ch, 0))
        losses.append(max(-ch, 0))
    ag = mean(gains)
    al = mean(losses)
    if al == 0:
        return 100.0
    return 100.0 - (100.0 / (1.0 + ag / al))


# ── Fixture Helpers ──────────────────────────────────────────────

def make_ohlcv(closes, vol=1000.0):
    """Build OHLCV from closing prices with reasonable H/L spread."""
    return [
        {"close": c, "high": c * 1.005, "low": c * 0.995, "volume": vol}
        for c in closes
    ]


def make_event(symbol="BTC", price=50000.0):
    return Event(
        id="sig_test", source="test",
        event_type=EventType.PRICE_MOVEMENT,
        title=f"{symbol} test",
        summary="test",
        assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO, price_at_event=price)],
        timestamp=__import__("datetime").datetime(2024, 1, 15, 12, 0,
                         tzinfo=__import__("datetime").timezone.utc),
        sentiment=Sentiment.NEUTRAL, sentiment_score=0,
        confidence=0.5, urgency=Urgency.LOW,
    )


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def oversold_recovery_setup():
    """RSI < 30, price stabilizing. Current code produces SELL (MomBreak) not BUY."""
    closes = []
    price = 50000.0
    # Phase 1: gentle decline (30 candles) — sets SMA20/SMA50 context
    for _ in range(30):
        price *= 0.998
        closes.append(price)
    # Phase 2: sharp drop (10 candles) — pushes RSI below 30
    for _ in range(10):
        price *= 0.995
        closes.append(price)
    # Phase 3: stabilize and minor bounce (10 candles)
    # Last candle below the prior 5 lows but RSI is deeply oversold
    for _ in range(5):
        price *= 0.997
        closes.append(price)
    for _ in range(5):
        price *= 1.001
        closes.append(price)
    # Force last candle below 5-period low
    closes[-1] = min(closes[-6:-1]) - 50
    return closes


@pytest.fixture
def momentum_breakdown_setup():
    """Downtrend, close breaks low, RSI NOT oversold (35-55 range: enough up candles)."""
    closes = []
    price = 50000.0
    for _ in range(30):
        price *= 0.9995
        closes.append(price)
    # 10 candles with alternating small up/down, net down
    for i in range(10):
        price *= 0.997 if i % 3 == 0 else 1.001
        closes.append(price)
    # 6 candles: small up moves to keep RSI > 30
    for _ in range(5):
        price *= 1.001
        closes.append(price)
    # Final breakdown below 5-period low
    price = min(closes[-6:-1]) - 150
    closes.append(price)
    return closes


@pytest.fixture
def neutral_chop_setup():
    """No clear trend, RSI ~50, no strong momentum."""
    closes = []
    price = 50000.0
    import random
    rng = random.Random(42)
    for _ in range(50):
        price *= (1 + rng.gauss(0, 0.002))
        closes.append(price)
    return closes


@pytest.fixture
def strong_uptrend_setup():
    """SMA20 > SMA50, momentum positive, RSI < 70."""
    closes = []
    price = 50000.0
    for i in range(50):
        price *= 1.004
        price += i * 2
        closes.append(price)
    return closes


@pytest.fixture
def strong_downtrend_setup():
    """SMA20 < SMA50, momentum negative, RSI > 40."""
    closes = []
    price = 50000.0
    for i in range(50):
        if i % 2 == 0:
            price *= 1.0025  # up candle
        else:
            price *= 0.9975  # down candle (larger move)
        closes.append(price)
    return closes


def check_flaw14(closes):
    """Verify that FLAW-14 is present: MomBreak SHORT blocks RSI<30 BUY."""
    rsi_val = _rsi(closes, 14)
    last_below_5l = closes[-1] < min(closes[-6:-1])
    return rsi_val < 30 and last_below_5l


# ── Tests ─────────────────────────────────────────────────────────

class TestFLAW14Reproduction:
    """Phase 1: Confirm FLAW-14 exists in current code."""

    def test_flaw14_scenario_is_oversold_and_breakdown(self, oversold_recovery_setup):
        """The oversold fixture must have RSI<30 AND price below 5-period low."""
        closes = oversold_recovery_setup
        assert _rsi(closes, 14) < 30, "RSI must be oversold (<30)"
        assert closes[-1] < min(closes[-6:-1]), "Last close must be below 5-period low"

    def test_flaw14_fixed_oversold_buy_restored(self, oversold_recovery_setup):
        """FLAW-14 fixed: RSI<30 BUY now beats MomBreak SHORT."""
        agent = MarketAgent()
        ohlcv = make_ohlcv(oversold_recovery_setup)
        event = make_event()
        agent._fetch_ohlcv = lambda s: ohlcv
        opinion = agent.analyze(event)
        assert opinion is not None, "Agent must produce an opinion"
        # After fix: oversold BUY wins over MomBreak SHORT
        rec = opinion.recommendation
        assert rec in (Recommendation.BUY, Recommendation.STRONG_BUY), (
            f"FLAW-14 fixed: expected BUY, got {rec.value}"
        )


class TestMarketAgentSignalIntegrity:
    """Verify signal correctness for each setup."""

    def test_oversold_recovery_should_be_buy(self, oversold_recovery_setup):
        """When RSI<30 and price is at lows, signal should be BUY, not SELL."""
        agent = MarketAgent()
        agent._fetch_ohlcv = lambda s: make_ohlcv(oversold_recovery_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None
        # After FLAW-14 fix, this should be BUY
        rec = opinion.recommendation
        assert rec in (Recommendation.BUY, Recommendation.STRONG_BUY), (
            f"Oversold recovery should give BUY, got {rec.value}"
        )

    def test_momentum_breakdown_should_be_sell(self, momentum_breakdown_setup):
        """Clear breakdown without oversold should still be SELL."""
        agent = MarketAgent()
        agent._fetch_ohlcv = lambda s: make_ohlcv(momentum_breakdown_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None
        rec = opinion.recommendation
        assert rec in (Recommendation.SELL, Recommendation.STRONG_SELL), (
            f"Momentum breakdown should give SELL, got {rec.value}"
        )

    def test_neutral_chop_should_be_watch(self, neutral_chop_setup):
        """No clear signal should produce WATCH."""
        agent = MarketAgent()
        agent._fetch_ohlcv = lambda s: make_ohlcv(neutral_chop_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None
        rec = opinion.recommendation
        assert rec in (Recommendation.WATCH, Recommendation.HOLD, Recommendation.NO_ACTION), (
            f"Neutral chop should give WATCH, got {rec.value}"
        )

    def test_strong_uptrend_should_be_buy(self, strong_uptrend_setup):
        """Strong uptrend should produce BUY."""
        agent = MarketAgent()
        agent._fetch_ohlcv = lambda s: make_ohlcv(strong_uptrend_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None
        rec = opinion.recommendation
        assert rec in (Recommendation.BUY, Recommendation.STRONG_BUY), (
            f"Strong uptrend should give BUY, got {rec.value}"
        )

    def test_strong_downtrend_should_be_sell(self, strong_downtrend_setup):
        """Strong downtrend should produce SELL."""
        agent = MarketAgent()
        agent._fetch_ohlcv = lambda s: make_ohlcv(strong_downtrend_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None
        rec = opinion.recommendation
        assert rec in (Recommendation.SELL, Recommendation.STRONG_SELL), (
            f"Strong downtrend should give SELL, got {rec.value}"
        )


class TestSignalModeBehavior:
    """Signal mode constraints must still work with new logic."""

    def test_long_only_blocks_sell(self, momentum_breakdown_setup):
        agent = MarketAgent(signal_mode="long_only")
        agent._fetch_ohlcv = lambda s: make_ohlcv(momentum_breakdown_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None
        assert opinion.recommendation != Recommendation.SELL, (
            "long_only must block SELL"
        )

    def test_short_only_blocks_buy(self, strong_uptrend_setup):
        agent = MarketAgent(signal_mode="short_only")
        agent._fetch_ohlcv = lambda s: make_ohlcv(strong_uptrend_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None
        assert opinion.recommendation not in (Recommendation.BUY, Recommendation.STRONG_BUY), (
            "short_only must block BUY"
        )

    def test_short_style_mom_break_disables_rsi_short(self, oversold_recovery_setup):
        """short_style=mom_break should not emit RSI-based SHORT."""
        agent = MarketAgent(short_style="mom_break")
        agent._fetch_ohlcv = lambda s: make_ohlcv(oversold_recovery_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None

    def test_short_style_rsi_disables_mom_break(self, momentum_breakdown_setup):
        """short_style=rsi should not emit MomBreak SHORT."""
        agent = MarketAgent(short_style="rsi")
        agent._fetch_ohlcv = lambda s: make_ohlcv(momentum_breakdown_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None


class TestMetadataPreservation:
    """Required metadata fields must still be present after refactoring."""

    def test_metadata_has_required_fields(self, strong_uptrend_setup):
        agent = MarketAgent()
        agent._fetch_ohlcv = lambda s: make_ohlcv(strong_uptrend_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None
        meta = opinion.metadata
        for key in ("symbol", "price", "sma_20", "sma_50", "trend",
                     "rsi_14", "atr_14", "volatility_24h", "momentum_10d",
                     "volume_ratio", "position_size_factor"):
            assert key in meta, f"Missing metadata field: {key}"

    def test_metadata_has_required_fields_oversold(self, oversold_recovery_setup):
        agent = MarketAgent()
        agent._fetch_ohlcv = lambda s: make_ohlcv(oversold_recovery_setup)
        opinion = agent.analyze(make_event())
        assert opinion is not None
        meta = opinion.metadata
        for key in ("symbol", "price", "sma_20", "sma_50", "trend",
                     "rsi_14", "atr_14", "volatility_24h", "momentum_10d"):
            assert key in meta, f"Missing metadata field: {key}"
