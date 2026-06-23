"""Forex market profile."""
from core.markets.base import MarketProfile, TradingHours
from core.schemas.event_schema import AssetClass

FOREX_TRADING = TradingHours(
    session="24/5",
    timezone="UTC",
    notes="Opens Sunday 22:00 UTC, closes Friday 22:00 UTC. Sydney/Tokyo/London/New York overlap sessions.",
)

FOREX_PROFILE = MarketProfile(
    asset_class=AssetClass.FOREX,
    trading_hours=FOREX_TRADING,
    ohlcv_source="yfinance",
    spread_model="variable",
    slippage_model="fixed_pct",
    risk_model="var_95",
    symbol_format="TICKER=X",
    liquidity_model="bid_ask_spread",
    market_specific_constraints={
        "min_trade_size": 1000,
        "leverage_allowed": True,
        "max_leverage": 50,
        "swap_rates_daily": True,
        "session_overlap_required": False,
        "confirmed_symbols": [
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X",
            "AUDUSD=X", "USDCAD=X", "NZDUSD=X", "EURGBP=X",
        ],
    },
)
