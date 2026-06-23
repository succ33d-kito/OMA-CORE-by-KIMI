"""OSIRIS Crypto Signal Quality Audit — evaluate whether signals have directional value."""
import sys, os, json, math, random, statistics
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from dataclasses import dataclass

sys.path.insert(0, ".")

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Sentiment, Urgency
from core.schemas.agent_schema import AgentOpinion, Recommendation, AgentRole, CouncilTier
from core.schemas.trade_schema import TradeSignal, TradeDirection
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory

TRADE_SYMBOLS = ["BTC", "ETH"]


def generate_ohlcv(days: int, base_price: float, drift: float, vol: float,
                   seed: int = 42) -> Dict[str, List[Dict]]:
    rng = random.Random(seed)
    hours = days * 24
    result = {}
    for symbol, base, sym_drift, sym_vol in [
        ("BTC", base_price, drift, vol),
        ("ETH", base_price / 16, drift * 0.9, vol * 1.1),
    ]:
        candles = []
        price = base
        for h in range(hours):
            ret = rng.gauss(sym_drift / 24, sym_vol / math.sqrt(24))
            price *= (1 + ret)
            high = price * (1 + abs(rng.gauss(0, sym_vol / math.sqrt(24) * 0.5)))
            low = price * (1 - abs(rng.gauss(0, sym_vol / math.sqrt(24) * 0.5)))
            volume = max(100, rng.gauss(1000, 300))
            candles.append({"close": price, "high": high, "low": low, "volume": volume})
        result[symbol] = candles
    return result


@dataclass
class SignalRecord:
    event_id: str
    symbol: str
    timestamp: datetime
    recommendation: str
    conviction: float
    consensus_score: float
    risk_score: float
    price_at_signal: float
    forward_returns: Dict[int, float]


def run_signal_analysis(days: int = 180, seed: int = 42) -> List[SignalRecord]:
    data = generate_ohlcv(days, 50000.0, 0.08, 0.60, seed)
    records = []

    events = []
    for sym in TRADE_SYMBOLS:
        ohlcv = data[sym]
        for i in range(20, len(ohlcv)):
            c = ohlcv[i]
            prev = ohlcv[i - 1]
            change_pct = (c["close"] - prev["close"]) / prev["close"] * 100
            events.append({
                "symbol": sym,
                "index": i,
                "timestamp": datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i),
                "close": c["close"],
                "change_pct": change_pct,
            })
    events.sort(key=lambda e: e["timestamp"])

    mkt_agent = MarketAgent()
    risk_agent = RiskAgent()
    council = AgentCouncil()
    engine = PaperTradingEngine(initial_capital=10000.0)

    agent_ohlcv: Dict[str, List[Dict]] = {}
    mkt_agent._fetch_ohlcv = lambda s: agent_ohlcv.get(s)
    risk_agent._fetch_ohlcv = lambda s: agent_ohlcv.get(s)

    # Pre-compute forward prices for each event index
    forward_prices: Dict[str, Dict[int, Dict[int, float]]] = {}
    for sym in TRADE_SYMBOLS:
        ohlcv = data[sym]
        fp = {}
        for i in range(len(ohlcv)):
            fp[i] = {}
            for fwd_hours in [6, 12, 24, 48, 72]:
                fwd_idx = min(i + fwd_hours, len(ohlcv) - 1)
                fp[i][fwd_hours] = ohlcv[fwd_idx]["close"]
        forward_prices[sym] = fp

    for ev in events:
        sym = ev["symbol"]
        idx = ev["index"]
        ohlcv = data[sym]
        start = max(0, idx - 100)
        window = ohlcv[start:idx]
        agent_ohlcv[sym] = window

        event_obj = Event(
            id=f"{sym}_{idx}",
            source="signal_audit",
            event_type=EventType.PRICE_MOVEMENT,
            title=f"{sym} price movement",
            summary=f"{sym} moved {ev['change_pct']:+.2f}%",
            timestamp=ev["timestamp"],
            detected_at=ev["timestamp"],
            assets=[Asset(symbol=sym, name=sym, asset_class=AssetClass.CRYPTO,
                          price_at_event=ev["close"])],
            keywords=[sym],
            entities=[sym],
            regions=["global"],
            sentiment=Sentiment.BULLISH if ev["change_pct"] > 0 else Sentiment.BEARISH,
            sentiment_score=min(1.0, abs(ev["change_pct"]) / 10),
            urgency=Urgency.LOW,
            confidence=0.7,
        )

        market_op = mkt_agent.analyze(event_obj)
        risk_op = risk_agent.analyze(event_obj)
        if market_op is None or risk_op is None:
            continue

        risk_meta = risk_op.metadata
        market_op.metadata["suggested_stop_pct"] = risk_meta.get("suggested_stop_pct", 2.0)
        market_op.metadata["max_position_pct"] = risk_meta.get("max_position_pct", 20.0)
        market_op.metadata["atr_pct"] = risk_meta.get("atr_pct", 1.5)

        council.submit_opinion(market_op)
        council.submit_opinion(risk_op)
        decision = council.decide(event_obj.id)
        if decision is None:
            continue

        rec = decision.action.value
        if rec in ("buy", "sell", "strong_buy", "strong_sell", "hedge"):
            fwd_returns = {}
            for fwd_hours in [6, 12, 24, 48, 72]:
                fwd_price = forward_prices[sym][idx][fwd_hours]
                ret = (fwd_price - ev["close"]) / ev["close"] * 100
                fwd_returns[fwd_hours] = round(ret, 2)

            records.append(SignalRecord(
                event_id=event_obj.id,
                symbol=sym,
                timestamp=ev["timestamp"],
                recommendation=rec,
                conviction=decision.conviction,
                consensus_score=decision.consensus_score,
                risk_score=risk_op.risk_score if risk_op else 0.5,
                price_at_signal=ev["close"],
                forward_returns=fwd_returns,
            ))

    return records


def classify_direction(rec: str) -> str:
    if rec in ("buy", "strong_buy"):
        return "LONG"
    if rec in ("sell", "strong_sell", "hedge"):
        return "SHORT"
    return "FLAT"


def directional_accuracy(rec: str, fwd_return: float) -> bool:
    dir = classify_direction(rec)
    if dir == "LONG":
        return fwd_return > 0
    if dir == "SHORT":
        return fwd_return < 0
    return False


def generate_report(records: List[SignalRecord]) -> str:
    lines = []
    lines.append("# OSIRIS Crypto Signal Quality Audit Report")
    lines.append(f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"> Signals analyzed: {len(records)}")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("Each signal's recommendation is compared against forward price movement")
    lines.append("at 6h, 12h, 24h, 48h, and 72h horizons. Directional accuracy measures")
    lines.append("whether the market moved in the predicted direction.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Overall Signal Distribution")
    lines.append("")

    rec_counts = defaultdict(int)
    for r in records:
        rec_counts[r.recommendation] += 1
    lines.append("| Recommendation | Count | % of Total |")
    lines.append("|---|---|---|")
    total = len(records)
    for rec, count in sorted(rec_counts.items()):
        lines.append(f"| {rec} | {count} | {count/total*100:.1f}% |")
    lines.append("")

    lines.append("## Directional Accuracy by Horizon")
    lines.append("")
    lines.append("| Horizon | Signals | Correct | Wrong | Accuracy % | Avg Fwd Return % | Median Fwd Return % |")
    lines.append("|---|---|---|---|---|---|---|")
    for fwd_hours in [6, 12, 24, 48, 72]:
        n = len(records)
        correct = sum(1 for r in records if directional_accuracy(r.recommendation, r.forward_returns.get(fwd_hours, 0)))
        returns = [r.forward_returns.get(fwd_hours, 0) for r in records]
        avg_ret = statistics.mean(returns) if returns else 0
        med_ret = statistics.median(returns) if returns else 0
        lines.append(f"| {fwd_hours}h | {n} | {correct} | {n-correct} | {correct/n*100:.1f}% | {avg_ret:+.2f} | {med_ret:+.2f} |")
    lines.append("")

    lines.append("## Directional Accuracy by Recommendation")
    lines.append("")
    lines.append("| Rec | Count | 6h Acc% | 12h Acc% | 24h Acc% | 48h Acc% | 72h Acc% |")
    lines.append("|---|---|---|---|---|---|---|")
    for rec in ["buy", "sell", "hedge", "strong_buy", "strong_sell"]:
        group = [r for r in records if r.recommendation == rec]
        if not group:
            continue
        row = f"| {rec} | {len(group)} |"
        for fwd_hours in [6, 12, 24, 48, 72]:
            correct = sum(1 for r in group if directional_accuracy(r.recommendation, r.forward_returns[fwd_hours]))
            row += f" {correct/len(group)*100:.1f}% |"
        lines.append(row)
    lines.append("")

    lines.append("## Outcome by Asset")
    lines.append("")
    for sym in ["BTC", "ETH"]:
        group = [r for r in records if r.symbol == sym]
        if not group:
            continue
        lines.append(f"### {sym}")
        lines.append(f"| Horizon | Signals | Accuracy % | Avg Return % |")
        lines.append(f"|---|---|---|---|")
        for fwd_hours in [6, 12, 24, 48, 72]:
            correct = sum(1 for r in group if directional_accuracy(r.recommendation, r.forward_returns[fwd_hours]))
            returns = [r.forward_returns[fwd_hours] for r in group]
            avg = statistics.mean(returns)
            lines.append(f"| {fwd_hours}h | {len(group)} | {correct/len(group)*100:.1f}% | {avg:+.2f} |")
        lines.append("")

    lines.append("## Conviction vs Outcome")
    lines.append("")
    conviction_buckets = [(0, 40), (40, 60), (60, 80), (80, 101)]
    lines.append("| Conviction | Count | 24h Acc% | 24h Avg Ret% |")
    lines.append("|---|---|---|---|")
    for lo, hi in conviction_buckets:
        group = [r for r in records if lo <= r.conviction < hi]
        if not group:
            continue
        correct = sum(1 for r in group if directional_accuracy(r.recommendation, r.forward_returns.get(24, 0)))
        returns = [r.forward_returns.get(24, 0) for r in group]
        avg = statistics.mean(returns) if returns else 0
        lines.append(f"| {lo}-{hi} | {len(group)} | {correct/len(group)*100:.1f}% | {avg:+.2f} |")
    lines.append("")

    lines.append("## Consensus Score vs Outcome")
    lines.append("")
    consensus_buckets = [(0, 0.5), (0.5, 0.7), (0.7, 0.85), (0.85, 1.01)]
    lines.append("| Consensus | Count | 24h Acc% | 24h Avg Ret% |")
    lines.append("|---|---|---|---|")
    for lo, hi in consensus_buckets:
        group = [r for r in records if lo <= r.consensus_score < hi]
        if not group:
            continue
        correct = sum(1 for r in group if directional_accuracy(r.recommendation, r.forward_returns.get(24, 0)))
        returns = [r.forward_returns.get(24, 0) for r in group]
        avg = statistics.mean(returns) if returns else 0
        lines.append(f"| {lo}-{hi} | {len(group)} | {correct/len(group)*100:.1f}% | {avg:+.2f} |")
    lines.append("")

    lines.append("## Best/Worst Signals")
    lines.append("")
    for fwd_hours in [24, 72]:
        scored = [(r, r.forward_returns[fwd_hours]) for r in records]
        scored.sort(key=lambda x: x[1])
        lines.append(f"### {fwd_hours}h Forward")
        lines.append(f"- Best: {scored[-1][0].event_id} — {scored[-1][1]:+.2f}% ({scored[-1][0].recommendation} @ {scored[-1][0].conviction:.0f} conf)")
        lines.append(f"- Worst: {scored[0][0].event_id} — {scored[0][1]:+.2f}% ({scored[0][0].recommendation} @ {scored[0][0].conviction:.0f} conf)")
        lines.append("")

    lines.append("## False Positive / Negative Analysis")
    lines.append("")
    fp_fn = {"FP_BUY": 0, "FN_BUY": 0, "FP_SELL": 0, "FN_SELL": 0, "FP_HEDGE": 0, "FN_HEDGE": 0}
    for r in records:
        for fwd_hours in [24]:
            ret = r.forward_returns.get(fwd_hours, 0)
            if r.recommendation in ("buy", "strong_buy"):
                if ret <= -2:
                    fp_fn["FP_BUY"] += 1  # predicted up, went down > 2%
                elif ret >= 2:
                    fp_fn["FN_BUY"] += 1  # should have predicted up, actual up > 2%
            if r.recommendation in ("sell", "strong_sell", "hedge"):
                if ret >= 2:
                    fp_fn["FP_SELL"] += 1  # predicted down, went up > 2%
                elif ret <= -2:
                    fp_fn["FN_SELL"] += 1  # should have predicted down, actual down > 2%

    lines.append("| Metric | Count |")
    lines.append("|---|---|")
    lines.append(f"| False Positive BUY (predicted up, fell >2%) | {fp_fn['FP_BUY']} |")
    lines.append(f"| False Negative BUY (missed up move >2%) | {fp_fn['FN_BUY']} |")
    lines.append(f"| False Positive SELL (predicted down, rose >2%) | {fp_fn['FP_SELL']} |")
    lines.append(f"| False Negative SELL (missed down move >2%) | {fp_fn['FN_SELL']} |")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    total_signals = len(records)
    if total_signals > 0:
        avg_24h_ret = statistics.mean([r.forward_returns.get(24, 0) for r in records])
        acc_24h = sum(1 for r in records if directional_accuracy(r.recommendation, r.forward_returns.get(24, 0))) / total_signals * 100
        lines.append(f"- Total actionable signals: {total_signals}")
        lines.append(f"- 24h directional accuracy: {acc_24h:.1f}%")
        lines.append(f"- 24h average forward return: {avg_24h_ret:+.2f}%")
        lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs("_project-memory/crypto_consolidation", exist_ok=True)
    print("=" * 60)
    print("OSIRIS Crypto Signal Quality Audit")
    print("=" * 60)
    print("\nRunning 180-day signal analysis...")
    records = run_signal_analysis(days=180)
    print(f"  Signals collected: {len(records)}")

    report = generate_report(records)
    path = "_project-memory/crypto_consolidation/signal_quality_report.md"
    with open(path, "w") as f:
        f.write(report)
    print(f"Report written to {path}")

    json_path = "_project-memory/crypto_consolidation/signal_quality_report.json"
    with open(json_path, "w") as f:
        json.dump([{
            "event_id": r.event_id,
            "symbol": r.symbol,
            "recommendation": r.recommendation,
            "conviction": round(r.conviction, 1),
            "consensus_score": round(r.consensus_score, 3),
            "risk_score": round(r.risk_score, 3),
            "price": round(r.price_at_signal, 2),
            "forward_returns": {str(k): v for k, v in r.forward_returns.items()},
        } for r in records], f, indent=2, default=str)

    print(f"JSON data written to {json_path}")


if __name__ == "__main__":
    main()
