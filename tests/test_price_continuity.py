import json
import sqlite3
from datetime import timedelta
import pytest
from tests.test_point_in_time_observations import fixture_args, T
from core.scientific.prospective_receipts import append_observation, load_observations
from core.scientific.price_continuity import next_capture_at, status, anchor
from scripts.capture_price_h1 import runner_lock, running


def args_at(offset, **changes):
    a = fixture_args()
    t = T + timedelta(hours=offset)
    a['event_time'] = t
    a['source_metric_at'] = t-timedelta(milliseconds=1)
    a['received_at'] = t+timedelta(seconds=2)
    a['clock'] = lambda: t+timedelta(seconds=3)
    start = int((t-timedelta(hours=1)).timestamp()*1000)
    a['payload'].update(time=(t-timedelta(hours=1)).isoformat(), open_time_ms=start, close_time_ms=start+3599999)
    row = json.loads(a['provenance']['raw_klines'])[0]
    row[0], row[6] = start, start+3599999
    a['provenance'].update(raw_klines=json.dumps([row]), raw_server_time=json.dumps({'serverTime':int(t.timestamp()*1000)}),
        server_received_at=(t+timedelta(seconds=1)).isoformat(), klines_requested_at=(t+timedelta(seconds=1)).isoformat())
    a.update(changes)
    return a


def series(tmp_path, offsets):
    db = tmp_path/'r.db'
    for i in offsets:
        append_observation(db, **args_at(i))
    return db


def report(db, tmp_path, offset):
    return status(db, tmp_path/'state', T+timedelta(hours=offset, seconds=10))


@pytest.mark.parametrize('seconds,expected', [(0,5), (4,5), (5,3605), (3599,3605)])
def test_scheduler(seconds, expected):
    assert next_capture_at(T+timedelta(seconds=seconds)) == T+timedelta(seconds=expected)


def test_idempotence_restart_and_conflict(tmp_path):
    db = series(tmp_path, [0])
    first = load_observations(db)
    append_observation(db, **args_at(0))
    assert load_observations(db) == first
    a = args_at(0); a['payload']['close'] += .1
    with pytest.raises(ValueError, match='conflicting'):
        append_observation(db, **a)
    assert report(db, tmp_path, 0)['bars_to_81'] == 80


@pytest.mark.parametrize('count,ready', [(80,False), (81,True), (82,True)])
def test_certificate(tmp_path, count, ready):
    db = series(tmp_path, range(count))
    s = report(db, tmp_path, count-1)
    assert s['regime_input_ready'] == ready
    assert bool(s['certificate']) == ready
    assert report(db, tmp_path, count-1) == s
    if ready:
        assert len(s['certificate']['receipt_ids']) == 81
        assert s['certificate']['historical_backfill'] is False


def test_gap_40_plus_41(tmp_path):
    db = series(tmp_path, list(range(40))+list(range(41,82)))
    s = report(db, tmp_path, 81)
    assert s['current_streak'] == s['longest_streak'] == 41
    assert s['bars_to_81'] == 40 and s['certificate'] is None
    assert s['gaps'][0]['hours'] == 1


def test_invalid_in_81(tmp_path):
    db = series(tmp_path, range(80))
    a = args_at(80); a['provenance']['bar_closed'] = False
    append_observation(db, **a)
    s = report(db, tmp_path, 80)
    assert s['certificate'] is None and len(s['invalid']) == 1


@pytest.mark.parametrize('kind', ['unknown', 'instrument', 'historical', 'out_of_order', 'duplicate'])
def test_bad_receipts(tmp_path, kind):
    db = series(tmp_path, [0])
    a = args_at(1)
    if kind == 'unknown': a['feature'] = 'OpenInterest'
    if kind == 'instrument': a['instrument'] = 'ETHUSDT'
    if kind == 'historical':
        a = args_at(-1)
        a['received_at'] = T+timedelta(hours=1, seconds=2)
        a['clock'] = lambda: T+timedelta(hours=1, seconds=3)
        a['provenance']['klines_requested_at'] = (T+timedelta(hours=1, seconds=1)).isoformat()
    if kind == 'out_of_order':
        a = args_at(-1)
        a['received_at'] = T+timedelta(seconds=4)
        a['clock'] = lambda: T+timedelta(seconds=5)
    if kind == 'duplicate':
        # Alternative source metric identity is invalid and cannot add a bar.
        a = args_at(0); a['source_metric_at'] = T-timedelta(milliseconds=2)
    append_observation(db, **a)
    s = report(db, tmp_path, 1)
    assert s['certificate'] is None
    assert s['valid_price_receipts'] <= 1
    if kind == 'out_of_order': assert s['out_of_order']
    else: assert s['invalid']


def test_anchors_and_rollback(tmp_path):
    db = series(tmp_path, [0,1])
    a = anchor(db, tmp_path/'state', T+timedelta(hours=1, seconds=10))
    assert report(db, tmp_path, 1)['last_external_anchor'] == a
    with sqlite3.connect(db) as c:
        c.execute('DROP TRIGGER observations_v2_no_delete')
        c.execute('DELETE FROM observations_v2 WHERE seq=2')
    assert report(db, tmp_path, 1)['ledger_integrity'] == 'FAIL'


def test_corrupted_chain(tmp_path):
    db = series(tmp_path, [0])
    with sqlite3.connect(db) as c:
        c.execute('DROP TRIGGER observations_v2_no_update')
        c.execute("UPDATE observations_v2 SET receipt_hash='broken'")
    assert report(db, tmp_path, 0)['ledger_integrity'] == 'FAIL'


def test_trailing_missing_hour(tmp_path):
    db = series(tmp_path, [0])
    s = report(db, tmp_path, 2)
    assert s['current_streak'] == 0 and s['gaps'][0]['hours'] == 2


def test_singleton_restart(tmp_path):
    assert not running(tmp_path)
    with runner_lock(tmp_path):
        assert running(tmp_path)
        with pytest.raises(OSError):
            with runner_lock(tmp_path): pass
    assert not running(tmp_path)


def test_conflict_blocks_certificate(tmp_path):
    db = series(tmp_path, range(81))
    p = tmp_path/'state'/'attempts'; p.mkdir(parents=True)
    (p/'conflict.json').write_text(json.dumps({'status':'CONFLICT'}))
    assert report(db, tmp_path, 80)['certificate'] is None


def test_attempt_timeout_logged_without_receipt(tmp_path, monkeypatch):
    from scripts import capture_price_h1 as runner
    def timeout(*args, **kwargs):
        raise TimeoutError('network timeout')
    monkeypatch.setattr(runner, 'capture_price_receipt', timeout)
    result = runner.attempt(None, tmp_path/'r.db', tmp_path/'state', T)
    assert result['status'] == 'FAILED'
    assert not (tmp_path/'r.db').exists()
    assert len(list((tmp_path/'state'/'attempts').glob('*.json'))) == 2


def test_attempt_conflict_persisted(tmp_path, monkeypatch):
    from scripts import capture_price_h1 as runner
    def conflict(*args, **kwargs):
        raise ValueError('conflicting observation; no silent overwrite')
    monkeypatch.setattr(runner, 'capture_price_receipt', conflict)
    assert runner.attempt(None, tmp_path/'r.db', tmp_path/'state', T)['status'] == 'CONFLICT'


def test_clock_regression_refuses_restart(tmp_path, monkeypatch):
    from scripts import capture_price_h1 as runner
    db = series(tmp_path, [0])
    monkeypatch.setattr(runner, 'now', lambda:T)
    with pytest.raises(ValueError, match='clock regression'):
        runner.run(db, tmp_path/'state')


def test_anchor_prefix_survives_extension(tmp_path):
    db = series(tmp_path, [0])
    a = anchor(db, tmp_path/'state', T+timedelta(seconds=10))
    append_observation(db, **args_at(1))
    s = report(db, tmp_path, 1)
    assert s['ledger_integrity'] == 'PASS' and s['last_external_anchor'] == a
    b = anchor(db, tmp_path/'state', T+timedelta(hours=1, seconds=10))
    assert b['observation_count'] == 2


def test_scheduled_slot_mismatch_never_persists(tmp_path):
    from types import SimpleNamespace
    from core.market_mechanics.binance_live_adapter import capture_price_receipt
    a = args_at(0)
    class Session:
        def get(self, url, **kwargs):
            raw = a['provenance']['raw_server_time' if url.endswith('/time') else 'raw_klines']
            return SimpleNamespace(status_code=200, text=raw, raise_for_status=lambda:None)
    with pytest.raises(ValueError, match='scheduled slot mismatch'):
        capture_price_receipt(Session(), tmp_path/'r.db', clock=lambda:T+timedelta(seconds=5), expected_event_time=T-timedelta(hours=1))
    assert not (tmp_path/'r.db').exists()
