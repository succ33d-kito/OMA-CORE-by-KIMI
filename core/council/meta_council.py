"""OSIRIS Meta Council — Cross-profile comparison engine"""
from typing import List, Optional
from statistics import mean, stdev
from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.schemas.agent_schema import (
    AgentOpinion, CouncilDecision, CouncilTier, Recommendation, AgentRole
)
from core.event_bus import EventBus, EventTopic


@dataclass
class ProfileOpportunity:
    profile_type: str
    conviction: float
    action: Recommendation
    rationale: str
    opinion: AgentOpinion
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MetaCouncilDecision:
    event_id: str
    trader: Optional[ProfileOpportunity]
    entrepreneur: Optional[ProfileOpportunity]
    creator: Optional[ProfileOpportunity]
    best_profile: str
    meta_conviction: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "trader": self.trader.__dict__ if self.trader else None,
            "entrepreneur": self.entrepreneur.__dict__ if self.entrepreneur else None,
            "creator": self.creator.__dict__ if self.creator else None,
            "best_profile": self.best_profile,
            "meta_conviction": self.meta_conviction,
            "timestamp": self.timestamp.isoformat(),
        }


class MetaCouncil:
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.bus = event_bus
        self._profile_opinions: dict = {}

    def evaluate_for_profile(
        self,
        opinion: AgentOpinion,
        profile_type: str,
    ) -> ProfileOpportunity:
        profile_multipliers = {
            "trader": 1.0,
            "entrepreneur": 0.7,
            "creator": 0.5,
        }
        trader_weight = profile_multipliers.get(profile_type, 0.5)

        conviction = min(100, opinion.confidence * 40 +
                         opinion.impact_score * 30 +
                         (1 - opinion.risk_score) * 10 +
                         trader_weight * 20)

        rationale = (
            f"[{profile_type.upper()}] Agent '{opinion.agent_name}' recommends {opinion.recommendation.value}. "
            f"Conviction: {conviction:.1f}. "
            f"Impact: {opinion.impact_score:.2f}, Risk: {opinion.risk_score:.2f}."
        )

        return ProfileOpportunity(
            profile_type=profile_type,
            conviction=round(conviction, 2),
            action=opinion.recommendation,
            rationale=rationale,
            opinion=opinion,
        )

    def decide_best_profile(
        self,
        event_id: str,
        opinions: List[AgentOpinion],
    ) -> MetaCouncilDecision:
        trader_opps = []
        entrepreneur_opps = []
        creator_opps = []

        for opinion in opinions:
            base = self.evaluate_for_profile(opinion, "trader")
            trader_opps.append(base)
            base_entrepreneur = ProfileOpportunity(
                profile_type="entrepreneur",
                conviction=round(base.conviction * 0.7, 2),
                action=base.action,
                rationale=base.rationale.replace("TRADER", "ENTREPRENEUR"),
                opinion=base.opinion,
            )
            entrepreneur_opps.append(base_entrepreneur)
            base_creator = ProfileOpportunity(
                profile_type="creator",
                conviction=round(base.conviction * 0.5, 2),
                action=base.action,
                rationale=base.rationale.replace("TRADER", "CREATOR"),
                opinion=base.opinion,
            )
            creator_opps.append(base_creator)

        best_trader = max(trader_opps, key=lambda x: x.conviction) if trader_opps else None
        best_entrepreneur = max(entrepreneur_opps, key=lambda x: x.conviction) if entrepreneur_opps else None
        best_creator = max(creator_opps, key=lambda x: x.conviction) if creator_opps else None

        profile_scores = [
            ("trader", best_trader.conviction if best_trader else 0),
            ("entrepreneur", best_entrepreneur.conviction if best_entrepreneur else 0),
            ("creator", best_creator.conviction if best_creator else 0),
        ]
        best_profile = max(profile_scores, key=lambda x: x[1])[0]
        meta_conviction = max(s for _, s in profile_scores)

        decision = MetaCouncilDecision(
            event_id=event_id,
            trader=best_trader,
            entrepreneur=best_entrepreneur,
            creator=best_creator,
            best_profile=best_profile,
            meta_conviction=meta_conviction,
        )

        if self.bus:
            self.bus.publish(
                EventTopic.DECISIONS_COUNCIL,
                decision.to_dict(),
                source="meta_council",
            )

        return decision
