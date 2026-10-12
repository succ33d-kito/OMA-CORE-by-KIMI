"""Operational retry tests: synthetic transport, frozen causal gates, no live HTTP."""
from datetime import timedelta
from pathlib import Path
import json
import subprocess
import pytest
from tests.test_price_role_h1_runner import env, REPO, S
from core.scientific import price_role_h1_runner as runner
from core.scientific import price_role_attestation as roles
from core.scientific.capture_clock import ClockHealthError
from core.scientific.prospective_receipts import append_observation


def records(env):
    return runner._network_records(env.root, env.config, S)


def test_strict_clock_first_failure_second_frozen_capture_success(env, monkeypatch):
    original_get = env.session.get
    original_auth = roles.authorize_capture
    auth_calls, captures = [], []
    def authorize(*a, **k):
        auth_calls.append(True)
        return original_auth(*a, **k)
    monkeypatch.setattr(roles, 'authorize_capture', authorize)
    def get(*a, **k):
        if not captures[-1] > 1:
            env.t += timedelta(seconds=2.5)  # frozen monotonic RTT exceeds 2s
        return original_get(*a, **k)
    env.session.get = get
    def capture(*a, **k):
        captures.append(len(captures)+1)
        return env.capture(*a, **k)
    result = env.run(capture=capture)
    assert result['status'] == 'SUCCESS'
    assert len(auth_calls) == 1 and captures == [1, 2]
    assert len(runner._rows(env.root)) == 2
    assert len(list((env.root/'authorizations').glob('*.json'))) == 1
    rs = records(env)
    assert {(r['attempt_index'], r['status']) for r in rs} == {(1,'STARTED'),(1,'FAILED'),(2,'STARTED'),(2,'SUCCESS')}
    failure = next(r for r in rs if r['status']=='FAILED')
    assert failure['exception_type'] == 'ClockHealthError'
    assert failure['exception_message'] == 'clock health: uncertain RTT or wall-clock discontinuity'
    assert failure['failure_kind'] == 'CLOCK' and failure['raw_present_after_failure'] is False
    assert failure['remaining_window_seconds'] == 116.5
    second = next(r for r in rs if r['attempt_index']==2 and r['status']=='STARTED')
    assert runner.utc(second['started_at'])-runner.utc(failure['completed_at']) == timedelta(seconds=20)
    known = runner._rows(env.root)
    assert known[result['attestation_id']]['dependencies'] == [result['raw_id']]
    assert roles.price_role_authenticated(known,known[result['raw_id']],'PILOT',env.t)


def test_persisted_raw_then_exception_never_retries(env):
    calls = []
    def capture(*a, **k):
        calls.append(True)
        env.capture(*a, **k)
        raise OSError('return interrupted after commit')
    assert env.run(capture=capture)['status'] == 'SUCCESS'
    assert calls == [True]
    failed = next(r for r in records(env) if r['status']=='FAILED')
    assert failed['raw_present_after_failure'] is True
    assert failed['exception_message'] == 'return interrupted after commit'
    assert len(runner._rows(env.root)) == 2


def test_conflicting_raw_after_exception_prevents_retry(env):
    calls = []
    def capture(*a, **k):
        calls.append(True)
        price = env.capture(*a, **k)
        append_observation(env.root/'observations.db',source='conflict',instrument='BTCUSDT',feature='Price/OHLCV',
            event_time=S,source_metric_at=S,received_at=env.t,payload=price['payload'],provenance=price['provenance'],clock=env.clock)
        raise OSError('ambiguous conflicting return')
    assert env.run(capture=capture)['status'] == 'CONFLICT'
    assert calls == [True] and len(runner._rows(env.root)) == 2
    assert next(r for r in records(env) if r['status']=='FAILED')['raw_present_after_failure'] is True


@pytest.mark.parametrize('overshoot',[0,3600])
def test_deadline_sleep_clamped_and_no_late_retry(env,overshoot):
    env.t = S+timedelta(seconds=120)
    calls, waits = [], []
    def fail(*a, **k):
        calls.append(True)
        raise ClockHealthError('transient')
    def sleep(seconds):
        waits.append(seconds)
        env.t += timedelta(seconds=seconds+overshoot)
    result=env.run(capture=fail,sleeper=sleep)
    assert result['status']=='CAPTURE_FAILED' and result['reason']=='RETRY_WINDOW_EXHAUSTED'
    assert calls==[True] and waits==[5]
    assert env.run()==result


def test_failure_completes_after_deadline_no_wait(env):
    def fail(*a, **k):
        env.t = S+timedelta(seconds=126)
        raise ClockHealthError('late preflight')
    assert env.run(capture=fail,sleeper=lambda n:pytest.fail('no waiting after deadline'))['status']=='CAPTURE_FAILED'
    failed=next(r for r in records(env) if r['status']=='FAILED')
    assert failed['remaining_window_seconds']==0


def test_retry_crash_never_resumes_after_restart(env):
    calls=[]
    def capture(*a, **k):
        calls.append(True)
        if len(calls)==1: raise ClockHealthError('first transient')
        raise SystemExit('crash during second network call')
    with pytest.raises(SystemExit): env.run(capture=capture)
    before={p:p.read_bytes() for p in (env.root/'attempts').rglob('*.json')}
    result=env.run(capture=lambda *a,**k:pytest.fail('restart must not retry'))
    assert result['reason']=='INTERRUPTED_CAPTURE_NO_RETRY'
    assert all(p.read_bytes()==b for p,b in before.items())
    assert len([r for r in records(env) if r['status']=='STARTED'])==2


def test_v1_1800_terminal_history_is_byte_immutable(env):
    slot=S+timedelta(hours=6)
    env.t=slot+timedelta(seconds=5)
    auth=roles.authorize_capture(env.root,repo_root=REPO,expected_event_time=slot)
    for status in ('STARTED','AUTHORIZED','CAPTURE_STARTED'):
        details={} if status=='STARTED' else {'authorization_id':auth['authorization_id']}
        runner._record(env.root,env.config,slot,status,env.t,**details)
    env.t+=timedelta(seconds=4)
    failure=runner._record(env.root,env.config,slot,'CAPTURE_FAILED',env.t,reason='CAPTURE_EXCEPTION_NO_RETRY')
    before={p:p.read_bytes() for p in env.root.rglob('*.json')}
    env.t+=timedelta(hours=1)
    assert env.run(slot,capture=lambda *a,**k:pytest.fail('historical slot must remain failed'))==failure
    assert all(p.read_bytes()==b for p,b in before.items())
    assert not (runner._directory(env.root,slot)/'network').exists()
    report=runner.status(env.root,repo_root=REPO,clock=env.clock)
    assert report['runtime_network_attempts']==1 and report['legacy_uninstrumented_network_attempts']==1
    assert report['last_network_attempt_status']=='CAPTURE_FAILED' and report['attested_hours']==0


def test_status_read_only_and_explicit_runtime_activity(env):
    env.run()
    before={p:p.read_bytes() for p in env.root.rglob('*') if p.is_file()}
    report=runner.status(env.root,repo_root=REPO,clock=env.clock)
    assert report['status_command_network_executed'] is False
    assert report['runtime_network_attempts']==1 and report['last_network_attempt_status']=='SUCCESS'
    assert report['legacy_uninstrumented_network_attempts']==0
    assert {p:p.read_bytes() for p in before}==before


def test_numbered_record_is_create_only_and_corruption_fails_closed(env):
    env.run()
    with pytest.raises(FileExistsError):
        runner._network_record(env.root,env.config,S,1,'STARTED',env.t,env.t)
    path=runner._directory(env.root,S)/'network'/'0001-STARTED.json'
    path.write_text('{}')
    with pytest.raises(ValueError,match='corrupt'): runner.status(env.root,repo_root=REPO,clock=env.clock)


def test_wait_clock_regression_never_retries(env):
    def fail(*a, **k): raise ClockHealthError('transient')
    def sleep(n): env.t-=timedelta(seconds=1)
    with pytest.raises(ValueError,match='clock'): env.run(capture=fail,sleeper=sleep)
    assert len([r for r in records(env) if r['status']=='STARTED'])==1


def test_all_six_frozen_surfaces_identical():
    names=['core/market_mechanics/binance_live_adapter.py','core/scientific/prospective_receipts.py',
        'core/scientific/price_continuity.py','core/scientific/capture_clock.py',
        'scripts/capture_price_h1.py','scripts/install_price_capture_task.ps1']
    for name in names:
        old=subprocess.check_output(['git','show','82c3796389df9b9bbe1b32fc89d32e18b63196c7:'+name],cwd=REPO)
        assert (REPO/name).read_bytes().replace(b'\r\n',b'\n')==old.replace(b'\r\n',b'\n')
