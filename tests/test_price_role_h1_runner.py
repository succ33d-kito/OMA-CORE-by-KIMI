"""Synthetic transport exercises the unchanged frozen Price capture, never Internet."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import json
import pytest
from core.scientific import price_role_activation as activation
from core.scientific import price_role_attestation as roles
from core.scientific import price_role_h1_runner as runner
from core.market_mechanics.binance_live_adapter import capture_price_receipt
from core.scientific.prospective_receipts import observation_hash, append_observation

REPO = Path(__file__).resolve().parents[1]
S = datetime(2026,10,12,12,tzinfo=timezone.utc)


@pytest.fixture
def env(tmp_path,monkeypatch):
    e = SimpleNamespace(root=tmp_path/runner.LEAF,t=S-timedelta(minutes=1),calls=0)
    e.clock = lambda:e.t
    monkeypatch.setattr(activation,"_now",e.clock)
    monkeypatch.setattr(roles,"_now",e.clock)
    e.config = activation.activate(state_root=e.root,repo_root=REPO,dataset_role="PILOT")
    e.t = S+timedelta(seconds=5)
    class Session:
        def get(self,url,params=None,timeout=None):
            e.calls += 1
            e.t += timedelta(seconds=1)
            if url.endswith('/time'):
                body = {"serverTime":int(e.t.timestamp()*1000)}
            else:
                slot = e.t.replace(minute=0,second=0,microsecond=0)
                opened = int((slot-timedelta(hours=1)).timestamp()*1000)
                body = [[opened,"100","101","99","100","5",opened+3599999,"500",2,"2","200","0"]]
            return SimpleNamespace(status_code=200,text=json.dumps(body),raise_for_status=lambda:None)
    e.session = Session()
    def capture(session,ledger,**kwargs):
        return capture_price_receipt(e.session,ledger,monotonic=lambda:e.t.timestamp(),**kwargs)
    e.capture = capture
    e.run = lambda slot=S,**kwargs:runner.attempt_slot(e.root,slot,repo_root=REPO,
        clock=e.clock,capture=kwargs.pop('capture',e.capture),**kwargs)
    return e


def test_frozen_capture_success_exact_chain_and_idempotence(env):
    checked = []
    def capture(session,ledger,**kwargs):
        auth = list((env.root/'authorizations').glob('*.json'))
        assert len(auth) == 1
        assert kwargs['expected_event_time'] == S
        assert kwargs['capture_deadline'] == S+timedelta(seconds=125)
        checked.append(True)
        return env.capture(session,ledger,**kwargs)
    result = env.run(capture=capture)
    assert result['status'] == 'SUCCESS' and checked == [True] and env.calls == 2
    known = runner._rows(env.root)
    price, att = known[result['raw_id']],known[result['attestation_id']]
    assert not price['derived'] and att['dependencies'] == [price['id']]
    assert roles.price_role_authenticated(known,price,'PILOT',env.t)
    assert roles.verified_price_role_attestation(known,price,'PILOT',env.t) == att
    before = {p:p.read_bytes() for p in (env.root/'attempts').rglob('*.json')}
    assert env.run() == result and env.calls == 2
    assert before == {p:p.read_bytes() for p in before}
    assert runner.status(env.root,repo_root=REPO,clock=env.clock)['attested_hours'] == 1


def test_activation_required_without_state_creation(tmp_path):
    root = tmp_path/runner.LEAF
    with pytest.raises(FileNotFoundError):
        runner.attempt_slot(root,S,repo_root=REPO)
    assert not root.exists()


@pytest.mark.parametrize('role',['DISCOVERY','CONFIRMATION'])
def test_wrong_authenticated_role_rejected(tmp_path,monkeypatch,role):
    root = tmp_path/runner.LEAF
    monkeypatch.setattr(activation,'_now',lambda:S)
    activation.activate(state_root=root,repo_root=REPO,dataset_role=role)
    with pytest.raises(ValueError,match='PILOT'):
        runner.attempt_slot(root,S,repo_root=REPO)
    assert not (root/'authorizations').exists()


@pytest.mark.parametrize('offset',[-3600,126,3600])
def test_late_or_historical_slot_never_captured(env,offset):
    slot = S-timedelta(hours=1) if offset == -3600 else S
    if offset != -3600:
        env.t = S+timedelta(seconds=offset)
    assert env.run(slot)['status'] == 'MISSED_SLOT'
    assert env.calls == 0 and not (env.root/'authorizations').exists()
    assert env.run(slot)['status'] == 'MISSED_SLOT'


def test_early_slot_waits_without_authorization(env):
    env.t = S+timedelta(seconds=4)
    assert env.run()['status'] == 'WAITING'
    assert env.calls == 0 and not (env.root/'authorizations').exists()


def test_crash_after_authorization_recovers(env):
    auth = roles.authorize_capture(env.root,repo_root=REPO,expected_event_time=S)
    result = env.run()
    assert result['status'] == 'SUCCESS'
    assert runner._rows(env.root)[result['attestation_id']]['payload']['authorization_id'] == auth['authorization_id']


def test_crash_after_raw_recovers_without_capture(env):
    def crash(*args,**kwargs):
        env.capture(*args,**kwargs)
        raise SystemExit('simulated process crash')
    with pytest.raises(SystemExit):
        env.run(capture=crash)
    assert env.calls == 2
    env.t += timedelta(hours=1)
    def forbidden(*args,**kwargs):
        pytest.fail('raw recovery must never recapture')
    result = env.run(capture=forbidden)
    assert result['status'] == 'SUCCESS' and env.calls == 2


def test_attestation_failure_preserves_raw_and_authorization(env,monkeypatch):
    original = roles.attest_price_observation
    monkeypatch.setattr(roles,'attest_price_observation',lambda *a,**k: (_ for _ in ()).throw(OSError('disk failure')))
    assert env.run()['status'] == 'ATTESTATION_FAILED'
    assert len(runner._rows(env.root)) == 1
    monkeypatch.setattr(roles,'attest_price_observation',original)
    assert env.run()['status'] == 'SUCCESS' and env.calls == 2
    assert (runner._directory(env.root,S)/'ATTESTATION_FAILED.json').is_file()


def test_raw_without_authorization_never_rescued(env):
    env.capture(None,env.root/'observations.db',clock=env.clock,expected_event_time=S,capture_deadline=S+timedelta(seconds=125))
    result = env.run()
    assert result['status'] == 'CONFLICT' and env.calls == 2
    assert not (env.root/'authorizations').exists()
    assert env.run() == result


def test_late_authorization_cannot_rescue_raw(env):
    env.capture(None,env.root/'observations.db',clock=env.clock,expected_event_time=S,capture_deadline=S+timedelta(seconds=125))
    roles.authorize_capture(env.root,repo_root=REPO,expected_event_time=S)
    assert env.run()['status'] == 'CONFLICT'
    assert len(runner._rows(env.root)) == 1 and env.calls == 2


def test_capture_failure_is_terminal_no_hidden_retry(env):
    def failed(*args,**kwargs):
        raise OSError('network failure')
    first = env.run(capture=failed)
    assert first['status'] == 'CAPTURE_FAILED'
    assert env.run() == first and env.calls == 0


def test_ambiguous_crash_before_raw_never_retries(env):
    def crash(*args,**kwargs):
        raise SystemExit('request outcome unknown')
    with pytest.raises(SystemExit):
        env.run(capture=crash)
    assert env.run()['status'] == 'CAPTURE_FAILED' and env.calls == 0


def test_tampered_authorization_fails_closed(env):
    auth = roles.authorize_capture(env.root,repo_root=REPO,expected_event_time=S)
    path = env.root/'authorizations'/(auth['slot_id']+'.json')
    body = json.loads(path.read_text()); body['dataset_role'] = 'DISCOVERY'
    path.write_bytes(roles._canonical(body))
    assert env.run()['status'] == 'CONFLICT' and env.calls == 0


def test_conflicting_raw_fails_closed(env):
    roles.authorize_capture(env.root,repo_root=REPO,expected_event_time=S)
    price = env.capture(None,env.root/'observations.db',clock=env.clock,expected_event_time=S,capture_deadline=S+timedelta(seconds=125))
    append_observation(env.root/'observations.db',source='conflicting-source',instrument='BTCUSDT',feature='Price/OHLCV',
        event_time=S,source_metric_at=S,received_at=env.t,payload=price['payload'],provenance=price['provenance'],clock=env.clock)
    assert env.run()['status'] == 'CONFLICT' and env.calls == 2


def test_tampered_attestation_cannot_repair(env,monkeypatch):
    result = env.run()
    known = deepcopy(runner._rows(env.root))
    known[result['attestation_id']]['payload']['dataset_role'] = 'CONFIRMATION'
    monkeypatch.setattr(runner,'_rows',lambda root:known)
    assert env.run()['status'] == 'CONFLICT' and env.calls == 2


def test_clock_regression_and_naive_clock_rejected(env):
    env.run()
    env.t -= timedelta(seconds=1)
    with pytest.raises(ValueError,match='clock'):
        env.run()
    env.t = env.t.replace(tzinfo=None)
    with pytest.raises(ValueError,match='timezone'):
        env.run()


def test_no_success_from_callback_without_persistence(env):
    assert env.run(capture=lambda *a,**k:{'id':'fabricated'})['status'] == 'CONFLICT'


def test_closed_deadline_rejects_network_completion(env):
    env.t = S+timedelta(seconds=125)
    assert env.run()['status'] == 'CAPTURE_FAILED'
    assert not runner._rows(env.root)


def test_state_alias_and_wrong_leaf_rejected(env,tmp_path):
    with pytest.raises(ValueError):
        runner.validate_state(tmp_path,repo_root=REPO)
    from unittest.mock import patch
    with patch.object(runner,'_reject_aliases',side_effect=ValueError('reparse')):
        with pytest.raises(ValueError,match='reparse'):
            runner.validate_state(env.root,repo_root=REPO)



def test_activation_in_another_checkout_cannot_write_runtime(tmp_path,monkeypatch):
    other = tmp_path/'other-repo'
    other.mkdir()
    (other/'.git').write_text('gitdir: other')
    root = other/runner.LEAF
    monkeypatch.setattr(activation,'_now',lambda:S)
    activation.activate(state_root=root,repo_root=REPO,dataset_role='PILOT')
    with pytest.raises(ValueError,match='outside repository'):
        runner.attempt_slot(root,S,repo_root=REPO)
    assert not (root/'runtime').exists()


def test_attestation_commit_then_crash_is_not_recapture(env,monkeypatch):
    original = roles.attest_price_observation
    def crash(*a,**k):
        original(*a,**k)
        raise SystemExit('crash after attestation persistence')
    monkeypatch.setattr(roles,'attest_price_observation',crash)
    with pytest.raises(SystemExit):
        env.run()
    assert len(runner._rows(env.root)) == 2
    assert env.run()['status'] == 'SUCCESS' and env.calls == 2


def test_record_corruption_is_not_repaired(env):
    result = env.run()
    path = runner._directory(env.root,S)/'SUCCESS.json'
    path.write_text('{}')
    with pytest.raises(ValueError,match='corrupt'):
        env.run()
    assert path.read_text() == '{}' and env.calls == 2



def test_other_slot_valid_authorization_cannot_authorize_current_capture(env):
    auth = roles.authorize_capture(env.root,repo_root=REPO,expected_event_time=S+timedelta(hours=1))
    wrong_path = env.root/'authorizations'/(roles._slot_id(env.config['activation_id'],S)+'.json')
    wrong_path.write_bytes(roles._canonical(auth))
    assert env.run()['status'] == 'CONFLICT' and env.calls == 0
