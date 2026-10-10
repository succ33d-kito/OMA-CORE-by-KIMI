"""Create-only Windows operator activation. No capture, scheduler or ledger IO.

Only config.json is published; the final directory rename is the commit point.
Frozen design is authenticated on demand, never loaded with import side effects.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import uuid


_REPO = Path(__file__).resolve().parents[2]
_FROZEN = {
    'docs/METRICS_H1_CAPTURE_PROTOCOL.md': '36a9c1b0e3c4319e31c7a38df0c3987924b9a4430e37ca4299d82eedf9cecf18',
    'docs/METRICS_H1_RUNTIME_DESIGN.json': '9334fa01c9adbbf5f3ce7d5d49dd3746be3474c007ef4129fa1a65f8f4ca34d7',
    'research/metrics_2024_2025/PROSPECTIVE_H1_PREREGISTRATION.json': '012a80dcfd4566c7906c61a03f2c5ce3991c31481d2bdb4d87e6855d6005bc46',
}


def _design():
    bodies = {}
    for name, digest in _FROZEN.items():
        body = (_REPO / name).read_bytes()
        if hashlib.sha256(body).hexdigest() != digest:
            raise ValueError('frozen contract hash mismatch: ' + name)
        bodies[name] = body
    return json.loads(bodies['docs/METRICS_H1_RUNTIME_DESIGN.json'])


def _utc(value):
    if not isinstance(value, datetime):
        raise TypeError('datetime required')
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('timezone-aware datetime required')
    return value.astimezone(timezone.utc)


def _select(now, design):
    threshold = _utc(now) + timedelta(seconds=design['activation']['minimum_lead_seconds'])
    boundary = threshold.replace(minute=0, second=0, microsecond=0)
    return boundary if boundary == threshold else boundary + timedelta(hours=1)


def select_activation_slot(now):
    """First UTC hour at or after aware now + the frozen minimum lead."""
    return _select(now, _design())


def _reject_aliases(path):
    # lstat sees dangling links too; inspect ancestors before resolve follows them.
    for component in (path, *path.parents):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError('symlink/reparse path forbidden')


def validate_state_root(state_root, *, repo_root):
    root, repo = Path(state_root), Path(repo_root)
    if not root.is_absolute():
        raise ValueError('absolute state root required')
    if not repo.is_absolute():
        raise ValueError('absolute repository root required')
    if '..' in root.parts or '..' in repo.parts:
        raise ValueError('parent traversal forbidden')
    _reject_aliases(root)
    _reject_aliases(repo)
    if not repo.is_dir():
        raise ValueError('repository root must exist and be directory')
    repo = repo.resolve(strict=True)
    root = root.resolve(strict=False)
    if root == repo or repo in root.parents:
        raise ValueError('state must remain outside repository')
    if root.name != _design()['state_root_policy']['required_leaf']:
        raise ValueError('state root leaf mismatch')
    if not root.parent.is_dir():
        raise ValueError('state parent must already exist and be directory')
    return root


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _config(root, observed, role, design):
    if type(role) is not str or role not in {'PILOT', 'DISCOVERY', 'CONFIRMATION'}:
        raise ValueError('explicit dataset role required')
    body = {
        'schema': 'metrics-h1-activation-v1',
        'contract': design['protocol_contract'],
        'state_root': str(root),
        'observed_at': observed.isoformat(),
        'activation_slot': _select(observed, design).isoformat(),
        'dataset_role': role,
        'instrument': design['instrument'],
        'provider': design['provider'],
        'product': design['product'],
        'minimum_lead_seconds': design['activation']['minimum_lead_seconds'],
        'capture': design['capture'],
        'source_bundle': design['source_bundle'],
        'components': design['components'],
        'readiness': design['readiness'],
        'frozen_sha256': dict(_FROZEN),
    }
    return {**body, 'activation_id': hashlib.sha256(_canonical(body)).hexdigest()}


def _initialize(staging, config):
    with (staging / 'config.json').open('xb') as handle:
        handle.write(_canonical(config))
        handle.flush()
        os.fsync(handle.fileno())


def _verify_staged(staging, expected):
    _reject_aliases(staging)
    if {p.name for p in staging.iterdir()} != {'config.json'}:
        raise ValueError('unexpected activation artifacts')
    path = staging / 'config.json'
    _reject_aliases(path)
    raw = path.read_bytes()
    config = json.loads(raw)
    # Reconstruct from frozen authority, not merely a write/read roundtrip.
    rebuilt = _config(Path(expected['state_root']), datetime.fromisoformat(expected['observed_at']), expected['dataset_role'], _design())
    if raw != _canonical(rebuilt) or _canonical(config) != _canonical(expected):
        raise ValueError('staged configuration violates frozen contract')


def _cleanup(staging):
    # Only our exact staging and known file; never recursive deletion of ambiguity.
    _reject_aliases(staging)
    config = staging / 'config.json'
    _reject_aliases(config)
    if config.exists():
        config.unlink()
    staging.rmdir()  # Unexpected residue propagates; never silently swallowed.


def activate(state_root, *, repo_root, now, dataset_role):
    """Explicit operator transaction; dataset role has no implicit default.

    Windows-only publication guarantees rename cannot replace any existing root.
    now is operator clock input (injectable for tests), not market availability.
    """
    if os.name != 'nt':
        raise OSError('Windows non-replacing directory publication required')
    observed = _utc(now)
    design = _design()
    root = validate_state_root(state_root, repo_root=repo_root)
    if root.exists():
        raise FileExistsError('activation state already exists')
    prefix = '.' + root.name + '.activating-'
    if any(root.parent.glob(prefix + '*')):
        raise FileExistsError('activation staging residue exists')
    config = _config(root, observed, dataset_role, design)
    result = {'status': 'ACTIVATED', **config}
    staging = root.parent / (prefix + uuid.uuid4().hex)
    staging.mkdir()  # Exclusive; failed mkdir never grants cleanup ownership.
    published = False
    try:
        _initialize(staging, config)
        _verify_staged(staging, config)
        validate_state_root(root, repo_root=repo_root)
        if any(p != staging for p in root.parent.glob(prefix + '*')):
            raise FileExistsError('concurrent activation residue exists')
        os.rename(staging, root)  # Windows: atomic, destination must not exist.
        published = True
    finally:
        if not published:
            _cleanup(staging)
    return result  # No fallible IO after the commit point.
