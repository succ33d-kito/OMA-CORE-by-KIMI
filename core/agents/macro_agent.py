"""OSIRIS Macro Agent — Analyzes macroeconomic events"""
from typing import List, Optional
from core.schemas.agent_schema import (
    AgentOpinion, AgentRole, Recommendation
)
from core.schemas.event_schema import Event, EventType
from core.event_bus import EventBus, EventTopic, bus as default_bus


class MacroAgent:
    def __init__(
        self,
        name: str = "macro_agent",
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
            EventType.MACRO_EVENT,
            EventType.EARNINGS,
            EventType.PRICE_MOVEMENT,
            EventType.MERGER_ACQUISITION,
        ):
            return None

        evidence = []
        impact_score = 0.4
        risk_score = 0.3

        macro_indicators = {
            "gdp": 0.9, "inflation": 0.85, "cpi": 0.85, "employment": 0.8,
            "unemployment": 0.8, "interest rate": 0.95, "fed": 0.9,
            "central bank": 0.9, "monetary policy": 0.85, "fiscal": 0.8,
            "treasury": 0.75, "yield": 0.7, "recession": 0.9,
            "expansion": 0.7, "manufacturing": 0.7, "services pmi": 0.7,
            "consumer confidence": 0.7, "retail sales": 0.7,
            "industrial production": 0.7, "trade balance": 0.6,
            "current account": 0.6, "debt": 0.7, "deficit": 0.7,
        }

        title_lower = event.title.lower()
        summary_lower = (event.summary or "").lower()
        combined_text = title_lower + " " + summary_lower

        matched_indicators = []
        for indicator, weight in macro_indicators.items():
            if indicator in combined_text:
                matched_indicators.append((indicator, weight))
                impact_score = max(impact_score, weight)

        if matched_indicators:
            top = sorted(matched_indicators, key=lambda x: -x[1])[:5]
            evidence.append(f"Macro indicators detected: {', '.join(i[0] for i in top)}")

        if "recession" in combined_text:
            base_recommendation = Recommendation.HEDGE
            risk_score = 0.8
            evidence.append("Recession signal — defensive positioning advised")
        elif event.sentiment_score > 0.3 or "expansion" in combined_text or "growth" in combined_text:
            base_recommendation = Recommendation.BUY
            risk_score = 0.3
            evidence.append("Expansion signal — risk-on environment")
        elif event.sentiment_score < -0.3:
            base_recommendation = Recommendation.HEDGE
            risk_score = 0.6
            evidence.append("Contraction signal — risk-off environment")
        else:
            base_recommendation = Recommendation.WATCH
            evidence.append("Neutral macro signal — monitoring")

        if event.event_type == EventType.EARNINGS:
            evidence.append("Earnings event — company-level fundamental shift")
            impact_score = max(impact_score, 0.5)
            if event.sentiment_score > 0.5:
                base_recommendation = Recommendation.BUY
            elif event.sentiment_score < -0.5:
                base_recommendation = Recommendation.SELL
                risk_score = 0.5

        if event.event_type == EventType.MERGER_ACQUISITION:
            evidence.append("M&A event — potential arbitrage opportunity")
            impact_score = max(impact_score, 0.6)
            base_recommendation = Recommendation.BUY
            risk_score = 0.5

        if event.event_type == EventType.PRICE_MOVEMENT:
            change = abs(event.sentiment_score)
            if change > 0.08:
                impact_score = max(impact_score, 0.7)
                risk_score = max(risk_score, 0.5)
                evidence.append(f"Significant price movement ({change*100:.1f}%) — structural shift possible")

        evidence.append(f"Source: {event.source} (confidence: {event.confidence})")
        evidence.append(f"Event type: {event.event_type.value}")

        if event.assets:
            evidence.append(f"Affected assets: {', '.join(a.symbol for a in event.assets)}")

        confidence = min(1.0, (event.confidence or 0.5) + 0.15)
        impact_score = min(1.0, impact_score + 0.1)
        risk_score = min(1.0, risk_score)

        return AgentOpinion(
            agent_name=self.name,
            agent_role=AgentRole.MACRO_ANALYST,
            confidence=round(confidence, 3),
            impact_score=round(impact_score, 3),
            risk_score=round(risk_score, 3),
            evidence=evidence,
            recommendation=base_recommendation,
            rationale=f"Macro event '{event.title[:80]}...' analysed. "
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
