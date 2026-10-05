"""Prospective continuity only. No outcomes, regimes or hypothesis execution."""
import json
import hashlib
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .prospective_receipts import (observation_snapshot, observation_hash, _utc,
                                  snapshot_causally_available)

CONTRACT = 'binance-usdm-h1-rest-v1'
HOUR = timedelta(hours=1)


def hour(t):
    return _utc(t).replace(minute=0, second=0, microsecond=0)


def next_capture_at(now, delay=5):
    if not 0 <= delay <= 60:
        raise ValueError('safety delay must be between 0 and 60 seconds')
    now = _utc(now)
    candidate = hour(now) + timedelta(seconds=delay)
    return candidate if candidate > now else candidate + HOUR


def exclusive_json(path, body):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(body, f, sort_keys=True, indent=2, allow_nan=False)
        f.flush()
        import os
        os.fsync(f.fileno())


def verify_anchors(state, observations, prefixes):
    last = None
    for path in sorted((Path(state)/'anchors').glob('*.json')):
        a = json.loads(path.read_text(encoding='utf-8'))
        digest = a.pop('anchor_hash')
        n = a['observation_count']
        if (observation_hash(a) != digest or n < 1 or n > len(prefixes)
                or prefixes[n-1] != a['ledger_head']
                or list(observations)[n-1] != a['last_observation_id']
                or a['contract'] != CONTRACT):
            raise ValueError('external anchor incompatible with ledger prefix')
        last = dict(a, anchor_hash=digest)
    return last


def anchor(ledger, state, now):
    obs, prefixes = observation_snapshot(ledger)
    previous = verify_anchors(state, obs, prefixes)
    if not prefixes or (previous and previous['ledger_head'] == prefixes[-1]):
        return previous
    last = list(obs.values())[-1]
    a = dict(schema='price-ledger-anchor-v1', timestamp=_utc(now).isoformat(),
             ledger_head=prefixes[-1], observation_count=len(obs),
             last_event_time=last['event_time'], last_observation_id=last['id'], contract=CONTRACT)
    a['anchor_hash'] = observation_hash(a)
    path = Path(state)/'anchors'/f'{len(obs):012d}-{prefixes[-1]}.json'
    exclusive_json(path, a)
    return a


def status(ledger, state, reference, delay=5, *, read_only=False):
    reference = _utc(reference)
    result = dict(schema='price-continuity-v1', reference_at=reference.isoformat(),
        total_receipts=0, valid_price_receipts=0, current_streak=0, longest_streak=0,
        first_valid_event_time=None, last_valid_event_time=None, last_receipt_at=None,
        gaps=[], conflicts=0, invalid=[], duplicates=[], out_of_order=[],
        bars_to_81=81, regime_input_ready=False, ledger_integrity='FAIL',
        last_external_anchor=None, certificate=None)
    try:
        obs, prefixes = observation_snapshot(ledger,read_only=True) if read_only else observation_snapshot(ledger)
        result['total_receipts'] = len(obs)
        result['last_external_anchor'] = verify_anchors(state, obs, prefixes)
        result['ledger_head'] = prefixes[-1] if prefixes else '0'*64
        result['ledger_integrity'] = 'PASS'
        for p in (Path(state)/'attempts').glob('*.json'):
            attempt = json.loads(p.read_text(encoding='utf-8'))
            if attempt.get('status') == 'CONFLICT':
                result['conflicts'] += 1
        events = []
        seen_hours = Counter()
        last_event = None
        for x in obs.values():
            try:
                t = _utc(x['event_time'])
                if x['instrument'] == 'BTCUSDT' and x['feature'] == 'Price/OHLCV':
                    seen_hours[t] += 1
                if last_event is not None and t < last_event:
                    result['out_of_order'].append(x['id'])
                last_event = t
                p = x['provenance']
                # Only the latest closed hour at actual request time can count.
                # This prevents a later historical request from repairing a gap.
                eligible = (x['instrument'] == 'BTCUSDT' and x['feature'] == 'Price/OHLCV'
                    and not x['derived'] and snapshot_causally_available(obs, x['id'], reference)
                    and t == hour(p['klines_requested_at'])
                    and t == hour(x['received_at'])
                    and t == hour(datetime.fromtimestamp(json.loads(p['raw_server_time'])['serverTime']/1000, timezone.utc)))
                if not eligible:
                    raise ValueError('causal gate, type or contemporaneous-capture check failed')
                events.append((t, x))
            except (ValueError, KeyError, TypeError, OverflowError) as exc:
                result['invalid'].append(dict(id=x.get('id'), reason=str(exc)))
        counts = Counter(t for t, x in events)
        result['duplicates'] = [t.isoformat() for t, n in seen_hours.items() if n > 1]
        events = sorted((t, x) for t, x in events if counts[t] == 1 and seen_hours[t] == 1)
        result['valid_price_receipts'] = len(events)
        streak, window, previous = 0, [], None
        for t, x in events:
            if previous is not None and t != previous + HOUR:
                result['gaps'].append(dict(first=(previous+HOUR).isoformat(), last=(t-HOUR).isoformat(), hours=int((t-previous)/HOUR)-1))
                streak, window = 0, []
            streak += 1
            window.append(x)
            result['longest_streak'] = max(result['longest_streak'], streak)
            previous = t
        if events:
            result.update(first_valid_event_time=events[0][0].isoformat(),
                          last_valid_event_time=events[-1][0].isoformat(),
                          last_receipt_at=events[-1][1]['received_at'])
            due = hour(reference-timedelta(seconds=delay))
            if previous < due:
                result['gaps'].append(dict(first=(previous+HOUR).isoformat(), last=due.isoformat(), hours=int((due-previous)/HOUR)))
                streak = 0
        result['current_streak'] = streak
        result['bars_to_81'] = max(0, 81-streak)
        ready = streak >= 81 and not result['conflicts'] and not result['out_of_order'] and not result['duplicates']
        result['regime_input_ready'] = ready
        if ready:
            selected = window[-81:]
            result['certificate'] = dict(schema='price-81h-certificate-v1', instrument='BTCUSDT',
                feature='Price/OHLCV', first_event_time=selected[0]['event_time'],
                last_event_time=selected[-1]['event_time'], number_of_bars=81,
                receipt_ids=[x['id'] for x in selected], ledger_head=result['ledger_head'],
                ledger_observation_count=len(obs), certified_set_hash=observation_hash(selected),
                certified_at=reference.isoformat(), contract=CONTRACT,
                causal_gate_code_hash=hashlib.sha256(Path(__file__).with_name('prospective_receipts.py').read_bytes()).hexdigest(),
                continuity_code_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                gaps=0, conflicts=0, historical_backfill=False)
    except Exception as exc:
        result.update(ledger_integrity='FAIL', integrity_error=str(exc), regime_input_ready=False, certificate=None)
    return result
