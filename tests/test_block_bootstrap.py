import pytest
from core.scientific.block_bootstrap import moving_block_mean_ci

def test_deterministic():
    x=list(range(100)); assert moving_block_mean_ci(x,resamples=200)==moving_block_mean_ci(x,resamples=200)
def test_contains_estimate_for_constant_series():
    r=moving_block_mean_ci([.01]*100,resamples=200); assert r.lower<=r.estimate<=r.upper
def test_rejects_too_little_data():
    with pytest.raises(ValueError): moving_block_mean_ci([1,2,3])
def test_rejects_nan():
    with pytest.raises(ValueError): moving_block_mean_ci([1.0]*50+[float("nan")])
