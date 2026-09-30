"""Provider-neutral causal context for market variables not present in OHLCV.
Descriptors only. Missing inputs remain unknown; no imputation from price is allowed.
"""
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from math import isfinite

def _utc(x):
    if not isinstance(x,datetime) or x.tzinfo is None: raise ValueError("timezone-aware timestamp required")
    return x.astimezone(timezone.utc)
@dataclass(frozen=True)
class TimedValue:
    observed_at: datetime
    value: float
    source: str
@dataclass(frozen=True)
class LatentMarketContext:
    open_interest_change: float|None
    funding_rate: float|None
    long_short_ratio: float|None
    liquidation_imbalance: float|None
    taker_imbalance: float|None
    spot_netflow: float|None
    available_axes: tuple[str,...]
    unknown_axes: tuple[str,...]
    method: str="latent-context-v1"
    def to_dict(self): return asdict(self)

def build_latent_context(*,as_of,open_interest_change=None,funding_rate=None,long_short_ratio=None,liquidation_imbalance=None,taker_imbalance=None,spot_netflow=None):
    as_of=_utc(as_of); raw=locals(); names=("open_interest_change","funding_rate","long_short_ratio","liquidation_imbalance","taker_imbalance","spot_netflow"); vals={}
    for name in names:
        item=raw[name]
        if item is None: vals[name]=None; continue
        if _utc(item.observed_at)>as_of: raise ValueError("future latent-market observation")
        value=float(item.value)
        if not isfinite(value): raise ValueError("non-finite latent-market value")
        if not item.source: raise ValueError("source provenance required")
        vals[name]=value
    available=tuple(n for n in names if vals[n] is not None); unknown=tuple(n for n in names if vals[n] is None)
    return LatentMarketContext(**vals,available_axes=available,unknown_axes=unknown)
