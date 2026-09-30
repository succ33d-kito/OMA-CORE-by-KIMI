"""Longitudinal stability gate for conditional effects across independent periods/venues.

This module evaluates evidence; it does not emit trading signals or promote Criterion.
"""
from dataclasses import dataclass, asdict
from math import isfinite

@dataclass(frozen=True)
class PeriodEffect:
    period: str
    n: int
    mean_effect: float
    venue: str = ""
    instrument: str = ""

@dataclass(frozen=True)
class StabilityResult:
    status: str
    qualified_periods: int
    sign_persistence: float | None
    max_abs_effect_delta: float | None
    min_abs_effect: float | None
    reason: str
    def to_dict(self): return asdict(self)

def evaluate_longitudinal_stability(effects, *, min_n=50, min_periods=3, zero_band=0.0):
    if min_n < 1 or min_periods < 2 or zero_band < 0:
        raise ValueError("invalid stability thresholds")
    clean=[]
    for e in effects:
        if e.n < 0 or not isfinite(float(e.mean_effect)):
            raise ValueError("invalid period effect")
        if e.n >= min_n:
            clean.append(e)
    if len(clean) < min_periods:
        return StabilityResult("insufficient_evidence",len(clean),None,None,None,"not enough qualified independent periods")
    signs=[]
    for e in clean:
        x=float(e.mean_effect)
        signs.append(0 if abs(x)<=zero_band else (1 if x>0 else -1))
    nonzero=[s for s in signs if s]
    if len(nonzero)<min_periods:
        return StabilityResult("unstable",len(clean),0.0,None,min(abs(float(e.mean_effect)) for e in clean),"effects enter zero band")
    majority=1 if sum(nonzero)>0 else -1 if sum(nonzero)<0 else 0
    persistence=sum(s==majority for s in nonzero)/len(nonzero) if majority else 0.5
    vals=[float(e.mean_effect) for e in clean]
    delta=max(vals)-min(vals)
    minimum=min(abs(x) for x in vals)
    status="stable_sign" if persistence==1.0 else "unstable_sign"
    return StabilityResult(status,len(clean),persistence,delta,minimum,"all qualified periods share sign" if status=="stable_sign" else "sign changes across qualified periods")
