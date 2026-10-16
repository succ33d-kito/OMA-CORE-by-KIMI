"""Qualification of the prospective Regime producer (fail-closed before 81 slots).

TEST evidence only: no outcome, no Experiment 51 execution, no phase activation.
"""
import json
import shutil
from datetime import timedelta
from pathlib import Path

import pytest

import tests.test_price_role_attestation as fixture
from core.scientific import price_role_attestation as attestation
from core.scientific import regime_derived_operator as producer_module
from core.scientific.decision_rule import IntentAction
from core.scientific.derived_snapshot_admission import (
    DERIVED_ADMISSION_RULE_HASH, DERIVED_SNAPSHOT_SCHEMA_HASH, REGIME_DERIVATION_RULE_HASH,
    arm_requirements, require_admitted_regime)
from core.scientific.experiment51_derived import actions
from core.scientific.prospective_receipts import append_observation, observation_snapshot
from core.scientific.regime_derived_operator import (
    FROZEN_ADMISSION_RULE_HASH, FROZEN_RULE_HASH, FROZEN_SNAPSHOT_SCHEMA_HASH, GRACE_SLOTS, HOUR,
    WINDOW_BARS, RegimeDerivedOperatorV1, candidates, window_cutoff)


def build_role(tmp, hours, *, role='PILOT', skip=()):
    """Build a role ledger with `hours` captured H1 slots (optionally skipping some)."""
    mp = pytest.MonkeyPatch()
    start = fixture.T
    state = fixture.create_activation(tmp, mp)
    ledger = tmp / 'base.db'
    ids, t = [], start
    for hour in range(hours):
        t = start + timedelta(hours=hour)
        if hour in skip:
            continue
        mp.setattr(fixture, 'T', t)
        auth = fixture.authorize(state, mp)
        row = fixture.append_price(ledger)
        mp.setattr(attestation, '_now', lambda t=t: t + timedelta(seconds=4))
        attestation.attest_price_observation(state, ledger, repo_root=fixture.repo_root(),
                                             slot_id=auth['slot_id'], observation_id=row['id'])
        ids.append(row['id'])
    mp.undo()
    return ledger, ids, t


@pytest.fixture(scope='module')
def full(tmp_path_factory):
    tmp = tmp_path_factory.mktemp('regime-full')
    return build_role(tmp, 82)


def root_for(tmp, ledger, *, role='PILOT', config=True):
    root = tmp / 'role'
    root.mkdir()
    shutil.copyfile(ledger, root / 'observations.db')
    for suffix in ('-wal', '-shm'):
        candidate = Path(str(ledger) + suffix)
        if candidate.exists():
            shutil.copyfile(candidate, str(root / 'observations.db') + suffix)
    if config:
        (root / 'config.json').write_text(json.dumps(
            {'schema': 'price-role-activation-v1', 'dataset_role': role,
             'activation_id': 'e4235606e0c80c8aad0d3628c3c166e6993bf2c7d23f5dae75c1f49b18da2de7'}))
    return root


def snapshots(root):
    ledger = Path(root) / 'observations.db'
    if not ledger.exists():
        return []
    known, _ = observation_snapshot(ledger, read_only=True)
    return [row for row in known.values() if row.get('feature') == 'Regime/Role/v2']


def rows(root):
    ledger = Path(root) / 'observations.db'
    if not ledger.exists():
        return 0
    known, _ = observation_snapshot(ledger, read_only=True)
    return len(known)


# 1 --------------------------------------------------------------------------
def test_producer_with_zero_evidence_writes_nothing(tmp_path):
    root = tmp_path / 'role'
    root.mkdir()
    (root / 'config.json').write_text(json.dumps({'dataset_role': 'PILOT'}))
    out = RegimeDerivedOperatorV1(root).once()
    assert out['status'] == 'NOT_READY' and out['reason'] == 'PRICE_HISTORY_NOT_READY'
    assert out['regime_snapshot_created'] is False and snapshots(root) == []


# 2 --------------------------------------------------------------------------
def test_producer_with_80_slots_writes_nothing(tmp_path):
    ledger, ids, last = build_role(tmp_path, 80)
    root = root_for(tmp_path, ledger)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    assert out['status'] == 'NOT_READY' and out['reason'] == 'PRICE_HISTORY_NOT_READY'
    assert out['price_current_streak'] == 80 and out['price_slots_to_81'] == 1
    assert snapshots(root) == []


# 3 --------------------------------------------------------------------------
def test_streak_81_contiguous_produces_exactly_one_snapshot(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    assert out['status'] == 'PRODUCED' and out['reason'] == 'OK', out
    assert out['regime_snapshot_created'] is True
    rows_ = snapshots(root)
    assert len(rows_) == 1 and rows_[0]['id'] == out['regime_id']


# 4 --------------------------------------------------------------------------
def test_gap_inside_window_writes_nothing(tmp_path):
    ledger, ids, last = build_role(tmp_path, 82, skip={40})
    root = root_for(tmp_path, ledger)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    assert out['status'] == 'NOT_READY' and out['reason'] == 'PRICE_GAP', out
    assert snapshots(root) == []


# 5 --------------------------------------------------------------------------
def test_bad_role_writes_nothing(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger, role='DISCOVERY')
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    assert out['status'] == 'NOT_READY' and out['reason'] == 'PRICE_ROLE_NOT_AUTHENTICATED'
    assert snapshots(root) == []


# 6 --------------------------------------------------------------------------
def test_wrong_authority_writes_nothing(tmp_path, full):
    ledger, ids, last = full
    missing = root_for(tmp_path, ledger, config=False)
    out = RegimeDerivedOperatorV1(missing).once(now=last + timedelta(minutes=5))
    assert out['status'] == 'REJECTED' and out['reason'] == 'AUTHORITY_MISMATCH'
    assert snapshots(missing) == []
    wrong = tmp_path / 'unknown-role'
    wrong.mkdir()
    shutil.copyfile(ledger, wrong / 'observations.db')
    (wrong / 'config.json').write_text(json.dumps({'dataset_role': 'UNKNOWN'}))
    out = RegimeDerivedOperatorV1(wrong).once(now=last + timedelta(minutes=5))
    assert out['status'] == 'REJECTED' and out['reason'] == 'ROLE_MISMATCH'
    assert snapshots(wrong) == []


# 7 --------------------------------------------------------------------------
def test_future_evidence_is_rejected(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    operator = RegimeDerivedOperatorV1(root)
    out = operator.once(now=fixture.T + timedelta(hours=1))     # long before capture
    assert out['status'] == 'NOT_READY' and out['regime_snapshot_created'] is False
    assert snapshots(root) == []
    known, _ = observation_snapshot(root / 'observations.db', read_only=True)
    prices = sorted([r for r in known.values() if r['feature'] == 'Price/OHLCV'], key=lambda r: r['event_time'])
    future = {**known, prices[-1]['id']: {**prices[-1], 'available_at': (last + timedelta(days=30)).isoformat()}}
    ids_, reason = operator.window_status(future, last, 'PILOT', last + timedelta(minutes=5))
    assert ids_ is None and reason == 'RAW_INPUT_NOT_CAUSAL'


# 8 --------------------------------------------------------------------------
def test_conflicting_price_evidence_is_rejected(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    operator = RegimeDerivedOperatorV1(root)
    known, _ = observation_snapshot(root / 'observations.db', read_only=True)
    prices = sorted([r for r in known.values() if r['feature'] == 'Price/OHLCV'], key=lambda r: r['event_time'])
    target = prices[-1]
    duplicate = {**target, 'id': 'conflicting:twin'}
    conflicted = {**known, 'conflicting:twin': duplicate}
    ids_, reason = operator.window_status(conflicted, last, 'PILOT', last + timedelta(minutes=5))
    assert ids_ is None and reason == 'WINDOW_CONFLICT'
    assert snapshots(root) == []


# 9 --------------------------------------------------------------------------
def test_identical_rerun_is_idempotent(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    moment = last + timedelta(minutes=5)
    first = RegimeDerivedOperatorV1(root).once(now=moment)
    before = rows(root)
    second = RegimeDerivedOperatorV1(root).once(now=moment + timedelta(seconds=30))
    assert first['status'] == 'PRODUCED'
    assert second['status'] == 'ALREADY_ADMITTED' and second['regime_id'] == first['regime_id']
    assert rows(root) == before and len(snapshots(root)) == 1


# 10 -------------------------------------------------------------------------
def test_no_earlier_historical_slot_is_backfilled(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    row = [r for r in snapshots(root) if r['id'] == out['regime_id']][0]
    certificate = row['provenance']['certificate']
    assert certificate['last_event_time'] == last.isoformat()
    assert certificate['first_event_time'] == (last - timedelta(hours=80)).isoformat()
    assert len(snapshots(root)) == 1


# 11 -------------------------------------------------------------------------
def test_only_the_current_prospective_candidate_may_be_admitted(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    operator = RegimeDerivedOperatorV1(root)
    produced = operator.once(now=last + timedelta(minutes=5))
    assert produced['status'] == 'PRODUCED'
    stale = operator.once(now=last + timedelta(hours=2, minutes=5))   # candidate + grace beyond data
    assert stale['status'] == 'NOT_READY'
    assert len(snapshots(root)) == 1                                   # old window not re-admitted


# 12 -------------------------------------------------------------------------
def test_snapshot_binds_the_exact_81_source_slots(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    row = [r for r in snapshots(root) if r['id'] == out['regime_id']][0]
    certificate = row['provenance']['certificate']
    assert certificate['receipt_ids'] == list(ids[-WINDOW_BARS:])
    assert certificate['number_of_bars'] == WINDOW_BARS and certificate['gaps'] == 0
    assert len(row['dependencies']) == 2 * WINDOW_BARS


# 13 -------------------------------------------------------------------------
def test_snapshot_rule_hash_matches_the_frozen_rule(tmp_path, full, monkeypatch):
    assert FROZEN_RULE_HASH == REGIME_DERIVATION_RULE_HASH
    assert FROZEN_SNAPSHOT_SCHEMA_HASH == DERIVED_SNAPSHOT_SCHEMA_HASH
    assert FROZEN_ADMISSION_RULE_HASH == DERIVED_ADMISSION_RULE_HASH
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    row = [r for r in snapshots(root) if r['id'] == out['regime_id']][0]
    assert row['provenance']['contract'] == 'causal-role-regime-v2'
    monkeypatch.setattr(producer_module, 'FROZEN_RULE_HASH', 'deadbeef')
    drift = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=6))
    assert drift['status'] == 'REJECTED' and drift['reason'] == 'DERIVATION_RULE_MISMATCH'


# 14 -------------------------------------------------------------------------
def test_snapshot_availability_is_causal(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    moment = last + timedelta(minutes=5)
    out = RegimeDerivedOperatorV1(root).once(now=moment)
    known, _ = observation_snapshot(root / 'observations.db', read_only=True)
    row = known[out['regime_id']]
    from core.scientific.regime_observation import _utc
    deps = [_utc(known[i]['available_at']) for i in row['dependencies']]
    assert _utc(row['available_at']) == max([_utc(row['computed_at'])] + deps)
    assert _utc(row['event_time']) <= _utc(row['received_at']) <= _utc(row['computed_at']) <= _utc(row['available_at'])
    assert _utc(row['computed_at']) >= _utc(row['provenance']['certificate']['cutoff'])
    assert window_cutoff(last) == last + timedelta(minutes=5)


# 15 -------------------------------------------------------------------------
def test_unknown_is_not_emitted_for_missing_data(tmp_path):
    ledger, ids, last = build_role(tmp_path, 80)
    root = root_for(tmp_path, ledger)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    assert 'UNKNOWN' not in json.dumps(out)
    assert snapshots(root) == []
    known, _ = observation_snapshot(root / 'observations.db', read_only=True)
    # no scientific derived snapshot of interest was emitted (attestations are separate rows)
    assert not [row for row in known.values()
                if row.get('feature') in ('Regime/Role/v2', 'Mechanics/Descriptive/v1')]


# 16 -------------------------------------------------------------------------
def test_no_placeholder_or_neutral_state_is_written(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    before = rows(root)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(hours=3))
    assert out['status'] == 'NOT_READY'
    assert rows(root) == before and snapshots(root) == []


# 17 -------------------------------------------------------------------------
def test_restart_preserves_idempotence(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    first = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    restarted = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=6))
    assert first['status'] == 'PRODUCED' and restarted['status'] == 'ALREADY_ADMITTED'
    assert restarted['regime_id'] == first['regime_id']
    assert len(snapshots(root)) == 1


# 18 -------------------------------------------------------------------------
def test_state_loss_cannot_fabricate_scientific_history(tmp_path):
    root = tmp_path / 'role'
    root.mkdir()
    (root / 'config.json').write_text(json.dumps({'dataset_role': 'PILOT'}))
    operator = RegimeDerivedOperatorV1(root)
    first = operator.once()
    status = operator.status()
    assert first['status'] == 'NOT_READY' and status['regime_snapshots_admitted'] == 0
    files = sorted(p.name for p in root.iterdir())
    assert not [name for name in files if 'state' in name or 'heartbeat' in name or 'producer' in name]
    assert set(files) <= {'config.json', 'observations.db', 'observations.db-wal', 'observations.db-shm'}
    assert snapshots(root) == []


# 19 -------------------------------------------------------------------------
def test_experiment51_can_resolve_the_snapshot_by_exact_id(tmp_path, full):
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    resolved = require_admitted_regime(root / 'observations.db', dataset_role='PILOT',
                                       cutoff=last + timedelta(hours=1), regime_id=out['regime_id'])
    assert resolved['id'] == out['regime_id']
    assert resolved['payload']['regime']['structure'] in ('trend', 'range', 'transition', 'unknown')


# 20 -------------------------------------------------------------------------
def test_p0_remains_independent_of_regime(tmp_path, full):
    assert arm_requirements('P0') == ()
    assert arm_requirements('PR') == ('REGIME',)
    ledger, ids, last = full
    root = root_for(tmp_path, ledger)
    out = RegimeDerivedOperatorV1(root).once(now=last + timedelta(minutes=5))
    assert out['status'] == 'PRODUCED'
    assert actions(IntentAction.LONG, None, None)[0] == (IntentAction.LONG, 'P0_AGREEMENT')
    assert candidates(last + timedelta(minutes=5)) == (last, last - HOUR)   # bounded grace only
    assert GRACE_SLOTS == 1
