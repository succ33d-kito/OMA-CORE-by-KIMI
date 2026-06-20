"""O.M.A.-C.O.R.E. RSS News Collector"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from core.collectors.base_collector import BaseCollector
from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency

class RSSCollector(BaseCollector):
    RSS_SOURCES = {
        "rss_reuters_business": {
            "url": "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best",
            "confidence": 0.90,
            "focus": ["stocks", "markets", "macro", "earnings"],
            "language": "en",
        },
        "rss_bloomberg": {
            "url": "https://feeds.bloomberg.com/business/news.rss",
            "confidence": 0.90,
            "focus": ["stocks", "markets", "macro", "tech"],
            "language": "en",
        },
        "rss_coindesk": {
            "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "confidence": 0.80,
            "focus": ["crypto", "bitcoin", "ethereum", "regulation"],
            "language": "en",
        },
        "rss_cointelegraph": {
            "url": "https://cointelegraph.com/rss",
            "confidence": 0.80,
            "focus": ["crypto", "blockchain", "defi", "nft"],
            "language": "en",
        },
        "rss_forexlive": {
            "url": "https://www.forexlive.com/feed",
            "confidence": 0.80,
            "focus": ["forex", "central-banks", "macro"],
            "language": "en",
        },
        "rss_cnbc": {
            "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "confidence": 0.80,
            "focus": ["stocks", "markets", "earnings", "tech"],
            "language": "en",
        },
        "rss_marketwatch": {
            "url": "https://www.marketwatch.com/rss/topstories",
            "confidence": 0.80,
            "focus": ["stocks", "markets", "personal-finance"],
            "language": "en",
        },
    }

    KEYWORDS_CRYPTO = ["bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", "blockchain", "defi", "nft", "altcoin", "mining", "wallet"]
    KEYWORDS_STOCKS = ["stock", "shares", "equity", "earnings", "revenue", "profit", "dividend", "ipo", "merger", "acquisition", "buyback"]
    KEYWORDS_MACRO = ["fed", "federal reserve", "interest rate", "inflation", "cpi", "gdp", "unemployment", "recession", "stimulus", "fiscal"]
    KEYWORDS_GEO = ["war", "sanctions", "treaty", "election", "vote", "president", "prime minister", "conflict", "diplomatic", "nato", "eu"]
    KEYWORDS_REGULATORY = ["sec", "regulation", "regulatory", "compliance", "law", "bill", "legislation", "ban", "approve", "license"]
    KEYWORDS_HACK = ["hack", "exploit", "breach", "security", "vulnerability", "stolen", "attack", "ransomware", "phishing"]
    BULLISH_WORDS = ["surge", "rally", "soar", "jump", "gain", "rise", "bullish", "breakout", " ATH", "record high", "strong", "beat", "exceed"]
    BEARISH_WORDS = ["crash", "plunge", "drop", "fall", "decline", "bearish", "breakdown", " ATL", "record low", "weak", "miss", "below"]

    def __init__(self, sources=None):
        super().__init__("rss_feeds", source_confidence=0.80)
        self.sources = sources or list(self.RSS_SOURCES.keys())
        try:
            import feedparser
            self.feedparser = feedparser
        except ImportError:
            print("[rss] feedparser no instalado. Ejecuta: pip install feedparser")
            self.feedparser = None

    def collect(self):
        events = []
        if not self.feedparser:
            return events
        for source_name in self.sources:
            if source_name not in self.RSS_SOURCES:
                continue
            source_config = self.RSS_SOURCES[source_name]
            try:
                feed_events = self._parse_feed(source_name, source_config)
                events.extend(feed_events)
            except Exception as e:
                print(f"[rss] Error en {source_name}: {e}")
                continue
        self.stats["events_generated"] += len(events)
        self.stats["last_run"] = datetime.now(timezone.utc).isoformat()
        return events

    def _parse_feed(self, source_name, config):
        events = []
        feed = self.feedparser.parse(config["url"])
        for entry in feed.entries[:20]:
            try:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                link = entry.get("link", "")
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    try:
                        timestamp = datetime(*published[:6], tzinfo=timezone.utc)
                    except:
                        timestamp = datetime.now(timezone.utc)
                else:
                    timestamp = datetime.now(timezone.utc)
                age_hours = (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600
                if age_hours > 24:
                    continue
                event_type, sentiment, sentiment_score, urgency = self._classify_news(title, summary, config["focus"])
                assets = self._extract_assets(title + " " + summary)
                keywords = self._extract_keywords(title + " " + summary)
                events.append(Event(
                    id=str(uuid.uuid4()), source=source_name, source_url=link,
                    event_type=event_type, title=title[:200], summary=summary[:500],
                    raw_content=title + "\n" + summary, timestamp=timestamp,
                    assets=assets, keywords=keywords, sentiment=sentiment,
                    sentiment_score=sentiment_score, urgency=urgency,
                    confidence=config["confidence"], language=config["language"],
                    metadata={"source_name": source_name, "feed_title": feed.feed.get("title", ""), "published": entry.get("published", ""), "focus_areas": config["focus"]}
                ))
            except Exception as e:
                print(f"[rss] Error procesando entrada: {e}")
                continue
        return events

    def _classify_news(self, title, summary, focus):
        text = (title + " " + summary).lower()
        if any(kw in text for kw in self.KEYWORDS_HACK):
            event_type = EventType.HACK_EXPLOIT
            urgency = Urgency.CRITICAL
        elif any(kw in text for kw in self.KEYWORDS_REGULATORY):
            event_type = EventType.REGULATORY
            urgency = Urgency.HIGH
        elif any(kw in text for kw in self.KEYWORDS_GEO):
            event_type = EventType.GEOPOLITICAL
            urgency = Urgency.HIGH
        elif any(kw in text for kw in self.KEYWORDS_MACRO):
            event_type = EventType.MACRO_EVENT
            urgency = Urgency.HIGH
        elif any(kw in text for kw in self.KEYWORDS_CRYPTO):
            event_type = EventType.NEWS
            urgency = Urgency.MEDIUM
        elif any(kw in text for kw in self.KEYWORDS_STOCKS):
            event_type = EventType.EARNINGS if "earnings" in text else EventType.NEWS
            urgency = Urgency.MEDIUM
        else:
            event_type = EventType.NEWS
            urgency = Urgency.LOW
        bullish_count = sum(1 for w in self.BULLISH_WORDS if w in text)
        bearish_count = sum(1 for w in self.BEARISH_WORDS if w in text)
        if bullish_count > bearish_count:
            sentiment = Sentiment.BULLISH
            sentiment_score = min(0.3 + (bullish_count - bearish_count) * 0.1, 1.0)
        elif bearish_count > bullish_count:
            sentiment = Sentiment.BEARISH
            sentiment_score = max(-0.3 - (bearish_count - bullish_count) * 0.1, -1.0)
        else:
            sentiment = Sentiment.NEUTRAL
            sentiment_score = 0.0
        if abs(sentiment_score) > 0.7:
            urgency = Urgency.HIGH if urgency.value < Urgency.HIGH.value else urgency
        return event_type, sentiment, sentiment_score, urgency

    def _extract_assets(self, text):
        assets = []
        text_upper = text.upper()
        symbol_map = {
            "BTC": ("Bitcoin", AssetClass.CRYPTO), "BITCOIN": ("Bitcoin", AssetClass.CRYPTO),
            "ETH": ("Ethereum", AssetClass.CRYPTO), "ETHEREUM": ("Ethereum", AssetClass.CRYPTO),
            "SOL": ("Solana", AssetClass.CRYPTO), "XRP": ("Ripple", AssetClass.CRYPTO),
            "BNB": ("Binance Coin", AssetClass.CRYPTO), "ADA": ("Cardano", AssetClass.CRYPTO),
            "DOGE": ("Dogecoin", AssetClass.CRYPTO), "AVAX": ("Avalanche", AssetClass.CRYPTO),
            "AAPL": ("Apple Inc.", AssetClass.STOCK), "MSFT": ("Microsoft Corp.", AssetClass.STOCK),
            "GOOGL": ("Alphabet Inc.", AssetClass.STOCK), "AMZN": ("Amazon.com Inc.", AssetClass.STOCK),
            "TSLA": ("Tesla Inc.", AssetClass.STOCK), "NVDA": ("NVIDIA Corp.", AssetClass.STOCK),
            "META": ("Meta Platforms Inc.", AssetClass.STOCK), "NFLX": ("Netflix Inc.", AssetClass.STOCK),
            "AMD": ("AMD Inc.", AssetClass.STOCK), "INTC": ("Intel Corp.", AssetClass.STOCK),
            "EURUSD": ("EUR/USD", AssetClass.FOREX), "GBPUSD": ("GBP/USD", AssetClass.FOREX),
            "USDJPY": ("USD/JPY", AssetClass.FOREX), "GOLD": ("Gold", AssetClass.COMMODITY),
            "SILVER": ("Silver", AssetClass.COMMODITY), "OIL": ("Crude Oil", AssetClass.COMMODITY),
        }
        for symbol, (name, asset_class) in symbol_map.items():
            if symbol in text_upper:
                if not any(a.symbol == symbol for a in assets):
                    assets.append(Asset(symbol=symbol, name=name, asset_class=asset_class, currency="USD"))
        return assets

    def _extract_keywords(self, text):
        text_lower = text.lower()
        keywords = []
        all_keywords = self.KEYWORDS_CRYPTO + self.KEYWORDS_STOCKS + self.KEYWORDS_MACRO + self.KEYWORDS_GEO + self.KEYWORDS_REGULATORY + self.KEYWORDS_HACK + self.BULLISH_WORDS + self.BEARISH_WORDS
        for kw in all_keywords:
            if kw in text_lower:
                keywords.append(kw)
        return list(set(keywords))[:10]
