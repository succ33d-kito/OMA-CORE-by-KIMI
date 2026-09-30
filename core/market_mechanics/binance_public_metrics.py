"""Adapter for Binance USD-M public-data `metrics` rows.
The archive is free/public; this adapter performs no network I/O and never imputes gaps.
"""
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from math import isfinite

@dataclass(frozen=True)
class BinanceMetricsPoint:
    observed_at: datetime
    open_interest: float
    open_interest_value: float
    top_account_long_short_ratio: float|None
    top_position_long_short_ratio: float|None
    global_long_short_ratio: float|None
    taker_long_short_ratio: float|None
    source: str="binance-public-data/um/metrics"
    def to_dict(self): return asdict(self)

def _num(row,*names):
    for n in names:
        if n in row and row[n] not in (None,""):
            x=float(row[n]);
            if not isfinite(x): raise ValueError("non-finite Binance metric")
            return x
    return None

def parse_metrics_row(row):
    raw=row.get("create_time") or row.get("timestamp")
    if raw is None: raise ValueError("missing metric timestamp")
    if isinstance(raw,str) and not raw.isdigit():
        t=datetime.fromisoformat(raw.replace("Z","+00:00"))
    else:
        x=float(raw); t=datetime.fromtimestamp(x/(1000 if x>1e11 else 1),timezone.utc)
    if t.tzinfo is None:t=t.replace(tzinfo=timezone.utc)
    oi=_num(row,"sum_open_interest","sumOpenInterest"); oiv=_num(row,"sum_open_interest_value","sumOpenInterestValue")
    if oi is None or oiv is None: raise ValueError("missing open interest fields")
    return BinanceMetricsPoint(t.astimezone(timezone.utc),oi,oiv,
        _num(row,"count_toptrader_long_short_ratio"),_num(row,"sum_toptrader_long_short_ratio"),
        _num(row,"count_long_short_ratio"),_num(row,"sum_taker_long_short_vol_ratio"))

def hourly_last(points):
    """Downsample causally: last actually observed point in each UTC hour. Missing hours remain absent."""
    out={}
    for p in sorted(points,key=lambda x:x.observed_at):
        key=p.observed_at.replace(minute=0,second=0,microsecond=0); out[key]=p
    return [out[k] for k in sorted(out)]

def metrics_asof(point, decision_time):
    """Only expose a metric if its observation precedes the decision (UTC aware)."""
    if point.observed_at.tzinfo is None or decision_time.tzinfo is None:
        raise ValueError("timezone-aware timestamps required")
    if point.observed_at > decision_time:
        raise ValueError("metric observed after decision")
    return point
