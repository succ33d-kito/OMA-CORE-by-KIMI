"""Explicit curator operator boundary; no capture, classification or outcome API."""
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import json
import os
from .real_event_receipt import RealEventStore
from .event_direction_v1 import EventDirectionAuthority, ClassAssertion, EventClass, Direction, RULE_HASH
from .experiment51_p0 import prepare, bind_population, P0_HASH
from .nuisance_pilot_contracts import DatasetRole, digest, closed
from .policy_kernel import SharedControls, PolicyKernel

SCHEMA = 'event-direction-operator-v1'


def activate(root, event_journal, *, role):
    closed(role, DatasetRole)
    root, source = Path(root).resolve(), Path(event_journal).resolve()
    if source == root / 'authority.sqlite':
        raise ValueError('separate source journal required')
    rows = RealEventStore(source, read_only=True)._rows() if source.exists() else []
    # Preserve existing paths, including interrupted activation; never repair.
    root.mkdir(parents=True, exist_ok=False)
    authority = EventDirectionAuthority.activate(root / 'authority.sqlite', role=role)
    config = dict(schema=SCHEMA, event_journal=str(source), source_prefix_count=len(rows),
                  source_prefix_hash=digest(rows), role=role.value, rule_hash=RULE_HASH)
    authority._journal._append('operator_binding', config, lambda rows, at: None)
    return inspect(root, role=role)


def _open(root, role, *, writable=False):
    closed(role, DatasetRole)
    root = Path(root).resolve()
    authority = EventDirectionAuthority(root / 'authority.sqlite', read_only=not writable)
    rows = authority._journal._rows()
    bindings = [r for r in rows if r['kind'] == 'operator_binding']
    if len(bindings) != 1 or len(rows) < 2 or rows[1] != bindings[0]:
        raise ValueError('missing/conflicting operator binding; no repair')
    binding = bindings[0]; config = binding['data']
    if (config['schema'] != SCHEMA or config['rule_hash'] != RULE_HASH
            or config['role'] != role.value or authority.role is not role):
        raise ValueError('activation role/rule/schema mismatch')
    activated = datetime.fromisoformat(binding['at'])
    if activated < datetime.fromisoformat(rows[0]['at']):
        raise ValueError('activation chronology invalid')
    source = Path(config['event_journal'])
    if source.resolve() == root / 'authority.sqlite':
        raise ValueError('source and authority must differ')
    store = RealEventStore(source, read_only=True) if source.exists() else None
    source_rows = store._rows() if store else []
    count = config['source_prefix_count']
    if type(count) is not int or count < 0 or len(source_rows) < count or digest(source_rows[:count]) != config['source_prefix_hash']:
        raise ValueError('source journal binding mismatch')
    return root, authority, store, rows, binding


def _record(authority, store, receipt_id, activated):
    if store is None:
        raise ValueError('source journal not yet present')
    receipt = store.receipt(receipt_id)
    if receipt.received_at <= activated:
        raise ValueError('receipt precedes completed operator activation')
    return authority.verify(store, receipt_id)


def attest(root, receipt_id, assertion, *, role):
    _, authority, store, _, binding = _open(root, role, writable=True)
    if store is None:
        raise ValueError('source journal not yet present')
    if store.receipt(receipt_id).received_at <= datetime.fromisoformat(binding['at']):
        raise ValueError('receipt precedes completed operator activation')
    return authority.attest(store, receipt_id, assertion)


def controls_from_json(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    data['risk_budget_quote'] = Decimal(str(data['risk_budget_quote']))
    controls = SharedControls(**data)
    if controls.policy_contract_hash != P0_HASH or controls.outcome_horizon_seconds != 14400:
        raise ValueError('frozen P0/4H controls required')
    return controls


def _exclusive(path, text):
    with path.open('x', encoding='utf-8', newline='') as stream:
        stream.write(text); stream.flush(); os.fsync(stream.fileno())


def bind(root, controls, *, role, price_ledger=None):
    root, authority, store, rows, binding = _open(root, role, writable=True)
    if store is None:
        raise ValueError('source journal not yet present')
    if (root / 'population').exists() or any(r['kind'] == 'operator_population' for r in rows):
        raise ValueError('population already attempted; inspect, never overwrite')
    activated = datetime.fromisoformat(binding['at'])
    for op in store.population():
        candidates = [r for r in rows if r['kind'] == 'direction' and r['data']['event_id'] == op.event_id]
        if len(candidates) != 1:
            raise ValueError('missing/ambiguous direction; no population filtering')
        _record(authority, store, candidates[0]['data']['receipt_id'], activated)
    manifest, official = bind_population(authority, store, controls, price_ledger=price_ledger,
                                         directory=root / 'population')
    payload = manifest.to_json()
    _exclusive(root / 'population' / 'manifest.json', payload)
    data = dict(manifest=payload, binding=official.to_json(), scope_id=official.scope_id,
                count=len(manifest.records), manifest_id=manifest.manifest_id)
    authority._journal._append('operator_population', data, lambda rows, at: None)
    return official


def inspect(root, *, role, controls=None, price_ledger=None):
    root, authority, store, rows, binding = _open(root, role)
    activated = datetime.fromisoformat(binding['at'])
    counts = {d.value: 0 for d in Direction}; reasons = Counter(); post = 0; eligible = 0
    latest = None
    if controls is not None and (controls.policy_contract_hash != P0_HASH or controls.outcome_horizon_seconds != 14400):
        raise ValueError('frozen P0/4H controls required')
    if store is not None:
        for row in store._rows():
            if row['kind'] != 'receipt':
                continue
            receipt = store.receipt(row['data']['receipt_id'])
            if receipt.received_at <= activated:
                reasons['PRE_ACTIVATION'] += 1
                continue
            post += 1
            if receipt.role is not role:
                reasons['WRONG_ROLE'] += 1
                continue
            try:
                record = _record(authority, store, receipt.receipt_id, activated)
                counts[record.direction.value] += 1
            except (ValueError, StopIteration) as error:
                reasons['DIRECTION_INVALID: ' + str(error)] += 1
                continue
            if controls is None:
                continue
            try:
                op, _, _ = prepare(authority, store, receipt.receipt_id, price_ledger=price_ledger)
                if PolicyKernel().form(op, controls)[0].information_set.causal_eligible:
                    eligible += 1
                    latest = max(latest, op.decision_at) if latest else op.decision_at
                else:
                    reasons['P0_INPUT_INELIGIBLE'] += 1
            except (ValueError, StopIteration) as error:
                reasons['P0_INVALID: ' + str(error)] += 1
    bound = [r for r in rows if r['kind'] == 'operator_population']
    if len(bound) > 1:
        raise ValueError('conflicting population publications')
    population_count = 0
    population_state = 'NOT_BOUND'
    if bound:
        data = bound[0]['data']; directory = root / 'population'
        if ((directory / 'manifest.json').read_text(encoding='utf-8') != data['manifest']
                or (directory / (data['scope_id'] + '.json')).read_text(encoding='utf-8') != data['binding'] + '\n'
                or json.loads(data['binding'])['manifest_content_digest'] != digest(data['manifest'])):
            raise ValueError('bound population integrity failure')
        population_count = data['count']; population_state = 'BOUND'
    elif (root / 'population').exists():
        population_state = 'INCOMPLETE_PUBLICATION'
        reasons[population_state] += 1
    return dict(schema=SCHEMA, authority_status='ACTIVE', activation_id=digest(binding),
                authority_id=authority.authority_id, activated_at=binding['at'], rule_hash=RULE_HASH,
                dataset_role=role.value, event_journal=binding['data']['event_journal'],
                source_journal_present=store is not None, post_activation_event_receipts=post,
                direction_attestations=sum(counts.values()), directions=counts,
                bound_event_population=population_count, population_state=population_state,
                p0_eligible_opportunities=eligible if controls is not None or post == 0 else None,
                p0_assessment='ASSESSED' if controls is not None or post == 0 else 'CONTROLS_REQUIRED',
                ineligible_reasons=dict(sorted(reasons.items())), latest_eligible_decision_at=latest.isoformat() if latest else None)
