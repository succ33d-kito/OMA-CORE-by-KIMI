"""Tests for OSIRIS Agent Communication Protocol"""
import pytest
from datetime import datetime, timezone
from core.schemas.agent_schema import (
    AgentOpinion, CouncilDecision, AgentRole, CouncilTier, Recommendation,
)


class TestAgentOpinion:
    def test_create_opinion(self):
        opinion = AgentOpinion(
            agent_name="test_agent",
            agent_role=AgentRole.NEWS_ANALYST,
            confidence=0.85,
            impact_score=0.7,
            risk_score=0.3,
            evidence=["Source A reported X", "Market reacted Y"],
            recommendation=Recommendation.BUY,
            rationale="Strong bullish signal detected",
            event_id="evt_12345",
        )
        assert opinion.agent_name == "test_agent"
        assert opinion.confidence == 0.85
        assert opinion.recommendation == Recommendation.BUY

    def test_serialization_roundtrip(self):
        opinion = AgentOpinion(
            agent_name="trader_bot",
            agent_role=AgentRole.MARKET_ANALYST,
            confidence=0.92,
            impact_score=0.8,
            risk_score=0.2,
            evidence=["Price breakout detected"],
            recommendation=Recommendation.STRONG_BUY,
            rationale="Bull flag pattern confirmed",
            event_id="evt_999",
        )
        data = opinion.to_dict()
        restored = AgentOpinion.from_dict(data)
        assert restored.agent_name == opinion.agent_name
        assert restored.agent_role == opinion.agent_role
        assert restored.confidence == opinion.confidence
        assert restored.recommendation == opinion.recommendation
        assert restored.event_id == opinion.event_id


class TestCouncilDecision:
    def test_create_decision(self):
        opinions = [
            AgentOpinion(
                agent_name="agent_a", agent_role=AgentRole.NEWS_ANALYST,
                confidence=0.8, impact_score=0.7, risk_score=0.3,
                evidence=["News break"], recommendation=Recommendation.BUY,
                rationale="Positive news", event_id="evt_1",
            ),
            AgentOpinion(
                agent_name="agent_b", agent_role=AgentRole.MACRO_ANALYST,
                confidence=0.6, impact_score=0.5, risk_score=0.4,
                evidence=["Macro data"], recommendation=Recommendation.HOLD,
                rationale="Mixed signals", event_id="evt_1",
            ),
        ]
        decision = CouncilDecision(
            event_id="evt_1",
            council_tier=CouncilTier.AGENT_COUNCIL,
            conviction=72.5,
            consensus_score=85.0,
            disagreement_score=15.0,
            rationale="Consensus reached",
            action=Recommendation.BUY,
            opinions=opinions,
        )
        assert decision.conviction == 72.5
        assert len(decision.opinions) == 2
        assert decision.action == Recommendation.BUY

    def test_decision_serialization(self):
        opinion = AgentOpinion(
            agent_name="x", agent_role=AgentRole.RISK_ANALYST,
            confidence=0.7, impact_score=0.6, risk_score=0.8,
            evidence=["High volatility"], recommendation=Recommendation.AVOID,
            rationale="Too risky", event_id="evt_2",
        )
        decision = CouncilDecision(
            event_id="evt_2", council_tier=CouncilTier.META_COUNCIL,
            conviction=45.0, consensus_score=60.0, disagreement_score=40.0,
            rationale="Disagreement on risk assessment",
            action=Recommendation.WATCH, opinions=[opinion],
        )
        data = decision.to_dict()
        restored = CouncilDecision.from_dict(data)
        assert restored.event_id == decision.event_id
        assert restored.council_tier == decision.council_tier
        assert restored.conviction == decision.conviction
        assert len(restored.opinions) == 1
        assert restored.opinions[0].agent_name == "x"
