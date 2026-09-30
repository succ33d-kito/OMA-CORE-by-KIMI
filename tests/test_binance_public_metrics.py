from core.market_mechanics.binance_public_metrics import parse_metrics_row,hourly_last

def row(t="2025-01-01 00:05:00"):
 return {"create_time":t,"sum_open_interest":"100","sum_open_interest_value":"1000","count_toptrader_long_short_ratio":"1.1","sum_toptrader_long_short_ratio":"1.2","count_long_short_ratio":"0.9","sum_taker_long_short_vol_ratio":"1.05"}
def test_parse():
 x=parse_metrics_row(row()); assert x.open_interest==100 and x.taker_long_short_ratio==1.05
def test_hourly_last_no_imputation():
 a=parse_metrics_row(row("2025-01-01 00:05:00")); b=parse_metrics_row(row("2025-01-01 00:55:00")); c=parse_metrics_row(row("2025-01-01 02:05:00")); out=hourly_last([a,b,c]); assert len(out)==2 and out[0].observed_at.minute==55
def test_missing_oi_rejected():
 import pytest
 r=row(); del r["sum_open_interest"]
 with pytest.raises(ValueError): parse_metrics_row(r)
