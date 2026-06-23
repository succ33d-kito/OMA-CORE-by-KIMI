"""OSIRIS Configuration — Centralized, env-based config"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    path: str = "oma_core.db"
    postgres_url: Optional[str] = None

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            path=os.getenv("OMA_DB_PATH", "oma_core.db"),
            postgres_url=os.getenv("DATABASE_URL"),
        )


@dataclass
class TelegramConfig:
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        return cls(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        )


@dataclass
class CollectorConfig:
    fred_api_key: Optional[str] = None
    request_timeout: int = 30
    user_agent: str = "OSIRIS/2.0"

    @classmethod
    def from_env(cls) -> "CollectorConfig":
        return cls(
            fred_api_key=os.getenv("FRED_API_KEY"),
        )


@dataclass
class ScoringConfig:
    min_score: float = 40.0
    urgency_weight: float = 0.25
    sentiment_weight: float = 0.20
    source_weight: float = 0.20
    relevance_weight: float = 0.15
    recency_weight: float = 0.10
    correlation_weight: float = 0.10

    @classmethod
    def from_env(cls) -> "ScoringConfig":
        return cls(
            min_score=float(os.getenv("OMA_MIN_SCORE", "40.0")),
            urgency_weight=float(os.getenv("OMA_URGENCY_WEIGHT", "0.25")),
            sentiment_weight=float(os.getenv("OMA_SENTIMENT_WEIGHT", "0.20")),
            source_weight=float(os.getenv("OMA_SOURCE_WEIGHT", "0.20")),
            relevance_weight=float(os.getenv("OMA_RELEVANCE_WEIGHT", "0.15")),
            recency_weight=float(os.getenv("OMA_RECENCY_WEIGHT", "0.10")),
            correlation_weight=float(os.getenv("OMA_CORRELATION_WEIGHT", "0.10")),
        )


@dataclass
class OSIRISConfig:
    debug: bool = False
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    collectors: CollectorConfig = field(default_factory=CollectorConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)

    @classmethod
    def load(cls) -> "OSIRISConfig":
        from dotenv import load_dotenv
        load_dotenv()
        return cls(
            debug=os.getenv("OMA_DEBUG", "false").lower() == "true",
            database=DatabaseConfig.from_env(),
            telegram=TelegramConfig.from_env(),
            collectors=CollectorConfig.from_env(),
            scoring=ScoringConfig.from_env(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "debug": self.debug,
            "database": {"path": self.database.path, "postgres_url": "***" if self.database.postgres_url else None},
            "telegram": {"bot_token": "***" if self.telegram.bot_token else None, "chat_id": "***" if self.telegram.chat_id else None},
            "collectors": {"fred_api_key": "***" if self.collectors.fred_api_key else None},
            "scoring": self.scoring.__dict__,
        }


def load_config() -> OSIRISConfig:
    return OSIRISConfig.load()
