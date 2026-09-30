import pytest
from core.market_mechanics.state import build_market_state
from core.market_mechanics.context import classify_context
from datetime import datetime,timedelta,timezone

def mk(n=81):
    start=datetime(2026,1,1,tzinfo=timezone.utc); out=[]; price=100.
    for i in range(n):
        c=price*(1.001 if i%3 else .9995); out.append({"time":start+timedelta(hours=i),"open":price,"high":max(price,c)*1.001,"low":min(price,c)*.999,"close":c,"volume":100+i%5}); price=c
    return out

def state(b):
    obs=b[-1]["time"]+timedelta(hours=1)
    return build_market_state("X",b,source_id="test",observed_at=obs,as_of=obs)

def test_context_is_descriptive_and_complete():
    x=classify_context(state(mk())); assert x.trend_age in {"established","young_or_mixed"} and "macro" in x.unknown_axes

def test_requires_history():
    with pytest.raises(ValueError): classify_context(state(mk(21)))

def test_high_volume_participation():
    b=mk(); b[-1]["volume"]=1000; assert classify_context(state(b)).participation=="high"

def test_breakout_up_location():
    b=mk(); b[-1]["close"]=max(x["high"] for x in b[-21:-1])*1.01; b[-1]["high"]=b[-1]["close"]*1.001; assert classify_context(state(b)).range_location=="breakout_up"
