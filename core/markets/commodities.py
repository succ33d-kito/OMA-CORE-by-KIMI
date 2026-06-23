"""Commodities market profile."""
from core.markets.base import MarketProfile, TradingHours
from core.schemas.event_schema import AssetClass

COMMODITIES_TRADING = TradingHours(
    session="varies by exchange",
    timezone="UTC",
    notes="CME Globex: Sunday 17:00 - Friday 17:00 UTC (with daily breaks). COMEX/NYMEX/ICE have different hours. Futures rollover calendar critical.",
)

COMMODITIES_PROFILE = MarketProfile(
    asset_class=AssetClass.COMMODITY,
    trading_hours=COMMODITIES_TRADING,
    ohlcv_source="yfinance",
    spread_model="variable",
    slippage_model="volume_based",
    risk_model="var_95",
    symbol_format="TICKER=F",
    liquidity_model="volume_based",
    market_specific_constraints={
        "min_trade_size": 1,
        "leverage_allowed": True,
        "has_futures_rollover": True,
        "has_expiry_calendar": True,
        "has_storage_costs": True,
        "has_contango_backwardation": True,
        "confirmed_symbols": [
            "GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "ZW=F", "ZC=F", "ZS=F",
        ],
    },
)
