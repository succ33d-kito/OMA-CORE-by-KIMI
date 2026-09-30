"""Versioned checkpoint for the mutable paper portfolio and risk state."""

from collections import deque
from datetime import date, datetime

from core.schemas.trade_schema import Trade, TradeDirection, TradeSignal, TradeStatus, ExitReason

VERSION = 1


def _trade_dump(trade):
    return trade.to_dict() | {"updates": trade.updates}


def _trade_load(data):
    raw = data["signal"]
    signal = TradeSignal(
        event_id=raw["event_id"], council_decision_id=raw["council_decision_id"],
        asset=raw["asset"], direction=TradeDirection(raw["direction"]),
        entry_price=raw["entry_price"], stop_loss=raw["stop_loss"],
        take_profit=raw["take_profit"], position_size_pct=raw["position_size_pct"],
        conviction=raw["conviction"], risk_score=raw["risk_score"],
        time_horizon_hours=raw["time_horizon_hours"], rationale=raw["rationale"],
        timestamp=datetime.fromisoformat(raw["timestamp"]), metadata=raw["metadata"],
    )
    return Trade(
        signal=signal, entry_time=datetime.fromisoformat(data["entry_time"]),
        entry_price_executed=data["entry_price_executed"], size=data["size"],
        status=TradeStatus(data["status"]),
        exit_time=datetime.fromisoformat(data["exit_time"]) if data["exit_time"] else None,
        exit_price=data["exit_price"],
        exit_reason=ExitReason(data["exit_reason"]) if data["exit_reason"] else None,
        pnl_percent=data["pnl_percent"], pnl_absolute=data["pnl_absolute"],
        holding_hours=data["holding_hours"], updates=data.get("updates", []),
    )


def snapshot(engine):
    guard = engine.capital_guard
    return {
        "version": VERSION,
        "initial_capital": engine.initial_capital,
        "capital": engine.capital,
        "closed_pnl": engine.closed_pnl,
        "total_trades": engine.total_trades,
        "total_wins": engine.total_wins,
        "total_losses": engine.total_losses,
        "positions": [_trade_dump(t) for t in engine.positions],
        "closed_trades": [_trade_dump(t) for t in engine.closed_trades],
        "guard": {
            "kill_switch": guard.kill_switch_active,
            "daily_pnls": {d.isoformat(): v for d, v in guard._daily_pnls.items()},
            "weekly_pnls": {str(w): v for w, v in guard._weekly_pnls.items()},
            "equity_peak": guard._equity_peak,
            "consecutive_losses": guard._consecutive_losses,
            "total_trades": guard._total_trades,
            "recovery_trades": guard._recovery_trades,
        },
        "direction": {
            "long_pnls": list(engine.direction_ctrl._long_pnls),
            "short_pnls": list(engine.direction_ctrl._short_pnls),
        },
        "crash": {
            "price_history": engine.crash_detector._price_history,
            "volume_history": engine.crash_detector._volume_history,
            "consecutive_losses": engine.crash_detector._consecutive_losses,
            "peak_equity": engine.crash_detector._peak_equity,
        },
        "gap": {
            "price_history": engine.gap_risk._price_history,
            "historical_gaps": engine.gap_risk._historical_gaps,
        },
    }


def restore(engine, data):
    """Reject incomplete/foreign checkpoints before mutating live state."""
    if data.get("version") != VERSION or data.get("initial_capital") != engine.initial_capital:
        raise ValueError("incompatible paper checkpoint")
    required = ("capital", "closed_pnl", "total_trades", "total_wins", "total_losses",
                "positions", "closed_trades", "guard", "direction", "crash", "gap")
    if any(field not in data for field in required):
        raise ValueError("incomplete paper checkpoint")
    positions = [_trade_load(t) for t in data["positions"]]
    closed = [_trade_load(t) for t in data["closed_trades"]]
    if any(t.status != TradeStatus.OPEN for t in positions) or any(t.status != TradeStatus.CLOSED for t in closed):
        raise ValueError("inconsistent trade status in checkpoint")
    if data["total_trades"] != len(closed) or data["capital"] < 0:
        raise ValueError("inconsistent paper portfolio in checkpoint")
    guard, direction, crash, gap = (data[k] for k in ("guard", "direction", "crash", "gap"))
    engine.capital = data["capital"]
    engine.closed_pnl = data["closed_pnl"]
    engine.total_trades = data["total_trades"]
    engine.total_wins = data["total_wins"]
    engine.total_losses = data["total_losses"]
    engine.positions = positions
    engine.closed_trades = closed
    g = engine.capital_guard
    g.kill_switch_active = guard["kill_switch"]
    g._daily_pnls = {date.fromisoformat(k): v for k, v in guard["daily_pnls"].items()}
    g._weekly_pnls = {int(k): v for k, v in guard["weekly_pnls"].items()}
    g._equity_peak = guard["equity_peak"]
    g._consecutive_losses = guard["consecutive_losses"]
    g._total_trades = guard["total_trades"]
    g._recovery_trades = guard["recovery_trades"]
    g.update_open_trades([{
        "symbol": t.signal.asset, "size": t.size, "direction": t.signal.direction.value,
        "entry_price": t.entry_price_executed, "stop_loss": t.signal.stop_loss,
        "stop_distance": abs(t.entry_price_executed - t.signal.stop_loss) / t.entry_price_executed,
    } for t in positions])
    dc = engine.direction_ctrl
    dc._long_pnls = deque(direction["long_pnls"], maxlen=dc.window)
    dc._short_pnls = deque(direction["short_pnls"], maxlen=dc.window)
    c = engine.crash_detector
    c._price_history = crash["price_history"]
    c._volume_history = crash["volume_history"]
    c._consecutive_losses = crash["consecutive_losses"]
    c._peak_equity = crash["peak_equity"]
    engine.gap_risk._price_history = gap["price_history"]
    engine.gap_risk._historical_gaps = gap["historical_gaps"]
