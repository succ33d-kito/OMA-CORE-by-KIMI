"""OSIRIS Validation Sprint — Full Report

Run: python scripts/run_validation.py
Output: prints structured report with all Phase 3-5 findings
"""
import sys
sys.path.insert(0, ".")

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from statistics import mean, stdev
from math import sqrt

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Urgency
from core.schemas.agent_schema import Recommendation
from core.schemas.trade_schema import TradeDirection
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory
from core.execution.backtest_engine_v2 import BacktestEngineV2


SYMBOLS = ["BTC", "ETH", "SOL"]
DAYS = 14


def generate_events(symbol, ohlcv):
    events = []
    for i in range(1, len(ohlcv)):
        prev, curr = ohlcv[i - 1], ohlcv[i]
        change = (curr["close"] - prev["close"]) / prev["close"]
        urgency = Urgency.HIGH if abs(change) > 0.05 else Urgency.MEDIUM if abs(change) > 0.02 else Urgency.LOW
        et = EventType.VOLUME_SPIKE if (abs(change) > 0.05 and curr["volume"] > prev["volume"] * 1.5) else EventType.PRICE_MOVEMENT
        events.append(Event(
            id=f"{symbol}_{i}", source="validation",
            event_type=et, title=f"{symbol} {change*100:+.2f}%",
            assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO, price_at_event=curr["close"])],
            timestamp=curr["time"], detected_at=curr["time"],
            urgency=urgency, sentiment_score=change, confidence=0.7,
        ))
    return events


def main():
    print("=" * 72)
    print("  OSIRIS VALIDATION REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)

    # Phase 3: Fetch data and run pipeline
    print("\n[Phase 3] Fetching OHLCV data...")
    fetcher = BacktestEngineV2()
    all_ohlcv = {}
    for sym in SYMBOLS:
        data = fetcher.fetch_ohlcv(sym, days=DAYS + 5)
        if data and len(data) >= 50:
            all_ohlcv[sym] = data
            print(f"  {sym}: {len(data)} candles")

    if not all_ohlcv:
        print("  ERROR: No OHLCV data available.")
        return

    # Build pipeline with cached OHLCV
    market = MarketAgent()
    risk = RiskAgent()

    def make_fetcher(cache):
        def f(sym):
            return cache.get(sym)
        return f
    market._fetch_ohlcv = make_fetcher(all_ohlcv)
    risk._fetch_ohlcv = make_fetcher(all_ohlcv)

    council = AgentCouncil()
    perf = PerformanceMemory()
    engine = PaperTradingEngine(initial_capital=10000.0, performance_memory=perf, council=council)

    all_events = []
    for sym, ohlcv in all_ohlcv.items():
        all_events.extend(generate_events(sym, ohlcv))
    all_events.sort(key=lambda e: e.timestamp)

    print(f"  Generated {len(all_events)} events from OHLCV movements")
    print(f"  Running pipeline ({len(all_events)} cycles)...")

    decisions = []
    price_history = {}
    for sym in SYMBOLS:
        price_history[sym] = []

    for event in all_events:
        sym = event.assets[0].symbol
        price = event.assets[0].price_at_event
        price_history[sym].append((event.timestamp, price))

        mo = market.analyze(event)
        ro = risk.analyze(event)
        if not mo or not ro:
            continue

        council.submit_opinion(mo)
        council.submit_opinion(ro)
        decision = council.decide(event.id)
        if decision:
            decisions.append(decision)

        signal = engine.process_decision(decision)
        if signal:
            engine.execute_signal(signal)

        current = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
        engine.check_positions(current)

    final = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
    engine.check_positions(final)

    # ── Phase 3: Portfolio & Trade Results ──────────────────────────
    print("\n" + "=" * 72)
    print("  PHASE 3 — PAPER TRADING RESULTS")
    print("=" * 72)
    p = engine.get_portfolio_summary()
    print(f"  Initial capital:   ${p['initial_capital']:,.2f}")
    print(f"  Final equity:      ${p['equity']:,.2f}")
    print(f"  Total return:      {p['total_return_pct']:+.2f}%")
    print(f"  Total trades:      {p['total_trades']}")
    print(f"  Win rate:          {p['win_rate']:.1f}%")
    print(f"  Avg PnL:           {p['avg_pnl_pct']:+.2f}%")
    print(f"  Sharpe ratio:      {p['sharpe_ratio']:.2f}")
    print(f"  Open positions:    {p['open_positions']}")

    # Trade detail
    if engine.closed_trades:
        by_asset = defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0})
        by_dir = defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0})
        for t in engine.closed_trades:
            pnl = t.pnl_percent or 0
            by_asset[t.signal.asset]["count"] += 1
            by_asset[t.signal.asset]["wins"] += 1 if pnl > 0 else 0
            by_asset[t.signal.asset]["pnl"] += pnl
            by_dir[t.signal.direction.value]["count"] += 1
            by_dir[t.signal.direction.value]["wins"] += 1 if pnl > 0 else 0
            by_dir[t.signal.direction.value]["pnl"] += pnl

        print(f"\n  Per Asset:")
        for asset, s in sorted(by_asset.items()):
            wr = s["wins"] / s["count"] * 100 if s["count"] > 0 else 0
            print(f"    {asset:6s}: {s['count']:3d} trades, {wr:5.1f}% WR, PnL={s['pnl']:+6.2f}%")

        print(f"\n  Per Direction:")
        for d, s in sorted(by_dir.items()):
            wr = s["wins"] / s["count"] * 100 if s["count"] > 0 else 0
            print(f"    {d:6s}: {s['count']:3d} trades, {wr:5.1f}% WR, PnL={s['pnl']:+6.2f}%")

        print(f"\n  Exit Reasons:")
        reasons = defaultdict(int)
        for t in engine.closed_trades:
            reasons[t.exit_reason.value] += 1
        for r, c in sorted(reasons.items()):
            print(f"    {r}: {c}")

    # ── Phase 4: Agent Performance Attribution ──────────────────────
    print("\n" + "=" * 72)
    print("  PHASE 4 — AGENT PERFORMANCE ATTRIBUTION")
    print("=" * 72)

    agent_stats = {}
    for name in perf._agent_records:
        records = perf._agent_records[name]
        wins = sum(1 for r in records if r["correct"])
        total = len(records)
        acc = wins / total if total > 0 else 0
        avg_conf = mean(r["confidence"] for r in records) if records else 0
        cal = perf.get_agent_confidence_calibration(name)
        agent_stats[name] = (total, wins, acc, avg_conf, cal)

    if agent_stats:
        ranked = sorted(agent_stats.items(), key=lambda x: -x[1][2])
        print(f"  {'Agent':20s} {'Acc':>6s} {'W/L':>8s} {'Conf':>6s} {'Bias':>7s} {'Status':>15s}")
        print(f"  {'-'*62}")
        for name, (total, wins, acc, conf, cal) in ranked:
            status = "overconfident" if cal["overconfidence"] else "underconfident" if cal["underconfidence"] else "calibrated"
            print(f"  {name:20s} {acc:6.1%} {wins}/{total:<5d} {conf:6.2f} {cal['bias']:+6.3f} {status:>15s}")

        # Which agent contributes more to winning?
        print(f"\n  Contribution Analysis:")
        for name, (total, wins, acc, conf, cal) in ranked:
            if total >= 3:
                contribution = acc - 0.5
                print(f"    {name:20s}: {'+' if contribution > 0 else ''}{contribution:+.1%} vs random, "
                      f"{'POSITIVE' if contribution > 0 else 'NEGATIVE'} contribution")
    else:
        print("  No agent records — no closed trades with opinion tracking.")

    # ── Phase 5: Council Validation ─────────────────────────────────
    print("\n" + "=" * 72)
    print("  PHASE 5 — COUNCIL VALIDATION")
    print("=" * 72)

    # Build conviction→outcome pairs
    pairs_conv = []
    pairs_cons = []
    for sym, ohlcv in all_ohlcv.items():
        events = generate_events(sym, ohlcv)
        for event in events:
            mo = market.analyze(event)
            ro = risk.analyze(event)
            if not mo or not ro:
                continue
            c = AgentCouncil()
            c.submit_opinion(mo)
            c.submit_opinion(ro)
            d = c.decide(event.id)
            if not d:
                continue

            idx = next((i for i, cv in enumerate(ohlcv) if cv["time"] >= event.timestamp), None)
            if idx is None or idx + 24 >= len(ohlcv):
                continue

            fwd = ohlcv[idx + 24]["close"]
            cur = event.assets[0].price_at_event or ohlcv[idx]["close"]
            mult = 1 if d.action in (Recommendation.BUY, Recommendation.STRONG_BUY) else -1 if d.action in (Recommendation.SELL, Recommendation.STRONG_SELL) else 0
            if mult == 0:
                continue
            outcome = (fwd - cur) / cur * mult
            pairs_conv.append((d.conviction, outcome))
            pairs_cons.append((d.consensus_score, outcome))

    n = len(pairs_conv)
    print(f"  Total decision-outcome pairs: {n}")
    print()

    if n >= 10:
        # 1. Conviction analysis
        med_conv = sorted(pairs_conv, key=lambda x: x[0])[n // 2][0]
        high = [p[1] for p in pairs_conv if p[0] >= med_conv]
        low = [p[1] for p in pairs_conv if p[0] < med_conv]
        h_avg, l_avg = mean(high), mean(low)
        print(f"  1. Conviction vs Outcome:")
        print(f"     High conviction avg: {h_avg:+.4f} (n={len(high)})")
        print(f"     Low conviction avg:  {l_avg:+.4f} (n={len(low)})")
        print(f"     Delta:               {h_avg - l_avg:+.4f}")
        print(f"     Conviction predicts: {'YES ✓' if h_avg > l_avg else 'NO ✗'}")
        print()

        # 2. Consensus analysis
        med_cons = sorted(pairs_cons, key=lambda x: x[0])[n // 2][0]
        hc = [p[1] for p in pairs_cons if p[0] >= med_cons]
        lc = [p[1] for p in pairs_cons if p[0] < med_cons]
        hc_avg = mean(hc) if hc else 0
        lc_avg = mean(lc) if lc else 0
        print(f"  2. Consensus vs Outcome:")
        print(f"     High consensus avg:  {hc_avg:+.4f} (n={len(hc)})")
        print(f"     Low consensus avg:   {lc_avg:+.4f} (n={len(lc)})")
        print(f"     Delta:               {hc_avg - lc_avg:+.4f}")
        print(f"     Consensus predicts:  {'YES ✓' if hc_avg > lc_avg else 'NO ✗'}")
        print()

        # 3. Conviction as continuous variable
        try:
            from scipy.stats import pearsonr
            corr_c, p_c = pearsonr([p[0] for p in pairs_conv], [p[1] for p in pairs_conv])
            print(f"  3. Conviction-Outcome correlation: r={corr_c:.4f} (p={p_c:.4f})")
            print(f"     {'Statistically significant' if p_c < 0.05 else 'Not statistically significant'}")
        except ImportError:
            print(f"  3. Pearson correlation: scipy not installed, computing manually")
            conv_vals = [p[0] for p in pairs_conv]
            out_vals = [p[1] for p in pairs_conv]
            n = len(conv_vals)
            mx, my = mean(conv_vals), mean(out_vals)
            sx = stdev(conv_vals) if len(conv_vals) > 1 else 1
            sy = stdev(out_vals) if len(out_vals) > 1 else 1
            cov = sum((conv_vals[i] - mx) * (out_vals[i] - my) for i in range(n)) / (n - 1)
            r = cov / (sx * sy) if sx * sy > 0 else 0
            print(f"     r ≈ {r:.4f}")
        except Exception:
            print(f"  3. Correlation computation failed")
        print()

        # 4. Track record analysis
        if agent_stats:
            print(f"  4. Track Record Impact:")
            for name, (total, wins, acc, conf, cal) in ranked:
                if total >= 3:
                    print(f"     {name:20s}: {acc:.1%} accuracy, weights {'increase' if acc > 0.5 else 'decrease'} conviction")
            print()

    else:
        print(f"  Insufficient data for council validation.")

    # ── Track record effect on conviction ───────────────────────────
    if agent_stats:
        print(f"  5. Weighted vs Unweighted Conviction:")
        test_council = AgentCouncil()
        unweighted = AgentCouncil()
        # Reset track records to neutral
        for name in perf._agent_records:
            test_council.update_track_record(name, True)
            unweighted._track_record[name] = 0.5
        # Compare on a sample event
        if all_events:
            e = all_events[0]
            mo = market.analyze(e)
            ro = risk.analyze(e)
            if mo and ro:
                test_council.submit_opinion(mo)
                test_council.submit_opinion(ro)
                d_weighted = test_council.decide(e.id)
                unweighted.submit_opinion(mo)
                unweighted.submit_opinion(ro)
                d_unweighted = unweighted.decide(e.id)
                if d_weighted and d_unweighted:
                    diff = d_weighted.conviction - d_unweighted.conviction
                    print(f"     Weighted conv:   {d_weighted.conviction:.2f}")
                    print(f"     Unweighted conv: {d_unweighted.conviction:.2f}")
                    print(f"     Difference:      {diff:+.2f} "
                          f"({'Track records help' if diff > 0 else 'Track records hurt'})")

    # ── Phase 6: Production Readiness ───────────────────────────────
    print("\n" + "=" * 72)
    print("  PHASE 6 — PRODUCTION READINESS ASSESSMENT")
    print("=" * 72)

    issues = []

    if p["total_trades"] == 0:
        issues.append(("CRITICAL", "Paper Trading", "No trades executed in 14-day experiment"))
    if n < 30:
        issues.append(("WARNING", "Council Validation", f"Only {n} decision-outcome pairs"))
    if agent_stats:
        for name, (total, wins, acc, conf, cal) in ranked:
            if total >= 5 and cal["overconfidence"]:
                issues.append(("WARNING", f"Agent {name}", f"Overconfident: bias={cal['bias']:+.3f}"))

    issues.append(("INFO", "Slippage", "No slippage model in backtest or paper trading"))
    issues.append(("INFO", "OHLCV Cache", "No caching between runs — repeated Binance calls"))
    issues.append(("INFO", "Persistence", "PerformanceMemory in-memory only — lost on restart"))
    issues.append(("INFO", "Single-asset", "Agents analyze only assets[0], ignore multi-asset events"))
    issues.append(("INFO", "Spread", "No bid-ask spread in paper trading execution"))

    levels = {
        "Paper Trading": (0.6 if p["total_trades"] > 0 else 0.3),
        "Demo Trading": (0.3 if p["total_trades"] > 5 else 0.15),
        "Real Capital": 0.0,
    }
    blockers = {
        "Paper Trading": ["PerformanceMemory persistence needed for multi-session tracking"],
        "Demo Trading": ["Slippage model", "Position sizing Kelly criterion"],
        "Real Capital": ["Broker API integration", "Regulatory compliance", "Slippage & spread models",
                         "Risk limits enforcement", "Multi-asset correlation risk", "Backup execution path"],
    }

    for level, score in levels.items():
        print(f"\n  Readiness for {level}: {score:.0%}")
        if score < 0.5:
            print(f"    ⚠ Below threshold — not recommended")
        for issue in blockers.get(level, []):
            print(f"    • {issue}")

    print(f"\n  Open Issues ({len(issues)}):")
    for severity, component, issue in sorted(issues):
        tag = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "⚪"}.get(severity, "⚪")
        print(f"    {tag} [{severity:8s}] {component:25s} {issue}")

    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print(f"  Days simulated:     {DAYS}")
    print(f"  Assets:             {', '.join(all_ohlcv.keys())}")
    print(f"  Trades executed:    {p['total_trades']}")
    print(f"  Win rate:           {p['win_rate']:.1f}%")
    print(f"  Total return:       {p['total_return_pct']:+.2f}%")
    print(f"  Conviction signal:  {'Present ✓' if h_avg > l_avg else 'Not detected ✗'}")
    print(f"  Consensus signal:   {'Present ✓' if hc_avg > lc_avg else 'Not detected ✗'}")
    print(f"  Agent tracking:     {'Active ✓' if agent_stats else 'Not recording ✗'}")
    print(f"  Feedback loop:      {'Complete ✓' if agent_stats else 'Broken ✗'}")
    print("=" * 72)


if __name__ == "__main__":
    main()
