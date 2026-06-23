"""Capital Protection Layer — prevents account destruction.

Max daily loss, max weekly loss, max open risk, kill switch, emergency mode.
"""
from datetime import datetime, date
from typing import Dict, Optional, List
from enum import Enum


class GuardMode(Enum):
    NORMAL = "normal"
    CAUTION = "caution"
    EMERGENCY = "emergency"
    HALT = "halt"


class CapitalGuard:
    def __init__(self,
                 initial_capital: float = 10000.0,
                 max_daily_loss_pct: float = 10.0,
                 max_weekly_loss_pct: float = 20.0,
                 max_open_risk_pct: float = 25.0,
                 max_correlated_pct: float = 40.0,
                 emergency_dd_threshold: float = 20.0,
                 halt_dd_threshold: float = 35.0,
                 consecutive_loss_limit: int = 7,
                 recovery_min_trades: int = 10):
        self.initial_capital = initial_capital
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_weekly_loss_pct = max_weekly_loss_pct
        self.max_open_risk_pct = max_open_risk_pct
        self.max_correlated_pct = max_correlated_pct
        self.emergency_dd_threshold = emergency_dd_threshold
        self.halt_dd_threshold = halt_dd_threshold
        self.consecutive_loss_limit = consecutive_loss_limit
        self.recovery_min_trades = recovery_min_trades

        self.kill_switch_active = False
        self._daily_pnls: Dict[date, List[float]] = {}
        self._weekly_pnls: Dict[int, List[float]] = {}
        self._open_trades: List[Dict] = []
        self._equity_peak = initial_capital
        self._consecutive_losses = 0
        self._total_trades = 0
        self._recovery_trades = 0

    def record_trade_result(self, pnl_abs: float, timestamp: Optional[datetime] = None) -> None:
        ts = timestamp or datetime.now()
        d = ts.date()
        w = ts.isocalendar()[1]

        if d not in self._daily_pnls:
            self._daily_pnls[d] = []
        self._daily_pnls[d].append(pnl_abs)

        if w not in self._weekly_pnls:
            self._weekly_pnls[w] = []
        self._weekly_pnls[w].append(pnl_abs)

        if pnl_abs < 0:
            self._consecutive_losses += 1
        else:
            if self._consecutive_losses > 0:
                self._recovery_trades += 1
            self._consecutive_losses = 0

        self._total_trades += 1

    def update_equity(self, equity: float) -> None:
        if equity > self._equity_peak:
            self._equity_peak = equity

    def update_open_trades(self, trades: List[Dict]) -> None:
        self._open_trades = trades

    def drawdown_pct(self, current_capital: float) -> float:
        if self._equity_peak <= 0:
            return 0.0
        return max(0, (self._equity_peak - current_capital) / self._equity_peak * 100)

    def daily_loss_pct(self, current_capital: float) -> float:
        today = date.today()
        pnls = self._daily_pnls.get(today, [])
        if not pnls or current_capital <= 0:
            return 0.0
        total = sum(pnls)
        return abs(total) / current_capital * 100 if total < 0 else 0.0

    def weekly_loss_pct(self, current_capital: float) -> float:
        w = datetime.now().isocalendar()[1]
        pnls = self._weekly_pnls.get(w, [])
        if not pnls or current_capital <= 0:
            return 0.0
        total = sum(pnls)
        return abs(total) / current_capital * 100 if total < 0 else 0.0

    def open_risk_pct(self, current_capital: float) -> float:
        if not self._open_trades or current_capital <= 0:
            return 0.0
        total_risk = sum(
            abs(t.get("stop_distance", 0)) * t.get("size", 0)
            for t in self._open_trades
        )
        return total_risk / current_capital * 100

    def guard_mode(self, current_capital: float) -> GuardMode:
        if self.kill_switch_active:
            return GuardMode.HALT
        dd = self.drawdown_pct(current_capital)
        if dd >= self.halt_dd_threshold:
            return GuardMode.HALT
        if dd >= self.emergency_dd_threshold:
            return GuardMode.EMERGENCY
        if self._consecutive_losses >= self.consecutive_loss_limit:
            return GuardMode.EMERGENCY
        if self.daily_loss_pct(current_capital) > self.max_daily_loss_pct * 0.8:
            return GuardMode.CAUTION
        if self.weekly_loss_pct(current_capital) > self.max_weekly_loss_pct * 0.8:
            return GuardMode.CAUTION
        if self._consecutive_losses >= self.consecutive_loss_limit * 0.6:
            return GuardMode.CAUTION
        return GuardMode.NORMAL

    def is_trading_allowed(self) -> bool:
        if self.kill_switch_active:
            return False
        return True

    def should_reduce_size(self, current_capital: float) -> float:
        reduction = 1.0
        mode = self.guard_mode(current_capital)

        if mode == GuardMode.HALT:
            return 0.0
        if mode == GuardMode.EMERGENCY:
            reduction *= 0.25
        if mode == GuardMode.CAUTION:
            reduction *= 0.5

        dl = self.daily_loss_pct(current_capital)
        wl = self.weekly_loss_pct(current_capital)
        if dl > self.max_daily_loss_pct * 0.7:
            reduction *= 0.5
        if wl > self.max_weekly_loss_pct * 0.7:
            reduction *= 0.5
        if self.open_risk_pct(current_capital) > self.max_open_risk_pct:
            reduction *= 0.5

        return max(reduction, 0.0)

    def can_enter_new_position(self, current_capital: float) -> bool:
        if self.kill_switch_active:
            return False
        mode = self.guard_mode(current_capital)
        if mode == GuardMode.HALT:
            return False
        if mode == GuardMode.EMERGENCY:
            dd = self.drawdown_pct(current_capital)
            if dd >= self.emergency_dd_threshold:
                return False
        return True

    def activate_kill_switch(self) -> None:
        self.kill_switch_active = True

    def deactivate_kill_switch(self) -> None:
        self.kill_switch_active = False

    def reset_consecutive_losses(self) -> None:
        self._consecutive_losses = 0

    def is_recovery_complete(self) -> bool:
        return self._recovery_trades >= self.recovery_min_trades

    def summary(self, current_capital: Optional[float] = None) -> Dict:
        cap = current_capital if current_capital is not None else self._equity_peak
        return {
            "mode": self.guard_mode(cap).value,
            "drawdown_pct": round(self.drawdown_pct(cap), 2),
            "daily_loss_pct": round(self.daily_loss_pct(cap), 2),
            "weekly_loss_pct": round(self.weekly_loss_pct(cap), 2),
            "open_risk_pct": round(self.open_risk_pct(cap), 2),
            "consecutive_losses": self._consecutive_losses,
            "kill_switch": self.kill_switch_active,
            "size_reduction": self.should_reduce_size(cap),
            "trading_allowed": self.is_trading_allowed(),
            "can_enter": self.can_enter_new_position(cap),
        }
