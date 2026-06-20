"""O.M.A.-C.O.R.E. Binance Collector"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from core.collectors.base_collector import BaseCollector
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency

class BinanceCollector(BaseCollector):
    """
    Collector para datos de mercado crypto via Binance API.
    
    Fuente: https://api.binance.com
    Confianza: 0.96 (exchange real, datos de trading en vivo)
    Ventaja: Precios y volumen en tiempo real directo del exchange
    """
    
    API_BASE = "https://api.binance.com/api/v3"
    
    # Pares a monitorear (USDT)
    SYMBOLS = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT",
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT",
        "DOTUSDT", "UNIUSDT", "LTCUSDT", "BCHUSDT", "ATOMUSDT",
    ]
    
    # Umbrales
    PRICE_CHANGE_THRESHOLD = 3.0
    PRICE_CHANGE_CRITICAL = 8.0
    VOLUME_SPIKE_MULTIPLIER = 2.5
    
    def __init__(self):
        super().__init__("binance", source_confidence=0.96)
    
    def collect(self) -> List[Event]:
        """Recolecta datos de mercado de Binance."""
        events = []
        
        # 1. Precios de 24h (ticker/24hr)
        tickers = self._get_24h_tickers()
        if tickers:
            events.extend(self._process_tickers(tickers))
        
        # 2. Precios actuales para validación
        prices = self._get_prices()
        if prices:
            # Guardar en metadata para cross-validation
            pass
        
        self.stats["events_generated"] += len(events)
        self.stats["last_run"] = datetime.now(timezone.utc).isoformat()
        return events
    
    def _get_24h_tickers(self) -> Optional[List[dict]]:
        """Obtiene datos de 24h para todos los símbolos."""
        symbols_str = '["' + '","'.join(self.SYMBOLS) + '"]'
        return self._make_request(
            f"{self.API_BASE}/ticker/24hr",
            {"symbols": symbols_str}
        )
    
    def _get_prices(self) -> Optional[List[dict]]:
        """Obtiene precios actuales."""
        return self._make_request(f"{self.API_BASE}/ticker/price")
    
    def _process_tickers(self, tickers: List[dict]) -> List[Event]:
        """Procesa tickers de 24h en eventos."""
        events = []
        
        for ticker in tickers:
            try:
                symbol = ticker.get("symbol", "")
                # Solo procesar símbolos que monitoreamos
                if symbol not in self.SYMBOLS:
                    continue
                
                # Extraer datos
                price_change_pct = float(ticker.get("priceChangePercent", 0))
                last_price = float(ticker.get("lastPrice", 0))
                volume = float(ticker.get("volume", 0))
                quote_volume = float(ticker.get("quoteVolume", 0))
                high_price = float(ticker.get("highPrice", 0))
                low_price = float(ticker.get("lowPrice", 0))
                weighted_avg = float(ticker.get("weightedAvgPrice", 0))
                
                # Calcular ratio volumen/precio
                volume_ratio = (volume * last_price) / quote_volume if quote_volume > 0 else 0
                
                # Evento: Movimiento de precio significativo
                if abs(price_change_pct) >= self.PRICE_CHANGE_THRESHOLD:
                    urgency = Urgency.CRITICAL if abs(price_change_pct) >= self.PRICE_CHANGE_CRITICAL else Urgency.HIGH
                    sentiment = Sentiment.BULLISH if price_change_pct > 0 else Sentiment.BEARISH
                    sentiment_score = min(max(price_change_pct / 100, -1.0), 1.0)
                    
                    # Mapear símbolo a nombre legible
                    asset_symbol = symbol.replace("USDT", "")
                    asset_name = {
                        "BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana",
                        "XRP": "Ripple", "BNB": "Binance Coin", "ADA": "Cardano",
                        "DOGE": "Dogecoin", "AVAX": "Avalanche", "LINK": "Chainlink",
                        "MATIC": "Polygon", "DOT": "Polkadot", "UNI": "Uniswap",
                        "LTC": "Litecoin", "BCH": "Bitcoin Cash", "ATOM": "Cosmos",
                    }.get(asset_symbol, asset_symbol)
                    
                    events.append(Event(
                        id=str(uuid.uuid4()),
                        source="binance",
                        source_url=f"https://www.binance.com/en/trade/{symbol}",
                        source_id=symbol,
                        event_type=EventType.PRICE_MOVEMENT,
                        title=f"{asset_symbol} {'+' if price_change_pct > 0 else ''}{price_change_pct:.2f}% en 24h (Binance) — ${last_price:,.2f}",
                        summary=f"{asset_name} ({asset_symbol}) movió {price_change_pct:.2f}% en 24h en Binance. "
                                f"Precio: ${last_price:,.2f}. Volumen: ${quote_volume:,.0f}. "
                                f"High: ${high_price:,.2f}, Low: ${low_price:,.2f}.",
                        timestamp=datetime.now(timezone.utc),
                        assets=[Asset(
                            symbol=asset_symbol,
                            name=asset_name,
                            asset_class=AssetClass.CRYPTO,
                            price_at_event=last_price,
                            currency="USD"
                        )],
                        keywords=[asset_symbol, "crypto", "binance", "price-movement"],
                        sentiment=sentiment,
                        sentiment_score=sentiment_score,
                        urgency=urgency,
                        confidence=0.96,
                        metadata={
                            "change_24h": price_change_pct,
                            "price": last_price,
                            "volume_24h": volume,
                            "quote_volume": quote_volume,
                            "high_24h": high_price,
                            "low_24h": low_price,
                            "weighted_avg": weighted_avg,
                            "exchange": "binance",
                            "pair": symbol,
                        }
                    ))
                
                # Evento: Spike de volumen
                if volume_ratio > self.VOLUME_SPIKE_MULTIPLIER:
                    events.append(Event(
                        id=str(uuid.uuid4()),
                        source="binance",
                        source_url=f"https://www.binance.com/en/trade/{symbol}",
                        source_id=symbol,
                        event_type=EventType.VOLUME_SPIKE,
                        title=f"Volumen anómalo en {asset_symbol} (Binance) — ${quote_volume:,.0f}",
                        summary=f"{asset_name} muestra volumen excepcional en Binance: "
                                f"${quote_volume:,.0f} en 24h.",
                        timestamp=datetime.now(timezone.utc),
                        assets=[Asset(
                            symbol=asset_symbol,
                            name=asset_name,
                            asset_class=AssetClass.CRYPTO,
                            price_at_event=last_price,
                            currency="USD"
                        )],
                        keywords=[asset_symbol, "volume-spike", "binance", "crypto"],
                        urgency=Urgency.MEDIUM,
                        confidence=0.90,
                        metadata={
                            "volume_24h": volume,
                            "quote_volume": quote_volume,
                            "volume_ratio": volume_ratio,
                            "exchange": "binance",
                            "pair": symbol,
                        }
                    ))
                    
            except Exception as e:
                print(f"[binance] Error procesando {symbol}: {e}")
                continue
        
        return events
