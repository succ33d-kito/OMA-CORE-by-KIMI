"""Causal trade-count participation features for feeds that expose closed-bar trade counts.

Research descriptor only: it emits no signal/action and makes no claim about order flow.
"""
from dataclasses import dataclass, asdict
from math import isfinite
from statistics import mean

@dataclass(frozen=True)
class ParticipationState:
    participation: str
    trade_count_ratio: float
    trade_size: str
    avg_trade_size_ratio: float
    lookback: int = 60
    method: str = "trade-count-and-volume-v1"
    def to_dict(self): return asdict(self)

def classify_participation(bars, *, lookback=60):
    if lookback < 20 or len(bars) < lookback + 1:
        raise ValueError("participation requires current bar plus sufficient trailing history")
    window=bars[-(lookback+1):]
    def vals(b):
        v=float(b["volume"]); t=float(b["trades"])
        if not isfinite(v) or not isfinite(t) or v < 0 or t <= 0:
            raise ValueError("finite nonnegative volume and positive trade count required")
        return v,t
    prior=[vals(b) for b in window[:-1]]; v,t=vals(window[-1])
    tr=t/mean(x[1] for x in prior)
    prior_sizes=[x[0]/x[1] for x in prior]
    sr=(v/t)/mean(prior_sizes) if mean(prior_sizes)>0 else 1.0
    label="high" if tr>=1.5 else "low" if tr<=2/3 else "normal"
    size="large" if sr>=1.5 else "small" if sr<=2/3 else "normal"
    return ParticipationState(label,tr,size,sr,lookback)
