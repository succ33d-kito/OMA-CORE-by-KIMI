"""O.M.A.-C.O.R.E. Yahoo Finance Collector"""
import uuid
import math
from datetime import datetime, timezone
from typing import List, Optional
from core.collectors.base_collector import BaseCollector
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency


class YahooFinanceCollector(BaseCollector):
    WATCHLIST_STOCKS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX",
        "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER", "COIN", "PLTR",
        "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO",
    ]
    WATCHLIST_FOREX = [
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X",
        "USDCAD=X", "NZDUSD=X", "EURGBP=X",
    ]
    WATCHLIST_COMMODITIES = [
        "GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "ZW=F", "ZC=F", "ZS=F",
    ]
    WATCHLIST_INDICES = [
        "^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX", "^FTSE", "^N225", "^HSI",
    ]
    PRICE_CHANGE_THRESHOLD = 3.0
    PRICE_CHANGE_THRESHOLD_CRYPTO = 5.0
    VOLUME_SPIKE_MULTIPLIER = 2.0

    def __init__(self):
        super().__init__("yahoo_finance", source_confidence=0.95)
        self._yf = None

    def _get_yf(self):
        if self._yf is None:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                print("[yahoo_finance] yfinance no instalado. Ejecuta: pip install yfinance")
                return None
        return self._yf

    def _safe_float(self, value, default=0.0):
        """Convierte un valor a float de forma segura, manejando NaN."""
        if value is None:
            return default
        try:
            result = float(value)
            if math.isnan(result) or math.isinf(result):
                return default
            return result
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value, default=0):
        """Convierte un valor a int de forma segura, manejando NaN."""
        if value is None:
            return default
        try:
            result = float(value)
            if math.isnan(result) or math.isinf(result):
                return default
            return int(result)
        except (ValueError, TypeError):
            return default

    def collect(self) -> List[Event]:
        events = []
        yf = self._get_yf()
        if not yf:
            return events
        events.extend(self._collect_tickers(self.WATCHLIST_STOCKS, AssetClass.STOCK))
        events.extend(self._collect_tickers(self.WATCHLIST_FOREX, AssetClass.FOREX))
        events.extend(self._collect_tickers(self.WATCHLIST_COMMODITIES, AssetClass.COMMODITY))
        events.extend(self._collect_indices())
        self.stats["events_generated"] += len(events)
        self.stats["last_run"] = datetime.now(timezone.utc).isoformat()
        return events

    def _collect_tickers(self, symbols: List[str], asset_class: AssetClass) -> List[Event]:
        events = []
        yf = self._get_yf()
        if not yf:
            return events
        try:
            tickers = yf.Tickers(" ".join(symbols))
            data = tickers.download(period="2d", interval="1d", group_by="ticker", threads=True)
            if data.empty:
                return events
            for symbol in symbols:
                try:
                    ticker_data = data[symbol] if len(symbols) > 1 else data
                    if ticker_data.empty:
                        continue
                    latest = ticker_data.iloc[-1]
                    prev = ticker_data.iloc[-2] if len(ticker_data) > 1 else latest
                    close = self._safe_float(latest.get("Close"))
                    prev_close = self._safe_float(prev.get("Close"), close)
                    volume = self._safe_int(latest.get("Volume"))
                    avg_volume = self._safe_int(ticker_data["Volume"].mean()) if "Volume" in ticker_data.columns else volume
                    if prev_close == 0:
                        continue
                    change_pct = ((close - prev_close) / prev_close) * 100
                    threshold = self.PRICE_CHANGE_THRESHOLD_CRYPTO if "-USD" in symbol or "=X" in symbol else self.PRICE_CHANGE_THRESHOLD
                    if abs(change_pct) >= threshold:
                        events.extend(self._create_price_event(symbol, close, change_pct, volume, asset_class))
                    if avg_volume > 0 and volume / avg_volume >= self.VOLUME_SPIKE_MULTIPLIER:
                        events.extend(self._create_volume_event(symbol, close, volume, avg_volume, asset_class))
                except Exception as e:
                    print(f"[yahoo_finance] Error procesando {symbol}: {e}")
                    continue
        except Exception as e:
            print(f"[yahoo_finance] Error en batch download: {e}")
        return events

    def _create_price_event(self, symbol: str, price: float, change_pct: float, volume: int, asset_class: AssetClass) -> List[Event]:
        urgency = Urgency.CRITICAL if abs(change_pct) >= 8.0 else Urgency.HIGH if abs(change_pct) >= 5.0 else Urgency.MEDIUM
        sentiment = Sentiment.BULLISH if change_pct > 0 else Sentiment.BEARISH
        sentiment_score = min(max(change_pct / 100, -1.0), 1.0)
        name = symbol
        try:
            import yfinance as yf
            ticker_info = yf.Ticker(symbol).info
            name = ticker_info.get("shortName", ticker_info.get("longName", symbol))
        except:
            pass
        event = Event(
            id=str(uuid.uuid4()), source="yahoo_finance",
            source_url=f"https://finance.yahoo.com/quote/{symbol}",
            source_id=symbol, event_type=EventType.PRICE_MOVEMENT,
            title=f"{symbol} {'+' if change_pct > 0 else ''}{change_pct:.2f}% -- ${price:,.2f}",
            summary=f"{name} ({symbol}) movio {change_pct:.2f}% en la sesion. Precio: ${price:,.2f}. Volumen: {volume:,}.",
            timestamp=datetime.now(timezone.utc),
            assets=[Asset(symbol=symbol, name=name, asset_class=asset_class, price_at_event=price, currency="USD")],
            keywords=[symbol, name, asset_class.value, "price-movement"],
            sentiment=sentiment, sentiment_score=sentiment_score,
            urgency=urgency, confidence=0.92,
            metadata={"change_percent": change_pct, "price": price, "volume": volume, "asset_class": asset_class.value, "source": "yahoo_finance"}
        )
        return [event]

    def _create_volume_event(self, symbol: str, price: float, volume: int, avg_volume: int, asset_class: AssetClass) -> List[Event]:
        ratio = volume / avg_volume if avg_volume > 0 else 0
        name = symbol
        try:
            import yfinance as yf
            ticker_info = yf.Ticker(symbol).info
            name = ticker_info.get("shortName", ticker_info.get("longName", symbol))
        except:
            pass
        event = Event(
            id=str(uuid.uuid4()), source="yahoo_finance",
            source_url=f"https://finance.yahoo.com/quote/{symbol}",
            source_id=symbol, event_type=EventType.VOLUME_SPIKE,
            title=f"Volumen {ratio:.1f}x promedio en {symbol}",
            summary=f"{name} ({symbol}) muestra volumen anomalo: {volume:,} ({ratio:.1f}x del promedio de {avg_volume:,}).",
            timestamp=datetime.now(timezone.utc),
            assets=[Asset(symbol=symbol, name=name, asset_class=asset_class, price_at_event=price, currency="USD")],
            keywords=[symbol, "volume-spike", asset_class.value],
            urgency=Urgency.MEDIUM, confidence=0.80,
            metadata={"volume": volume, "avg_volume": avg_volume, "volume_ratio": ratio, "asset_class": asset_class.value}
        )
        return [event]

    def _collect_indices(self) -> List[Event]:
        events = []
        yf = self._get_yf()
        if not yf:
            return events
        try:
            for symbol in self.WATCHLIST_INDICES:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if hist.empty or len(hist) < 2:
                    continue
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                close = self._safe_float(latest["Close"])
                prev_close = self._safe_float(prev["Close"])
                if prev_close == 0:
                    continue
                change_pct = ((close - prev_close) / prev_close) * 100
                if abs(change_pct) >= 2.0:
                    name = {
                        "^GSPC": "S&P 500", "^IXIC": "NASDAQ Composite",
                        "^DJI": "Dow Jones", "^RUT": "Russell 2000",
                        "^VIX": "VIX Volatility Index", "^FTSE": "FTSE 100",
                        "^N225": "Nikkei 225", "^HSI": "Hang Seng Index",
                    }.get(symbol, symbol)
                    sentiment = Sentiment.BULLISH if change_pct > 0 else Sentiment.BEARISH
                    urgency = Urgency.HIGH if abs(change_pct) >= 3.0 else Urgency.MEDIUM
                    if symbol == "^VIX" and change_pct > 5.0:
                        sentiment = Sentiment.BEARISH
                        urgency = Urgency.HIGH
                    events.append(Event(
                        id=str(uuid.uuid4()), source="yahoo_finance",
                        source_url=f"https://finance.yahoo.com/quote/{symbol}",
                        source_id=symbol,
                        event_type=EventType.MACRO_EVENT if symbol in ["^GSPC", "^IXIC", "^DJI", "^VIX"] else EventType.PRICE_MOVEMENT,
                        title=f"{name} {'+' if change_pct > 0 else ''}{change_pct:.2f}%",
                        summary=f"El indice {name} ({symbol}) cerro en {close:,.2f} con un cambio de {change_pct:.2f}%.",
                        timestamp=datetime.now(timezone.utc),
                        assets=[Asset(symbol=symbol, name=name, asset_class=AssetClass.INDEX, price_at_event=close, currency="USD")],
                        keywords=[symbol, name, "index", "macro" if symbol in ["^GSPC", "^IXIC", "^DJI", "^VIX"] else "index"],
                        sentiment=sentiment, sentiment_score=min(max(change_pct / 100, -1.0), 1.0),
                        urgency=urgency, confidence=0.95,
                        metadata={"change_percent": change_pct, "price": close, "index_name": name}
                    ))
        except Exception as e:
            print(f"[yahoo_finance] Error en indices: {e}")
        return events
