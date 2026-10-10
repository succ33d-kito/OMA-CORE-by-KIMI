"""Network-free, once-only Metrics H1 orchestration with injected capture.

SUCCESS qualifies the callback envelope, not Binance payloads or raw admission.
The future live adapter must verify/persist the actual complete causal bundle.
No initialization, continuity engine, heartbeat, lock, or scientific ledger IO.
"""
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path

from . import metrics_h1_activation as activation


def _utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return activation._utc(value)


def _slot(value):
    value = _utc(value)
    if value != value.replace(minute=0, second=0, microsecond=0):
        raise ValueError('UTC H1 boundary required')
    return value


def _hash(value):
    return hashlib.sha256(activation._canonical(value)).hexdigest()


def load_config(state, *, repo_root):
    """Read-only authentication of the exact activation configuration."""
    root = activation.validate_state_root(state, repo_root=repo_root)
    path = root / 'config.json'
    activation._reject_aliases(path)
    raw = path.read_bytes()
    config = json.loads(raw)
    if type(config) is not dict:
        raise ValueError('configuration must be object')
    try:
        expected = activation._config(root, _utc(config['observed_at']), config['dataset_role'], activation._design())
    except (KeyError, TypeError) as exc:
        raise ValueError('malformed activation config') from exc
    if raw != activation._canonical(expected):
        raise ValueError('activation config changed or violates frozen contract')
    return config


def _bounds(config, slot):
    c = config['capture']
    return (slot + timedelta(seconds=c['target_offset_seconds']),
            slot + timedelta(seconds=c['deadline_offset_seconds']))


def _path(state, slot):
    path = Path(state) / 'attempts' / slot.strftime('%Y%m%dT%H0000Z')
    activation._reject_aliases(path)
    return path


def select_slot(state, now, *, repo_root):
    """Current eligible/future slot only; never scan past slots for work."""
    config = load_config(state, repo_root=repo_root)
    now = _utc(now)
    first = _slot(config['activation_slot'])
    if now < first:
        return first
    slot = now.replace(minute=0, second=0, microsecond=0)
    if now >= _bounds(config, slot)[1] or _path(state, slot).exists():
        return slot + timedelta(hours=1)
    return slot


def _write(path, body):
    activation._reject_aliases(path)
    with path.open('xb') as handle:
        handle.write(activation._canonical(body))
        handle.flush()
        os.fsync(handle.fileno())


def _capture_result(value, slot, started, completed, deadline):
    fields = {'status', 'slot', 'source_period_end', 'capture_receipt_id', 'raw_bundle_sha256', 'available_at'}
    if type(value) is not dict or set(value) != fields or value['status'] != 'SUCCESS':
        raise ValueError('invalid capture structure')
    if _slot(value['slot']) != slot or _slot(value['source_period_end']) != slot:
        raise ValueError('capture slot/source period mismatch')
    if type(value['capture_receipt_id']) is not str or not value['capture_receipt_id'].strip():
        raise ValueError('capture identity missing')
    digest = value['raw_bundle_sha256']
    if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('invalid raw bundle SHA256')
    available = _utc(value['available_at'])
    if not started <= available <= completed <= deadline:
        raise ValueError('capture availability/completion outside causal window')
    return {**value, 'slot': slot.isoformat(), 'source_period_end': slot.isoformat(), 'available_at': available.isoformat()}


def attempt_slot(state, slot, capture, *, repo_root, clock):
    """One attempt, keyword-only capture boundary, no retry even after failure.

    Callback returns exactly status, slot, source_period_end, capture_receipt_id,
    raw_bundle_sha256, available_at. Capture must persist its own evidence before
    returning; runner only authenticates this envelope. Clock failure preserves
    INCOMPLETE rather than fabricating a completion timestamp.
    """
    config = load_config(state, repo_root=repo_root)
    slot = _slot(slot)
    first = _slot(config['activation_slot'])
    started = _utc(clock())
    target, deadline = _bounds(config, slot)
    base = {'slot': slot.isoformat()}
    if slot < first or started < first:
        return {**base, 'status': 'NOT_ACTIVE'}
    path = _path(state, slot)
    if path.exists():
        # This is a no-retry marker, not a fresh integrity certificate.
        return {**base, 'status': 'EXISTING_NOOP' if (path/'result.json').exists() else 'INCOMPLETE'}
    if started < target:
        return {**base, 'status': 'BEFORE_TARGET'}
    if started >= deadline:
        return {**base, 'status': 'MISSED_SLOT'}
    if not callable(capture):
        raise TypeError('capture callable required')
    path.parent.mkdir(exist_ok=True)  # Config must already exist; no state init.
    activation._reject_aliases(path)
    try:
        path.mkdir()  # Exclusive reservation is the once-only authority.
    except FileExistsError:
        return {**base, 'status': 'EXISTING_NOOP'}
    slot_id = _hash([config['contract'], config['activation_id'], config['instrument'], slot.isoformat()])
    attempt_id = _hash(['metrics-h1-attempt-v1', slot_id])
    attempt = {**base, 'schema': 'metrics-h1-attempt-v1', 'contract': config['contract'],
               'activation_id': config['activation_id'], 'dataset_role': config['dataset_role'],
               'slot_id': slot_id, 'attempt_id': attempt_id, 'status': 'STARTED',
               'target_at': target.isoformat(), 'deadline_at': deadline.isoformat(),
               'expected_source_period_end': slot.isoformat(), 'started_at': started.isoformat()}
    _write(path/'attempt.json', attempt)
    previous = started
    clock_invalid = False

    def guarded_clock():
        nonlocal previous, clock_invalid
        try:
            current = _utc(clock())
            if clock_invalid or current < previous:
                raise ValueError('clock moved backwards')
            previous = current
            return current
        except Exception:
            clock_invalid = True
            raise

    error = None
    value = None
    try:
        if guarded_clock() >= deadline:
            raise ValueError('deadline elapsed before capture dispatch')
        value = capture(capture_directory=path/'capture', slot=slot,
                        expected_source_period_end=slot, target_at=target,
                        deadline_at=deadline, attempt_started_at=started,
                        clock=guarded_clock)
    except Exception as exc:
        # Do not persist arbitrary callback exceptions containing sensitive data.
        error = 'CAPTURE_EXCEPTION:' + type(exc).__name__
    completed = guarded_clock()  # Regressed/invalid clock leaves forensic INCOMPLETE.
    if load_config(state, repo_root=repo_root) != config:
        raise ValueError('configuration changed during attempt')
    if error is None:
        try:
            value = _capture_result(value, slot, started, completed, deadline)
        except (ValueError, TypeError, KeyError, OverflowError):
            error = 'INVALID_CAPTURE_RESULT'
    result = {**base, 'schema': 'metrics-h1-result-v1', 'contract': config['contract'],
              'attempt_id': attempt_id, 'status': 'FAILED' if error else 'SUCCESS',
              'completed_at': completed.isoformat()}
    if error:
        result['error'] = error
    else:
        result['capture'] = value
    result['result_id'] = _hash(result)
    _write(path/'result.json', result)
    return result
