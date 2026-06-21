#!/usr/bin/env python3
import os

PROJECT = "/home/kito/Projects/OMA-CORE by KIMI"

files = {}

files["core/schemas/event_schema.py"] = r'''"""O.M.A.-C.O.R.E. Event Schema"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
import json

class EventType(Enum):
    NEWS = "news"
    PRICE_MOVEMENT = "price_movement"
    VOLUME_SPIKE = "volume_spike"
    SENTIMENT_SHIFT = "sentiment_shift"
    MACRO_EVENT = "macro_event"
    GEOPOLITICAL = "geopolitical"
    REGULATORY = "regulatory"
    WHALE_MOVEMENT = "whale_movement"
    HACK_EXPLOIT = "hack_exploit"
    SOCIAL_TREND = "social_trend"
    TECHNICAL_SIGNAL = "technical_signal"
    EARNINGS = "earnings"
    MERGER_ACQUISITION = "merger_acquisition"

class AssetClass(Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCK = "stock"
    COMMODITY = "commodity"
    INDEX = "index"
    BOND = "bond"

class Sentiment(Enum):
    VERY_BULLISH = 2
    BULLISH = 1
    NEUTRAL = 0
    BEARISH = -1
    VERY_BEARISH = -2

class Urgency(Enum):
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    BACKGROUND = 0

@dataclass
class Asset:
    symbol: str
    name: str
    asset_class: AssetClass
    exchange: Optional[str] = None
    price_at_event: Optional[float] = None
    currency: str = "USD"
    
    def to_dict(self):
        return {
            "symbol": self.symbol, "name": self.name,
            "asset_class": self.asset_class.value,
            "exchange": self.exchange,
            "price_at_event": self.price_at_event,
            "currency": self.currency
        }

@dataclass
class Event:
    id: str
    source: str
    source_url: Optional[str] = None
    source_id: Optional[str] = None
    event_type: EventType = EventType.NEWS
    category: Optional[str] = None
    title: str = ""
    summary: str = ""
    raw_content: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    assets: List[Asset] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)
    sentiment: Sentiment = Sentiment.NEUTRAL
    sentiment_score: float = 0.0
    urgency: Urgency = Urgency.LOW
    confidence: float = 0.0
    impact_score: Optional[float] = None
    relevance_score: Optional[float] = None
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    enriched: bool = False
    
    def to_dict(self):
        return {
            "id": self.id, "source": self.source,
            "source_url": self.source_url, "source_id": self.source_id,
            "event_type": self.event_type.value,
            "category": self.category, "title": self.title,
            "summary": self.summary, "raw_content": self.raw_content,
            "timestamp": self.timestamp.isoformat(),
            "detected_at": self.detected_at.isoformat(),
            "assets": [a.to_dict() for a in self.assets],
            "keywords": self.keywords, "entities": self.entities,
            "regions": self.regions,
            "sentiment": self.sentiment.value,
            "sentiment_score": self.sentiment_score,
            "urgency": self.urgency.value,
            "confidence": self.confidence,
            "impact_score": self.impact_score,
            "relevance_score": self.relevance_score,
            "language": self.language,
            "metadata": json.dumps(self.metadata),
            "processed": self.processed, "enriched": self.enriched
        }
    
    @classmethod
    def from_dict(cls, data):
        event = cls(
            id=data["id"], source=data["source"],
            source_url=data.get("source_url"),
            source_id=data.get("source_id"),
            event_type=EventType(data["event_type"]),
            category=data.get("category"), title=data["title"],
            summary=data.get("summary", ""),
            raw_content=data.get("raw_content"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            detected_at=datetime.fromisoformat(data["detected_at"]),
            sentiment=Sentiment(data["sentiment"]),
            sentiment_score=data.get("sentiment_score", 0.0),
            urgency=Urgency(data["urgency"]),
            confidence=data.get("confidence", 0.0),
            impact_score=data.get("impact_score"),
            relevance_score=data.get("relevance_score"),
            language=data.get("language", "en"),
            metadata=json.loads(data.get("metadata", "{}")),
            processed=data.get("processed", False),
            enriched=data.get("enriched", False)
        )
        if "assets" in data and data["assets"]:
            event.assets = [Asset(
                symbol=a["symbol"], name=a["name"],
                asset_class=AssetClass(a["asset_class"]),
                exchange=a.get("exchange"),
                price_at_event=a.get("price_at_event"),
                currency=a.get("currency", "USD")
            ) for a in data["assets"]]
        event.keywords = data.get("keywords", [])
        event.entities = data.get("entities", [])
        event.regions = data.get("regions", [])
        return event

EVENT_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY, source TEXT NOT NULL, source_url TEXT, source_id TEXT,
    event_type TEXT NOT NULL, category TEXT, title TEXT NOT NULL, summary TEXT,
    raw_content TEXT, timestamp TEXT NOT NULL, detected_at TEXT NOT NULL,
    assets TEXT, keywords TEXT, entities TEXT, regions TEXT, sentiment INTEGER,
    sentiment_score REAL, urgency INTEGER, confidence REAL, impact_score REAL,
    relevance_score REAL, language TEXT, metadata TEXT, processed INTEGER DEFAULT 0,
    enriched INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_urgency ON events(urgency);
CREATE INDEX IF NOT EXISTS idx_events_processed ON events(processed);
"""
'''

files["core/database/db.py"] = r'''"""O.M.A.-C.O.R.E. Database Layer"""
import sqlite3, json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from core.schemas.event_schema import Event, EVENT_TABLE_SCHEMA

class OMACoreDatabase:
    def __init__(self, db_path="oma_core.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        with self._get_connection() as conn:
            conn.executescript(EVENT_TABLE_SCHEMA)
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id TEXT PRIMARY KEY, event_id TEXT NOT NULL, title TEXT NOT NULL,
                    description TEXT, opportunity_type TEXT NOT NULL, asset_class TEXT,
                    assets TEXT, score REAL, conviction REAL, priority TEXT,
                    action_suggested TEXT, risk_level TEXT, timestamp TEXT NOT NULL,
                    expires_at TEXT, status TEXT DEFAULT 'active',
                    FOREIGN KEY (event_id) REFERENCES events(id)
                );
                CREATE INDEX IF NOT EXISTS idx_opp_event ON opportunities(event_id);
                CREATE INDEX IF NOT EXISTS idx_opp_score ON opportunities(score);
                CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status);
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id TEXT PRIMARY KEY, name TEXT, profile_type TEXT NOT NULL,
                    preferences TEXT, watchlist TEXT, risk_tolerance TEXT, created_at TEXT NOT NULL
                );
            """)
    
    def insert_event(self, event: Event) -> str:
        data = event.to_dict()
        for field in ["assets", "keywords", "entities", "regions"]:
            if field in data and data[field] is not None:
                data[field] = json.dumps(data[field])
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO events 
                (id, source, source_url, source_id, event_type, category, title, summary,
                 raw_content, timestamp, detected_at, assets, keywords, entities, regions,
                 sentiment, sentiment_score, urgency, confidence, impact_score, relevance_score,
                 language, metadata, processed, enriched)
                VALUES (:id, :source, :source_url, :source_id, :event_type, :category, :title,
                 :summary, :raw_content, :timestamp, :detected_at, :assets, :keywords,
                 :entities, :regions, :sentiment, :sentiment_score, :urgency, :confidence,
                 :impact_score, :relevance_score, :language, :metadata, :processed, :enriched)
            """, data)
        return event.id
    
    def get_unprocessed_events(self, limit=100):
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE processed = 0 ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [self._row_to_event(row) for row in rows]
    
    def get_recent_events(self, hours=24, limit=50):
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM events WHERE timestamp > datetime('now', '-{} hours')
                   ORDER BY urgency DESC, timestamp DESC LIMIT ?""".format(hours),
                (limit,)
            ).fetchall()
            return [self._row_to_event(row) for row in rows]
    
    def mark_processed(self, event_id):
        with self._get_connection() as conn:
            conn.execute("UPDATE events SET processed = 1 WHERE id = ?", (event_id,))
    
    def update_event_scores(self, event_id, impact, relevance):
        with self._get_connection() as conn:
            conn.execute("UPDATE events SET impact_score = ?, relevance_score = ? WHERE id = ?",
                        (impact, relevance, event_id))
    
    def get_event_stats(self):
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            unprocessed = conn.execute("SELECT COUNT(*) FROM events WHERE processed = 0").fetchone()[0]
            by_type = conn.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type").fetchall()
            by_urgency = conn.execute("SELECT urgency, COUNT(*) FROM events GROUP BY urgency").fetchall()
            return {
                "total_events": total, "unprocessed": unprocessed,
                "by_type": {row[0]: row[1] for row in by_type},
                "by_urgency": {row[0]: row[1] for row in by_urgency}
            }
    
    def _row_to_event(self, row):
        data = dict(row)
        for field in ["assets", "keywords", "entities", "regions"]:
            if data.get(field):
                try: data[field] = json.loads(data[field])
                except: data[field] = []
            else: data[field] = []
        if data.get("metadata"):
            try: data["metadata"] = json.loads(data["metadata"])
            except: data["metadata"] = {}
        return Event.from_dict(data)
    
    def insert_opportunity(self, opportunity):
        opp_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO opportunities 
                (id, event_id, title, description, opportunity_type, asset_class,
                 assets, score, conviction, priority, action_suggested, risk_level,
                 timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (opp_id, opportunity.get("event_id"), opportunity.get("title", ""),
                  opportunity.get("description", ""), opportunity.get("opportunity_type", ""),
                  opportunity.get("asset_class", ""), json.dumps(opportunity.get("assets", [])),
                  opportunity.get("score", 0.0), opportunity.get("conviction", 0.0),
                  opportunity.get("priority", "low"), opportunity.get("action_suggested", ""),
                  opportunity.get("risk_level", "medium"),
                  datetime.now(timezone.utc).isoformat(), "active"))
        return opp_id
    
    def get_active_opportunities(self, limit=50):
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT o.*, e.title as event_title, e.source, e.event_type
                   FROM opportunities o JOIN events e ON o.event_id = e.id
                   WHERE o.status = 'active'
                   ORDER BY o.score DESC, o.conviction DESC LIMIT ?""", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

db = OMACoreDatabase()
'''

files["core/collectors/world_monitor.py"] = r'''"""O.M.A.-C.O.R.E. World Monitor"""
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
            price = coin.get("current_price", 0)
            change_24h = coin.get("price_change_percentage_24h_in_currency") or coin.get("price_change_percentage_24h", 0)
            change_7d = coin.get("price_change_percentage_7d_in_currency") or 0
            volume = coin.get("total_volume", 0)
            market_cap = coin.get("market_cap", 0)
            
            if abs(change_24h) >= 5:
                urgency = Urgency.HIGH if abs(change_24h) >= 10 else Urgency.MEDIUM
                sentiment = Sentiment.BULLISH if change_24h > 0 else Sentiment.BEARISH
                events.append(Event(
                    id=str(uuid.uuid4()), source="coingecko",
                    source_url=f"https://www.coingecko.com/en/coins/{coin.get('id')}",
                    event_type=EventType.PRICE_MOVEMENT,
                    title=f"{symbol} {'+' if change_24h > 0 else ''}{change_24h:.2f}% en 24h — ${price:,.2f}",
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
                    title=f"Volumen anomalo en {symbol} — ${volume:,.0f} en 24h",
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
                title=f"🔥 {symbol} en tendencia (#{coin.get('market_cap_rank', '?')})",
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
'''

files["core/engines/score_opportunity.py"] = r'''"""O.M.A.-C.O.R.E. Score & Opportunity Engine"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
import json
from core.schemas.event_schema import Event, EventType, Sentiment, Urgency, AssetClass
from core.database.db import OMACoreDatabase

class ScoreEngine:
    WEIGHTS = {
        "urgency": 0.25, "sentiment_magnitude": 0.20, "source_confidence": 0.20,
        "asset_relevance": 0.15, "recency": 0.10, "correlation_boost": 0.10
    }
    
    EVENT_MULTIPLIERS = {
        EventType.PRICE_MOVEMENT: 1.2, EventType.VOLUME_SPIKE: 1.1, EventType.HACK_EXPLOIT: 1.5,
        EventType.REGULATORY: 1.4, EventType.GEOPOLITICAL: 1.3, EventType.MACRO_EVENT: 1.3,
        EventType.EARNINGS: 1.2, EventType.MERGER_ACQUISITION: 1.1, EventType.SENTIMENT_SHIFT: 1.0,
        EventType.SOCIAL_TREND: 0.8, EventType.NEWS: 0.7, EventType.TECHNICAL_SIGNAL: 0.9,
        EventType.WHALE_MOVEMENT: 1.3
    }
    
    SOURCE_CONFIDENCE = {
        "coingecko": 0.95, "yahoo_finance": 0.95, "gdelt": 0.70,
        "rss_reuters_business": 0.85, "rss_coindesk": 0.80, "rss_cointelegraph": 0.80,
        "rss_forexlive": 0.80, "rss_investing": 0.75, "rss_marketwatch": 0.80,
        "rss_cnbc": 0.80, "rss_bloomberg": 0.90, "osiris": 0.75
    }
    
    def __init__(self, db):
        self.db = db
    
    def score_event(self, event):
        scores = {}
        urgency_scores = {Urgency.CRITICAL: 100, Urgency.HIGH: 80, Urgency.MEDIUM: 50, Urgency.LOW: 25, Urgency.BACKGROUND: 10}
        scores["urgency"] = urgency_scores.get(event.urgency, 25)
        scores["sentiment_magnitude"] = min(abs(event.sentiment_score) * 100, 100)
        source_conf = self.SOURCE_CONFIDENCE.get(event.source, 0.5)
        scores["source_confidence"] = source_conf * 100
        scores["asset_relevance"] = self._calculate_asset_relevance(event)
        scores["recency"] = self._calculate_recency(event)
        scores["correlation_boost"] = self._calculate_correlation_boost(event)
        
        raw_score = sum(scores[key] * self.WEIGHTS[key] for key in self.WEIGHTS.keys())
        multiplier = self.EVENT_MULTIPLIERS.get(event.event_type, 1.0)
        final_score = min(raw_score * multiplier, 100.0)
        
        return {
            "raw_score": raw_score, "final_score": round(final_score, 2),
            "multiplier": multiplier, "component_scores": scores, "event_id": event.id
        }
    
    def _calculate_asset_relevance(self, event):
        if not event.assets:
            return 50.0
        high_interest = {"BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "EURUSD", "GBPUSD", "USDJPY", "GC=F", "SI=F", "CL=F"}
        relevance_sum = sum(100 if a.symbol in high_interest else 70 if a.asset_class in [AssetClass.CRYPTO, AssetClass.STOCK] else 50 for a in event.assets)
        return min(relevance_sum / max(len(event.assets), 1), 100)
    
    def _calculate_recency(self, event):
        age = (datetime.now(timezone.utc) - event.timestamp).total_seconds()
        if age < 3600: return 100
        elif age < 7200: return 90
        elif age < 14400: return 75
        elif age < 28800: return 60
        elif age < 86400: return 40
        elif age < 172800: return 25
        else: return 10
    
    def _calculate_correlation_boost(self, event):
        try:
            recent = self.db.get_recent_events(hours=6, limit=100)
            similar = [e for e in recent if e.event_type == event.event_type and e.id != event.id]
            if len(similar) >= 5: return 100
            elif len(similar) >= 3: return 75
            elif len(similar) >= 1: return 50
            else: return 25
        except:
            return 25
    
    def score_batch(self, events):
        return [self.score_event(e) for e in events]

class OpportunityEngine:
    OPPORTUNITY_TYPES = {
        EventType.PRICE_MOVEMENT: {"bullish": "LONG_SETUP", "bearish": "SHORT_SETUP", "neutral": "WATCHLIST_ADD"},
        EventType.VOLUME_SPIKE: {"default": "MOMENTUM_PLAY"},
        EventType.HACK_EXPLOIT: {"default": "AVOID_OR_SHORT"},
        EventType.REGULATORY: {"bullish": "REGULATORY_TAILWIND", "bearish": "REGULATORY_HEADWIND", "neutral": "MONITOR_COMPLIANCE"},
        EventType.GEOPOLITICAL: {"bullish": "SAFE_HAVEN_FLOW", "bearish": "RISK_OFF", "neutral": "MONITOR_GEO"},
        EventType.MACRO_EVENT: {"bullish": "MACRO_TAILWIND", "bearish": "MACRO_HEADWIND", "neutral": "MONITOR_MACRO"},
        EventType.EARNINGS: {"bullish": "POST_EARNINGS_RUN", "bearish": "POST_EARNINGS_DROP", "neutral": "EARNINGS_NEUTRAL"},
        EventType.SENTIMENT_SHIFT: {"bullish": "SENTIMENT_TURN_BULL", "bearish": "SENTIMENT_TURN_BEAR", "neutral": "SENTIMENT_WATCH"},
        EventType.SOCIAL_TREND: {"default": "VIRAL_MOMENTUM"},
        EventType.NEWS: {"default": "NEWS_DRIVEN"},
        EventType.TECHNICAL_SIGNAL: {"bullish": "TECHNICAL_BREAKOUT", "bearish": "TECHNICAL_BREAKDOWN", "neutral": "TECHNICAL_WATCH"},
        EventType.WHALE_MOVEMENT: {"bullish": "WHALE_ACCUMULATION", "bearish": "WHALE_DISTRIBUTION", "neutral": "WHALE_WATCH"},
        EventType.MERGER_ACQUISITION: {"default": "ARB_OPPORTUNITY"}
    }
    
    ACTION_TEMPLATES = {
        "LONG_SETUP": {"action": "Considerar posicion larga", "timeframe": "Swing (1-5 dias)", "risk": "Stop-loss bajo soporte reciente", "rationale": "Momentum alcista con catalizador fundamental"},
        "SHORT_SETUP": {"action": "Considerar posicion corta", "timeframe": "Swing (1-5 dias)", "risk": "Stop-loss sobre resistencia reciente", "rationale": "Momentum bajista con catalizador negativo"},
        "MOMENTUM_PLAY": {"action": "Entrada en momentum", "timeframe": "Day trade / Scalp", "risk": "Tight stop, objetivo parcial rapido", "rationale": "Volumen anomalo indica interes institucional"},
        "AVOID_OR_SHORT": {"action": "Evitar o posicion corta", "timeframe": "Inmediato", "risk": "Alto — eventos de seguridad son impredecibles", "rationale": "Evento de seguridad compromete valor fundamental"},
        "SAFE_HAVEN_FLOW": {"action": "Rotacion a activos refugio", "timeframe": "1-2 semanas", "risk": "Reversion rapida si tensiones se calman", "rationale": "Tension geopolitica impulsa demanda de seguridad"},
        "RISK_OFF": {"action": "Reducir exposicion o hedging", "timeframe": "Inmediato", "risk": "Falso positivo si crisis no materializa", "rationale": "Evento geopolitico aumenta aversion al riesgo"},
        "WHALE_ACCUMULATION": {"action": "Seguimiento de ballenas", "timeframe": "Posicion acumulativa", "risk": "Ballena puede distribuir despues", "rationale": "Grandes tenedores estan comprando"},
        "WHALE_DISTRIBUTION": {"action": "Precaucion — presion vendedora", "timeframe": "Corto plazo", "risk": "Puede ser reubicacion, no venta total", "rationale": "Grandes tenedores estan vendiendo"},
        "VIRAL_MOMENTUM": {"action": "Ride the wave (con cuidado)", "timeframe": "Muy corto (horas-dias)", "risk": "Alta volatilidad, pump-and-dump", "rationale": "Tendencia social impulsa demanda especulativa"},
        "POST_EARNINGS_RUN": {"action": "Seguimiento post-earnings", "timeframe": "1-3 dias", "risk": "Profit-taking puede revertir movimiento", "rationale": "Resultados positivos no estan completamente precificados"},
        "MACRO_TAILWIND": {"action": "Alineacion con tendencia macro", "timeframe": "1-4 semanas", "risk": "Datos posteriores pueden contradecir", "rationale": "Datos macro favorables para el activo/sector"},
        "ARB_OPPORTUNITY": {"action": "Arbitraje de fusion", "timeframe": "Hasta cierre del deal", "risk": "Deal puede fracasar", "rationale": "Diferencial de precio entre oferta y mercado"},
        "WATCHLIST_ADD": {"action": "Agregar a watchlist", "timeframe": "Monitoreo", "risk": "Ninguna — solo observacion", "rationale": "Activo muestra actividad relevante"}
    }
    
    def __init__(self, db, score_engine):
        self.db = db
        self.score_engine = score_engine
    
    def generate_opportunities(self, events, min_score=40.0):
        opportunities = []
        scored_events = self.score_engine.score_batch(events)
        
        for score_data in scored_events:
            if score_data["final_score"] < min_score:
                continue
            event = next((e for e in events if e.id == score_data["event_id"]), None)
            if not event:
                continue
            opportunity = self._create_opportunity(event, score_data)
            if opportunity:
                opportunities.append(opportunity)
                self.db.insert_opportunity(opportunity)
                self.db.update_event_scores(event.id, score_data["final_score"], opportunity.get("relevance", 0))
                self.db.mark_processed(event.id)
        
        opportunities.sort(key=lambda x: x["score"], reverse=True)
        return opportunities
    
    def _create_opportunity(self, event, score_data):
        if event.sentiment_score > 0.3:
            direction = "bullish"
        elif event.sentiment_score < -0.3:
            direction = "bearish"
        else:
            direction = "neutral"
        
        type_map = self.OPPORTUNITY_TYPES.get(event.event_type, {"default": "NEWS_DRIVEN"})
        opp_type = type_map.get(direction, type_map.get("default", "NEWS_DRIVEN"))
        action_template = self.ACTION_TEMPLATES.get(opp_type, self.ACTION_TEMPLATES["WATCHLIST_ADD"])
        
        conviction = self._calculate_conviction(event, score_data)
        priority = self._determine_priority(score_data["final_score"], conviction)
        risk_level = self._calculate_risk(event, opp_type)
        
        return {
            "id": f"opp_{event.id[:8]}", "event_id": event.id,
            "title": f"[{opp_type}] {event.title[:80]}",
            "description": self._build_description(event, action_template),
            "opportunity_type": opp_type,
            "asset_class": event.assets[0].asset_class.value if event.assets else "unknown",
            "assets": [a.symbol for a in event.assets],
            "score": score_data["final_score"], "conviction": conviction,
            "priority": priority, "action_suggested": action_template["action"],
            "action_details": action_template, "risk_level": risk_level,
            "event_type": event.event_type.value, "sentiment": event.sentiment.name,
            "source": event.source, "timestamp": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }
    
    def _calculate_conviction(self, event, score_data):
        base = score_data["final_score"] * 0.6
        source_boost = score_data["component_scores"]["source_confidence"] * 0.2
        asset_boost = min(len(event.assets) * 5, 15)
        neutral_penalty = 10 if event.sentiment == Sentiment.NEUTRAL else 0
        conviction = base + source_boost + asset_boost - neutral_penalty
        return round(min(max(conviction, 0), 100), 2)
    
    def _determine_priority(self, score, conviction):
        combined = (score + conviction) / 2
        if combined >= 75: return "CRITICAL"
        elif combined >= 60: return "HIGH"
        elif combined >= 45: return "MEDIUM"
        else: return "LOW"
    
    def _calculate_risk(self, event, opp_type):
        if event.event_type == EventType.HACK_EXPLOIT: return "VERY_HIGH"
        if event.event_type == EventType.GEOPOLITICAL: return "HIGH"
        if opp_type == "VIRAL_MOMENTUM": return "HIGH"
        if event.event_type == EventType.PRICE_MOVEMENT:
            if abs(event.sentiment_score) > 0.8: return "HIGH"
            elif abs(event.sentiment_score) > 0.5: return "MEDIUM"
        return "MEDIUM"
    
    def _build_description(self, event, action_template):
        parts = [f"Evento: {event.event_type.value}", event.title,
                 f"Accion: {action_template['action']}", f"Timeframe: {action_template['timeframe']}",
                 f"Rationale: {action_template['rationale']}", f"Riesgo: {action_template['risk']}"]
        if event.assets:
            assets_info = ", ".join([f"{a.symbol} (${a.price_at_event:,.2f})" if a.price_at_event else a.symbol for a in event.assets])
            parts.insert(1, f"Activos: {assets_info}")
        if event.summary:
            parts.insert(2, f"Contexto: {event.summary[:200]}...")
        return "\n".join(parts)

class Pipeline:
    def __init__(self, db_path="oma_core.db"):
        self.db = OMACoreDatabase(db_path)
        self.score_engine = ScoreEngine(self.db)
        self.opportunity_engine = OpportunityEngine(self.db, self.score_engine)
    
    def run(self, events, min_score=40.0):
        print(f"[Pipeline] Procesando {len(events)} eventos...")
        stored = 0
        for event in events:
            try:
                self.db.insert_event(event)
                stored += 1
            except Exception as e:
                print(f"[Pipeline] Error: {e}")
        print(f"[Pipeline] {stored}/{len(events)} eventos almacenados")
        
        opportunities = self.opportunity_engine.generate_opportunities(events, min_score)
        print(f"[Pipeline] {len(opportunities)} oportunidades generadas")
        
        stats = self.db.get_event_stats()
        return {
            "events_processed": len(events), "events_stored": stored,
            "opportunities_generated": len(opportunities),
            "database_stats": stats, "top_opportunities": opportunities[:10]
        }
'''

files["core/cli/main.py"] = r'''#!/usr/bin/env python3
"""O.M.A.-C.O.R.E. CLI Interface"""
import argparse
import json
import csv
import time
import sys
from datetime import datetime, timezone
from core.database.db import OMACoreDatabase
from core.collectors.world_monitor import WorldMonitor
from core.engines.score_opportunity import Pipeline

class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"

class OMACLI:
    def __init__(self, db_path="oma_core.db"):
        self.db = OMACoreDatabase(db_path)
        self.pipeline = Pipeline(db_path)
        self.monitor = WorldMonitor()
    
    def print_banner(self):
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
 ██████  ███    ███  █████      ██████  ██████  ██████  ███████ 
██    ██ ████  ████ ██   ██    ██      ██    ██ ██   ██ ██      
██    ██ ██ ████ ██ ███████    ██      ██    ██ ██████  █████   
██    ██ ██  ██  ██ ██   ██    ██      ██    ██ ██   ██ ██      
 ██████  ██      ██ ██   ██     ██████  ██████  ██   ██ ███████ 
{Colors.END}
{Colors.YELLOW}  One Man Army — Create. Own. Run. Everything.{Colors.END}
{Colors.GREEN}  Intelligence Engine v1.0 — Trading Focus{Colors.END}
{Colors.BLUE}  —————————————————————————————————————————{Colors.END}
        """
        print(banner)
    
    def print_opportunity(self, opp, index=0):
        priority_colors = {"CRITICAL": Colors.RED + Colors.BOLD, "HIGH": Colors.YELLOW + Colors.BOLD, "MEDIUM": Colors.CYAN, "LOW": Colors.BLUE}
        score_color = Colors.GREEN if opp["score"] >= 70 else Colors.YELLOW if opp["score"] >= 50 else Colors.BLUE
        risk_colors = {"VERY_HIGH": Colors.RED + Colors.BOLD, "HIGH": Colors.RED, "MEDIUM": Colors.YELLOW, "LOW": Colors.GREEN}
        p_color = priority_colors.get(opp["priority"], Colors.END)
        r_color = risk_colors.get(opp["risk_level"], Colors.END)
        
        print(f"""
{Colors.BOLD}[{index}] {p_color}[{opp["priority"]}]{Colors.END} {opp["title"]}{Colors.END}
{Colors.BLUE}   |- Score:{Colors.END} {score_color}{opp["score"]}/100{Colors.END} | {Colors.BLUE}Conviccion:{Colors.END} {opp["conviction"]}/100
{Colors.BLUE}   |- Tipo:{Colors.END} {opp["opportunity_type"]} | {Colors.BLUE}Assets:{Colors.END} {', '.join(opp["assets"]) if opp["assets"] else 'N/A'}
{Colors.BLUE}   |- Riesgo:{Colors.END} {r_color}{opp["risk_level"]}{Colors.END} | {Colors.BLUE}Fuente:{Colors.END} {opp["source"]}
{Colors.BLUE}   |- Accion:{Colors.END} {Colors.GREEN}{opp["action_suggested"]}{Colors.END}
{Colors.BLUE}   |- Timeframe:{Colors.END} {opp["action_details"]["timeframe"]}
{Colors.BLUE}   |- Rationale:{Colors.END} {opp["action_details"]["rationale"]}
        """)
    
    def print_event(self, event, index=0):
        urgency_colors = {"CRITICAL": Colors.RED + Colors.BOLD, "HIGH": Colors.YELLOW + Colors.BOLD, "MEDIUM": Colors.CYAN, "LOW": Colors.BLUE, "BACKGROUND": Colors.END}
        sentiment_emoji = {"VERY_BULLISH": "🚀", "BULLISH": "📈", "NEUTRAL": "➖", "BEARISH": "📉", "VERY_BEARISH": "💥"}
        u_color = urgency_colors.get(event.urgency.name, Colors.END)
        s_emoji = sentiment_emoji.get(event.sentiment.name, "➖")
        assets = ", ".join([a.symbol for a in event.assets]) if event.assets else "N/A"
        
        print(f"""
{Colors.BOLD}[{index}] {u_color}[{event.urgency.name}]{Colors.END} {s_emoji} {event.title[:100]}{Colors.END}
{Colors.BLUE}   |- Tipo:{Colors.END} {event.event_type.value} | {Colors.BLUE}Fuente:{Colors.END} {event.source}
{Colors.BLUE}   |- Assets:{Colors.END} {assets}
{Colors.BLUE}   |- Sentimiento:{Colors.END} {event.sentiment.name} ({event.sentiment_score:+.2f})
{Colors.BLUE}   |- Confianza:{Colors.END} {event.confidence:.0%}
{Colors.BLUE}   |- Hora:{Colors.END} {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC
        """)
    
    def cmd_collect(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[COLLECT] Iniciando recoleccion...{Colors.END}\n")
        events = self.monitor.collect_all()
        if not events:
            print(f"{Colors.YELLOW}⚠ No se encontraron eventos.{Colors.END}")
            return
        print(f"{Colors.GREEN}✓ {len(events)} eventos recolectados{Colors.END}\n")
        stored = 0
        for event in events:
            try:
                self.db.insert_event(event)
                stored += 1
            except Exception as e:
                print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
        print(f"{Colors.GREEN}✓ {stored}/{len(events)} eventos almacenados{Colors.END}")
        stats = self.db.get_event_stats()
        print(f"\n{Colors.BLUE}📊 Stats:{Colors.END} Total: {stats['total_events']} | Sin procesar: {stats['unprocessed']}")
    
    def cmd_process(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[PROCESS] Procesando eventos...{Colors.END}\n")
        unprocessed = self.db.get_unprocessed_events(limit=200)
        if not unprocessed:
            print(f"{Colors.YELLOW}⚠ No hay eventos pendientes.{Colors.END}")
            return
        print(f"{Colors.BLUE}📥 {len(unprocessed)} eventos pendientes{Colors.END}\n")
        result = self.pipeline.run(unprocessed, min_score=args.min_score)
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Pipeline completado{Colors.END}")
        print(f"   Eventos: {result['events_processed']} | Oportunidades: {result['opportunities_generated']}")
        if result['top_opportunities']:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}🏆 TOP OPORTUNIDADES:{Colors.END}\n")
            for i, opp in enumerate(result['top_opportunities'][:args.limit], 1):
                self.print_opportunity(opp, i)
    
    def cmd_opportunities(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[OPPORTUNITIES] Activas{Colors.END}\n")
        opps = self.db.get_active_opportunities(limit=args.limit)
        if not opps:
            print(f"{Colors.YELLOW}⚠ No hay oportunidades. Ejecuta 'oma collect' y 'oma process' primero.{Colors.END}")
            return
        print(f"{Colors.GREEN}✓ {len(opps)} oportunidades{Colors.END}\n")
        for i, opp in enumerate(opps, 1):
            self.print_opportunity(opp, i)
    
    def cmd_events(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[EVENTS] Recientes (ultimas {args.hours}h){Colors.END}\n")
        events = self.db.get_recent_events(hours=args.hours, limit=args.limit)
        if not events:
            print(f"{Colors.YELLOW}⚠ No hay eventos.{Colors.END}")
            return
        print(f"{Colors.GREEN}✓ {len(events)} eventos{Colors.END}\n")
        for i, event in enumerate(events, 1):
            self.print_event(event, i)
    
    def cmd_status(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[STATUS] Sistema{Colors.END}\n")
        stats = self.db.get_event_stats()
        opps = self.db.get_active_opportunities(limit=1000)
        print(f"{Colors.BOLD}📊 DB:{Colors.END} Total: {stats['total_events']} | Sin procesar: {stats['unprocessed']} | Oportunidades: {len(opps)}")
        print(f"\n{Colors.BOLD}📈 Por tipo:{Colors.END}")
        for etype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 20)
            print(f"   {etype:20s} {bar} {count}")
        print(f"\n{Colors.BOLD}⚡ Por urgencia:{Colors.END}")
        urgency_names = {4: "CRITICAL", 3: "HIGH", 2: "MEDIUM", 1: "LOW", 0: "BACKGROUND"}
        for urg, count in sorted(stats['by_urgency'].items(), key=lambda x: -x[0]):
            print(f"   {urgency_names.get(urg, str(urg)):20s} {'█' * min(count, 20)} {count}")
        if opps:
            avg_score = sum(o["score"] for o in opps) / len(opps)
            print(f"\n{Colors.BOLD}🎯 Score promedio: {avg_score:.1f}{Colors.END}")
    
    def cmd_watch(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[WATCH] Monitoreo continuo{Colors.END}")
        print(f"   Intervalo: {args.interval}s | Min score: {args.min_score}")
        print(f"   Presiona Ctrl+C para detener\n")
        cycle = 0
        try:
            while True:
                cycle += 1
                print(f"{Colors.BLUE}\n[Cycle {cycle}] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC{Colors.END}")
                events = self.monitor.collect_all()
                if events:
                    print(f"   {Colors.GREEN}✓ {len(events)} eventos recolectados{Colors.END}")
                    result = self.pipeline.run(events, min_score=args.min_score)
                    if result['opportunities_generated'] > 0:
                        print(f"   {Colors.YELLOW}🏆 {result['opportunities_generated']} oportunidades!{Colors.END}")
                        for opp in result['top_opportunities'][:3]:
                            p_color = Colors.RED if opp["priority"] == "CRITICAL" else Colors.YELLOW if opp["priority"] == "HIGH" else Colors.CYAN
                            print(f"      {p_color}[{opp['priority']}] {opp['title'][:80]} (Score: {opp['score']}){Colors.END}")
                else:
                    print(f"   {Colors.BLUE}○ Sin eventos nuevos{Colors.END}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}\n⚠ Monitoreo detenido{Colors.END}")
    
    def cmd_export(self, args):
        print(f"{Colors.CYAN}{Colors.BOLD}[EXPORT] Exportando...{Colors.END}\n")
        if args.format == "json":
            opps = self.db.get_active_opportunities(limit=10000)
            filename = f"oma_opportunities_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(opps, f, indent=2, default=str)
            print(f"{Colors.GREEN}✓ {len(opps)} oportunidades exportadas a {filename}{Colors.END}")
        elif args.format == "csv":
            opps = self.db.get_active_opportunities(limit=10000)
            filename = f"oma_opportunities_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
            if opps:
                keys = opps[0].keys()
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(opps)
                print(f"{Colors.GREEN}✓ {len(opps)} oportunidades exportadas a {filename}{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠ No hay oportunidades{Colors.END}")
    
    def cmd_run(self, args):
        self.cmd_collect(args)
        print("\n" + "—" * 60 + "\n")
        self.cmd_process(args)
    
    def run(self):
        parser = argparse.ArgumentParser(
            description="O.M.A.-C.O.R.E. — Intelligence Engine CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos:
  python -m core.cli.main collect
  python -m core.cli.main process --min-score 50
  python -m core.cli.main run
  python -m core.cli.main watch --interval 300
  python -m core.cli.main opportunities --limit 20
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
        
        p_collect = subparsers.add_parser("collect", help="Recolectar datos")
        
        p_process = subparsers.add_parser("process", help="Procesar eventos")
        p_process.add_argument("--min-score", type=float, default=40.0)
        p_process.add_argument("--limit", type=int, default=10)
        
        p_opps = subparsers.add_parser("opportunities", help="Ver oportunidades")
        p_opps.add_argument("--limit", type=int, default=20)
        
        p_events = subparsers.add_parser("events", help="Ver eventos")
        p_events.add_argument("--hours", type=int, default=24)
        p_events.add_argument("--limit", type=int, default=20)
        
        p_status = subparsers.add_parser("status", help="Estado del sistema")
        
        p_watch = subparsers.add_parser("watch", help="Monitoreo continuo")
        p_watch.add_argument("--interval", type=int, default=300)
        p_watch.add_argument("--min-score", type=float, default=40.0)
        
        p_export = subparsers.add_parser("export", help="Exportar datos")
        p_export.add_argument("--format", choices=["json", "csv"], default="json")
        
        p_run = subparsers.add_parser("run", help="Ciclo completo")
        p_run.add_argument("--min-score", type=float, default=40.0)
        p_run.add_argument("--limit", type=int, default=10)
        
        args = parser.parse_args()
        self.print_banner()
        
        if not args.command:
            parser.print_help()
            return
        
        command_map = {
            "collect": self.cmd_collect, "process": self.cmd_process,
            "opportunities": self.cmd_opportunities, "events": self.cmd_events,
            "status": self.cmd_status, "watch": self.cmd_watch,
            "export": self.cmd_export, "run": self.cmd_run
        }
        
        if args.command in command_map:
            command_map[args.command](args)
        else:
            print(f"{Colors.RED}Comando desconocido: {args.command}{Colors.END}")


if __name__ == "__main__":
    cli = OMACLI()
    cli.run()
'''

# Crear archivos
print("=" * 60)
print("🚀 O.M.A.-C.O.R.E. — Generando archivos")
print("=" * 60)
for path, content in files.items():
    full = os.path.join(PROJECT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    size = os.path.getsize(full)
    print(f"  ✅ {path} ({size:,} bytes)")

print()
print("=" * 60)
print("✅ Todos los archivos generados")
print("=" * 60)
print()
print("Ejecutar ahora:")
print(f'  cd "{PROJECT}"')
print("  source venv/bin/activate")
print("  python -m core.cli.main run")
