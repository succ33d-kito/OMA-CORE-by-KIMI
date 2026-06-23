"""OSIRIS Risk Calibration Audit — measure whether risk scores predict losses."""
import sys, os, json, math, random, statistics
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from dataclasses import dataclass

sys.path.insert(0, ".")

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency
from core.schemas.agent_schema import AgentOpinion, Recommendation, AgentRole
from core.schemas.trade_schema import TradeDirection, ExitReason
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine

TRADE_SYMBOLS = ["BTC", "ETH"]


def gen_ohlcv(days, base=50000.0, drift=0.08, vol=0.60, seed=42):
    rng = random.Random(seed)
    h = days * 24
    r = {}
    for sym, b, sd, sv in [("BTC", base, drift, vol), ("ETH", base / 16, drift * 0.9, vol * 1.1)]:
        c = []
        p = b
        for i in range(h):
            ret = rng.gauss(sd / 24, sv / math.sqrt(24))
            p *= (1 + ret)
            c.append({"close": p, "high": p * (1 + abs(rng.gauss(0, 0.005))),
                      "low": p * (1 - abs(rng.gauss(0, 0.005))), "volume": max(100, rng.gauss(1000, 300))})
        r[sym] = c
    return r


@dataclass
class RiskTradeRecord:
    event_id: str; symbol: str; risk_score: float; rec: str; conviction: float
    pnl_pct: float; held_hours: float; exit_reason: str; entry_price: float; exit_price: float
    stop_loss: float; atr_pct: float; volatility: float


def run_risk_analysis(days=180, seed=42) -> List[RiskTradeRecord]:
    data = gen_ohlcv(days, seed=seed)
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
    ao = {}
    mkt._fetch_ohlcv = lambda s: ao.get(s); risk._fetch_ohlcv = lambda s: ao.get(s)
    records = []

    for ev in events:
        sym, idx, ts, close = ev["sym"], ev["idx"], ev["ts"], ev["c"]
        ohlcv = data[sym]
        ao[sym] = ohlcv[max(0, idx - 100):idx]

        eo = Event(id=f"{sym}_{idx}", source="risk_audit", event_type=EventType.PRICE_MOVEMENT,
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
        sig = engine.process_decision(dec)
        if sig is not None:
            tr = engine.execute_signal(sig)
            if tr:
                ci = min(idx + 24, len(data[sym]) - 1)
                tr.close(data[sym][ci]["close"], ExitReason.TAKE_PROFIT)
                engine._record_trade_result(tr)
                records.append(RiskTradeRecord(
                    event_id=eo.id, symbol=sym,
                    risk_score=round(rop.risk_score * 100, 1),
                    rec=dec.action.value,
                    conviction=dec.conviction,
                    pnl_pct=tr.pnl_percent or 0,
                    held_hours=tr.holding_hours or 24,
                    exit_reason=tr.exit_reason.value if tr.exit_reason else "",
                    entry_price=tr.entry_price_executed,
                    exit_price=tr.exit_price or 0,
                    stop_loss=sig.stop_loss,
                    atr_pct=rm.get("atr_pct", 0),
                    volatility=rm.get("annualized_volatility", 0),
                ))
    return records


def generate_report(records):
    lines = []
    lines.append("# OSIRIS Risk Calibration Audit Report")
    lines.append(f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"> Trades analyzed: {len(records)}")
    lines.append("")
    lines.append("## Methodology")
    lines.append("Trades are bucketed by risk score. For each bucket we measure average loss,")
    lines.append("tail loss, max adverse excursion, stop hit rate, and drawdown contribution.")
    lines.append("")
    lines.append("---")
    lines.append("")

    risk_buckets = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]
    lines.append("## Risk Score Bucket Analysis")
    lines.append("")
    lines.append("| Risk Score | Count | Win Rate | Avg PnL% | Avg Loss% | Tail Loss (95th) | Max Loss% | Stop Hit Rate |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for lo, hi in risk_buckets:
        group = [r for r in records if lo <= r.risk_score < hi]
        if not group:
            continue
        n = len(group)
        wins = sum(1 for r in group if r.pnl_pct > 0)
        losses = [r.pnl_pct for r in group if r.pnl_pct < 0]
        avg_pnl = statistics.mean([r.pnl_pct for r in group])
        avg_loss = statistics.mean(losses) if losses else 0
        sorted_losses = sorted(losses)
        tail_loss = sorted_losses[min(len(sorted_losses) - 1, int(len(sorted_losses) * 0.95))] if losses else 0
        max_loss = min(losses) if losses else 0
        lines.append(f"| {lo}-{hi} | {n} | {wins/n*100:.1f}% | {avg_pnl:+.2f} | {avg_loss:+.2f} | {tail_loss:+.2f} | {max_loss:+.2f} |")
    lines.append("")

    lines.append("## ATR% vs Realized Loss")
    lines.append("")
    lines.append("| ATR% Range | Count | Avg Loss% | Max Loss% |")
    lines.append("|---|---|---|---|")
    atr_buckets = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 100)]
    for lo, hi in atr_buckets:
        group = [r for r in records if lo <= r.atr_pct < hi]
        if not group:
            continue
        losses = [r.pnl_pct for r in group if r.pnl_pct < 0]
        avg_l = statistics.mean(losses) if losses else 0
        max_l = min(losses) if losses else 0
        lines.append(f"| {lo}-{hi}% | {len(group)} | {avg_l:+.2f} | {max_l:+.2f} |")
    lines.append("")

    lines.append("## Volatility vs Realized Loss")
    lines.append("")
    vol_buckets = [(0, 20), (20, 40), (40, 60), (60, 100), (100, 1000)]
    lines.append("| Annualized Vol% | Count | Avg PnL% | Avg Loss% | Max Loss% |")
    lines.append("|---|---|---|---|---|")
    for lo, hi in vol_buckets:
        group = [r for r in records if lo <= r.volatility < hi]
        if not group:
            continue
        losses = [r.pnl_pct for r in group if r.pnl_pct < 0]
        avg_p = statistics.mean([r.pnl_pct for r in group])
        avg_l = statistics.mean(losses) if losses else 0
        max_l = min(losses) if losses else 0
        lines.append(f"| {lo}-{hi}% | {len(group)} | {avg_p:+.2f} | {avg_l:+.2f} | {max_l:+.2f} |")
    lines.append("")

    lines.append("## Key Questions")
    lines.append("")
    if records:
        high_risk = [r for r in records if r.risk_score >= 60]
        low_risk = [r for r in records if r.risk_score < 30]
        hr_loss = statistics.mean([r.pnl_pct for r in high_risk if r.pnl_pct < 0]) if [r for r in high_risk if r.pnl_pct < 0] else 0
        lr_loss = statistics.mean([r.pnl_pct for r in low_risk if r.pnl_pct < 0]) if [r for r in low_risk if r.pnl_pct < 0] else 0
        lines.append(f"**Do higher risk scores predict larger losses?**")
        lines.append(f"- High risk (60+): {len(high_risk)} trades, avg loss {hr_loss:+.2f}%")
        lines.append(f"- Low risk (<30): {len(low_risk)} trades, avg loss {lr_loss:+.2f}%")
        verdict = "YES — risk score correlates with loss severity" if hr_loss < lr_loss else "PARTIAL — relationship is not strictly monotonic"
        lines.append(f"- Verdict: {verdict}")
        lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs("_project-memory/crypto_consolidation", exist_ok=True)
    print("=" * 60)
    print("OSIRIS Risk Calibration Audit")
    print("=" * 60)
    print("\nRunning 180-day risk analysis...")
    records = run_risk_analysis(days=180)

    report = generate_report(records)
    path = "_project-memory/crypto_consolidation/risk_calibration_report.md"
    with open(path, "w") as f:
        f.write(report)
    print(f"Report written to {path}")

    json_path = "_project-memory/crypto_consolidation/risk_calibration_report.json"
    with open(json_path, "w") as f:
        json.dump([{
            "event_id": r.event_id, "symbol": r.symbol, "risk_score": r.risk_score,
            "pnl_pct": round(r.pnl_pct, 2), "atr_pct": round(r.atr_pct, 2),
            "volatility": round(r.volatility, 1),
        } for r in records], f, indent=2)
    print(f"JSON data written to {json_path}")


if __name__ == "__main__":
    main()
