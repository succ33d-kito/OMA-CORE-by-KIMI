"""O.M.A.-C.O.R.E. Sentiment Collector"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from core.collectors.base_collector import BaseCollector
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency

class SentimentCollector(BaseCollector):
    CRYPTO_FNG_URL = "https://api.alternative.me/fng/?limit=2"
    FNG_THRESHOLD = 20

    def __init__(self):
        super().__init__("sentiment_fng_crypto", source_confidence=0.85)

    def collect(self) -> List[Event]:
        events = []
        crypto_fng = self._get_crypto_fng()
        if crypto_fng:
            events.extend(self._process_crypto_fng(crypto_fng))
        self.stats["events_generated"] += len(events)
        self.stats["last_run"] = datetime.now(timezone.utc).isoformat()
        return events

    def _get_crypto_fng(self) -> Optional[List[dict]]:
        result = self._make_request(self.CRYPTO_FNG_URL)
        if result and "data" in result:
            return result["data"]
        return None

    def _process_crypto_fng(self, data: List[dict]) -> List[Event]:
        events = []
        if not data or len(data) < 1:
            return events
        latest = data[0]
        value = int(latest.get("value", 50))
        classification = latest.get("value_classification", "Neutral")
        timestamp_str = latest.get("timestamp", "")
        if value > 80 or value < 20:
            if value <= 20:
                sentiment = Sentiment.VERY_BEARISH
                sentiment_score = -0.9
                urgency = Urgency.HIGH
                event_type = EventType.SENTIMENT_SHIFT
                title = f"Extreme Fear en Crypto ({value}/100) -- Oportunidad de compra"
                summary = f"El índice Fear & Greed de criptomonedas está en {value}/100 ({classification}). Esto indica pánico extremo, históricamente un buen momento para acumular."
            else:
                sentiment = Sentiment.VERY_BULLISH
                sentiment_score = 0.9
                urgency = Urgency.HIGH
                event_type = EventType.SENTIMENT_SHIFT
                title = f"Extreme Greed en Crypto ({value}/100) -- Precaución"
                summary = f"El índice Fear & Greed de criptomonedas está en {value}/100 ({classification}). Esto indica euforia extrema, históricamente un momento de riesgo."
            events.append(Event(
                id=str(uuid.uuid4()), source="sentiment_fng_crypto",
                source_url="https://alternative.me/crypto/fear-and-greed-index/",
                event_type=event_type,
                title=title,
                summary=summary,
                timestamp=datetime.now(timezone.utc),
                assets=[Asset(symbol="FNG-CRYPTO", name="Crypto Fear & Greed Index", asset_class=AssetClass.INDEX, currency="USD")],
                keywords=["sentiment", "fear-greed", "crypto", "index", "extreme"],
                sentiment=sentiment, sentiment_score=sentiment_score,
                urgency=urgency, confidence=0.85,
                metadata={
                    "index_type": "fear_greed_crypto", "value": value,
                    "classification": classification, "timestamp": timestamp_str,
                    "scale": "0-100", "interpretation": "extreme_fear" if value <= 20 else "extreme_greed",
                }
            ))
        if len(data) >= 2:
            previous = data[1]
            prev_value = int(previous.get("value", 50))
            change = value - prev_value
            if abs(change) >= 20:
                sentiment = Sentiment.BULLISH if change > 0 else Sentiment.BEARISH
                sentiment_score = min(max(change / 50, -1.0), 1.0)
                events.append(Event(
                    id=str(uuid.uuid4()), source="sentiment_fng_crypto",
                    source_url="https://alternative.me/crypto/fear-and-greed-index/",
                    event_type=EventType.SENTIMENT_SHIFT,
                    title=f"Sentimiento Crypto cambió {change:+d} puntos ({prev_value}→{value})",
                    summary=f"El índice Fear & Greed de crypto cambió drásticamente de {prev_value} a {value} en un día. Esto indica un cambio significativo en el sentimiento del mercado.",
                    timestamp=datetime.now(timezone.utc),
                    assets=[Asset(symbol="FNG-CRYPTO", name="Crypto Fear & Greed Index", asset_class=AssetClass.INDEX, currency="USD")],
                    keywords=["sentiment", "fear-greed", "crypto", "shift", "momentum"],
                    sentiment=sentiment, sentiment_score=sentiment_score,
                    urgency=Urgency.HIGH, confidence=0.85,
                    metadata={
                        "index_type": "fear_greed_crypto", "previous_value": prev_value,
                        "current_value": value, "change": change, "change_type": "drastic_shift",
                    }
                ))
        return events
