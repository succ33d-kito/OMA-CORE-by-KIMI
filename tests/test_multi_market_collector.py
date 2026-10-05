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
