from datetime import datetime,timezone,timedelta
from core.scientific.prospective_receipts import record
from scripts.prospective_health import status

def test_health_exposes_gap_and_late_receipt(tmp_path):
    db=tmp_path/'ledger.db';t=datetime(2026,10,1,tzinfo=timezone.utc)
    record(db,'bar',{'time':t.isoformat(),'open':100,'high':101,'low':99,'close':100,'volume':1},source='test',clock=lambda:t+timedelta(hours=1,minutes=6))
    m={'timestamp':(t+timedelta(hours=2,minutes=55)).isoformat(),'sum_open_interest':100,'sum_open_interest_value':10000,'count_toptrader_long_short_ratio':1.1,'sum_toptrader_long_short_ratio':1.1,'count_long_short_ratio':1.1,'sum_taker_long_short_vol_ratio':1.1}
    record(db,'metric',m,source='test',clock=lambda:t+timedelta(hours=3,minutes=4))
    at=t+timedelta(hours=2)
    record(db,'bar',{'time':at.isoformat(),'open':100,'high':101,'low':99,'close':100,'volume':1},source='test',clock=lambda:t+timedelta(hours=3,minutes=6))
    x=status(db,now=t+timedelta(hours=4))
    assert x['missing_bar_hours']==1 and x['bars_by_deadline']==0 and x['metrics_by_deadline']==1
    assert x['scientific_gate']=='not_evaluated'
