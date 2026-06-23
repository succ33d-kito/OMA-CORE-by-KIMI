"""OSIRIS Multi-Market Classification Layer"""
from core.markets.base import MarketProfile
from core.markets.crypto import CRYPTO_PROFILE
from core.markets.forex import FOREX_PROFILE
from core.markets.stocks import STOCKS_PROFILE
from core.markets.commodities import COMMODITIES_PROFILE
from core.markets.bonds import BONDS_PROFILE
from core.markets.indices import INDICES_PROFILE

MARKET_PROFILES = {
    "crypto": CRYPTO_PROFILE,
    "forex": FOREX_PROFILE,
    "stocks": STOCKS_PROFILE,
    "commodities": COMMODITIES_PROFILE,
    "bonds": BONDS_PROFILE,
    "indices": INDICES_PROFILE,
}

def get_profile(asset_class: str) -> MarketProfile:
    return MARKET_PROFILES[asset_class]
