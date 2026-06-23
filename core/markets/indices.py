"""Indices market profile."""
from core.markets.base import MarketProfile, TradingHours
from core.schemas.event_schema import AssetClass

INDICES_TRADING = TradingHours(
    session="varies by index",
    timezone="varies",
    notes="US indices: 9:30-16:00 ET (spot). Futures trade nearly 24/5. Each index has its own exchange calendar.",
)

INDICES_PROFILE = MarketProfile(
    asset_class=AssetClass.INDEX,
    trading_hours=INDICES_TRADING,
    ohlcv_source="yfinance",
    spread_model="fixed",
    slippage_model="volume_based",
    risk_model="var_95",
    symbol_format="^TICKER",
    liquidity_model="volume_based",
    market_specific_constraints={
        "min_trade_size": 1,
        "leverage_allowed": True,
        "not_directly_tradeable": True,
        "traded_via_futures_or_etf": True,
        "confirmed_symbols": [
            "^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX", "^FTSE", "^N225", "^HSI",
        ],
    },
)
