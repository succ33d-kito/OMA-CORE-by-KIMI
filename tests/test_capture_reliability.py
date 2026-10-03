import json
from datetime import timedelta
from types import SimpleNamespace

import pytest

from core.scientific.capture_clock import ClockHealthError, preflight
from core.market_mechanics.binance_live_adapter import capture_price_receipt
from core.scientific.prospective_receipts import load_observations
from scripts import capture_price_h1 as runner
from tests.test_point_in_time_observations import T, fixture_args


@pytest.mark.parametrize('start,end,server,elapsed', [
    (0,.1,.2,.1), (2,2.1,0,.1), (0,3,1,3), (0,-1,0,.1), (0,1,0,.1)])
def test_unreliable_clock(start,end,server,elapsed):
    with pytest.raises(ClockHealthError):
        preflight(T+timedelta(seconds=start), T+timedelta(seconds=end),
                  T+timedelta(seconds=server), elapsed)


class Session:
    def __init__(self, server=T):
        self.server = server
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        raw = (json.dumps({'serverTime':int(self.server.timestamp()*1000)})
               if url.endswith('/time') else fixture_args()['provenance']['raw_klines'])
        return SimpleNamespace(status_code=200, text=raw, raise_for_status=lambda:None)


@pytest.mark.parametrize('server', [T+timedelta(seconds=1), T-timedelta(seconds=2)])
def test_preflight_blocks_before_bar_or_ledger(tmp_path, server):
    session = Session(server)
    with pytest.raises(ClockHealthError):
        capture_price_receipt(session, tmp_path/'r.db', clock=lambda:T, monotonic=lambda:0)
    assert len(session.calls) == 1
    assert not (tmp_path/'r.db').exists()


def test_capture_real_times_restart_duplicates(tmp_path):
    db = tmp_path/'r.db'
    def capture():
        wall = iter(T+timedelta(seconds=s) for s in [0,.1,.1,.2,.2,.2,.2])
        mono = iter([0,.1,.1,.2,.2,.2,.2])
        return capture_price_receipt(Session(), db, clock=lambda:next(wall),
                                     monotonic=lambda:next(mono), expected_event_time=T)
    first = capture()
    assert first['received_at'] == (T+timedelta(seconds=.2)).isoformat()
    assert first['provenance']['clock_health']['contract'] == 'pit-clock-health-v1'
    assert capture() == first
    assert len(load_observations(db)) == 1


def test_retry_deadline_never_backdates(tmp_path):
    wall = iter(T+timedelta(seconds=s) for s in [0,.1,.1,121,121])
    mono = iter([0,.1,.1,121,121])
    with pytest.raises(ValueError, match='window exhausted'):
        capture_price_receipt(Session(), tmp_path/'r.db', clock=lambda:next(wall),
                             monotonic=lambda:next(mono), capture_deadline=T+timedelta(seconds=120))
    assert not (tmp_path/'r.db').exists()


@pytest.mark.parametrize('recover', [True,False])
def test_network_retries(tmp_path, monkeypatch, recover):
    current = [T+timedelta(seconds=5)]
    calls = []
    monkeypatch.setattr(runner, 'now', lambda:current[0])
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds:current.__setitem__(0,current[0]+timedelta(seconds=seconds)))
    def capture(*args, **kwargs):
        calls.append(current[0])
        assert kwargs['expected_event_time'] == T
        assert kwargs['capture_deadline'] == T+timedelta(seconds=125)
        if not recover or len(calls)<3:
            raise TimeoutError('network timeout')
        return {'id':'real-receipt'}
    monkeypatch.setattr(runner, 'capture_price_receipt', capture)
    result = runner.capture_slot(None, tmp_path/'r.db', tmp_path/'state', T+timedelta(seconds=5))
    assert result['status'] == ('SUCCESS' if recover else 'FAILED')
    assert len(calls) == (3 if recover else 6)
    assert max(calls) <= T+timedelta(seconds=125)


def test_sleep_logs_missing_slots_without_requests(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'now', lambda:T+timedelta(hours=3,seconds=200))
    monkeypatch.setattr(runner, 'attempt', lambda *a:pytest.fail('backfill attempted'))
    runner.capture_slot(None,tmp_path/'r.db',tmp_path/'state',T+timedelta(seconds=5))
    result = json.loads(next((tmp_path/'state'/'attempts').glob('*result.json')).read_text())
    assert result['status'] == 'MISSED_SLOT' and result['missed_slots'] == 4
    assert not (tmp_path/'r.db').exists()


def test_health_is_independent_of_process(tmp_path):
    report = dict(reference_at=T.isoformat(),last_receipt_at=None,runner={'at':T.isoformat()},
                  capture_running=True,ledger_integrity='PASS')
    assert runner.capture_health(report,tmp_path)['capture_health'] == 'DEGRADED'
    report['last_receipt_at']=T.isoformat()
    assert runner.capture_health(report,tmp_path)['capture_healthy']
    p=tmp_path/'attempts';p.mkdir()
    (p/'a-result.json').write_text(json.dumps(dict(status='FAILED',failure_kind='CLOCK',completed_at=T.isoformat())))
    health=runner.capture_health(report,tmp_path)
    assert health['capture_health']=='UNHEALTHY' and health['clock_failures']==1
    assert health['consecutive_failures']==1
    report['runner']['at']=(T-timedelta(seconds=61)).isoformat()
    assert not runner.capture_health(report,tmp_path)['capture_healthy']


def test_network_recovery_persists_actual_later_receipt(tmp_path, monkeypatch):
    current=[T+timedelta(seconds=5)]
    monkeypatch.setattr(runner,'now',lambda:current[0])
    monkeypatch.setattr(runner.time,'sleep',lambda s:current.__setitem__(0,current[0]+timedelta(seconds=s)))
    class Recovering(Session):
        failures=2
        def get(self,url,**kwargs):
            if self.failures:
                self.failures-=1
                raise TimeoutError('network unavailable')
            self.server=current[0]
            return super().get(url,**kwargs)
    def capture(session,ledger,**kwargs):
        return capture_price_receipt(session,ledger,clock=lambda:current[0],monotonic=lambda:0,**kwargs)
    monkeypatch.setattr(runner,'capture_price_receipt',capture)
    db=tmp_path/'r.db'
    result=runner.capture_slot(Recovering(),db,tmp_path/'state',T+timedelta(seconds=5))
    assert result['status']=='SUCCESS'
    receipt=next(iter(load_observations(db).values()))
    assert receipt['received_at']==(T+timedelta(seconds=45)).isoformat()
    assert receipt['provenance']['clock_health']['checked_at']==receipt['received_at']
    assert receipt['event_time']==T.isoformat()


def test_windows_sleep_request_released_on_error(monkeypatch):
    import ctypes
    calls=[]
    monkeypatch.setattr(runner.os,'name','nt')
    monkeypatch.setattr(ctypes,'windll',SimpleNamespace(kernel32=SimpleNamespace(
        SetThreadExecutionState=lambda flags:calls.append(flags) or 1)),raising=False)
    with pytest.raises(RuntimeError):
        with runner.prevent_sleep(True):
            raise RuntimeError('exit')
    assert calls==[0x80000001,0x80000000]

@pytest.mark.parametrize('elapsed', [float('nan'), float('inf'), -1])
def test_nonfinite_monotonic_fails_closed(elapsed):
    from core.scientific.capture_clock import continuous
    with pytest.raises(ClockHealthError):
        preflight(T, T, T, elapsed)
    with pytest.raises(ClockHealthError):
        continuous(T, T, elapsed)


def test_latency_cannot_hide_host_ahead():
    # True host offset can be 2 seconds: response generated at true +.5,
    # delivered at true +2; local request starts at +2, receives at +4.
    with pytest.raises(ClockHealthError, match='host clock ahead'):
        preflight(T+timedelta(seconds=2), T+timedelta(seconds=4),
                  T+timedelta(seconds=2.5), 2)
    evidence = preflight(T, T+timedelta(seconds=.2), T+timedelta(seconds=.1), .2)
    assert evidence['offset_lower_seconds'] == -.1
    assert evidence['offset_upper_seconds'] == .1


def test_compensated_jump_between_requests_rejected(tmp_path):
    samples = iter([(0,0),(.1,.1),(1,.1),(1.1,1.1),(1.1,1.1),(1.1,1.1)])
    elapsed = [0]
    def wall():
        seconds, elapsed[0] = next(samples)
        return T+timedelta(seconds=seconds)
    session = Session()
    with pytest.raises(ClockHealthError, match='discontinuity'):
        capture_price_receipt(session, tmp_path/'r.db', clock=wall,
                              monotonic=lambda:elapsed[0])
    assert len(session.calls) == 1
    assert not (tmp_path/'r.db').exists()


@pytest.mark.parametrize('start', [-.1,120.1])
def test_no_request_outside_window(tmp_path, start):
    session=Session(T+timedelta(seconds=start))
    with pytest.raises(ValueError):
        capture_price_receipt(session,tmp_path/'r.db',clock=lambda:T+timedelta(seconds=start),
                              capture_deadline=T+timedelta(seconds=120),monotonic=lambda:0)
    assert not session.calls
    assert not (tmp_path/'r.db').exists()


@pytest.mark.parametrize('admission', [1,121])
def test_ledger_lock_wait_rechecks_deadline_and_availability(tmp_path, monkeypatch, admission):
    from core.scientific import prospective_receipts as receipts
    current=[T]
    original=receipts._observation_db
    class Connection:
        def __init__(self, con): self.con=con
        def execute(self, sql, *args):
            result=self.con.execute(sql,*args)
            if sql=='BEGIN IMMEDIATE': current[0]=T+timedelta(seconds=admission)
            return result
        def __getattr__(self,name): return getattr(self.con,name)
    monkeypatch.setattr(receipts,'_observation_db',lambda path:Connection(original(path)))
    db=tmp_path/'r.db'
    options=dict(clock=lambda:current[0],monotonic=lambda:(current[0]-T).total_seconds(),
                 capture_deadline=T+timedelta(seconds=120),expected_event_time=T)
    if admission>120:
        with pytest.raises(ValueError,match='window exhausted'):
            capture_price_receipt(Session(),db,**options)
        assert receipts.load_observations(db)=={}
    else:
        item=capture_price_receipt(Session(),db,**options)
        assert item['received_at']==T.isoformat()
        assert item['available_at']==current[0].isoformat()
        assert not receipts.is_causally_available(db,item['id'],T)
        assert receipts.is_causally_available(db,item['id'],current[0])


@pytest.mark.parametrize('exit_kind', ['normal','early','exception','interrupt'])
def test_keep_awake_all_exit_paths(monkeypatch, exit_kind):
    import ctypes
    calls=[]
    monkeypatch.setattr(ctypes,'windll',SimpleNamespace(kernel32=SimpleNamespace(
        SetThreadExecutionState=lambda flags:calls.append(flags) or 1)),raising=False)
    def use():
        with runner.prevent_sleep(True):
            if exit_kind=='early': return
            if exit_kind=='exception': raise RuntimeError('exit')
            if exit_kind=='interrupt': raise KeyboardInterrupt()
    if exit_kind in ('exception','interrupt'):
        with pytest.raises(RuntimeError if exit_kind=='exception' else KeyboardInterrupt): use()
    else: use()
    assert calls==[0x80000001,0x80000000]


def test_early_slot_has_no_requests(tmp_path, monkeypatch):
    monkeypatch.setattr(runner,'now',lambda:T)
    monkeypatch.setattr(runner,'attempt',lambda *a:pytest.fail('early request'))
    assert runner.capture_slot(None,tmp_path/'r.db',tmp_path/'state',T+timedelta(seconds=5)) is None


def test_real_laptop_sequence_with_full_capture_and_health(tmp_path, monkeypatch):
    from tests.test_price_continuity import args_at
    from core.scientific.price_continuity import status
    current=[T]
    counts={}
    failed_hours={7,10,11,12,13} # 06 and 09--12 relative to 23.
    retry_hours={3,6} # 02 and 05.
    monkeypatch.setattr(runner,'now',lambda:current[0])
    monkeypatch.setattr(runner.time,'sleep',lambda s:current.__setitem__(0,current[0]+timedelta(seconds=s)))
    class ReplaySession:
        def get(self,url,**kwargs):
            index=int((runner.hour(current[0])-T).total_seconds()/3600)
            current[0]+=timedelta(seconds=.1)
            if url.endswith('/time'):
                counts[index]=counts.get(index,0)+1
                fail=index in failed_hours or (index in retry_hours and counts[index]==1)
                server=current[0]+timedelta(seconds=.01) if fail else current[0]-timedelta(seconds=.05)
                raw=json.dumps({'serverTime':int(server.timestamp()*1000)})
            else: raw=args_at(index)['provenance']['raw_klines']
            return SimpleNamespace(status_code=200,text=raw,raise_for_status=lambda:None)
    def capture(session, ledger, **kwargs):
        return capture_price_receipt(session,ledger,clock=lambda:current[0],
            monotonic=lambda:(current[0]-T).total_seconds(),**kwargs)
    monkeypatch.setattr(runner,'capture_price_receipt',capture)
    db,state=tmp_path/'r.db',tmp_path/'state'
    for index in range(15):
        current[0]=T+timedelta(hours=index,seconds=5)
        result=runner.capture_slot(ReplaySession(),db,state,current[0])
        report=status(db,state,current[0])
        report.update(capture_running=True,runner={'at':current[0].isoformat()})
        health=runner.capture_health(report,state)
        assert result['status']==('FAILED' if index in failed_hours else 'SUCCESS')
        assert health['capture_health']==('UNHEALTHY' if index in failed_hours else 'HEALTHY')
    assert counts=={i:6 if i in failed_hours else 2 if i in retry_hours else 1 for i in range(15)}
    assert len(load_observations(db))==10
    assert report['ledger_integrity']=='PASS'
    assert report['valid_price_receipts']==10
    assert not any(report[k] for k in ('conflicts','invalid','duplicates','out_of_order'))
    assert report['longest_streak']==7 and report['current_streak']==1
    assert health['missed_slots']==5
    assert health['clock_failures']==32
    assert health['consecutive_failures']==0
