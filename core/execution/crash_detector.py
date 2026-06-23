"""CrashDetector v2 — Detects both FAST and SLOW crashes.
Multi-window drawdown velocity (6h/24h/72h), drawdown acceleration,
ATR expansion, volume spike, volatility regime.

Inputs: OHLCV data (price, volume)
Outputs: CrashRiskScore (0-100), CrashMode (NONE / WARNING / EMERGENCY / PANIC)
"""
from statistics import mean, stdev
from typing import List, Dict, Optional
from enum import Enum
from math import sqrt


class CrashMode(Enum):
    NONE = "none"
    WARNING = "warning"
    EMERGENCY = "emergency"
    PANIC = "panic"


class CrashDetector:
    def __init__(self,
                 fast_velocity_threshold: float = 5.0,
                 medium_velocity_threshold: float = 3.5,
                 slow_velocity_threshold: float = 6.0,
                 gap_threshold_pct: float = 3.0,
                 atr_expansion_threshold: float = 2.0,
                 volume_spike_threshold: float = 3.0,
                 consecutive_loss_threshold: int = 5):
        self.fast_velocity_threshold = fast_velocity_threshold       # 6h
        self.medium_velocity_threshold = medium_velocity_threshold   # 24h
        self.slow_velocity_threshold = slow_velocity_threshold       # 72h
        self.gap_threshold_pct = gap_threshold_pct
        self.atr_expansion_threshold = atr_expansion_threshold
        self.volume_spike_threshold = volume_spike_threshold
        self.consecutive_loss_threshold = consecutive_loss_threshold
        self._price_history: List[float] = []
        self._volume_history: List[float] = []
        self._consecutive_losses = 0
        self._peak_equity = 10000.0

    def update_price(self, price: float, volume: Optional[float] = None) -> None:
        self._price_history.append(price)
        if volume is not None:
            self._volume_history.append(volume)
        if len(self._price_history) > 1000:
            self._price_history.pop(0)
        if len(self._volume_history) > 1000:
            self._volume_history.pop(0)

    def record_trade_result(self, pnl_pct: float) -> None:
        if pnl_pct < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0

    def update_equity(self, equity: float) -> None:
        if equity > self._peak_equity:
            self._peak_equity = equity

    def drawdown_pct(self, current_equity: float) -> float:
        if self._peak_equity <= 0:
            return 0.0
        return max(0, (self._peak_equity - current_equity) / self._peak_equity * 100)

    # ── Multi-window drawdown velocity ──

    def _window_velocity(self, window: int) -> float:
        """Percent drop over last N price samples."""
        if len(self._price_history) < window:
            return 0.0
        recent = self._price_history[-window:]
        start = recent[0]
        end = recent[-1]
        if start == 0:
            return 0.0
        return (start - end) / start * 100

    def drawdown_velocity_6h(self) -> float:
        return self._window_velocity(6)

    def drawdown_velocity_24h(self) -> float:
        return self._window_velocity(24)

    def drawdown_velocity_72h(self) -> float:
        return self._window_velocity(72)

    def drawdown_acceleration(self) -> float:
        """Change in 6h velocity vs 6h velocity 18 periods ago.
        Positive = crash accelerating (getting worse faster).
        """
        if len(self._price_history) < 24:
            return 0.0
        current = self._window_velocity(6)
        earlier = self._window_velocity_at(6, -18)
        return current - earlier

    def _window_velocity_at(self, window: int, offset: int) -> float:
        """Velocity for a window ending at offset from end."""
        if len(self._price_history) < abs(offset) + window:
            return 0.0
        end_idx = len(self._price_history) + offset
        start_idx = end_idx - window
        if start_idx < 0:
            return 0.0
        start = self._price_history[start_idx]
        end = self._price_history[end_idx]
        if start == 0:
            return 0.0
        return (start - end) / start * 100

    # ── Existing indicators ──

    def gap_size(self) -> float:
        if len(self._price_history) < 3:
            return 0.0
        return abs(self._price_history[-1] - self._price_history[-2]) / self._price_history[-2] * 100

    def atr_expansion(self) -> float:
        if len(self._price_history) < 28:
            return 1.0
        recent = self._price_history[-14:]
        longer = self._price_history[-28:-14]
        recent_range = [abs(recent[i] - recent[i-1]) for i in range(1, len(recent))]
        longer_range = [abs(longer[i] - longer[i-1]) for i in range(1, len(longer))]
        recent_atr = mean(recent_range) if recent_range else 0
        longer_atr = mean(longer_range) if longer_range and any(r > 0 for r in longer_range) else 0.001
        return recent_atr / longer_atr if longer_atr > 0 else 1.0

    def volume_ratio(self) -> float:
        if len(self._volume_history) < 20:
            return 1.0
        recent_vol = self._volume_history[-1]
        avg_vol = mean(self._volume_history[:-1]) if len(self._volume_history) > 1 else recent_vol
        return recent_vol / avg_vol if avg_vol > 0 else 1.0

    def volatility_regime(self) -> str:
        """Classify volatility regime from recent price action."""
        if len(self._price_history) < 14:
            return "normal"
        returns = [abs(self._price_history[i] - self._price_history[i-1]) / self._price_history[i-1]
                   for i in range(1, len(self._price_history))]
        avg_vol = mean(returns) * 100
        if avg_vol > 3.0:
            return "extreme"
        if avg_vol > 1.5:
            return "elevated"
        return "normal"

    def crash_score(self) -> float:
        """Compute Crash Risk Score 0-100. Multi-window detection."""
        score = 0.0

        # ── Fast crash: 6h velocity ──
        dv6 = self.drawdown_velocity_6h()
        if dv6 > self.fast_velocity_threshold * 2:
            score += 25
        elif dv6 > self.fast_velocity_threshold:
            score += 15
        elif dv6 > self.fast_velocity_threshold * 0.5:
            score += 5

        # ── Medium crash: 24h velocity ──
        dv24 = self.drawdown_velocity_24h()
        if dv24 > self.medium_velocity_threshold * 2:
            score += 20
        elif dv24 > self.medium_velocity_threshold:
            score += 12
        elif dv24 > self.medium_velocity_threshold * 0.5:
            score += 5

        # ── Slow crash: 72h persistent decline ──
        dv72 = self.drawdown_velocity_72h()
        if dv72 > self.slow_velocity_threshold * 2:
            score += 20
        elif dv72 > self.slow_velocity_threshold:
            score += 15
        elif dv72 > self.slow_velocity_threshold * 0.5:
            score += 8

        # ── Drawdown acceleration ──
        accel = self.drawdown_acceleration()
        if accel > 3.0:
            score += 15
        elif accel > 1.5:
            score += 8
        elif accel > 0.5:
            score += 3

        # ── Gap size ──
        gs = self.gap_size()
        if gs > self.gap_threshold_pct * 2:
            score += 10
        elif gs > self.gap_threshold_pct:
            score += 6
        elif gs > self.gap_threshold_pct * 0.5:
            score += 3

        # ── ATR expansion ──
        atr_exp = self.atr_expansion()
        if atr_exp > self.atr_expansion_threshold * 1.5:
            score += 10
        elif atr_exp > self.atr_expansion_threshold:
            score += 6
        elif atr_exp > self.atr_expansion_threshold * 0.5:
            score += 3

        # ── Volume spike ──
        vr = self.volume_ratio()
        if vr > self.volume_spike_threshold * 1.5:
            score += 10
        elif vr > self.volume_spike_threshold:
            score += 6
        elif vr > self.volume_spike_threshold * 0.5:
            score += 3

        # ── Consecutive losses ──
        if self._consecutive_losses >= self.consecutive_loss_threshold:
            score += 10
        elif self._consecutive_losses >= self.consecutive_loss_threshold * 0.6:
            score += 5

        # ── Volatility regime multiplier ──
        regime = self.volatility_regime()
        if regime == "extreme":
            score = int(score * 1.3)
        elif regime == "elevated":
            score = int(score * 1.15)

        return min(100, score)

    def crash_mode(self, current_equity: float) -> CrashMode:
        score = self.crash_score()
        dd = self.drawdown_pct(current_equity)
        if score >= 70 or dd > 30:
            return CrashMode.PANIC
        if score >= 45 or dd > 20:
            return CrashMode.EMERGENCY
        if score >= 25 or dd > 10:
            return CrashMode.WARNING
        return CrashMode.NONE

    def position_size_multiplier(self, current_equity: float) -> float:
        mode = self.crash_mode(current_equity)
        if mode == CrashMode.PANIC:
            return 0.0
        if mode == CrashMode.EMERGENCY:
            return 0.25
        if mode == CrashMode.WARNING:
            return 0.5
        return 1.0

    def summary(self) -> Dict:
        return {
            "crash_score": round(self.crash_score(), 1),
            "mode": self.crash_mode(10000).value,
            "drawdown_velocity_6h": round(self.drawdown_velocity_6h(), 2),
            "drawdown_velocity_24h": round(self.drawdown_velocity_24h(), 2),
            "drawdown_velocity_72h": round(self.drawdown_velocity_72h(), 2),
            "drawdown_acceleration": round(self.drawdown_acceleration(), 2),
            "gap_size": round(self.gap_size(), 2),
            "atr_expansion": round(self.atr_expansion(), 2),
            "volume_ratio": round(self.volume_ratio(), 2),
            "volatility_regime": self.volatility_regime(),
            "consecutive_losses": self._consecutive_losses,
            "price_samples": len(self._price_history),
        }
