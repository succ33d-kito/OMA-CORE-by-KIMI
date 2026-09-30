"""Temporal descriptors for sequences of already-classified regimes.
Research context only; never emits an action or probability.
"""
from dataclasses import dataclass,asdict

@dataclass(frozen=True)
class RegimeTransition:
    previous_structure: str
    current_structure: str
    structure_age_bars: int
    previous_direction: str
    current_direction: str
    direction_age_bars: int
    previous_volatility: str
    current_volatility: str
    volatility_age_bars: int
    structure_changed: bool
    direction_changed: bool
    volatility_changed: bool
    method: str="regime-transition-v1"
    def to_dict(self): return asdict(self)

def _age(states, attr):
    current=getattr(states[-1],attr); age=1
    for s in reversed(states[:-1]):
        if getattr(s,attr)!=current: break
        age+=1
    return age

def describe_transition(states):
    if len(states)<2: raise ValueError("at least two regime states required")
    a,b=states[-2],states[-1]
    return RegimeTransition(a.structure,b.structure,_age(states,"structure"),a.direction,b.direction,_age(states,"direction"),a.volatility,b.volatility,_age(states,"volatility"),a.structure!=b.structure,a.direction!=b.direction,a.volatility!=b.volatility)
