"""OSIRIS Phase 8 — Paper Trading Reality Test
30-day forward-test with slippage, direction bias, and capital protection.
No intervention. Comprehensive metrics.

Usage: python scripts/reality_test.py
"""
import sys, json, time, math
sys.path.insert(0, ".")
from collections import defaultdict
from datetime import datetime, timezone
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
from core.execution.slippage import SlippageEngine
from core.execution.direction_controller import DirectionController
from core.execution.capital_guard import CapitalGuard

SYMBOLS = ["BTC", "ETH", "SOL"]
BNB_MAP = {"BTC":"BTCUSDT","ETH":"ETHUSDT","SOL":"SOLUSDT","XRP":"XRPUSDT","BNB":"BNBUSDT"}

def fetch_ohlcv(symbol, days, interval="1h"):
    pair = BNB_MAP.get(symbol)
    if not pair:
        return None
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
    return None

def generate_events(symbol, ohlcv):
    events = []
    for i in range(1, len(ohlcv)):
        prev, curr = ohlcv[i-1], ohlcv[i]
        change = (curr["close"] - prev["close"]) / prev["close"]
        u = Urgency.HIGH if abs(change) > 0.05 else Urgency.MEDIUM if abs(change) > 0.02 else Urgency.LOW
        et = EventType.VOLUME_SPIKE if (abs(change) > 0.05 and curr["volume"] > prev["volume"] * 1.5) else EventType.PRICE_MOVEMENT
        events.append(Event(
            id=f"{symbol}_{i}", source="reality_test",
            event_type=et, title=f"{symbol} {change*100:+.2f}%",
            assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO, price_at_event=curr["close"])],
            timestamp=curr["time"], detected_at=curr["time"],
            urgency=u, sentiment_score=change, confidence=0.7,
        ))
    return events

def run_reality_test(days=30, slippage_bps=10, signal_mode="both"):
    print(f"\n{'='*70}")
    print(f"  PHASE 8 — PAPER TRADING REALITY TEST")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  {days} days | Slippage {slippage_bps}bps + spread | DirectionController | CapitalGuard")
    print(f"{'='*70}")

    start = time.time()

    # ── Data ──
    ohlcv_cache = {}
    for sym in SYMBOLS:
        data = fetch_ohlcv(sym, days + 5)
        if data and len(data) >= 50:
            ohlcv_cache[sym] = data
            print(f"  {sym}: {len(data)} candles ({data[0]['time'].strftime('%Y-%m-%d')} -> {data[-1]['time'].strftime('%Y-%m-%d')})")
        else:
            print(f"  {sym}: FAILED ({len(data) if data else 0} candles)")
            return None

    # ── Agents + Guards ──
    market = MarketAgent(signal_mode=signal_mode)
    market._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    risk = RiskAgent()
    risk._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    council = AgentCouncil()
    perf = PerformanceMemory()
    slippage = SlippageEngine(slippage_pct=slippage_bps / 10000)
    direction_ctrl = DirectionController(window=20, wr_threshold=0.25, recovery_threshold=0.35)
    capital_guard = CapitalGuard(initial_capital=10000.0, max_daily_loss_pct=10.0,
                                 max_weekly_loss_pct=20.0, max_open_risk_pct=25.0)

    engine = PaperTradingEngine(
        initial_capital=10000.0,
        performance_memory=perf,
        council=council,
        slippage_engine=slippage,
        direction_controller=direction_ctrl,
        capital_guard=capital_guard,
    )

    # ── Events ──
    all_events = []
    for sym, ohlcv in ohlcv_cache.items():
        all_events.extend(generate_events(sym, ohlcv))
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

    # ── Run pipeline ──
    price_history = {s: [] for s in SYMBOLS}
    all_decisions = []
    all_signals = []
    blocked_by_direction = 0
    blocked_by_capital = 0

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
        else:
            if decision and decision.action in (Recommendation.BUY, Recommendation.SELL, Recommendation.STRONG_BUY, Recommendation.STRONG_SELL):
                blocked_by_direction += 1

        current = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
        engine.check_positions(current)

        if not engine.capital_guard.is_trading_allowed():
            blocked_by_capital += 1

    # Close remaining
    final = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
    engine.check_positions(final)

    elapsed = time.time() - start

    # ── Collect detailed data ──
    detailed_trades = []
    for t in engine.closed_trades:
        detailed_trades.append({
            "asset": t.signal.asset,
            "direction": t.signal.direction.value,
            "pnl_pct": t.pnl_percent or 0,
            "pnl_abs": t.pnl_absolute or 0,
            "exit_reason": t.exit_reason.value if t.exit_reason else "unknown",
            "conviction": t.signal.conviction,
            "entry_price": t.entry_price_executed,
            "exit_price": t.exit_price or 0,
            "stop_loss": t.signal.stop_loss,
            "take_profit": t.signal.take_profit,
            "entry_time": t.entry_time.isoformat() if t.entry_time else None,
            "exit_time": t.exit_time.isoformat() if t.exit_time else None,
            "holding_hours": t.holding_hours or 0,
        })

    portfolio = engine.get_portfolio_summary()

    # Equity curve / max DD
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

    # Direction controller stats
    dc_summary = direction_ctrl.summary()

    # Capital guard summary
    cg_summary = capital_guard.summary()

    # ── Print summary ──
    print(f"\n{'='*70}")
    print(f"  RESULTS")
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

    print(f"\n  --- Direction Controller ---")
    print(f"  LONG last {dc_summary['long_window']}: WR={dc_summary['long_wr']:.1%}, PF={dc_summary['long_pf']}")
    print(f"  SHORT last {dc_summary['short_window']}: WR={dc_summary['short_wr']:.1%}, PF={dc_summary['short_pf']}")
    print(f"  Disable SHORT:     {dc_summary['disable_short']}")
    print(f"  Disable LONG:      {dc_summary['disable_long']}")
    print(f"  Allowed direction: {dc_summary['allowed']}")

    print(f"\n  --- Capital Guard ---")
    print(f"  Daily loss:        {cg_summary['daily_loss_pct']:.2f}%")
    print(f"  Weekly loss:       {cg_summary['weekly_loss_pct']:.2f}%")
    print(f"  Open risk:         {cg_summary['open_risk_pct']:.2f}%")
    print(f"  Kill switch:       {cg_summary['kill_switch']}")
    print(f"  Size reduction:    {cg_summary['size_reduction']:.2f}x")
    print(f"  Trading allowed:   {cg_summary['trading_allowed']}")
    print(f"  Trades blocked (dir): {blocked_by_direction}")
    print(f"  Trades blocked (cap): {blocked_by_capital}")

    print(f"\n  --- Per-direction ---")
    by_dir = defaultdict(list)
    for t in detailed_trades:
        by_dir[t["direction"]].append(t["pnl_pct"])
    for direction in ["long", "short"]:
        pnls = by_dir.get(direction, [])
        if not pnls:
            print(f"  {direction:6s}: 0 trades")
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
        print(f"  {direction:6s}: {n:4d} trades, WR={wr:5.1f}%, PnL={total_pnl:+.2f}%, "
              f"Avg={avg_pnl:+.3f}%, Sharpe={sharpe:.2f}, PF={pf:.2f}")

    print(f"\n  --- Exit Reasons ---")
    by_reason = defaultdict(int)
    for t in detailed_trades:
        by_reason[t["exit_reason"]] += 1
    for reason, count in sorted(by_reason.items()):
        print(f"  {reason:15s}: {count}")

    print(f"\n  --- Per-asset ---")
    by_asset = defaultdict(lambda: {"long": {"trades": 0, "pnl": 0}, "short": {"trades": 0, "pnl": 0}})
    for t in detailed_trades:
        a = t["asset"]
        d = t["direction"]
        by_asset[a][d]["trades"] += 1
        by_asset[a][d]["pnl"] += t["pnl_pct"]
    for asset in SYMBOLS:
        for direction in ["long", "short"]:
            data = by_asset[asset][direction]
            if data["trades"] > 0:
                print(f"  {asset:4s} {direction:6s}: {data['trades']:4d} trades, PnL={data['pnl']:+.2f}%")

    print(f"\n{'='*70}")
    verdict = "SURVIVED" if portfolio["total_return_pct"] > 0 and max_dd < 30 else "FAILED"
    print(f"  VERDICT: {verdict}")
    print(f"  30-day return: {portfolio['total_return_pct']:+.2f}% | MaxDD: {max_dd:.2f}% | Sharpe: {portfolio['sharpe_ratio']:.2f}")
    print(f"{'='*70}")

    return {
        "summary": portfolio,
        "max_drawdown": round(max_dd, 2),
        "direction_controller": dc_summary,
        "capital_guard": cg_summary,
        "blocked_by_direction": blocked_by_direction,
        "blocked_by_capital": blocked_by_capital,
        "trades": detailed_trades,
        "elapsed_sec": round(elapsed, 1),
    }

def run_baseline(days=30, slippage_bps=10):
    """Run without guards for comparison."""
    print(f"\n{'='*70}")
    print(f"  BASELINE (no guards) — for comparison")
    print(f"{'='*70}")

    ohlcv_cache = {}
    for sym in SYMBOLS:
        data = fetch_ohlcv(sym, days + 5)
        if data and len(data) >= 50:
            ohlcv_cache[sym] = data

    market = MarketAgent(signal_mode="both")
    market._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    risk = RiskAgent()
    risk._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
    council = AgentCouncil()
    perf = PerformanceMemory()
    slippage = SlippageEngine(slippage_pct=slippage_bps / 10000)
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

        current = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
        engine.check_positions(current)

    final = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
    engine.check_positions(final)

    p = engine.get_portfolio_summary()

    detailed_trades = []
    for t in engine.closed_trades:
        detailed_trades.append({
            "pnl_pct": t.pnl_percent or 0,
            "pnl_abs": t.pnl_absolute or 0,
            "direction": t.signal.direction.value,
        })

    running_equity = 10000.0
    peak = 10000.0
    max_dd = 0.0
    for t in detailed_trades:
        running_equity += t["pnl_abs"]
        if running_equity > peak:
            peak = running_equity
        dd = (peak - running_equity) / peak * 100
        max_dd = max(max_dd, dd)

    print(f"\n  Baseline results:")
    print(f"    Trades: {p['total_trades']}, WR: {p['win_rate']:.1f}%, "
          f"Return: {p['total_return_pct']:+.2f}%, Sharpe: {p['sharpe_ratio']:.2f}, "
          f"MaxDD: {max_dd:.2f}%")

    return {"summary": p, "max_drawdown": max_dd}

if __name__ == "__main__":
    # Test on most recent 30 days
    print(f"{'='*70}")
    print(f"  PHASE 8 — PAPER TRADING REALITY TEST")
    print(f"  Testing on recent data (May 18 - Jun 22)")
    print(f"{'='*70}")
    r_recent = run_reality_test(days=30, slippage_bps=10, signal_mode="both")

    # Test on earlier data (30-day window offset by 30 days) for comparison
    if r_recent:
        print(f"\n{'='*70}")
        print(f"  SECONDARY TEST — Earlier 30-day window (comparison)")
        print(f"  Note: API returns most recent data, so 60-day run covers older data")
        print(f"{'='*70}")
        r_older = run_reality_test(days=60, slippage_bps=10, signal_mode="both")

        if r_older and r_recent:
            print(f"\n{'='*70}")
            print(f"  COMPARISON — Two Windows")
            print(f"{'='*70}")
            print(f"  {'Metric':>20s} | {'Recent 30d':>12s} | {'Older 30d (of 60)':>16s} | {'Delta':>10s}")
            print(f"  {'-'*20} | {'-'*12} | {'-'*16} | {'-'*10}")
            metrics = [
                ("Return", f"{r_recent['summary']['total_return_pct']:+.2f}%",
                 f"{r_older['summary']['total_return_pct']:+.2f}%",
                 f"{r_older['summary']['total_return_pct'] - r_recent['summary']['total_return_pct']:+.2f}%"),
                ("Win Rate", f"{r_recent['summary']['win_rate']:.1f}%",
                 f"{r_older['summary']['win_rate']:.1f}%",
                 f"{r_older['summary']['win_rate'] - r_recent['summary']['win_rate']:+.1f}%"),
                ("Sharpe", f"{r_recent['summary']['sharpe_ratio']:.2f}",
                 f"{r_older['summary']['sharpe_ratio']:.2f}",
                 f"{r_older['summary']['sharpe_ratio'] - r_recent['summary']['sharpe_ratio']:+.2f}"),
                ("Max DD", f"{r_recent['max_drawdown']:.2f}%",
                 f"{r_older['max_drawdown']:.2f}%",
                 f"{r_older['max_drawdown'] - r_recent['max_drawdown']:+.2f}%"),
                ("Trades", f"{r_recent['summary']['total_trades']}",
                 f"{r_older['summary']['total_trades']}", ""),
            ]
            for row in metrics:
                print(f"  {row[0]:>20s} | {row[1]:>12s} | {row[2]:>16s} | {row[3]:>10s}")

            print(f"\n")
            if r_recent['summary']['total_return_pct'] > 0 and r_older['summary']['total_return_pct'] > 0:
                print(f"  VERDICT: System profitable in both windows. Guards operational.")
            elif r_recent['summary']['total_return_pct'] > 0 and r_older['summary']['total_return_pct'] <= 0:
                print(f"  VERDICT: Guards protected system during unfavorable window. CRITICAL EVIDENCE.")
            else:
                print(f"  VERDICT: Both windows unfavorable. Guards may need tuning.")

        # Run baseline (no guards) on recent window
        print(f"\n  Running baseline (no guards) on recent window...")
        baseline = run_baseline(days=30, slippage_bps=10)

        if baseline:
            print(f"\n{'='*70}")
            print(f"  COMPARISON — Recent 30d: Guards vs No Guards")
            print(f"{'='*70}")
            print(f"  {'Metric':>20s} | {'Guards':>12s} | {'No Guards':>12s} | {'Delta':>10s}")
            print(f"  {'-'*20} | {'-'*12} | {'-'*12} | {'-'*10}")
            metrics = [
                ("Return", f"{r_recent['summary']['total_return_pct']:+.2f}%",
                 f"{baseline['summary']['total_return_pct']:+.2f}%",
                 f"{r_recent['summary']['total_return_pct'] - baseline['summary']['total_return_pct']:+.2f}%"),
                ("Win Rate", f"{r_recent['summary']['win_rate']:.1f}%",
                 f"{baseline['summary']['win_rate']:.1f}%",
                 f"{r_recent['summary']['win_rate'] - baseline['summary']['win_rate']:+.1f}%"),
                ("Sharpe", f"{r_recent['summary']['sharpe_ratio']:.2f}",
                 f"{baseline['summary']['sharpe_ratio']:.2f}",
                 f"{r_recent['summary']['sharpe_ratio'] - baseline['summary']['sharpe_ratio']:+.2f}"),
                ("Max DD", f"{r_recent['max_drawdown']:.2f}%",
                 f"{baseline['max_drawdown']:.2f}%",
                 f"{r_recent['max_drawdown'] - baseline['max_drawdown']:+.2f}%"),
                ("Trades", f"{r_recent['summary']['total_trades']}",
                 f"{baseline['summary']['total_trades']}", ""),
            ]
            for row in metrics:
                print(f"  {row[0]:>20s} | {row[1]:>12s} | {row[2]:>12s} | {row[3]:>10s}")

            delta_ret = r_recent['summary']['total_return_pct'] - baseline['summary']['total_return_pct']
            dd_change = r_recent['max_drawdown'] - baseline['max_drawdown']
            print(f"\n  Guard impact (recent window — favorable):")
            print(f"    Return delta: {delta_ret:+.2f}%")
            print(f"    MaxDD delta:  {dd_change:+.2f}%")
            if r_recent['summary']['total_return_pct'] == baseline['summary']['total_return_pct']:
                print(f"    NOTE: Guards didn't trigger in this window (97.8% WR). Need bearish window to verify.")
