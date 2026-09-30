"""Causal market context descriptors layered around Regime v1.
No trading action, probability, or causal claim is emitted.
"""
from dataclasses import dataclass,asdict
from statistics import mean,stdev

@dataclass(frozen=True)
class MarketContext:
    trend_age: str
    participation: str
    range_location: str
    impulse: str
    volatility_expansion: str
    unknown_axes: tuple[str,...]=("liquidity","positioning","derivatives","risk_appetite","event","macro")
    method: str="ohlcv-context-v2"
    def to_dict(self): return asdict(self)

def classify_context(state):
    rows=state.input_bars
    if len(rows)<81: raise ValueError("context requires at least 81 closed bars")
    closes=[float(x[4]) for x in rows]; vols=[float(x[5]) for x in rows]
    rets=[closes[i]/closes[i-1]-1 for i in range(1,len(closes))]
    # Persistence: fraction of last 20 returns sharing the 20-bar net direction.
    recent=rets[-20:]; net=closes[-1]/closes[-21]-1
    same=sum((r>0)==(net>0) for r in recent if r!=0)/max(1,sum(r!=0 for r in recent))
    trend_age="established" if same>=.60 else "young_or_mixed"
    # Participation from volume only, causal relative to prior 60 bars.
    vr=vols[-1]/mean(vols[-61:-1]) if mean(vols[-61:-1]) else 1.0
    participation="high" if vr>=1.5 else "low" if vr<=2/3 else "normal"
    hi=max(float(x[2]) for x in rows[-21:-1]); lo=min(float(x[3]) for x in rows[-21:-1]); c=closes[-1]
    if c>hi: loc="breakout_up"
    elif c<lo: loc="breakout_down"
    else:
        pos=(c-lo)/(hi-lo) if hi>lo else .5
        loc="upper" if pos>=2/3 else "lower" if pos<=1/3 else "middle"
    sigma=stdev(rets[-61:-1]) if len(rets)>=61 else stdev(rets[:-1])
    impulse="large" if sigma and abs(rets[-1])>=1.5*sigma else "quiet" if sigma and abs(rets[-1])<=.5*sigma else "normal"
    old=stdev(rets[-80:-20]); new=stdev(rets[-20:])
    ratio=new/old if old>1e-12 else 1.0
    vex="expanding" if ratio>=1.5 else "contracting" if ratio<=2/3 else "stable"
    return MarketContext(trend_age,participation,loc,impulse,vex)
