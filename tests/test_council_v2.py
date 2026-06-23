"""Tests for OSIRIS Agent Council v2 — track record, weighted voting"""
import pytest
from core.council import AgentCouncil
from core.schemas.agent_schema import (
    AgentOpinion, AgentRole, Recommendation,
)


class TestCouncilV2:
    def test_track_record_weighting(self):
        council = AgentCouncil()
        council.update_track_record("good_agent", True)
        council.update_track_record("good_agent", True)
        council.update_track_record("good_agent", True)
        council.update_track_record("bad_agent", False)
        council.update_track_record("bad_agent", False)

        good_record = council.get_track_record("good_agent")
        bad_record = council.get_track_record("bad_agent")
        assert good_record > bad_record

    def test_min_opinions_consensus(self):
        council = AgentCouncil()
        opinion = AgentOpinion(
            agent_name="single", agent_role=AgentRole.NEWS_ANALYST,
            confidence=0.9, impact_score=0.8, risk_score=0.2,
            evidence=["test"], recommendation=Recommendation.BUY,
            rationale="test", event_id="evt_single",
        )
        council.submit_opinion(opinion)
        decision = council.decide("evt_single")
        assert decision is not None
        assert decision.consensus_score == 0.0

    def test_weighted_majority_overturns_naive(self):
        council = AgentCouncil()
        council.update_track_record("high_confidence", True)
        council.update_track_record("high_confidence", True)
        council.update_track_record("high_confidence", True)
        council.update_track_record("low_confidence", False)
        council.update_track_record("low_confidence", False)

        event_id = "evt_weight"
        council.submit_opinion(AgentOpinion(
            agent_name="high_confidence", agent_role=AgentRole.MARKET_ANALYST,
            confidence=0.9, impact_score=0.8, risk_score=0.2,
            evidence=["Strong signal"], recommendation=Recommendation.SELL,
            rationale="Bearish", event_id=event_id,
        ))
        for i in range(3):
            council.submit_opinion(AgentOpinion(
                agent_name="low_confidence", agent_role=AgentRole.NEWS_ANALYST,
                confidence=0.3, impact_score=0.2, risk_score=0.5,
                evidence=["Weak signal"], recommendation=Recommendation.BUY,
                rationale="Bullish", event_id=event_id,
            ))

        decision = council.decide(event_id)
        assert decision is not None
        assert decision.action == Recommendation.SELL

    def test_risk_weights_in_conviction(self):
        council = AgentCouncil()
        event_id = "evt_risk"
        council.submit_opinion(AgentOpinion(
            agent_name="risk_averse", agent_role=AgentRole.RISK_ANALYST,
            confidence=0.8, impact_score=0.3, risk_score=0.9,
            evidence=["High risk"], recommendation=Recommendation.AVOID,
            rationale="Too risky", event_id=event_id,
        ))
        council.submit_opinion(AgentOpinion(
            agent_name="risk_taker", agent_role=AgentRole.MARKET_ANALYST,
            confidence=0.8, impact_score=0.7, risk_score=0.2,
            evidence=["Good setup"], recommendation=Recommendation.BUY,
            rationale="Bullish", event_id=event_id,
        ))
        decision = council.decide(event_id)
        assert decision is not None
        assert decision.metadata["weighted_risk"] > 0.3

    def test_trade_metadata_in_decision(self):
        council = AgentCouncil()
        event_id = "evt_meta"
        council.submit_opinion(AgentOpinion(
            agent_name="market", agent_role=AgentRole.MARKET_ANALYST,
            confidence=0.8, impact_score=0.7, risk_score=0.3,
            evidence=["Price at 50000"], recommendation=Recommendation.BUY,
            rationale="Bullish", event_id=event_id,
            metadata={"symbol": "BTC", "price": 50000.0, "atr_14": 800.0},
        ))
        decision = council.decide(event_id)
        assert decision is not None
        assert decision.metadata.get("entry_price") == 50000.0
        assert decision.metadata.get("suggested_stop_pct") is not None
