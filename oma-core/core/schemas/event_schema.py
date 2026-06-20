"""
O.M.A.-C.O.R.E. — Event Schema
=============================
Esquema normalizado para cualquier evento detectado por el sistema.
Cualquier fuente de datos (OSIRIS, API externa, RSS, etc.) se mapea a este schema.

Versión: 1.0.0
Foco: Trading (Crypto, Forex, Stocks, Commodities)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json

class EventType(Enum):
    """Tipos de eventos detectables"""
    NEWS = "news"                    # Noticia general
    PRICE_MOVEMENT = "price_movement" # Movimiento significativo de precio
    VOLUME_SPIKE = "volume_spike"    # Pico de volumen
    SENTIMENT_SHIFT = "sentiment_shift" # Cambio de sentimiento
    MACRO_EVENT = "macro_event"      # Evento macroeconómico
    GEOPOLITICAL = "geopolitical"     # Evento geopolítico
    REGULATORY = "regulatory"        # Noticia regulatoria
    WHALE_MOVEMENT = "whale_movement" # Movimiento de ballena (crypto)
    HACK_EXPLOIT = "hack_exploit"    # Hackeo o exploit
    SOCIAL_TREND = "social_trend"    # Tendencia en redes sociales
    TECHNICAL_SIGNAL = "technical_signal" # Señal técnica
    EARNINGS = "earnings"            # Reporte de ganancias
    MERGER_ACQUISITION = "merger_acquisition" # Fusiones/adquisiciones

class AssetClass(Enum):
    """Clases de activos soportadas"""
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCK = "stock"
    COMMODITY = "commodity"
    INDEX = "index"
    BOND = "bond"

class Sentiment(Enum):
    """Sentimiento del evento"""
    VERY_BULLISH = 2
    BULLISH = 1
    NEUTRAL = 0
    BEARISH = -1
    VERY_BEARISH = -2

class Urgency(Enum):
    """Nivel de urgencia"""
    CRITICAL = 4      # Requiere acción inmediata
    HIGH = 3          # Importante, actuar pronto
    MEDIUM = 2        # Relevante, monitorear
    LOW = 1           # Contexto, no urgente
    BACKGROUND = 0    # Información general

@dataclass
class Asset:
    """Representa un activo financiero detectado"""
    symbol: str                           # BTC, AAPL, EURUSD, GC=F
    name: str                             # Bitcoin, Apple Inc., Euro/Dollar
    asset_class: AssetClass
    exchange: Optional[str] = None        # Binance, NYSE, Forex
    price_at_event: Optional[float] = None
    currency: str = "USD"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "asset_class": self.asset_class.value,
            "exchange": self.exchange,
            "price_at_event": self.price_at_event,
            "currency": self.currency
        }

@dataclass  
class Event:
    """
    Evento normalizado — el objeto fundamental del sistema.
    Cualquier dato entrante se transforma en esta estructura.
    """
    # Identificación
    id: str                               # UUID único
    source: str                           # De dónde viene: "gdelt", "coingecko", "osiris", "rss_reuters"
    source_url: Optional[str] = None      # URL original
    source_id: Optional[str] = None         # ID en la fuente original

    # Clasificación
    event_type: EventType = EventType.NEWS
    category: Optional[str] = None        # Categoría secundaria

    # Contenido
    title: str = ""
    summary: str = ""                     # Resumen generado o extraído
    raw_content: Optional[str] = None     # Contenido original completo

    # Temporal
    timestamp: datetime = field(default_factory=datetime.utcnow)
    detected_at: datetime = field(default_factory=datetime.utcnow)

    # Entidades
    assets: List[Asset] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)  # Personas, organizaciones, países
    regions: List[str] = field(default_factory=list)   # Países/regiones mencionadas

    # Análisis
    sentiment: Sentiment = Sentiment.NEUTRAL
    sentiment_score: float = 0.0          # -1.0 a 1.0
    urgency: Urgency = Urgency.LOW
    confidence: float = 0.0               # 0.0 a 1.0, confianza en la detección

    # Métricas de impacto
    impact_score: Optional[float] = None # Calculado por Score Engine
    relevance_score: Optional[float] = None # Relevancia para el perfil de usuario

    # Metadata
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Estado
    processed: bool = False
    enriched: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario para SQLite/JSON"""
        return {
            "id": self.id,
            "source": self.source,
            "source_url": self.source_url,
            "source_id": self.source_id,
            "event_type": self.event_type.value,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "raw_content": self.raw_content,
            "timestamp": self.timestamp.isoformat(),
            "detected_at": self.detected_at.isoformat(),
            "assets": [a.to_dict() for a in self.assets],
            "keywords": self.keywords,
            "entities": self.entities,
            "regions": self.regions,
            "sentiment": self.sentiment.value,
            "sentiment_score": self.sentiment_score,
            "urgency": self.urgency.value,
            "confidence": self.confidence,
            "impact_score": self.impact_score,
            "relevance_score": self.relevance_score,
            "language": self.language,
            "metadata": json.dumps(self.metadata),
            "processed": self.processed,
            "enriched": self.enriched
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Deserializa desde diccionario"""
        event = cls(
            id=data["id"],
            source=data["source"],
            source_url=data.get("source_url"),
            source_id=data.get("source_id"),
            event_type=EventType(data["event_type"]),
            category=data.get("category"),
            title=data["title"],
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
        # Reconstruir assets
        if "assets" in data and data["assets"]:
            event.assets = [Asset(
                symbol=a["symbol"],
                name=a["name"],
                asset_class=AssetClass(a["asset_class"]),
                exchange=a.get("exchange"),
                price_at_event=a.get("price_at_event"),
                currency=a.get("currency", "USD")
            ) for a in data["assets"]]
        event.keywords = data.get("keywords", [])
        event.entities = data.get("entities", [])
        event.regions = data.get("regions", [])
        return event

    def __repr__(self):
        assets_str = ", ".join([a.symbol for a in self.assets]) if self.assets else "none"
        return f"Event({self.id[:8]} | {self.event_type.value} | {self.urgency.name} | Assets: [{assets_str}] | {self.title[:60]}...)"


# Esquema SQL para SQLite
EVENT_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_url TEXT,
    source_id TEXT,
    event_type TEXT NOT NULL,
    category TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    raw_content TEXT,
    timestamp TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    assets TEXT,  -- JSON array
    keywords TEXT,  -- JSON array
    entities TEXT,  -- JSON array
    regions TEXT,  -- JSON array
    sentiment INTEGER,
    sentiment_score REAL,
    urgency INTEGER,
    confidence REAL,
    impact_score REAL,
    relevance_score REAL,
    language TEXT,
    metadata TEXT,
    processed INTEGER DEFAULT 0,
    enriched INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_urgency ON events(urgency);
CREATE INDEX IF NOT EXISTS idx_events_processed ON events(processed);
"""
