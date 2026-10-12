from datetime import timedelta
import json
import pytest
from tests.test_price_role_h1_runner import env, REPO, S
from core.scientific import price_role_h1_runner as runner
from core.scientific import price_role_h1_runtime as runtime
from core.scientific.funding_h1_runtime import _process_lock


def test_runtime_network_failure_preserves_next_future_slot(env):
    seen = []
    def run_slot(root,slot,**kwargs):
        seen.append(slot)
        return {'status':'CAPTURE_FAILED' if len(seen)==1 else 'SUCCESS','slot':slot.isoformat()}
    def sleep(seconds):
        assert seconds == 5
        env.t += timedelta(hours=1)
    result = runtime.run_forever(env.root,repo_root=REPO,clock=env.clock,sleeper=sleep,
        max_iterations=2,run_slot=run_slot)
    assert seen == [S,S+timedelta(hours=1)]
    assert result['last_result']['status'] == 'SUCCESS'
    heartbeat = json.loads((env.root/'runtime'/'heartbeat.json').read_text())
    assert heartbeat['heartbeat_is_evidence'] is False
    assert heartbeat['status'] == 'STOPPED' and heartbeat['pid'] > 0
    assert heartbeat['last_slot'] == (S+timedelta(hours=1)).isoformat()


def test_second_runtime_lock_fails_closed(env):
    path = env.root/'runtime'
    path.mkdir()
    with _process_lock(path/'runner.lock'):
        with pytest.raises(RuntimeError,match='locked'):
            runtime.run_forever(env.root,repo_root=REPO,clock=env.clock,max_iterations=1)
    assert not (path/'heartbeat.json').exists()


def test_direct_slot_lock_fails_closed(env):
    path = env.root/'runtime'
    path.mkdir()
    with _process_lock(path/'slot.lock'):
        with pytest.raises(RuntimeError,match='locked'):
            env.run()
    assert env.calls == 0


def test_restart_recovers_raw_without_network(env):
    def crash(*args,**kwargs):
        env.capture(*args,**kwargs)
        raise SystemExit('crash')
    with pytest.raises(SystemExit):
        env.run(capture=crash)
    env.t = S+timedelta(minutes=10)
    runtime.run_forever(env.root,repo_root=REPO,clock=env.clock,max_iterations=1)
    assert env.calls == 2
    assert runner.status(env.root,repo_root=REPO,clock=env.clock)['attested_hours'] == 1
    before = (env.root/'observations.db').read_bytes()
    runtime.run_forever(env.root,repo_root=REPO,clock=env.clock,max_iterations=1)
    assert (env.root/'observations.db').read_bytes() == before and env.calls == 2


def test_clock_regression_within_runtime_fails(env):
    def sleep(seconds):
        env.t -= timedelta(seconds=1)
    with pytest.raises(ValueError,match='clock'):
        runtime.run_forever(env.root,repo_root=REPO,clock=env.clock,sleeper=sleep,max_iterations=2,
            run_slot=lambda root,slot,**k:{'status':'CAPTURE_FAILED','slot':slot.isoformat()})


def test_clock_regression_across_restart_fails(env):
    env.t = S+timedelta(minutes=10)
    runtime.run_forever(env.root,repo_root=REPO,clock=env.clock,max_iterations=1)
    env.t -= timedelta(seconds=1)
    with pytest.raises(ValueError,match='clock'):
        runtime.run_forever(env.root,repo_root=REPO,clock=env.clock,max_iterations=1)


def test_sleep_resume_does_not_catch_up(env):
    env.t = S+timedelta(seconds=4)
    def sleep(seconds):
        env.t += timedelta(hours=3,seconds=10)
    result = runtime.run_forever(env.root,repo_root=REPO,clock=env.clock,sleeper=sleep,max_iterations=2)
    assert result['last_result']['status'] == 'MISSED_SLOT'
    assert env.calls == 0 and not (env.root/'authorizations').exists()


def test_runtime_without_activation_does_not_initialize(tmp_path):
    root = tmp_path/runner.LEAF
    with pytest.raises(FileNotFoundError):
        runtime.run_forever(root,repo_root=REPO,max_iterations=1)
    assert not root.exists()



def test_runtime_two_real_contract_cycles_with_synthetic_transport(env):
    def run_slot(root,slot,**kwargs):
        return runner.attempt_slot(root,slot,capture=env.capture,**kwargs)
    def sleep(seconds):
        env.t += timedelta(hours=1)
    runtime.run_forever(env.root,repo_root=REPO,session=env.session,clock=env.clock,
        sleeper=sleep,max_iterations=2,run_slot=run_slot)
    report = runner.status(env.root,repo_root=REPO,clock=env.clock)
    assert env.calls == 4 and report['attested_hours'] == 2
    assert len([r for r in report['attempt_records'] if r['status']=='SUCCESS']) == 2
