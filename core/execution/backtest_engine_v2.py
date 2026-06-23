"""OSIRIS Backtest Engine v2 — Real OHLCV-based backtesting
Replaces the heuristic BacktestEngine with data-driven simulation.
Uses Binance klines (free, no API key) as primary data source.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from statistics import mean, stdev
from math import sqrt
import json

from core.schemas.trade_schema import (
    TradeSignal, Trade, TradeDirection, TradeStatus, ExitReason
)
from core.schemas.agent_schema import Recommendation
from core.database.db import OMACoreDatabase


@dataclass
class BacktestTrade:
    signal: TradeSignal
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    pnl_percent: Optional[float] = None
    holding_hours: Optional[float] = None
    met_stop_loss: bool = False
    met_take_profit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.signal.asset,
            "direction": self.signal.direction.value,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_reason": self.exit_reason.value if self.exit_reason else None,
            "pnl_percent": self.pnl_percent,
            "holding_hours": self.holding_hours,
            "stop_loss": self.signal.stop_loss,
            "take_profit": self.signal.take_profit,
            "conviction": self.signal.conviction,
            "risk_score": self.signal.risk_score,
            "met_stop_loss": self.met_stop_loss,
            "met_take_profit": self.met_take_profit,
        }


class BacktestEngineV2:
    def __init__(self, db=None):
        self.db = db or OMACoreDatabase()

    def fetch_ohlcv(self, symbol: str, days: int = 30) -> Optional[List[Dict]]:
        try:
            import requests
            binance_map = {
                "BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT",
                "XRP": "XRPUSDT", "BNB": "BNBUSDT", "ADA": "ADAUSDT",
                "DOGE": "DOGEUSDT", "AVAX": "AVAXUSDT", "LINK": "LINKUSDT",
                "MATIC": "MATICUSDT", "DOT": "DOTUSDT", "UNI": "UNIUSDT",
                "LTC": "LTCUSDT", "BCH": "BCHUSDT", "ATOM": "ATOMUSDT",
            }
            if symbol in binance_map:
                pair = binance_map[symbol]
                url = "https://api.binance.com/api/v3/klines"
                resp = requests.get(url, params={"symbol": pair, "interval": "1h", "limit": days * 24}, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "time": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
                            "open": float(k[1]), "high": float(k[2]),
                            "low": float(k[3]), "close": float(k[4]),
                            "volume": float(k[5]),
                        }
                        for k in data
                    ]
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d", interval="1h")
            if not hist.empty:
                return [
                    {
                        "time": idx.to_pydatetime().replace(tzinfo=timezone.utc) if idx.tzinfo is None else idx.to_pydatetime(),
                        "open": float(r["Open"]), "high": float(r["High"]),
                        "low": float(r["Low"]), "close": float(r["Close"]),
                        "volume": float(r["Volume"]),
                    }
                    for idx, r in hist.iterrows()
                ]
        except Exception as e:
            print(f"[BacktestV2] OHLCV fetch error for {symbol}: {e}")
        return None

    def simulate(
        self,
        signal: TradeSignal,
        ohlcv: List[Dict],
    ) -> BacktestTrade:
        entry_idx = None
        for i, candle in enumerate(ohlcv):
            if candle["time"] >= signal.timestamp:
                entry_idx = i
                break

        if entry_idx is None or entry_idx >= len(ohlcv) - 1:
            return BacktestTrade(
                signal=signal,
                entry_time=ohlcv[-1]["time"],
                entry_price=ohlcv[-1]["close"],
                exit_reason=ExitReason.TIME_EXPIRY,
                pnl_percent=0.0,
                holding_hours=0,
            )

        entry_candle = ohlcv[entry_idx]
        entry_price = entry_candle["open"]
        direction = signal.direction
        sl = signal.stop_loss
        tp = signal.take_profit
        max_hours = signal.time_horizon_hours

        for j in range(entry_idx, min(entry_idx + int(max_hours), len(ohlcv))):
            candle = ohlcv[j]
            high, low = candle["high"], candle["low"]

            if direction == TradeDirection.LONG:
                if low <= sl:
                    return BacktestTrade(
                        signal=signal, entry_time=entry_candle["time"],
                        entry_price=entry_price, exit_time=candle["time"],
                        exit_price=sl, exit_reason=ExitReason.STOP_LOSS,
                        pnl_percent=round((sl - entry_price) / entry_price * 100, 2),
                        holding_hours=round((candle["time"] - entry_candle["time"]).total_seconds() / 3600, 1),
                        met_stop_loss=True,
                    )
                if high >= tp:
                    return BacktestTrade(
                        signal=signal, entry_time=entry_candle["time"],
                        entry_price=entry_price, exit_time=candle["time"],
                        exit_price=tp, exit_reason=ExitReason.TAKE_PROFIT,
                        pnl_percent=round((tp - entry_price) / entry_price * 100, 2),
                        holding_hours=round((candle["time"] - entry_candle["time"]).total_seconds() / 3600, 1),
                        met_take_profit=True,
                    )
            else:
                if high >= sl:
                    return BacktestTrade(
                        signal=signal, entry_time=entry_candle["time"],
                        entry_price=entry_price, exit_time=candle["time"],
                        exit_price=sl, exit_reason=ExitReason.STOP_LOSS,
                        pnl_percent=round((entry_price - sl) / entry_price * 100, 2),
                        holding_hours=round((candle["time"] - entry_candle["time"]).total_seconds() / 3600, 1),
                        met_stop_loss=True,
                    )
                if low <= tp:
                    return BacktestTrade(
                        signal=signal, entry_time=entry_candle["time"],
                        entry_price=entry_price, exit_time=candle["time"],
                        exit_price=tp, exit_reason=ExitReason.TAKE_PROFIT,
                        pnl_percent=round((entry_price - tp) / entry_price * 100, 2),
                        holding_hours=round((candle["time"] - entry_candle["time"]).total_seconds() / 3600, 1),
                        met_take_profit=True,
                    )

        last_idx = min(entry_idx + int(max_hours), len(ohlcv) - 1)
        exit_price = ohlcv[last_idx]["close"]
        if direction == TradeDirection.LONG:
            pnl = round((exit_price - entry_price) / entry_price * 100, 2)
        else:
            pnl = round((entry_price - exit_price) / entry_price * 100, 2)

        return BacktestTrade(
            signal=signal, entry_time=entry_candle["time"],
            entry_price=entry_price, exit_time=ohlcv[last_idx]["time"],
            exit_price=exit_price, exit_reason=ExitReason.TIME_EXPIRY,
            pnl_percent=pnl,
            holding_hours=round((ohlcv[last_idx]["time"] - entry_candle["time"]).total_seconds() / 3600, 1),
        )

    def run_backtest(
        self,
        signals: List[TradeSignal],
        days: int = 30,
    ) -> Dict[str, Any]:
        trades = []
        unique_assets = set(s.asset for s in signals)
        ohlcv_cache = {}

        for asset in unique_assets:
            ohlcv_cache[asset] = self.fetch_ohlcv(asset, days=days)

        for signal in signals:
            ohlcv = ohlcv_cache.get(signal.asset)
            if not ohlcv or len(ohlcv) < 20:
                continue
            trade = self.simulate(signal, ohlcv)
            trades.append(trade)

        if not trades:
            return {"status": "no_data", "total_trades": 0}

        total = len(trades)
        wins = sum(1 for t in trades if t.pnl_percent and t.pnl_percent > 0)
        losses = sum(1 for t in trades if t.pnl_percent and t.pnl_percent < 0)
        flat = sum(1 for t in trades if t.pnl_percent and t.pnl_percent == 0)

        win_rate = (wins / total * 100) if total > 0 else 0
        pnls = [t.pnl_percent for t in trades if t.pnl_percent is not None]
        total_pnl = sum(pnls)
        avg_pnl = mean(pnls) if pnls else 0

        win_pnls = [p for p in pnls if p > 0]
        loss_pnls = [p for p in pnls if p < 0]
        avg_win = mean(win_pnls) if win_pnls else 0
        avg_loss = mean(loss_pnls) if loss_pnls else 0

        profit_factor = abs(sum(win_pnls) / sum(loss_pnls)) if loss_pnls and sum(loss_pnls) != 0 else float("inf")

        equity = []
        running = 10000.0
        peak = 10000.0
        max_dd = 0.0
        for p in pnls:
            running *= (1 + p / 100)
            equity.append(running)
            if running > peak:
                peak = running
            dd = (peak - running) / peak * 100
            max_dd = max(max_dd, dd)

        expectancy = avg_pnl
        if stdev(pnls) > 0:
            sharpe = (mean(pnls) / stdev(pnls)) * sqrt(365)
        else:
            sharpe = 0.0

        by_asset = {}
        for t in trades:
            a = t.signal.asset
            if a not in by_asset:
                by_asset[a] = {"count": 0, "wins": 0, "pnl": 0.0}
            by_asset[a]["count"] += 1
            by_asset[a]["pnl"] += t.pnl_percent or 0
            if t.pnl_percent and t.pnl_percent > 0:
                by_asset[a]["wins"] += 1

        return {
            "status": "ok",
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "flat": flat,
            "win_rate": round(win_rate, 2),
            "total_pnl_pct": round(total_pnl, 2),
            "avg_pnl_pct": round(avg_pnl, 2),
            "avg_win_pct": round(avg_win, 2),
            "avg_loss_pct": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "Inf",
            "max_drawdown_pct": round(max_dd, 2),
            "sharpe_ratio": round(sharpe, 2),
            "expectancy_pct": round(expectancy, 2),
            "final_equity": round(running, 2),
            "total_return_pct": round((running - 10000) / 10000 * 100, 2),
            "by_asset": by_asset,
            "trades": [t.to_dict() for t in trades],
        }
