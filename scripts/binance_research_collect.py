"""Single-run optional live capture; run only where provider access is authorized."""
import argparse,json,os,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.market_mechanics.binance_live_adapter import fetch_once
from core.scientific.prospective_receipts import record

def main():
    p=argparse.ArgumentParser();p.add_argument('ledger',type=Path);p.add_argument('--raw-dir',type=Path,required=True);p.add_argument('--not-before',default='2026-10-01T00:00:00+00:00');p.add_argument('--preflight',action='store_true');a=p.parse_args()
    cutoff=datetime.fromisoformat(a.not_before.replace('Z','+00:00'))
    if cutoff.tzinfo is None:raise ValueError('not-before must be timezone-aware')
    if not a.preflight and datetime.now(timezone.utc)<cutoff.astimezone(timezone.utc):
        print(json.dumps({'status':'not_started','not_before':cutoff.isoformat()}));return
    import requests
    bundle=fetch_once(requests.Session(),api_key=os.environ.get('BINANCE_API_KEY'))
    if a.preflight:
        print(json.dumps({'status':'source_accessible','metric_timestamp':bundle['metric']['timestamp'],'bar_time':bundle['bar']['time']}));return
    a.raw_dir.mkdir(parents=True,exist_ok=True)
    raw=a.raw_dir/(bundle['raw_metrics_sha256']+'.json')
    raw.write_text(json.dumps(bundle['raw_metrics'],sort_keys=True,indent=2))
    output=[]
    for kind in ('bar','metric'):
        try:output.append(record(a.ledger,kind,bundle[kind],source='binance-usdm-fapi raw-metrics-sha256='+bundle['raw_metrics_sha256']))
        except Exception as e:
            if 'UNIQUE constraint failed' not in str(e):raise
            output.append({'kind':kind,'status':'already_recorded'})
    print(json.dumps({'receipts':output,'raw_metrics_sha256':bundle['raw_metrics_sha256']}))
if __name__=='__main__':main()
