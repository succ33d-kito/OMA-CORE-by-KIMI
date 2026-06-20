"""O.M.A.-C.O.R.E. World Monitor"""
import requests, feedparser, json, uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency

class BaseCollector:
    def __init__(self, name):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "OMA-CORE/1.0"})
    
    def collect(self):
        raise NotImplementedError
    
    def _make_request(self, url, params=None, timeout=30):
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else {"text": response.text}
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return None

class CoinGeckoCollector(BaseCollector):
    API_BASE = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        super().__init__("coingecko")
    
    def collect(self):
        events = []
        market_data = self._get_market_data()
        if market_data:
            events.extend(self._process_market_data(market_data))
        trending = self._get_trending()
        if trending:
            events.extend(self._process_trending(trending))
        return events
    
    def _get_market_data(self):
        return self._make_request(f"{self.API_BASE}/coins/markets", {
            "vs_currency": "usd", "order": "market_cap_desc", "per_page": 50,
            "page": 1, "sparkline": False, "price_change_percentage": "24h,7d"
        })
    
    def _process_market_data(self, data):
        events = []
        for coin in data:
            symbol = coin.get("symbol", "").upper()
            name = coin.get("name", "")
            price = float(coin.get("current_price") or 0)
            change_24h_raw = coin.get("price_change_percentage_24h_in_currency") or coin.get("price_change_percentage_24h")
            change_24h = float(change_24h_raw) if change_24h_raw is not None else 0.0
            change_7d_raw = coin.get("price_change_percentage_7d_in_currency")
            change_7d = float(change_7d_raw) if change_7d_raw is not None else 0.0
            volume = float(coin.get("total_volume") or 0)
            market_cap = float(coin.get("market_cap") or 0)
            
            if abs(change_24h) >= 5:
                urgency = Urgency.HIGH if abs(change_24h) >= 10 else Urgency.MEDIUM
                sentiment = Sentiment.BULLISH if change_24h > 0 else Sentiment.BEARISH
                events.append(Event(
                    id=str(uuid.uuid4()), source="coingecko",
                    source_url=f"https://www.coingecko.com/en/coins/{coin.get('id')}",
                    event_type=EventType.PRICE_MOVEMENT,
                    title=f"{symbol} {'+' if change_24h > 0 else ''}{change_24h:.2f}% en 24h -- ${price:,.2f}",
                    summary=f"{name} ({symbol}) movio {change_24h:.2f}% en 24h. Volumen: ${volume:,.0f}. Market Cap: ${market_cap:,.0f}.",
                    timestamp=datetime.now(timezone.utc),
                    assets=[Asset(symbol=symbol, name=name, asset_class=AssetClass.CRYPTO, price_at_event=price, currency="USD")],
                    keywords=[symbol, name, "crypto", "price-movement"],
                    sentiment=sentiment, sentiment_score=change_24h / 100,
                    urgency=urgency, confidence=0.85,
                    metadata={"change_24h": change_24h, "change_7d": change_7d, "volume_24h": volume, "market_cap": market_cap, "rank": coin.get("market_cap_rank")}
                ))
            
            volume_to_mcap = volume / market_cap if market_cap > 0 else 0
            if volume_to_mcap > 0.15:
                events.append(Event(
                    id=str(uuid.uuid4()), source="coingecko",
                    source_url=f"https://www.coingecko.com/en/coins/{coin.get('id')}",
                    event_type=EventType.VOLUME_SPIKE,
                    title=f"Volumen anomalo en {symbol} -- ${volume:,.0f} en 24h",
                    summary=f"{name} muestra volumen excepcional: ${volume:,.0f} en 24h ({volume_to_mcap*100:.1f}% de market cap).",
                    timestamp=datetime.now(timezone.utc),
                    assets=[Asset(symbol=symbol, name=name, asset_class=AssetClass.CRYPTO, price_at_event=price, currency="USD")],
                    keywords=[symbol, "volume-spike", "crypto"],
                    urgency=Urgency.MEDIUM, confidence=0.75,
                    metadata={"volume_24h": volume, "volume_to_mcap": volume_to_mcap}
                ))
        return events
    
    def _get_trending(self):
        result = self._make_request(f"{self.API_BASE}/search/trending")
        return result.get("coins", []) if result else None
    
    def _process_trending(self, data):
        events = []
        for item in data:
            coin = item.get("item", {})
            symbol = coin.get("symbol", "").upper()
            name = coin.get("name", "")
            events.append(Event(
                id=str(uuid.uuid4()), source="coingecko",
                source_url=f"https://www.coingecko.com/en/coins/{coin.get('id')}",
                event_type=EventType.SOCIAL_TREND,
                title=f"{symbol} en tendencia (#{coin.get('market_cap_rank', '?')})",
                summary=f"{name} ({symbol}) esta en busquedas populares de CoinGecko. Score: {coin.get('score', 'N/A')}.",
                timestamp=datetime.now(timezone.utc),
                assets=[Asset(symbol=symbol, name=name, asset_class=AssetClass.CRYPTO, currency="USD")],
                keywords=[symbol, "trending", "social"],
                sentiment=Sentiment.BULLISH, urgency=Urgency.LOW, confidence=0.7,
                metadata={"trending_score": coin.get("score"), "market_cap_rank": coin.get("market_cap_rank")}
            ))
        return events

class WorldMonitor:
    def __init__(self):
        self.collectors = [CoinGeckoCollector()]
    
    def collect_all(self):
        all_events = []
        for collector in self.collectors:
            try:
                print(f"[WorldMonitor] Ejecutando {collector.name}...")
                events = collector.collect()
                print(f"[WorldMonitor] {collector.name}: {len(events)} eventos")
                all_events.extend(events)
            except Exception as e:
                print(f"[WorldMonitor] Error en {collector.name}: {e}")
                continue
        return all_events
    
    def collect_by_source(self, source_name):
        for collector in self.collectors:
            if collector.name == source_name:
                return collector.collect()
        return []
