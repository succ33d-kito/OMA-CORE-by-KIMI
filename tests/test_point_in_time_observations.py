import json
import sqlite3
from datetime import datetime, timedelta, timezone
import pytest
from core.scientific.prospective_receipts import append_observation, load_observations, is_causally_available
from core.market_mechanics.binance_live_adapter import capture_price_receipt

T = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)

def fixture_args():
    start = int((T-timedelta(hours=1)).timestamp()*1000)
    row = [start,'100','101','99','100','5',start+3599999,'500',2,'2','200','0']
    return dict(source='https://fapi.binance.com/fapi/v1/klines', instrument='BTCUSDT', feature='Price/OHLCV',
        event_time=T, source_metric_at=T-timedelta(milliseconds=1), received_at=T+timedelta(seconds=2),
        payload=dict(time=(T-timedelta(hours=1)).isoformat(),open=100.,high=101.,low=99.,close=100.,volume=5.,open_time_ms=start,close_time_ms=start+3599999),
        provenance=dict(contract='binance-usdm-h1-rest-v1',bar_closed=True,raw_server_time=json.dumps({'serverTime':int(T.timestamp()*1000)}),raw_klines=json.dumps([row]),server_received_at=(T+timedelta(seconds=1)).isoformat(),klines_requested_at=(T+timedelta(seconds=1)).isoformat()),
        clock=lambda:T+timedelta(seconds=3))


def test_closed_receipt_and_restart(tmp_path):
    p=tmp_path/'receipts.db'; x=append_observation(p,**fixture_args())
    assert is_causally_available(p,x['id'],T+timedelta(seconds=4))
    assert load_observations(p)[x['id']]==x
    assert load_observations(p)==load_observations(p)
    assert not is_causally_available(p,x['id'],T+timedelta(seconds=1))
    assert not is_causally_available(p,x['id'],datetime(2024,1,1,tzinfo=timezone.utc))
    assert not is_causally_available(p,x['id'],T.replace(tzinfo=None))


@pytest.mark.parametrize('case',['open','provenance','future','naive','hash','unknown','wrong_close'])
def test_fail_closed(tmp_path,case):
    p=tmp_path/'r.db'; a=fixture_args()
    if case=='open':a['provenance']['bar_closed']=False
    if case=='provenance':a['provenance']={'unverified':True}
    if case=='future':a['event_time']=T+timedelta(days=1)
    if case=='naive':a['received_at']=T.replace(tzinfo=None)
    if case=='unknown':a['feature']='OpenInterest'
    if case=='wrong_close':a['payload']['close_time_ms']-=1
    if case in ['future','naive']:
        with pytest.raises(ValueError):append_observation(p,**a)
        return
    x=append_observation(p,**a)
    if case=='hash':
        with sqlite3.connect(p) as db:
            db.execute('DROP TRIGGER observations_v2_no_update')
            d=json.loads(db.execute('SELECT body FROM observations_v2').fetchone()[0]);d['payload']['close']=900
            db.execute('UPDATE observations_v2 SET body=?',(json.dumps(d),))
    assert not is_causally_available(p,x['id'],T+timedelta(seconds=10))


def test_duplicate_conflict_and_append_only(tmp_path):
    p=tmp_path/'r.db';a=fixture_args();first=append_observation(p,**a)
    a['clock']=lambda:T+timedelta(seconds=10)
    assert append_observation(p,**a)==first
    a['payload']['close']=100.5
    with pytest.raises(ValueError,match='conflicting'):append_observation(p,**a)
    with sqlite3.connect(p) as db:
        with pytest.raises(sqlite3.IntegrityError,match='append-only'):db.execute('DELETE FROM observations_v2')


def test_derived_max_and_unknown_dependencies(tmp_path):
    p=tmp_path/'r.db';x=append_observation(p,**fixture_args())
    a=fixture_args();a.update(feature='test-derived',derived=True,dependencies=[x['id']],clock=lambda:T+timedelta(seconds=8))
    d=append_observation(p,**a)
    assert d['available_at']==max(x['available_at'],d['computed_at'])
    assert not is_causally_available(p,d['id'],T+timedelta(seconds=7))
    assert is_causally_available(p,d['id'],T+timedelta(seconds=9))
    a.update(feature='missing-dependency',dependencies=['absent'])
    u=append_observation(p,**a)
    assert u['available_at'] is None
    assert not is_causally_available(p,u['id'],T+timedelta(seconds=20))
    a.update(feature='OpenInterest',derived=False,dependencies=[])
    u=append_observation(p,**a)
    a.update(feature='unknown-derived',derived=True,dependencies=[u['id']])
    d=append_observation(p,**a)
    assert d['available_at'] is None
    assert not is_causally_available(p,d['id'],T+timedelta(seconds=20))


def test_historical_download_cannot_be_receipt(tmp_path):
    a=fixture_args();a['event_time']=datetime(2024,1,1,tzinfo=timezone.utc)
    with pytest.raises(ValueError,match='historical backfill'):append_observation(tmp_path/'r.db',**a)


def test_unchecked_raw_dependencies_and_report_overwrite_rejected(tmp_path):
    from scripts.probe_price_point_in_time import run
    a=fixture_args(); a['dependencies']=['absent']
    with pytest.raises(ValueError,match='unchecked dependencies'):
        append_observation(tmp_path/'r.db',**a)
    report=tmp_path/'probe.json'; report.write_text('prior evidence')
    with pytest.raises(FileExistsError):run(tmp_path/'r.db',report)
    assert report.read_text()=='prior evidence'


def test_capture_uses_only_two_public_price_requests(tmp_path):
    a=fixture_args();calls=[]
    class Response:
        status_code=200
        def __init__(self,text):self.text=text
        def raise_for_status(self):pass
    class Session:
        def get(self,url,**kwargs):
            calls.append(url)
            return Response(a['provenance']['raw_server_time'] if url.endswith('/time') else a['provenance']['raw_klines'])
    x=capture_price_receipt(Session(),tmp_path/'r.db',clock=lambda:T+timedelta(seconds=5))
    assert len(calls)==2
    assert is_causally_available(tmp_path/'r.db',x['id'],T+timedelta(seconds=6))
