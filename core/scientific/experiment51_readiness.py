"""Read-only coverage of closed H1 slots. Never grants experiment authorization.

Provider payloads are read only by existing semantic/integrity validators; this
module projects identities/times/status, never prices, returns or outcomes.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
import sqlite3
from pathlib import Path

HOUR = timedelta(hours=1)
DECISION_DELAY = timedelta(minutes=5)


def utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('aware timestamp required')
    return value.astimezone(timezone.utc)


def slots(start, end):
    start, end = utc(start), utc(end)
    if any(t != t.replace(minute=0, second=0, microsecond=0) for t in (start, end)):
        raise ValueError('exact H1 boundaries required')
    while start <= end:
        yield start
        start += HOUR


def summarize(records):
    """Closed metadata only; duplicates fail, absent H1 slots break the suffix."""
    rows = sorted(records, key=lambda r: utc(r['slot']))
    if len({utc(r['slot']) for r in rows}) != len(rows):
        raise ValueError('duplicate slot')
    valid, current, longest, previous = [], 0, 0, None
    for r in rows:
        t = utc(r['slot'])
        if t != t.replace(minute=0, second=0, microsecond=0):
            raise ValueError('exact H1 boundary required')
        if previous is not None and t != previous + HOUR:
            current = 0
        current = current + 1 if r['status'] == 'VALID' else 0
        longest = max(longest, current)
        previous = t
        if r['status'] == 'VALID':
            valid.append(r['slot'])
    present = {r['slot'] for r in rows if r['status'] == 'VALID'}
    gaps = [t.isoformat() for t in slots(rows[0]['slot'], rows[-1]['slot'])
            if t.isoformat() not in present] if rows else []
    return dict(total_valid_h1=len(valid), consecutive_valid_h1=current,
                longest_streak=longest, first_valid_slot=valid[0] if valid else None,
                last_valid_slot=valid[-1] if valid else None, gaps=gaps,
                counts=dict(sorted(Counter(r['status'] for r in rows).items())), records=rows)


def intersection(streams):
    """Only exact same closed slot and role; no latest-value substitution."""
    indexes = {name: {r['slot']: r for r in rows} for name, rows in streams.items()}
    for rows in streams.values():
        summarize(rows)  # duplicate/chronology check before any projection
    domain = sorted({slot for rows in indexes.values() for slot in rows})
    records = []
    for slot in domain:
        reasons = []
        for name, rows in sorted(indexes.items()):
            r = rows.get(slot)
            if r is None:
                reasons.append('MISSING_' + name.upper())
            elif r['status'] != 'VALID':
                reasons.append(name.upper() + ':' + r['status'])
            elif r.get('role') != 'PILOT':
                reasons.append(name.upper() + ':ROLE_MISMATCH')
            elif r.get('available_at') is None or not utc(r['available_at']) <= utc(slot) + DECISION_DELAY:
                reasons.append(name.upper() + ':CAUSAL_AVAILABILITY_FAILED')
        records.append(dict(slot=slot, status='EXCLUDED' if reasons else 'VALID', reasons=reasons))
    result = summarize(records)
    result['exclusion_counts'] = dict(sorted(Counter(x for r in records for x in r['reasons']).items()))
    return result


def _row(slot, status, available=None, role='PILOT', **extra):
    if status == 'SUCCESS':
        status = 'VALID'
    if status == 'VALID' and (available is None or utc(available) > slot + DECISION_DELAY):
        status = 'CAUSAL_AVAILABILITY_FAILED'
    if status == 'VALID' and role != 'PILOT':
        status = 'ROLE_MISMATCH'
    return dict(slot=slot.isoformat(), status=status, available_at=available, role=role, **extra)


def _price(state, repo, now, end):
    from . import price_role_h1_runner as p
    from .role_price_window import _build
    root, config = p.validate_state(state, repo_root=repo)
    known = p._rows(root)  # observations_v2, SQLite mode=ro, authenticates hash chain
    report = p.status(state, repo_root=repo, clock=lambda: now)
    pairs = {r['slot']: r for r in report['verified_pairs']}
    start = utc(config['not_before']).replace(minute=0, second=0, microsecond=0)
    if start < utc(config['not_before']):
        start += HOUR
    records, eligible_ids, regime_slots = [], [], []
    for slot in slots(start, end):
        pair = pairs.get(slot.isoformat())
        directory = p._directory(root, slot)
        status, available = 'MISSING_PRICE', None
        for terminal in p.TERMINAL:
            if (directory / (terminal + '.json')).exists():
                status = terminal
                break
        else:
            if pair and (directory / 'SUCCESS.json').exists():
                success = p._read(directory / 'SUCCESS.json')
                if (success.get('schema') != p.SCHEMA or success.get('status') != 'SUCCESS'
                        or success.get('raw_id') != pair['raw_id'] or success.get('attestation_id') != pair['attestation_id']
                        or success.get('activation_id') != config['activation_id'] or success.get('slot') != slot.isoformat()
                        or success.get('dataset_role') != 'PILOT' or utc(success['at']) > now
                        or utc(success['at']) < utc(known[pair['attestation_id']]['available_at'])):
                    status = 'INVALID'
                else:
                    available = max(known[pair[k]]['available_at'] for k in ('raw_id', 'attestation_id'))
                    status = 'VALID'
            elif p._prices(known, slot):
                status = 'PRICE_NOT_ROLE_AUTHENTICATED'
        record = _row(slot, status, available, config['dataset_role'])
        records.append(record)
        eligible_ids = eligible_ids + [pair['raw_id']] if record['status'] == 'VALID' else []
        if len(eligible_ids) >= 81:
            try:
                _build(known, eligible_ids[-81:], 'PILOT', slot + DECISION_DELAY)
                regime_slots.append(slot.isoformat())
            except (ValueError, KeyError, TypeError, OverflowError):
                pass  # no certificate => no readiness
    return {**summarize(records), 'activation_id': config['activation_id'], 'dataset_role': config['dataset_role'],
            'ledger_integrity': report['ledger_integrity'], 'regime_input_slots': regime_slots,
            'network_attempts': report['runtime_network_attempts'],
            'numbered_retries': sum(r['status'] == 'STARTED' and r['attempt_index'] > 1 for r in report['network_attempt_records']),
            'heartbeat_is_evidence': False, 'runtime_liveness': 'UNVERIFIED'}


def _metrics(state, repo, now, end):
    from . import metrics_h1_runner as runner, metrics_continuity as verifier
    config = runner.load_config(state, repo_root=repo)
    records = []
    for slot in slots(config['activation_slot'], end):
        result = verifier.verify_slot(state, slot, repo_root=repo, now=now)
        available = None
        if result['status'] == 'SUCCESS':
            available = verifier._read(runner._path(state, slot) / 'capture' / 'available.json')['available_at']
        records.append(_row(slot, result['status'], available, config['dataset_role']))
    return {**summarize(records), 'activation_id': config['activation_id'], 'dataset_role': config['dataset_role'],
            'atomic_bundle': 'FIVE_RESPONSES_SIX_VALUES_VERIFIED',
            'admission': 'NOT_VERIFIED_BY_CAPTURE_COVERAGE'}


def _funding(state, repo, now, end):
    from . import funding_h1_runner as runner, funding_continuity as verifier
    from .premium_index_capture import load_premium
    config = runner.load_config(state)
    report = verifier.status(state, config['activation_slot'], now)
    records = []
    for r in report['records']:
        slot = utc(r['slot'])
        if slot > end:
            continue
        available = None
        status = r['status']
        if status == 'SUCCESS':
            path = verifier._attempt_path(state, slot)
            available = load_premium(path / 'capture').receipts[0].available_at.isoformat()
            completed = utc(verifier._read_json(path / 'result.json')['completed_at'])
            if completed > now:
                status = 'CAUSAL_AVAILABILITY_FAILED'
        if report['structural_invalid']:
            status = 'INVALID'
        records.append(_row(slot, status, available, verifier.ROLE))
    return {**summarize(records), 'role_authority': 'funding_continuity.ROLE=PILOT; authenticated ExecutionReceipt scope',
            'semantics': 'PUBLISHED_RATE_NOT_REALIZED_PAYMENT', 'integrity': report['integrity'],
            'admission': 'NOT_VERIFIED_BY_CAPTURE_COVERAGE'}


def check_readiness(*, price_state, metrics_state, funding_state, repo_root, checked_at):
    now = utc(checked_at)
    # Only slots whose Experiment 51 decision cutoff has elapsed. Pending slots
    # are never declared missed. Collector-specific windows are still verified.
    end = (now - DECISION_DELAY).replace(minute=0, second=0, microsecond=0)
    output = dict(schema='experiment51-readiness-v1', checked_at=now.isoformat(), last_closed_decision_slot=end.isoformat())
    for name, state, reader in (('price', price_state, _price), ('metrics', metrics_state, _metrics), ('funding', funding_state, _funding)):
        try:
            output[name] = reader(Path(state), Path(repo_root), now, end)
        except (OSError, sqlite3.Error, ValueError, KeyError, TypeError, OverflowError) as exc:
            output[name] = {**summarize([]), 'verification': 'FAILED_CLOSED', 'error_type': type(exc).__name__}
    for name, members in (('price_metrics', ('price','metrics')), ('price_funding', ('price','funding')), ('price_metrics_funding', ('price','metrics','funding'))):
        output[name] = intersection({m: output[m]['records'] for m in members})
    regime_slots = set(output['price'].get('regime_input_slots', []))
    common = output['price_metrics']
    derived = [dict(r, status='VALID' if r['status'] == 'VALID' and r['slot'] in regime_slots else 'MISSING_REQUIRED_INPUT') for r in common['records']]
    output['regime_metrics_capture_support'] = summarize(derived)
    output['required_inputs'] = dict(regime='81 contiguous authenticated Price H1; certificate reconstructed',
        mechanics='Price plus authenticated atomic six-value Metrics subset; causal admission and derived availability separately required',
        funding='Coverage only, not required in the frozen primary comparison')
    output['regime_input_ready'] = end.isoformat() in regime_slots
    output['mechanics_capture_input_ready'] = bool(common['records'] and common['records'][-1]['slot'] == end.isoformat() and common['records'][-1]['status'] == 'VALID')
    output['mechanics_input_ready'] = False
    output['experiment_51_ready'] = False
    output['blockers'] = ['ADMITTED_MECHANICS_SNAPSHOT_NOT_VERIFIED', 'FROZEN_EVENT_POPULATION_NOT_BOUND',
                          'REAL_POLICY_VALUE_RULE_NOT_QUALIFIED', 'DISCOVERY_CONFIRMATION_ACTIVATIONS_NOT_BOUND']
    output['unknown_mechanics_dimensions'] = ['open_interest_change','aggressor_flow','aggressor_imbalance',
        'trade_intensity','average_trade_size','resting_liquidity','absorption','participant_identity',
        'participant_intent','capital_flow','realized_funding_payment']
    output['no_outcome_analysis'] = True
    return output
