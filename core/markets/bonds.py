"""Bond market profile."""
from core.markets.base import MarketProfile, TradingHours
from core.schemas.event_schema import AssetClass

BONDS_TRADING = TradingHours(
    session="6:00-17:00 ET",
    timezone="US/Eastern",
    notes="Treasury cash market. Electronic trading via BrokerTec. No weekends. Follows US bond market holiday calendar.",
)

BONDS_PROFILE = MarketProfile(
    asset_class=AssetClass.BOND,
    trading_hours=BONDS_TRADING,
    ohlcv_source="fred",
    spread_model="fixed",
    slippage_model="fixed_pct",
    risk_model="duration_based",
    symbol_format="FRED_SERIES",
    liquidity_model="market_cap",
    market_specific_constraints={
        "min_trade_size": 1000,
        "leverage_allowed": True,
        "has_duration_risk": True,
        "has_yield_curve_risk": True,
        "has_credit_spread_risk": True,
        "confirmed_symbols": ["DGS10", "DGS2", "T10Y2Y", "DFF"],
    },
)
