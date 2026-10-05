from datetime import timedelta
import pytest
from core.scientific import multi_market_collector as r
from core.scientific import multi_market_capture as c
from tests.test_multi_market_capture import freeze, transport, rows, T


def test_restart_duplicate_and_integrity(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch)
    state=r.initialize(tmp_path/'state',tmp_path/'universe')
    slot=T+timedelta(hours=1)
    transport(monkeypatch,rows(),slot)
    assert r.run_slot(state,tmp_path/'universe',slot)=='COMPLETE'
    before={str(p):p.read_bytes() for p in state.rglob('*') if p.is_file()}
    assert r.initialize(state,tmp_path/'universe')==state
    assert r.run_slot(state,tmp_path/'universe',slot)=='DUPLICATE_NOOP'
    assert before=={str(p):p.read_bytes() for p in state.rglob('*') if p.is_file()}


def test_missed_slot_never_fetches(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); state=r.initialize(tmp_path/'state',tmp_path/'universe')
    monkeypatch.setattr(c,'_now',lambda:T+timedelta(hours=1,minutes=7))
    monkeypatch.setattr(c,'_http',lambda url:pytest.fail('no backfill request'))
    assert r.run_slot(state,tmp_path/'universe',T+timedelta(hours=1))=='MISSED_SLOT'
    r.recover(state,tmp_path/'universe')


def test_state_corruption_fails_closed(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); state=r.initialize(tmp_path/'state',tmp_path/'universe')
    (state/'config.json').write_bytes(b'{}')
    with pytest.raises(ValueError): r.initialize(state,tmp_path/'universe')


def test_incomplete_attempt_not_retried(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); state=r.initialize(tmp_path/'state',tmp_path/'universe')
    slot=T+timedelta(hours=1); path=state/'attempts'/slot.strftime('%Y%m%dT%H0000Z'); path.mkdir()
    c._write(path/'attempt.json',c._json(dict(slot=slot.isoformat(),kind='H1')))
    monkeypatch.setattr(c,'_http',lambda url:pytest.fail('no retry'))
    assert r.run_slot(state,tmp_path/'universe',slot)=='DUPLICATE_NOOP'


def test_next_target_strictly_future():
    assert r.next_target(T)==T+timedelta(hours=1,seconds=5)
    assert r.next_target(T+timedelta(minutes=59))==T+timedelta(hours=1,seconds=5)


def test_failed_capture_retained_without_retry(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); state=r.initialize(tmp_path/'state',tmp_path/'universe')
    slot=T+timedelta(hours=1)
    transport(monkeypatch,[{**rows()[0],'unknown':1}],slot)
    with pytest.raises(ValueError): r.run_slot(state,tmp_path/'universe',slot)
    assert r.run_slot(state,tmp_path/'universe',slot)=='DUPLICATE_NOOP'
    result=next((state/'attempts').glob('*/result.json'))
    assert r._unseal(result)=={'status':'FAILED','cycle_id':None}


def test_network_failure_then_next_slot_succeeds(tmp_path,monkeypatch):
    from urllib.error import URLError
    freeze(tmp_path,monkeypatch); state=r.initialize(tmp_path/'state',tmp_path/'universe')
    slot=T+timedelta(hours=1)
    transport(monkeypatch,rows(),slot)
    def offline(url): raise URLError('offline')
    monkeypatch.setattr(c,'_http',offline)
    with pytest.raises(c.NetworkCaptureError): r.run_slot(state,tmp_path/'universe',slot)
    before={str(p):p.read_bytes() for p in (state/'attempts').rglob('*') if p.is_file()}
    transport(monkeypatch,rows(),slot+timedelta(hours=1))
    assert r.run_slot(state,tmp_path/'universe',slot+timedelta(hours=1))=='COMPLETE'
    assert all(__import__('pathlib').Path(p).read_bytes()==v for p,v in before.items())
    assert r.run_slot(state,tmp_path/'universe',slot)=='DUPLICATE_NOOP'
    r.initialize(state,tmp_path/'universe')


def test_scheduler_continues_after_network_failure(tmp_path,monkeypatch):
    from contextlib import nullcontext
    monkeypatch.setattr(r,'runner_lock',lambda root:nullcontext())
    monkeypatch.setattr(r,'initialize',lambda *args:tmp_path)
    monkeypatch.setattr(r,'recover',lambda *args:None)
    monkeypatch.setattr(r,'health',lambda *args:None)
    times=iter([T+timedelta(minutes=59),T+timedelta(hours=1,seconds=5),
                T+timedelta(hours=1,seconds=6),T+timedelta(hours=2,seconds=5)])
    monkeypatch.setattr(c,'_now',lambda:next(times))
    seen=[]
    class Finished(Exception): pass
    def attempt(root,universe,slot):
        seen.append(slot)
        if len(seen)==1: raise c.NetworkCaptureError('offline')
        raise Finished()
    monkeypatch.setattr(r,'run_slot',attempt)
    with pytest.raises(Finished): r.run(tmp_path,tmp_path)
    assert seen==[T+timedelta(hours=1),T+timedelta(hours=2)]
