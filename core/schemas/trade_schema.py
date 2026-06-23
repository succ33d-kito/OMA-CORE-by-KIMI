"""OSIRIS Trade Schema — Bridge between Council decisions and execution"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from core.schemas.agent_schema import Recommendation


class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class TradeStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ExitReason(Enum):
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    MANUAL = "manual"
    TIME_EXPIRY = "time_expiry"
    SIGNAL_REVERSAL = "signal_reversal"


@dataclass
class TradeSignal:
    event_id: str
    council_decision_id: str
    asset: str
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size_pct: float
    conviction: float
    risk_score: float
    time_horizon_hours: float
    rationale: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def risk_reward_ratio(self) -> float:
        if self.direction == TradeDirection.LONG:
            risk = self.entry_price - self.stop_loss
            reward = self.take_profit - self.entry_price
        else:
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.take_profit
        return round(reward / risk, 2) if risk > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "council_decision_id": self.council_decision_id,
            "asset": self.asset,
            "direction": self.direction.value,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size_pct": self.position_size_pct,
            "conviction": self.conviction,
            "risk_score": self.risk_score,
            "time_horizon_hours": self.time_horizon_hours,
            "risk_reward_ratio": self.risk_reward_ratio(),
            "rationale": self.rationale,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Trade:
    signal: TradeSignal
    entry_time: datetime
    entry_price_executed: float
    size: float
    status: TradeStatus = TradeStatus.OPEN
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    pnl_percent: Optional[float] = None
    pnl_absolute: Optional[float] = None
    holding_hours: Optional[float] = None
    updates: List[Dict[str, Any]] = field(default_factory=list)

    def close(self, exit_price: float, reason: ExitReason, exit_time: Optional[datetime] = None) -> None:
        self.exit_price = exit_price
        self.exit_reason = reason
        self.exit_time = exit_time or datetime.now(timezone.utc)
        self.status = TradeStatus.CLOSED
        holding = (self.exit_time - self.entry_time).total_seconds() / 3600
        self.holding_hours = round(holding, 2)
        if self.signal.direction == TradeDirection.LONG:
            self.pnl_percent = round((exit_price - self.entry_price_executed) / self.entry_price_executed * 100, 2)
        else:
            self.pnl_percent = round((self.entry_price_executed - exit_price) / self.entry_price_executed * 100, 2)
        self.pnl_absolute = round(self.pnl_percent * self.size / 100, 2)
        self.updates.append({
            "type": "close",
            "time": self.exit_time.isoformat(),
            "price": exit_price,
            "reason": reason.value,
            "pnl_pct": self.pnl_percent,
            "pnl_abs": self.pnl_absolute,
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal": self.signal.to_dict(),
            "entry_time": self.entry_time.isoformat(),
            "entry_price_executed": self.entry_price_executed,
            "size": self.size,
            "status": self.status.value,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason.value if self.exit_reason else None,
            "pnl_percent": self.pnl_percent,
            "pnl_absolute": self.pnl_absolute,
            "holding_hours": self.holding_hours,
        }


DIRECTION_MAP = {
    Recommendation.STRONG_BUY: TradeDirection.LONG,
    Recommendation.BUY: TradeDirection.LONG,
    Recommendation.HOLD: TradeDirection.FLAT,
    Recommendation.SELL: TradeDirection.SHORT,
    Recommendation.STRONG_SELL: TradeDirection.SHORT,
    Recommendation.WATCH: TradeDirection.FLAT,
    Recommendation.AVOID: TradeDirection.FLAT,
    Recommendation.HEDGE: TradeDirection.SHORT,
    Recommendation.NO_ACTION: TradeDirection.FLAT,
}
