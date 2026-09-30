import numpy as np
import pandas as pd
import pytest
from core.scientific.calendar_block_inference import calendar_block_simultaneous_ci

def frame(n=600):
    t=pd.date_range('2027-01-01',periods=n,freq='h',tz='UTC')
    rng=np.random.default_rng(7)
    x=pd.DataFrame({'decision_at':t,'target':np.arange(n)%2==0,'control':np.arange(n)%2==1})
    for h in (1,4,12,24,48):x[f'ret_{h}h']=rng.normal(0,.01,n)
    return x

def test_calendar_gap_is_visible_and_joint_intervals_deterministic():
    x=frame().drop(index=[11,12]);a=calendar_block_simultaneous_ci(x,target_col='target',comparator_col='control',block_hours=72,resamples=100,min_each=100)
    b=calendar_block_simultaneous_ci(x,target_col='target',comparator_col='control',block_hours=72,resamples=100,min_each=100)
    assert a==b and a['missing_calendar_hours']==2
    assert len(a['estimates'])==5
    assert all(e['simultaneous_low']<e['difference']<e['simultaneous_high'] for e in a['estimates'])

def test_rejects_overlap_and_duplicate_time():
    x=frame();x.loc[0,'control']=True
    with pytest.raises(ValueError,match='overlap'):calendar_block_simultaneous_ci(x,target_col='target',comparator_col='control',block_hours=72,resamples=100,min_each=100)
    y=frame();y.loc[1,'decision_at']=y.loc[0,'decision_at']
    with pytest.raises(ValueError,match='unique'):calendar_block_simultaneous_ci(y,target_col='target',comparator_col='control',block_hours=72,resamples=100,min_each=100)

def test_rejects_underpowered_arm():
    x=frame();x['target']=False
    with pytest.raises(ValueError,match='minimum N'):calendar_block_simultaneous_ci(x,target_col='target',comparator_col='control',block_hours=72,resamples=100,min_each=100)
