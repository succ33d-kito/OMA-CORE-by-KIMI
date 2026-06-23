"""OSIRIS News Agent — Analyzes news events and produces structured opinions"""
from typing import List, Optional
from core.schemas.agent_schema import (
    AgentOpinion, AgentRole, Recommendation
)
from core.schemas.event_schema import Event, EventType
from core.event_bus import EventBus, EventTopic, bus as default_bus


class NewsAgent:
    def __init__(
        self,
        name: str = "news_agent",
        event_bus: Optional[EventBus] = None,
    ):
        self.name = name
        self.bus = event_bus or default_bus
        self.processed_count = 0
        self.bus.subscribe(EventTopic.EVENTS_RAW, self.on_event)

    def on_event(self, event_data: dict) -> None:
        event = Event.from_dict(event_data)
        opinion = self.analyze(event)
        if opinion:
            self.bus.publish(EventTopic.OPINIONS_AGENT, opinion.to_dict(), source=self.name)
            self.processed_count += 1

    def analyze(self, event: Event) -> Optional[AgentOpinion]:
        if event.event_type not in (
            EventType.NEWS,
            EventType.GEOPOLITICAL,
            EventType.REGULATORY,
            EventType.HACK_EXPLOIT,
            EventType.SOCIAL_TREND,
        ):
            return None

        evidence = []
        urgency_weight = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2, "background": 0.0}
        urgency_key = event.urgency.name.lower()

        impact_score = 0.5
        risk_score = 0.3

        geopolitical_keywords = {"sanctions", "war", "conflict", "invasion", "tariff", "trade war",
                                 "military", "terrorism", "geopolitical", "embargo"}
        regulatory_keywords = {"regulation", "sec", "cfpb", "cftc", "ban", "legal", "compliance",
                               "law", "bill", "act", "policy", "restriction", "approved", "rejected"}
        hack_keywords = {"hack", "exploit", "breach", "attack", "ransomware", "phishing",
                         "vulnerability", "cyber", "malware", "data leak"}

        title_lower = event.title.lower()
        summary_lower = (event.summary or "").lower()

        if "bullish" in event.keywords or event.sentiment_score > 0.3:
            base_recommendation = Recommendation.BUY
        elif "bearish" in event.keywords or event.sentiment_score < -0.3:
            base_recommendation = Recommendation.SELL
        else:
            base_recommendation = Recommendation.WATCH

        if any(kw in title_lower for kw in hack_keywords):
            impact_score = 0.8
            risk_score = 0.9
            base_recommendation = Recommendation.AVOID
            evidence.append("Security event detected — high risk of value compromise")
        elif any(kw in title_lower for kw in geopolitical_keywords):
            impact_score = 0.7
            risk_score = 0.7
            evidence.append("Geopolitical tension detected — market uncertainty")
        elif any(kw in title_lower for kw in regulatory_keywords):
            impact_score = 0.6
            risk_score = 0.5
            evidence.append("Regulatory event — compliance risk or tailwind")
        elif event.sentiment_score > 0.5:
            impact_score = 0.6
            evidence.append(f"Strong {'bullish' if event.sentiment_score > 0 else 'bearish'} sentiment detected")
        elif event.sentiment_score < -0.5:
            impact_score = 0.6
            risk_score = 0.6

        evidence.append(f"Source: {event.source} (confidence: {event.confidence})")
        evidence.append(f"Event type: {event.event_type.value}")
        evidence.append(f"Urgency: {event.urgency.name}")

        keywords_used = event.keywords[:5]

        clean_keywords = []
        for kw in keywords_used:
            if isinstance(kw, str):
                clean_keywords.append(kw)
            elif isinstance(kw, dict):
                clean_keywords.append(str(kw.get("symbol") or kw.get("name") or kw))
            else:
                clean_keywords.append(str(kw))

        if clean_keywords:
            evidence.append(f"Keywords: {', '.join(clean_keywords)}")

        confidence = min(1.0, (event.confidence or 0.5) + urgency_weight.get(urgency_key, 0.3) * 0.3)
        impact_score = min(1.0, impact_score + urgency_weight.get(urgency_key, 0.3) * 0.2)
        risk_score = min(1.0, risk_score + (0.2 if base_recommendation in (Recommendation.SELL, Recommendation.AVOID) else 0))

        if event.assets:
            evidence.append(f"Affected assets: {', '.join(a.symbol for a in event.assets)}")

        return AgentOpinion(
            agent_name=self.name,
            agent_role=AgentRole.NEWS_ANALYST,
            confidence=round(confidence, 3),
            impact_score=round(impact_score, 3),
            risk_score=round(risk_score, 3),
            evidence=evidence,
            recommendation=base_recommendation,
            rationale=f"News event '{event.title[:80]}...' analyzed. "
                      f"Impact: {impact_score:.2f}, Risk: {risk_score:.2f}. "
                      f"Recommendation: {base_recommendation.value}.",
            event_id=event.id,
        )

    def analyze_batch(self, events: List[Event]) -> List[AgentOpinion]:
        opinions = []
        for event in events:
            opinion = self.analyze(event)
            if opinion:
                opinions.append(opinion)
                self.processed_count += 1
        return opinions
