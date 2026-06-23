"""OSIRIS Agent Communication Protocol (ACP)"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum


class AgentRole(Enum):
    NEWS_ANALYST = "news_analyst"
    MACRO_ANALYST = "macro_analyst"
    MARKET_ANALYST = "market_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    RISK_ANALYST = "risk_analyst"
    CORRELATION_ANALYST = "correlation_analyst"
    RESEARCH_ANALYST = "research_analyst"
    ENTREPRENEUR_ANALYST = "entrepreneur_analyst"
    CREATOR_ANALYST = "creator_analyst"
    MEMORY_ANALYST = "memory_analyst"
    EXECUTION_ANALYST = "execution_analyst"


class CouncilTier(Enum):
    AGENT_COUNCIL = "agent_council"
    META_COUNCIL = "meta_council"


class Recommendation(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    WATCH = "watch"
    AVOID = "avoid"
    HEDGE = "hedge"
    NO_ACTION = "no_action"


@dataclass
class AgentOpinion:
    agent_name: str
    agent_role: AgentRole
    confidence: float
    impact_score: float
    risk_score: float
    evidence: List[str]
    recommendation: Recommendation
    rationale: str
    event_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role.value,
            "confidence": self.confidence,
            "impact_score": self.impact_score,
            "risk_score": self.risk_score,
            "evidence": self.evidence,
            "recommendation": self.recommendation.value,
            "rationale": self.rationale,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentOpinion":
        return cls(
            agent_name=data["agent_name"],
            agent_role=AgentRole(data["agent_role"]),
            confidence=data["confidence"],
            impact_score=data["impact_score"],
            risk_score=data["risk_score"],
            evidence=data["evidence"],
            recommendation=Recommendation(data["recommendation"]),
            rationale=data["rationale"],
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CouncilDecision:
    event_id: str
    council_tier: CouncilTier
    conviction: float
    consensus_score: float
    disagreement_score: float
    rationale: str
    action: Recommendation
    opinions: List[AgentOpinion]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "council_tier": self.council_tier.value,
            "conviction": self.conviction,
            "consensus_score": self.consensus_score,
            "disagreement_score": self.disagreement_score,
            "rationale": self.rationale,
            "action": self.action.value,
            "opinions": [o.to_dict() for o in self.opinions],
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CouncilDecision":
        return cls(
            event_id=data["event_id"],
            council_tier=CouncilTier(data["council_tier"]),
            conviction=data["conviction"],
            consensus_score=data["consensus_score"],
            disagreement_score=data["disagreement_score"],
            rationale=data["rationale"],
            action=Recommendation(data["action"]),
            opinions=[AgentOpinion.from_dict(o) for o in data["opinions"]],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )
