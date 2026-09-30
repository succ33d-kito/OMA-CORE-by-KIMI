from datetime import datetime, timezone, timedelta
import pytest
from core.market_mechanics.binance_public_metrics import BinanceMetricsPoint, metrics_asof, hourly_last

def point(minute):
    return BinanceMetricsPoint(datetime(2025,1,1,0,minute,tzinfo=timezone.utc),1,2,1,1,1,1)

def test_metric_available_only_after_observation():
    p=point(55)
    with pytest.raises(ValueError):metrics_asof(p,datetime(2025,1,1,0,0,tzinfo=timezone.utc))
    assert metrics_asof(p,datetime(2025,1,1,1,0,tzinfo=timezone.utc)) is p

def test_hourly_missing_hour_is_not_imputed():
    later=BinanceMetricsPoint(point(0).observed_at+timedelta(hours=2),1,2,1,1,1,1)
    assert len(hourly_last([point(0),later]))==2
