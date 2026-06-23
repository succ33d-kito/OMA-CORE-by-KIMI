"""OSIRIS Paper Trading Engine — Simulated execution of Council decisions
Manages positions, SL/TP, trailing stops, position sizing, and portfolio tracking.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from statistics import mean, stdev
from math import sqrt

from core.schemas.trade_schema import (
    TradeSignal, Trade, TradeDirection, TradeStatus, ExitReason,
)
from core.schemas.agent_schema import CouncilDecision, Recommendation, AgentOpinion
from core.schemas.trade_schema import DIRECTION_MAP
from core.execution.performance_memory import PerformanceMemory
from core.execution.slippage import SlippageEngine
from core.execution.direction_controller import DirectionController
from core.execution.capital_guard import CapitalGuard, GuardMode
from core.execution.crash_detector import CrashDetector
from core.execution.knife_detector import KnifeDetector
from core.execution.gap_risk import GapRiskEngine


class PaperTradingEngine:
    def __init__(
        self,
        initial_capital: float = 10000.0,
        max_open_positions: int = 5,
        performance_memory: Optional[PerformanceMemory] = None,
        council=None,
        slippage_engine: Optional[SlippageEngine] = None,
        direction_controller: Optional[DirectionController] = None,
        capital_guard: Optional[CapitalGuard] = None,
        crash_detector: Optional[CrashDetector] = None,
        knife_detector: Optional[KnifeDetector] = None,
        gap_risk_engine: Optional[GapRiskEngine] = None,
    ):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.max_open_positions = max_open_positions
        self.positions: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.performance = performance_memory or PerformanceMemory()
        self.council = council
        self.total_trades = 0
        self.total_wins = 0
        self.total_losses = 0
        self.closed_pnl = 0.0
        self.slippage = slippage_engine or SlippageEngine(slippage_pct=0.0)
        self.direction_ctrl = direction_controller or DirectionController()
        self.capital_guard = capital_guard or CapitalGuard(initial_capital=initial_capital)
        self.crash_detector = crash_detector or CrashDetector()
        self.knife_detector = knife_detector or KnifeDetector()
        self.gap_risk = gap_risk_engine or GapRiskEngine()

    def _risk_base(self) -> float:
        """Capital base for position sizing. Grows slowly to avoid unrealistic compounding.
        Increases at most 0.1% per trade from initial capital.
        """
        max_base = self.initial_capital * (1 + self.total_trades * 0.001)
        return min(self.capital, max_base)

    def update_market_data(self, symbol: str, price: float, timestamp: Optional[datetime] = None,
                           ohlcv_history: Optional[List[Dict]] = None) -> None:
        self.capital_guard.update_equity(self.capital)
        if symbol.upper() == "BTC":
            self.gap_risk.record_price(price, timestamp)
            self.crash_detector.update_price(price)
            if ohlcv_history:
                self._last_ohlcv = ohlcv_history
                for c in ohlcv_history[-20:]:
                    vol = c.get("volume")
                    if vol is not None:
                        self.crash_detector.update_price(price, vol)

    def process_decision(self, decision: CouncilDecision) -> Optional[TradeSignal]:
        if decision.action in (Recommendation.WATCH, Recommendation.NO_ACTION, Recommendation.HOLD):
            return None

        direction = DIRECTION_MAP.get(decision.action)
        if not direction or direction == TradeDirection.FLAT:
            return None

        if not self.capital_guard.is_trading_allowed():
            return None

        if direction == TradeDirection.SHORT and self.direction_ctrl.should_disable_short():
            return None
        if direction == TradeDirection.LONG and self.direction_ctrl.should_disable_long():
            return None

        guard_mode = self.capital_guard.guard_mode(self.capital)
        if guard_mode in (GuardMode.EMERGENCY, GuardMode.HALT) and not self.capital_guard.can_enter_new_position(self.capital):
            return None

        crash_mode = self.crash_detector.crash_mode(self.capital)
        if crash_mode.value == "panic":
            return None
        if crash_mode.value == "emergency" and direction == TradeDirection.LONG:
            # In emergency crash, LONG entries are high-risk dip buys
            # Check if it's a safe dip or falling knife
            ohlcv = self._last_ohlcv if hasattr(self, '_last_ohlcv') else None
            if ohlcv:
                closes = [c["close"] for c in ohlcv]
                volumes = [c["volume"] for c in ohlcv]
                highs = [c["high"] for c in ohlcv]
                lows = [c["low"] for c in ohlcv]
                if not self.knife_detector.is_safe_to_buy(closes, volumes, highs, lows):
                    return None

        opinions_with_meta = [o for o in decision.opinions if o.metadata]
        if not opinions_with_meta:
            return None

        meta = opinions_with_meta[0].metadata
        symbol = meta.get("symbol") or meta.get("asset")
        price = meta.get("price")
        if not symbol or not price or price <= 0:
            return None

        conviction = decision.conviction / 100.0
        risk_score = mean([o.risk_score for o in decision.opinions]) if decision.opinions else 0.5

        entry_price = self.slippage.entry_price(price, direction.value, symbol)
        suggested_stop = meta.get("suggested_stop_pct") or meta.get("atr_pct", 2.0) * 1.5
        stop_pct = max(suggested_stop, 1.0)

        gap_cushion = self.gap_risk.stop_cushion_multiplier()
        stop_pct *= gap_cushion

        rr_target = 2.0 if conviction > 0.7 else 1.5
        take_profit_pct = stop_pct * rr_target

        if direction == TradeDirection.LONG:
            sl_price = round(entry_price * (1 - stop_pct / 100), 8)
            tp_price = round(entry_price * (1 + take_profit_pct / 100), 8)
        else:
            sl_price = round(entry_price * (1 + stop_pct / 100), 8)
            tp_price = round(entry_price * (1 - take_profit_pct / 100), 8)

        sl = self.slippage.stop_price(sl_price, direction.value, symbol)
        tp = self.slippage.target_price(tp_price, direction.value, symbol)

        position_pct = conviction * (1.0 - risk_score) * 0.5
        max_pos_pct = meta.get("max_position_pct", 20.0) / 100.0
        position_pct = min(position_pct, max_pos_pct, 0.5)

        size_reduction = self.capital_guard.should_reduce_size(self._risk_base())
        gap_size_reduction = self.gap_risk.size_reduction()
        size_reduction = min(size_reduction, gap_size_reduction)
        position_pct *= size_reduction

        size = self._risk_base() * position_pct

        signal = TradeSignal(
            event_id=decision.event_id,
            council_decision_id=decision.event_id,
            asset=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=sl,
            take_profit=tp,
            position_size_pct=round(position_pct * 100, 1),
            conviction=decision.conviction,
            risk_score=risk_score,
            time_horizon_hours=24.0,
            rationale=decision.rationale[:200],
            metadata={"opinions": [o.to_dict() for o in decision.opinions]},
        )
        return signal

    def execute_signal(self, signal: TradeSignal) -> Optional[Trade]:
        if len(self.positions) >= self.max_open_positions:
            return None

        total_allocated = sum(p.signal.position_size_pct for p in self.positions)
        remaining_capacity = 100.0 - total_allocated
        if signal.position_size_pct > remaining_capacity:
            signal.position_size_pct = remaining_capacity

        size = self._risk_base() * (signal.position_size_pct / 100)
        if size <= 0 or signal.entry_price <= 0:
            return None

        trade = Trade(
            signal=signal,
            entry_time=datetime.now(timezone.utc),
            entry_price_executed=signal.entry_price,
            size=size,
        )
        self.positions.append(trade)
        return trade

    def check_positions(self, current_prices: Dict[str, float]) -> List[Trade]:
        closed = []
        remaining = []
        now = datetime.now(timezone.utc)
        for trade in self.positions:
            symbol = trade.signal.asset
            price = current_prices.get(symbol)
            if price is None:
                remaining.append(trade)
                continue

            direction = trade.signal.direction
            sl_target = trade.signal.stop_loss
            tp_target = trade.signal.take_profit

            if direction == TradeDirection.LONG:
                hit_sl = price <= sl_target
                hit_tp = price >= tp_target
            else:
                hit_sl = price >= sl_target
                hit_tp = price <= tp_target

            if hit_sl:
                exit_price = self.slippage.stop_price(sl_target, direction.value, symbol)
                trade.close(exit_price, ExitReason.STOP_LOSS)
                closed.append(trade)
                self._record_trade_result(trade)
            elif hit_tp:
                exit_price = self.slippage.target_price(tp_target, direction.value, symbol)
                trade.close(exit_price, ExitReason.TAKE_PROFIT)
                closed.append(trade)
                self._record_trade_result(trade)
            else:
                elapsed = (now - trade.entry_time).total_seconds() / 3600
                if trade.signal.time_horizon_hours > 0 and elapsed >= trade.signal.time_horizon_hours:
                    trade.close(price, ExitReason.TIME_EXPIRY)
                    closed.append(trade)
                    self._record_trade_result(trade)
                else:
                    remaining.append(trade)

        self.positions = remaining
        self.closed_trades.extend(closed)

        open_trade_data = [
            {
                "symbol": t.signal.asset,
                "size": t.size,
                "direction": t.signal.direction.value,
                "entry_price": t.entry_price_executed,
                "stop_loss": t.signal.stop_loss,
                "stop_distance": (t.entry_price_executed - t.signal.stop_loss) / t.entry_price_executed
                    if t.signal.direction.value == "long"
                    else (t.signal.stop_loss - t.entry_price_executed) / t.entry_price_executed,
            }
            for t in self.positions
        ]
        self.capital_guard.update_open_trades(open_trade_data)

        return closed

    def close_position(self, trade_id: str, reason: ExitReason = ExitReason.MANUAL) -> Optional[Trade]:
        for trade in self.positions:
            if trade.signal.event_id == trade_id:
                exit_price = self.slippage.exit_price(
                    trade.entry_price_executed, trade.signal.direction.value, trade.signal.asset
                )
                trade.close(exit_price, reason)
                self.positions.remove(trade)
                self.closed_trades.append(trade)
                self._record_trade_result(trade)
                return trade
        return None

    def _record_trade_result(self, trade: Trade) -> None:
        self.total_trades += 1
        if trade.pnl_percent and trade.pnl_percent > 0:
            self.total_wins += 1
        elif trade.pnl_percent and trade.pnl_percent < 0:
            self.total_losses += 1

        self.closed_pnl += trade.pnl_absolute or 0
        self.capital = max(self.initial_capital + self.closed_pnl, 0)

        self.direction_ctrl.record_trade(
            trade.signal.direction.value,
            trade.pnl_percent or 0,
        )
        self.capital_guard.record_trade_result(
            trade.pnl_absolute or 0,
        )
        self.crash_detector.record_trade_result(trade.pnl_percent or 0)

        correct = (trade.pnl_percent or 0) > 0
        for opinion in trade.signal.metadata.get("opinions", []):
            self.performance.record_opinion_outcome(
                agent_name=opinion.get("agent_name", "unknown"),
                opinion=opinion,
                trade_result=trade.pnl_percent or 0,
                correct=correct,
            )
            if self.council:
                self.council.update_track_record(
                    opinion.get("agent_name", "unknown"), correct
                )

        self.performance.record_trade(trade)

    def get_portfolio_summary(self) -> Dict[str, Any]:
        open_value = sum(t.size for t in self.positions)
        equity = self.initial_capital + self.closed_pnl

        win_rate = (self.total_wins / self.total_trades * 100) if self.total_trades > 0 else 0
        pnls = [t.pnl_percent for t in self.closed_trades if t.pnl_percent is not None]
        avg_pnl = mean(pnls) if pnls else 0
        sharpe = (mean(pnls) / stdev(pnls)) * sqrt(365) if len(pnls) > 1 and stdev(pnls) > 0 else 0

        crash_info = self.crash_detector.summary()
        gap_info = self.gap_risk.summary()
        guard_info = self.capital_guard.summary(self.capital)

        # Compute max drawdown from cumulative PnL history
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in self.closed_trades:
            cumulative += t.pnl_absolute or 0
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        max_dd_pct = max_dd / self.initial_capital * 100 if self.initial_capital > 0 else 0

        return {
            "initial_capital": self.initial_capital,
            "equity": round(equity, 2),
            "open_positions": len(self.positions),
            "closed_trades": len(self.closed_trades),
            "total_trades": self.total_trades,
            "wins": self.total_wins,
            "losses": self.total_losses,
            "win_rate": round(win_rate, 2),
            "avg_pnl_pct": round(avg_pnl, 2),
            "sharpe_ratio": round(sharpe, 2),
            "crash_score": crash_info["crash_score"],
            "crash_mode": crash_info["mode"],
            "gap_risk_score": gap_info["gap_risk_score"],
            "guard_mode": guard_info["mode"],
            "kill_switch": guard_info["kill_switch"],
            "total_pnl_abs": round(self.closed_pnl, 2),
            "total_return_pct": round(self.closed_pnl / self.initial_capital * 100, 2),
            "max_drawdown_pct": round(max_dd_pct, 2),
        }
