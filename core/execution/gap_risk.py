"""GapRiskEngine — Models overnight, weekend, news gaps and liquidation cascades.

Adjusts stop loss placement and position sizing based on gap risk.
"""
from statistics import mean, stdev
from typing import List, Optional, Dict
from datetime import datetime, timezone


class GapRiskEngine:
    def __init__(self,
                 lookback_periods: int = 30,
                 gap_risk_cap_pct: float = 5.0,
                 weekend_risk_multiplier: float = 2.0):
        self.lookback_periods = lookback_periods
        self.gap_risk_cap_pct = gap_risk_cap_pct
        self.weekend_risk_multiplier = weekend_risk_multiplier
        self._historical_gaps: List[float] = []
        self._price_history: List[float] = []

    def record_price(self, price: float, timestamp: Optional[datetime] = None) -> None:
        if self._price_history:
            gap = abs(price - self._price_history[-1]) / self._price_history[-1] * 100
            ts = timestamp or datetime.now(timezone.utc)
            if self._is_gap_event(self._price_history[-1], price, ts):
                self._historical_gaps.append(gap)
                if len(self._historical_gaps) > self.lookback_periods:
                    self._historical_gaps.pop(0)
        self._price_history.append(price)
        if len(self._price_history) > 168:
            self._price_history.pop(0)

    def _is_gap_event(self, prev_price: float, current_price: float, ts: datetime) -> bool:
        gap = abs(current_price - prev_price) / prev_price * 100
        return gap > 0.5

    def avg_gap_size(self) -> float:
        if not self._historical_gaps:
            return 0.0
        return mean(self._historical_gaps)

    def max_gap_size(self) -> float:
        if not self._historical_gaps:
            return 0.0
        return max(self._historical_gaps)

    def gap_frequency(self) -> float:
        if len(self._price_history) < 10:
            return 0.0
        return len(self._historical_gaps) / len(self._price_history)

    def is_weekend(self, ts: Optional[datetime] = None) -> bool:
        dt = ts or datetime.now(timezone.utc)
        return dt.weekday() >= 5

    def is_overnight(self, ts: Optional[datetime] = None) -> bool:
        dt = ts or datetime.now(timezone.utc)
        return dt.hour < 1 or dt.hour > 22

    def gap_risk_score(self, ts: Optional[datetime] = None) -> float:
        """Compute gap risk score 0-100."""
        score = 0.0
        dt = ts or datetime.now(timezone.utc)

        avg_gap = self.avg_gap_size()
        max_gap = self.max_gap_size()

        # Historical gap severity
        if max_gap > 5.0:
            score += 25
        elif max_gap > 3.0:
            score += 15
        elif max_gap > 1.0:
            score += 5

        # Current gap risk from recent volatility
        if avg_gap > 2.0:
            score += 20
        elif avg_gap > 1.0:
            score += 10
        elif avg_gap > 0.5:
            score += 5

        # Weekend risk (markets closed → gaps larger)
        if self.is_weekend(dt):
            score += 25
        elif self.is_overnight(dt):
            score += 10

        # Gap frequency
        freq = self.gap_frequency()
        if freq > 0.3:
            score += 20
        elif freq > 0.15:
            score += 10
        elif freq > 0.05:
            score += 5

        # Liquidation cascade risk (extreme gaps in crypto)
        if self._price_history and len(self._price_history) >= 6:
            recent_vol = stdev(self._price_history[-6:]) if len(self._price_history) >= 6 else 0
            long_vol = stdev(self._price_history) if len(self._price_history) > 1 else recent_vol
            vol_ratio = recent_vol / long_vol if long_vol > 0 else 1.0
            if vol_ratio > 2.0:
                score += 20

        return min(100, score)

    def stop_cushion_multiplier(self, ts: Optional[datetime] = None) -> float:
        """How much extra room to add to stop loss based on gap risk.
        1.0 = normal, 2.0 = double stop distance, etc.
        """
        risk = self.gap_risk_score(ts)
        if risk > 70:
            return 2.5
        if risk > 40:
            return 1.5
        if risk > 20:
            return 1.2
        return 1.0

    def size_reduction(self, ts: Optional[datetime] = None) -> float:
        risk = self.gap_risk_score(ts)
        if risk > 70:
            return 0.25
        if risk > 40:
            return 0.5
        if risk > 20:
            return 0.75
        return 1.0

    def summary(self) -> Dict:
        return {
            "gap_risk_score": round(self.gap_risk_score(), 1),
            "avg_gap_size": round(self.avg_gap_size(), 2),
            "max_gap_size": round(self.max_gap_size(), 2),
            "gap_frequency": round(self.gap_frequency(), 3),
            "stop_multiplier": round(self.stop_cushion_multiplier(), 2),
            "size_reduction": round(self.size_reduction(), 2),
        }
