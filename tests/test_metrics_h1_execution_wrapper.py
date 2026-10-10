from datetime import datetime, timezone
import json

import pytest
from scripts import run_metrics_h1 as wrapper
from core.scientific import metrics_h1_activation as activation


@pytest.fixture
def state(tmp_path, monkeypatch):
    repo = tmp_path/'repo'
    repo.mkdir()
    monkeypatch.setattr(wrapper, 'REPO_ROOT', repo)
    root = tmp_path/'metrics-h1-v1'
    activation.activate(root, repo_root=repo,
                        now=datetime(2026,10,10,tzinfo=timezone.utc), dataset_role='PILOT')
    return root


def forbidden(*args, **kwargs):
    raise AssertionError('unexpected runtime/network invocation')


def test_check_is_read_only_and_not_liveness(state, capsys):
    before = (state/'config.json').read_bytes()
    assert wrapper.main(['check','--state',str(state)], run_runtime=forbidden, transport=forbidden)==0
    result = json.loads(capsys.readouterr().out)
    assert result['runtime_liveness']=='UNVERIFIED'
    assert result['network_executed'] is False
    assert result['dataset_role']=='PILOT'
    assert list(state.iterdir()) == [state/'config.json']
    assert (state/'config.json').read_bytes()==before


def test_run_passes_exact_state_and_explicit_transport(state):
    calls=[]
    def runtime(root, **kwargs): calls.append((root,kwargs))
    assert wrapper.main(['run','--state',str(state),'--allow-public-http'],
                        run_runtime=runtime,transport=forbidden)==0
    assert calls==[(state,dict(repo_root=wrapper.REPO_ROOT,transport=forbidden))]


def test_run_requires_explicit_network_flag(state):
    with pytest.raises(SystemExit):
        wrapper.main(['run','--state',str(state)],run_runtime=forbidden,transport=forbidden)


@pytest.mark.parametrize('command',['check','run'])
def test_missing_state_never_activates(tmp_path, monkeypatch, command):
    repo=tmp_path/'repo'; repo.mkdir()
    monkeypatch.setattr(wrapper,'REPO_ROOT',repo)
    root=tmp_path/'metrics-h1-v1'
    args=[command,'--state',str(root)]
    if command=='run': args.append('--allow-public-http')
    with pytest.raises(FileNotFoundError):
        wrapper.main(args,run_runtime=forbidden,transport=forbidden)
    assert not root.exists()


@pytest.mark.parametrize('mutation',['role','hash','unknown'])
def test_tampered_config_never_runs(state,mutation):
    path=state/'config.json'; body=json.loads(path.read_bytes())
    if mutation=='role': body['dataset_role']='CONFIRMATION'
    elif mutation=='hash': body['activation_id']='0'*64
    else: body['extra']=True
    path.write_text(json.dumps(body))
    with pytest.raises(ValueError):
        wrapper.main(['run','--state',str(state),'--allow-public-http'],
                     run_runtime=forbidden,transport=forbidden)


def test_relative_state_rejected():
    with pytest.raises(ValueError): wrapper.check_state('metrics-h1-v1')


def test_no_timestamp_or_role_override(state):
    with pytest.raises(SystemExit):
        wrapper.main(['run','--state',str(state),'--allow-public-http','--role','DISCOVERY'],
                     run_runtime=forbidden,transport=forbidden)
