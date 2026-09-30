"""Read-only data collection health; never evaluates forward returns."""
import argparse,json,sys,tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.scientific.prospective_receipts import export_verified
import pandas as pd

def status(ledger,*,now=None):
    now=now or datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory() as temp:
        manifest=export_verified(ledger,temp)
        bars=pd.read_csv(Path(temp)/'prospective_bars.csv')
        metrics=pd.read_csv(Path(temp)/'prospective_metrics.csv')
    if bars.empty or metrics.empty:
        return {'status':'no_complete_feed','bar_rows':len(bars),'metric_rows':len(metrics),'ledger_head_sha256':manifest['ledger_head_sha256']}
    bt=pd.to_datetime(bars.time,utc=True);ba=pd.to_datetime(bars.available_at,utc=True)
    mt=pd.to_datetime(metrics.timestamp,utc=True);ma=pd.to_datetime(metrics.available_at,utc=True)
    gaps=int(((bt.diff().dropna()/pd.Timedelta(hours=1))-1).clip(lower=0).sum())
    decision=bt+pd.Timedelta(hours=1)
    bar_on_time=int((ba<=decision+pd.Timedelta(minutes=5)).sum())
    metric_decision=mt.dt.floor('h')+pd.Timedelta(hours=1)
    metric_on_time=int((ma<=metric_decision+pd.Timedelta(minutes=5)).sum())
    return {'status':'collecting' if gaps==0 else 'gaps_detected','bar_rows':len(bars),'metric_rows':len(metrics),
      'first_bar_utc':bt.iloc[0].isoformat(),'last_bar_utc':bt.iloc[-1].isoformat(),
      'missing_bar_hours':gaps,'bars_by_deadline':bar_on_time,'metrics_by_deadline':metric_on_time,
      'last_bar_age_hours':(pd.Timestamp(now)-bt.iloc[-1]).total_seconds()/3600,
      'ledger_head_sha256':manifest['ledger_head_sha256'],
      'scientific_gate':'not_evaluated'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('ledger',type=Path);a=p.parse_args()
    print(json.dumps(status(a.ledger),indent=2))
