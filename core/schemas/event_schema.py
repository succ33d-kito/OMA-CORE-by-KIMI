"""O.M.A.-C.O.R.E. Event Schema"""
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
        # Handle metadata: could be string (JSON) or already a dict
        metadata = data.get("metadata", "{}")
        if isinstance(metadata, dict):
            metadata_dict = metadata
        elif isinstance(metadata, str):
            try:
                metadata_dict = json.loads(metadata)
            except:
                metadata_dict = {}
        else:
            metadata_dict = {}
        
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
            metadata=metadata_dict,
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
