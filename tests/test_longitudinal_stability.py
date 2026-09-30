import pytest
from core.scientific.longitudinal_stability import PeriodEffect,evaluate_longitudinal_stability as ev

def test_three_period_same_sign():
    r=ev([PeriodEffect("a",100,-.01),PeriodEffect("b",80,-.02),PeriodEffect("c",60,-.005)])
    assert r.status=="stable_sign" and r.sign_persistence==1.0

def test_flip_is_unstable():
    r=ev([PeriodEffect("a",100,-.01),PeriodEffect("b",80,.02),PeriodEffect("c",60,-.005)])
    assert r.status=="unstable_sign" and r.sign_persistence<1

def test_small_sample_cannot_promote():
    r=ev([PeriodEffect("a",100,-.01),PeriodEffect("b",20,-.02),PeriodEffect("c",60,-.005)])
    assert r.status=="insufficient_evidence"

def test_zero_band_blocks_tiny_effect():
    r=ev([PeriodEffect("a",100,-.01),PeriodEffect("b",80,-.0001),PeriodEffect("c",60,-.005)],zero_band=.0005)
    assert r.status=="unstable"

def test_nonfinite_rejected():
    with pytest.raises(ValueError): ev([PeriodEffect("a",100,float("nan"))])
