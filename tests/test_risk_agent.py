"""Tests for OSIRIS Risk Agent"""
import pytest
from datetime import datetime, timezone
from core.agents.risk_agent import RiskAgent
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency
from core.schemas.agent_schema import Recommendation


class TestRiskAgent:
    def test_no_assets_returns_none(self):
        agent = RiskAgent()
        event = Event(id="test_1", source="test", title="No assets")
        opinion = agent.analyze(event)
        assert opinion is None

    def test_hack_event_increases_risk(self, monkeypatch):
        agent = RiskAgent()

        def mock_fetch(*args, **kwargs):
            return None
        monkeypatch.setattr(agent, "_fetch_ohlcv", mock_fetch)

        event = Event(
            id="test_2", source="test",
            event_type=EventType.HACK_EXPLOIT,
            title="Exchange hacked",
            assets=[Asset(symbol="BTC", name="Bitcoin", asset_class=AssetClass.CRYPTO, price_at_event=50000.0)],
            urgency=Urgency.CRITICAL,
        )
        opinion = agent.analyze(event)
        assert opinion is not None
        assert opinion.recommendation in (Recommendation.AVOID, Recommendation.HEDGE)
        assert opinion.risk_score >= 0.5
        assert "security_breach" in str(opinion.evidence)

    def test_macro_event_risk(self, monkeypatch):
        agent = RiskAgent()

        def mock_fetch(*args, **kwargs):
            return None
        monkeypatch.setattr(agent, "_fetch_ohlcv", mock_fetch)

        event = Event(
            id="test_3", source="fred",
            event_type=EventType.MACRO_EVENT,
            title="Fed rate decision",
            assets=[Asset(symbol="SPY", name="S&P 500", asset_class=AssetClass.STOCK, price_at_event=450.0)],
            urgency=Urgency.HIGH,
        )
        opinion = agent.analyze(event)
        assert opinion is not None
        assert "macro_shock" in str(opinion.evidence) or "Event urgency" in str(opinion.evidence)

    def test_ohlcv_risk_calculation(self):
        agent = RiskAgent()
        prefs = agent._assess_scenario_risk(
            Event(id="t", source="t", event_type=EventType.GEOPOLITICAL, title="t",
                  urgency=Urgency.HIGH)
        )
        assert prefs["weight"] > 0
        assert prefs["label"] == "geopolitical_crisis"

    def test_batch_analysis(self, monkeypatch):
        agent = RiskAgent()
        events = [
            Event(id=f"batch_{i}", source="test",
                  event_type=EventType.PRICE_MOVEMENT,
                  title=f"Event {i}",
                  assets=[Asset(symbol="BTC", name="Bitcoin", asset_class=AssetClass.CRYPTO, price_at_event=50000.0)])
            for i in range(3)
        ]

        def mock_fetch(*args, **kwargs):
            return None
        monkeypatch.setattr(agent, "_fetch_ohlcv", mock_fetch)

        opinions = agent.analyze_batch(events)
        assert len(opinions) == 3
        for o in opinions:
            assert o.agent_role.value == "risk_analyst"
            assert o.risk_score > 0
