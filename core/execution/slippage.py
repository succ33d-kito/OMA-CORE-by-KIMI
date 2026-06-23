"""Slippage & Spread models — cost simulation for realistic backtesting."""
from typing import Dict, Optional

DEFAULT_SPREAD_BPS: Dict[str, float] = {
    "BTC": 1.0, "ETH": 2.0, "SOL": 3.0,
    "XRP": 5.0, "BNB": 3.0, "ADA": 5.0,
    "DOGE": 10.0, "AVAX": 5.0, "LINK": 5.0,
}


class SlippageEngine:
    def __init__(self, slippage_pct: float = 0.0, spread_bps: Optional[Dict[str, float]] = None):
        self.slippage_pct = slippage_pct
        self.spread_bps = spread_bps or {}

    def get_spread_pct(self, symbol: str) -> float:
        bps = self.spread_bps.get(symbol) or DEFAULT_SPREAD_BPS.get(symbol, 3.0)
        return bps / 10000.0

    def entry_price(self, price: float, direction: str, symbol: str) -> float:
        total_cost = self.slippage_pct / 100.0 + self.get_spread_pct(symbol)
        if direction == "long":
            return round(price * (1 + total_cost), 8)
        else:
            return round(price * (1 - total_cost), 8)

    def exit_price(self, price: float, direction: str, symbol: str) -> float:
        total_cost = self.slippage_pct / 100.0 + self.get_spread_pct(symbol)
        if direction == "long":
            return round(price * (1 - total_cost), 8)
        else:
            return round(price * (1 + total_cost), 8)

    def stop_price(self, price: float, direction: str, symbol: str) -> float:
        cost = self.slippage_pct / 100.0
        if direction == "long":
            return round(price * (1 - cost), 8)
        else:
            return round(price * (1 + cost), 8)

    def target_price(self, price: float, direction: str, symbol: str) -> float:
        cost = self.slippage_pct / 100.0
        if direction == "long":
            return round(price * (1 - cost), 8)
        else:
            return round(price * (1 + cost), 8)
