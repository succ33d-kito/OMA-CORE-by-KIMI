"""OSIRIS Agent Council — Consensus Engine v2
Changes from v1:
- Track record weighting: agents with higher historical accuracy get more vote weight
- Minimum 2 opinions for consensus_score > 0
- risk_score now weights 25% in conviction (was 10%)
- Weighted vote by confidence x track record (not naive majority)
- TradeSignal parameters in metadata
"""
from typing import List, Optional, Dict
from statistics import mean, stdev
from collections import defaultdict
from core.schemas.agent_schema import (
    AgentOpinion, CouncilDecision, CouncilTier, Recommendation
)
from core.schemas.trade_schema import DIRECTION_MAP
from core.event_bus import EventBus, EventTopic


class AgentCouncil:
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.bus = event_bus or EventBus()
        self._opinions: dict = {}
        self._track_record: Dict[str, float] = {}

    def submit_opinion(self, opinion: AgentOpinion) -> None:
        event_id = opinion.event_id
        if event_id not in self._opinions:
            self._opinions[event_id] = []
        self._opinions[event_id].append(opinion)
        if self.bus:
            self.bus.publish(EventTopic.OPINIONS_AGENT, opinion.to_dict(), source=opinion.agent_name)

    def get_opinions(self, event_id: str) -> List[AgentOpinion]:
        return self._opinions.get(event_id, [])

    def update_track_record(self, agent_name: str, was_correct: bool) -> None:
        alpha = 0.1
        current = self._track_record.get(agent_name, 0.5)
        self._track_record[agent_name] = current + alpha * (1.0 if was_correct else 0.0 - current)

    def get_track_record(self, agent_name: str) -> float:
        return self._track_record.get(agent_name, 0.5)

    def decide(self, event_id: str) -> Optional[CouncilDecision]:
        opinions = self._opinions.get(event_id, [])
        if not opinions:
            return None

        n = len(opinions)
        confidences = [o.confidence for o in opinions]
        impact_scores = [o.impact_score for o in opinions]
        risk_scores = [o.risk_score for o in opinions]

        weights = []
        for o in opinions:
            track = self.get_track_record(o.agent_name)
            weights.append(o.confidence * track)

        weight_sum = sum(weights) if sum(weights) > 0 else 1.0
        norm_weights = [w / weight_sum for w in weights]

        weighted_confidence = sum(c * w for c, w in zip(confidences, norm_weights))
        weighted_impact = sum(i * w for i, w in zip(impact_scores, norm_weights))
        weighted_risk = sum(r * w for r, w in zip(risk_scores, norm_weights))

        avg_confidence = mean(confidences)
        avg_impact = mean(impact_scores)
        avg_risk = mean(risk_scores)

        if n >= 2:
            consensus_score = max(0, 100 - stdev(confidences) * 20)
            disagreement_score = stdev(confidences) * 20
        else:
            consensus_score = 0.0
            disagreement_score = 0.0

        conviction = min(100,
            weighted_impact * 25 +
            weighted_confidence * 30 +
            (1 - weighted_risk) * 25 +
            (consensus_score / 100) * 20
        )

        neutral_recs = {Recommendation.WATCH, Recommendation.HOLD, Recommendation.NO_ACTION}
        rec_scores = defaultdict(float)
        for o, w in zip(opinions, norm_weights):
            rec_scores[o.recommendation] += w

        actionable = {k: v for k, v in rec_scores.items() if k not in neutral_recs}
        if actionable:
            majority_rec = max(actionable, key=actionable.get)
            action_conviction = actionable[majority_rec]
        else:
            majority_rec = max(rec_scores, key=rec_scores.get)
            action_conviction = rec_scores[majority_rec]

        action = majority_rec

        avg_agent_record = mean([self.get_track_record(o.agent_name) for o in opinions])
        conviction = conviction * (0.8 + 0.2 * avg_agent_record)

        conf_interval = (1.96 * stdev(confidences) / (n ** 0.5)) if n >= 2 else 0.5
        lower_bound = max(0, avg_confidence - conf_interval)
        upper_bound = min(1, avg_confidence + conf_interval)

        rationale_parts = [
            f"Council analysed {n} opinions on event {event_id}.",
            f"Weighted recommendation: {action.value} ({action_conviction*100:.0f}% weighted support).",
            f"Weighted confidence: {weighted_confidence:.2f} (range: {lower_bound:.2f}-{upper_bound:.2f}).",
            f"Average impact: {avg_impact:.2f}, Average risk: {avg_risk:.2f}.",
            f"Consensus score: {consensus_score:.1f}, Disagreement: {disagreement_score:.1f}.",
        ]

        evidencers = defaultdict(list)
        for o in opinions:
            for e in o.evidence:
                evidencers[e].append(o.agent_name)
        top_evidence = sorted(evidencers.items(), key=lambda x: -len(x[1]))[:5]
        if top_evidence:
            rationale_parts.append("Key evidence: " + "; ".join(
                f"'{e}' (cited by {', '.join(agents)})" for e, agents in top_evidence
            ))

        metadata = {
            "weighted_confidence": round(weighted_confidence, 3),
            "weighted_impact": round(weighted_impact, 3),
            "weighted_risk": round(weighted_risk, 3),
            "confidence_ci_95_lower": round(lower_bound, 3),
            "confidence_ci_95_upper": round(upper_bound, 3),
            "n_opinions": n,
            "agent_weights": {o.agent_name: round(w, 3) for o, w in zip(opinions, norm_weights)},
            "track_records": {o.agent_name: round(self.get_track_record(o.agent_name), 3) for o in opinions},
            "rec_scores": {k.value: round(v, 3) for k, v in rec_scores.items()},
        }

        direction = DIRECTION_MAP.get(action, None)
        if direction and direction.value != "flat" and opinions[0].metadata:
            if "price" in opinions[0].metadata:
                metadata["entry_price"] = opinions[0].metadata["price"]
            if "atr_14" in opinions[0].metadata:
                atr = opinions[0].metadata["atr_14"]
                price = opinions[0].metadata.get("price", 0)
                if price > 0:
                    metadata["suggested_stop_pct"] = round(atr / price * 100 * 1.5, 2)

        decision = CouncilDecision(
            event_id=event_id,
            council_tier=CouncilTier.AGENT_COUNCIL,
            conviction=round(conviction, 2),
            consensus_score=round(consensus_score, 2),
            disagreement_score=round(disagreement_score, 2),
            rationale="\n".join(rationale_parts),
            action=action,
            opinions=opinions,
            metadata=metadata,
        )

        if self.bus:
            self.bus.publish(EventTopic.DECISIONS_COUNCIL, decision.to_dict(), source="agent_council")

        return decision

    def clear_event(self, event_id: str) -> None:
        self._opinions.pop(event_id, None)
