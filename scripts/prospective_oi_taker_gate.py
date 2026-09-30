"""Prospective, pre-registered OI+taker hypothesis. No network or order execution."""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.market_mechanics.state import build_market_state
from core.market_mechanics.regime import classify_regime
from core.scientific.calendar_block_inference import calendar_block_simultaneous_ci
from scripts.metrics_2024_2025 import FIELDS,sha

HERE=Path(__file__).resolve().parents[1]
PROTOCOL=HERE/'research/metrics_2024_2025/PROSPECTIVE_H1_PREREGISTRATION.json'
FROZEN_PROTOCOL_SHA256='012a80dcfd4566c7906c61a03f2c5ce3991c31481d2bdb4d87e6855d6005bc46'

def evaluate(price_path,metric_path,output,*,protocol_path=PROTOCOL):
    if sha(protocol_path)!=FROZEN_PROTOCOL_SHA256:raise ValueError('frozen protocol SHA-256 mismatch')
    spec=json.loads(protocol_path.read_text());cutoff=pd.Timestamp(spec['holdout_start_utc'])
    bars=pd.read_csv(price_path);metrics=pd.read_csv(metric_path)
    if list(bars.columns)!=['time','available_at','open','high','low','close','volume'] or list(metrics.columns)!=['timestamp','available_at',*FIELDS]:raise ValueError('unexpected source schema')
    bt=pd.to_datetime(bars.time,utc=True,errors='raise');mt=pd.to_datetime(metrics.timestamp,utc=True,errors='raise')
    ba=pd.to_datetime(bars.available_at,utc=True,errors='raise');ma=pd.to_datetime(metrics.available_at,utc=True,errors='raise')
    if (ba<bt+pd.Timedelta(hours=1)).any() or (ma<mt).any():raise ValueError('availability precedes observation or bar close')
    if bt.duplicated().any() or not bt.is_monotonic_increasing or (bt.diff().dropna()!=pd.Timedelta(hours=1)).any():raise ValueError('bars must be unique contiguous H1')
    if mt.duplicated().any() or not mt.is_monotonic_increasing:raise ValueError('metric observations must be unique ordered')
    bv=bars[['open','high','low','close','volume']].to_numpy(float);o,h,l,c,v=bv.T
    if not np.isfinite(bv).all() or np.any(bv[:,:4]<=0) or np.any(v<0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(l>h):raise ValueError('invalid OHLCV')
    metrics=metrics.copy();metrics['timestamp']=mt;metrics['available_at']=ma
    good=np.isfinite(metrics[FIELDS].to_numpy(float)).all(axis=1)&(metrics[FIELDS].to_numpy(float)>0).all(axis=1)
    metrics=metrics.loc[good].copy()
    metrics['decision_at']=metrics.timestamp.dt.floor('h')+pd.Timedelta(hours=1)
    metrics=metrics[metrics.available_at<=metrics.decision_at+pd.Timedelta(minutes=5)].copy()
    last=metrics.groupby('decision_at',sort=True).tail(1).set_index('decision_at')
    bars=bars.copy();bars['time']=bt;bars['available_at']=ba;records=bars.to_dict('records');source_digest=sha(price_path)
    rows=[]
    for i in range(80,len(records)-49):
        decision=bt.iloc[i]+pd.Timedelta(hours=1)
        if decision<cutoff or decision not in last.index:continue
        if not window_available(ba.iloc[i-80:i+1], decision+pd.Timedelta(minutes=5)):continue
        m=last.loc[decision]
        if (decision-m.timestamp)>pd.Timedelta(hours=1) or m.available_at>decision+pd.Timedelta(minutes=5):continue
        prior=last.loc[decision-pd.Timedelta(hours=1)] if decision-pd.Timedelta(hours=1) in last.index else None
        if prior is None or decision-pd.Timedelta(hours=1)-prior.timestamp>pd.Timedelta(hours=1):continue
        state=build_market_state('BTCUSDT',records[i-80:i+1],source_id=source_digest,observed_at=(decision+pd.Timedelta(minutes=5)).to_pydatetime(),as_of=(decision+pd.Timedelta(minutes=5)).to_pydatetime())
        reg=classify_regime(state)
        baseline=reg.structure=='range'
        oi_up=m.sum_open_interest>prior.sum_open_interest
        oi_change=m.sum_open_interest!=prior.sum_open_interest
        target=bool(baseline and oi_change and oi_up and m.sum_taker_long_short_vol_ratio>1)
        comparator=bool(baseline and oi_change and not target)
        row={'decision_at':decision,'actual_decision_at':decision+pd.Timedelta(minutes=5),'bar_available_at':ba.iloc[i],'metric_observed_at':m.timestamp,'metric_available_at':m.available_at,'regime':reg.structure+'_'+reg.direction+'_'+reg.volatility,'target':target,'comparator':comparator}
        for horizon in spec['family_horizons_hours']:
            row[f'ret_{horizon}h']=records[i+horizon+1]['close']/records[i+2]['open']-1
        rows.append(row)
    if not rows:raise ValueError('no eligible prospective rows after cutoff')
    panel=pd.DataFrame(rows)
    if panel.decision_at.max()-panel.decision_at.min()<pd.Timedelta(hours=spec['minimum_calendar_hours']-1):raise ValueError('prospective minimum calendar duration not met')
    result=calendar_block_simultaneous_ci(panel,target_col='target',comparator_col='comparator',horizons=tuple(spec['family_horizons_hours']),block_hours=168,resamples=2000,min_each=spec['minimum_n_each_arm_each_horizon'],confidence=.95,seed=1729)
    primary=next(e for e in result['estimates'] if e['horizon_h']==spec['primary_horizon_hours'])
    result['research_gate_pass']=primary['simultaneous_low']>0 and primary['mean_target']-.001>0
    result['promotion']='none';result['protocol_sha256']=sha(protocol_path);result['price_sha256']=sha(price_path);result['metrics_sha256']=sha(metric_path)
    output.mkdir(parents=True,exist_ok=True)
    panel.to_csv(output/'prospective_panel.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    (output/'prospective_gate.json').write_text(json.dumps(result,indent=2))
    return result

def window_available(receipts, decision_at):
    """Every observation in the regime window must be known at the decision."""
    return bool(len(receipts) == 81 and receipts.notna().all() and (receipts <= decision_at).all())


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('bars',type=Path);parser.add_argument('metrics',type=Path);parser.add_argument('--out',type=Path,required=True);a=parser.parse_args()
    print(json.dumps(evaluate(a.bars,a.metrics,a.out),indent=2))
