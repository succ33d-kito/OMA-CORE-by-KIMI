from datetime import datetime, timedelta, timezone
import json

import pytest
from core.scientific import metrics_h1_activation as activation
from core.scientific import metrics_h1_runtime as runtime

S=datetime(2026,10,11,13,tzinfo=timezone.utc)


@pytest.fixture
def state(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); root=tmp_path/'metrics-h1-v1'
    activation.activate(root,repo_root=repo,now=S-timedelta(minutes=20),dataset_role='PILOT')
    return root,repo


def forbidden(*args,**kwargs): raise AssertionError('must not invoke transport')


def run(state,**kwargs):
    args=dict(repo_root=state[1],transport=forbidden,clock=lambda:S,sleeper=lambda n:None,max_iterations=2)
    args.update(kwargs)
    return runtime.run_forever(state[0],**args)


def test_runtime_metadata_only_before_target(state):
    assert run(state)['iterations']==2
    assert not (state[0]/'attempts').exists()
    hb=json.loads((state[0]/'runtime'/'heartbeat.json').read_bytes())
    assert hb['status']=='STOPPED' and hb['heartbeat_is_evidence'] is False
    assert hb['last_adapter_status']=='NOT_DUE'


def test_missing_config_no_autoactivation(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); root=tmp_path/'metrics-h1-v1'
    with pytest.raises(FileNotFoundError): run((root,repo))
    assert not root.exists()


@pytest.mark.parametrize('interval',[0,-1,5.1,True,float('nan'),float('inf')])
def test_bad_poll_no_runtime_directory(state,interval):
    with pytest.raises(ValueError): run(state,poll_seconds=interval)
    assert not (state[0]/'runtime').exists()


def test_lock_excludes_competitor_and_releases(state):
    folder=state[0]/'runtime'; folder.mkdir()
    with runtime.process_lock(folder/'runner.lock'):
        with pytest.raises(RuntimeError,match='locked'): run(state)
    assert run(state)['status']=='STOPPED'


def test_restart_regression_rejected_without_heartbeat_rewrite(state):
    run(state); path=state[0]/'runtime'/'heartbeat.json'; before=path.read_bytes()
    with pytest.raises(ValueError,match='backwards'): run(state,clock=lambda:S-timedelta(seconds=1))
    assert path.read_bytes()==before


def test_midrun_regression_fails_closed(state):
    values=iter([S,S-timedelta(seconds=1)])
    with pytest.raises(ValueError,match='backwards'): run(state,clock=lambda:next(values))


def test_pre_requested_stop_no_capture(state):
    assert run(state,stop_requested=lambda:True)['iterations']==0
    assert not (state[0]/'attempts').exists()


def test_failed_slot_does_not_stop_future_slot(state):
    current=S+timedelta(seconds=180); calls=[]
    def transport(url,**kwargs): calls.append(url); raise TimeoutError('fixture only')
    def sleep(seconds):
        nonlocal current
        assert seconds<=5
        current+=timedelta(hours=1)  # Simulated suspension, no historical catch-up.
    assert run(state,clock=lambda:current,sleeper=sleep,transport=transport)['iterations']==2
    assert len(calls)==2
    for name in ('20261011T130000Z','20261011T140000Z'):
        assert json.loads((state[0]/'attempts'/name/'result.json').read_bytes())['status']=='FAILED'


def test_restart_does_not_retry_completed_slot(state):
    calls=[]
    def transport(url,**kwargs): calls.append(url); raise TimeoutError()
    run(state,clock=lambda:S+timedelta(seconds=180),transport=transport)
    run(state,clock=lambda:S+timedelta(seconds=180),transport=transport)
    assert len(calls)==1


def test_malformed_heartbeat_and_pending_fail_closed(state):
    run(state); path=state[0]/'runtime'/'heartbeat.json'
    path.write_bytes(b'{}')
    with pytest.raises(ValueError,match='heartbeat'): run(state)
    path.unlink(); (path.parent/'.heartbeat.pending').write_bytes(b'partial')
    with pytest.raises(ValueError,match='interrupted'): run(state)
