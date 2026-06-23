"""OSIRIS Recovery Sprint — Parameterized Experiment Harness
Run: python scripts/recovery_experiment.py [--atr 2.5] [--days 14] [--agents market,risk]
"""
import sys, json, argparse
sys.path.insert(0, ".")
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from statistics import mean, stdev, StatisticsError
from math import sqrt

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Urgency
from core.schemas.agent_schema import AgentOpinion, AgentRole, Recommendation
from core.schemas.trade_schema import TradeDirection, Trade, ExitReason
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.agents.trend_agent import TrendAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory
from core.execution.backtest_engine_v2 import BacktestEngineV2

SYMBOLS = ["BTC", "ETH", "SOL"]

# ── helpers ───────────────────────────────────────────────────────────────

def generate_events(symbol, ohlcv):
    events = []
    for i in range(1, len(ohlcv)):
        prev, curr = ohlcv[i-1], ohlcv[i]
        change = (curr["close"] - prev["close"]) / prev["close"]
        u = Urgency.HIGH if abs(change) > 0.05 else Urgency.MEDIUM if abs(change) > 0.02 else Urgency.LOW
        et = EventType.VOLUME_SPIKE if (abs(change) > 0.05 and curr["volume"] > prev["volume"] * 1.5) else EventType.PRICE_MOVEMENT
        events.append(Event(
            id=f"{symbol}_{i}", source="recovery",
            event_type=et, title=f"{symbol} {change*100:+.2f}%",
            assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO, price_at_event=curr["close"])],
            timestamp=curr["time"], detected_at=curr["time"],
            urgency=u, sentiment_score=change, confidence=0.7,
        ))
    return events

def fetch_ohlcv(days):
    fetcher = BacktestEngineV2()
    cache = {}
    for sym in SYMBOLS:
        data = fetcher.fetch_ohlcv(sym, days=days+5)
        if data and len(data) >= 50:
            cache[sym] = data
    return cache

# ── TrendAgent (Phase 4) ─────────────────────────────────────────────────



# ── Parameterized Experiment ─────────────────────────────────────────────

def run_experiment(
    days=14,
    atr_multiplier=1.5,
    use_market=True,
    use_risk=True,
    use_trend=False,
    risk_confidence_override=None,  # None = use agent's default
    market_confidence_override=None,
    track_record_alpha=0.1,
    track_record_modifier_range=0.2,  # ± range, e.g. 0.2 = 0.8-1.2
    position_size_formula="default",  # "default", "kelly"
    signal_mode="both",
):
    ohlcv_cache = fetch_ohlcv(days)
    if not ohlcv_cache:
        print("ERROR: No OHLCV data")
        return None

    # Build agents
    agents = []
    if use_market:
        market = MarketAgent(signal_mode=signal_mode)
        orig_market_fetch = market._fetch_ohlcv
        market._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
        if market_confidence_override is not None:
            orig_analyze = market.analyze
            def make_market_analyze(conf):
                def wrapped(event):
                    op = orig_analyze(event)
                    if op:
                        op.confidence = conf
                    return op
                return wrapped
            market.analyze = make_market_analyze(market_confidence_override)
        agents.append(("market_agent", market))

    if use_risk:
        risk = RiskAgent()
        risk._fetch_ohlcv = lambda s: ohlcv_cache.get(s)
        if risk_confidence_override is not None:
            orig_risk_analyze = risk.analyze
            def make_risk_analyze(conf):
                def wrapped(event):
                    op = orig_risk_analyze(event)
                    if op:
                        op.confidence = conf
                    return op
                return wrapped
            risk.analyze = make_risk_analyze(risk_confidence_override)
        agents.append(("risk_agent", risk))

    trend = TrendAgent() if use_trend else None
    if trend:
        agents.append(("trend_agent", trend))

    # Generate events
    all_events = []
    for sym, ohlcv in ohlcv_cache.items():
        all_events.extend(generate_events(sym, ohlcv))
        if trend:
            # TrendAgent needs OHLCV passed separately
            pass
    all_events.sort(key=lambda e: e.timestamp)

    # Council with custom alpha
    council = AgentCouncil()
    if track_record_alpha != 0.1:
        orig_update = council.update_track_record
        def make_update(alpha):
            def wrapped(name, correct):
                cur = council.get_track_record(name)
                council._track_record[name] = cur + alpha * (1.0 if correct else 0.0 - cur)
            return wrapped
        council.update_track_record = make_update(track_record_alpha)

    # Override track_record_modifier_range
    orig_decide = council.decide
    def make_decide(mod_range):
        def wrapped(event_id):
            result = orig_decide(event_id)
            if result and mod_range != 0.2:
                # Recalculate conviction with new modifier
                pass
            return result
        return wrapped

    perf = PerformanceMemory()
    engine = PaperTradingEngine(initial_capital=10000.0, performance_memory=perf, council=council)

    # Override stop loss sizing
    if atr_multiplier != 1.5:
        orig_process = engine.process_decision
        def make_process(atr_mul):
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
        engine.process_decision = make_process(atr_multiplier)

    price_history = {s: [] for s in SYMBOLS}
    decisions = []
    signals_count = 0

    for event in all_events:
        sym = event.assets[0].symbol
        price = event.assets[0].price_at_event
        price_history[sym].append((event.timestamp, price))

        opinions = []
        for name, agent in agents:
            if isinstance(agent, TrendAgent):
                op = agent.analyze(event, ohlcv_cache.get(sym))
            else:
                op = agent.analyze(event)
            if op:
                opinions.append(op)

        if len(opinions) < 2:
            continue

        for op in opinions:
            council.submit_opinion(op)
        decision = council.decide(event.id)
        if decision:
            decisions.append(decision)

        signal = engine.process_decision(decision)
        if signal:
            signals_count += 1
            engine.execute_signal(signal)

        current = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
        engine.check_positions(current)

    # Final check
    final = {s: (price_history[s][-1][1] if price_history[s] else 0) for s in SYMBOLS}
    engine.check_positions(final)

    # ── Results ──────────────────────────────────────────────────────

    portfolio = engine.get_portfolio_summary()
    learning = perf.get_learning_summary()

    # Agent stats
    agent_stats = {}
    for name in perf._agent_records:
        recs = perf._agent_records[name]
        wins = sum(1 for r in recs if r["correct"])
        t = len(recs)
        acc = wins / t if t > 0 else 0
        avg_c = mean(r["confidence"] for r in recs) if recs else 0
        cal = perf.get_agent_confidence_calibration(name)
        agent_stats[name] = {"total": t, "wins": wins, "accuracy": round(acc, 4),
                             "avg_confidence": round(avg_c, 3), "bias": round(cal.get("bias", 0), 3)}

    # Trade stats
    by_asset = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0.0})
    by_dir = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0.0})
    exit_reasons = defaultdict(int)
    for t in engine.closed_trades:
        pnl = t.pnl_percent or 0
        by_asset[t.signal.asset]["n"] += 1
        by_asset[t.signal.asset]["w"] += 1 if pnl > 0 else 0
        by_asset[t.signal.asset]["pnl"] += pnl
        by_dir[t.signal.direction.value]["n"] += 1
        by_dir[t.signal.direction.value]["w"] += 1 if pnl > 0 else 0
        by_dir[t.signal.direction.value]["pnl"] += pnl
        exit_reasons[t.exit_reason.value] += 1

    # Decision composition
    action_dist = defaultdict(int)
    for d in decisions:
        action_dist[d.action.value] += 1

    direction_dist = defaultdict(int)
    for d in decisions:
        dr = {"buy": "LONG", "strong_buy": "LONG", "sell": "SHORT", "strong_sell": "SHORT",
              "watch": "FLAT", "avoid": "FLAT", "hedge": "SHORT", "hold": "FLAT", "no_action": "FLAT"}
        direction_dist[direction_dist.get(d.action.value, "FLAT")] += 1

    # Council composition: agent weight distribution
    weight_samples = []
    for d in decisions[:100]:  # first 100 decisions
        aw = d.metadata.get("agent_weights", {})
        weight_samples.append(aw)

    avg_weights = defaultdict(list)
    for ws in weight_samples:
        for agent, w in ws.items():
            avg_weights[agent].append(w)

    return {
        "config": {
            "days": days, "atr_multiplier": atr_multiplier,
            "use_market": use_market, "use_risk": use_risk, "use_trend": use_trend,
            "risk_confidence": risk_confidence_override,
            "market_confidence": market_confidence_override,
            "track_record_alpha": track_record_alpha,
        },
        "portfolio": portfolio,
        "agent_stats": agent_stats,
        "trade_stats": {
            "by_asset": dict(by_asset), "by_direction": dict(by_dir),
            "exit_reasons": dict(exit_reasons),
        },
        "composition": {
            "total_decisions": len(decisions),
            "action_distribution": dict(action_dist),
            "total_signals": signals_count,
            "avg_agent_weights": {k: round(mean(v), 3) for k, v in avg_weights.items()},
        },
        "total_events": len(all_events),
    }


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--atr", type=float, default=1.5)
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--agents", type=str, default="market,risk")
    parser.add_argument("--risk-conf", type=float, default=None)
    parser.add_argument("--market-conf", type=float, default=None)
    parser.add_argument("--mode", type=str, default="both", choices=["both", "short_only", "long_only"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    agent_list = args.agents.split(",")
    result = run_experiment(
        days=args.days, atr_multiplier=args.atr,
        use_market="market" in agent_list,
        use_risk="risk" in agent_list,
        use_trend="trend" in agent_list,
        risk_confidence_override=args.risk_conf,
        market_confidence_override=args.market_conf,
        signal_mode=args.mode,
    )

    if not result:
        sys.exit(1)

    p = result["portfolio"]
    print(f"\n{'='*60}")
    print(f"  Config: ATR×{args.atr} | Agents: {args.agents}")
    if args.risk_conf is not None:
        print(f"  RiskAgent conf override: {args.risk_conf}")
    if args.market_conf is not None:
        print(f"  MarketAgent conf override: {args.market_conf}")
    print(f"{'='*60}")
    print(f"  Trades:     {p['total_trades']}")
    print(f"  Win Rate:   {p['win_rate']:.1f}%")
    print(f"  Return:     {p['total_return_pct']:+.2f}%")
    print(f"  Sharpe:     {p['sharpe_ratio']:.2f}")
    print(f"  Avg PnL:    {p['avg_pnl_pct']:+.2f}%")
    print(f"  Equity:     ${p['equity']:,.2f}")

    ts = result["trade_stats"]
    if ts["by_direction"]:
        print(f"\n  Direction:")
        for d, s in sorted(ts["by_direction"].items()):
            wr = s["w"]/s["n"]*100 if s["n"] else 0
            print(f"    {d:6s}: {s['n']:3d} trades, {wr:5.1f}% WR, PnL={s['pnl']:+7.2f}%")

    if ts["by_asset"]:
        print(f"\n  Per Asset:")
        for a, s in sorted(ts["by_asset"].items()):
            wr = s["w"]/s["n"]*100 if s["n"] else 0
            print(f"    {a:6s}: {s['n']:3d} trades, {wr:5.1f}% WR, PnL={s['pnl']:+7.2f}%")

    if ts["exit_reasons"]:
        print(f"\n  Exits:")
        for r, c in sorted(ts["exit_reasons"].items()):
            print(f"    {r}: {c}")

    if result["agent_stats"]:
        print(f"\n  Agent Stats:")
        for n, s in sorted(result["agent_stats"].items()):
            print(f"    {n:20s}: acc={s['accuracy']:.1%} conf={s['avg_confidence']:.2f} "
                  f"bias={s['bias']:+.3f} ({s['wins']}/{s['total']})")

    w = result["composition"]["avg_agent_weights"]
    if w:
        print(f"\n  Avg Vote Weights:")
        for agent, weight in sorted(w.items()):
            print(f"    {agent:20s}: {weight:.1%}")

    if args.json:
        print(json.dumps(result, indent=2, default=str))
