"""Reproducible, research-only Binance metrics audit and causal hourly evaluation."""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

EXPECTED='db5959a0e38d8155ee5931a5a22fb04b6ed3af853faba01fe498f65d17ea37ce'
FIELDS=['sum_open_interest','sum_open_interest_value','count_toptrader_long_short_ratio','sum_toptrader_long_short_ratio','count_long_short_ratio','sum_taker_long_short_vol_ratio']
HORIZONS=(1,4,12,24,48)
VARIANTS={'Regime':[], 'Regime + OI':['oi'], 'Regime + Positioning':['positioning'], 'Regime + Taker Flow':['taker'], 'Regime + OI + Positioning':['oi','positioning'], 'Regime + OI + Positioning + Taker Flow':['oi','positioning','taker']}

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()

def normalize(source,out):
    if sha(source)!=EXPECTED:raise ValueError('Parquet SHA-256 mismatch')
    d=pd.read_parquet(source); original=len(d)
    if list(d.columns)!=['timestamp',*FIELDS]:raise ValueError('unexpected schema')
    d['timestamp']=pd.to_datetime(d.timestamp,utc=True)
    duplicates=int(d.timestamp.duplicated().sum()); reversed_rows=int((d.timestamp.diff().dropna()<pd.Timedelta(0)).sum())
    nulls={c:int(d[c].isna().sum()) for c in d.columns}
    invalid={c:int((~np.isfinite(d[c].to_numpy(dtype=float)) | (d[c].to_numpy(dtype=float)<=0)).sum()) for c in FIELDS}
    intervals=d.timestamp.sort_values().diff().dropna(); gaps=intervals[intervals>pd.Timedelta(minutes=5)]
    audit={'source_sha256':EXPECTED,'rows':original,'schema':{c:str(v) for c,v in d.dtypes.items()},'first_utc':d.timestamp.min().isoformat(),'last_utc':d.timestamp.max().isoformat(),'duplicate_timestamps':duplicates,'out_of_order_rows':reversed_rows,'nulls':nulls,'nonfinite_or_nonpositive':invalid,'off_grid_timestamps':int(((d.timestamp.dt.minute%5!=0)|(d.timestamp.dt.second!=0)).sum()),'gap_events':len(gaps),'missing_5m_slots':int(sum(max(0,int(x//pd.Timedelta(minutes=5))-1) for x in gaps)),'gap_duration_counts':{str(k):int(v) for k,v in gaps.value_counts().items()}}
    if duplicates or reversed_rows:raise ValueError('duplicate or unsorted timestamps')
    out.mkdir(parents=True,exist_ok=True)
    csv=out/'BTCUSDT_metrics_5m.csv.gz'; d.to_csv(csv,index=False,compression={'method':'gzip','compresslevel':6,'mtime':0},date_format='%Y-%m-%dT%H:%M:%S%z')
    audit['normalized_csv_sha256']=sha(csv);(out/'metrics_audit.json').write_text(json.dumps(audit,indent=2))
    # A metric at HH:55 can enter the HH+1:00 decision, never the HH:00 decision.
    d=d[(d.timestamp.dt.year>=2024)&(d.timestamp.dt.year<=2025)].copy()
    good=np.isfinite(d[FIELDS]).all(axis=1)&(d[FIELDS]>0).all(axis=1)
    audit['excluded_invalid_2024_2025_rows']=int((~good).sum())
    d=d.loc[good].copy()
    d['decision_at']=d.timestamp.dt.floor('h')+pd.Timedelta(hours=1)
    h=d.sort_values('timestamp').groupby('decision_at',sort=True).tail(1).copy()
    h=h[(h.decision_at.dt.year>=2024)&(h.decision_at.dt.year<=2025)]
    h['age_minutes']=(h.decision_at-h.timestamp).dt.total_seconds()/60
    h=h[h.age_minutes<=60].copy()
    h.to_csv(out/'BTCUSDT_metrics_H1_2024_2025.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    audit['hourly_rows_by_year']={str(k):int(v) for k,v in h.decision_at.dt.year.value_counts().sort_index().items()}
    audit['hourly_expected_by_year']={'2024':8784,'2025':8760}
    audit['hourly_csv_sha256']=sha(out/'BTCUSDT_metrics_H1_2024_2025.csv.gz')
    (out/'metrics_audit.json').write_text(json.dumps(audit,indent=2))
    (out/'manifest.json').write_text(json.dumps({'algorithm':'last observed 5m metric per completed UTC hour; decision at next hour boundary; no fill','source':str(source.name),'source_sha256':EXPECTED,'outputs':{'BTCUSDT_metrics_5m.csv.gz':audit['normalized_csv_sha256'],'BTCUSDT_metrics_H1_2024_2025.csv.gz':audit['hourly_csv_sha256']},'python':sys.version,'pandas':pd.__version__,'pyarrow':__import__('pyarrow').__version__,'audit':audit},indent=2))
    return h,audit

def evaluate(h, price_file,out):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from core.market_mechanics.state import build_market_state
    from core.market_mechanics.regime import classify_regime
    from core.market_mechanics.context import classify_context
    from core.scientific.block_bootstrap import moving_block_mean_ci
    raw=json.loads(Path(price_file).read_text()); bars=[]
    for x in raw:
        x=x.copy();x['time']=pd.Timestamp(x['time']).to_pydatetime();bars.append(x)
    rows=[]
    metric=h.set_index('decision_at')
    for i in range(80,len(bars)):
        decision=pd.Timestamp(bars[i]['time'])+pd.Timedelta(hours=1)
        if decision not in metric.index:continue
        try:
            state=build_market_state('BTCUSDT',bars[i-80:i+1],source_id='research/data/BTCUSDT_1h_2025.json',observed_at=decision.to_pydatetime(),as_of=decision.to_pydatetime())
            regime=classify_regime(state); context=classify_context(state)
        except ValueError:continue
        m=metric.loc[decision]; prior=metric.loc[decision-pd.Timedelta(hours=1)] if decision-pd.Timedelta(hours=1) in metric.index else None
        row={'decision_at':decision,'source_metric_at':m.timestamp,'regime':regime.structure+'_'+regime.direction+'_'+regime.volatility,'market_state':state.range_status,'market_context':context.range_location,'participation':context.participation,'oi': 'rising' if prior is not None and m.sum_open_interest>prior.sum_open_interest else 'falling' if prior is not None and m.sum_open_interest<prior.sum_open_interest else 'unknown','positioning':'top_long' if m.sum_toptrader_long_short_ratio>1 and m.count_toptrader_long_short_ratio>1 and m.count_long_short_ratio>1 else 'top_short' if m.sum_toptrader_long_short_ratio<1 and m.count_toptrader_long_short_ratio<1 and m.count_long_short_ratio<1 else 'mixed','taker':'buy' if m.sum_taker_long_short_vol_ratio>1 else 'sell' if m.sum_taker_long_short_vol_ratio<1 else 'neutral'}
        for c in FIELDS:row[c]=m[c]
        for horizon in HORIZONS:
            # Entry at next bar open; contiguous hourly source required. No invented gap returns.
            if i+horizon<len(bars) and pd.Timestamp(bars[i+horizon]['time'])-pd.Timestamp(bars[i+1]['time'])==pd.Timedelta(hours=horizon-1):
                row[f'ret_{horizon}h']=bars[i+horizon]['close']/bars[i+1]['open']-1
            else:row[f'ret_{horizon}h']=np.nan
        rows.append(row)
    panel=pd.DataFrame(rows);panel.to_csv(out/'BTCUSDT_H1_2025_joined.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    result=[]
    for name,extra in VARIANTS.items():
        keys=['regime',*extra]
        for group,part in panel.groupby(keys,dropna=False):
            if not isinstance(group,tuple):group=(group,)
            for horizon in HORIZONS:
                values=part[f'ret_{horizon}h'].dropna().to_numpy();n=len(values)
                ci=moving_block_mean_ci(values,block_size=24,resamples=1000,seed=1729).to_dict() if n>=50 else None
                result.append({'variant':name,'cell':'|'.join(map(str,group)),'horizon_h':horizon,'n':n,'coverage':n/len(panel),'mean_forward_return':float(values.mean()) if n else None,'positive_return_fraction':float((values>0).mean()) if n else None,'ci95_low':ci['lower'] if ci else None,'ci95_high':ci['upper'] if ci else None,'status':'exploratory_2025_only'})
    pd.DataFrame(result).to_csv(out/'ABLATION_2025_EXPLORATORY.csv',index=False)
    return {'joined_rows':len(panel),'price_source_sha256':sha(price_file),'ablation_cells':len(result),'qualified_n50':sum(x['n']>=50 for x in result),'comparison_2024_2025':'blocked_missing_2024_OHLCV','sign_persistence':'not_estimable','effect_size_stability':'not_estimable','sign_flips_explained':'not_estimable'}

def main():
    p=argparse.ArgumentParser();p.add_argument('parquet',type=Path);p.add_argument('--price-2025',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    h,audit=normalize(a.parquet,a.out)
    result=evaluate(h,a.price_2025,a.out) if a.price_2025 else {'comparison_2024_2025':'blocked_missing_2024_OHLCV'}
    (a.out/'evaluation_manifest.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'audit':audit,'evaluation':result},indent=2))
if __name__=='__main__':main()
