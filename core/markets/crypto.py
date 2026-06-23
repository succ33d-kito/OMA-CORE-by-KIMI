"""Crypto market profile (Validated Trading Profile v1)."""
from core.markets.base import MarketProfile, TradingHours
from core.schemas.event_schema import AssetClass

CRYPTO_TRADING = TradingHours(
    session="24/7",
    timezone="UTC",
    notes="Continuous trading. No market holidays or session gaps.",
)

CRYPTO_PROFILE = MarketProfile(
    asset_class=AssetClass.CRYPTO,
    trading_hours=CRYPTO_TRADING,
    ohlcv_source="binance",
    spread_model="percentage",
    slippage_model="volume_based",
    risk_model="volatility_daily",
    symbol_format="TICKERUSDT",
    liquidity_model="volume_based",
    market_specific_constraints={
        "min_trade_size": 0.001,
        "leverage_allowed": False,
        "perpetual_funding_available": False,
        "spot_only": True,
        "confirmed_symbols": [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT",
            "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT",
            "DOTUSDT", "UNIUSDT", "LTCUSDT", "BCHUSDT", "ATOMUSDT",
        ],
    },
)
