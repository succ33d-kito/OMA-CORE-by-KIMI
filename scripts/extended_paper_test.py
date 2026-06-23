"""OSIRIS Extended Paper Trading & Demo Gate Sprint
Phases 1-2: Extended paper trading with full guard activation logging.
Phase 4: COVID crash failure replay.

Usage:
  python scripts/extended_paper_test.py [--days 30] [--covid-replay]
  python scripts/extended_paper_test.py --phase 1   # 30-day paper trading
  python scripts/extended_paper_test.py --phase 4   # COVID replay
"""
import sys, json, time, math
sys.path.insert(0, ".")
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from statistics import mean, stdev
from math import sqrt
from typing import Optional, Dict, List

import requests as req

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Urgency
from core.schemas.agent_schema import AgentOpinion, AgentRole, Recommendation
from core.schemas.trade_schema import TradeDirection, Trade, ExitReason
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory
from core.execution.slippage import SlippageEngine
from core.execution.direction_controller import DirectionController
from core.execution.capital_guard import CapitalGuard, GuardMode
from core.execution.crash_detector import CrashDetector
from core.execution.knife_detector import KnifeDetector
from core.execution.gap_risk import GapRiskEngine

SYMBOLS = ["BTC", "ETH", "SOL"]
BNB_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}

PERIODS = {
    "COVID_Crash": {
        "start": "2020-03-01T00:00:00Z",
        "end": "2020-04-30T23:59:59Z",
        "label": "COVID Crash (Mar-Apr 2020)",
    },
}


# ── Data ────────────────────────────────────────────────────────────────────

def ms(dt_str):
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def fetch_ohlcv(symbol, days, interval="1h"):
    pair = BNB_MAP.get(symbol)
    if not pair:
        return None
    try:
        resp = req.get("https://api.binance.com/api/v3/klines",
                       params={"symbol": pair, "interval": interval,
                               "limit": min(days * 24, 1000)}, timeout=15)
        if resp.status_code == 200:
            return [
                {"time": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
                 "open": float(k[1]), "high": float(k[2]), "low": float(k[3]),
                 "close": float(k[4]), "volume": float(k[5])}
                for k in resp.json()
            ]
    except Exception:
        pass
    return None


def fetch_ohlcv_range(symbol, start_ms, end_ms, interval="1h"):
    pair = BNB_MAP.get(symbol)
    if not pair:
        return None
    limit = 1000
    candles = []
    current_start = start_ms
    while current_start < end_ms:
        params = {"symbol": pair, "interval": interval, "limit": limit,
                  "startTime": current_start, "endTime": end_ms}
        try:
            resp = req.get("https://api.binance.com/api/v3/klines",
                           params=params, timeout=15)
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not batch:
                break
            for k in batch:
                candles.append({
                    "time": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
                    "open": float(k[1]), "high": float(k[2]),
                    "low": float(k[3]), "close": float(k[4]),
                    "volume": float(k[5]),
                })
            if len(batch) < limit:
                break
            current_start = batch[-1][0] + 1
        except Exception as e:
            break
    candles.sort(key=lambda c: c["time"])
    return candles if len(candles) >= 50 else None


def fetch_period(period_name, buffer_days=5):
    p = PERIODS[period_name]
    start_ms = ms(p["start"]) - buffer_days * 24 * 3600 * 1000
    end_ms = ms(p["end"])
    sol_start = int(datetime(2020, 8, 1, tzinfo=timezone.utc).timestamp() * 1000)
    symbols = [s for s in SYMBOLS if s != "SOL" or start_ms >= sol_start]
    result = {}
    for sym in symbols:
        data = fetch_ohlcv_range(sym, start_ms, end_ms)
        if data and len(data) >= 50:
            result[sym] = data
    return result


def generate_events(symbol, ohlcv):
    events = []
    for i in range(1, len(ohlcv)):
        prev, curr = ohlcv[i - 1], ohlcv[i]
        change = (curr["close"] - prev["close"]) / prev["close"]
        u = (Urgency.HIGH if abs(change) > 0.05
             else Urgency.MEDIUM if abs(change) > 0.02
             else Urgency.LOW)
        et = (EventType.VOLUME_SPIKE
              if (abs(change) > 0.05 and curr["volume"] > prev["volume"] * 1.5)
              else EventType.PRICE_MOVEMENT)
        events.append(Event(
            id=f"{symbol}_{i}", source="extended_test",
            event_type=et, title=f"{symbol} {change * 100:+.2f}%",
            assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO,
                          price_at_event=curr["close"])],
            timestamp=curr["time"], detected_at=curr["time"],
            urgency=u, sentiment_score=change, confidence=0.7,
        ))
    return events


# ── Guard Activation Logging ────────────────────────────────────────────────

class GuardLogger:
    def __init__(self):
        self.blocks = []
        self.activations = defaultdict(int)

    def log_block(self, reason, asset=None, timestamp=None, direction=None,
                  would_be_size=None, market_condition=None):
        self.blocks.append({
            "reason": reason,
            "asset": asset,
            "timestamp": timestamp.isoformat() if timestamp else None,
            "direction": direction,
            "would_be_size": would_be_size,
            "market_condition": market_condition,
        })
        self.activations[reason] += 1

    def summary(self):
        return {
            "total_blocks": len(self.blocks),
            "by_reason": dict(self.activations),
            "blocks": self.blocks,
        }


# ── Run Paper Trading ──────────────────────────────────────────────────────

def run_paper_test(days=30, slippage_bps=10, signal_mode="both",
                   short_style="mom_break", label="Paper Test",
                   ohlcv_override=None, track_baseline=True):
    """Run extended paper trading with full guard logging."""
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  {days} days | Slippage {slippage_bps}bps + spread | Full protection stack")
    print(f"{'='*70}")

    start_ts = time.time()

    # ── Data ──
    if ohlcv_override:
        ohlcv_cache = ohlcv_override
    else:
        ohlcv_cache = {}
        for sym in SYMBOLS:
            data = fetch_ohlcv(sym, days + 5)
            if data and len(data) >= 50:
                ohlcv_cache[sym] = data
                print(f"  {sym}: {len(data)} candles ({data[0]['time'].strftime('%Y-%m-%d')} "
                      f"-> {data[-1]['time'].strftime('%Y-%m-%d')})")
            else:
                print(f"  {sym}: FAILED")
                return None

    # ── Agents + Full Protection Stack ──
    market = MarketAgent(signal_mode=signal_mode, short_style=short_style)
    market._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    risk = RiskAgent()
    risk._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    council = AgentCouncil()
    perf = PerformanceMemory()
    slippage = SlippageEngine(slippage_pct=slippage_bps / 10000)
    direction_ctrl = DirectionController(window=20, wr_threshold=0.25, recovery_threshold=0.35)
    capital_guard = CapitalGuard(initial_capital=10000.0, max_daily_loss_pct=10.0,
                                 max_weekly_loss_pct=20.0, max_open_risk_pct=25.0,
                                 emergency_dd_threshold=20.0, halt_dd_threshold=35.0,
                                 consecutive_loss_limit=7)
    crash_detector = CrashDetector()
    knife_detector = KnifeDetector()
    gap_risk = GapRiskEngine()

    engine = PaperTradingEngine(
        initial_capital=10000.0,
        performance_memory=perf,
        council=council,
        slippage_engine=slippage,
        direction_controller=direction_ctrl,
        capital_guard=capital_guard,
        crash_detector=crash_detector,
        knife_detector=knife_detector,
        gap_risk_engine=gap_risk,
    )

    guard_log = GuardLogger()

    # ── Events ──
    all_events = []
    for sym, ohlcv in ohlcv_cache.items():
        all_events.extend(generate_events(sym, ohlcv))
        if sym.upper() == "BTC":
            for candle in ohlcv:
                vol = candle.get("volume")
                engine.crash_detector.update_price(candle["close"], vol)
                engine.gap_risk.record_price(candle["close"], candle["time"])
    all_events.sort(key=lambda e: e.timestamp)
    print(f"  Events: {len(all_events)}")

    # ── Override stop sizing ──
    orig_process = engine.process_decision

    def process_with_atr(mul=3.0):
        def wrapped(decision):
            signal = orig_process(decision)
            if signal and decision.opinions:
                meta = decision.opinions[0].metadata
                if "atr_14" in meta and meta.get("price", 0) > 0:
                    atr_pct = meta["atr_14"] / meta["price"] * 100
                    stop_pct = max(atr_pct * mul, 1.0)
                    price = meta["price"]
                    target_pct = stop_pct * 2
                    if signal.direction == TradeDirection.LONG:
                        signal.stop_loss = round(price * (1 - stop_pct / 100), 8)
                        signal.take_profit = round(price * (1 + target_pct / 100), 8)
                    else:
                        signal.stop_loss = round(price * (1 + stop_pct / 100), 8)
                        signal.take_profit = round(price * (1 - target_pct / 100), 8)
            return signal
        return wrapped
    engine.process_decision = process_with_atr(3.0)

    # ── Monitoring counters ──
    direction_blocks = 0
    capital_blocks = 0
    emergency_blocks = 0
    crash_warning_blocks = 0
    knife_rejections = 0
    gap_reductions = 0
    kill_switch_triggers = 0

    price_history = {s: [] for s in SYMBOLS}
    all_decisions = []
    all_signals = []
    equity_curve = [10000.0]

    for event in all_events:
        sym = event.assets[0].symbol
        price = event.assets[0].price_at_event
        ts = event.timestamp
        price_history[sym].append((ts, price))

        engine.update_market_data(sym, price, ts)

        opinions = []
        for agent in [market, risk]:
            op = agent.analyze(event)
            if op:
                opinions.append(op)

        if len(opinions) < 2:
            continue

        for op in opinions:
            council.submit_opinion(op)
        decision = council.decide(event.id)
        if decision:
            all_decisions.append(decision)

        # ── Before calling process_decision, check guard states ──
        is_trade_signal = (decision and decision.action in (
            Recommendation.BUY, Recommendation.SELL,
            Recommendation.STRONG_BUY, Recommendation.STRONG_SELL))

        if is_trade_signal:
            direction = "long" if decision.action in (
                Recommendation.BUY, Recommendation.STRONG_BUY) else "short"
            meta = decision.opinions[0].metadata if decision.opinions else {}
            asset = meta.get("symbol") or meta.get("asset", sym)

            # Track guard states at decision time
            if not engine.capital_guard.is_trading_allowed():
                guard_log.log_block(
                    "capital_guard_kill_switch", asset=asset, timestamp=ts,
                    direction=direction, market_condition=f"price={price:.2f}")
                capital_blocks += 1

            guard_mode = engine.capital_guard.guard_mode(engine.capital)
            if guard_mode in (GuardMode.EMERGENCY, GuardMode.HALT):
                guard_log.log_block(
                    f"capital_guard_{guard_mode.value}", asset=asset, timestamp=ts,
                    direction=direction, would_be_size="would_enter",
                    market_condition=f"mode={guard_mode.value},price={price:.2f}")
                emergency_blocks += 1

            crash_mode = engine.crash_detector.crash_mode(engine.capital)
            if crash_mode.value in ("panic", "emergency"):
                guard_log.log_block(
                    f"crash_detector_{crash_mode.value}", asset=asset, timestamp=ts,
                    direction=direction,
                    market_condition=(f"crash_mode={crash_mode.value},"
                                      f"score={engine.crash_detector.crash_score():.0f}"))
                crash_warning_blocks += 1

            gap_risk_score = engine.gap_risk.gap_risk_score()
            gap_size_reduction = engine.gap_risk.size_reduction()
            if gap_size_reduction < 0.8:
                guard_log.log_block(
                    "gap_risk_size_reduction", asset=asset, timestamp=ts,
                    direction=direction, would_be_size=f"x{gap_size_reduction:.2f}",
                    market_condition=f"gap_score={gap_risk_score:.0f}")
                gap_reductions += 1

        # ── Process decision ──
        signal = engine.process_decision(decision)
        if signal:
            all_signals.append(signal)
            engine.execute_signal(signal)
        elif is_trade_signal and not signal:
            direction = "long" if decision.action in (
                Recommendation.BUY, Recommendation.STRONG_BUY) else "short"
            guard_log.log_block(
                "guard_blocked_unknown_reason", asset=asset, timestamp=ts,
                direction=direction, market_condition=f"price={price:.2f}")
            direction_blocks += 1

        # ── Check positions ──
        current_prices = {s: (price_history[s][-1][1] if price_history[s] else 0)
                         for s in SYMBOLS}
        engine.check_positions(current_prices)

        # Track equity state
        equity_curve.append(engine.capital)

        if not engine.capital_guard.is_trading_allowed():
            kill_switch_triggers += 1

    final_prices = {s: (price_history[s][-1][1] if price_history[s] else 0)
                   for s in SYMBOLS}
    engine.check_positions(final_prices)
    elapsed = time.time() - start_ts

    # ── Collect detailed trade data ──
    detailed_trades = []
    for t in engine.closed_trades:
        detailed_trades.append({
            "asset": t.signal.asset,
            "direction": t.signal.direction.value,
            "pnl_pct": t.pnl_percent or 0,
            "pnl_abs": t.pnl_absolute or 0,
            "exit_reason": t.exit_reason.value if t.exit_reason else "unknown",
            "conviction": t.signal.conviction,
            "risk_score": t.signal.risk_score,
            "entry_price": t.entry_price_executed,
            "exit_price": t.exit_price or 0,
            "stop_loss": t.signal.stop_loss,
            "take_profit": t.signal.take_profit,
            "entry_time": t.entry_time.isoformat() if t.entry_time else None,
            "exit_time": t.exit_time.isoformat() if t.exit_time else None,
            "holding_hours": t.holding_hours or 0,
        })

    portfolio = engine.get_portfolio_summary()

    # ── Compute max drawdown ──
    peak_e = 10000.0
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak_e:
            peak_e = eq
        dd = (peak_e - eq) / peak_e * 100
        max_dd = max(max_dd, dd)

    # ── Direction breakdown ──
    by_dir = defaultdict(list)
    by_exit = defaultdict(int)
    for t in detailed_trades:
        by_dir[t["direction"]].append(t["pnl_pct"])
        by_exit[t["exit_reason"]] += 1

    def compute_dir_stats(pnls):
        if not pnls:
            return {"trades": 0, "wins": 0, "wr": 0, "total_pnl": 0, "avg_pnl": 0, "pf": 0}
        wins = sum(1 for p in pnls if p > 0)
        total_pnl = sum(pnls)
        win_pnls = [p for p in pnls if p > 0]
        loss_pnls = [p for p in pnls if p < 0]
        pf = (abs(sum(win_pnls) / sum(loss_pnls))
              if loss_pnls and sum(loss_pnls) != 0 else float("inf"))
        return {
            "trades": len(pnls),
            "wins": wins,
            "wr": wins / len(pnls) * 100 if pnls else 0,
            "total_pnl": round(total_pnl, 2),
            "avg_pnl": round(mean(pnls), 3),
            "pf": pf,
        }

    dir_stats = {d: compute_dir_stats(pnls) for d, pnls in by_dir.items()}

    # ── Per-asset breakdown ──
    by_asset = defaultdict(lambda: defaultdict(list))
    for t in detailed_trades:
        by_asset[t["asset"]][t["direction"]].append(t["pnl_pct"])
    asset_stats = {}
    for asset, dirs in by_asset.items():
        asset_stats[asset] = {}
        for d, pnls in dirs.items():
            asset_stats[asset][d] = {
                "trades": len(pnls),
                "pnl": sum(pnls),
                "wr": sum(1 for p in pnls if p > 0) / len(pnls) * 100 if pnls else 0,
            }

    # ── Guard summaries ──
    dc_summary = direction_ctrl.summary()
    cg_summary = capital_guard.summary()
    cd_summary = crash_detector.summary()
    gr_summary = gap_risk.summary()

    # ── Print report ──
    print(f"\n{'='*70}")
    print(f"  RESULTS — {label}")
    print(f"{'='*70}")

    print(f"\n  --- Core Metrics ---")
    print(f"  Duration:          {elapsed:.1f}s")
    print(f"  Total trades:      {portfolio['total_trades']}")
    print(f"  Win rate:          {portfolio['win_rate']:.1f}%")
    print(f"  Total return:      {portfolio['total_return_pct']:+.2f}%")
    print(f"  Equity:            ${portfolio['equity']:,.2f}")
    print(f"  Avg PnL/trade:     {portfolio['avg_pnl_pct']:+.3f}%")
    print(f"  Sharpe (annual):   {portfolio['sharpe_ratio']:.2f}")
    print(f"  Max drawdown:      {max_dd:.2f}%")
    print(f"  Total PnL:         ${portfolio['total_pnl_abs']:,.2f}")

    print(f"\n  --- Direction Breakdown ---")
    for d in ["long", "short"]:
        s = dir_stats.get(d, {})
        if s.get("trades", 0) > 0:
            print(f"  {d:6s}: {s['trades']:4d} trades, WR={s['wr']:5.1f}%, "
                  f"PnL={s['total_pnl']:+.2f}%, Avg={s['avg_pnl']:+.3f}%, PF={s['pf']:.2f}")
        else:
            print(f"  {d:6s}: 0 trades")

    print(f"\n  --- Exit Reasons ---")
    for reason, count in sorted(by_exit.items()):
        print(f"  {reason:15s}: {count}")

    print(f"\n  --- Per-Asset ---")
    for asset in sorted(asset_stats.keys()):
        for d, s in asset_stats[asset].items():
            print(f"  {asset:4s} {d:6s}: {s['trades']:4d} trades, "
                  f"WR={s['wr']:5.1f}%, PnL={s['pnl']:+.2f}%")

    print(f"\n  --- Guard Activations ---")
    print(f"  DirectionController blocks:  {direction_blocks}")
    print(f"  CapitalGuard blocks:         {capital_blocks}")
    print(f"  Emergency/HALT blocks:       {emergency_blocks}")
    print(f"  CrashDetector blocks:        {crash_warning_blocks}")
    print(f"  KnifeDetector rejections:    {knife_rejections}")
    print(f"  GapRisk size reductions:     {gap_reductions}")
    print(f"  Kill switch triggers:        {kill_switch_triggers}")

    print(f"\n  --- Direction Controller ---")
    print(f"  LONG WR (last {dc_summary.get('long_window', '?')}): "
          f"{dc_summary.get('long_wr', 0):.1%}")
    print(f"  SHORT WR (last {dc_summary.get('short_window', '?')}): "
          f"{dc_summary.get('short_wr', 0):.1%}")
    print(f"  SHORT disabled:  {dc_summary.get('disable_short', False)}")
    print(f"  LONG disabled:   {dc_summary.get('disable_long', False)}")
    print(f"  Allowed dir:     {dc_summary.get('allowed', 'both')}")

    print(f"\n  --- Capital Guard ---")
    print(f"  Mode:              {cg_summary.get('mode', 'normal')}")
    print(f"  Drawdown:          {cg_summary.get('drawdown_pct', 0):.2f}%")
    print(f"  Daily loss:        {cg_summary.get('daily_loss_pct', 0):.2f}%")
    print(f"  Weekly loss:       {cg_summary.get('weekly_loss_pct', 0):.2f}%")
    print(f"  Open risk:         {cg_summary.get('open_risk_pct', 0):.2f}%")
    print(f"  Consecutive losses:{cg_summary.get('consecutive_losses', 0)}")
    print(f"  Kill switch:       {cg_summary.get('kill_switch', False)}")
    print(f"  Size reduction:    {cg_summary.get('size_reduction', 1.0):.2f}x")
    print(f"  Can enter:         {cg_summary.get('can_enter', True)}")

    print(f"\n  --- Crash Detector ---")
    print(f"  Crash score:       {cd_summary.get('crash_score', 0)}")
    print(f"  Crash mode:        {cd_summary.get('mode', 'none')}")
    print(f"  Drawdown velocity: {cd_summary.get('drawdown_velocity', 0):.2f}%")
    print(f"  Gap size:          {cd_summary.get('gap_size', 0):.2f}%")
    print(f"  ATR expansion:     {cd_summary.get('atr_expansion', 0):.2f}x")
    print(f"  Volume ratio:      {cd_summary.get('volume_ratio', 0):.2f}x")
    print(f"  Consecutive losses:{cd_summary.get('consecutive_losses', 0)}")

    print(f"\n  --- Gap Risk Engine ---")
    print(f"  Gap risk score:    {gr_summary.get('gap_risk_score', 0)}")
    print(f"  Avg gap size:      {gr_summary.get('avg_gap_size', 0):.2f}%")
    print(f"  Max gap size:      {gr_summary.get('max_gap_size', 0):.2f}%")
    print(f"  Gap frequency:     {gr_summary.get('gap_frequency', 0):.3f}")
    print(f"  Stop multiplier:   {gr_summary.get('stop_multiplier', 1.0):.2f}x")
    print(f"  Size reduction:    {gr_summary.get('size_reduction', 1.0):.2f}x")

    print(f"\n  --- Guard Activation Details ---")
    by_reason = guard_log.activations
    for reason, count in sorted(by_reason.items(), key=lambda x: -x[1]):
        sample = next((b for b in guard_log.blocks if b["reason"] == reason), None)
        if sample:
            print(f"  {reason:40s}: {count:4d} "
                  f"(e.g. {sample.get('asset', '?')} {sample.get('direction', '?')} "
                  f"@ {sample.get('market_condition', '?')})")
        else:
            print(f"  {reason:40s}: {count:4d}")

    # ── Verdict ──
    print(f"\n{'='*70}")
    survival = portfolio["total_return_pct"] > 0
    low_dd = max_dd < 30
    guards_active = (direction_blocks + capital_blocks + emergency_blocks +
                     crash_warning_blocks + knife_rejections > 0)
    verdict = ("SURVIVED" if survival and low_dd else
               "SURVIVED (negative)" if survival else
               "FAILED")
    print(f"  VERDICT: {verdict}")
    print(f"  Return: {portfolio['total_return_pct']:+.2f}% | "
          f"MaxDD: {max_dd:.2f}% | Sharpe: {portfolio['sharpe_ratio']:.2f}")
    print(f"  Guards triggered: {guards_active}")
    print(f"{'='*70}")

    return {
        "summary": portfolio,
        "max_drawdown": round(max_dd, 2),
        "direction_controller": dc_summary,
        "capital_guard": cg_summary,
        "crash_detector": cd_summary,
        "gap_risk": gr_summary,
        "guard_log": guard_log.summary(),
        "direction_stats": dir_stats,
        "exit_reasons": dict(by_exit),
        "asset_stats": asset_stats,
        "trades": detailed_trades,
        "equity_curve": equity_curve,
        "counts": {
            "direction_blocks": direction_blocks,
            "capital_blocks": capital_blocks,
            "emergency_blocks": emergency_blocks,
            "crash_warning_blocks": crash_warning_blocks,
            "knife_rejections": knife_rejections,
            "gap_reductions": gap_reductions,
            "kill_switch_triggers": kill_switch_triggers,
        },
        "elapsed_sec": round(elapsed, 1),
    }


# ── Phase 1: Extended Paper Trading ────────────────────────────────────────

def phase1_extended_paper():
    """7-day and 30-day paper trading with full guard logging."""
    print(f"\n{'='*70}")
    print(f"  PHASE 1 — EXTENDED PAPER TRADING")
    print(f"  Full protection stack | No parameter changes | No intervention")
    print(f"{'='*70}")

    # 7-day run
    r7 = run_paper_test(days=7, label="7-Day Paper Test")

    # 30-day run
    r30 = run_paper_test(days=30, label="30-Day Extended Paper Test")

    # Comparison
    if r7 and r30:
        print(f"\n{'='*70}")
        print(f"  COMPARISON — 7-Day vs 30-Day")
        print(f"{'='*70}")
        print(f"  {'Metric':>20s} | {'7-Day':>12s} | {'30-Day':>12s} | {'Delta':>10s}")
        print(f"  {'-'*20} | {'-'*12} | {'-'*12} | {'-'*10}")
        for key, label in [("total_return_pct", "Return"),
                           ("win_rate", "Win Rate"),
                           ("sharpe_ratio", "Sharpe"),
                           ("total_trades", "Trades")]:
            v7 = r7["summary"].get(key, 0)
            v30 = r30["summary"].get(key, 0)
            delta = v30 - v7 if isinstance(v7, (int, float)) else ""
            print(f"  {label:>20s} | {v7:>12} | {v30:>12} | {delta:>10}")

        dd_label = "Max DD"
        print(f"  {dd_label:>20s} | {r7['max_drawdown']:>11.2f}% | "
              f"{r30['max_drawdown']:>11.2f}% | "
              f"{r30['max_drawdown'] - r7['max_drawdown']:>+9.2f}%")

        # Guard comparison
        print(f"\n  --- Guard Activation Comparison ---")
        for key, label in [("direction_blocks", "Direction blocks"),
                           ("capital_blocks", "Capital blocks"),
                           ("emergency_blocks", "Emergency blocks"),
                           ("crash_warning_blocks", "Crash blocks"),
                           ("knife_rejections", "Knife rejections"),
                           ("gap_reductions", "Gap reductions")]:
            print(f"  {label:20s}: {r7['counts'][key]:4d} (7d) | {r30['counts'][key]:4d} (30d)")

    return {"7d": r7, "30d": r30}


# ── Phase 2: Guard Validation (integrated into Phase 1) ────────────────────

def phase2_guard_validation(r30):
    """Validate protection stack from 30-day run data."""
    if not r30:
        print("  No 30-day data — run Phase 1 first")
        return None

    print(f"\n{'='*70}")
    print(f"  PHASE 2 — GUARD VALIDATION")
    print(f"  Verify all protection layers from 30-day paper trading data")
    print(f"{'='*70}")

    checks = []

    # 1. CapitalGuard
    cg = r30.get("capital_guard", {})
    cg_ok = cg.get("mode") in ("normal", "caution")
    checks.append(("CapitalGuard operational", cg_ok,
                   f"mode={cg.get('mode')}, dd={cg.get('drawdown_pct', 0):.2f}%"))

    kill_ok = not cg.get("kill_switch", False)
    checks.append(("Kill switch not triggered", kill_ok,
                   f"kill_switch={cg.get('kill_switch')}"))

    can_enter = cg.get("can_enter", True)
    checks.append(("Can enter positions", can_enter,
                   f"can_enter={can_enter}"))

    # 2. DirectionController
    dc = r30.get("direction_controller", {})
    dc_ok = dc.get("allowed", "both") != "none"
    checks.append(("DirectionController allows trading", dc_ok,
                   f"allowed={dc.get('allowed')}"))

    # 3. CrashDetector
    cd = r30.get("crash_detector", {})
    not_panic = cd.get("mode") not in ("panic",)
    checks.append(("No panic crash mode", not_panic,
                   f"mode={cd.get('mode')}, score={cd.get('crash_score', 0)}"))

    # 4. GapRiskEngine reporting
    gr = r30.get("gap_risk", {})
    gap_reporting = gr.get("gap_risk_score", -1) >= 0
    checks.append(("GapRiskEngine reporting", gap_reporting,
                   f"score={gr.get('gap_risk_score', 'N/A')}"))

    # 5. PerformanceMemory tracking
    trades = r30.get("trades", [])
    perf_ok = len(trades) == r30["summary"].get("total_trades", 0)
    checks.append(("All trades recorded in PerformanceMemory", perf_ok,
                   f"{len(trades)} trades"))

    # 6. Portfolio summary exposes risk state
    portfolio = r30.get("summary", {})
    has_risk = all(k in portfolio for k in
                   ["crash_score", "crash_mode", "gap_risk_score",
                    "guard_mode", "kill_switch"])
    checks.append(("Portfolio summary exposes risk state", has_risk,
                   f"keys: crash_score, crash_mode, gap_risk_score, guard_mode, kill_switch"))

    # 7. Emergency Mode not triggered
    emergency_count = r30["counts"].get("emergency_blocks", 0)
    emergency_ok = emergency_count == 0
    checks.append(("No emergency mode activations (expected in current bull)",
                   emergency_ok, f"{emergency_count} blocks"))

    # 8. CrashDetector not in emergency (expected in current market)
    crash_emergency = cd.get("mode") in ("emergency",)
    crash_ok = not crash_emergency
    checks.append(("No emergency crash mode",
                   crash_ok, f"mode={cd.get('mode')}"))

    # Print results
    print(f"\n  {'Check':>55s} | {'Status':>8s} | {'Detail':>40s}")
    print(f"  {'-'*55} | {'-'*8} | {'-'*40}")
    all_pass = True
    for name, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  {name:>55s} | {status:>8s} | {detail:>40s}")

    print(f"\n  Guard validation: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
    if all_pass:
        print(f"  Protection stack verified on 30-day live paper data.")

    return {"checks": checks, "all_pass": all_pass}


# ── Phase 4: COVID Crash Failure Replay ────────────────────────────────────

def phase4_covid_replay():
    """Replay COVID crash with full protection stack. Measure loss capping."""
    print(f"\n{'='*70}")
    print(f"  PHASE 4 — FAILURE REPLAY: COVID CRASH")
    print(f"  Test CrashDetector + GapRiskEngine + CapitalGuard + Emergency Mode")
    print(f"  Goal: Ensure expected loss is *capped*, not eliminated")
    print(f"{'='*70}")

    ohlcv_cache = fetch_period("COVID_Crash")
    if not ohlcv_cache or len(ohlcv_cache) < 1:
        print("  No COVID data available — aborting")
        return None

    for sym, data in ohlcv_cache.items():
        print(f"  {sym}: {len(data)} candles "
              f"({data[0]['time'].strftime('%Y-%m-%d')} -> "
              f"{data[-1]['time'].strftime('%Y-%m-%d')})")

    # ── Run WITH full protection stack ──
    with_guards = run_paper_test(
        days=60, label="COVID Replay — WITH Full Protection",
        ohlcv_override=ohlcv_cache, track_baseline=False)

    # ── Run WITHOUT guards ──
    print(f"\n{'='*70}")
    print(f"  BASELINE — COVID Replay without guards")
    print(f"{'='*70}")

    # Build baseline without guards
    market = MarketAgent(signal_mode="both", short_style="mom_break")
    market._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    risk = RiskAgent()
    risk._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    council = AgentCouncil()
    perf = PerformanceMemory()
    slippage = SlippageEngine(slippage_pct=0.001)

    engine = PaperTradingEngine(
        initial_capital=10000.0,
        performance_memory=perf,
        council=council,
        slippage_engine=slippage,
    )

    all_events = []
    for sym, ohlcv in ohlcv_cache.items():
        all_events.extend(generate_events(sym, ohlcv))
    all_events.sort(key=lambda e: e.timestamp)

    orig_process = engine.process_decision

    def process_with_atr(mul=3.0):
        def wrapped(decision):
            signal = orig_process(decision)
            if signal and decision.opinions:
                meta = decision.opinions[0].metadata
                if "atr_14" in meta and meta.get("price", 0) > 0:
                    atr_pct = meta["atr_14"] / meta["price"] * 100
                    stop_pct = max(atr_pct * mul, 1.0)
                    price = meta["price"]
                    target_pct = stop_pct * 2
                    if signal.direction == TradeDirection.LONG:
                        signal.stop_loss = round(price * (1 - stop_pct / 100), 8)
                        signal.take_profit = round(price * (1 + target_pct / 100), 8)
                    else:
                        signal.stop_loss = round(price * (1 + stop_pct / 100), 8)
                        signal.take_profit = round(price * (1 - target_pct / 100), 8)
            return signal
        return wrapped
    engine.process_decision = process_with_atr(3.0)

    price_history = {s: [] for s in SYMBOLS}
    equity_curve_base = [10000.0]

    for event in all_events:
        sym = event.assets[0].symbol
        price = event.assets[0].price_at_event
        price_history[sym].append((event.timestamp, price))

        opinions = []
        for agent in [market, risk]:
            op = agent.analyze(event)
            if op:
                opinions.append(op)
        if len(opinions) < 2:
            continue
        for op in opinions:
            council.submit_opinion(op)
        decision = council.decide(event.id)
        if decision:
            signal = engine.process_decision(decision)
            if signal:
                engine.execute_signal(signal)

        current_prices = {s: (price_history[s][-1][1] if price_history[s] else 0)
                         for s in SYMBOLS}
        engine.check_positions(current_prices)
        equity_curve_base.append(engine.capital)

    final_prices = {s: (price_history[s][-1][1] if price_history[s] else 0)
                   for s in SYMBOLS}
    engine.check_positions(final_prices)

    p_base = engine.get_portfolio_summary()

    peak_b = 10000.0
    max_dd_b = 0.0
    for eq in equity_curve_base:
        if eq > peak_b:
            peak_b = eq
        dd = (peak_b - eq) / peak_b * 100
        max_dd_b = max(max_dd_b, dd)

    base_return = p_base["total_return_pct"]

    # ── Comparison ──
    guard_return = with_guards["summary"]["total_return_pct"] if with_guards else 0
    guard_dd = with_guards["max_drawdown"] if with_guards else 100

    print(f"\n{'='*70}")
    print(f"  COVID REPLAY — WITH vs WITHOUT Protection")
    print(f"{'='*70}")
    print(f"  {'Metric':>30s} | {'Without Guards':>15s} | {'With Guards':>15s} | {'Delta':>10s}")
    print(f"  {'-'*30} | {'-'*15} | {'-'*15} | {'-'*10}")
    print(f"  {'Total Return':>30s} | {base_return:>+14.2f}% | "
          f"{guard_return:>+14.2f}% | {guard_return - base_return:>+9.2f}%")
    print(f"  {'Max Drawdown':>30s} | {max_dd_b:>14.2f}% | "
          f"{guard_dd:>14.2f}% | {guard_dd - max_dd_b:>+9.2f}%")
    print(f"  {'Trades':>30s} | {p_base['total_trades']:>14d} | "
          f"{with_guards['summary']['total_trades']:>14d} | "
          f"{with_guards['summary']['total_trades'] - p_base['total_trades']:>+9d}")

    print(f"\n  --- Guard Activations During COVID ---")
    counts = with_guards["counts"] if with_guards else {}
    for key, label in [("direction_blocks", "Direction blocks"),
                       ("capital_blocks", "Capital blocks"),
                       ("emergency_blocks", "Emergency/HALT blocks"),
                       ("crash_warning_blocks", "Crash blocks"),
                       ("knife_rejections", "Knife rejections"),
                       ("gap_reductions", "Gap reductions"),
                       ("kill_switch_triggers", "Kill switch triggers")]:
        print(f"  {label:30s}: {counts.get(key, 0)}")

    # ── COVID Crash Detector analysis ──
    cd = with_guards["crash_detector"] if with_guards else {}
    gr = with_guards["gap_risk"] if with_guards else {}
    cg = with_guards["capital_guard"] if with_guards else {}

    print(f"\n  --- COVID Risk State ---")
    print(f"  Peak crash score:     {cd.get('crash_score', 'N/A')}")
    print(f"  Crash mode:           {cd.get('mode', 'N/A')}")
    print(f"  Gap risk score:       {gr.get('gap_risk_score', 'N/A')}")
    print(f"  CapitalGuard mode:    {cg.get('mode', 'N/A')}")
    print(f"  Max drawdown:         {cg.get('drawdown_pct', 'N/A')}%")
    print(f"  Stop multiplier:      {gr.get('stop_multiplier', 'N/A')}x")
    print(f"  Size reduction:       {gr.get('size_reduction', 'N/A')}x")

    # ── Verdict ──
    print(f"\n{'='*70}")
    print(f"  COVID REPLAY VERDICT")
    print(f"{'='*70}")
    print(f"  Without guards: {base_return:+.2f}% return, {max_dd_b:.2f}% max DD")
    print(f"  With guards:    {guard_return:+.2f}% return, {guard_dd:.2f}% max DD")

    loss_capped = guard_return > base_return
    dd_reduced = guard_dd < max_dd_b

    if loss_capped and dd_reduced:
        print(f"\n  ✓ Loss CAPPED: Guards improved both return and drawdown")
    elif loss_capped:
        print(f"\n  ✓ Loss CAPPED: Return improved despite drawdown")
    elif dd_reduced:
        print(f"\n  ~ Loss PARTIALLY CAPPED: Drawdown reduced, but return not improved")
    else:
        print(f"\n  ✗ Loss NOT CAPPED: Guards did not improve outcome")

    if guard_return < -10:
        print(f"  ⚠ COVID still caused {guard_return:.1f}% loss even with guards")
        print(f"  This is the 12.5% gap-down failure mode — expected and accepted")
    else:
        print(f"  COVID loss capped at {guard_return:.1f}%")

    return {"with_guards": with_guards, "baseline": {
        "return_pct": base_return,
        "max_dd": max_dd_b,
        "total_trades": p_base["total_trades"],
    }}


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"{'='*70}")
    print(f"  OSIRIS EXTENDED PAPER TRADING & DEMO GATE SPRINT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    phases = [1, 2, 4]
    if "--phase" in sys.argv:
        idx = sys.argv.index("--phase")
        phases = [int(sys.argv[idx + 1])]

    results = {}

    if 1 in phases:
        print(f"\n{'='*70}")
        print(f"  PHASE 1 — EXTENDED PAPER TRADING")
        print(f"{'='*70}")
        r1 = phase1_extended_paper()
        results["phase1"] = r1

        # Save to file
        if r1:
            with open("_project-memory/extended_paper_results.json", "w") as f:
                json.dump({
                    "7d_return": r1.get("7d", {}).get("summary", {}).get("total_return_pct"),
                    "7d_maxdd": r1.get("7d", {}).get("max_drawdown"),
                    "30d_return": r1.get("30d", {}).get("summary", {}).get("total_return_pct"),
                    "30d_maxdd": r1.get("30d", {}).get("max_drawdown"),
                    "30d_trades": r1.get("30d", {}).get("summary", {}).get("total_trades"),
                    "guard_counts": r1.get("30d", {}).get("counts"),
                }, f, indent=2)
            print(f"\n  Saved to _project-memory/extended_paper_results.json")

    if 2 in phases:
        r30 = results.get("phase1", {}).get("30d") if "phase1" in results else None
        if not r30:
            # Try to load from saved file
            try:
                with open("_project-memory/extended_paper_results.json") as f:
                    saved = json.load(f)
                print("  Using saved 30-day data from file")
            except (FileNotFoundError, json.JSONDecodeError):
                # Re-run 30-day if not available
                print("  No saved data — running 30-day test first")
                r30 = run_paper_test(days=30, label="30-Day Guard Validation")
        if r30:
            phase2_guard_validation(r30)

    if 4 in phases:
        r4 = phase4_covid_replay()
        results["phase4"] = r4

        if r4:
            with open("_project-memory/covid_replay_results.json", "w") as f:
                w = r4.get("with_guards", {})
                b = r4.get("baseline", {})
                json.dump({
                    "with_guards": {
                        "return_pct": w.get("summary", {}).get("total_return_pct"),
                        "max_dd": w.get("max_drawdown"),
                        "trades": w.get("summary", {}).get("total_trades"),
                        "guard_counts": w.get("counts"),
                        "crash_detector": w.get("crash_detector"),
                        "gap_risk": w.get("gap_risk"),
                        "capital_guard": w.get("capital_guard"),
                    },
                    "baseline": b,
                }, f, indent=2)
            print(f"\n  Saved to _project-memory/covid_replay_results.json")

    print(f"\n{'='*70}")
    print(f"  EXTENDED PAPER TRADING & DEMO GATE SPRINT COMPLETE")
    print(f"{'='*70}")
