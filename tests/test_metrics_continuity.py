import json
from datetime import datetime, timedelta, timezone

import pytest
from core.scientific import metrics_continuity as continuity
from core.scientific import metrics_h1_activation as activation
from core.scientific import metrics_h1_live_adapter as live

S=datetime(2026,10,11,13,tzinfo=timezone.utc)


@pytest.fixture
def state(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); root=tmp_path/'metrics-h1-v1'
    activation.activate(root,repo_root=repo,now=S-timedelta(minutes=20),dataset_role='PILOT')
    return root,repo


def capture(state,slot=S):
    def transport(url,*,params,**kwargs):
        key=next(k for k,v in live.METRIC_ENDPOINTS.items() if url.endswith(v))
        row={'symbol':'BTCUSDT','timestamp':int(slot.timestamp()*1000)-(300000 if key=='taker' else 0)}
        row.update({'sumOpenInterest':'100','sumOpenInterestValue':'10000'} if key=='oi' else {'buySellRatio':'1.4'} if key=='taker' else {'longShortRatio':'1.2'})
        return 200,url+'?symbol=BTCUSDT&period=5m&limit=5',json.dumps([row]).encode()
    return live.run_once(state[0],repo_root=state[1],transport=transport,clock=lambda:slot+timedelta(seconds=180))


def verify(state):
    return continuity.verify_slot(state[0],S,repo_root=state[1],now=S+timedelta(minutes=5))['status']


def snapshot(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_success_recomputed_read_only(state):
    assert capture(state)['status']=='SUCCESS'
    before=snapshot(state[0]); assert verify(state)=='SUCCESS'
    report=continuity.status(state[0],repo_root=state[1],now=S+timedelta(minutes=5))
    assert report['current_streak']==report['longest_streak']==1
    assert not report['METRICS_OPERATIONAL_READINESS_81H']
    assert snapshot(state[0])==before


@pytest.mark.parametrize('file',['attempt.json','result.json','capture/receipt.json','capture/available.json','capture/raw/oi.json','capture/raw/top_account.json','capture/raw/top_position.json','capture/raw/global.json','capture/raw/taker.json'])
def test_corruption_rejected_without_mutation(state,file):
    capture(state); path=state[0]/'attempts'/'20261011T130000Z'/file
    path.write_bytes(b'{}'); before=snapshot(state[0])
    assert verify(state)=='INVALID' and snapshot(state[0])==before


@pytest.mark.parametrize('field,value',[('dataset_role','CONFIRMATION'),('source_period_end','2026-10-11T14:00:00+00:00'),('normalized_metrics',{}),('provider','https://evil.example')])
def test_rehashed_receipt_cannot_override_contract(state,field,value):
    capture(state); path=state[0]/'attempts'/'20261011T130000Z'/'capture'/'receipt.json'
    body=json.loads(path.read_bytes()); body[field]=value; body.pop('receipt_id')
    body['receipt_id']=continuity._digest(body); path.write_bytes(activation._canonical(body))
    assert verify(state)=='INVALID'


def test_availability_without_result_is_incomplete(state):
    capture(state); path=state[0]/'attempts'/'20261011T130000Z'
    (path/'result.json').unlink(); before=snapshot(state[0])
    assert verify(state)=='INCOMPLETE' and snapshot(state[0])==before


def test_failed_with_leftover_valid_capture_never_counts(state):
    capture(state); path=state[0]/'attempts'/'20261011T130000Z'/'result.json'
    result=json.loads(path.read_bytes()); result.pop('capture'); result.pop('result_id')
    result.update(status='FAILED',error='late publication'); result['result_id']=continuity._digest(result)
    path.write_bytes(activation._canonical(result))
    assert verify(state)=='FAILED'


def test_missing_deadline_and_no_backfill(state):
    before=snapshot(state[0]); assert verify(state)=='MISSED_SLOT'
    assert continuity.verify_slot(state[0],S,repo_root=state[1],now=S+timedelta(seconds=299))['status']=='NOT_DUE'
    assert snapshot(state[0])==before


def test_future_result_not_available_at_past_time(state):
    capture(state)
    assert continuity.verify_slot(state[0],S,repo_root=state[1],now=S)['status']=='INVALID'


def test_81_success_gate_and_gap_breaks_current_streak(state):
    for n in range(81): capture(state,S+timedelta(hours=n))
    now=S+timedelta(hours=80,minutes=5)
    report=continuity.status(state[0],repo_root=state[1],now=now)
    assert report['METRICS_OPERATIONAL_READINESS_81H'] is True
    assert report['current_streak']==report['longest_streak']==81
    report=continuity.status(state[0],repo_root=state[1],now=now+timedelta(hours=1))
    assert report['current_streak']==0 and report['longest_streak']==81
    assert report['counts']['MISSED_SLOT']==1 and report['research_gate']=='NOT_EVALUATED'
    assert report['EDGE']=='NOT_DEMONSTRATED'


def test_naive_clock_rejected(state):
    with pytest.raises(ValueError): continuity.status(state[0],repo_root=state[1],now=S.replace(tzinfo=None))
