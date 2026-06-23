"""Tests for OSIRIS Agent Council"""
import pytest
from core.council import AgentCouncil, MetaCouncil
from core.schemas.agent_schema import (
    AgentOpinion, AgentRole, Recommendation, CouncilTier,
)


class TestAgentCouncil:
    def test_submit_and_decide(self):
        council = AgentCouncil()
        opinion = AgentOpinion(
            agent_name="news_agent", agent_role=AgentRole.NEWS_ANALYST,
            confidence=0.85, impact_score=0.7, risk_score=0.3,
            evidence=["Key evidence"], recommendation=Recommendation.BUY,
            rationale="Bullish signal", event_id="evt_test_1",
        )
        council.submit_opinion(opinion)
        decision = council.decide("evt_test_1")

        assert decision is not None
        assert decision.event_id == "evt_test_1"
        assert decision.conviction > 0
        assert decision.consensus_score == 0.0
        assert len(decision.opinions) == 1

    def test_multiple_opinions_consensus(self):
        council = AgentCouncil()
        event_id = "evt_test_2"
        opinions_data = [
            ("agent_a", 0.9, 0.8, 0.2, Recommendation.BUY),
            ("agent_b", 0.8, 0.7, 0.3, Recommendation.BUY),
            ("agent_c", 0.6, 0.5, 0.5, Recommendation.HOLD),
        ]
        for name, conf, impact, risk, rec in opinions_data:
            council.submit_opinion(AgentOpinion(
                agent_name=name, agent_role=AgentRole.MARKET_ANALYST,
                confidence=conf, impact_score=impact, risk_score=risk,
                evidence=["test"], recommendation=rec,
                rationale="test", event_id=event_id,
            ))

        decision = council.decide(event_id)
        assert decision is not None
        assert decision.action == Recommendation.BUY
        assert decision.conviction > 50
        assert decision.disagreement_score >= 0

    def test_no_opinions(self):
        council = AgentCouncil()
        decision = council.decide("non_existent_event")
        assert decision is None


class TestMetaCouncil:
    def test_meta_council_decision(self):
        council = AgentCouncil()
        meta = MetaCouncil()
        event_id = "evt_meta_1"

        opinion = AgentOpinion(
            agent_name="macro_agent", agent_role=AgentRole.MACRO_ANALYST,
            confidence=0.85, impact_score=0.75, risk_score=0.25,
            evidence=["GDP growth"], recommendation=Recommendation.BUY,
            rationale="Expansion cycle", event_id=event_id,
        )
        council.submit_opinion(opinion)
        decision = council.decide(event_id)
        assert decision is not None

        meta_decision = meta.decide_best_profile(event_id, decision.opinions)
        assert meta_decision.event_id == event_id
        assert meta_decision.best_profile in ("trader", "entrepreneur", "creator")
        assert meta_decision.meta_conviction > 0
        assert meta_decision.trader is not None
        assert meta_decision.entrepreneur is not None
        assert meta_decision.creator is not None
