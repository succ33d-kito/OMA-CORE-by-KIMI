"""Isolated activation qualification. No real state, HTTP or scheduler."""
import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import socket
import stat
from types import SimpleNamespace

import pytest
from core.scientific import metrics_h1_activation as a


def dt(hour, minute=0, second=0, microsecond=0):
    return datetime(2026, 10, 10, hour, minute, second, microsecond, tzinfo=timezone.utc)


@pytest.fixture
def roots(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    parent = tmp_path / 'prospective'
    parent.mkdir()
    return repo, parent / 'metrics-h1-v1'


def activate(roots, **kwargs):
    repo, state = roots
    return a.activate(state, repo_root=repo, now=kwargs.pop('now', dt(12, 40)), dataset_role=kwargs.pop('dataset_role', 'PILOT'), **kwargs)


@pytest.mark.parametrize('now,expected', [(dt(12,40),dt(13)), (dt(12,51),dt(14)), (dt(12,50),dt(13)), (dt(12,50,0,1),dt(14)), (dt(23,55),dt(1)+timedelta(days=1)), (dt(12,50).astimezone(timezone(timedelta(hours=2))),dt(13))])
def test_slot_boundaries(now, expected):
    assert a.select_activation_slot(now) == expected


def test_naive_rejected_before_writes(roots):
    with pytest.raises(ValueError, match='timezone-aware'):
        activate(roots, now=datetime(2026,10,10))
    assert list(roots[1].parent.iterdir()) == []


@pytest.mark.parametrize('case', ['relative_state','relative_repo','missing_repo','repo_file','inside','equal','wrong_leaf','missing_parent','parent_file','traversal'])
def test_invalid_paths(roots, case):
    repo, state = roots
    if case == 'relative_state': state = Path('metrics-h1-v1')
    if case == 'relative_repo': repo = Path('repo')
    if case == 'missing_repo': repo = repo / 'missing'
    if case == 'repo_file':
        repo = repo / 'file'; repo.write_text('x')
    if case == 'inside': state = repo / 'metrics-h1-v1'
    if case == 'equal': state = repo
    if case == 'wrong_leaf': state = state.with_name('funding-h1-v1')
    if case == 'missing_parent': state = state.parent / 'missing' / state.name
    if case == 'parent_file':
        parent = state.parent / 'file'; parent.write_text('x'); state = parent / state.name
    if case == 'traversal': state = state.parent / '..' / state.parent.name / state.name
    with pytest.raises((ValueError, OSError)):
        a.activate(state, repo_root=repo, now=dt(12), dataset_role='PILOT')


def test_success_frozen_config_only_no_network(roots, monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError('network forbidden')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    result = activate(roots)
    state = roots[1]
    assert result['status'] == 'ACTIVATED'
    assert [p.name for p in state.iterdir()] == ['config.json']
    c = json.loads((state/'config.json').read_bytes())
    assert c == {k:v for k,v in result.items() if k != 'status'}
    assert c['activation_slot'] == dt(13).isoformat()
    assert c['dataset_role'] == 'PILOT'
    assert (c['instrument'],c['product'],c['provider']) == ('BTCUSDT','USD-M','https://fapi.binance.com')
    assert c['capture']['cadence'] == 'H1'
    assert (c['capture']['target_offset_seconds'],c['capture']['deadline_offset_seconds']) == (180,300)
    assert c['capture']['same_slot_retry'] == 'NONE'
    assert all(c['capture'][k] is False for k in ('backfill','historical_repair','interpolation','synthetic_availability'))
    assert c['source_bundle']['expected_period_end'] == 'SLOT'
    assert c['source_bundle']['complete_required'] is True
    assert c['readiness']['required_consecutive_success_slots'] == 81
    assert list(state.parent.iterdir()) == [state]
    identity = c.pop('activation_id')
    assert identity == hashlib.sha256(a._canonical(c)).hexdigest()


@pytest.mark.parametrize('populated', [False, True])
def test_existing_root_preserved(roots, populated):
    state = roots[1]; state.mkdir()
    if populated: (state/'sentinel').write_bytes(b'preserve')
    before = {p.name:p.read_bytes() for p in state.iterdir()}
    with pytest.raises(FileExistsError): activate(roots)
    assert {p.name:p.read_bytes() for p in state.iterdir()} == before


def test_reactivation_cannot_shift_slot_or_role(roots):
    activate(roots)
    path = roots[1]/'config.json'; before = path.read_bytes()
    with pytest.raises(FileExistsError): activate(roots, now=dt(15), dataset_role='CONFIRMATION')
    assert path.read_bytes() == before


def test_unknown_role_creates_nothing(roots):
    with pytest.raises(ValueError, match='role'): activate(roots, dataset_role='UNKNOWN')
    assert list(roots[1].parent.iterdir()) == []


def test_residue_preserved(roots):
    residue = roots[1].parent / '.metrics-h1-v1.activating-old'; residue.mkdir()
    (residue/'partial').write_bytes(b'evidence')
    with pytest.raises(FileExistsError, match='residue'): activate(roots)
    assert (residue/'partial').read_bytes() == b'evidence'
    assert not roots[1].exists()


@pytest.mark.parametrize('phase', ['initialize','validate','publish'])
def test_precommit_failure_no_final_root(roots, monkeypatch, phase):
    def fail(*args): raise OSError('injected failure')
    if phase == 'initialize': monkeypatch.setattr(a,'_initialize',fail)
    if phase == 'validate': monkeypatch.setattr(a,'_verify_staged',fail)
    if phase == 'publish': monkeypatch.setattr(a.os,'rename',fail)
    with pytest.raises(OSError, match='injected'): activate(roots)
    assert list(roots[1].parent.iterdir()) == []


def test_staged_tamper_is_independently_rejected(roots, monkeypatch):
    original = a._initialize
    def tamper(path, config):
        original(path, config)
        changed = dict(config); changed['capture'] = dict(config['capture'], target_offset_seconds=0)
        (path/'config.json').write_bytes(a._canonical(changed))
    monkeypatch.setattr(a,'_initialize',tamper)
    with pytest.raises(ValueError, match='frozen contract'): activate(roots)
    assert list(roots[1].parent.iterdir()) == []


def test_partial_write_is_cleaned(roots, monkeypatch):
    def fail(path, config):
        (path/'config.json').write_bytes(b'{')
        raise OSError('partial write')
    monkeypatch.setattr(a,'_initialize',fail)
    with pytest.raises(OSError, match='partial'): activate(roots)
    assert list(roots[1].parent.iterdir()) == []


def test_cleanup_failure_visible_and_blocks_next_call(roots, monkeypatch):
    def fail(*args): raise OSError('initialization failed')
    def cleanup(*args): raise OSError('cleanup failed')
    with monkeypatch.context() as m:
        m.setattr(a,'_initialize',fail); m.setattr(a,'_cleanup',cleanup)
        with pytest.raises(OSError, match='cleanup failed') as error: activate(roots)
        assert 'initialization failed' in str(error.value.__context__)
    assert not roots[1].exists()
    with pytest.raises(FileExistsError, match='residue'): activate(roots)


def test_racing_destination_never_overwritten(roots, monkeypatch):
    rename = a.os.rename
    def race(source, destination):
        destination.mkdir()
        return rename(source,destination)
    monkeypatch.setattr(a.os,'rename',race)
    with pytest.raises(FileExistsError): activate(roots)
    assert roots[1].is_dir() and list(roots[1].iterdir()) == []


def test_no_read_after_publication(roots, monkeypatch):
    rename = a.os.rename
    def publish(source,destination):
        assert [p.name for p in source.iterdir()] == ['config.json']
        rename(source,destination)
        def forbidden(*args,**kwargs): raise AssertionError('read after commit')
        monkeypatch.setattr(Path,'read_bytes',forbidden)
        monkeypatch.setattr(Path,'exists',forbidden)
    monkeypatch.setattr(a.os,'rename',publish)
    assert activate(roots)['status'] == 'ACTIVATED'


def test_ancestor_reparse_rejected(roots, monkeypatch):
    original = Path.lstat
    parent = roots[1].parent
    def lstat(path,*args,**kwargs):
        if path == parent: return SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'lstat',lstat)
    with pytest.raises(ValueError, match='reparse'): activate(roots)


def test_actual_symlink_rejected_when_supported(roots):
    link = roots[1]
    try: link.symlink_to(roots[0],target_is_directory=True)
    except OSError as exc:
        if getattr(exc,'winerror',None) == 1314: pytest.skip('Windows symlink privilege unavailable; reparse regression covered')
        raise
    with pytest.raises(ValueError, match='symlink'): activate(roots)


def test_frozen_hashes_and_import_surface():
    for name,digest in a._FROZEN.items():
        assert hashlib.sha256((a._REPO/name).read_bytes()).hexdigest() == digest
    tree = ast.parse(Path(a.__file__).read_text())
    imports = {n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
    imports |= {alias.name for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names}
    assert imports == {'datetime','hashlib','json','os','pathlib','stat','uuid'}
