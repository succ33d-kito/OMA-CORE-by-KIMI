import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/activate_funding_h1.py"

@pytest.fixture
def ceremony(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("ceremony", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / 'docs').mkdir()
    (repo / 'docs/FUNDING_H1_RUNTIME_DESIGN.json').write_bytes((module.REPO_ROOT / 'docs/FUNDING_H1_RUNTIME_DESIGN.json').read_bytes())
    module.REPO_ROOT = repo
    monkeypatch.setattr(module, '_now', clock)
    monkeypatch.setattr(module, '_repository', lambda: dict(root=str(repo),branch='test',head='a'*40,dirty=False,activation_sha256='b'*64,ceremony_sha256='c'*64))
    monkeypatch.setenv('USERPROFILE', str(tmp_path / 'profile'))
    parent = tmp_path / 'profile' / 'Documents' / 'O-C data' / 'prospective'
    parent.mkdir(parents=True)
    return module, parent / "funding-h1-v1"


def clock():
    return datetime(2026, 10, 10, 11, 49, 30, tzinfo=timezone.utc)


def execute_at(module, plan, delay):
    module._now = lambda: clock()+timedelta(seconds=delay)
    return module.execute(plan,module.confirmation(plan))


@pytest.mark.parametrize('key,value', [('head','d'*40),('dirty',True),('activation_sha256','e'*64),('ceremony_sha256','f'*64)])
def test_repository_change_blocks(ceremony,monkeypatch,key,value):
    module,state=ceremony
    plan=module.prepare()
    changed=dict(plan['repository']); changed[key]=value
    monkeypatch.setattr(module,'_repository',lambda:changed)
    with pytest.raises(ValueError): module.execute(plan,module.confirmation(plan))
    assert not state.exists()


def test_design_and_arbitrary_state_change_block(ceremony):
    module,state=ceremony
    plan=module.prepare()
    plan['state_root']=str(state.parent/'other')
    with pytest.raises(ValueError): module.execute(plan,module.confirmation(plan))
    design=module.REPO_ROOT/'docs/FUNDING_H1_RUNTIME_DESIGN.json'
    design.write_bytes(design.read_bytes()+b' ')
    with pytest.raises(ValueError,match='design identity'): module.prepare()
    assert not state.exists()


def test_no_public_path_or_time_override(ceremony):
    import inspect
    module,state=ceremony
    assert not inspect.signature(module.prepare).parameters
    assert tuple(inspect.signature(module.execute).parameters)==('plan','token')
    for args in (['plan','--state',str(state)],['plan','--now',clock().isoformat()]):
        with pytest.raises(SystemExit): module.main(args)
    assert not state.exists()


def test_reparse_ancestor_fails_closed(ceremony,monkeypatch):
    import stat
    from types import SimpleNamespace
    module,state=ceremony
    original=Path.lstat
    def guarded(path,*args,**kwargs):
        if path==state.parent:
            return SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'lstat',guarded)
    with pytest.raises(ValueError,match='reparse'): module.prepare()


def test_primitive_failure_has_no_retry(ceremony,monkeypatch):
    module,state=ceremony
    plan=module.prepare(); calls=[]
    def failure(*args,**kwargs):
        calls.append(1)
        raise OSError('publication failed')
    monkeypatch.setattr(module.activation,'activate',failure)
    with pytest.raises(OSError): module.execute(plan,module.confirmation(plan))
    assert calls==[1] and not state.exists()


def test_plan_is_read_only(ceremony):
    module, state = ceremony
    before = list(state.parent.iterdir())
    plan = module.prepare()
    assert list(state.parent.iterdir()) == before
    assert plan["activation_slot"] == "2026-10-10T12:00:00+00:00"
    assert not plan["installs_task"]
    assert not plan["starts_runtime"]


@pytest.mark.parametrize("delay", [-1, 61])
def test_stale_or_regressed_clock_has_no_writes(ceremony, delay):
    module, state = ceremony
    plan = module.prepare()
    with pytest.raises(ValueError, match="expired or clock regressed"):
        execute_at(module, plan, delay)
    assert list(state.parent.iterdir()) == []


def test_changed_boundary_has_no_writes(ceremony):
    module, state = ceremony
    plan = module.prepare()
    with pytest.raises(ValueError, match="boundary changed"):
        execute_at(module, plan, 31)
    assert list(state.parent.iterdir()) == []


def test_confirmation_and_contract_required(ceremony):
    module, state = ceremony
    plan = module.prepare()
    with pytest.raises(ValueError, match="confirmation"):
        module.execute(plan, "yes")
    plan["retry_policy"] = "RETRY"
    with pytest.raises(ValueError, match="contract mismatch"):
        module.execute(plan, module.confirmation(plan))
    assert list(state.parent.iterdir()) == []


def test_confirmed_activation_is_create_only(ceremony):
    module, state = ceremony
    plan = module.prepare()
    result = execute_at(module, plan, 10)
    assert result["activation_slot"] == plan["activation_slot"]
    assert list((state / "attempts").iterdir()) == []
    assert not (state / "runtime").exists()
    before = (state / "config.json").read_bytes()
    with pytest.raises((FileExistsError, ValueError)):
        execute_at(module, plan, 20)
    assert (state / "config.json").read_bytes() == before


def test_residue_blocks_plan(ceremony):
    module, state = ceremony
    residue = state.parent / ".funding-h1-v1.activating-interrupted"
    residue.mkdir()
    plan = module.prepare()
    assert plan['activation_residue'] == [residue.name]
    with pytest.raises(FileExistsError, match="residue"):
        module.execute(plan, module.confirmation(plan))
    assert residue.exists()
    assert not state.exists()
