"""Calendar-time block inference for predeclared, matched conditional returns.

Resamples the entire UTC time axis jointly. Missing hours stay unobserved; labels,
returns and overlapping horizons move together. Research only; no trading action.
"""
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class MatchedEstimate:
    horizon_h: int
    n_target: int
    n_comparator: int
    mean_target: float
    mean_comparator: float
    difference: float
    simultaneous_low: float
    simultaneous_high: float
    bootstrap_se: float
    def to_dict(self): return asdict(self)

def calendar_block_simultaneous_ci(frame, *, target_col, comparator_col,
                                   horizons=(1,4,12,24,48),
                                   block_hours=168, resamples=2000,
                                   min_each=200, confidence=.95, seed=1729):
    """Studentized max-deviation CI across horizons; fixed masks, no filling.

    `frame` has decision_at, two disjoint boolean masks and ret_<h>h. Rows
    absent from the source remain absent after reindexing to the calendar grid.
    Each replicate draws whole contiguous calendar blocks for all hypotheses.
    """
    if block_hours < max(horizons) or resamples < 100 or min_each < 1 or not 0<confidence<1:
        raise ValueError('invalid frozen inference parameters')
    if target_col == comparator_col or not horizons or len(set(horizons))!=len(horizons):
        raise ValueError('distinct masks and unique horizons required')
    cols=['decision_at',target_col,comparator_col]+[f'ret_{h}h' for h in horizons]
    d=frame.loc[:,cols].copy()
    t=pd.to_datetime(d.decision_at,utc=True)
    if t.isna().any() or t.duplicated().any() or not t.is_monotonic_increasing or (t.dt.minute!=0).any() or (t.dt.second!=0).any():
        raise ValueError('unique, sorted UTC hourly decisions required')
    d.index=pd.DatetimeIndex(t);d=d.drop(columns='decision_at')
    if d[[target_col,comparator_col]].isna().any().any() or not all(pd.api.types.is_bool_dtype(d[c]) for c in [target_col,comparator_col]):
        raise ValueError('explicit boolean exposure masks required')
    if (d[target_col]&d[comparator_col]).any():raise ValueError('target/comparator overlap')
    for h in horizons:
        col=f'ret_{h}h'
        x=pd.to_numeric(d[col],errors='raise')
        if np.isinf(x).any():raise ValueError('infinite return')
        d[col]=x
    grid=pd.date_range(d.index[0],d.index[-1],freq='h',tz='UTC')
    d=d.reindex(grid)  # Missing hours remain NaN; never interpolate outcomes.
    if len(grid)<2*block_hours:raise ValueError('insufficient calendar duration')
    targets=d[target_col].eq(True).to_numpy(dtype=bool)
    controls=d[comparator_col].eq(True).to_numpy(dtype=bool)
    y=d[[f'ret_{h}h' for h in horizons]].to_numpy(dtype=float)
    valid=np.isfinite(y)
    mask_a=valid & targets[:,None];mask_b=valid & controls[:,None]
    na=mask_a.sum(axis=0);nb=mask_b.sum(axis=0)
    if np.any(na<min_each) or np.any(nb<min_each):raise ValueError('minimum N not met in both arms at every horizon')
    ya=np.where(mask_a,y,0.);yb=np.where(mask_b,y,0.)
    mean_a=ya.sum(axis=0)/na;mean_b=yb.sum(axis=0)/nb;theta=mean_a-mean_b
    rng=np.random.default_rng(seed);n=len(grid);starts=n-block_hours+1
    reps=np.empty((resamples,len(horizons)),dtype=float)
    for j in range(resamples):
        offsets=rng.integers(0,starts,size=(n+block_hours-1)//block_hours)
        indices=(offsets[:,None]+np.arange(block_hours)).reshape(-1)[:n]
        a=mask_a[indices].sum(axis=0);b=mask_b[indices].sum(axis=0)
        if np.any(a==0) or np.any(b==0):raise ValueError('bootstrap arm absent; insufficient coverage')
        reps[j]=ya[indices].sum(axis=0)/a-yb[indices].sum(axis=0)/b
    se=reps.std(axis=0,ddof=1)
    if np.any(se==0):raise ValueError('zero bootstrap variation')
    maximum=np.max(np.abs((reps-theta)/se),axis=1)
    critical=float(np.quantile(maximum,confidence,method='higher'))
    estimates=[MatchedEstimate(int(h),int(na[k]),int(nb[k]),float(mean_a[k]),float(mean_b[k]),float(theta[k]),float(theta[k]-critical*se[k]),float(theta[k]+critical*se[k]),float(se[k])) for k,h in enumerate(horizons)]
    return {'method':'joint-calendar-moving-block-max-t-v1','calendar_start':grid[0].isoformat(),
            'calendar_end':grid[-1].isoformat(),'observed_hours':len(frame),'calendar_hours':n,
            'missing_calendar_hours':n-len(frame),'block_hours':block_hours,'resamples':resamples,
            'confidence':confidence,'seed':seed,'family_horizons':list(horizons),
            'critical_value':critical,'estimates':[e.to_dict() for e in estimates]}
