"""Qualification of the Experiment 51 derived-snapshot admission binding.

Synthetic fixtures are TEST evidence: passing these tests does NOT mean live
derived snapshots exist. No outcome, label, phase activation or Experiment 51
evaluation is touched here.
"""
import ast
import json
import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_role_price_window import window
from tests.test_causal_latent_context import admit_metrics
from tests.test_metrics_continuity import state, S

from core.scientific import causal_mechanics
from core.scientific import derived_snapshot_admission as dsa
from core.scientific.causal_regime import append_causal_regime
from core.scientific.experiment51_derived import actions
from core.scientific.decision_rule import IntentAction
from core.scientific.prospective_receipts import append_observation, observation_snapshot
from core.scientific.role_price_window import certify_role_price_window

ROOT = Path(__file__).resolve().parents[1]
LIVE_METRICS_DB = Path(__import__('os').environ.get('OMA_DATA_ROOT', '<OMA_DATA_ROOT>')) / 'prospective/metrics-admission-v1/observations.sqlite'

DERIVED_OK = ('METRICS_HISTORY_NOT_READY', 'BUNDLE_NOT_ATOMIC')


def regime_cert(ledger, ids, role, cutoff):
    return certify_role_price_window(ledger, receipt_ids=ids, dataset_role=role, cutoff=cutoff)


# --- Regime: history, gaps, authority, provenance, availability -------------
def test_regime_computes_with_exactly_81_contiguous_slots(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    assert outcome.admitted and outcome.reason == 'OK' and outcome.observation_id


def test_regime_cannot_derive_with_less_than_81_slots(window):
    ledger, ids, cutoff, _ = window
    certificate = {**regime_cert(ledger, ids, 'PILOT', cutoff), 'receipt_ids': list(ids[:80])}
    outcome = dsa.admit_regime(ledger, certificate, dataset_role='PILOT',
                               clock=lambda: cutoff + timedelta(seconds=1))
    assert not outcome.admitted and outcome.reason == 'PRICE_HISTORY_NOT_READY'


def test_regime_rejects_a_gap_inside_the_window(window):
    ledger, ids, cutoff, _ = window
    gapped = list(ids[:40]) + list(ids[41:]) + [ids[40]]
    certificate = {**regime_cert(ledger, ids, 'PILOT', cutoff), 'receipt_ids': gapped}
    outcome = dsa.admit_regime(ledger, certificate, dataset_role='PILOT',
                               clock=lambda: cutoff + timedelta(seconds=1))
    assert not outcome.admitted and outcome.reason == 'PRICE_HISTORY_NOT_READY'


def test_regime_rejects_unauthenticated_price_role(window):
    ledger, ids, cutoff, _ = window
    certificate = {**regime_cert(ledger, ids, 'PILOT', cutoff), 'dataset_role': 'DISCOVERY'}
    outcome = dsa.admit_regime(ledger, certificate, dataset_role='DISCOVERY',
                               clock=lambda: cutoff + timedelta(seconds=1))
    assert not outcome.admitted and outcome.reason in ('AUTHORITY_MISMATCH', 'RAW_INPUT_NOT_ADMITTED')


def test_regime_snapshot_references_the_exact_source_window(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    row = known[outcome.observation_id]
    certificate = row['provenance']['certificate']
    assert certificate['receipt_ids'] == list(ids)
    assert certificate['number_of_bars'] == 81 and certificate['gaps'] == 0
    assert len(row['dependencies']) == 162
    assert set(certificate['receipt_ids'] + certificate['attestation_ids']) == set(row['dependencies'])


def test_regime_availability_cannot_precede_any_raw_input(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    row = known[outcome.observation_id]
    from core.scientific.regime_observation import _utc
    assert _utc(row['available_at']) >= max(_utc(known[i]['available_at']) for i in row['dependencies'])


def test_regime_availability_cannot_precede_computation(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    from core.scientific.regime_observation import _utc
    row = known[outcome.observation_id]
    assert _utc(row['available_at']) >= _utc(row['computed_at'])


def test_regime_availability_cannot_precede_durable_publication(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    from core.scientific.regime_observation import _utc
    row = known[outcome.observation_id]
    assert _utc(row['recorded_at']) <= _utc(row['available_at'])
    assert _utc(row['received_at']) <= _utc(row['available_at'])
    assert _utc(row['computed_at']) >= _utc(row['provenance']['certificate']['cutoff'])


# --- Mechanics (Taker only) -------------------------------------------------
def mechanics_ledger(state, ledger):
    admit_metrics(state, ledger)
    return ledger, S + timedelta(minutes=5)


def test_mechanics_cannot_derive_without_required_metrics_history(window):
    ledger, ids, cutoff, _ = window          # price-only ledger: no metrics bundle
    outcome = dsa.admit_taker_mechanics(ledger, dataset_role='PILOT', cutoff=cutoff,
                                        clock=lambda: cutoff + timedelta(seconds=1))
    assert not outcome.admitted and outcome.reason in DERIVED_OK


def test_mechanics_uses_only_the_frozen_taker_input(state, tmp_path):
    ledger, cutoff = mechanics_ledger(state, tmp_path / 'm.db')
    outcome = dsa.admit_taker_mechanics(ledger, dataset_role='PILOT', cutoff=cutoff,
                                        clock=lambda: cutoff + timedelta(seconds=1))
    assert outcome.admitted, outcome
    known, _ = observation_snapshot(ledger, read_only=True)
    row = known[outcome.observation_id]
    assert dsa.EXP51_MECHANICS_INPUTS == (dsa.TAKER_FEATURE,)
    assert set(k for k in row['payload']['raw_values'] if k.startswith('MarketMetrics/')) == set(dsa.BUNDLE_FEATURES)
    assert dsa.TAKER_FEATURE in row['payload']['raw_values']


def test_mechanics_rejects_a_partial_six_value_bundle(state, tmp_path, monkeypatch):
    ledger, cutoff = mechanics_ledger(state, tmp_path / 'partial.db')
    real = causal_mechanics.build_causal_mechanics

    def partial(*args, **kwargs):
        view = dict(real(*args, **kwargs))
        dropped = dsa.TAKER_FEATURE
        view['raw_values'] = {k: v for k, v in view['raw_values'].items() if k != dropped}
        return view

    monkeypatch.setattr(causal_mechanics, 'build_causal_mechanics', partial)
    outcome = dsa.admit_taker_mechanics(ledger, dataset_role='PILOT', cutoff=cutoff,
                                        clock=lambda: cutoff + timedelta(seconds=1))
    assert not outcome.admitted and outcome.reason == 'BUNDLE_NOT_ATOMIC'


def test_mechanics_rejects_unauthenticated_metrics_role(state, tmp_path):
    ledger, cutoff = mechanics_ledger(state, tmp_path / 'role.db')
    outcome = dsa.admit_taker_mechanics(ledger, dataset_role='DISCOVERY', cutoff=cutoff,
                                        clock=lambda: cutoff + timedelta(seconds=1))
    assert not outcome.admitted and outcome.reason in ('BUNDLE_NOT_ATOMIC', 'METRICS_HISTORY_NOT_READY')
    assert not dsa.admit_taker_mechanics(ledger, dataset_role='UNKNOWN', cutoff=cutoff).admitted
    assert dsa.admit_taker_mechanics(ledger, dataset_role='UNKNOWN', cutoff=cutoff).reason == 'ROLE_MISMATCH'


def test_mechanics_references_exact_bundle_identities(state, tmp_path):
    ledger, cutoff = mechanics_ledger(state, tmp_path / 'ids.db')
    outcome = dsa.admit_taker_mechanics(ledger, dataset_role='PILOT', cutoff=cutoff,
                                        clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    row = known[outcome.observation_id]
    assert row['dependencies']
    for identity in row['dependencies']:
        assert identity in known
    for feature, item in row['payload']['raw_values'].items():
        assert item['source_id'] in known and known[item['source_id']]['feature'] == feature
    assert row['payload']['snapshot_id']


def test_mechanics_availability_obeys_the_causal_rule(state, tmp_path):
    ledger, cutoff = mechanics_ledger(state, tmp_path / 'avail.db')
    outcome = dsa.admit_taker_mechanics(ledger, dataset_role='PILOT', cutoff=cutoff,
                                        clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    from core.scientific.regime_observation import _utc
    row = known[outcome.observation_id]
    deps = [_utc(known[i]['available_at']) for i in row['dependencies']]
    assert _utc(row['available_at']) == max([_utc(row['computed_at'])] + deps)
    assert _utc(row['event_time']) <= _utc(row['received_at']) <= _utc(row['computed_at']) <= _utc(row['available_at'])


# --- missing != UNKNOWN != zero --------------------------------------------
def test_missing_is_not_unknown(state, tmp_path):
    ledger, cutoff = mechanics_ledger(state, tmp_path / 'unk.db')
    outcome = dsa.admit_taker_mechanics(ledger, dataset_role='PILOT', cutoff=cutoff,
                                        clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    row = known[outcome.observation_id]
    unsupported = row['payload']['unknown_dimensions']
    assert unsupported and all(value is None for value in unsupported.values())
    assert not any(value == 0 for value in unsupported.values())


def test_missing_is_not_zero(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_taker_mechanics(ledger, dataset_role='PILOT', cutoff=cutoff,
                                       clock=lambda: cutoff + timedelta(seconds=1))
    assert not outcome.admitted                   # no metrics history at all
    assert outcome.reason in DERIVED_OK           # explicit reason, never a neutral value


# --- append-only / idempotence / conflict ----------------------------------
def test_duplicate_identical_admission_is_idempotent(window):
    ledger, ids, cutoff, _ = window
    certificate = regime_cert(ledger, ids, 'PILOT', cutoff)
    first = dsa.admit_regime(ledger, certificate, dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    before = len(observation_snapshot(ledger, read_only=True)[0])
    second = dsa.admit_regime(ledger, certificate, dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=2))
    after = len(observation_snapshot(ledger, read_only=True)[0])
    assert first.observation_id == second.observation_id and before == after


def test_conflicting_duplicate_fails_closed(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    row = known[outcome.observation_id]
    with pytest.raises(ValueError, match='conflicting observation'):
        append_observation(ledger, source=row['source'], instrument=row['instrument'],
                           feature=row['feature'], event_time=row['event_time'],
                           source_metric_at=row['source_metric_at'], received_at=row['received_at'],
                           payload={'tampered': True}, provenance=row['provenance'],
                           dependencies=row['dependencies'], derived=True,
                           clock=lambda: row['received_at'])


def test_historical_publication_rows_remain_unchanged():
    if not LIVE_METRICS_DB.exists():
        pytest.skip('live metrics admission store not present')
    con = sqlite3.connect('file:' + str(LIVE_METRICS_DB).replace('\\', '/') + '?mode=ro', uri=True)
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        target = 'metrics_publications_v1' if 'metrics_publications_v1' in tables else None
        if target is None:
            pytest.skip('publication table not present')
        rows = [json.loads(r[0]) for r in con.execute('SELECT body FROM ' + target)]
    finally:
        con.close()
    assert rows
    assert all(row.get('mechanics_id') is None for row in rows)   # never rewritten by this cut


def test_no_derived_snapshot_is_backdated(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    from core.scientific.regime_observation import _utc
    row = known[outcome.observation_id]
    assert _utc(row['computed_at']) >= _utc(row['provenance']['certificate']['cutoff'])
    assert _utc(row['available_at']) >= _utc(row['computed_at'])
    assert _utc(row['available_at']) > _utc(row['event_time'])


def test_future_evidence_cannot_enter_derivation(window):
    ledger, ids, cutoff, _ = window
    with pytest.raises(ValueError, match='future observation'):
        append_observation(ledger, source='oma://test/future', instrument='BTCUSDT',
                           feature='Price/OHLCV', event_time=cutoff, source_metric_at=cutoff,
                           received_at=cutoff + timedelta(hours=2), payload={'close': 1.0},
                           provenance={'contract': 'test'}, clock=lambda: cutoff)


# --- Experiment 51 arm binding ---------------------------------------------
def test_pr_requires_admitted_regime():
    assert dsa.arm_requirements('PR') == ('REGIME',)
    assert actions(IntentAction.LONG, None, None)[1][0] is IntentAction.ABSTAIN
    assert actions(IntentAction.LONG, 'transition', '1.5')[1][0] is IntentAction.ABSTAIN


def test_pm_requires_admitted_mechanics():
    assert dsa.arm_requirements('PM') == ('MECHANICS_TAKER',)
    assert actions(IntentAction.LONG, 'trend', None)[2][0] is IntentAction.ABSTAIN


def test_prm_requires_both_admitted_snapshots():
    assert dsa.arm_requirements('PRM') == ('REGIME', 'MECHANICS_TAKER')
    assert actions(IntentAction.LONG, None, '1.5')[3][0] is IntentAction.ABSTAIN
    assert actions(IntentAction.LONG, 'unknown', None)[3][0] is IntentAction.ABSTAIN


def test_p0_does_not_require_derived_snapshots():
    assert dsa.arm_requirements('P0') == ()
    for structure in (None, 'transition', 'unknown'):
        for taker in (None, '1'):
            assert actions(IntentAction.LONG, structure, taker)[0] == (IntentAction.LONG, 'P0_AGREEMENT')


def test_evaluation_cannot_compute_derived_state_ad_hoc():
    forbidden = ('build_causal_mechanics', 'append_causal_mechanics', 'append_causal_regime',
                 'classify_regime', 'build_market_state', '_derive')
    for name in ('experiment51_derived.py', 'experiment51_sealed.py'):
        source = (ROOT / 'core/scientific' / name).read_text(encoding='utf-8')
        tree = ast.parse(source)
        imported = set()
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                imported.update(alias.name.split('.')[-1] for alias in node.names)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.add(node.func.id)
        assert not (imported & set(forbidden)), name
        assert not (called & set(forbidden)), name
    derived = (ROOT / 'core/scientific/experiment51_derived.py').read_text(encoding='utf-8')
    assert 'validate_causal_regime' in derived and 'validate_causal_mechanics' in derived


def test_role_mismatch_fails_closed(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    with pytest.raises(dsa.DerivedSnapshotRejected) as error:
        dsa.require_admitted_regime(ledger, dataset_role='DISCOVERY', cutoff=cutoff + timedelta(seconds=1),
                                    regime_id=outcome.observation_id)
    assert error.value.reason in ('ROLE_MISMATCH', 'DERIVATION_NOT_AVAILABLE', 'AUTHORITY_MISMATCH')
    with pytest.raises(dsa.DerivedSnapshotRejected) as unknown_role:
        dsa.require_admitted_regime(ledger, dataset_role='UNKNOWN', cutoff=cutoff, regime_id=outcome.observation_id)
    assert unknown_role.value.reason == 'ROLE_MISMATCH'


def test_authority_mismatch_fails_closed(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    row = known[outcome.observation_id]
    with pytest.raises(dsa.DerivedSnapshotRejected) as forged:
        dsa.require_admitted_regime(ledger, dataset_role='PILOT', cutoff=cutoff + timedelta(seconds=1),
                                    regime_id={**row, 'id': 'forged'}['id'])
    assert forged.value.reason in ('RAW_INPUT_NOT_ADMITTED', 'AUTHORITY_MISMATCH', 'DERIVATION_NOT_AVAILABLE')


def test_rule_hash_mismatch_fails_closed(window):
    ledger, ids, cutoff, _ = window
    outcome = dsa.admit_regime(ledger, regime_cert(ledger, ids, 'PILOT', cutoff),
                               dataset_role='PILOT', clock=lambda: cutoff + timedelta(seconds=1))
    known, _ = observation_snapshot(ledger, read_only=True)
    tampered = {**known[outcome.observation_id]}
    tampered['payload'] = {**tampered['payload'], 'regime': {'structure': 'trend'}}
    from core.scientific.causal_regime import validate_causal_regime
    with pytest.raises(ValueError):
        validate_causal_regime({**known, outcome.observation_id: tampered}, tampered,
                               dataset_role='PILOT', cutoff=cutoff + timedelta(seconds=1))
    with pytest.raises(dsa.DerivedSnapshotRejected) as unknown_id:
        dsa.require_admitted_regime(ledger, dataset_role='PILOT', cutoff=cutoff + timedelta(seconds=1),
                                    regime_id='not-a-persisted-derived-id')
    assert unknown_id.value.reason == 'RAW_INPUT_NOT_ADMITTED'


def test_commitment_bundle_is_deterministic_and_complete():
    bundle = dsa.verify()
    assert dsa.bundle_commitment() == dsa.bundle_commitment()
    for key in ('regime_derived_schema', 'mechanics_derived_schema', 'regime_derivation_rule_id',
                'regime_derivation_rule_hash', 'mechanics_taker_derivation_rule_id',
                'mechanics_taker_derivation_rule_hash', 'derived_snapshot_schema_hash',
                'derived_admission_rule_hash', 'derived_availability_rule', 'arms'):
        assert key in bundle
    assert bundle['regime_derived_schema'] == 'causal-role-regime-v2'
    assert bundle['mechanics_derived_schema'] == 'causal-descriptive-mechanics-v1'
    assert bundle['append_only'] and bundle['backfill'] is False
    assert bundle['historical_rewrite'] is False
    assert 'available_at = max(computed_at' in bundle['derived_availability_rule']


def test_bundle_feature_order_is_canonical_and_hash_reproducible():
    """EXPECTED_FEATURES is a frozenset: without sorting, the schema hash depends on
    PYTHONHASHSEED and the commitment is not reproducible across processes."""
    assert dsa.BUNDLE_FEATURES == tuple(sorted(dsa.EXPECTED_FEATURES))
    assert list(dsa.BUNDLE_FEATURES) == sorted(dsa.BUNDLE_FEATURES)
    assert len(dsa.BUNDLE_FEATURES) == 6 and dsa.TAKER_FEATURE in dsa.BUNDLE_FEATURES
    assert dsa.derived_snapshot_schema_hash() == dsa.DERIVED_SNAPSHOT_SCHEMA_HASH
    assert dsa.verify()['derived_snapshot_schema_hash'] == dsa.DERIVED_SNAPSHOT_SCHEMA_HASH
