from types import SimpleNamespace as S
import pytest
from core.market_mechanics.transitions import describe_transition

def r(s="range",d="up",v="normal"): return S(structure=s,direction=d,volatility=v)
def test_age_accumulates():
    x=describe_transition([r(),r(),r()]); assert x.structure_age_bars==3 and not x.structure_changed

def test_transition_detected():
    x=describe_transition([r("range"),r("trend")]); assert x.structure_changed and x.structure_age_bars==1

def test_axes_independent():
    x=describe_transition([r("range","down","low"),r("range","up","low")]); assert x.direction_changed and not x.structure_changed and not x.volatility_changed

def test_needs_history():
    with pytest.raises(ValueError): describe_transition([r()])
