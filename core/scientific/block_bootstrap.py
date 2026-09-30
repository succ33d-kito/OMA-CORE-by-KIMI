"""Deterministic moving-block bootstrap for dependent return observations."""
from dataclasses import dataclass,asdict
import random
from math import isfinite

@dataclass(frozen=True)
class BootstrapCI:
    estimate: float
    lower: float
    upper: float
    confidence: float
    block_size: int
    resamples: int
    def to_dict(self): return asdict(self)

def moving_block_mean_ci(values,*,block_size=24,resamples=2000,confidence=.95,seed=1729):
    xs=[float(x) for x in values]
    if len(xs)<max(2*block_size,20): raise ValueError("insufficient observations")
    if not all(isfinite(x) for x in xs) or block_size<1 or resamples<100 or not 0<confidence<1: raise ValueError("invalid bootstrap input")
    blocks=[xs[i:i+block_size] for i in range(0,len(xs)-block_size+1)]
    rng=random.Random(seed); means=[]
    for _ in range(resamples):
        sample=[]
        while len(sample)<len(xs): sample.extend(rng.choice(blocks))
        means.append(sum(sample[:len(xs)])/len(xs))
    means.sort(); alpha=(1-confidence)/2
    lo=means[int(alpha*resamples)]; hi=means[min(resamples-1,int((1-alpha)*resamples)-1)]
    return BootstrapCI(sum(xs)/len(xs),lo,hi,confidence,block_size,resamples)
