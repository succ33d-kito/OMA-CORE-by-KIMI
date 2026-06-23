"""Tests for OSIRIS Market Agent"""
import pytest
from datetime import datetime, timezone
from core.agents.market_agent import MarketAgent
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency
from core.schemas.agent_schema import Recommendation


class TestMarketAgent:
    def test_no_assets_returns_none(self):
        agent = MarketAgent()
        event = Event(
            id="test_1", source="test",
            title="Test event with no assets",
        )
        opinion = agent.analyze(event)
        assert opinion is None

    def test_skip_without_ohlcv(self, monkeypatch):
        agent = MarketAgent()
        event = Event(
            id="test_2", source="test",
            event_type=EventType.PRICE_MOVEMENT,
            title="BTC price movement",
            assets=[Asset(symbol="FAKE123XYZ", name="Fake", asset_class=AssetClass.CRYPTO, price_at_event=100.0)],
        )

        def mock_fetch(*args, **kwargs):
            return None
        monkeypatch.setattr(agent, "_fetch_ohlcv", mock_fetch)

        opinion = agent.analyze(event)
        assert opinion is None

    def test_indicator_calculations(self):
        agent = MarketAgent()
        closes = [100, 102, 101, 105, 107, 106, 108, 110, 109, 111,
                  115, 114, 116, 118, 120, 119, 121, 123, 122, 124]
        highs = [x + 2 for x in closes]
        lows = [x - 2 for x in closes]
        volumes = [1000] * 20

        rsi = agent._calculate_rsi(closes, 14)
        atr = agent._calculate_atr(highs, lows, closes, 14)

        assert 0 <= rsi <= 100
        assert atr > 0

    def test_analyze_with_mock_ohlcv(self, monkeypatch):
        agent = MarketAgent()
        event = Event(
            id="test_3", source="test",
            event_type=EventType.PRICE_MOVEMENT,
            title="BTC moving",
            assets=[Asset(symbol="BTC", name="Bitcoin", asset_class=AssetClass.CRYPTO, price_at_event=50000.0)],
            sentiment=Sentiment.BULLISH, sentiment_score=0.5,
            confidence=0.9,
        )

        mock_ohlcv = [
            {"close": 49000 + i * 100, "high": 49100 + i * 100, "low": 48900 + i * 100, "volume": 1000 + i * 10}
            for i in range(50)
        ]
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: mock_ohlcv)

        opinion = agent.analyze(event)
        assert opinion is not None
        assert opinion.agent_name == "market_agent"
        assert opinion.agent_role.value == "market_analyst"
        assert opinion.event_id == "test_3"
        assert len(opinion.evidence) > 0
        assert opinion.metadata.get("symbol") == "BTC"

    def test_multiple_events(self, monkeypatch):
        agent = MarketAgent()

        def mock_fetch(*args, **kwargs):
            return [
                {"close": 100.0 + i, "high": 102.0 + i, "low": 98.0 + i, "volume": 1000.0}
                for i in range(50)
            ]
        monkeypatch.setattr(agent, "_fetch_ohlcv", mock_fetch)

        events = [
            Event(
                id=f"batch_{i}",
                source="test",
                event_type=EventType.PRICE_MOVEMENT,
                title=f"Event {i}",
                assets=[Asset(symbol="BTC", name="Bitcoin", asset_class=AssetClass.CRYPTO, price_at_event=50000.0)],
            )
            for i in range(3)
        ]
        opinions = agent.analyze_batch(events)
        assert len(opinions) == 3
        for o in opinions:
            assert o.agent_role.value == "market_analyst"
