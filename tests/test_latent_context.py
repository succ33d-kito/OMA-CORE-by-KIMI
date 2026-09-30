from datetime import datetime,timedelta,timezone
import pytest
from core.market_mechanics.latent_context import TimedValue,build_latent_context
NOW=datetime(2026,1,1,tzinfo=timezone.utc)
def tv(x,t=NOW): return TimedValue(t,x,"test")
def test_missing_stays_unknown():
    x=build_latent_context(as_of=NOW,funding_rate=tv(.001)); assert x.funding_rate==.001 and "open_interest_change" in x.unknown_axes
def test_future_rejected():
    with pytest.raises(ValueError): build_latent_context(as_of=NOW,funding_rate=tv(.1,NOW+timedelta(seconds=1)))
def test_multiple_axes_preserved():
    x=build_latent_context(as_of=NOW,open_interest_change=tv(.02),taker_imbalance=tv(-.3)); assert set(x.available_axes)=={"open_interest_change","taker_imbalance"}
def test_no_provenance_rejected():
    with pytest.raises(ValueError): build_latent_context(as_of=NOW,funding_rate=TimedValue(NOW,.1,""))
