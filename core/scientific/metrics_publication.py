"""Post-commit Metrics authority. No recovery or historical receipt synthesis.

Hashes attest integrity within the trusted local admission boundary; they are not
signatures against an administrator capable of rewriting the database and code.
"""
from datetime import datetime, timezone
import json
from copy import deepcopy
from pathlib import Path
import sqlite3
from .prospective_receipts import canonical_observation, observation_hash, observation_snapshot as _snapshot, _utc

SCHEMA = 'metrics-durable-publication-v1'
TABLE = 'metrics_publications_v1'


def _now():
    return datetime.now(timezone.utc)


class _PublishedRows(dict):
    __slots__ = ('_receipts', '_prefixes')

    def __init__(self, rows, receipts=(), prefixes=()):
        super().__init__(rows)
        object.__setattr__(self, '_receipts', tuple(receipts))
        object.__setattr__(self, '_prefixes', tuple(prefixes))

    def __setattr__(self, name, value):
        raise AttributeError('publication authority is immutable')

    def __deepcopy__(self, memo):
        return _PublishedRows(deepcopy(dict(self), memo), self._receipts, self._prefixes)


def _binding(rows, bundle_id):
    from .metrics_observation_admission import ADMISSION_CONTRACT, EXPECTED_FEATURES
    members = sorted((r for r in rows.values() if r.get('provenance', {}).get('bundle_id') == bundle_id), key=lambda r:r['id'])
    if len(members) != 6 or {r['feature'] for r in members} != EXPECTED_FEATURES:
        raise ValueError('publication requires exactly six Metrics observations')
    roles = {r['provenance']['dataset_role'] for r in members}
    if len(roles) != 1 or not roles <= {'PILOT', 'DISCOVERY', 'CONFIRMATION'}:
        raise ValueError('publication role conflict')
    if any(r['provenance']['contract'] != ADMISSION_CONTRACT for r in members):
        raise ValueError('publication contract mismatch')
    return dict(schema=SCHEMA, bundle_id=bundle_id, observation_ids=[r['id'] for r in members],
        dataset_role=next(iter(roles)), admission_contract=ADMISSION_CONTRACT,
        observations_commitment=observation_hash(members))


def _validate(receipt, rows, prefixes):
    expected = _binding(rows, receipt['bundle_id'])
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError('publication binding mismatch')
    if set(receipt) != set(expected) | {'ledger_commitment', 'published_at', 'publication_id'}:
        raise ValueError('publication schema mismatch')
    # The committed prefix must include all six exact observations.
    anchor = receipt['ledger_commitment']
    if anchor not in prefixes:
        raise ValueError('publication ledger commitment mismatch')
    ids = set(receipt['observation_ids'])
    if not ids <= set(list(rows)[:prefixes.index(anchor)+1]):
        raise ValueError('publication precedes complete bundle')
    if receipt['publication_id'] != observation_hash({k:v for k,v in receipt.items() if k != 'publication_id'}):
        raise ValueError('publication hash mismatch')
    if _utc(receipt['published_at']) < max(_utc(rows[i]['available_at']) for i in ids):
        raise ValueError('publication clock precedes row admission')
    return receipt


def observation_snapshot(path, *, read_only=True):
    # Read-only by default, including missing receipt tables. Never repair.
    rows, prefixes = _snapshot(path, read_only=read_only)
    with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True) as con:
        exists = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone()
        raw = con.execute(f'SELECT bundle_id, body FROM {TABLE} ORDER BY bundle_id').fetchall() if exists else []
    receipts = []
    for bundle, body in raw:
        receipt = json.loads(body)
        if receipt['bundle_id'] != bundle or canonical_observation(receipt) != body:
            raise ValueError('corrupt publication record')
        _validate(receipt, rows, prefixes)
        receipts.append(body)
    return _PublishedRows(rows, receipts, prefixes), prefixes


def publication_for(rows, bundle_id):
    if not isinstance(rows, _PublishedRows):
        raise ValueError('physical rows are not publication authority')
    matches = [json.loads(raw) for raw in rows._receipts if json.loads(raw)['bundle_id'] == bundle_id]
    if len(matches) != 1:
        raise ValueError('missing valid publication receipt; recovery prohibited')
    receipt = matches[0]
    # Recheck bindings against mutable row aliases on every causal consumption.
    return _validate(receipt, rows, rows._prefixes)


def _publish_committed(path, bundle_id):
    """Internal continuation of a newly successful six-row commit only.

    No timestamp argument; never called for existing/unpublished admissions.
    """
    rows, prefixes = _snapshot(path, read_only=True)
    body = _binding(rows, bundle_id)
    body.update(ledger_commitment=prefixes[-1], published_at=_utc(_now()).isoformat())
    body['publication_id'] = observation_hash(body)
    _validate(body, rows, prefixes)
    with sqlite3.connect(path) as con:
        con.execute('PRAGMA synchronous=FULL')
        con.execute(f'CREATE TABLE IF NOT EXISTS {TABLE} (bundle_id TEXT PRIMARY KEY, body TEXT NOT NULL)')
        for op in ('UPDATE', 'DELETE'):
            con.execute(f"CREATE TRIGGER IF NOT EXISTS {TABLE}_no_{op.lower()} BEFORE {op} ON {TABLE} BEGIN SELECT RAISE(ABORT, 'append-only publication'); END")
        con.execute('BEGIN IMMEDIATE')
        old = con.execute(f'SELECT body FROM {TABLE} WHERE bundle_id=?', (bundle_id,)).fetchone()
        raw = canonical_observation(body)
        if old is not None:
            if old[0] != raw:
                raise ValueError('conflicting publication; no overwrite')
        else:
            con.execute(f'INSERT INTO {TABLE} VALUES (?,?)', (bundle_id, raw))
        con.commit()
    return body
