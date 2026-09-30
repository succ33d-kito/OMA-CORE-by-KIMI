"""Chronological long-only entry ablation, not a full runtime backtest."""

from dataclasses import asdict, dataclass
from datetime import timedelta
from hashlib import sha256
import json

from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.event_bus import EventBus
from core.market_mechanics import build_market_state
from core.schemas.agent_schema import Recommendation
from core.schemas.event_schema import Event, Asset, AssetClass, EventType, Urgency


@dataclass(frozen=True)
class ComparisonProtocol:
    protocol_id: str = "MM-H1-v1"
    warmup: int = 120
    development_fraction: float = 0.6
    horizon: int = 24
    stop_fraction: float = 0.02
    target_fraction: float = 0.04
    allocation: float = 0.2
    fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 5.0
    minimum_volume_ratio: float = 1.5

    def __post_init__(self):
        if self.warmup < 50 or self.horizon < 1 or not 0 < self.development_fraction < 1:
            raise ValueError("invalid chronological protocol")
        if not 0 < self.stop_fraction < 1 or self.target_fraction <= 0 or not 0 < self.allocation <= 1:
            raise ValueError("invalid trade construction")
        if min(self.fee_bps_per_side, self.slippage_bps_per_side) < 0:
            raise ValueError("costs must be nonnegative")


def candidate_rows(bars, symbol, source_id, protocol):
    """Each agent can access only the trailing closed window."""
    market = MarketAgent(event_bus=EventBus())
    risk = RiskAgent(event_bus=EventBus())
    council = AgentCouncil(event_bus=EventBus())
    rows = []
    for i in range(protocol.warmup - 1, len(bars)):
        window = bars[max(0, i - protocol.warmup + 1):i + 1]
        timestamp = bars[i]["time"] + timedelta(hours=1)
        state = build_market_state(symbol, window, source_id=source_id,
                                   observed_at=timestamp, as_of=timestamp)
        market._fetch_ohlcv = lambda _, w=window: w
        risk._fetch_ohlcv = lambda _, w=window: w
        change = bars[i]["close"] / bars[i-1]["close"] - 1
        spike = abs(change) > .05 and bars[i]["volume"] > bars[i-1]["volume"] * 1.5
        event = Event(id=f"{symbol}:{i}", source=source_id,
                      event_type=EventType.VOLUME_SPIKE if spike else EventType.PRICE_MOVEMENT,
                      timestamp=timestamp, detected_at=timestamp, sentiment_score=change,
                      urgency=Urgency.HIGH if abs(change) > .05 else Urgency.MEDIUM if abs(change) > .02 else Urgency.LOW,
                      confidence=.7, assets=[Asset(symbol, symbol, AssetClass.CRYPTO, price_at_event=bars[i]["close"])])
        opinions = [market.analyze(event), risk.analyze(event)]
        for opinion in opinions:
            if opinion is not None:
                opinion.timestamp = timestamp
                council.submit_opinion(opinion)
        decision = council.decide(event.id)
        baseline = decision is not None and decision.action in (Recommendation.BUY, Recommendation.STRONG_BUY)
        accepted = baseline and state.range_status == "above_prior_range" and (
            state.volume_ratio is not None and state.volume_ratio >= protocol.minimum_volume_ratio)
        rows.append({"index": i, "decision_time": timestamp.isoformat(), "baseline": baseline,
                     "mechanics_filter": accepted, "range_status": state.range_status,
                     "volume_ratio": state.volume_ratio, "state_id": state.state_id})
        council._opinions.pop(event.id, None)
    return rows


def simulate_long(bars, signal_index, protocol):
    """Next-open entry; stop wins ambiguous intrabar order; costs both sides."""
    start = signal_index + 1
    slip = protocol.slippage_bps_per_side / 10000
    fee = protocol.fee_bps_per_side / 10000
    entry = bars[start]["open"] * (1 + slip)
    stop = entry * (1 - protocol.stop_fraction)
    target = entry * (1 + protocol.target_fraction)
    for j in range(start, start + protocol.horizon):
        bar = bars[j]
        if bar["open"] <= stop:
            raw_exit, reason = bar["open"], "gap_stop"
        elif bar["low"] <= stop:
            raw_exit, reason = stop, "stop"
        elif bar["high"] >= target:
            raw_exit, reason = target, "target"
        elif j == start + protocol.horizon - 1:
            raw_exit, reason = bar["close"], "horizon"
        else:
            continue
        exit_price = raw_exit * (1 - slip)
        net = exit_price / entry - 1 - fee * (1 + exit_price / entry)
        return {"signal_index": signal_index, "entry_index": start, "exit_index": j,
                "entry_time": bars[start]["time"].isoformat(),
                "exit_bar_time": bar["time"].isoformat(), "entry": entry,
                "exit": exit_price, "net_return": net, "reason": reason}


def evaluate_partition(bars, candidates, start, end, policy, protocol):
    equity, peak, dd, next_index = 1.0, 1.0, 0.0, start
    trades = []
    for row in candidates:
        i = row["index"]
        if not (start <= i < end - protocol.horizon) or i < next_index or not row[policy]:
            continue
        trade = simulate_long(bars, i, protocol)
        equity *= 1 + protocol.allocation * trade["net_return"]
        peak = max(peak, equity)
        dd = max(dd, 1 - equity / peak)
        trades.append(trade)
        next_index = trade["exit_index"]
    wins = [t["net_return"] for t in trades if t["net_return"] > 0]
    losses = [t["net_return"] for t in trades if t["net_return"] < 0]
    return {"trade_count": len(trades), "net_return_pct": (equity - 1) * 100,
            "closed_equity_max_drawdown_pct": dd * 100,
            "win_rate": len(wins) / len(trades) if trades else None,
            "mean_trade_return": sum(t["net_return"] for t in trades) / len(trades) if trades else None,
            "profit_factor": sum(wins) / -sum(losses) if losses else None,
            "trades": trades}


def compare(bars, *, symbol, source_id, data_kind, protocol=None):
    if data_kind not in ("historical", "synthetic"):
        raise ValueError("declare historical or synthetic data")
    protocol = protocol or ComparisonProtocol()
    if len(bars) < protocol.warmup + 4 * protocol.horizon:
        raise ValueError("insufficient bars for chronological split and embargo")
    # Validate the entire supplied history before slicing it.
    last_close = bars[-1]["time"] + timedelta(hours=1)
    build_market_state(symbol, bars, source_id=source_id, observed_at=last_close, as_of=last_close)
    cut = protocol.warmup + int((len(bars) - protocol.warmup) * protocol.development_fraction)
    test_start = cut + protocol.horizon
    if test_start >= len(bars) - protocol.horizon:
        raise ValueError("holdout too short after embargo")
    candidates = candidate_rows(bars, symbol, source_id, protocol)
    results = {}
    for name, start, end in (("development", protocol.warmup-1, cut), ("holdout", test_start, len(bars))):
        results[name] = {policy: evaluate_partition(bars, candidates, start, end, policy, protocol)
                         for policy in ("baseline", "mechanics_filter")}
        results[name]["signal_index_range"] = [start, end-protocol.horizon-1]
    encoded = json.dumps(bars, default=lambda x: x.isoformat(), sort_keys=True).encode()
    return {"protocol": asdict(protocol), "data_kind": data_kind, "symbol": symbol,
            "source_id": source_id, "input_sha256": sha256(encoded).hexdigest(),
            "bars": len(bars), "split_index": cut, "embargo_bars": protocol.horizon,
            "scope": "long_only_entry_ablation_fixed_execution_not_full_runtime",
            "verdict": "synthetic_smoke_only" if data_kind == "synthetic" else "exploratory_not_validated_edge",
            "results": results, "candidates": candidates}
