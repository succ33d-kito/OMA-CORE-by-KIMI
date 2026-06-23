"""Universal Market Profile — abstraction layer for any tradeable market."""
from dataclasses import dataclass, field
from typing import Dict, Any
from core.schemas.event_schema import AssetClass


@dataclass(frozen=True)
class TradingHours:
    session: str
    timezone: str
    notes: str = ""


@dataclass(frozen=True)
class MarketProfile:
    asset_class: AssetClass
    trading_hours: TradingHours
    ohlcv_source: str
    spread_model: str
    slippage_model: str
    risk_model: str
    symbol_format: str
    liquidity_model: str
    market_specific_constraints: Dict[str, Any] = field(default_factory=dict)
