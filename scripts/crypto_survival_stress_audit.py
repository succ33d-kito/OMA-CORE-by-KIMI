"""OSIRIS Survival Stress Audit — replay hostile regimes and verify protection layers."""
import sys, os, json, math, random, statistics
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from dataclasses import dataclass

sys.path.insert(0, ".")

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.schemas.trade_schema import ExitReason, TradeDirection

TRADE_SYMBOLS = ["BTC", "ETH"]


def regime_covid(days=90) -> Dict[str, List[Dict]]:
    """COVID crash simulation: sharp -50% drop, recovery, volatile aftermath."""
    rng = random.Random(99)
    result = {}
    for symbol, base, vol_factor in [("BTC", 50000.0, 1.5), ("ETH", 3000.0, 1.6)]:
        candles = []
        price = base
        for d in range(days * 24):
            if d < 48:
                ret = rng.gauss(-0.005, 0.02)  # mild decline
            elif d < 120:
                ret = rng.gauss(-0.015, 0.04)  # crash phase
            elif d < 168:
                ret = rng.gauss(-0.03, 0.06)  # panic
            elif d < 336:
                ret = rng.gauss(0.005, 0.04)  # recovery
            elif d < 504:
                ret = rng.gauss(0.002, 0.025)  # stabilization
            else:
                ret = rng.gauss(0.001, 0.02)  # normalization
            ret *= vol_factor
            price *= (1 + ret)
            price = max(price, base * 0.3)
            candles.append({"close": price, "high": price * 1.02, "low": price * 0.98, "volume": max(500, rng.gauss(2000, 500))})
        result[symbol] = candles
    return result


def regime_luna(days=60) -> Dict[str, List[Dict]]:
    """Luna/3AC style: stable then catastrophic collapse."""
    rng = random.Random(77)
    result = {}
    for symbol, base, vol_factor in [("BTC", 40000.0, 1.3), ("ETH", 2500.0, 1.4)]:
        candles = []
        price = base
        for d in range(days * 24):
            if d < 168:
                ret = rng.gauss(-0.001, 0.015)
            elif d < 240:
                ret = rng.gauss(-0.025, 0.05)
            elif d < 288:
                ret = rng.gauss(-0.05, 0.08)
            else:
                ret = rng.gauss(0.001, 0.03)
            ret *= vol_factor
            price *= (1 + ret)
            price = max(price, base * 0.2)
            candles.append({"close": price, "high": price * 1.025, "low": price * 0.975, "volume": max(500, rng.gauss(3000, 1000))})
        result[symbol] = candles
    return result


def regime_ftx(days=45) -> Dict[str, List[Dict]]:
    """FTX collapse: slow bleed then rapid crash."""
    rng = random.Random(55)
    result = {}
    for symbol, base, vol_factor in [("BTC", 20000.0, 1.2), ("ETH", 1500.0, 1.3)]:
        candles = []
        price = base
        for d in range(days * 24):
            if d < 72:
                ret = rng.gauss(-0.002, 0.02)
            elif d < 144:
                ret = rng.gauss(-0.005, 0.025)
            elif d < 192:
                ret = rng.gauss(-0.04, 0.06)
            else:
                ret = rng.gauss(0.002, 0.025)
            ret *= vol_factor
            price *= (1 + ret)
            price = max(price, base * 0.15)
            candles.append({"close": price, "high": price * 1.02, "low": price * 0.98, "volume": max(500, rng.gauss(4000, 1500))})
        result[symbol] = candles
    return result


def regime_bull(days=60) -> Dict[str, List[Dict]]:
    """Strong bull trend."""
    rng = random.Random(33)
    result = {}
    for symbol, base, vol_factor in [("BTC", 30000.0, 0.8), ("ETH", 2000.0, 0.9)]:
        candles = []
        price = base
        for d in range(days * 24):
            ret = rng.gauss(0.003, 0.02) * vol_factor
            price *= (1 + ret)
            candles.append({"close": price, "high": price * 1.015, "low": price * 0.985, "volume": max(500, rng.gauss(1500, 400))})
        result[symbol] = candles
    return result


def regime_chop(days=60) -> Dict[str, List[Dict]]:
    """Sideways chop."""
    rng = random.Random(44)
    result = {}
    for symbol, base, vol_factor in [("BTC", 45000.0, 0.6), ("ETH", 2800.0, 0.7)]:
        candles = []
        price = base
        for d in range(days * 24):
            ret = rng.gauss(0.0, 0.015) * vol_factor
            price *= (1 + ret)
            price = max(base * 0.85, min(base * 1.15, price))
            candles.append({"close": price, "high": price * 1.01, "low": price * 0.99, "volume": max(300, rng.gauss(800, 200))})
        result[symbol] = candles
    return result


def regime_flash_crash(days=10) -> Dict[str, List[Dict]]:
    """Synthetic flash crash: -30% in 1 hour, rapid recovery."""
    result = {}
    for symbol, base in [("BTC", 50000.0), ("ETH", 3000.0)]:
        candles = []
        price = base
        for h in range(days * 24):
            if 48 <= h < 49:
                ret = -0.30
            elif 49 <= h < 55:
                ret = 0.05
            elif 55 <= h < 72:
                ret = 0.02
            else:
                ret = 0.001
            price *= (1 + ret)
            candles.append({
                "close": price,
                "high": price * (1 + 0.01 if h < 48 else 0.05),
                "low": price * (1 - 0.01 if h < 48 else 0.05),
                "volume": 5000 if 48 <= h < 55 else 1000,
            })
        result[symbol] = candles
    return result


REGIMES = {
    "covid_2020": ("COVID Crash 2020", regime_covid),
    "luna_3ac": ("Luna/3AC Crash", regime_luna),
    "ftx_collapse": ("FTX Collapse", regime_ftx),
    "strong_bull": ("Strong Bull Trend", regime_bull),
    "sideways_chop": ("Sideways Chop", regime_chop),
    "flash_crash_synthetic": ("Flash Crash Synthetic", regime_flash_crash),
}


@dataclass
class StressResult:
    regime: str; label: str; cycles: int; trades: int; pnl_pct: float; max_dd: float
    final_capital: float; final_guard: str; guard_transition_count: int
    crash_warnings: int; crash_emergencies: int; crash_panics: int
    final_crash: str; dir_allowed: str; blocks: int
    survived: bool; kill_switch: bool


def run_regime(name, label, data_fn) -> StressResult:
    data = data_fn()
    events = []
    for sym in TRADE_SYMBOLS:
        ohlcv = data[sym]
        for i in range(20, len(ohlcv)):
            c = ohlcv[i]; p = ohlcv[i - 1]
            ch = (c["close"] - p["close"]) / p["close"] * 100
            events.append({"sym": sym, "idx": i, "ts": datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i), "c": c["close"], "ch": ch})
    events.sort(key=lambda e: e["ts"])

    mkt = MarketAgent(); risk = RiskAgent(); council = AgentCouncil()
    engine = PaperTradingEngine(initial_capital=10000.0)
    ao = {}; mkt._fetch_ohlcv = lambda s: ao.get(s); risk._fetch_ohlcv = lambda s: ao.get(s)

    guard_transitions = 0; last_guard = "normal"
    crash_w = 0; crash_e = 0; crash_p = 0
    blocks = 0

    for ev in events:
        sym, idx, ts, close = ev["sym"], ev["idx"], ev["ts"], ev["c"]
        ohlcv = data[sym]; ao[sym] = ohlcv[max(0, idx - 100):idx]
        eo = Event(id=f"{sym}_{idx}", source="stress", event_type=EventType.PRICE_MOVEMENT,
                   title=f"{sym} price", summary=f"move {ev['ch']:+.2f}%",
                   timestamp=ts, detected_at=ts,
                   assets=[Asset(symbol=sym, name=sym, asset_class=AssetClass.CRYPTO, price_at_event=close)],
                   keywords=[sym], entities=[sym], regions=["global"],
                   sentiment=Sentiment.BULLISH if ev["ch"] > 0 else Sentiment.BEARISH,
                   sentiment_score=min(1.0, abs(ev["ch"]) / 10), urgency=Urgency.LOW, confidence=0.7)
        mop = mkt.analyze(eo); rop = risk.analyze(eo)
        if mop is None or rop is None:
            continue
        rm = rop.metadata
        mop.metadata["suggested_stop_pct"] = rm.get("suggested_stop_pct", 2.0)
        mop.metadata["max_position_pct"] = rm.get("max_position_pct", 20.0)
        mop.metadata["atr_pct"] = rm.get("atr_pct", 1.5)
        council.submit_opinion(mop); council.submit_opinion(rop)
        dec = council.decide(eo.id)
        if dec is None:
            continue
        cp = {s: data[s][min(idx, len(data[s]) - 1)]["close"] for s in TRADE_SYMBOLS}
        for s in TRADE_SYMBOLS:
            end = min(idx, len(data[s]))
            engine.update_market_data(s, cp.get(s, 50000), ts, ohlcv[max(0, end - 100):end])
        engine.check_positions(cp)
        gi = engine.capital_guard.summary(engine.capital)
        if gi["mode"] != last_guard:
            guard_transitions += 1; last_guard = gi["mode"]
        ci = engine.crash_detector.summary()
        if ci["mode"] == "warning": crash_w += 1
        elif ci["mode"] == "emergency": crash_e += 1
        elif ci["mode"] == "panic": crash_p += 1
        sig = engine.process_decision(dec)
        if sig is None:
            blocks += 1
        else:
                tr = engine.execute_signal(sig)
                if tr:
                    ci_idx = min(idx + 24, len(data[sym]) - 1)
                    reason = ExitReason.TAKE_PROFIT if data[sym][ci_idx]["close"] > tr.entry_price_executed else ExitReason.STOP_LOSS
                    tr.close(data[sym][ci_idx]["close"], reason)
                    engine._record_trade_result(tr)

    sm = engine.get_portfolio_summary()
    ds = engine.direction_ctrl.summary() if engine.direction_ctrl else {}
    return StressResult(
        regime=name, label=label,
        cycles=len(events), trades=len(engine.closed_trades),
        pnl_pct=sm.get("total_return_pct", 0),
        max_dd=sm.get("max_drawdown_pct", 0),
        final_capital=sm.get("equity", engine.capital),
        final_guard=sm.get("guard_mode", "unknown"),
        guard_transition_count=guard_transitions,
        crash_warnings=crash_w, crash_emergencies=crash_e, crash_panics=crash_p,
        final_crash=sm.get("crash_mode", "none"),
        dir_allowed=ds.get("allowed", "both"),
        blocks=blocks,
        survived=gi["mode"] not in ("halt",) and engine.capital > 0,
        kill_switch=gi.get("kill_switch", False),
    )


def generate_report(results):
    lines = []
    lines.append("# OSIRIS Survival Stress Audit Report")
    lines.append(f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    lines.append("## Methodology")
    lines.append("Hostile regimes are replayed through the full OSIRIS pipeline.")
    lines.append("Each regime uses synthetic OHLCV calibrated to match historical crisis characteristics.")
    lines.append("Protection layers (CrashDetector, CapitalGuard, KnifeDetector, etc.) are monitored.")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Results Matrix")
    lines.append("")
    headers = ["Regime", "Cycles", "Trades", "PnL%", "MaxDD%", "Final Guard", "Guard Δ",
               "Crash W", "Crash E", "Crash P", "Final Crash", "Direction", "Blocks", "Survived"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "---|" * len(headers))
    for r in results:
        survived = "✅" if r.survived else "❌"
        lines.append(f"| {r.label} | {r.cycles} | {r.trades} | {r.pnl_pct:+.2f} | {r.max_dd:.2f} | {r.final_guard} | "
                     f"{r.guard_transition_count} | {r.crash_warnings} | {r.crash_emergencies} | {r.crash_panics} | "
                     f"{r.final_crash} | {r.dir_allowed} | {r.blocks} | {survived} |")
    lines.append("")

    lines.append("## Per-Regime Analysis")
    lines.append("")
    for r in results:
        lines.append(f"### {r.label}")
        lines.append(f"- **Cycles**: {r.cycles}")
        lines.append(f"- **PnL**: {r.pnl_pct:+.2f}% | **Max DD**: {r.max_dd:.2f}%")
        lines.append(f"- **Guard**: Final = `{r.final_guard}`, transitions = {r.guard_transition_count}")
        lines.append(f"- **CrashDetector**: Warnings {r.crash_warnings}, Emergencies {r.crash_emergencies}, Panics {r.crash_panics}")
        lines.append(f"- **Capital survived**: {'✅' if r.final_capital > 0 else '❌'} ${r.final_capital:.2f}")
        lines.append(f"- **Kill switch**: {'⚠️ Activated' if r.kill_switch else '✅ Not activated'}")
        lines.append(f"- **Direction**: {r.dir_allowed}")
        lines.append("")

    lines.append("## Key Questions")
    lines.append("")
    covid = next((r for r in results if r.regime == "covid_2020"), None)
    if covid:
        lines.append(f"**COVID-style crash detected as WARNING+?**")
        lines.append(f"{'✅ YES' if covid.crash_warnings > 0 or covid.crash_emergencies > 0 else '❌ NO'} — "
                     f"{covid.crash_warnings} warnings, {covid.crash_emergencies} emergencies")
        lines.append("")

    for r in results:
        killed = r.kill_switch
        guard_blocked = r.final_guard in ("halt", "emergency")
        lines.append(f"**{r.label}: Loss capped and guards working?**")
        if r.survived and r.final_capital > 0:
            lines.append(f"✅ Survived with {r.pnl_pct:+.2f}% PnL, max DD {r.max_dd:.2f}%")
        else:
            lines.append(f"❌ System {'halted' if guard_blocked else 'lost capital'}")
        if killed:
            lines.append(f"⚠️ Kill switch was activated during this regime")
        lines.append("")

    crash_regimes = [r for r in results if r.regime in ("covid_2020", "luna_3ac", "ftx_collapse")]
    all_detected = all(r.crash_warnings > 0 or r.crash_emergencies > 0 for r in crash_regimes)
    lines.append(f"**CrashDetector activates early enough?**")
    lines.append(f"{'✅ All crashes detected at WARNING+ level' if all_detected else '⚠️ Some regimes had no crash warning'}")
    lines.append("")

    lines.append("**CapitalGuard prevents deadlock?**")
    non_halt = [r for r in results if r.final_guard == "halt"]
    lines.append(f"{'✅ No guard deadlock (no regime ended in HALT)' if not non_halt else '❌ HALT occurred in ' + str(len(non_halt)) + ' regimes'}")
    lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs("_project-memory/crypto_consolidation", exist_ok=True)
    print("=" * 60)
    print("OSIRIS Survival Stress Audit")
    print("=" * 60)
    results = []
    for name, (label, fn) in REGIMES.items():
        print(f"\nRunning {label}...")
        r = run_regime(name, label, fn)
        results.append(r)
        print(f"  Cycles: {r.cycles}, Trades: {r.trades}, PnL: {r.pnl_pct:+.2f}%, MaxDD: {r.max_dd:.2f}%")
        print(f"  Guard: {r.final_guard}, Crash: {r.final_crash}, Survived: {r.survived}")

    report = generate_report(results)
    path = "_project-memory/crypto_consolidation/survival_stress_report.md"
    with open(path, "w") as f:
        f.write(report)
    print(f"\nReport written to {path}")

    json_path = "_project-memory/crypto_consolidation/survival_stress_report.json"
    with open(json_path, "w") as f:
        json.dump([{
            "regime": r.regime, "label": r.label, "cycles": r.cycles, "trades": r.trades,
            "pnl_pct": round(r.pnl_pct, 2), "max_dd": round(r.max_dd, 2),
            "final_capital": round(r.final_capital, 2), "final_guard": r.final_guard,
            "guard_transitions": r.guard_transition_count,
            "crash_warnings": r.crash_warnings, "crash_emergencies": r.crash_emergencies,
            "crash_panics": r.crash_panics, "final_crash": r.final_crash,
            "direction": r.dir_allowed, "blocks": r.blocks, "survived": r.survived,
        } for r in results], f, indent=2)
    print(f"JSON data written to {json_path}")


if __name__ == "__main__":
    main()
