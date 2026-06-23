"""OSIRIS Regime Robustness Sprint — Survive Bear, Sideways, High-Vol Markets
Usage: python scripts/regime_robustness.py [--phase 1] [--short-style rsi]
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
from core.execution.capital_guard import CapitalGuard

SYMBOLS = ["BTC", "ETH", "SOL"]
BNB_MAP = {"BTC":"BTCUSDT","ETH":"ETHUSDT","SOL":"SOLUSDT"}

# ── Historical regime periods ──────────────────────────────────────────
PERIODS = {
    "COVID_Crash": {
        "start": "2020-03-01T00:00:00Z",
        "end": "2020-04-30T23:59:59Z",
        "regime": "bear",
        "label": "COVID Crash (Mar-Apr 2020)",
    },
    "May21_Crash": {
        "start": "2021-04-20T00:00:00Z",
        "end": "2021-06-15T23:59:59Z",
        "regime": "bear",
        "label": "May 2021 Crash (Apr-Jun 2021)",
    },
    "Luna_Crash": {
        "start": "2022-04-15T00:00:00Z",
        "end": "2022-06-15T23:59:59Z",
        "regime": "bear",
        "label": "Luna/3AC Crash (Apr-Jun 2022)",
    },
    "FTX_Collapse": {
        "start": "2022-10-15T00:00:00Z",
        "end": "2022-12-15T23:59:59Z",
        "regime": "bear",
        "label": "FTX Collapse (Oct-Dec 2022)",
    },
    "PostFTX_Range": {
        "start": "2023-01-15T00:00:00Z",
        "end": "2023-03-30T23:59:59Z",
        "regime": "sideways",
        "label": "Post-FTX Range (Jan-Mar 2023)",
    },
    "Mid2023_Range": {
        "start": "2023-06-01T00:00:00Z",
        "end": "2023-08-31T23:59:59Z",
        "regime": "sideways",
        "label": "Mid-2023 Consolidation (Jun-Aug 2023)",
    },
    "Bull_2023Q4": {
        "start": "2023-10-01T00:00:00Z",
        "end": "2023-12-31T23:59:59Z",
        "regime": "bull",
        "label": "2023 Q4 Rally (Oct-Dec 2023)",
    },
}

# ── Data fetching ──────────────────────────────────────────────────────

def ms(dt_str):
    """ISO datetime string → milliseconds timestamp."""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)

def fetch_ohlcv_range(symbol: str, start_ms: int, end_ms: int, interval: str = "1h") -> Optional[List[Dict]]:
    """Fetch OHLCV data for a date range with forward pagination."""
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
            resp = req.get("https://api.binance.com/api/v3/klines", params=params, timeout=15)
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not batch:
                break
            for k in batch:
                candles.append({
                    "time": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
                    "time_raw": k[0],
                    "open": float(k[1]), "high": float(k[2]),
                    "low": float(k[3]), "close": float(k[4]),
                    "volume": float(k[5]),
                })
            if len(batch) < limit:
                break
            current_start = batch[-1][0] + 1
        except Exception as e:
            print(f"  [WARN] Fetch error {symbol}: {e}")
            break
    candles.sort(key=lambda c: c["time"])
    return candles if len(candles) >= 50 else None

def fetch_period(period_name: str, days_buffer: int = 5) -> Dict[str, Optional[List[Dict]]]:
    """Fetch OHLCV for all symbols in a period."""
    p = PERIODS[period_name]
    start_ms = ms(p["start"])
    end_ms = ms(p["end"])
    start_ms -= days_buffer * 24 * 3600 * 1000  # buffer for indicators

    # SOL only listed on Binance from Aug 2020
    sol_start = int(datetime(2020, 8, 1, tzinfo=timezone.utc).timestamp() * 1000)
    symbols = [s for s in SYMBOLS if s != "SOL" or start_ms >= sol_start]

    result = {}
    for sym in symbols:
        data = fetch_ohlcv_range(sym, start_ms, end_ms)
        if data and len(data) >= 50:
            result[sym] = data
    return result

# ── Event generation ──────────────────────────────────────────────────

def generate_events(symbol, ohlcv):
    events = []
    for i in range(1, len(ohlcv)):
        prev, curr = ohlcv[i-1], ohlcv[i]
        change = (curr["close"] - prev["close"]) / prev["close"]
        u = Urgency.HIGH if abs(change) > 0.05 else Urgency.MEDIUM if abs(change) > 0.02 else Urgency.LOW
        et = EventType.VOLUME_SPIKE if (abs(change) > 0.05 and curr["volume"] > prev["volume"] * 1.5) else EventType.PRICE_MOVEMENT
        events.append(Event(
            id=f"{symbol}_{i}", source="regime_test",
            event_type=et, title=f"{symbol} {change*100:+.2f}%",
            assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO, price_at_event=curr["close"])],
            timestamp=curr["time"], detected_at=curr["time"],
            urgency=u, sentiment_score=change, confidence=0.7,
        ))
    return events

# ── Run experiment ────────────────────────────────────────────────────

def run_experiment(period_name: str, short_style: str = "mom_break",
                   slippage_bps: int = 10, signal_mode: str = "both",
                   use_guards: bool = True,
                   ohlcv_override: Optional[Dict] = None) -> Optional[Dict]:
    """Run OSIRIS pipeline on a historical period with given config."""
    p = PERIODS[period_name]
    print(f"\n{'='*60}")
    print(f"  {p['label']} ({p['regime']})")
    print(f"  SHORT: {short_style}, Slippage: {slippage_bps}bps, Mode: {signal_mode}")
    print(f"{'='*60}")

    ohlcv_cache = ohlcv_override or fetch_period(period_name)
    if not ohlcv_cache or len(ohlcv_cache) < 1:
        print("  No data — skipping")
        return None

    for sym, data in ohlcv_cache.items():
        print(f"  {sym}: {len(data)} candles ({data[0]['time'].strftime('%Y-%m-%d')} -> {data[-1]['time'].strftime('%Y-%m-%d')})")

    market = MarketAgent(signal_mode=signal_mode, short_style=short_style)
    market._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    risk = RiskAgent()
    risk._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    council = AgentCouncil()
    perf = PerformanceMemory()
    slippage = SlippageEngine(slippage_pct=slippage_bps / 10000)

    if use_guards:
        direction_ctrl = DirectionController(window=20, wr_threshold=0.25, recovery_threshold=0.35)
        capital_guard = CapitalGuard(initial_capital=10000.0, max_daily_loss_pct=10.0,
                                     max_weekly_loss_pct=20.0, max_open_risk_pct=25.0)
    else:
        direction_ctrl = DirectionController(window=9999, wr_threshold=-0.01)  # never disable
        capital_guard = CapitalGuard(initial_capital=10000.0, max_daily_loss_pct=999,
                                     max_weekly_loss_pct=999, max_open_risk_pct=999)

    engine = PaperTradingEngine(
        initial_capital=10000.0,
        performance_memory=perf,
        council=council,
        slippage_engine=slippage,
        direction_controller=direction_ctrl,
        capital_guard=capital_guard,
    )

    all_events = []
    for sym, ohlcv in ohlcv_cache.items():
        all_events.extend(generate_events(sym, ohlcv))
    all_events.sort(key=lambda e: e.timestamp)
    print(f"  Events: {len(all_events)}")

    # Override stop sizing
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
    all_signals = []
    blocked_by_direction = 0

    start_time = time.time()
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
                all_signals.append(signal)
                engine.execute_signal(signal)

        current = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
        engine.check_positions(current)

    final = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
    engine.check_positions(final)
    elapsed = time.time() - start_time

    # Collect data
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

    # Max drawdown
    running_equity = 10000.0
    peak = 10000.0
    max_dd = 0.0
    for t in detailed_trades:
        running_equity += t["pnl_abs"]
        if running_equity > peak:
            peak = running_equity
        dd = (peak - running_equity) / peak * 100
        max_dd = max(max_dd, dd)

    # Direction breakdown
    by_dir = defaultdict(list)
    by_exit = defaultdict(int)
    for t in detailed_trades:
        by_dir[t["direction"]].append(t["pnl_pct"])
        by_exit[t["exit_reason"]] += 1

    # Per-asset breakdown
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
                "avg": mean(pnls) if pnls else 0,
                "wins": sum(1 for p in pnls if p > 0),
                "wr": sum(1 for p in pnls if p > 0) / len(pnls) * 100 if pnls else 0,
            }

    result = {
        "period": period_name,
        "regime": p["regime"],
        "label": p["label"],
        "config": {"short_style": short_style, "slippage_bps": slippage_bps, "signal_mode": signal_mode},
        "trades": detailed_trades,
        "summary": {
            "total_trades": portfolio["total_trades"],
            "win_rate": portfolio["win_rate"],
            "return_pct": portfolio["total_return_pct"],
            "sharpe": portfolio["sharpe_ratio"],
            "max_dd": round(max_dd, 2),
            "avg_pnl": portfolio["avg_pnl_pct"],
            "equity": portfolio["equity"],
            "total_pnl_abs": portfolio["total_pnl_abs"],
        },
        "direction_stats": {
            d: {
                "trades": len(pnls),
                "wins": sum(1 for p in pnls if p > 0),
                "wr": sum(1 for p in pnls if p > 0) / len(pnls) * 100 if pnls else 0,
                "total_pnl": sum(pnls),
                "avg_pnl": mean(pnls) if pnls else 0,
                "pf": abs(sum(p for p in pnls if p > 0) / sum(p for p in pnls if p < 0))
                      if any(p < 0 for p in pnls) and sum(p for p in pnls if p < 0) != 0 else float("inf"),
            }
            for d, pnls in by_dir.items()
        },
        "exit_reasons": dict(by_exit),
        "direction_ctrl_summary": direction_ctrl.summary(),
        "elapsed_sec": round(elapsed, 1),
    }
    return result

# ── Phase 1: Bear Market Validation ────────────────────────────────────

def phase1_bear():
    """Run on all bear periods and summarize."""
    bear_periods = [k for k, v in PERIODS.items() if v["regime"] == "bear"]
    results = {}

    for pname in bear_periods:
        r = run_experiment(pname, short_style="mom_break")
        if r:
            results[pname] = r
        print()  # spacing

    print(f"\n{'='*70}")
    print(f"  PHASE 1 — BEAR MARKET VALIDATION")
    print(f"{'='*70}")
    print(f"  {'Period':>30s} | {'Trades':>6s} | {'WR':>6s} | {'Return':>10s} | {'Sharpe':>7s} | {'MaxDD':>7s} | {'AvgPnL':>7s}")
    print(f"  {'-'*30} | {'-'*6} | {'-'*6} | {'-'*10} | {'-'*7} | {'-'*7} | {'-'*7}")
    for pname in bear_periods:
        r = results.get(pname)
        if not r:
            continue
        s = r["summary"]
        print(f"  {r['label']:>30s} | {s['total_trades']:>6d} | {s['win_rate']:>5.1f}% | {s['return_pct']:>+9.2f}% | {s['sharpe']:>7.2f} | {s['max_dd']:>6.2f}% | {s['avg_pnl']:>+6.2f}%")

    print(f"\n  --- Direction Breakdown ---")
    for pname in bear_periods:
        r = results.get(pname)
        if not r:
            continue
        ds = r.get("direction_stats", {})
        for d in ("long", "short"):
            stats = ds.get(d, {})
            if stats.get("trades", 0) > 0:
                print(f"  {r['label']:>30s} | {d:>6s}: {stats['trades']:4d} trades, "
                      f"WR={stats['wr']:5.1f}%, PnL={stats['total_pnl']:+.2f}%, "
                      f"PF={stats.get('pf', 0):.2f}")

    print(f"\n  --- Per-Asset (Luna/3AC example) ---")
    luna = results.get("Luna_Crash", {})
    if luna:
        for asset, dirs in luna.get("asset_stats", {}).items():
            for d, stats in dirs.items():
                print(f"  {asset:4s} {d:>6s}: {stats['trades']:4d} trades, "
                      f"WR={stats['wr']:5.1f}%, PnL={stats['pnl']:+.2f}%")

    survivors = sum(1 for r in results.values() if r["summary"]["return_pct"] > 0 and r["summary"]["max_dd"] < 50)
    print(f"\n  Bear survival: {survivors}/{len(bear_periods)} periods")
    if survivors == len(bear_periods):
        print(f"  VERDICT: OSIRIS survives bear markets ✓")
    elif survivors >= len(bear_periods) / 2:
        print(f"  VERDICT: Partial bear survival — investigate failing periods")
    else:
        print(f"  VERDICT: OSIRIS FAILS in bear markets ✗")

    return results

# ── Phase 2: Sideways Market Validation ────────────────────────────────

def phase2_sideways():
    """Run on sideways periods."""
    side_periods = [k for k, v in PERIODS.items() if v["regime"] == "sideways"]
    results = {}

    for pname in side_periods:
        r = run_experiment(pname, short_style="mom_break")
        if r:
            results[pname] = r

    print(f"\n{'='*70}")
    print(f"  PHASE 2 — SIDEWAYS MARKET VALIDATION")
    print(f"{'='*70}")
    print(f"  {'Period':>30s} | {'Trades':>6s} | {'WR':>6s} | {'Return':>10s} | {'Sharpe':>7s} | {'MaxDD':>7s} | {'AvgPnL':>7s}")
    print(f"  {'-'*30} | {'-'*6} | {'-'*6} | {'-'*10} | {'-'*7} | {'-'*7} | {'-'*7}")
    for pname in side_periods:
        r = results.get(pname)
        if not r:
            continue
        s = r["summary"]
        print(f"  {r['label']:>30s} | {s['total_trades']:>6d} | {s['win_rate']:>5.1f}% | {s['return_pct']:>+9.2f}% | {s['sharpe']:>7.2f} | {s['max_dd']:>6.2f}% | {s['avg_pnl']:>+6.2f}%")

    survivors = sum(1 for r in results.values() if r["summary"]["return_pct"] > 0 and r["summary"]["max_dd"] < 50)
    print(f"\n  Sideways survival: {survivors}/{len(side_periods)} periods")
    if survivors == len(side_periods):
        print(f"  VERDICT: Alpha survives sideways markets ✓")
    elif survivors >= len(side_periods) / 2:
        print(f"  VERDICT: Partial sideways survival")
    else:
        print(f"  VERDICT: Alpha disappears in sideways markets ✗")

    return results

# ── Phase 3: Volatility Regime Testing ─────────────────────────────────

def phase3_volatility(bear_results: Dict, side_results: Dict, bull_result: Optional[Dict]):
    """Classify trades by volatility regime at entry time."""
    all_results = {}
    all_results.update(bear_results)
    all_results.update(side_results)
    if bull_result:
        all_results["Bull_2023Q4"] = bull_result

    print(f"\n{'='*70}")
    print(f"  PHASE 3 — VOLATILITY REGIME TESTING")
    print(f"{'='*70}")

    # Collect all trades with volatility classification
    high_vol_trades = []
    low_vol_trades = []
    normal_vol_trades = []

    for pname, r in all_results.items():
        trades = r["trades"]
        ohlcv = {}  # we'll refetch if needed, or use trade metadata

        for t in trades:
            vol = t.get("volatility", 0.05)  # default to normal
            # Classify by volatility > 0.05 (high), < 0.02 (low)
            if t["holding_hours"] > 0 and t.get("pnl_pct") is not None:
                # Use time-based vol classification from experiment data
                if t.get("conviction", 0) > 0:
                    pass  # use direction from trade data
            direction = t["direction"]
            pnl = t["pnl_pct"]

            # Approximate vol from entry/exit price swing
            entry = t["entry_price"]
            stop = t["stop_loss"]
            if entry > 0:
                stop_dist = abs(entry - stop) / entry
                if stop_dist > 0.03:  # wide stop = high vol
                    high_vol_trades.append((direction, pnl))
                elif stop_dist < 0.015:  # tight stop = low vol
                    low_vol_trades.append((direction, pnl))
                else:
                    normal_vol_trades.append((direction, pnl))

    def print_vol_stats(label, trades):
        if not trades:
            print(f"  {label:12s}: 0 trades")
            return
        longs = [p for d, p in trades if d == "long"]
        shorts = [p for d, p in trades if d == "short"]
        all_pnls = [p for _, p in trades]
        n = len(all_pnls)
        wins = sum(1 for p in all_pnls if p > 0)
        total_pnl = sum(all_pnls)
        print(f"  {label:12s}: {n:4d} trades, WR={wins/n*100:5.1f}%, PnL={total_pnl:+.2f}%, "
              f"LONG={len(longs)}/SHORT={len(shorts)}")

    print_vol_stats("High Vol", high_vol_trades)
    print_vol_stats("Normal Vol", normal_vol_trades)
    print_vol_stats("Low Vol", low_vol_trades)

    return {"high_vol": high_vol_trades, "normal_vol": normal_vol_trades, "low_vol": low_vol_trades}

# ── Phase 4: SHORT Replacement A/B ─────────────────────────────────────

# ── Data cache for reproducibility ────────────────────────────────────
DATA_CACHE = {}

def get_cached_period(period_name):
    """Fetch and cache OHLCV data for a period."""
    if period_name not in DATA_CACHE:
        DATA_CACHE[period_name] = fetch_period(period_name)
    return DATA_CACHE[period_name]

def run_experiment_cached(period_name: str, short_style: str = "mom_break",
                          slippage_bps: int = 10, signal_mode: str = "both",
                          use_guards: bool = True) -> Optional[Dict]:
    """Like run_experiment but uses cached data for reproducibility."""
    ohlcv_cache = get_cached_period(period_name)
    return run_experiment(period_name, short_style=short_style,
                          slippage_bps=slippage_bps, signal_mode=signal_mode,
                          use_guards=use_guards, ohlcv_override=ohlcv_cache)

def phase4_ab_short():
    """A/B compare RSI vs MomentumBreakdown SHORT using cached data."""
    test_periods = [k for k, v in PERIODS.items() if v["regime"] in ("bear", "sideways")]
    styles = ["rsi", "mom_break"]
    results = {}

    for pname in test_periods:
        cache = get_cached_period(pname)
        for style in styles:
            key = f"{pname}_{style}"
            print(f"\n  ─── {PERIODS[pname]['label']} | SHORT: {style} ───")
            r = run_experiment(pname, short_style=style, ohlcv_override=cache)
            if r:
                results[key] = r

    print(f"\n{'='*70}")
    print(f"  PHASE 4 — SHORT REPLACEMENT A/B")
    print(f"{'='*70}")
    print(f"  {'Period':>30s} | {'Style':>12s} | {'Trades':>6s} | {'Long':>5s} | {'Short':>5s} | {'WR':>6s} | {'Return':>10s} | {'Sharpe':>7s} | {'MaxDD':>7s}")
    print(f"  {'-'*30} | {'-'*12} | {'-'*6} | {'-'*5} | {'-'*5} | {'-'*6} | {'-'*10} | {'-'*7} | {'-'*7}")

    for pname in test_periods:
        for style in styles:
            key = f"{pname}_{style}"
            r = results.get(key)
            if not r:
                continue
            s = r["summary"]
            ds = r.get("direction_stats", {})
            l_trades = ds.get("long", {}).get("trades", 0)
            s_trades = ds.get("short", {}).get("trades", 0)
            print(f"  {r['label']:>30s} | {style:>12s} | {s['total_trades']:>6d} | {l_trades:>5d} | {s_trades:>5d} | {s['win_rate']:>5.1f}% | {s['return_pct']:>+9.2f}% | {s['sharpe']:>7.2f} | {s['max_dd']:>6.2f}%")

    # Determine winner
    print(f"\n  --- Winner Analysis ---")
    mom_break_ret = mean([results[f"{p}_{'mom_break'}"]["summary"]["return_pct"]
                         for p in test_periods if f"{p}_mom_break" in results] or [0])
    rsi_ret = mean([results[f"{p}_{'rsi'}"]["summary"]["return_pct"]
                   for p in test_periods if f"{p}_rsi" in results] or [0])
    print(f"  Avg return: MomBreak={mom_break_ret:+.2f}%, RSI={rsi_ret:+.2f}%")
    if mom_break_ret > rsi_ret:
        print(f"  WINNER: MomentumBreakdown SHORT (default now)")
    else:
        print(f"  WINNER: RSI>70 SHORT (keeping original)")

    return results

# ── Phase 5: Direction Controller Validation ──────────────────────────

def phase5_direction_ctrl():
    """Stress-test LONG_ONLY/SHORT_ONLY/BOTH across regimes (cached data)."""
    test_modes = ["both", "long_only", "short_only"]
    test_periods = [k for k, v in PERIODS.items() if v["regime"] in ("bear", "sideways")]
    results = {}

    for pname in test_periods:
        cache = get_cached_period(pname)
        for mode in test_modes:
            key = f"{pname}_{mode}"
            r = run_experiment(pname, short_style="mom_break", signal_mode=mode,
                               ohlcv_override=cache)
            if r:
                results[key] = r

    print(f"\n{'='*70}")
    print(f"  PHASE 5 — DIRECTION CONTROLLER VALIDATION")
    print(f"{'='*70}")
    print(f"  {'Period':>30s} | {'Mode':>12s} | {'Trades':>6s} | {'WR':>6s} | {'Return':>10s} | {'Sharpe':>7s} | {'MaxDD':>7s} | {'AvgPnL':>7s}")
    print(f"  {'-'*30} | {'-'*12} | {'-'*6} | {'-'*6} | {'-'*10} | {'-'*7} | {'-'*7} | {'-'*7}")

    for pname in test_periods:
        for mode in test_modes:
            key = f"{pname}_{mode}"
            r = results.get(key)
            if not r:
                continue
            s = r["summary"]
            print(f"  {r['label']:>30s} | {mode:>12s} | {s['total_trades']:>6d} | {s['win_rate']:>5.1f}% | {s['return_pct']:>+9.2f}% | {s['sharpe']:>7.2f} | {s['max_dd']:>6.2f}% | {s['avg_pnl']:>+6.2f}%")

    print(f"\n  --- Best Mode Per Regime ---")
    for pname in test_periods:
        best_mode = max(test_modes, key=lambda m: results.get(f"{pname}_{m}", {}).get("summary", {}).get("return_pct", -999))
        best_ret = results.get(f"{pname}_{best_mode}", {}).get("summary", {}).get("return_pct", 0)
        print(f"  {PERIODS[pname]['label']:>30s}: best={best_mode:>12s} ({best_ret:+.2f}%)")

    return results

# ── Phase 6: Failure Analysis ─────────────────────────────────────────

def phase6_failure(bear_results: Dict):
    """Find worst 50 trades and classify root cause."""
    all_trades = []
    for pname, r in bear_results.items():
        for t in r.get("trades", []):
            all_trades.append({**t, "period": pname, "regime": r["regime"]})

    all_trades.sort(key=lambda t: t["pnl_pct"])
    worst = all_trades[:50]

    print(f"\n{'='*70}")
    print(f"  PHASE 6 — FAILURE ANALYSIS (Worst {len(worst)} Trades)")
    print(f"{'='*70}")

    # Classify each trade
    classifications = defaultdict(list)
    for t in worst:
        dir_ = t["direction"]
        regime = t.get("regime", "unknown")
        price_change = abs(t["pnl_pct"])
        holding = t.get("holding_hours", 0)

        # Determine root cause
        if dir_ == "short" and regime in ("bull", "sideways"):
            cause = "Wrong direction (SHORT in wrong regime)"
        elif dir_ == "long" and regime == "bear":
            cause = "Wrong direction (LONG in bear)"
        elif holding < 2:
            cause = "Stop too tight / immediate reversal"
        elif holding < 6:
            cause = "Late entry — stopped out quickly"
        elif price_change > 5:
            cause = "Market regime mismatch (gap move)"
        elif t["exit_reason"] == "stop_loss":
            cause = "Stop loss hit (normal loss)"
        else:
            cause = "Unknown"

        classifications[cause].append(t)

    # Print classification summary
    print(f"  {'Root Cause':>45s} | {'Count':>5s} | {'Avg Loss':>9s} | {'Avg Hold':>8s}")
    print(f"  {'-'*45} | {'-'*5} | {'-'*9} | {'-'*8}")
    for cause, trades in sorted(classifications.items(), key=lambda x: -len(x[1])):
        avg_loss = mean(t["pnl_pct"] for t in trades)
        avg_hold = mean(t.get("holding_hours", 0) for t in trades)
        print(f"  {cause:>45s} | {len(trades):>5d} | {avg_loss:>+8.2f}% | {avg_hold:>7.1f}h")

    print(f"\n  Total worst trades: {len(worst)}")
    print(f"  Top 5 worst single trades:")
    for t in worst[:5]:
        print(f"    {t['pnl_pct']:+.2f}% | {t['direction']:6s} | {t.get('asset', '?'):4s} | "
              f"{t.get('exit_reason', '?'):15s} | holding={t.get('holding_hours', 0):.1f}h | "
              f"{t.get('period', '?'):15s} | conviction={t.get('conviction', 0):.0f}")

    return classifications

# ── Phase 7: Demo Readiness Assessment ─────────────────────────────────

def phase7_demo_readiness(all_results: Dict):
    """Compute survival probability across regimes."""
    print(f"\n{'='*70}")
    print(f"  PHASE 7 — DEMO READINESS ASSESSMENT")
    print(f"{'='*70}")

    regimes = defaultdict(list)
    for pname, r in all_results.items():
        if isinstance(r, dict) and "summary" in r:
            regimes[r.get("regime", "unknown")].append(r)

    print(f"\n  --- Per-Regime Performance ---")
    print(f"  {'Regime':>12s} | {'Periods':>7s} | {'Avg Return':>10s} | {'Avg WR':>6s} | {'Avg Sharpe':>10s} | {'Avg MaxDD':>9s} | {'Survival Rate':>13s}")
    print(f"  {'-'*12} | {'-'*7} | {'-'*10} | {'-'*6} | {'-'*10} | {'-'*9} | {'-'*13}")

    total_prob = 0
    regime_count = 0
    for regime, results_list in sorted(regimes.items()):
        n = len(results_list)
        avg_ret = mean(r["summary"]["return_pct"] for r in results_list)
        avg_wr = mean(r["summary"]["win_rate"] for r in results_list)
        avg_sharpe = mean(r["summary"]["sharpe"] for r in results_list)
        avg_dd = mean(r["summary"]["max_dd"] for r in results_list)
        survivors = sum(1 for r in results_list if r["summary"]["return_pct"] > 0)
        survival_rate = survivors / n * 100

        print(f"  {regime:>12s} | {n:>7d} | {avg_ret:>+9.2f}% | {avg_wr:>5.1f}% | {avg_sharpe:>10.2f} | {avg_dd:>8.2f}% | {survival_rate:>12.0f}%")

        # Per-regime survival probability
        if regime == "bear":
            bear_prob = survival_rate / 100
        elif regime == "sideways":
            side_prob = survival_rate / 100
        elif regime == "bull":
            bull_prob = survival_rate / 100

    # Overall probability
    prob_profitable = mean([
        regimes.get("bear", [{}])[0]["summary"]["return_pct"] > 0 if regimes.get("bear") else 0,
        regimes.get("sideways", [{}])[0]["summary"]["return_pct"] > 0 if regimes.get("sideways") else 0,
        regimes.get("bull", [{}])[0]["summary"]["return_pct"] > 0 if regimes.get("bull") else 0,
    ]) * 100

    all_regime_results = [r for lst in regimes.values() for r in lst]
    if all_regime_results:
        prob_breakeven = mean([
            max(-r["summary"]["return_pct"] / 100 + 0.5, 0) if r["summary"]["return_pct"] < 0 else 1.0
            for r in all_regime_results
        ]) * 100
        prob_failure = 100 - prob_profitable
    else:
        prob_breakeven = 0
        prob_failure = 100

    print(f"\n  --- Demo Readiness (Tier 2) ---")
    print(f"  Probability of profitability: {prob_profitable:.0f}%")
    print(f"  Probability of break-even:    {prob_breakeven:.0f}%")
    print(f"  Probability of failure:       {prob_failure:.0f}%")
    print(f"")
    if prob_profitable > 70:
        print(f"  VERDICT: DEMO READY ✓ ({prob_profitable:.0f}% survival across regimes)")
    elif prob_profitable > 40:
        print(f"  VERDICT: CONDITIONALLY READY ({prob_profitable:.0f}% — need SHORT fix)")
    else:
        print(f"  VERDICT: NOT DEMO READY ✗ ({prob_profitable:.0f}% — fails in too many regimes)")

    return {
        "prob_profitable": round(prob_profitable, 1),
        "prob_breakeven": round(prob_breakeven, 1),
        "prob_failure": round(prob_failure, 1),
    }

# ── Main ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"{'='*70}")
    print(f"  OSIRIS REGIME ROBUSTNESS SPRINT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    # Determine which phases to run
    phases = [1, 2, 3, 4, 5, 6, 7]
    if "--phase" in sys.argv:
        idx = sys.argv.index("--phase")
        phases = [int(sys.argv[idx + 1])]

    all_results = {}

    if 1 in phases:
        print(f"\n{'='*70}")
        print(f"  PHASE 1 — BEAR MARKET VALIDATION")
        print(f"{'='*70}")
        bear_results = phase1_bear()
        all_results.update(bear_results)

    if 2 in phases:
        print(f"\n{'='*70}")
        print(f"  PHASE 2 — SIDEWAYS MARKET VALIDATION")
        print(f"{'='*70}")
        side_results = phase2_sideways()
        all_results.update(side_results)

    if 3 in phases:
        # Phase 3 needs data from phases 1 and 2
        bear_r = {k: v for k, v in all_results.items() if v and v.get("regime") == "bear"}
        side_r = {k: v for k, v in all_results.items() if v and v.get("regime") == "sideways"}
        bull_r = all_results.get("Bull_2023Q4")
        phase3_volatility(bear_r, side_r, bull_r)

    if 4 in phases:
        ab_results = phase4_ab_short()
        all_results.update(ab_results)

    if 5 in phases:
        dc_results = phase5_direction_ctrl()
        all_results.update(dc_results)

    if 6 in phases:
        bear_only = {k: v for k, v in all_results.items() if v and v.get("regime") == "bear"}
        phase6_failure(bear_only)
        # Also analyze all losing trades
        all_trades = []
        for pname, r in all_results.items():
            if isinstance(r, dict) and "trades" in r:
                for t in r["trades"]:
                    all_trades.append({**t, "period": pname, "regime": r.get("regime", "?")})
        all_trades.sort(key=lambda t: t.get("pnl_pct", 0))
        worst_all = all_trades[:max(50, len(all_trades) // 10)]
        if worst_all:
            print(f"\n  --- Additional: Worst {len(worst_all)} across ALL regimes ---")
            phase6_failure({"_all": {"regime": "all", "trades": worst_all}})

    if 7 in phases:
        phase7_demo_readiness(all_results)

    print(f"\n{'='*70}")
    print(f"  REGIME ROBUSTNESS SPRINT COMPLETE")
    print(f"{'='*70}")
