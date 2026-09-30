"""Versioned descriptive regimes. Labels are heuristics, not probabilities."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from statistics import stdev


@dataclass(frozen=True)
class RegimeState:
    regime_id: str
    market_state_id: str
    as_of: str
    structure: str
    direction: str
    efficiency_ratio: float
    volatility: str
    volatility_ratio: float | None
    unknown_axes: tuple[str, ...] = ("risk_appetite", "liquidity", "event", "crisis")
    method: str = "er20-vol20-vs-prior60-v1"

    def to_dict(self):
        return asdict(self)


def classify_regime(state):
    closes = [row[4] for row in state.input_bars]
    if len(closes) < 21:
        raise ValueError("regime requires 21 closed bars")
    changes = [closes[i] - closes[i-1] for i in range(len(closes)-20, len(closes))]
    path = sum(abs(x) for x in changes)
    net = closes[-1] - closes[-21]
    efficiency = abs(net) / path if path else 0.0
    structure = "trend" if efficiency >= .6 else "range" if efficiency <= .25 else "transition"
    direction = "up" if net > 0 else "down" if net < 0 else "flat"
    vol, ratio = "unknown", None
    if len(closes) >= 81:
        returns = [closes[i]/closes[i-1]-1 for i in range(len(closes)-80, len(closes))]
        reference = stdev(returns[:-20])
        if reference > 1e-12:
            ratio = stdev(returns[-20:]) / reference
            vol = "high" if ratio >= 1.5 else "low" if ratio <= 2/3 else "normal"
    key = sha256((state.state_id + ":er20-vol20-vs-prior60-v1").encode()).hexdigest()
    return RegimeState(key, state.state_id, state.as_of, structure, direction, efficiency, vol, ratio)
