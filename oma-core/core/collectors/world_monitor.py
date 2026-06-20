"""
O.M.A.-C.O.R.E. — World Monitor / Data Collectors
===================================================
Colectores de datos para trading.
Fuentes gratuitas, sin API keys requeridas (excepto opcionales).

Fuentes implementadas:
- CoinGecko API (crypto precios, volumen, market cap)
- Yahoo Finance vía yfinance (stocks, forex, commodities)
- RSS Feeds (noticias financieras)
- GDELT v2 API (eventos globales)
"""

import requests
import feedparser
import json
import uuid
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency


class BaseCollector:
    """Clase base para todos los colectores"""

    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "OMA-CORE/1.0 (Intelligence Platform)"
        })

    def collect(self) -> List[Event]:
        """Método principal — debe implementarse en cada colector"""
        raise NotImplementedError

    def _make_request(self, url: str, params: Dict = None, timeout: int = 30) -> Optional[Dict]:
        """Wrapper seguro para requests"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else {"text": response.text}
        except Exception as e:
            print(f"[{self.name}] Error en request: {e}")
            return None


class CoinGeckoCollector(BaseCollector):
    """
    Colector de datos de CoinGecko.
    Proporciona: precios, volumen, market cap, cambios 24h, tendencias.
    API gratuita: 10-30 calls/minuto.
    """

    API_BASE = "https://api.coingecko.com/api/v3"

    # Mapeo de símbolos a IDs de CoinGecko
    CRYPTO_MAP = {
        "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
        "SOL": "solana", "XRP": "ripple", "ADA": "cardano",
        "DOGE": "dogecoin", "TRX": "tron", "AVAX": "avalanche-2",
        "DOT": "polkadot", "LINK": "chainlink", "MATIC": "matic-network",
        "LTC": "litecoin", "BCH": "bitcoin-cash", "UNI": "uniswap",
        "ATOM": "cosmos", "ETC": "ethereum-classic", "XLM": "stellar",
        "FIL": "filecoin", "ALGO": "algorand", "VET": "vechain",
        "ICP": "internet-computer", "HBAR": "hedera-hashgraph",
        "NEAR": "near", "APT": "aptos", "OP": "optimism",
        "ARB": "arbitrum", "SUI": "sui", "SEI": "sei-network"
    }

    def __init__(self):
        super().__init__("coingecko")

    def collect(self) -> List[Event]:
        """Obtiene datos de mercado y genera eventos de precio/volumen"""
        events = []

        # 1. Top 50 cryptos con datos de mercado
        market_data = self._get_market_data()
        if market_data:
            events.extend(self._process_market_data(market_data))

        # 2. Tendencias de búsqueda (trending)
        trending = self._get_trending()
        if trending:
            events.extend(self._process_trending(trending))

        return events

    def _get_market_data(self) -> Optional[List[Dict]]:
        """Obtiene datos de mercado de top cryptos"""
        url = f"{self.API_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h,7d"
        }
        return self._make_request(url, params)

    def _process_market_data(self, data: List[Dict]) -> List[Event]:
        """Procesa datos de mercado en eventos"""
        events = []

        for coin in data:
            symbol = coin.get("symbol", "").upper()
            name = coin.get("name", "")
            price = coin.get("current_price", 0)
            change_24h = coin.get("price_change_percentage_24h_in_currency") or coin.get("price_change_percentage_24h", 0)
            change_7d = coin.get("price_change_percentage_7d_in_currency") or 0
            volume = coin.get("total_volume", 0)
            market_cap = coin.get("market_cap", 0)

            # Detectar movimientos significativos (>5% en 24h)
            if abs(change_24h) >= 5:
                event_type = EventType.PRICE_MOVEMENT
                urgency = Urgency.HIGH if abs(change_24h) >= 10 else Urgency.MEDIUM
                sentiment = Sentiment.BULLISH if change_24h > 0 else Sentiment.BEARISH

                event = Event(
                    id=str(uuid.uuid4()),
                    source="coingecko",
                    source_url=f"https://www.coingecko.com/en/coins/{coin.get('id')}",
                    event_type=event_type,
                    title=f"{symbol} {'+' if change_24h > 0 else ''}{change_24h:.2f}% en 24h — ${price:,.2f}",
                    summary=f"{name} ({symbol}) ha movido {change_24h:.2f}% en las últimas 24h. "
                            f"Volumen: ${volume:,.0f}. Market Cap: ${market_cap:,.0f}.",
                    timestamp=datetime.utcnow(),
                    assets=[Asset(
                        symbol=symbol,
                        name=name,
                        asset_class=AssetClass.CRYPTO,
                        price_at_event=price,
                        currency="USD"
                    )],
                    keywords=[symbol, name, "crypto", "price-movement"],
                    sentiment=sentiment,
                    sentiment_score=change_24h / 100,
                    urgency=urgency,
                    confidence=0.85,
                    metadata={
                        "change_24h": change_24h,
                        "change_7d": change_7d,
                        "volume_24h": volume,
                        "market_cap": market_cap,
                        "rank": coin.get("market_cap_rank")
                    }
                )
                events.append(event)

            # Detectar picos de volumen (volumen > 3x promedio implícito)
            # Simplificado: volumen muy alto relativo a market cap
            volume_to_mcap = volume / market_cap if market_cap > 0 else 0
            if volume_to_mcap > 0.15:  # Volumen > 15% del market cap en 24h
                event = Event(
                    id=str(uuid.uuid4()),
                    source="coingecko",
                    source_url=f"https://www.coingecko.com/en/coins/{coin.get('id')}",
                    event_type=EventType.VOLUME_SPIKE,
                    title=f"Volumen anómalo en {symbol} — ${volume:,.0f} en 24h",
                    summary=f"{name} muestra volumen de trading excepcional: ${volume:,.0f} en 24h. "
                            f"Esto representa el {volume_to_mcap*100:.1f}% de su market cap.",
                    timestamp=datetime.utcnow(),
                    assets=[Asset(
                        symbol=symbol, name=name, asset_class=AssetClass.CRYPTO,
                        price_at_event=price, currency="USD"
                    )],
                    keywords=[symbol, "volume-spike", "crypto"],
                    urgency=Urgency.MEDIUM,
                    confidence=0.75,
                    metadata={"volume_24h": volume, "volume_to_mcap": volume_to_mcap}
                )
                events.append(event)

        return events

    def _get_trending(self) -> Optional[List[Dict]]:
        """Obtiene cryptos en tendencia"""
        url = f"{self.API_BASE}/search/trending"
        result = self._make_request(url)
        return result.get("coins", []) if result else None

    def _process_trending(self, data: List[Dict]) -> List[Event]:
        """Procesa cryptos en tendencia"""
        events = []

        for item in data:
            coin = item.get("item", {})
            symbol = coin.get("symbol", "").upper()
            name = coin.get("name", "")

            event = Event(
                id=str(uuid.uuid4()),
                source="coingecko",
                source_url=f"https://www.coingecko.com/en/coins/{coin.get('id')}",
                event_type=EventType.SOCIAL_TREND,
                title=f"🔥 {symbol} en tendencia (#{coin.get('market_cap_rank', '?')})",
                summary=f"{name} ({symbol}) está en las búsquedas más populares de CoinGecko. "
                        f"Score de tendencia: {coin.get('score', 'N/A')}.",
                timestamp=datetime.utcnow(),
                assets=[Asset(symbol=symbol, name=name, asset_class=AssetClass.CRYPTO, currency="USD")],
                keywords=[symbol, "trending", "social"],
                sentiment=Sentiment.BULLISH,
                urgency=Urgency.LOW,
                confidence=0.7,
                metadata={"trending_score": coin.get("score"), "market_cap_rank": coin.get("market_cap_rank")}
            )
            events.append(event)

        return events


class YahooFinanceCollector(BaseCollector):
    """
    Colector de Yahoo Finance vía yfinance.
    Stocks, Forex, Commodities (Oro, Plata, Petróleo).
    """

    # Símbolos a monitorear
    WATCHLIST = {
        # Stocks
        "AAPL": "Apple Inc.", "MSFT": "Microsoft", "GOOGL": "Alphabet",
        "AMZN": "Amazon", "TSLA": "Tesla", "NVDA": "NVIDIA",
        "META": "Meta", "JPM": "JPMorgan", "V": "Visa",
        "WMT": "Walmart", "JNJ": "Johnson & Johnson", "UNH": "UnitedHealth",
        "XOM": "Exxon Mobil", "BAC": "Bank of America", "PG": "Procter & Gamble",
        "MA": "Mastercard", "HD": "Home Depot", "CVX": "Chevron",
        "ABBV": "AbbVie", "KO": "Coca-Cola",

        # Forex
        "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
        "USDCHF=X": "USD/CHF", "AUDUSD=X": "AUD/USD", "USDCAD=X": "USD/CAD",

        # Commodities
        "GC=F": "Oro", "SI=F": "Plata", "HG=F": "Cobre",
        "CL=F": "Petróleo Crudo WTI", "BZ=F": "Petróleo Brent",
        "NG=F": "Gas Natural", "ZW=F": "Trigo", "ZC=F": "Maíz",

        # Índices
        "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ",
        "^VIX": "VIX (Volatilidad)", "^FTSE": "FTSE 100", "^N225": "Nikkei 225"
    }

    def __init__(self):
        super().__init__("yahoo_finance")
        self.yf = None
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            print("[yahoo_finance] yfinance no instalado. Instalar con: pip install yfinance")

    def collect(self) -> List[Event]:
        """Obtiene datos de mercado y genera eventos"""
        if not self.yf:
            return []

        events = []

        # Descargar datos de los últimos 2 días
        symbols = list(self.WATCHLIST.keys())

        try:
            data = self.yf.download(symbols, period="2d", interval="1d", progress=False, threads=True)

            if data.empty:
                return events

            for symbol in symbols:
                try:
                    symbol_events = self._process_symbol(symbol, data)
                    events.extend(symbol_events)
                except Exception as e:
                    print(f"[yahoo_finance] Error procesando {symbol}: {e}")
                    continue

        except Exception as e:
            print(f"[yahoo_finance] Error descargando datos: {e}")

        return events

    def _process_symbol(self, symbol: str, data) -> List[Event]:
        """Procesa datos de un símbolo"""
        events = []
        name = self.WATCHLIST.get(symbol, symbol)

        try:
            # Extraer datos del símbolo
            if len(symbols := list(self.WATCHLIST.keys())) > 1:
                close = data["Close"][symbol]
                volume = data["Volume"][symbol]
            else:
                close = data["Close"]
                volume = data["Volume"]

            if len(close) < 2:
                return events

            current_price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0

            # Determinar asset class
            asset_class = self._get_asset_class(symbol)

            # Detectar movimiento significativo
            threshold = 3 if asset_class == AssetClass.CRYPTO else 2 if asset_class == AssetClass.STOCK else 1

            if abs(change_pct) >= threshold:
                event_type = EventType.PRICE_MOVEMENT
                urgency = Urgency.HIGH if abs(change_pct) >= threshold * 2 else Urgency.MEDIUM
                sentiment = Sentiment.BULLISH if change_pct > 0 else Sentiment.BEARISH

                event = Event(
                    id=str(uuid.uuid4()),
                    source="yahoo_finance",
                    source_url=f"https://finance.yahoo.com/quote/{symbol}",
                    event_type=event_type,
                    title=f"{symbol.replace('=X', '').replace('^', '')} {'+' if change_pct > 0 else ''}{change_pct:.2f}% — ${current_price:,.2f}",
                    summary=f"{name} movió {change_pct:.2f}% en la última sesión. "
                            f"Precio actual: ${current_price:,.2f}. Volumen: {int(volume.iloc[-1]):,}.",
                    timestamp=datetime.utcnow(),
                    assets=[Asset(
                        symbol=symbol.replace("=X", "").replace("^", ""),
                        name=name,
                        asset_class=asset_class,
                        price_at_event=current_price,
                        currency="USD"
                    )],
                    keywords=[symbol, name, asset_class.value, "price-movement"],
                    sentiment=sentiment,
                    sentiment_score=change_pct / 100,
                    urgency=urgency,
                    confidence=0.9,
                    metadata={
                        "change_pct": change_pct,
                        "previous_close": prev_price,
                        "volume": int(volume.iloc[-1]) if not volume.empty else 0
                    }
                )
                events.append(event)

        except Exception as e:
            print(f"[yahoo_finance] Error en {symbol}: {e}")

        return events

    def _get_asset_class(self, symbol: str) -> AssetClass:
        """Determina la clase de activo"""
        if "=X" in symbol:
            return AssetClass.FOREX
        elif symbol in ["GC=F", "SI=F", "HG=F", "CL=F", "BZ=F", "NG=F", "ZW=F", "ZC=F"]:
            return AssetClass.COMMODITY
        elif symbol.startswith("^"):
            return AssetClass.INDEX
        else:
            return AssetClass.STOCK


class RSSCollector(BaseCollector):
    """
    Colector de feeds RSS financieros.
    Noticias de múltiples fuentes.
    """

    FEEDS = {
        "reuters_business": "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best",
        "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "cointelegraph": "https://cointelegraph.com/rss",
        "forexlive": "https://www.forexlive.com/feed",
        "investing": "https://www.investing.com/rss/news.rss",
        "marketwatch": "https://www.marketwatch.com/rss/topstories",
        "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "bloomberg": "https://feeds.bloomberg.com/business/news.rss",
    }

    # Keywords para clasificación
    CRYPTO_KEYWORDS = ["bitcoin", "ethereum", "crypto", "blockchain", "defi", "nft", "altcoin", 
                       "btc", "eth", "solana", "cardano", "binance", "coinbase", "mining"]
    FOREX_KEYWORDS = ["forex", "dollar", "euro", "yen", "pound", "fed", "ecb", "boe", 
                      "interest rate", "currency", "exchange rate", "usd", "eur", "gbp", "jpy"]
    STOCK_KEYWORDS = ["stock", "shares", "earnings", "ipo", "merger", "acquisition", 
                      "dividend", "bull market", "bear market", "nasdaq", "s&p", "dow"]
    COMMODITY_KEYWORDS = ["gold", "silver", "oil", "crude", "copper", "natural gas", 
                          "commodity", "opec", "precious metal", "wti", "brent"]

    URGENT_KEYWORDS = ["breaking", "urgent", "alert", "crash", "surge", "plunge", 
                       "soar", "tank", "collapse", "rally", "emergency", "crisis"]

    def __init__(self):
        super().__init__("rss")

    def collect(self) -> List[Event]:
        """Obtiene noticias de RSS feeds"""
        events = []

        for feed_name, feed_url in self.FEEDS.items():
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:10]:  # Últimas 10 noticias por feed
                    event = self._process_entry(entry, feed_name)
                    if event:
                        events.append(event)

            except Exception as e:
                print(f"[rss] Error en feed {feed_name}: {e}")
                continue

        return events

    def _process_entry(self, entry, feed_name: str) -> Optional[Event]:
        """Procesa una entrada RSS en Event"""
        title = entry.get("title", "")
        summary = entry.get("summary", "") or entry.get("description", "")
        link = entry.get("link", "")
        published = entry.get("published_parsed") or entry.get("updated_parsed")

        if not title:
            return None

        # Parsear fecha
        try:
            if published:
                timestamp = datetime(*published[:6])
            else:
                timestamp = datetime.utcnow()
        except:
            timestamp = datetime.utcnow()

        # Clasificar tipo de evento
        content_lower = (title + " " + summary).lower()
        event_type, asset_class, keywords = self._classify_content(content_lower)

        # Detectar sentimiento
        sentiment, sentiment_score = self._detect_sentiment(content_lower)

        # Detectar urgencia
        urgency = self._detect_urgency(content_lower)

        # Detectar activos mencionados
        assets = self._detect_assets(content_lower, asset_class)

        # Detectar regiones
        regions = self._detect_regions(content_lower)

        event = Event(
            id=str(uuid.uuid4()),
            source=f"rss_{feed_name}",
            source_url=link,
            event_type=event_type,
            title=title,
            summary=summary[:500] if summary else title,
            raw_content=summary,
            timestamp=timestamp,
            assets=assets,
            keywords=keywords,
            regions=regions,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            urgency=urgency,
            confidence=0.7,
            language="en"
        )

        return event

    def _classify_content(self, content: str) -> tuple:
        """Clasifica el contenido en tipo de evento y asset class"""
        keywords_found = []

        # Detectar clase de activo
        if any(kw in content for kw in self.CRYPTO_KEYWORDS):
            asset_class = AssetClass.CRYPTO
            keywords_found.extend(self.CRYPTO_KEYWORDS)
        elif any(kw in content for kw in self.FOREX_KEYWORDS):
            asset_class = AssetClass.FOREX
            keywords_found.extend(self.FOREX_KEYWORDS)
        elif any(kw in content for kw in self.COMMODITY_KEYWORDS):
            asset_class = AssetClass.COMMODITY
            keywords_found.extend(self.COMMODITY_KEYWORDS)
        elif any(kw in content for kw in self.STOCK_KEYWORDS):
            asset_class = AssetClass.STOCK
            keywords_found.extend(self.STOCK_KEYWORDS)
        else:
            asset_class = AssetClass.STOCK  # Default

        # Detectar tipo de evento
        if any(kw in content for kw in ["hack", "exploit", "breach", "attack", "stolen"]):
            event_type = EventType.HACK_EXPLOIT
        elif any(kw in content for kw in ["regulation", "sec", "ban", "legal", "law", "compliance"]):
            event_type = EventType.REGULATORY
        elif any(kw in content for kw in ["war", "conflict", "sanction", "geopolitical", "tension"]):
            event_type = EventType.GEOPOLITICAL
        elif any(kw in content for kw in ["earnings", "revenue", "profit", "quarterly", "report"]):
            event_type = EventType.EARNINGS
        elif any(kw in content for kw in ["merger", "acquisition", "acquire", "buyout"]):
            event_type = EventType.MERGER_ACQUISITION
        elif any(kw in content for kw in ["fed", "ecb", "interest rate", "inflation", "gdp", "unemployment"]):
            event_type = EventType.MACRO_EVENT
        else:
            event_type = EventType.NEWS

        return event_type, asset_class, list(set(kw for kw in keywords_found if kw in content))

    def _detect_sentiment(self, content: str) -> tuple:
        """Detecta sentimiento básico"""
        bullish = ["surge", "rally", "soar", "jump", "gain", "rise", "bull", "breakout", 
                   "moon", "pump", " ATH", "all-time high", "strong", "growth", "boom"]
        bearish = ["crash", "plunge", "tank", "drop", "fall", "bear", "dump", "collapse",
                   "decline", "loss", "sell-off", "correction", "recession", "fear"]

        bull_count = sum(1 for w in bullish if w in content)
        bear_count = sum(1 for w in bearish if w in content)

        if bull_count > bear_count:
            return Sentiment.BULLISH, min(bull_count * 0.2, 1.0)
        elif bear_count > bull_count:
            return Sentiment.BEARISH, -min(bear_count * 0.2, 1.0)
        else:
            return Sentiment.NEUTRAL, 0.0

    def _detect_urgency(self, content: str) -> Urgency:
        """Detecta nivel de urgencia"""
        if any(kw in content for kw in ["breaking", "urgent", "alert", "crash", "collapse", "emergency"]):
            return Urgency.CRITICAL
        elif any(kw in content for kw in ["surge", "plunge", "soar", "tank", "rally"]):
            return Urgency.HIGH
        elif any(kw in content for kw in ["update", "report", "announce", "launch"]):
            return Urgency.MEDIUM
        else:
            return Urgency.LOW

    def _detect_assets(self, content: str, asset_class: AssetClass) -> List[Asset]:
        """Detecta activos mencionados en el contenido"""
        assets = []

        # Mapeo de símbolos comunes
        symbol_map = {
            AssetClass.CRYPTO: {
                "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL", 
                "cardano": "ADA", "ripple": "XRP", "binance": "BNB",
                "dogecoin": "DOGE", "polkadot": "DOT", "chainlink": "LINK"
            },
            AssetClass.STOCK: {
                "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
                "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA",
                "meta": "META", "facebook": "META", "netflix": "NFLX"
            },
            AssetClass.FOREX: {
                "eur/usd": "EURUSD", "gbp/usd": "GBPUSD", "usd/jpy": "USDJPY",
                "usd/chf": "USDCHF", "aud/usd": "AUDUSD", "usd/cad": "USDCAD"
            },
            AssetClass.COMMODITY: {
                "gold": "GC=F", "silver": "SI=F", "copper": "HG=F",
                "oil": "CL=F", "crude": "CL=F", "brent": "BZ=F",
                "natural gas": "NG=F"
            }
        }

        mappings = symbol_map.get(asset_class, {})
        for name, symbol in mappings.items():
            if name in content:
                assets.append(Asset(
                    symbol=symbol,
                    name=name.title(),
                    asset_class=asset_class,
                    currency="USD"
                ))

        return assets

    def _detect_regions(self, content: str) -> List[str]:
        """Detecta regiones/países mencionados"""
        regions = []
        region_map = {
            "united states": "USA", "us ": "USA", "america": "USA", "washington": "USA",
            "china": "China", "beijing": "China", "chinese": "China",
            "europe": "Europe", "european": "Europe", "eu ": "Europe",
            "japan": "Japan", "tokyo": "Japan", "japanese": "Japan",
            "uk": "UK", "united kingdom": "UK", "britain": "UK", "london": "UK",
            "germany": "Germany", "berlin": "Germany", "german": "Germany",
            "france": "France", "paris": "France", "french": "France",
            "russia": "Russia", "russian": "Russia", "moscow": "Russia",
            "india": "India", "indian": "India", "mumbai": "India",
            "brazil": "Brazil", "brazilian": "Brazil", "saudi": "Saudi Arabia",
            "uae": "UAE", "dubai": "UAE", "israel": "Israel", "gaza": "Palestine",
            "ukraine": "Ukraine", "iran": "Iran", "north korea": "North Korea"
        }

        for region_name, code in region_map.items():
            if region_name in content and code not in regions:
                regions.append(code)

        return regions


class GDELTCollector(BaseCollector):
    """
    Colector de GDELT v2 API.
    Eventos globales con metadatos de impacto y tono.
    API pública, masiva, gratuita.
    """

    API_BASE = "https://api.gdeltproject.org/api/v2"

    # Temas relevantes para trading
    RELEVANT_THEMES = [
        "ECON_BANKRUPTCY", "ECON_BOYCOTT", "ECON_CENTRALBANK", "ECON_CURRENCY",
        "ECON_DEBT", "ECON_ENTREPRENEURSHIP", "ECON_HOUSINGPRICES", "ECON_INFLATION",
        "ECON_INTERESTRATES", "ECON_IPO", "ECON_MONOPOLY", "ECON_PRICECONTROL",
        "ECON_STOCKMARKET", "ECON_SUBSIDIES", "ECON_TRADE", "ECON_UNEMPLOYMENT",
        "TAX_GOODSANDSERVICES", "TAX_WORLDBANK", "WB_135_TRANSPORT", "WB_1661_DIGITALGOVERNMENT",
        "WB_178_TRANSPORTATION", "WB_199_ENERGY", "WB_214_COMPETITIVENESS",
        "WB_223_FINANCIALSECTOR", "WB_246_POOR", "WB_278_TAXATION",
        "WB_310_CLIMATECHANGE", "WB_696_BROADCASTMEDIA", "WB_697_INFORMATIONTECHNOLOGY",
        "WB_698_TELECOMMUNICATIONS", "WB_916_CRYPTOASSET", "WB_917_CRYPTOCURRENCY",
        "WB_918_BLOCKCHAIN", "WB_919_DIGITALCURRENCY", "WB_920_CENTRALBANKDIGITALCURRENCY"
    ]

    def __init__(self):
        super().__init__("gdelt")

    def collect(self) -> List[Event]:
        """Obtiene eventos de GDELT de las últimas 24h"""
        events = []

        # Usar el endpoint de artículos (más rico en datos)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)

        # Formato: YYYYMMDDHHMMSS
        start_str = start_date.strftime("%Y%m%d%H%M%S")
        end_str = end_date.strftime("%Y%m%d%H%M%S")

        params = {
            "query": " OR ".join([f'theme:"{t}"' for t in self.RELEVANT_THEMES[:10]]),
            "mode": "ArtList",
            "maxrecords": 50,
            "format": "json",
            "startdatetime": start_str,
            "enddatetime": end_str,
            "sort": " tonedesc"  # Más negativo primero (más impacto)
        }

        url = f"{self.API_BASE}/doc/doc"

        try:
            result = self._make_request(url, params)
            if result and "articles" in result:
                for article in result["articles"]:
                    event = self._process_article(article)
                    if event:
                        events.append(event)
        except Exception as e:
            print(f"[gdelt] Error: {e}")

        return events

    def _process_article(self, article: Dict) -> Optional[Event]:
        """Procesa un artículo GDELT en Event"""
        title = article.get("title", "")
        url = article.get("url", "")

        if not title:
            return None

        # Extraer tono (sentimiento GDELT: -100 a +100)
        tone = article.get("tone", 0)

        # Normalizar sentimiento
        if tone < -5:
            sentiment = Sentiment.VERY_BEARISH
        elif tone < -2:
            sentiment = Sentiment.BEARISH
        elif tone > 5:
            sentiment = Sentiment.VERY_BULLISH
        elif tone > 2:
            sentiment = Sentiment.BULLISH
        else:
            sentiment = Sentiment.NEUTRAL

        sentiment_score = tone / 100

        # Detectar tipo de evento por temas
        themes = article.get("themes", "")
        event_type = self._classify_by_themes(themes)

        # Urgencia por impacto social
        social = article.get("socialimage", "")
        urgency = Urgency.HIGH if social and "high" in social.lower() else Urgency.MEDIUM

        # Detectar regiones
        locations = article.get("locations", "")
        regions = [r.strip() for r in locations.split(";") if r.strip()] if locations else []

        event = Event(
            id=str(uuid.uuid4()),
            source="gdelt",
            source_url=url,
            event_type=event_type,
            title=title,
            summary=article.get("seendate", ""),
            timestamp=datetime.utcnow(),
            keywords=[t.strip() for t in themes.split(";") if t.strip()][:10],
            regions=regions,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            urgency=urgency,
            confidence=0.65,
            metadata={
                "gdelt_tone": tone,
                "gdelt_themes": themes,
                "gdelt_locations": locations,
                "gdelt_seendate": article.get("seendate"),
                "gdelt_domain": article.get("domain")
            }
        )

        return event

    def _classify_by_themes(self, themes: str) -> EventType:
        """Clasifica evento por temas GDELT"""
        themes_lower = themes.lower()

        if "bankruptcy" in themes_lower or "debt" in themes_lower:
            return EventType.MACRO_EVENT
        elif "stockmarket" in themes_lower or "ipo" in themes_lower:
            return EventType.PRICE_MOVEMENT
        elif "cryptocurrency" in themes_lower or "blockchain" in themes_lower or "cryptoasset" in themes_lower:
            return EventType.NEWS
        elif "centralbank" in themes_lower or "interestrates" in themes_lower or "inflation" in themes_lower:
            return EventType.MACRO_EVENT
        elif "trade" in themes_lower or "boycott" in themes_lower:
            return EventType.GEOPOLITICAL
        else:
            return EventType.NEWS


class WorldMonitor:
    """
    Orquestador de colectores.
    Ejecuta todos los colectores y consolida eventos.
    """

    def __init__(self):
        self.collectors = [
            CoinGeckoCollector(),
            # YahooFinanceCollector(),  # Requiere yfinance instalado
            RSSCollector(),
            GDELTCollector()
        ]

    def collect_all(self) -> List[Event]:
        """Ejecuta todos los colectores y retorna eventos consolidados"""
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

    def collect_by_source(self, source_name: str) -> List[Event]:
        """Ejecuta un colector específico por nombre"""
        for collector in self.collectors:
            if collector.name == source_name:
                return collector.collect()
        return []
