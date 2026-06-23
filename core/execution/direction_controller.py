"""Direction Bias Controller — adapts signal mode based on rolling performance.

Disables direction when recent WR drops below threshold.
Prevents SHORT from destroying alpha in trending-up markets.
"""
from collections import deque
from statistics import mean
from typing import Dict, Optional


class DirectionController:
    def __init__(self, window: int = 20, wr_threshold: float = 0.25, recovery_threshold: float = 0.35):
        self.window = window
        self.wr_threshold = wr_threshold
        self.recovery_threshold = recovery_threshold
        self._long_pnls: deque = deque(maxlen=window)
        self._short_pnls: deque = deque(maxlen=window)

    def record_trade(self, direction: str, pnl_pct: float) -> None:
        if direction == "long":
            self._long_pnls.append(pnl_pct)
        elif direction == "short":
            self._short_pnls.append(pnl_pct)

    def long_wr(self) -> float:
        if not self._long_pnls:
            return 0.5
        return sum(1 for p in self._long_pnls if p > 0) / len(self._long_pnls)

    def short_wr(self) -> float:
        if not self._short_pnls:
            return 0.5
        return sum(1 for p in self._short_pnls if p > 0) / len(self._short_pnls)

    def long_pf(self) -> float:
        wins = [p for p in self._long_pnls if p > 0]
        losses = [p for p in self._long_pnls if p < 0]
        if not losses: return float("inf")
        return abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0

    def short_pf(self) -> float:
        wins = [p for p in self._short_pnls if p > 0]
        losses = [p for p in self._short_pnls if p < 0]
        if not losses: return float("inf")
        return abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0

    def allowed_directions(self) -> str:
        lw, sw = self.long_wr(), self.short_wr()
        if lw < self.wr_threshold and sw < self.wr_threshold:
            return "both"
        if lw < self.wr_threshold and lw < sw:
            return "short_only"
        if sw < self.wr_threshold and sw < lw:
            return "long_only"
        return "both"

    def should_disable_short(self) -> bool:
        if len(self._short_pnls) < 5:
            return False
        return self.short_wr() < self.wr_threshold

    def should_disable_long(self) -> bool:
        if len(self._long_pnls) < 5:
            return False
        return self.long_wr() < self.wr_threshold

    def summary(self) -> Dict:
        return {
            "long_window": len(self._long_pnls),
            "long_wr": round(self.long_wr(), 3),
            "long_pf": round(self.long_pf(), 2),
            "short_window": len(self._short_pnls),
            "short_wr": round(self.short_wr(), 3),
            "short_pf": round(self.short_pf(), 2),
            "allowed": self.allowed_directions(),
            "disable_short": self.should_disable_short(),
            "disable_long": self.should_disable_long(),
        }
