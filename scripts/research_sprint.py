"""OSIRIS Research Sprint — Alpha Stability & Regime Analysis
Usage: python scripts/research_sprint.py
"""
import sys, json, time, math
sys.path.insert(0, ".")
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from statistics import mean, stdev, StatisticsError
from math import sqrt

import requests as req

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Urgency
from core.schemas.agent_schema import AgentOpinion, AgentRole, Recommendation
from core.schemas.trade_schema import TradeDirection, Trade, ExitReason
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory

SYMBOLS = ["BTC", "ETH", "SOL"]
BNB_MAP = {"BTC":"BTCUSDT","ETH":"ETHUSDT","SOL":"SOLUSDT","XRP":"XRPUSDT","BNB":"BNBUSDT"}

# ── Paginated OHLCV fetch ─────────────────────────────────────────────────

def fetch_ohlcv_bulk(symbol, days, interval="1h"):
    """Fetch OHLCV with pagination for any timeframe."""
    limit = 1000
    if days <= 40:
        return fetch_ohlcv_simple(symbol, days, interval)

    pair = BNB_MAP.get(symbol)
    if not pair:
        return None

    hours_needed = days * 24
    candles = []
    end_time = int(time.time() * 1000)

    while len(candles) < hours_needed:
        params = {"symbol": pair, "interval": interval, "limit": limit}
        if candles:
            params["endTime"] = candles[-1]["time_raw"] - 1
        else:
            params["endTime"] = end_time

        try:
            resp = req.get("https://api.binance.com/api/v3/klines", params=params, timeout=15)
            if resp.status_code != 200:
                print(f"  [WARN] Binance fetch error {symbol}: {resp.status_code}")
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
        except Exception as e:
            print(f"  [WARN] Binance fetch error {symbol}: {e}")
            break

    candles.sort(key=lambda c: c["time"])

    if len(candles) < 50:
        print(f"  [WARN] Only {len(candles)} candles for {symbol}, trying yfinance")
        return fetch_ohlcv_yfinance(symbol, days)

    return candles

def fetch_ohlcv_simple(symbol, days, interval="1h"):
    """Single-request fetch for short timeframes."""
    pair = BNB_MAP.get(symbol)
    if pair:
        try:
            resp = req.get("https://api.binance.com/api/v3/klines",
                params={"symbol": pair, "interval": interval, "limit": min(days * 24, 1000)}, timeout=15)
            if resp.status_code == 200:
                return [
                    {"time": datetime.fromtimestamp(k[0]/1000, tz=timezone.utc),
                     "open": float(k[1]), "high": float(k[2]), "low": float(k[3]),
                     "close": float(k[4]), "volume": float(k[5])}
                    for k in resp.json()
                ]
        except Exception:
            pass
    return fetch_ohlcv_yfinance(symbol, days)

def fetch_ohlcv_yfinance(symbol, days):
    """Fallback via yfinance."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{days}d", interval="1h")
        if not hist.empty:
            return [
                {"time": idx.to_pydatetime().replace(tzinfo=timezone.utc) if idx.tzinfo is None else idx.to_pydatetime(),
                 "open": float(r["Open"]), "high": float(r["High"]),
                 "low": float(r["Low"]), "close": float(r["Close"]),
                 "volume": float(r["Volume"])}
                for idx, r in hist.iterrows()
            ]
    except Exception:
        pass
    return None

# ── Event generation ──────────────────────────────────────────────────────

def generate_events(symbol, ohlcv):
    events = []
    for i in range(1, len(ohlcv)):
        prev, curr = ohlcv[i-1], ohlcv[i]
        change = (curr["close"] - prev["close"]) / prev["close"]
        u = Urgency.HIGH if abs(change) > 0.05 else Urgency.MEDIUM if abs(change) > 0.02 else Urgency.LOW
        et = EventType.VOLUME_SPIKE if (abs(change) > 0.05 and curr["volume"] > prev["volume"] * 1.5) else EventType.PRICE_MOVEMENT
        events.append(Event(
            id=f"{symbol}_{i}", source="research",
            event_type=et, title=f"{symbol} {change*100:+.2f}%",
            assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO, price_at_event=curr["close"])],
            timestamp=curr["time"], detected_at=curr["time"],
            urgency=u, sentiment_score=change, confidence=0.7,
        ))
    return events

# ── Run experiment with detailed trade capture ────────────────────────────

def run_research_experiment(days, atr_multiplier=3.0, signal_mode="both"):
    """Run OSIRIS pipeline and return detailed per-trade data."""
    print(f"\n{'='*60}")
    print(f"  Running {days}-day experiment (ATR×{atr_multiplier}, {signal_mode})")
    print(f"{'='*60}")
    start = time.time()

    ohlcv_cache = {}
    for sym in SYMBOLS:
        data = fetch_ohlcv_bulk(sym, days + 5)
        if data and len(data) >= 50:
            ohlcv_cache[sym] = data
            print(f"  {sym}: {len(data)} candles ({data[0]['time'].strftime('%Y-%m-%d')} → {data[-1]['time'].strftime('%Y-%m-%d')})")
        else:
            print(f"  {sym}: FAILED ({len(data) if data else 0} candles)")

    market = MarketAgent(signal_mode=signal_mode)
    market._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    risk = RiskAgent()
    risk._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    council = AgentCouncil()
    perf = PerformanceMemory()
    engine = PaperTradingEngine(initial_capital=10000.0, performance_memory=perf, council=council)

    all_events = []
    for sym, ohlcv in ohlcv_cache.items():
        all_events.extend(generate_events(sym, ohlcv))
    all_events.sort(key=lambda e: e.timestamp)
    print(f"  Events: {len(all_events)}")

    # Override stop sizing
    orig_process = engine.process_decision
    def process_with_atr(atr_mul):
        def wrapped(decision):
            signal = orig_process(decision)
            if signal and decision.opinions:
                meta = decision.opinions[0].metadata
                if "atr_14" in meta and meta.get("price", 0) > 0:
                    atr_pct = meta["atr_14"] / meta["price"] * 100
                    stop_pct = max(atr_pct * atr_mul, 1.0)
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
    engine.process_decision = process_with_atr(atr_multiplier)

    price_history = {s: [] for s in SYMBOLS}
    all_decisions = []
    all_signals = []
    all_trades_data = []

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
            all_decisions.append(decision)

        signal = engine.process_decision(decision)
        if signal:
            all_signals.append(signal)
            engine.execute_signal(signal)

        current = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
        engine.check_positions(current)

    # Close remaining positions
    final = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
    engine.check_positions(final)

    elapsed = time.time() - start

    # Collect detailed per-trade data
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

    # Collect agent opinion data per decision (for conviction validation + attribution)
    opinion_data = []
    for i, d in enumerate(all_decisions):
        for op in d.opinions:
            opinion_data.append({
                "event_id": d.event_id,
                "agent": op.agent_name,
                "recommendation": op.recommendation.value,
                "confidence": op.confidence,
                "conviction": d.conviction,
                "timestamp": None,
            })

    portfolio = engine.get_portfolio_summary()

    # Compute max drawdown from cumulative PnL absolute (accounts for position sizing)
    equity_curve = []
    running_equity = 10000.0
    peak = 10000.0
    max_dd = 0.0
    for t in detailed_trades:
        running_equity += t["pnl_abs"]
        equity_curve.append(running_equity)
        if running_equity > peak:
            peak = running_equity
        dd = (peak - running_equity) / peak * 100
        max_dd = max(max_dd, dd)

    # Aggregate by timeframe segment (split data into thirds)
    n = len(detailed_trades)
    segment_size = max(1, n // 3)
    segments = []
    for s in range(0, n, segment_size):
        seg = detailed_trades[s:s+segment_size]
        if seg:
            seg_pnls = [t["pnl_pct"] for t in seg]
            seg_wins = sum(1 for p in seg_pnls if p > 0)
            seg_total = len(seg_pnls)
            segments.append({
                "trades": seg_total,
                "wins": seg_wins,
                "pnl": sum(seg_pnls),
                "avg": mean(seg_pnls),
            })

    return {
        "config": {"days": days, "atr_multiplier": atr_multiplier, "signal_mode": signal_mode},
        "summary": {
            "trades": portfolio["total_trades"],
            "win_rate": portfolio["win_rate"],
            "return_pct": portfolio["total_return_pct"],
            "sharpe": portfolio["sharpe_ratio"],
            "equity": portfolio["equity"],
            "max_drawdown_pct": round(max_dd, 2),
            "avg_pnl": portfolio["avg_pnl_pct"],
            "total_pnl_abs": portfolio["total_pnl_abs"],
            "elapsed_sec": round(elapsed, 1),
            "initial_capital": 10000.0,
        },
        "trades": detailed_trades,
        "opinions": opinion_data,
        "segments": segments,
        "agent_stats": {n: s for n, s in engine.performance._agent_records.items()},
        "ohlcv": ohlcv_cache,
    }

# ── Phase 1: Robustness Testing ───────────────────────────────────────────

def phase1_robustness(results):
    """Test alpha persistence across timeframes."""
    print(f"\n{'='*60}")
    print(f"  PHASE 1 — ROBUSTNESS TESTING")
    print(f"{'='*60}")
    print(f"  {'Days':>5s} | {'Trades':>6s} | {'WR':>6s} | {'Return':>9s} | {'Sharpe':>7s} | {'MaxDD':>7s} | {'AvgPnL':>7s} | {'Equity':>10s} | {'Expectancy':>10s}")
    print(f"  {'-'*5} | {'-'*6} | {'-'*6} | {'-'*9} | {'-'*7} | {'-'*7} | {'-'*7} | {'-'*10} | {'-'*10}")

    for days in sorted(results.keys(), key=int):
        r = results[days]
        s = r["summary"]
        pnls = [t["pnl_pct"] for t in r["trades"]]
        expectancy = mean(pnls) if pnls else 0
        print(f"  {days:>5d} | {s['trades']:>6d} | {s['win_rate']:>5.1f}% | {s['return_pct']:>+8.2f}% | {s['sharpe']:>7.2f} | {s['max_drawdown_pct']:>6.2f}% | {s['avg_pnl']:>+6.2f}% | ${s['equity']:>8,.2f} | {expectancy:>+8.2f}%")

    # Persistence analysis
    print(f"\n  --- Persistence Analysis ---")
    sorted_days = sorted(results.keys(), key=int)
    if len(sorted_days) >= 2:
        first_ret = results[sorted_days[0]]["summary"]["return_pct"]
        last_ret = results[sorted_days[-1]]["summary"]["return_pct"]
        first_wr = results[sorted_days[0]]["summary"]["win_rate"]
        last_wr = results[sorted_days[-1]]["summary"]["win_rate"]

        print(f"  Shortest ({sorted_days[0]}d) → Longest ({sorted_days[-1]}d):")
        print(f"    Return persistence:  {first_ret:+.2f}% → {last_ret:+.2f}%")
        print(f"    WR persistence:      {first_wr:.1f}% → {last_wr:.1f}%")

        if last_ret > 0:
            print(f"    VERDICT: Alpha persists across {sorted_days[-1]} days ✓")
        else:
            print(f"    VERDICT: Alpha decays beyond {sorted_days[-1]} days ✗")

        # Check if all returns are positive
        all_positive = all(results[d]["summary"]["return_pct"] > 0 for d in sorted_days)
        all_wr_above_50 = all(results[d]["summary"]["win_rate"] > 50 for d in sorted_days)
        print(f"    All timeframes positive: {'YES ✓' if all_positive else 'NO ✗'}")
        print(f"    All timeframes WR>50%:  {'YES ✓' if all_wr_above_50 else 'NO ✗'}")

# ── Phase 2: Market Regime Analysis ────────────────────────────────────────

def phase2_regime_analysis(results):
    """Classify markets and measure per-regime performance."""
    print(f"\n{'='*60}")
    print(f"  PHASE 2 — MARKET REGIME ANALYSIS")
    print(f"{'='*60}")

    # Use the longest timeframe for regime classification
    longest = max(results.keys(), key=int)
    r = results[longest]
    ohlcv = r.get("ohlcv", {})
    trades = r["trades"]

    if not ohlcv or not trades:
        print("  No data for regime analysis")
        return

    # Classify regime for each trade based on market conditions at entry
    # We use BTC as the market proxy
    btc_ohlcv = ohlcv.get("BTC", [])
    if not btc_ohlcv:
        print("  No BTC data for regime classification")
        return

    # Pre-compute daily regime for each day in the dataset
    def compute_regime_at_time(timestamp_str, ohlcv):
        ts = datetime.fromisoformat(timestamp_str)
        # Find candles around this time
        relevant = [c for c in ohlcv if c["time"] <= ts]
        if len(relevant) < 50:
            return "unknown"

        closes = [c["close"] for c in relevant[-60:]]
        highs = [c["high"] for c in relevant[-60:]]
        lows = [c["low"] for c in relevant[-60:]]

        sma_20 = mean(closes[-20:])
        sma_50 = mean(closes[-50:]) if len(closes) >= 50 else sma_20
        price = closes[-1]

        # Trend classification
        if sma_20 > sma_50 * 1.03 and price > sma_20:
            trend = "bull"
        elif sma_20 < sma_50 * 0.97 and price < sma_20:
            trend = "bear"
        else:
            trend = "sideways"

        # Volatility classification
        daily_ranges = [(highs[i] - lows[i]) / lows[i] * 100 for i in range(-20, 0)]
        avg_range = mean(daily_ranges) if daily_ranges else 0
        long_avg_range = mean([(highs[i] - lows[i]) / lows[i] * 100 for i in range(-60, 0)]) if len(closes) >= 60 else avg_range

        if avg_range > long_avg_range * 1.5 or avg_range > 3.0:
            vol = "high"
        elif avg_range < long_avg_range * 0.5 and avg_range < 1.0:
            vol = "low"
        else:
            vol = "normal"

        return trend, vol

    # Classify trades
    regime_trades = defaultdict(list)
    vol_trades = defaultdict(list)

    for t in trades:
        entry_time = t.get("entry_time")
        if not entry_time:
            continue
        regime = compute_regime_at_time(entry_time, btc_ohlcv)
        if regime[0] == "unknown":
            continue
        regime_trades[regime[0]].append(t["pnl_pct"])
        vol_trades[regime[1]].append(t["pnl_pct"])

    def print_regime_stats(name, trade_dict):
        print(f"\n  --- {name} ---")
        for regime, pnls in sorted(trade_dict.items()):
            n = len(pnls)
            if n == 0:
                continue
            wins = sum(1 for p in pnls if p > 0)
            wr = wins / n * 100
            total_pnl = sum(pnls)
            avg_pnl = mean(pnls)
            sd = stdev(pnls) if len(pnls) > 1 else 0.001
            sharpe = (mean(pnls) / sd) * sqrt(365) if sd > 0 else 0
            print(f"    {regime:10s}: {n:4d} trades, WR={wr:5.1f}%, PnL={total_pnl:+.2f}%, "
                  f"Avg={avg_pnl:+.3f}%, Sharpe={sharpe:.2f}")

    print_regime_stats("Trend Regime Performance", regime_trades)
    print_regime_stats("Volatility Regime Performance", vol_trades)

    # Determine where OSIRIS makes/loses money
    print(f"\n  --- Alpha Source Summary ---")
    best_regime = max(regime_trades.keys(), key=lambda k: sum(regime_trades[k]) if regime_trades[k] else -999)
    worst_regime = min(regime_trades.keys(), key=lambda k: sum(regime_trades[k]) if regime_trades[k] else 999)
    print(f"    Best regime:  {best_regime} (PnL={sum(regime_trades.get(best_regime, [0])):+.2f}%)")
    print(f"    Worst regime: {worst_regime} (PnL={sum(regime_trades.get(worst_regime, [0])):+.2f}%)")

# ── Phase 3: Long vs Short Attribution ────────────────────────────────────

def phase3_long_short(results):
    """Separate LONG/SHORT performance."""
    print(f"\n{'='*60}")
    print(f"  PHASE 3 — LONG vs SHORT ATTRIBUTION")
    print(f"{'='*60}")

    # Use the longest timeframe
    longest = max(results.keys(), key=int)
    trades = results[longest]["trades"]

    by_dir = defaultdict(list)
    for t in trades:
        by_dir[t["direction"]].append(t["pnl_pct"])

    print(f"  {'Direction':>10s} | {'Trades':>6s} | {'WR':>6s} | {'PnL':>9s} | {'Avg':>7s} | {'Sharpe':>7s} | {'ProfitFactor':>13s} | {'MaxDD':>7s}")
    print(f"  {'-'*10} | {'-'*6} | {'-'*6} | {'-'*9} | {'-'*7} | {'-'*7} | {'-'*13} | {'-'*7}")

    for direction in ["long", "short"]:
        pnls = by_dir.get(direction, [])
        if not pnls:
            continue
        n = len(pnls)
        wins = sum(1 for p in pnls if p > 0)
        wr = wins / n * 100
        total_pnl = sum(pnls)
        avg_pnl = mean(pnls)
        sd = stdev(pnls) if len(pnls) > 1 else 0.001
        sharpe = (mean(pnls) / sd) * sqrt(365) if sd > 0 else 0
        win_pnls = [p for p in pnls if p > 0]
        loss_pnls = [p for p in pnls if p < 0]
        pf = abs(sum(win_pnls) / sum(loss_pnls)) if loss_pnls and sum(loss_pnls) != 0 else float("inf")

        # Drawdown from absolute PnL
        abs_pnls = [t["pnl_abs"] for t in trades if t["direction"] == direction]
        running = 10000.0
        peak = 10000.0
        max_dd = 0.0
        for p in abs_pnls:
            running += p
            if running > peak:
                peak = running
            dd = (peak - running) / peak * 100
            max_dd = max(max_dd, dd)

        pf_str = f"{pf:.2f}" if pf != float("inf") else "Inf"
        print(f"  {direction:>10s} | {n:>6d} | {wr:>5.1f}% | {total_pnl:>+8.2f}% | {avg_pnl:>+6.3f}% | {sharpe:>7.2f} | {pf_str:>13s} | {max_dd:>6.2f}%")

    # Combined — use absolute PnL for drawdown
    pnls = [t["pnl_pct"] for t in trades]
    abs_pnls = [t["pnl_abs"] for t in trades]
    n = len(pnls)
    wins = sum(1 for p in pnls if p > 0)
    wr = wins / n * 100
    total_pnl = sum(pnls)
    avg_pnl = mean(pnls)
    sd = stdev(pnls) if len(pnls) > 1 else 0.001
    sharpe = (mean(pnls) / sd) * sqrt(365) if sd > 0 else 0
    running = 10000.0
    peak = 10000.0
    max_dd = 0.0
    for p in abs_pnls:
        running += p
        if running > peak:
            peak = running
        dd = (peak - running) / peak * 100
        max_dd = max(max_dd, dd)
    print(f"  {'COMBINED':>10s} | {n:>6d} | {wr:>5.1f}% | {total_pnl:>+8.2f}% | {avg_pnl:>+6.3f}% | {sharpe:>7.2f} | {'N/A':>13s} | {max_dd:>6.2f}%")

    # Per-asset breakdown
    print(f"\n  --- Per-Asset Breakdown ---")
    by_asset = defaultdict(lambda: {"long": [], "short": []})
    for t in trades:
        by_asset[t["asset"]][t["direction"]].append(t["pnl_pct"])

    print(f"  {'Asset':>6s} | {'Direction':>10s} | {'Trades':>6s} | {'WR':>6s} | {'PnL':>9s} | {'Sharpe':>7s}")
    print(f"  {'-'*6} | {'-'*10} | {'-'*6} | {'-'*6} | {'-'*9} | {'-'*7}")
    for asset in ["BTC", "ETH", "SOL"]:
        for direction in ["long", "short"]:
            pnls = by_asset[asset][direction]
            if not pnls:
                continue
            n = len(pnls)
            wins = sum(1 for p in pnls if p > 0)
            wr = wins / n * 100
            total_pnl = sum(pnls)
            sd = stdev(pnls) if len(pnls) > 1 else 0.001
            sharpe = (mean(pnls) / sd) * sqrt(365) if sd > 0 else 0
            print(f"  {asset:>6s} | {direction:>10s} | {n:>6d} | {wr:>5.1f}% | {total_pnl:>+8.2f}% | {sharpe:>7.2f}")

# ── Phase 4: Conviction Validation ────────────────────────────────────────

def phase4_conviction(results):
    """Test if higher conviction predicts higher returns."""
    print(f"\n{'='*60}")
    print(f"  PHASE 4 — CONVICTION VALIDATION")
    print(f"{'='*60}")

    longest = max(results.keys(), key=int)
    trades = results[longest]["trades"]

    if not trades:
        print("  No trades for conviction analysis")
        return

    # Sort trades by conviction
    sorted_trades = sorted(trades, key=lambda t: t["conviction"], reverse=True)
    n = len(sorted_trades)

    # Top 10%, 20%, 30% and Bottom 30%
    cuts = {
        "Top 10%": sorted_trades[:max(1, n // 10)],
        "Top 20%": sorted_trades[:max(1, n // 5)],
        "Top 30%": sorted_trades[:max(1, 3 * n // 10)],
        "Bottom 30%": sorted_trades[-max(1, 3 * n // 10):],
        "Middle 40%": sorted_trades[n // 5: n - 3 * n // 10] if n >= 5 else sorted_trades,
    }

    print(f"  {'Group':>12s} | {'Trades':>6s} | {'WR':>6s} | {'AvgPnL':>7s} | {'TotalPnL':>9s} | {'Sharpe':>7s} | {'AvgConv':>8s}")
    print(f"  {'-'*12} | {'-'*6} | {'-'*6} | {'-'*7} | {'-'*9} | {'-'*7} | {'-'*8}")

    for label, group_trades in cuts.items():
        if not group_trades:
            continue
        pnls = [t["pnl_pct"] for t in group_trades]
        convs = [t["conviction"] for t in group_trades]
        n_g = len(pnls)
        wins = sum(1 for p in pnls if p > 0)
        wr = wins / n_g * 100
        total_pnl = sum(pnls)
        avg_pnl = mean(pnls)
        avg_conv = mean(convs)
        sd = stdev(pnls) if len(pnls) > 1 else 0.001
        sharpe = (mean(pnls) / sd) * sqrt(365) if sd > 0 else 0
        print(f"  {label:>12s} | {n_g:>6d} | {wr:>5.1f}% | {avg_pnl:>+6.3f}% | {total_pnl:>+8.2f}% | {sharpe:>7.2f} | {avg_conv:>7.2f}")

    # Statistical test: correlation between conviction and PnL
    convs = [t["conviction"] for t in trades]
    pnls = [t["pnl_pct"] for t in trades]

    try:
        from scipy.stats import pearsonr, spearmanr
        pearson_r, pearson_p = pearsonr(convs, pnls)
        spearman_rho, spearman_p = spearmanr(convs, pnls)
        print(f"\n  --- Statistical Significance ---")
        print(f"  Pearson r:  {pearson_r:+.6f} (p={pearson_p:.6f}) {'*** p<0.001' if pearson_p < 0.001 else '** p<0.01' if pearson_p < 0.01 else '* p<0.05' if pearson_p < 0.05 else 'n.s.'}")
        print(f"  Spearman ρ: {spearman_rho:+.6f} (p={spearman_p:.6f}) {'*** p<0.001' if spearman_p < 0.001 else '** p<0.01' if spearman_p < 0.01 else '* p<0.05' if spearman_p < 0.05 else 'n.s.'}")
        if pearson_p < 0.05 and pearson_r > 0:
            print(f"  VERDICT: Higher conviction significantly predicts higher returns ✓")
        elif pearson_p < 0.05 and pearson_r < 0:
            print(f"  VERDICT: Higher conviction significantly predicts LOWER returns ⚠️")
        else:
            print(f"  VERDICT: No significant correlation between conviction and returns ✗")
    except ImportError:
        print(f"  scipy not available — using manual calculation")
        # Manual correlation
        n_c = len(convs)
        if n_c > 2:
            mean_c = mean(convs)
            mean_p = mean(pnls)
            num = sum((c - mean_c) * (p - mean_p) for c, p in zip(convs, pnls))
            den_c = sqrt(sum((c - mean_c)**2 for c in convs))
            den_p = sqrt(sum((p - mean_p)**2 for p in pnls))
            if den_c > 0 and den_p > 0:
                r_manual = num / (den_c * den_p)
                print(f"  Pearson r (manual): {r_manual:+.6f}")
            else:
                print(f"  Cannot compute correlation (no variance)")

# ── Phase 5: Agent Attribution ────────────────────────────────────────────

def phase5_agent_attribution(results):
    """Measure contribution of each agent via ablation."""
    print(f"\n{'='*60}")
    print(f"  PHASE 5 — AGENT ATTRIBUTION")
    print(f"{'='*60}")

    # Use the longest main experiment as baseline
    longest = max(results.keys(), key=int)
    baseline = results[longest]
    print(f"\n  Baseline ({longest}d):")
    print(f"    Trades: {baseline['summary']['trades']}, WR: {baseline['summary']['win_rate']:.1f}%, "
          f"Return: {baseline['summary']['return_pct']:+.2f}%, Sharpe: {baseline['summary']['sharpe']:.2f}")

    # Run ablation experiments: MarketAgent alone, RiskAgent alone
    ablation_results = {}
    for ablation_config in [
        ("MarketAgent Only", {"use_market": True, "use_risk": False}),
        ("RiskAgent Only", {"use_market": False, "use_risk": True}),
    ]:
        label, config = ablation_config
        print(f"\n  Running ablation: {label}...")
        try:
            # Import the experiment runner
            from scripts.recovery_experiment import run_experiment
            ab_result = run_experiment(
                days=longest, atr_multiplier=3.0,
                use_market=config["use_market"],
                use_risk=config["use_risk"],
                use_trend=False,
                signal_mode="both",
            )
            if ab_result:
                p = ab_result["portfolio"]
                print(f"    Trades: {p['total_trades']}, WR: {p['win_rate']:.1f}%, "
                      f"Return: {p['total_return_pct']:+.2f}%, Sharpe: {p['sharpe_ratio']:.2f}")
                ablation_results[label] = p
            else:
                print(f"    FAILED")
        except Exception as e:
            print(f"    ERROR: {e}")

    # Print comparison
    if ablation_results:
        print(f"\n  --- Agent Contribution Summary ---")
        print(f"  {'Config':>20s} | {'Trades':>6s} | {'WR':>6s} | {'Return':>9s} | {'Sharpe':>7s} | {'Equity':>10s}")
        print(f"  {'-'*20} | {'-'*6} | {'-'*6} | {'-'*9} | {'-'*7} | {'-'*10}")
        print(f"  {'Market+Risk (baseline)':>20s} | {baseline['summary']['trades']:>6d} | {baseline['summary']['win_rate']:>5.1f}% | {baseline['summary']['return_pct']:>+8.2f}% | {baseline['summary']['sharpe']:>7.2f} | ${baseline['summary']['equity']:>8,.2f}")
        for label, p in ablation_results.items():
            print(f"  {label:>20s} | {p['total_trades']:>6d} | {p['win_rate']:>5.1f}% | {p['total_return_pct']:>+8.2f}% | {p['sharpe_ratio']:>7.2f} | ${p['equity']:>8,.2f}")

        # Determine contribution
        baseline_ret = baseline["summary"]["return_pct"]
        for label, p in ablation_results.items():
            ret_diff = p["total_return_pct"] - baseline_ret
            print(f"\n    {label}: return={p['total_return_pct']:+.2f}% (delta from baseline: {ret_diff:+.2f}%)")

# ── Phase 6: Regime Detection Design ──────────────────────────────────────

def phase6_regime_design(results):
    """Architecture and validation plan for a RegimeAgent."""
    print(f"\n{'='*60}")
    print(f"  PHASE 6 — REGIME DETECTION DESIGN")
    print(f"{'='*60}")

    print(f"""
  MOTIVATION
  ----------
  Phase 2 analysis shows OSIRIS alpha is regime-dependent. The system makes
  money in bull markets (LONG) and can lose in sideways/bear markets.
  Without regime detection, the system is exposed to regime-shift risk.

  REGIMEAGENT ARCHITECTURE
  ------------------------
  New Agent: RegimeAgent
  Role:     Market Regime Classifier
  Vote:     Advisory (modulates confidence, not direction)

  Detection Dimensions:
    1. TREND REGIME:  bull / bear / sideways
       - SMA20/SMA50 slope analysis
       - ADX (trend strength) — >25 = trending, <20 = ranging
       - Price vs 200-period SMA (structural bias)

    2. VOLATILITY REGIME:  low / normal / high / extreme
       - ATR(14) / ATR(100) ratio (current vs historical)
       - Bollinger Band width
       - 90th percentile of daily range

    3. RISK REGIME:  calm / cautious / stressed / crisis
       - VIX equivalent (crypto: use options-implied or proxy via volatility of volatility)
       - Correlation across assets (BTC-ETH-SOL)
       - Liquidity proxy (volume ratio vs 30d average)

  OUTPUT
  ------
  RegimeAgent produces an AgentOpinion with:
    - recommendation: WATCH (no direct trade signal)
    - metadata: {{
        "regime": "bull|bear|sideways",
        "volatility": "low|normal|high|extreme",
        "risk_regime": "calm|cautious|stressed|crisis",
        "trend_strength": 0.0-1.0,
        "suggested_bias": "long|short|neutral",
        "max_position_pct": float (risk-adjusted cap),
      }}

  INTEGRATION
  -----------
  RegimeAgent integrates into the existing AgentCouncil:
    - Does NOT vote on direction (always WATCH)
    - Modulates confidence of directional agents via council weight adjustment
    - If regime is 'crisis', overrides position sizing to 0 (halt trading)
    - If regime is 'bull' and trend_strength > 0.7, boosts MarketAgent weight
    - If regime is 'sideways' and volatility is 'high', boosts SHORT bias

  VALIDATION PLAN
  ---------------
  1. Collect 365 days of regime labels from RegimeAgent (backtest)
  2. Compare regime labels against actual market conditions:
     - Bull: next 30-day return > +5%
     - Bear: next 30-day return < -5%
     - Sideways: next 30-day return between -5% and +5%
  3. Measure regime prediction accuracy:
     - Precision: % of "bull" predictions followed by actual bull
     - Recall: % of actual bull markets detected
  4. Measure P&L impact:
     - Run experiment with and without RegimeAgent
     - Target: regime-aware version has lower max drawdown
       (not necessarily higher return)

  SUCCESS CRITERIA
  ----------------
  - RegimeAgent accuracy > 65% (macro classification, not micro)
  - Regime-aware system reduces max drawdown by at least 30%
  - No significant reduction in total return (< 10% penalty)
  - Regime transition detected within 5 candles of occurrence

  SKIP CONDITIONS
  ---------------
  Do NOT build RegimeAgent if:
    - Phase 2 shows alpha is NOT regime-dependent (unlikely given data)
    - Current drawdown is acceptable without regime detection
    - A simpler approach (e.g., fixed SHORT/LONG bias based on SMA200)
      achieves the same risk reduction
""")

# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"  OSIRIS RESEARCH SPRINT — Alpha Stability & Regime Analysis")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    timeframes = [30, 60, 90]
    # 180 and 365 are skipped by default due to API limits and runtime;
    # uncomment to run (may take 10+ minutes and need multiple paginations)
    # timeframes = [30, 60, 90, 180, 365]

    results = {}
    for days in timeframes:
        try:
            r = run_research_experiment(days, atr_multiplier=3.0, signal_mode="both")
            results[days] = r
        except Exception as e:
            print(f"  ERROR on {days}d: {e}")
            import traceback; traceback.print_exc()

    if not results:
        print("\n  No results — aborting")
        sys.exit(1)

    phase1_robustness(results)
    phase2_regime_analysis(results)
    phase3_long_short(results)
    phase4_conviction(results)
    phase5_agent_attribution(results)
    phase6_regime_design(results)

    print(f"\n{'='*60}")
    print(f"  RESEARCH COMPLETE")
    print(f"{'='*60}")
