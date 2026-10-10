"""Exact-period Metrics capture; transport is always explicitly injected.

Transport(url, *, params, timeout, allow_redirects=False) returns
(HTTP status, final URL, exact response bytes). It must perform one bounded
request, without retries, proxies, caching or redirects. No default network
transport is installed here. A bounded five-row recent query is selection within
the current transaction, never a historical catch-up operation.

raw_bundle_sha256 follows 48B: SHA256(canonical endpoint -> base64 raw bytes).
receipt_id additionally commits scope, exact period, normalized values and
chronology. Canonical JSON is sorted-key compact UTF-8, no NaN, no newline.
No observations_v2 admission: persisted captures require later verification.
"""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlencode

from core.market_mechanics.binance_live_adapter import METRIC_ENDPOINTS, _period_end, normalize_bundle
from . import metrics_h1_activation as activation
from . import metrics_h1_runner as runner


TIMESTAMP_LABELS = {key: ('START' if key == 'taker' else 'END') for key in METRIC_ENDPOINTS}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _write(path, raw):
    activation._reject_aliases(path)
    with path.open('xb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON constant')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def _select(key, raw, slot, design):
    rows = _json(raw)
    if type(rows) is not list or not 1 <= len(rows) <= 5:
        raise ValueError('expected bounded nonempty endpoint rows')
    matched = []
    for row in rows:
        if type(row) is not dict or row.get('symbol') != design['instrument']:
            raise ValueError('endpoint instrument mismatch')
        if type(row.get('timestamp')) is not int or row['timestamp'] < 0:
            raise ValueError('invalid provider timestamp')
        end = _period_end(row['timestamp'], start_label=(TIMESTAMP_LABELS[key] == 'START'))
        if end == slot:
            matched.append(row)
    if len(matched) != 1:
        raise ValueError('exact source period missing or duplicated')
    selected = matched[0]
    for field in design['components'][key]['fields']:
        if type(selected.get(field)) not in (str, int, float):
            raise ValueError('invalid metric type')
    return selected


def capture_bundle(*, capture_directory, slot, expected_source_period_end,
                   target_at, deadline_at, attempt_started_at, clock, transport,
                   dataset_role, activation_id):
    """Capture five responses sequentially; raw partial evidence is never erased.

    available_at is sampled after durable raw/receipt persistence and independent
    reload authentication. available.json records that observation; it is not
    independently sufficient for admission without the runner's SUCCESS result.
    """
    design = activation._design()
    slot = runner._slot(slot)
    target, deadline, started = map(runner._utc, (target_at, deadline_at, attempt_started_at))
    if runner._slot(expected_source_period_end) != slot:
        raise ValueError('source period mismatch')
    if (target, deadline) != runner._bounds({'capture': design['capture']}, slot):
        raise ValueError('window differs from frozen contract')
    if not target <= started < deadline:
        raise ValueError('attempt outside capture window')
    if dataset_role not in {'PILOT', 'DISCOVERY', 'CONFIRMATION'} or not isinstance(activation_id, str) or not activation_id:
        raise ValueError('activation provenance required')
    previous = started

    def sample(*, request=False):
        nonlocal previous
        now = runner._utc(clock())
        if now < previous:
            raise ValueError('clock moved backwards')
        previous = now
        if now < target or now > deadline or (request and now == deadline):
            raise ValueError('capture outside frozen deadline')
        return now

    sample(request=True)
    root = Path(capture_directory)
    activation._reject_aliases(root)
    root.mkdir()  # Exclusive; no replacement/repair of previous captures.
    raw_dir = root/'raw'; raw_dir.mkdir()
    materials, selected, components = {}, {}, {}
    for key, endpoint in METRIC_ENDPOINTS.items():
        url = design['provider'] + endpoint
        # Five recent rows cover adjacent periods; exact-period matching is mandatory.
        params = {'symbol': design['instrument'], 'period': '5m', 'limit': 5}
        requested = sample(request=True)
        response = transport(url, params=params, timeout=min(8.0, (deadline-requested).total_seconds()), allow_redirects=False)
        if type(response) is not tuple or len(response) != 3:
            raise ValueError('transport response contract mismatch')
        status, final_url, raw = response
        if type(raw) is not bytes:
            raise ValueError('exact response bytes required')
        received = sample()
        _write(raw_dir/(key+'.json'), raw)
        # Requests preserves the encoded query in response.url. Authenticate it
        # exactly; never strip query parameters or accept a different endpoint.
        if type(status) is not int or not 200 <= status < 300 or final_url != url + '?' + urlencode(params):
            raise ValueError('HTTP status/source rejected; no fallback')
        selected[key] = _select(key, raw, slot, design)
        materials[endpoint] = base64.b64encode(raw).decode('ascii')
        components[key] = {'endpoint': endpoint, 'request_parameters': params,
                           'http_status': status, 'request_started_at': requested.isoformat(),
                           'received_at': received.isoformat(), 'raw_sha256': _sha(raw),
                           'raw_timestamp': selected[key]['timestamp'],
                           'timestamp_label': TIMESTAMP_LABELS[key],
                           'source_period_end': slot.isoformat()}
    normalized = normalize_bundle(selected)
    if runner._utc(normalized['timestamp']) != slot-timedelta(microseconds=1):
        raise ValueError('normalized source period mismatch')
    sample()
    receipt = {'schema': 'metrics-h1-capture-receipt-v1', 'contract': design['protocol_contract'],
               'provider': design['provider'], 'market': design['product'], 'instrument': design['instrument'],
               'dataset_role': dataset_role, 'activation_id': activation_id,
               'slot': slot.isoformat(), 'source_period_end': slot.isoformat(),
               'expected_source_period_end': slot.isoformat(),
               'source_period_start': (slot-timedelta(minutes=5)).isoformat(),
               'normalized_source_timestamp': normalized['timestamp'],
               'attempt_started_at': started.isoformat(), 'components': components,
               'normalized_metrics': normalized,
               'raw_bundle_sha256': _sha(activation._canonical(materials)),
               'selected_rows_sha256': _sha(activation._canonical(selected))}
    receipt['receipt_id'] = _sha(activation._canonical(receipt))
    # Re-read exact raw files before any complete-bundle receipt is published.
    for key in components:
        raw = (raw_dir/(key+'.json')).read_bytes()
        if _sha(raw) != components[key]['raw_sha256'] or _select(key, raw, slot, design) != selected[key]:
            raise ValueError('persisted raw evidence mismatch')
    sample()
    _write(root/'receipt.json', activation._canonical(receipt))
    if (root/'receipt.json').read_bytes() != activation._canonical(receipt):
        raise ValueError('receipt persistence mismatch')
    available = sample()
    marker = {'schema': 'metrics-h1-availability-v1', 'receipt_id': receipt['receipt_id'],
              'available_at': available.isoformat(), 'slot': slot.isoformat(), 'source_period_end': slot.isoformat()}
    _write(root/'available.pending', activation._canonical(marker))
    sample()
    # Non-overwriting publication; Windows is the qualified platform.
    if os.name != 'nt':
        raise OSError('Windows non-replacing publication required')
    os.rename(root/'available.pending', root/'available.json')
    sample()  # A late publication cannot return SUCCESS; artifacts remain forensic.
    return {'status': 'SUCCESS', 'slot': slot.isoformat(), 'source_period_end': slot.isoformat(),
            'capture_receipt_id': receipt['receipt_id'], 'raw_bundle_sha256': receipt['raw_bundle_sha256'],
            'available_at': available.isoformat()}


def run_once(state, *, repo_root, transport, clock=lambda: datetime.now(timezone.utc)):
    """One already-activated slot, injected transport only; no automatic state init."""
    config = runner.load_config(state, repo_root=repo_root)
    observed = runner._utc(clock())
    slot = runner.select_slot(state, observed, repo_root=repo_root)
    target, deadline = runner._bounds(config, slot)
    if not target <= observed < deadline:
        return {'status': 'NOT_DUE', 'slot': slot.isoformat(), 'observed_at': observed.isoformat()}
    previous = observed

    def guarded_clock():
        nonlocal previous
        now = runner._utc(clock())
        if now < previous:
            raise ValueError('clock moved backwards')
        previous = now
        return now

    def capture(**kwargs):
        return capture_bundle(**kwargs, transport=transport, dataset_role=config['dataset_role'], activation_id=config['activation_id'])

    return runner.attempt_slot(state, slot, capture, repo_root=repo_root, clock=guarded_clock)
