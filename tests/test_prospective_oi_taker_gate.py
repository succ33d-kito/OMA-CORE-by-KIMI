import pandas as pd
import pytest
from scripts.prospective_oi_taker_gate import evaluate
from scripts.metrics_2024_2025 import FIELDS

def files(tmp_path):
    t=pd.date_range('2025-01-01',periods=160,freq='h',tz='UTC')
    p=tmp_path/'bars.csv';m=tmp_path/'metrics.csv'
    pd.DataFrame({'time':t,'available_at':t+pd.Timedelta(hours=1,minutes=1),'open':100.,'high':101.,'low':99.,'close':100.,'volume':1.}).to_csv(p,index=False)
    d={'timestamp':t,'available_at':t+pd.Timedelta(minutes=1)};d.update({x:1.1 for x in FIELDS});pd.DataFrame(d).to_csv(m,index=False)
    return p,m

def test_rejects_historical_reuse(tmp_path):
    p,m=files(tmp_path)
    with pytest.raises(ValueError,match='no eligible prospective rows'):
        evaluate(p,m,tmp_path/'out')

def test_rejects_missing_price_hour(tmp_path):
    p,m=files(tmp_path);d=pd.read_csv(p).drop(index=[3]);d.to_csv(p,index=False)
    with pytest.raises(ValueError,match='contiguous H1'):
        evaluate(p,m,tmp_path/'out')

def test_rejects_protocol_edit(tmp_path):
    p,m=files(tmp_path);changed=tmp_path/'changed_protocol.json';changed.write_text('{}')
    with pytest.raises(ValueError,match='frozen protocol SHA-256 mismatch'):
        evaluate(p,m,tmp_path/'out',protocol_path=changed)

def test_late_metric_not_used(tmp_path):
    p,m=files(tmp_path)
    bars=pd.read_csv(p);metrics=pd.read_csv(m)
    bars['time']=pd.date_range('2027-01-01',periods=len(bars),freq='h',tz='UTC')
    bars['available_at']=pd.to_datetime(bars.time,utc=True)+pd.Timedelta(hours=1,minutes=1)
    metrics['timestamp']=bars.time
    metrics['available_at']=pd.to_datetime(bars.time,utc=True)+pd.Timedelta(hours=1,minutes=6)
    bars.to_csv(p,index=False);metrics.to_csv(m,index=False)
    with pytest.raises(ValueError,match='no eligible prospective rows'):
        evaluate(p,m,tmp_path/'out')
