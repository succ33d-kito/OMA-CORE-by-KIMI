from contextlib import nullcontext
from pathlib import Path
import json
import pytest
from tests.test_price_role_h1_runner import env, REPO
from scripts import run_price_role_h1 as cli
from core.scientific import price_role_h1_runner as runner


@pytest.mark.parametrize('command',['check','status'])
def test_read_only_commands_no_network_or_state_writes(env,capsys,command):
    before = {p.relative_to(env.root):p.read_bytes() for p in env.root.rglob('*') if p.is_file()}
    def forbidden():
        pytest.fail('no HTTP in check/status')
    assert cli.main([command,'--state',str(env.root)],session_factory=forbidden) == 0
    output = json.loads(capsys.readouterr().out)
    assert output['dataset_role'] == 'PILOT' and output['network_executed'] is False
    assert before == {p.relative_to(env.root):p.read_bytes() for p in env.root.rglob('*') if p.is_file()}


def test_run_requires_activation_before_session(tmp_path):
    root = tmp_path/runner.LEAF
    def forbidden():
        pytest.fail('session must not open before activation authentication')
    with pytest.raises(FileNotFoundError):
        cli.main(['run','--state',str(root),'--allow-public-http'],session_factory=forbidden)
    assert not root.exists()


def test_run_requires_explicit_network_consent(env):
    with pytest.raises(SystemExit):
        cli.main(['run','--state',str(env.root)])


def test_run_binds_only_explicit_existing_state(env):
    calls = []
    session = object()
    assert cli.main(['run','--state',str(env.root),'--allow-public-http'],
        run_runtime=lambda root,**k:calls.append((root,k)),session_factory=lambda:nullcontext(session)) == 0
    assert calls == [(env.root,{'repo_root':REPO,'session':session})]


def test_installer_is_separate_create_only_and_not_activation():
    source = (REPO/'scripts/install_price_role_h1_task.ps1').read_text()
    assert "'OMA-CORE-Prospective-Price-Role-H1'" in source
    assert "'OMA-CORE-Prospective-Price-H1'" not in source
    assert 'check --state' in source and 'CONFIG_VERIFIED' in source and 'PILOT' in source
    assert 'already exists; no overwrite' in source
    assert 'Start-ScheduledTask' not in source and ' -Force' not in source
    assert 'activate(' not in source and 'installer_initializes_state=$false' in source
    assert 'qualifiedPython' in source


def test_all_five_frozen_surfaces_unchanged():
    import subprocess
    paths = ['core/market_mechanics/binance_live_adapter.py','core/scientific/prospective_receipts.py',
        'core/scientific/price_continuity.py','scripts/capture_price_h1.py','scripts/install_price_capture_task.ps1']
    for name in paths:
        old = subprocess.check_output(['git','show','1bd4ca6f76fe5a62ee450547be6a68d44c105d65:'+name],cwd=REPO)
        assert (REPO/name).read_bytes().replace(b'\r\n',b'\n') == old.replace(b'\r\n',b'\n')
