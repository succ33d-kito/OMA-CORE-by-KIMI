"""Stock market profile."""
from core.markets.base import MarketProfile, TradingHours
from core.schemas.event_schema import AssetClass

STOCKS_TRADING = TradingHours(
    session="9:30-16:00 ET",
    timezone="US/Eastern",
    notes="Regular session only. Pre-market 4:00-9:30 ET, after-hours 16:00-20:00 ET. No trading weekends or market holidays.",
)

STOCKS_PROFILE = MarketProfile(
    asset_class=AssetClass.STOCK,
    trading_hours=STOCKS_TRADING,
    ohlcv_source="yfinance",
    spread_model="fixed",
    slippage_model="volume_based",
    risk_model="var_95",
    symbol_format="TICKER",
    liquidity_model="volume_based",
    market_specific_constraints={
        "min_trade_size": 1,
        "leverage_allowed": False,
        "has_dividends": True,
        "has_corporate_actions": True,
        "has_earnings_gap_risk": True,
        "pre_market_available": True,
        "after_hours_available": True,
        "confirmed_symbols": [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META",
            "NFLX", "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER",
            "COIN", "PLTR", "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO",
        ],
    },
)
