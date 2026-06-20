"""O.M.A.-C.O.R.E. Polymarket Collector (Prediction Markets)"""
import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict
from core.collectors.base_collector import BaseCollector
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency

class PolymarketCollector(BaseCollector):
    GAMMA_API = "https://gamma-api.polymarket.com"
    CLOB_API = "https://clob.polymarket.com"
    DATA_API = "https://data-api.polymarket.com"
    RELEVANT_TAGS = [
        "crypto", "bitcoin", "ethereum", "cryptocurrency",
        "politics", "elections", "trump", "biden",
        "economy", "fed", "inflation", "recession", "interest-rates",
        "geopolitics", "war", "ukraine", "israel", "china",
        "technology", "ai", "artificial-intelligence", "regulation",
    ]
    PRICE_CHANGE_THRESHOLD = 5.0
    VOLUME_THRESHOLD = 100000
    LIQUIDITY_THRESHOLD = 50000

    def __init__(self):
        super().__init__("polymarket", source_confidence=0.88)

    def collect(self) -> List[Event]:
        events = []
        markets = self._get_active_markets()
        if markets:
            events.extend(self._process_markets(markets))
        polymarket_events = self._get_active_events()
        if polymarket_events:
            events.extend(self._process_events(polymarket_events))
        high_volume = self._get_high_volume_markets()
        if high_volume:
            events.extend(self._process_high_volume(high_volume))
        self.stats["events_generated"] += len(events)
        self.stats["last_run"] = datetime.now(timezone.utc).isoformat()
        return events

    def _get_active_markets(self, limit: int = 50) -> Optional[List[dict]]:
        result = self._make_request(f"{self.GAMMA_API}/markets/keyset", {"limit": limit, "active": "true", "closed": "false"})
        if result and "markets" in result:
            return result["markets"]
        result = self._make_request(f"{self.GAMMA_API}/markets", {"limit": limit, "active": "true", "closed": "false"})
        return result if isinstance(result, list) else None

    def _get_active_events(self, limit: int = 20) -> Optional[List[dict]]:
        result = self._make_request(f"{self.GAMMA_API}/events", {"limit": limit, "active": "true", "closed": "false"})
        return result if isinstance(result, list) else None

    def _get_high_volume_markets(self, limit: int = 20) -> Optional[List[dict]]:
        result = self._make_request(f"{self.GAMMA_API}/markets", {"limit": limit, "active": "true", "order": "volume", "closed": "false"})
        return result if isinstance(result, list) else None

    def _is_relevant_market(self, market: dict) -> bool:
        tags = market.get("tags", [])
        if isinstance(tags, list):
            tags_lower = [t.lower() if isinstance(t, str) else "" for t in tags]
        else:
            tags_lower = []
        return any(tag in tags_lower for tag in self.RELEVANT_TAGS)

    def _process_markets(self, markets: List[dict]) -> List[Event]:
        events = []
        for market in markets:
            try:
                if not self._is_relevant_market(market):
                    continue
                question = market.get("question", "")
                slug = market.get("slug", "")
                market_id = market.get("id", "")
                condition_id = market.get("conditionId", "")
                outcome_prices_raw = market.get("outcomePrices", "[]")
                try:
                    outcome_prices = json.loads(outcome_prices_raw) if isinstance(outcome_prices_raw, str) else outcome_prices_raw
                except:
                    outcome_prices = []
                outcomes = market.get("outcomes", [])
                volume = float(market.get("volume", 0) or 0)
                liquidity = float(market.get("liquidity", 0) or 0)
                if volume < self.VOLUME_THRESHOLD or liquidity < self.LIQUIDITY_THRESHOLD:
                    continue
                event_type, sentiment, sentiment_score, urgency = self._classify_market(question, outcomes, outcome_prices, market)
                symbol = f"PM-{slug[:20]}" if slug else f"PM-{market_id[:8]}"
                asset = Asset(symbol=symbol, name=question[:50], asset_class=AssetClass.INDEX, price_at_event=outcome_prices[0] if outcome_prices else None, currency="USD")
                events.append(Event(
                    id=str(uuid.uuid4()), source="polymarket",
                    source_url=f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com",
                    source_id=market_id, event_type=event_type,
                    title=f"[Polymarket] {question[:100]}",
                    summary=f"Mercado de predicción: {question}. Volumen: ${volume:,.0f}. Liquidez: ${liquidity:,.0f}. Outcomes: {', '.join(outcomes[:3]) if outcomes else 'N/A'}.",
                    timestamp=datetime.now(timezone.utc),
                    assets=[asset],
                    keywords=["polymarket", "prediction-market"] + market.get("tags", [])[:5],
                    sentiment=sentiment, sentiment_score=sentiment_score,
                    urgency=urgency, confidence=0.88,
                    metadata={
                        "market_id": market_id, "condition_id": condition_id, "slug": slug,
                        "question": question, "outcomes": outcomes, "outcome_prices": outcome_prices,
                        "volume": volume, "liquidity": liquidity, "tags": market.get("tags", []),
                        "end_date": market.get("endDate"), "resolution_source": market.get("resolutionSource"),
                        "volume_24h": market.get("volume24hr", 0), "spread": market.get("spread", 0),
                    }
                ))
            except Exception as e:
                print(f"[polymarket] Error procesando mercado: {e}")
                continue
        return events

    def _process_events(self, polymarket_events: List[dict]) -> List[Event]:
        events = []
        for event in polymarket_events:
            try:
                event_id = event.get("id", "")
                title = event.get("title", "")
                description = event.get("description", "")
                markets = event.get("markets", [])
                if not markets:
                    continue
                total_volume = sum(float(m.get("volume", 0) or 0) for m in markets)
                total_liquidity = sum(float(m.get("liquidity", 0) or 0) for m in markets)
                if total_volume < self.VOLUME_THRESHOLD:
                    continue
                event_type = self._classify_event_type(title)
                events.append(Event(
                    id=str(uuid.uuid4()), source="polymarket",
                    source_url=f"https://polymarket.com/event/{event_id}",
                    source_id=event_id, event_type=event_type,
                    title=f"[Polymarket Event] {title[:100]}",
                    summary=f"Evento de predicción con {len(markets)} mercados. Volumen total: ${total_volume:,.0f}. {description[:200] if description else ''}",
                    timestamp=datetime.now(timezone.utc),
                    assets=[Asset(symbol=f"PM-EVT-{event_id[:8]}", name=title[:50], asset_class=AssetClass.INDEX, currency="USD")],
                    keywords=["polymarket", "event", "prediction"] + event.get("tags", [])[:5],
                    sentiment=Sentiment.NEUTRAL, sentiment_score=0.0,
                    urgency=Urgency.MEDIUM, confidence=0.85,
                    metadata={
                        "event_id": event_id, "title": title, "description": description,
                        "markets_count": len(markets), "total_volume": total_volume,
                        "total_liquidity": total_liquidity, "tags": event.get("tags", []),
                        "end_date": event.get("endDate"),
                    }
                ))
            except Exception as e:
                print(f"[polymarket] Error procesando evento: {e}")
                continue
        return events

    def _process_high_volume(self, markets: List[dict]) -> List[Event]:
        events = []
        for market in markets[:5]:
            try:
                if not self._is_relevant_market(market):
                    continue
                question = market.get("question", "")
                volume = float(market.get("volume", 0) or 0)
                if volume < 500000:
                    continue
                events.append(Event(
                    id=str(uuid.uuid4()), source="polymarket",
                    source_url=f"https://polymarket.com/event/{market.get('slug', '')}",
                    source_id=market.get("id", ""), event_type=EventType.SENTIMENT_SHIFT,
                    title=f"[High Volume Consensus] {question[:80]}",
                    summary=f"Mercado de alto volumen (${volume:,.0f}) en Polymarket. Fuerte consenso del mercado de predicción.",
                    timestamp=datetime.now(timezone.utc),
                    assets=[Asset(symbol=f"PM-HV-{market.get('id', '')[:8]}", name=question[:50], asset_class=AssetClass.INDEX, currency="USD")],
                    keywords=["polymarket", "high-volume", "consensus", "prediction"],
                    sentiment=Sentiment.BULLISH, sentiment_score=0.5,
                    urgency=Urgency.MEDIUM, confidence=0.90,
                    metadata={"market_id": market.get("id", ""), "volume": volume, "liquidity": market.get("liquidity", 0), "type": "high_volume_consensus"}
                ))
            except Exception as e:
                continue
        return events

    def _classify_market(self, question: str, outcomes: List[str], prices: List[float], market: dict) -> tuple:
        question_lower = question.lower()
        if any(w in question_lower for w in ["election", "vote", "president", "senate", "congress", "trump", "biden"]):
            event_type = EventType.GEOPOLITICAL
        elif any(w in question_lower for w in ["war", "ukraine", "israel", "china", "taiwan", "sanctions", "nato"]):
            event_type = EventType.GEOPOLITICAL
        elif any(w in question_lower for w in ["fed", "interest rate", "inflation", "recession", "gdp", "unemployment", "cpi", "pce"]):
            event_type = EventType.MACRO_EVENT
        elif any(w in question_lower for w in ["crypto", "bitcoin", "ethereum", "btc", "eth", "etf", "sec", "regulation"]):
            event_type = EventType.REGULATORY
        elif any(w in question_lower for w in ["ai", "artificial intelligence", "chatgpt", "openai", "technology"]):
            event_type = EventType.NEWS
        else:
            event_type = EventType.NEWS

        sentiment = Sentiment.NEUTRAL
        sentiment_score = 0.0
        if prices and len(prices) >= 2:
            prob = float(prices[0]) if prices[0] else 0.5
            if prob > 0.7:
                sentiment = Sentiment.BULLISH
                sentiment_score = (prob - 0.5) * 2
            elif prob < 0.3:
                sentiment = Sentiment.BEARISH
                sentiment_score = (prob - 0.5) * 2
            else:
                sentiment = Sentiment.NEUTRAL
                sentiment_score = (prob - 0.5) * 2

        urgency = Urgency.MEDIUM
        volume = float(market.get("volume", 0) or 0)
        if volume > 1000000:
            urgency = Urgency.HIGH
        if volume > 5000000:
            urgency = Urgency.CRITICAL
        return event_type, sentiment, sentiment_score, urgency

    def _classify_event_type(self, title: str) -> EventType:
        title_lower = title.lower()
        if any(w in title_lower for w in ["election", "vote", "president", "senate", "politics"]):
            return EventType.GEOPOLITICAL
        elif any(w in title_lower for w in ["war", "ukraine", "israel", "china", "geopolitics"]):
            return EventType.GEOPOLITICAL
        elif any(w in title_lower for w in ["fed", "interest rate", "inflation", "recession", "gdp", "economy"]):
            return EventType.MACRO_EVENT
        elif any(w in title_lower for w in ["crypto", "bitcoin", "ethereum", "regulation", "sec"]):
            return EventType.REGULATORY
        else:
            return EventType.NEWS
