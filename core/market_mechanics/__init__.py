"""Observable market structure from validated, closed OHLCV bars."""

from .state import MarketState, build_market_state

__all__ = ["MarketState", "build_market_state"]
