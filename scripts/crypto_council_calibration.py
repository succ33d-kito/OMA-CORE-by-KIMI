"""OSIRIS Council Calibration Audit — measure whether council scores are meaningful."""
import sys, os, json, math, random, statistics
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from dataclasses import dataclass

sys.path.insert(0, ".")

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency
from core.schemas.agent_schema import AgentOpinion, Recommendation, AgentRole, CouncilTier
from core.schemas.trade_schema import TradeSignal, TradeDirection, ExitReason
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory

TRADE_SYMBOLS = ["BTC", "ETH"]


def generate_ohlcv(days, base_price=50000.0, drift=0.08, vol=0.60, seed=42):
    rng = random.Random(seed)
    hours = days * 24
    result = {}
    for symbol, base, sd, sv in [
        ("BTC", base_price, drift, vol),
        ("ETH", base_price / 16, drift * 0.9, vol * 1.1),
    ]:
        candles = []
        price = base
        for h in range(hours):
            ret = rng.gauss(sd / 24, sv / math.sqrt(24))
            price *= (1 + ret)
            high = price * (1 + abs(rng.gauss(0, sv / math.sqrt(24) * 0.5)))
            low = price * (1 - abs(rng.gauss(0, sv / math.sqrt(24) * 0.5)))
            volume = max(100, rng.gauss(1000, 300))
            candles.append({"close": price, "high": high, "low": low, "volume": volume})
        result[symbol] = candles
    return result


@dataclass
class CouncilTradeRecord:
    event_id: str
    symbol: str
    recommendation: str
    conviction: float
    consensus_score: float
    disagreement_score: float
    market_confidence: float
    risk_confidence: float
    direction: str
    pnl_pct: float
    held_hours: float
    exit_reason: str


def run_council_analysis(days=180, seed=42) -> List[CouncilTradeRecord]:
    data = generate_ohlcv(days, seed=seed)
    forward_prices = {}
    for sym in TRADE_SYMBOLS:
        ohlcv = data[sym]
        fp = {}
        for i in range(len(ohlcv)):
            fp[i] = {}
            for fwd in [24, 48, 72]:
                idx = min(i + fwd, len(ohlcv) - 1)
                fp[i][fwd] = ohlcv[idx]["close"]
        forward_prices[sym] = fp

    events = []
    for sym in TRADE_SYMBOLS:
        ohlcv = data[sym]
        for i in range(20, len(ohlcv)):
            c = ohlcv[i]
            prev = ohlcv[i - 1]
            change = (c["close"] - prev["close"]) / prev["close"] * 100
            events.append({"symbol": sym, "idx": i, "ts": datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i), "close": c["close"], "change": change})
    events.sort(key=lambda e: e["ts"])

    mkt = MarketAgent()
    risk = RiskAgent()
    council = AgentCouncil()
    engine = PaperTradingEngine(initial_capital=10000.0)

    agent_ohlcv = {}
    mkt._fetch_ohlcv = lambda s: agent_ohlcv.get(s)
    risk._fetch_ohlcv = lambda s: agent_ohlcv.get(s)

    records = []

    for ev in events:
        sym = ev["symbol"]
        idx = ev["idx"]
        ohlcv = data[sym]
        start = max(0, idx - 100)
        agent_ohlcv[sym] = ohlcv[start:idx]

        event_obj = Event(
            id=f"{sym}_{idx}", source="council_audit",
            event_type=EventType.PRICE_MOVEMENT,
            title=f"{sym} price",
            summary=f"move {ev['change']:+.2f}%",
            timestamp=ev["ts"], detected_at=ev["ts"],
            assets=[Asset(symbol=sym, name=sym, asset_class=AssetClass.CRYPTO, price_at_event=ev["close"])],
            keywords=[sym], entities=[sym], regions=["global"],
            sentiment=Sentiment.BULLISH if ev["change"] > 0 else Sentiment.BEARISH,
            sentiment_score=min(1.0, abs(ev["change"]) / 10),
            urgency=Urgency.LOW, confidence=0.7,
        )

        mop = mkt.analyze(event_obj)
        rop = risk.analyze(event_obj)
        if mop is None or rop is None:
            continue

        rop_meta = rop.metadata
        mop.metadata["suggested_stop_pct"] = rop_meta.get("suggested_stop_pct", 2.0)
        mop.metadata["max_position_pct"] = rop_meta.get("max_position_pct", 20.0)
        mop.metadata["atr_pct"] = rop_meta.get("atr_pct", 1.5)

        council.submit_opinion(mop)
        council.submit_opinion(rop)
        decision = council.decide(event_obj.id)
        if decision is None:
            continue

        current_prices = {sym: data[sym][min(idx, len(data[sym]) - 1)]["close"] for sym in TRADE_SYMBOLS}
        for s in TRADE_SYMBOLS:
            end = min(idx, len(data[s]))
            win = data[s][max(0, end - 100):end]
            engine.update_market_data(s, current_prices.get(s, 50000), timestamp=ev["ts"], ohlcv_history=win)

        engine.check_positions(current_prices)
        signal = engine.process_decision(decision)
        if signal is not None:
            trade = engine.execute_signal(signal)
            if trade:
                # Close after 24h simulated
                close_idx = min(idx + 24, len(data[sym]) - 1)
                close_price = data[sym][close_idx]["close"]
                trade.close(close_price, ExitReason.TAKE_PROFIT if close_price > trade.entry_price_executed else ExitReason.STOP_LOSS)
                engine._record_trade_result(trade)
                records.append(CouncilTradeRecord(
                    event_id=event_obj.id,
                    symbol=sym,
                    recommendation=decision.action.value,
                    conviction=decision.conviction,
                    consensus_score=decision.consensus_score,
                    disagreement_score=decision.disagreement_score,
                    market_confidence=mop.confidence,
                    risk_confidence=rop.confidence,
                    direction=trade.signal.direction.value,
                    pnl_pct=trade.pnl_percent or 0,
                    held_hours=trade.holding_hours or 24,
                    exit_reason=trade.exit_reason.value if trade.exit_reason else "unknown",
                ))
    return records


def generate_report(records: List[CouncilTradeRecord]) -> str:
    lines = []
    lines.append("# OSIRIS Council Calibration Audit Report")
    lines.append(f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"> Trades analyzed: {len(records)}")
    lines.append("")
    lines.append("## Methodology")
    lines.append("Trades are bucketed by conviction, consensus score, disagreement score, and direction.")
    lines.append("For each bucket we measure: win rate, average PnL, profit factor, and forward return.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Conviction buckets
    lines.append("## Conviction Bucket Analysis")
    lines.append("")
    conv_buckets = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]
    lines.append("| Conviction | Count | Win Rate | Avg PnL% | Median PnL% | Profit Factor |")
    lines.append("|---|---|---|---|---|---|")
    for lo, hi in conv_buckets:
        group = [r for r in records if lo <= r.conviction < hi]
        if not group:
            continue
        wins = sum(1 for r in group if r.pnl_pct > 0)
        n = len(group)
        avg = statistics.mean([r.pnl_pct for r in group])
        med = statistics.median([r.pnl_pct for r in group])
        gross_win = sum(r.pnl_pct for r in group if r.pnl_pct > 0)
        gross_loss = abs(sum(r.pnl_pct for r in group if r.pnl_pct < 0))
        pf = gross_win / max(gross_loss, 0.01)
        lines.append(f"| {lo}-{hi} | {n} | {wins/n*100:.1f}% | {avg:+.2f} | {med:+.2f} | {pf:.2f} |")
    lines.append("")

    # Consensus buckets
    lines.append("## Consensus Score Bucket Analysis")
    lines.append("")
    cs_buckets = [(0, 0.5), (0.5, 0.7), (0.7, 0.85), (0.85, 1.01)]
    lines.append("| Consensus | Count | Win Rate | Avg PnL% | Profit Factor |")
    lines.append("|---|---|---|---|---|")
    for lo, hi in cs_buckets:
        group = [r for r in records if lo <= r.consensus_score < hi]
        if not group:
            continue
        wins = sum(1 for r in group if r.pnl_pct > 0)
        n = len(group)
        avg = statistics.mean([r.pnl_pct for r in group])
        gw = sum(r.pnl_pct for r in group if r.pnl_pct > 0)
        gl = abs(sum(r.pnl_pct for r in group if r.pnl_pct < 0))
        pf = gw / max(gl, 0.01)
        lines.append(f"| {lo}-{hi} | {n} | {wins/n*100:.1f}% | {avg:+.2f} | {pf:.2f} |")
    lines.append("")

    # Disagreement buckets
    lines.append("## Disagreement Score Bucket Analysis")
    lines.append("")
    ds_buckets = [(0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 1.0)]
    lines.append("| Disagreement | Count | Win Rate | Avg PnL% | Profit Factor |")
    lines.append("|---|---|---|---|---|")
    for lo, hi in ds_buckets:
        group = [r for r in records if lo <= r.disagreement_score < hi]
        if not group:
            continue
        wins = sum(1 for r in group if r.pnl_pct > 0)
        n = len(group)
        avg = statistics.mean([r.pnl_pct for r in group])
        gw = sum(r.pnl_pct for r in group if r.pnl_pct > 0)
        gl = abs(sum(r.pnl_pct for r in group if r.pnl_pct < 0))
        pf = gw / max(gl, 0.01)
        lines.append(f"| {lo}-{hi} | {n} | {wins/n*100:.1f}% | {avg:+.2f} | {pf:.2f} |")
    lines.append("")

    # Direction analysis
    lines.append("## Conviction by Direction")
    lines.append("")
    for direction in ["long", "short"]:
        group = [r for r in records if r.direction == direction]
        if not group:
            continue
        lines.append(f"### {direction.upper()}")
        lines.append("| Conviction | Count | Win Rate | Avg PnL% |")
        lines.append("|---|---|---|---|")
        for lo, hi in conv_buckets:
            sub = [r for r in group if lo <= r.conviction < hi]
            if not sub:
                continue
            wins = sum(1 for r in sub if r.pnl_pct > 0)
            avg = statistics.mean([r.pnl_pct for r in sub])
            lines.append(f"| {lo}-{hi} | {len(sub)} | {wins/len(sub)*100:.1f}% | {avg:+.2f} |")
        lines.append("")

    # Agent confidence analysis
    lines.append("## MarketAgent Confidence vs Outcome")
    lines.append("")
    mc_buckets = [(0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.85)]
    lines.append("| Mkt Confidence | Count | Win Rate | Avg PnL% |")
    lines.append("|---|---|---|---|")
    for lo, hi in mc_buckets:
        group = [r for r in records if lo <= r.market_confidence < hi]
        if not group:
            continue
        wins = sum(1 for r in group if r.pnl_pct > 0)
        avg = statistics.mean([r.pnl_pct for r in group])
        lines.append(f"| {lo}-{hi} | {len(group)} | {wins/len(group)*100:.1f}% | {avg:+.2f} |")
    lines.append("")

    lines.append("## RiskAgent Confidence vs Outcome")
    lines.append("")
    lines.append("| Risk Confidence | Count | Win Rate | Avg PnL% |")
    lines.append("|---|---|---|---|")
    for lo, hi in mc_buckets:
        group = [r for r in records if lo <= r.risk_confidence < hi]
        if not group:
            continue
        wins = sum(1 for r in group if r.pnl_pct > 0)
        avg = statistics.mean([r.pnl_pct for r in group])
        lines.append(f"| {lo}-{hi} | {len(group)} | {wins/len(group)*100:.1f}% | {avg:+.2f} |")
    lines.append("")

    # Key questions
    lines.append("## Key Questions")
    lines.append("")

    if records:
        high_conv = [r for r in records if r.conviction >= 60]
        low_conv = [r for r in records if r.conviction < 40]
        high_wr = sum(1 for r in high_conv if r.pnl_pct > 0) / max(len(high_conv), 1) * 100
        low_wr = sum(1 for r in low_conv if r.pnl_pct > 0) / max(len(low_conv), 1) * 100
        lines.append(f"**Does high conviction outperform low conviction?**")
        lines.append(f"- High conviction (60+): {len(high_conv)} trades, {high_wr:.1f}% win rate")
        lines.append(f"- Low conviction (<40): {len(low_conv)} trades, {low_wr:.1f}% win rate")
        lines.append(f"- Verdict: {'YES — conviction is informative' if high_wr > low_wr else 'WEAK — conviction does not strongly differentiate'}")
        lines.append("")

        high_cs = [r for r in records if r.consensus_score >= 0.8]
        low_cs = [r for r in records if r.consensus_score < 0.6]
        if high_cs and low_cs:
            hcs_wr = sum(1 for r in high_cs if r.pnl_pct > 0) / len(high_cs) * 100
            lcs_wr = sum(1 for r in low_cs if r.pnl_pct > 0) / len(low_cs) * 100
            lines.append(f"**Does consensus correlate with better outcomes?**")
            lines.append(f"- High consensus (0.8+): {len(high_cs)} trades, {hcs_wr:.1f}% win rate")
            lines.append(f"- Low consensus (<0.6): {len(low_cs)} trades, {lcs_wr:.1f}% win rate")
            lines.append(f"- Verdict: {'YES' if hcs_wr > lcs_wr else 'NO — consensus does not predict better outcomes'}")
            lines.append("")

        high_ds = [r for r in records if r.disagreement_score >= 0.2]
        low_ds = [r for r in records if r.disagreement_score < 0.1]
        if high_ds and low_ds:
            hds_wr = sum(1 for r in high_ds if r.pnl_pct > 0) / len(high_ds) * 100
            lds_wr = sum(1 for r in low_ds if r.pnl_pct > 0) / len(low_ds) * 100
            lines.append(f"**Does disagreement warn of lower-quality trades?**")
            lines.append(f"- High disagreement (0.2+): {len(high_ds)} trades, {hds_wr:.1f}% win rate")
            lines.append(f"- Low disagreement (<0.1): {len(low_ds)} trades, {lds_wr:.1f}% win rate")
            lines.append(f"- Verdict: {'YES — disagreement is a useful warning' if hds_wr < lds_wr else 'WEAK — disagreement does not consistently indicate lower quality'}")
            lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs("_project-memory/crypto_consolidation", exist_ok=True)
    print("=" * 60)
    print("OSIRIS Council Calibration Audit")
    print("=" * 60)
    print("\nRunning 180-day council analysis...")
    records = run_council_analysis(days=180)

    report = generate_report(records)
    path = "_project-memory/crypto_consolidation/council_calibration_report.md"
    with open(path, "w") as f:
        f.write(report)
    print(f"Report written to {path}")

    json_path = "_project-memory/crypto_consolidation/council_calibration_report.json"
    with open(json_path, "w") as f:
        json.dump([{
            "event_id": r.event_id,
            "symbol": r.symbol,
            "recommendation": r.recommendation,
            "conviction": round(r.conviction, 1),
            "consensus_score": round(r.consensus_score, 3),
            "disagreement_score": round(r.disagreement_score, 3),
            "direction": r.direction,
            "pnl_pct": round(r.pnl_pct, 2),
        } for r in records], f, indent=2)
    print(f"JSON data written to {json_path}")


if __name__ == "__main__":
    main()
