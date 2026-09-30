"""Frozen 2024→2025 metric ablations; no threshold selection from 2024 labels."""
import hashlib,json,sys,argparse,zipfile,io
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.market_mechanics.state import build_market_state
from core.market_mechanics.regime import classify_regime
from core.market_mechanics.context import classify_context
from core.scientific.block_bootstrap import moving_block_mean_ci
from scripts.metrics_2024_2025 import HORIZONS,VARIANTS,FIELDS,sha,evaluate

BLOB='629859ca96ea5e13816c10ce74bdd48e01ba93dd'

def validate(source,out):
    b=source.read_bytes();blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
    if blob!=BLOB:raise ValueError(f'Git blob mismatch: {blob}')
    d=pd.read_csv(source)
    if list(d.columns)!=['Date','Open','High','Low','Close','Volume']:raise ValueError('unexpected source columns')
    t=pd.to_datetime(d.Date,format='%d-%m-%Y %H:%M',utc=True,errors='raise')
    if len(d)!=17544 or sorted(t.dt.year.unique())!=[2024,2025]:raise ValueError('unexpected source coverage')
    d=d.loc[t.dt.year==2024].copy();t=t[t.dt.year==2024].reset_index(drop=True);d=d.reset_index(drop=True)
    expected=pd.date_range('2024-01-01',periods=8784,freq='h',tz='UTC')
    if len(d)!=8784 or t.duplicated().any() or not t.equals(pd.Series(expected)):
        raise ValueError('2024 must be 8784 unique contiguous hours exact UTC bounds')
    vals=d[['Open','High','Low','Close','Volume']].to_numpy(dtype=float)
    o,h,l,c,v=vals.T
    if not np.isfinite(vals).all() or np.any(vals[:,:4]<=0) or np.any(v<0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(l>h):raise ValueError('invalid OHLCV')
    clean=pd.DataFrame({'time':t.dt.strftime('%Y-%m-%dT%H:%M:%S+00:00'),'open':o,'high':h,'low':l,'close':c,'volume':v})
    out.mkdir(parents=True,exist_ok=True)
    path=out/'BTCUSDT_USDM_H1_2024.csv';clean.to_csv(path,index=False,float_format='%.10g',lineterminator='\n')
    manifest={'source':'SubhayanBiswas/Binance-Vision-Sample-Data BTCUSDT_1h_Cleaned.csv','source_git_blob_sha1':blob,'source_sha256':sha(source),'normalized_sha256':sha(path),'rows':len(clean),'first_utc':clean.time.iloc[0],'last_utc':clean.time.iloc[-1],'duplicates':0,'gaps':0,'invalid_ohlcv':0,'normalization':'Date strict day-month-year UTC; 2024 only; columns time/open/high/low/close/volume; no fill or corrections'}
    (out/'BTCUSDT_USDM_H1_2024_manifest.json').write_text(json.dumps(manifest,indent=2))
    return clean,manifest

def validate_2025(source,out):
    d=pd.read_csv(source);t=pd.to_datetime(d.Date,format='%d-%m-%Y %H:%M',utc=True)
    d=d.loc[t.dt.year==2025].reset_index(drop=True);t=t[t.dt.year==2025].reset_index(drop=True)
    expected=pd.date_range('2025-01-01',periods=8760,freq='h',tz='UTC')
    vals=d[['Open','High','Low','Close','Volume']].to_numpy(float);o,h,l,c,v=vals.T
    if len(d)!=8760 or not t.equals(pd.Series(expected)) or not np.isfinite(vals).all() or np.any(vals[:,:4]<=0) or np.any(v<0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(l>h):raise ValueError('invalid 2025 futures source')
    clean=pd.DataFrame({'time':t.dt.strftime('%Y-%m-%dT%H:%M:%S+00:00'),'open':o,'high':h,'low':l,'close':c,'volume':v})
    path=out/'BTCUSDT_USDM_H1_2025.csv';clean.to_csv(path,index=False,float_format='%.10g',lineterminator='\n')
    return clean,{'normalized_sha256':sha(path),'rows':8760,'first_utc':clean.time.iloc[0],'last_utc':clean.time.iloc[-1],'gaps':0,'duplicates':0,'invalid_ohlcv':0}

def official_compare(clean,official,out):
    files=sorted(official.glob('BTCUSDT-1h-2024-??.zip'))
    manifests=json.loads((official/'checksums_manifest.json').read_text()) if (official/'checksums_manifest.json').exists() else []
    if len(files)!=12 or len(manifests)!=12 or any(m['status']!='verified' for m in manifests):return {'status':'incomplete','verified_months':len(files)}
    for m in manifests:
        name=f"BTCUSDT-1h-2024-{m['month']:02d}.zip"
        z=official/name;check=official/(name+'.CHECKSUM')
        if sha(z)!=check.read_text().split()[0] or sha(z)!=m['zip_sha256']:
            raise ValueError(f'official checksum mismatch: {name}')
    raw=pd.concat([pd.read_csv(io.BytesIO(zipfile.ZipFile(p).read(zipfile.ZipFile(p).namelist()[0]))) for p in files],ignore_index=True)
    # Binance open_time, OHLC, volume: preserve raw precision and audit equality against cleaned source.
    ts=pd.to_datetime(raw.iloc[:,0],unit='ms',utc=True)
    if len(raw)!=8784 or not ts.reset_index(drop=True).equals(pd.to_datetime(clean.time,utc=True).reset_index(drop=True)):raise ValueError('official timestamp mismatch')
    delta={}
    for j,col in enumerate(['open','high','low','close','volume'],1):
        x=raw.iloc[:,j].to_numpy(float);y=clean[col].to_numpy(float)
        delta[col]={'exact_numeric_mismatches':int(np.sum(x!=y)),'max_abs_difference':float(np.max(np.abs(x-y))),'max_relative_difference':float(np.max(np.abs(x-y)/np.maximum(np.abs(x),1e-12)))}
    result={'status':'verified_checksums_and_compared','official_months':12,'comparisons':delta}
    (out/'official_comparison.json').write_text(json.dumps(result,indent=2))
    return result

def panel_2024(clean,metrics,out):
    bars=[]
    for x in clean.to_dict('records'):
        x['time']=pd.Timestamp(x['time']).to_pydatetime();bars.append(x)
    metric=metrics.set_index('decision_at');rows=[]
    for i in range(80,len(bars)):
        decision=pd.Timestamp(bars[i]['time'])+pd.Timedelta(hours=1)
        if decision not in metric.index:continue
        state=build_market_state('BTCUSDT',bars[i-80:i+1],source_id='BTCUSDT_USDM_H1_2024.csv',observed_at=decision.to_pydatetime(),as_of=decision.to_pydatetime())
        regime=classify_regime(state);context=classify_context(state)
        m=metric.loc[decision];prior=metric.loc[decision-pd.Timedelta(hours=1)] if decision-pd.Timedelta(hours=1) in metric.index else None
        row={'decision_at':decision,'source_metric_at':m.timestamp,'regime':regime.structure+'_'+regime.direction+'_'+regime.volatility,'market_state':state.range_status,'market_context':context.range_location,'participation':context.participation,'oi':'rising' if prior is not None and m.sum_open_interest>prior.sum_open_interest else 'falling' if prior is not None and m.sum_open_interest<prior.sum_open_interest else 'unknown','positioning':'top_long' if m.sum_toptrader_long_short_ratio>1 and m.count_toptrader_long_short_ratio>1 and m.count_long_short_ratio>1 else 'top_short' if m.sum_toptrader_long_short_ratio<1 and m.count_toptrader_long_short_ratio<1 and m.count_long_short_ratio<1 else 'mixed','taker':'buy' if m.sum_taker_long_short_vol_ratio>1 else 'sell' if m.sum_taker_long_short_vol_ratio<1 else 'neutral'}
        for c in FIELDS:row[c]=m[c]
        for horizon in HORIZONS:
            row[f'ret_{horizon}h']=bars[i+horizon]['close']/bars[i+1]['open']-1 if i+horizon<len(bars) else np.nan
        rows.append(row)
    panel=pd.DataFrame(rows);panel.to_csv(out/'BTCUSDT_H1_2024_joined.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    return panel

def ablate(panel,out):
    result=[]
    for name,extra in VARIANTS.items():
        for group,part in panel.groupby(['regime',*extra],dropna=False):
            if not isinstance(group,tuple):group=(group,)
            for horizon in HORIZONS:
                values=part[f'ret_{horizon}h'].dropna().to_numpy();n=len(values)
                ci=moving_block_mean_ci(values,block_size=24,resamples=1000,seed=1729).to_dict() if n>=50 else None
                result.append({'variant':name,'cell':'|'.join(map(str,group)),'horizon_h':horizon,'n':n,'coverage':n/len(panel),'mean_forward_return':float(values.mean()) if n else None,'positive_return_fraction':float((values>0).mean()) if n else None,'ci95_low':ci['lower'] if ci else None,'ci95_high':ci['upper'] if ci else None,'status':'2024_holdout_under_frozen_protocol'})
    d=pd.DataFrame(result);d.to_csv(out/'ABLATION_2024_FROZEN.csv',index=False);return d

def compare(a,b,out):
    paired=a.merge(b,on=['variant','cell','horizon_h'],suffixes=('_2024','_2025'))
    qualified=paired[(paired.n_2024>=50)&(paired.n_2025>=50)].copy()
    qualified['same_sign']=np.sign(qualified.mean_forward_return_2024)==np.sign(qualified.mean_forward_return_2025)
    qualified['effect_magnitude_ratio']=np.minimum(abs(qualified.mean_forward_return_2024),abs(qualified.mean_forward_return_2025))/np.maximum(abs(qualified.mean_forward_return_2024),abs(qualified.mean_forward_return_2025)).replace(0,np.nan)
    qualified['sign_flip']=~qualified.same_sign
    qualified.to_csv(out/'PAIRED_2024_2025_N50.csv',index=False)
    summary=[]
    for name,extra in VARIANTS.items():
        left=a[a.variant==name];right=b[b.variant==name];p=qualified[qualified.variant==name]
        # Only cells with adequate N in both periods; additional partitions are penalized by coverage and attrition.
        summary.append({'variant':name,'feature_count':len(extra),'cells_2024':len(left)//5,'cells_2025':len(right)//5,'paired_qualified_cells_horizons':len(p),'same_sign':int(p.same_sign.sum()),'sign_flips':int(p.sign_flip.sum()),'sign_persistence':float(p.same_sign.mean()) if len(p) else None,'median_effect_magnitude_ratio':float(p.effect_magnitude_ratio.median()) if len(p) else None,'median_coverage_2024':float(p.coverage_2024.median()) if len(p) else None,'median_coverage_2025':float(p.coverage_2025.median()) if len(p) else None,'ci_excludes_zero_both_same_sign':int(((p.ci95_low_2024>0)&(p.ci95_low_2025>0)|(p.ci95_high_2024<0)&(p.ci95_high_2025<0)).sum()),'ci_excludes_zero_2024':int(((p.ci95_low_2024>0)|(p.ci95_high_2024<0)).sum())})
    s=pd.DataFrame(summary);s.to_csv(out/'ABLATION_STABILITY_SUMMARY.csv',index=False)
    return s

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--repo',type=Path,required=True);p.add_argument('--official',type=Path);a=p.parse_args()
    out=a.repo/'research/metrics_2024_2025';clean,manifest=validate(a.source,out)
    verified=official_compare(clean,a.official,out) if a.official else {'status':'not_attempted'}
    metric=pd.read_csv(out/'BTCUSDT_metrics_H1_2024_2025.csv.gz',parse_dates=['timestamp','decision_at'])
    panel=panel_2024(clean,metric,out);x=ablate(panel,out)
    clean25,manifest25=validate_2025(a.source,out)
    bars25=clean25.to_dict('records');path25=out/'BTCUSDT_USDM_H1_2025.json';path25.write_text(json.dumps(bars25,separators=(',',':')))
    eval25=out/'recomputed_2025';eval25.mkdir(exist_ok=True)
    evaluation25=evaluate(metric,path25,eval25)
    y=pd.read_csv(eval25/'ABLATION_2025_EXPLORATORY.csv')
    y.to_csv(out/'ABLATION_2025_USDM_FROZEN.csv',index=False)
    summary=compare(x,y,out)
    manifest['normalized_2025']=manifest25;manifest['recomputed_2025']={k:v for k,v in evaluation25.items() if k not in ('comparison_2024_2025','sign_persistence','effect_size_stability','sign_flips_explained')}
    manifest['historical_2025_spot_like_source_excluded']='original research/data/BTCUSDT_1h_2025.json first bar differs from USD-M futures; original exploratory table preserved, not used in comparison'
    manifest.update({'official_comparison':verified,'joined_rows_2024':len(panel),'protocol':'scripts/metrics_2024_2025.py frozen HORIZONS, VARIANTS, Regime, MarketState, MarketContext, bins, n50, bootstrap 24/1000/1729; 2025 outputs unmodified','2025_ablation_sha256':sha(out/'ABLATION_2025_USDM_FROZEN.csv')})
    (out/'confirmatory_manifest.json').write_text(json.dumps(manifest,indent=2));print(summary.to_string(index=False));print(verified)
if __name__=='__main__':main()
