"""O.M.A.-C.O.R.E. CoinGecko Collector"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from core.collectors.base_collector import BaseCollector
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency

class CoinGeckoCollector(BaseCollector):
    API_BASE = "https://api.coingecko.com/api/v3"
    PRICE_CHANGE_THRESHOLD = 5.0
    PRICE_CHANGE_CRITICAL = 10.0
    VOLUME_TO_MCAP_THRESHOLD = 0.15

    def __init__(self):
        super().__init__("coingecko", source_confidence=0.95)

    def collect(self) -> List[Event]:
        events = []
        market_data = self._get_market_data()
        if market_data:
            events.extend(self._process_market_data(market_data))
        trending = self._get_trending()
        if trending:
            events.extend(self._process_trending(trending))
        global_data = self._get_global_data()
        if global_data:
            events.extend(self._process_global_data(global_data))
        self.stats["events_generated"] += len(events)
        self.stats["last_run"] = datetime.now(timezone.utc).isoformat()
        return events

    def _get_market_data(self) -> Optional[List[dict]]:
        return self._make_request(f"{self.API_BASE}/coins/markets", {
            "vs_currency": "usd", "order": "market_cap_desc", "per_page": 50,
            "page": 1, "sparkline": False, "price_change_percentage": "24h,7d"
        })

    def _get_trending(self) -> Optional[List[dict]]:
        result = self._make_request(f"{self.API_BASE}/search/trending")
        return result.get("coins", []) if result else None

    def _get_global_data(self) -> Optional[dict]:
        return self._make_request(f"{self.API_BASE}/global")

    def _process_market_data(self, data: List[dict]) -> List[Event]:
        events = []
        for coin in data:
            symbol = coin.get("symbol", "").upper()
            name = coin.get("name", "")
            coin_id = coin.get("id", "")
            price = float(coin.get("current_price") or 0)
            change_24h_raw = coin.get("price_change_percentage_24h_in_currency") or coin.get("price_change_percentage_24h")
            change_24h = float(change_24h_raw) if change_24h_raw is not None else 0.0
            change_7d_raw = coin.get("price_change_percentage_7d_in_currency")
            change_7d = float(change_7d_raw) if change_7d_raw is not None else 0.0
            volume = float(coin.get("total_volume") or 0)
            market_cap = float(coin.get("market_cap") or 0)

            if abs(change_24h) >= self.PRICE_CHANGE_THRESHOLD:
                urgency = Urgency.CRITICAL if abs(change_24h) >= self.PRICE_CHANGE_CRITICAL else Urgency.HIGH
                sentiment = Sentiment.BULLISH if change_24h > 0 else Sentiment.BEARISH
                sentiment_score = min(max(change_24h / 100, -1.0), 1.0)
                events.append(Event(
                    id=str(uuid.uuid4()), source="coingecko",
                    source_url=f"https://www.coingecko.com/en/coins/{coin_id}",
                    source_id=coin_id, event_type=EventType.PRICE_MOVEMENT,
                    title=f"{symbol} {'+' if change_24h > 0 else ''}{change_24h:.2f}% en 24h -- ${price:,.2f}",
                    summary=f"{name} ({symbol}) movió {change_24h:.2f}% en 24h. Volumen: ${volume:,.0f}. Market Cap: ${market_cap:,.0f}.",
                    timestamp=datetime.now(timezone.utc),
                    assets=[Asset(symbol=symbol, name=name, asset_class=AssetClass.CRYPTO, price_at_event=price, currency="USD")],
                    keywords=[symbol, name, "crypto", "price-movement"],
                    sentiment=sentiment, sentiment_score=sentiment_score,
                    urgency=urgency, confidence=0.85,
                    metadata={"change_24h": change_24h, "change_7d": change_7d, "volume_24h": volume, "market_cap": market_cap, "rank": coin.get("market_cap_rank")}
                ))

            volume_to_mcap = volume / market_cap if market_cap > 0 else 0
            if volume_to_mcap > self.VOLUME_TO_MCAP_THRESHOLD:
                events.append(Event(
                    id=str(uuid.uuid4()), source="coingecko",
                    source_url=f"https://www.coingecko.com/en/coins/{coin_id}",
                    source_id=coin_id, event_type=EventType.VOLUME_SPIKE,
                    title=f"Volumen anómalo en {symbol} -- ${volume:,.0f} en 24h",
                    summary=f"{name} muestra volumen excepcional: ${volume:,.0f} en 24h ({volume_to_mcap*100:.1f}% de market cap).",
                    timestamp=datetime.now(timezone.utc),
                    assets=[Asset(symbol=symbol, name=name, asset_class=AssetClass.CRYPTO, price_at_event=price, currency="USD")],
                    keywords=[symbol, "volume-spike", "crypto"],
                    urgency=Urgency.MEDIUM, confidence=0.75,
                    metadata={"volume_24h": volume, "volume_to_mcap": volume_to_mcap}
                ))
        return events

    def _process_trending(self, data: List[dict]) -> List[Event]:
        events = []
        for item in data:
            coin = item.get("item", {})
            symbol = coin.get("symbol", "").upper()
            name = coin.get("name", "")
            coin_id = coin.get("id", "")
            events.append(Event(
                id=str(uuid.uuid4()), source="coingecko",
                source_url=f"https://www.coingecko.com/en/coins/{coin_id}",
                source_id=coin_id, event_type=EventType.SOCIAL_TREND,
                title=f"{symbol} en tendencia (#{coin.get('market_cap_rank', '?')})",
                summary=f"{name} ({symbol}) está en búsquedas populares de CoinGecko. Score: {coin.get('score', 'N/A')}.",
                timestamp=datetime.now(timezone.utc),
                assets=[Asset(symbol=symbol, name=name, asset_class=AssetClass.CRYPTO, currency="USD")],
                keywords=[symbol, "trending", "social", "coingecko"],
                sentiment=Sentiment.BULLISH, urgency=Urgency.LOW, confidence=0.70,
                metadata={"trending_score": coin.get("score"), "market_cap_rank": coin.get("market_cap_rank"), "platform": "coingecko"}
            ))
        return events

    def _process_global_data(self, data: dict) -> List[Event]:
        events = []
        global_stats = data.get("data", {})
        total_mcap = global_stats.get("total_market_cap", {}).get("usd", 0)
        total_volume = global_stats.get("total_volume", {}).get("usd", 0)
        mcap_change_24h = global_stats.get("market_cap_change_percentage_24h_usd", 0)
        if abs(mcap_change_24h) >= 3.0:
            sentiment = Sentiment.BULLISH if mcap_change_24h > 0 else Sentiment.BEARISH
            urgency = Urgency.HIGH if abs(mcap_change_24h) >= 5.0 else Urgency.MEDIUM
            events.append(Event(
                id=str(uuid.uuid4()), source="coingecko",
                source_url="https://www.coingecko.com",
                event_type=EventType.MACRO_EVENT,
                title=f"Market Cap Global Crypto {'+' if mcap_change_24h > 0 else ''}{mcap_change_24h:.2f}%",
                summary=f"El market cap global de criptomonedas es ${total_mcap:,.0f} con un cambio de {mcap_change_24h:.2f}% en 24h. Volumen total: ${total_volume:,.0f}.",
                timestamp=datetime.now(timezone.utc),
                assets=[Asset(symbol="TOTAL_CRYPTO", name="Global Crypto Market", asset_class=AssetClass.CRYPTO, currency="USD")],
                keywords=["crypto", "global", "market-cap", "macro"],
                sentiment=sentiment, sentiment_score=min(max(mcap_change_24h / 100, -1.0), 1.0),
                urgency=urgency, confidence=0.90,
                metadata={"total_market_cap_usd": total_mcap, "total_volume_usd": total_volume, "market_cap_change_24h": mcap_change_24h, "active_cryptocurrencies": global_stats.get("active_cryptocurrencies"), "markets": global_stats.get("markets")}
            ))
        return events
