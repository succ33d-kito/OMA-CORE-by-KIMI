"""O.M.A.-C.O.R.E. FRED Collector (Federal Reserve Economic Data)"""
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from core.collectors.base_collector import BaseCollector
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency

class FREDCollector(BaseCollector):
    API_BASE = "https://api.stlouisfed.org/fred"
    SERIES = {
        "DFF": {"name": "Federal Funds Rate", "category": "rates", "unit": "%"},
        "DGS10": {"name": "10-Year Treasury Yield", "category": "rates", "unit": "%"},
        "DGS2": {"name": "2-Year Treasury Yield", "category": "rates", "unit": "%"},
        "T10Y2Y": {"name": "10Y-2Y Treasury Spread", "category": "rates", "unit": "%"},
        "CPIAUCSL": {"name": "CPI (All Urban Consumers)", "category": "inflation", "unit": "index"},
        "CPILFESL": {"name": "Core CPI", "category": "inflation", "unit": "index"},
        "PCEPI": {"name": "PCE Price Index", "category": "inflation", "unit": "index"},
        "PAYEMS": {"name": "Nonfarm Payrolls", "category": "employment", "unit": "thousands"},
        "UNRATE": {"name": "Unemployment Rate", "category": "employment", "unit": "%"},
        "ICSA": {"name": "Initial Jobless Claims", "category": "employment", "unit": "claims"},
        "GDP": {"name": "Gross Domestic Product", "category": "growth", "unit": "billions"},
        "GDPC1": {"name": "Real GDP", "category": "growth", "unit": "billions"},
        "INDPRO": {"name": "Industrial Production", "category": "growth", "unit": "index"},
        "UMCSENT": {"name": "Consumer Sentiment (Michigan)", "category": "sentiment", "unit": "index"},
    }
    THRESHOLDS = {
        "rates": {"change": 0.25, "level_critical": 5.0},
        "inflation": {"change": 0.3, "level_high": 4.0},
        "employment": {"change": 50, "level_critical": 6.0},
        "growth": {"change": 1.0, "level_recession": 0},
        "sentiment": {"change": 5.0, "level_low": 70},
    }

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("fred", source_confidence=0.98)
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        if not self.api_key:
            print("[fred] WARNING: FRED_API_KEY not set. FRED data will not be collected. "
                  "Set FRED_API_KEY in .env or pass api_key to FREDCollector.")

    def collect(self) -> List[Event]:
        events = []
        for series_id, info in self.SERIES.items():
            try:
                data = self._get_series_data(series_id)
                if data:
                    series_events = self._process_series(series_id, info, data)
                    events.extend(series_events)
            except Exception as e:
                print(f"[fred] Error en serie {series_id}: {e}")
                continue
        self.stats["events_generated"] += len(events)
        self.stats["last_run"] = datetime.now(timezone.utc).isoformat()
        return events

    def _get_series_data(self, series_id: str) -> Optional[List[dict]]:
        params = {"series_id": series_id, "file_type": "json", "sort_order": "desc", "limit": 10}
        if self.api_key:
            params["api_key"] = self.api_key
        result = self._make_request(f"{self.API_BASE}/series/observations", params)
        if result and "observations" in result:
            return result["observations"]
        return None

    def _process_series(self, series_id: str, info: dict, data: List[dict]) -> List[Event]:
        events = []
        category = info["category"]
        thresholds = self.THRESHOLDS.get(category, {})
        if len(data) < 2:
            return events
        latest = None
        previous = None
        for obs in data:
            try:
                val = float(obs.get("value", ""))
                if latest is None:
                    latest = {"date": obs.get("date"), "value": val}
                elif previous is None:
                    previous = {"date": obs.get("date"), "value": val}
                    break
            except (ValueError, TypeError):
                continue
        if not latest or not previous:
            return events
        change = latest["value"] - previous["value"]
        change_pct = (change / previous["value"] * 100) if previous["value"] != 0 else 0
        should_alert = False
        event_type = EventType.MACRO_EVENT
        urgency = Urgency.MEDIUM
        sentiment = Sentiment.NEUTRAL
        sentiment_score = 0.0

        if category == "rates":
            if abs(change) >= thresholds.get("change", 0.25):
                should_alert = True
                sentiment = Sentiment.BEARISH if change > 0 else Sentiment.BULLISH
                sentiment_score = min(max(-change / 1.0, -1.0), 1.0)
                urgency = Urgency.HIGH if abs(change) >= 0.50 else Urgency.MEDIUM
                if latest["value"] >= thresholds.get("level_critical", 5.0):
                    urgency = Urgency.CRITICAL
        elif category == "inflation":
            if abs(change_pct) >= thresholds.get("change", 0.3):
                should_alert = True
                sentiment = Sentiment.BEARISH if change > 0 else Sentiment.BULLISH
                sentiment_score = min(max(-change_pct / 5.0, -1.0), 1.0)
                urgency = Urgency.HIGH if abs(change_pct) >= 1.0 else Urgency.MEDIUM
                if latest["value"] >= thresholds.get("level_high", 4.0):
                    urgency = Urgency.CRITICAL
        elif category == "employment":
            if info["name"] == "Unemployment Rate":
                if abs(change) >= 0.2:
                    should_alert = True
                    sentiment = Sentiment.BEARISH if change > 0 else Sentiment.BULLISH
                    sentiment_score = min(max(-change / 2.0, -1.0), 1.0)
                    urgency = Urgency.HIGH if abs(change) >= 0.5 else Urgency.MEDIUM
                    if latest["value"] >= thresholds.get("level_critical", 6.0):
                        urgency = Urgency.CRITICAL
            else:
                if abs(change) >= thresholds.get("change", 50):
                    should_alert = True
                    if "Claims" in info["name"]:
                        sentiment = Sentiment.BEARISH if change > 0 else Sentiment.BULLISH
                    else:
                        sentiment = Sentiment.BULLISH if change > 0 else Sentiment.BEARISH
                    sentiment_score = min(max(change / 200, -1.0), 1.0)
                    urgency = Urgency.HIGH if abs(change) >= 100 else Urgency.MEDIUM
        elif category == "growth":
            if abs(change_pct) >= thresholds.get("change", 1.0):
                should_alert = True
                sentiment = Sentiment.BULLISH if change > 0 else Sentiment.BEARISH
                sentiment_score = min(max(change_pct / 5.0, -1.0), 1.0)
                urgency = Urgency.HIGH if abs(change_pct) >= 2.0 else Urgency.MEDIUM
                if change_pct < 0 and latest["value"] < 0:
                    urgency = Urgency.CRITICAL
        elif category == "sentiment":
            if abs(change) >= thresholds.get("change", 5.0):
                should_alert = True
                sentiment = Sentiment.BULLISH if change > 0 else Sentiment.BEARISH
                sentiment_score = min(max(change / 20.0, -1.0), 1.0)
                urgency = Urgency.HIGH if abs(change) >= 10 else Urgency.MEDIUM
                if latest["value"] <= thresholds.get("level_low", 70):
                    urgency = Urgency.CRITICAL

        if should_alert:
            if category == "rates":
                sentiment = Sentiment.BEARISH if change > 0 else Sentiment.BULLISH
                sentiment_score = -sentiment_score if sentiment_score > 0 else sentiment_score
            events.append(Event(
                id=str(uuid.uuid4()), source="fred",
                source_url=f"https://fred.stlouisfed.org/series/{series_id}",
                source_id=series_id, event_type=event_type,
                title=f"{info['name']}: {latest['value']:.2f}{info['unit']} ({'+' if change > 0 else ''}{change:.2f})",
                summary=f"{info['name']} reportó {latest['value']:.2f}{info['unit']} (cambio de {'+' if change > 0 else ''}{change:.2f} desde {previous['date']}). Dato del {latest['date']}.",
                timestamp=datetime.now(timezone.utc),
                assets=[Asset(symbol=series_id, name=info["name"], asset_class=AssetClass.BOND if category == "rates" else AssetClass.INDEX, currency="USD")],
                keywords=[series_id, info["name"], category, "macro", "fed"],
                sentiment=sentiment, sentiment_score=sentiment_score,
                urgency=urgency, confidence=0.98,
                metadata={
                    "series_id": series_id, "series_name": info["name"], "category": category,
                    "latest_value": latest["value"], "previous_value": previous["value"],
                    "change": change, "change_percent": change_pct,
                    "latest_date": latest["date"], "previous_date": previous["date"], "unit": info["unit"],
                }
            ))
        return events
