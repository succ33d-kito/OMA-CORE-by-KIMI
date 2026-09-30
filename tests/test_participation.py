from core.market_mechanics.participation import classify_participation
import pytest

def bars(n=61, current_trades=100, current_volume=10):
    out=[{"volume":10.0,"trades":100} for _ in range(n)]
    out[-1]={"volume":current_volume,"trades":current_trades}
    return out

def test_normal_baseline():
    x=classify_participation(bars())
    assert x.participation=="normal" and x.trade_size=="normal"

def test_high_trade_participation():
    assert classify_participation(bars(current_trades=200,current_volume=20)).participation=="high"

def test_large_average_trade_size_is_distinct_from_trade_count():
    x=classify_participation(bars(current_trades=100,current_volume=20))
    assert x.participation=="normal" and x.trade_size=="large"

def test_rejects_missing_history():
    with pytest.raises(ValueError): classify_participation(bars(20))

def test_rejects_zero_trades():
    with pytest.raises(ValueError): classify_participation(bars(current_trades=0))
