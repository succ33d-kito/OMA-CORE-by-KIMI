from datetime import datetime,timezone,timedelta
import sqlite3
import pytest
from core.scientific.prospective_receipts import record,export_verified

UTC=timezone.utc

def test_records_real_receipt_time_and_roundtrips(tmp_path):
    db=tmp_path/'receipts.db';out=tmp_path/'export'
    t=datetime(2026,10,1,0,tzinfo=UTC)
    bar={'time':t.isoformat(),'open':100,'high':102,'low':99,'close':101,'volume':10}
    metric={'timestamp':(t+timedelta(minutes=55)).isoformat(),'sum_open_interest':1000,'sum_open_interest_value':100000,'count_toptrader_long_short_ratio':1.2,'sum_toptrader_long_short_ratio':1.1,'count_long_short_ratio':1.05,'sum_taker_long_short_vol_ratio':1.3}
    x=record(db,'bar',bar,source='test',clock=lambda:t+timedelta(hours=1,minutes=1))
    y=record(db,'metric',metric,source='test',clock=lambda:t+timedelta(hours=1,minutes=2))
    assert x['available_at'].endswith('01:01:00+00:00')
    assert y['available_at'].endswith('01:02:00+00:00')
    a=export_verified(db,out);assert a['bar']['rows']==a['metric']['rows']==1
    assert 'available_at' in (out/'prospective_bars.csv').read_text()

def test_rejects_backdating_and_caller_receipt(tmp_path):
    t=datetime(2026,10,1,tzinfo=UTC)
    bar={'time':t.isoformat(),'open':100,'high':101,'low':99,'close':100,'volume':1}
    with pytest.raises(ValueError,match='receipt precedes'):record(tmp_path/'x.db','bar',bar,source='test',clock=lambda:t)
    with pytest.raises(ValueError,match='backfill'):record(tmp_path/'x.db','bar',bar,source='test',clock=lambda:t+timedelta(days=2))
    bar['available_at']=t.isoformat()
    with pytest.raises(ValueError,match='available_at'):record(tmp_path/'x.db','bar',bar,source='test',clock=lambda:t+timedelta(hours=1))

def test_detects_tamper_and_duplicate(tmp_path):
    t=datetime(2026,10,1,tzinfo=UTC);db=tmp_path/'x.db'
    bar={'time':t.isoformat(),'open':100,'high':101,'low':99,'close':100,'volume':1}
    record(db,'bar',bar,source='test',clock=lambda:t+timedelta(hours=1))
    with pytest.raises(sqlite3.IntegrityError):record(db,'bar',bar,source='test',clock=lambda:t+timedelta(hours=1,minutes=2))
    with sqlite3.connect(db) as con:con.execute("UPDATE receipts SET payload='{}'")
    with pytest.raises(ValueError,match='integrity'):export_verified(db,tmp_path/'out')
