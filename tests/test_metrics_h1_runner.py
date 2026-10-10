"""Synthetic execution envelopes only; never real market evidence."""
import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import socket

import pytest
from core.scientific import metrics_h1_activation as activation
from core.scientific import metrics_h1_runner as runner

S = datetime(2026,10,11,13,tzinfo=timezone.utc)


@pytest.fixture
def state(tmp_path):
    repo = tmp_path/'repo'; repo.mkdir()
    root = tmp_path/'metrics-h1-v1'
    activation.activate(root, repo_root=repo, now=S-timedelta(minutes=20), dataset_role='PILOT')
    return root, repo


def clock(*values):
    values = iter(values)
    return lambda: next(values)


def success(**kw):
    assert json.loads((kw['capture_directory'].parent/'attempt.json').read_bytes())['expected_source_period_end'] == kw['slot'].isoformat()
    assert kw['expected_source_period_end'] == kw['slot']
    assert kw['target_at'] == kw['slot']+timedelta(seconds=180)
    assert kw['deadline_at'] == kw['slot']+timedelta(seconds=300)
    return dict(status='SUCCESS',slot=kw['slot'],source_period_end=kw['slot'],
                capture_receipt_id='synthetic-test-only',raw_bundle_sha256='a'*64,
                available_at=kw['attempt_started_at'])


def attempt(state, capture=success, slot=S, seconds=180, timer=None):
    return runner.attempt_slot(state[0],slot,capture,repo_root=state[1],clock=timer or (lambda:slot+timedelta(seconds=seconds)))


def files(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_config_load_and_no_initialization(state,tmp_path):
    before=files(state[0])
    assert runner.load_config(state[0],repo_root=state[1])['activation_slot'] == S.isoformat()
    assert files(state[0]) == before
    missing=tmp_path/'missing'/'metrics-h1-v1'
    with pytest.raises((ValueError,FileNotFoundError)): runner.load_config(missing,repo_root=state[1])
    assert not missing.exists()


@pytest.mark.parametrize('field,value', [('target_offset_seconds',0),('deadline_offset_seconds',301),('same_slot_retry','ONE')])
def test_mutated_capture_config_rejected(state,field,value):
    p=state[0]/'config.json'; c=json.loads(p.read_bytes()); c['capture'][field]=value
    p.write_bytes(activation._canonical(c))
    with pytest.raises(ValueError): attempt(state)
    assert not (state[0]/'attempts').exists()


@pytest.mark.parametrize('case',['malformed','source','role','root','identity','extra'])
def test_other_config_corruption(state,case):
    p=state[0]/'config.json'; c=json.loads(p.read_bytes())
    if case=='source': c['source_bundle']['expected_period_end']='LATEST'
    if case=='role': c['dataset_role']='CONFIRMATION'
    if case=='root': c['state_root']='elsewhere'
    if case=='identity': c['activation_id']='b'*64
    if case=='extra': c['extra']=True
    p.write_bytes(b'{' if case=='malformed' else activation._canonical(c))
    with pytest.raises(ValueError): attempt(state)


@pytest.mark.parametrize('seconds,status', [(-60,'NOT_ACTIVE'),(0,'BEFORE_TARGET'),(179.999,'BEFORE_TARGET'),(180,'SUCCESS'),(180.000001,'SUCCESS'),(299.999999,'SUCCESS'),(300,'MISSED_SLOT'),(301,'MISSED_SLOT'),(7200,'MISSED_SLOT')])
def test_boundaries(state,seconds,status):
    assert attempt(state,seconds=seconds)['status']==status
    assert (state[0]/'attempts').exists() == (status=='SUCCESS')


def test_naive_time_rejected(state):
    with pytest.raises(ValueError,match='timezone-aware'):
        attempt(state,timer=lambda:S.replace(tzinfo=None))
    assert not (state[0]/'attempts').exists()


def test_selection_never_backlogs(state):
    for now,expected in [(S-timedelta(minutes=1),S),(S,S),(S+timedelta(seconds=180),S),(S+timedelta(seconds=300),S+timedelta(hours=1)),(S+timedelta(hours=6,minutes=7),S+timedelta(hours=7))]:
        assert runner.select_slot(state[0],now,repo_root=state[1])==expected
    assert files(state[0]).keys()=={'config.json'}


@pytest.mark.parametrize('failed',[False,True])
def test_once_only_and_next_slot(state,failed):
    calls=[]
    def capture(**kw):
        calls.append(kw)
        if failed: raise RuntimeError('private content should not be stored')
        return success(**kw)
    first=attempt(state,capture)
    assert first['status']==('FAILED' if failed else 'SUCCESS')
    before=files(state[0])
    assert attempt(state,capture)['status']=='EXISTING_NOOP'
    assert files(state[0])==before and len(calls)==1
    if failed:
        assert 'capture' not in first and 'private content' not in str(first)
    assert runner.select_slot(state[0],S+timedelta(seconds=181),repo_root=state[1])==S+timedelta(hours=1)
    assert attempt(state,slot=S+timedelta(hours=1))['status']=='SUCCESS'


def test_incomplete_is_never_resumed(state):
    path=state[0]/'attempts'/'20261011T130000Z'; path.mkdir(parents=True)
    (path/'attempt.json').write_bytes(b'partial forensic state')
    before=files(state[0])
    assert attempt(state,lambda **kw:pytest.fail('must not capture'))['status']=='INCOMPLETE'
    assert files(state[0])==before


@pytest.mark.parametrize('field,value', [('source_period_end',S-timedelta(minutes=5)),('slot',S+timedelta(hours=1)),('capture_receipt_id',''),('raw_bundle_sha256','not-a-hash'),('status',True),('available_at',S),('available_at',S+timedelta(seconds=301)),('available_at',S.replace(tzinfo=None)),('extra','PnL')])
def test_invalid_success_fails_without_receipt(state,field,value):
    def bad(**kw):
        result=success(**kw); result[field]=value; return result
    result=attempt(state,bad)
    assert result['status']=='FAILED' and 'capture' not in result
    before=files(state[0]); assert attempt(state)['status']=='EXISTING_NOOP'
    assert files(state[0])==before


def test_nonobject_success_fails(state):
    assert attempt(state,lambda **kw:None)['status']=='FAILED'


def test_completion_deadline_inclusive_and_no_late_success(state):
    t=S+timedelta(seconds=180)
    assert attempt(state,timer=clock(t,t,S+timedelta(seconds=300)))['status']=='SUCCESS'
    next_slot=S+timedelta(hours=1); t=next_slot+timedelta(seconds=180)
    assert attempt(state,slot=next_slot,timer=clock(t,t,next_slot+timedelta(seconds=301)))['status']=='FAILED'


def test_deadline_elapsed_during_setup_no_dispatch(state):
    t=S+timedelta(seconds=180); end=S+timedelta(seconds=300)
    assert attempt(state,lambda **kw:pytest.fail('late dispatch'),timer=clock(t,end,end))['status']=='FAILED'


def test_clock_regression_preserves_incomplete(state):
    t=S+timedelta(seconds=180)
    with pytest.raises(ValueError,match='backwards'): attempt(state,timer=clock(t,t,t-timedelta(seconds=1)))
    before=files(state[0]); assert not any(p.endswith('result.json') for p in before)
    assert attempt(state)['status']=='INCOMPLETE'
    assert files(state[0])==before


def test_swallowed_callback_clock_regression_still_fails_closed(state):
    t=S+timedelta(seconds=180)
    def bad(**kw):
        try: kw['clock']()
        except ValueError: pass
        return success(**kw)
    with pytest.raises(ValueError,match='backwards'): attempt(state,bad,timer=clock(t,t,t-timedelta(seconds=1),t))
    assert not any(p.endswith('result.json') for p in files(state[0]))


def test_racing_directory_no_capture(state,monkeypatch):
    original=Path.mkdir
    def mkdir(p,*args,**kw):
        if p.name=='20261011T130000Z':
            original(p)
            raise FileExistsError('other runner won')
        return original(p,*args,**kw)
    monkeypatch.setattr(Path,'mkdir',mkdir)
    assert attempt(state,lambda **kw:pytest.fail('duplicate capture'))['status']=='EXISTING_NOOP'


def test_no_network_or_ledger_surface_and_activation_unchanged(state,monkeypatch):
    def forbidden(*args,**kw): raise AssertionError('network forbidden')
    monkeypatch.setattr(socket.socket,'connect',forbidden)
    assert attempt(state)['status']=='SUCCESS'
    assert set(files(state[0]))=={'config.json','attempts/20261011T130000Z/attempt.json','attempts/20261011T130000Z/result.json'} or {p.replace('\\','/') for p in files(state[0])}=={'config.json','attempts/20261011T130000Z/attempt.json','attempts/20261011T130000Z/result.json'}
    tree=ast.parse(Path(runner.__file__).read_text())
    imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
    imports|={alias.name for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names}
    assert imports=={'datetime','hashlib','json','os','pathlib',None}
    assert hashlib.sha256(Path(activation.__file__).read_bytes()).hexdigest()=='d50b2c6ec8fc7e8335df9544746d9ad20c2dd0a20d5c25a1be845315d267069c'
