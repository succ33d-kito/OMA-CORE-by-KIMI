"""Read-only Metrics evidence verifier; no network, writes or outcome access.

Checks content integrity and the frozen causal contract, not provider honesty or
tamper resistance against an actor able to replace every local artifact/hash.
SUCCESS requires runner result AND all raw/receipt/availability evidence.
"""
import base64
from datetime import timedelta
import hashlib
from pathlib import Path

from core.market_mechanics.binance_live_adapter import METRIC_ENDPOINTS, _period_end, normalize_bundle
from . import metrics_h1_activation as activation
from . import metrics_h1_runner as runner
from .metrics_h1_live_adapter import _json


def _digest(value):
    return hashlib.sha256(activation._canonical(value)).hexdigest()


def _read(path):
    activation._reject_aliases(path)
    body = path.read_bytes()
    obj = _json(body)
    if type(obj) is not dict or activation._canonical(obj) != body:
        raise ValueError('noncanonical artifact')
    return obj


def _same(actual, expected):
    if activation._canonical(actual) != activation._canonical(expected):
        raise ValueError('artifact contract mismatch')


def _verify_success(path, config, slot, attempt, result, now):
    receipt = _read(path/'capture'/'receipt.json')
    marker = _read(path/'capture'/'available.json')
    if (path/'capture'/'available.pending').exists():
        raise ValueError('ambiguous availability publication')
    target, deadline = runner._bounds(config, slot)
    started = runner._utc(attempt['started_at'])
    available = runner._utc(marker['available_at'])
    completed = runner._utc(result['completed_at'])
    if not started <= available <= completed <= min(deadline, now):
        raise ValueError('noncausal publication')
    selected, material, components = {}, {}, {}
    previous = started
    if set(receipt['components']) != set(METRIC_ENDPOINTS):
        raise ValueError('incomplete component metadata')
    for key, endpoint in METRIC_ENDPOINTS.items():
        raw_path = path/'capture'/'raw'/(key+'.json')
        activation._reject_aliases(raw_path)
        raw = raw_path.read_bytes()
        rows = _json(raw)
        if type(rows) is not list or not 1 <= len(rows) <= 5:
            raise ValueError('invalid raw response')
        matches = []
        for row in rows:
            if type(row) is not dict or row.get('symbol') != config['instrument'] or type(row.get('timestamp')) is not int:
                raise ValueError('raw scope mismatch')
            if _period_end(row['timestamp'], start_label=key=='taker') == slot:
                matches.append(row)
        if len(matches) != 1:
            raise ValueError('exact row missing or duplicated')
        row = matches[0]
        for field in config['components'][key]['fields']:
            if type(row.get(field)) not in (int, float, str):
                raise ValueError('invalid numeric type')
        selected[key] = row
        material[endpoint] = base64.b64encode(raw).decode('ascii')
        meta = receipt['components'][key]
        requested, received = map(runner._utc, (meta['request_started_at'], meta['received_at']))
        if not target <= previous <= requested < deadline or not requested <= received <= available:
            raise ValueError('noncausal sequential capture')
        previous = received
        components[key] = {'endpoint': endpoint, 'request_parameters': {'symbol':'BTCUSDT','period':'5m','limit':5},
                           'http_status': meta['http_status'], 'request_started_at': requested.isoformat(),
                           'received_at': received.isoformat(), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
                           'raw_timestamp': row['timestamp'], 'timestamp_label': 'START' if key=='taker' else 'END',
                           'source_period_end': slot.isoformat()}
        if type(meta['http_status']) is not int or not 200 <= meta['http_status'] < 300:
            raise ValueError('HTTP status rejected')
    normalized = normalize_bundle(selected)
    expected = {'schema':'metrics-h1-capture-receipt-v1','contract':config['contract'],
                'provider':config['provider'],'market':config['product'],'instrument':config['instrument'],
                'dataset_role':config['dataset_role'],'activation_id':config['activation_id'],
                'slot':slot.isoformat(),'source_period_end':slot.isoformat(),'expected_source_period_end':slot.isoformat(),
                'source_period_start':(slot-timedelta(minutes=5)).isoformat(),
                'normalized_source_timestamp':(slot-timedelta(microseconds=1)).isoformat(),
                'attempt_started_at':started.isoformat(),'components':components,'normalized_metrics':normalized,
                'raw_bundle_sha256':_digest(material),'selected_rows_sha256':_digest(selected)}
    expected['receipt_id'] = _digest(expected)
    _same(receipt, expected)
    _same(marker, {'schema':'metrics-h1-availability-v1','receipt_id':expected['receipt_id'],
                   'available_at':available.isoformat(),'slot':slot.isoformat(),'source_period_end':slot.isoformat()})
    _same(result['capture'], {'status':'SUCCESS','slot':slot.isoformat(),'source_period_end':slot.isoformat(),
                             'capture_receipt_id':expected['receipt_id'],'raw_bundle_sha256':expected['raw_bundle_sha256'],
                             'available_at':available.isoformat()})


def _classify(root, config, slot, now):
    path = runner._path(root, slot)
    target, deadline = runner._bounds(config, slot)
    if not path.exists():
        return 'MISSED_SLOT' if now >= deadline else 'NOT_DUE'
    if not path.is_dir():
        raise ValueError('attempt path is not directory')
    if not (path/'attempt.json').exists():
        if any(path.iterdir()):
            raise ValueError('artifacts without attempt authority')
        return 'INCOMPLETE'
    attempt = _read(path/'attempt.json')
    started = runner._utc(attempt['started_at'])
    if not target <= started < deadline or started > now:
        raise ValueError('attempt start outside window')
    slot_id = _digest([config['contract'],config['activation_id'],config['instrument'],slot.isoformat()])
    attempt_id = _digest(['metrics-h1-attempt-v1',slot_id])
    _same(attempt, {'slot':slot.isoformat(),'schema':'metrics-h1-attempt-v1','contract':config['contract'],
                    'activation_id':config['activation_id'],'dataset_role':config['dataset_role'],
                    'slot_id':slot_id,'attempt_id':attempt_id,'status':'STARTED',
                    'target_at':target.isoformat(),'deadline_at':deadline.isoformat(),
                    'expected_source_period_end':slot.isoformat(),'started_at':started.isoformat()})
    if not (path/'result.json').exists():
        return 'INCOMPLETE'
    result = _read(path/'result.json')
    completed = runner._utc(result['completed_at'])
    if not started <= completed <= now:
        raise ValueError('invalid completion time')
    status = result['status']
    if status not in ('FAILED','SUCCESS'):
        raise ValueError('invalid final status')
    expected = {'slot':slot.isoformat(),'schema':'metrics-h1-result-v1','contract':config['contract'],
                'attempt_id':attempt_id,'status':status,'completed_at':completed.isoformat()}
    if status == 'FAILED':
        if type(result.get('error')) is not str or not result['error']:
            raise ValueError('failure reason missing')
        expected['error'] = result['error']
    else:
        expected['capture'] = result['capture']
    expected['result_id'] = _digest(expected)
    _same(result, expected)
    if status == 'SUCCESS':
        _verify_success(path, config, slot, attempt, result, now)
    return status  # FAILED never promotes leftover receipt/available artifacts.


def verify_slot(state, slot, *, repo_root, now):
    config = runner.load_config(state, repo_root=repo_root)
    slot, now = runner._slot(slot), runner._utc(now)
    if slot < runner._slot(config['activation_slot']):
        raise ValueError('slot precedes activation')
    try:
        status = _classify(Path(state), config, slot, now)
        return {'slot':slot.isoformat(),'status':status}
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return {'slot':slot.isoformat(),'status':'INVALID'}


def status(state, *, repo_root, now):
    """Certificate of closed slots only. Reads do not repair or create anything."""
    config = runner.load_config(state, repo_root=repo_root)
    now = runner._utc(now)
    slot = runner._slot(config['activation_slot'])
    counts = dict.fromkeys(('SUCCESS','FAILED','MISSED_SLOT','INCOMPLETE','INVALID'),0)
    current = longest = 0
    while runner._bounds(config, slot)[1] <= now:
        try:
            value = _classify(Path(state), config, slot, now)
        except (OSError, ValueError, TypeError, KeyError, OverflowError):
            value = 'INVALID'
        counts[value] += 1
        current = current+1 if value == 'SUCCESS' else 0
        longest = max(longest,current)
        slot += timedelta(hours=1)
    return {'schema':'metrics-h1-continuity-v1','as_of':now.isoformat(),'counts':counts,
            'current_streak':current,'longest_streak':longest,
            'METRICS_OPERATIONAL_READINESS_81H':current >= config['readiness']['required_consecutive_success_slots'],
            'meaning':'DATA_PLANE_READINESS_ONLY','research_gate':'NOT_EVALUATED','EDGE':'NOT_DEMONSTRATED'}
