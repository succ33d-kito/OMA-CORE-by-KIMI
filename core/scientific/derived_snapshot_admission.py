"""Prospective admission operator for the derived snapshots required by Experiment 51.

Scope: the exact derived Regime (`Regime/Role/v2`) and Taker Mechanics
(`Mechanics/Descriptive/v1`) snapshots. This module EXTENDS the existing causal
snapshot infrastructure (``causal_regime``, ``causal_mechanics``,
``prospective_receipts``); it does not create a parallel store and it never writes
raw evidence, backfills, repairs or rewrites history.

Guarantees:
* append-only through ``prospective_receipts.append_observation`` (hash chain);
* idempotent for an identical derivation, conflict-rejecting for the same identity
  with different content;
* role- and authority-aware (derivation rebuilds from the authenticated ledger);
* fail closed with explicit typed reasons; missing data NEVER becomes UNKNOWN and
  never becomes a synthetic neutral value.

Synthetic fixtures are TEST evidence only: qualifying this operator does not make
live derived snapshots available.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

from . import causal_mechanics, causal_regime
from .causal_mechanics import append_causal_mechanics, validate_causal_mechanics
from .causal_regime import append_causal_regime, validate_causal_regime
from .metrics_observation_admission import EXPECTED_FEATURES
from .nuisance_pilot_contracts import digest
from .price_role_activation import ROLES
from .prospective_receipts import observation_snapshot
from .regime_observation import _utc
from .role_price_window import SCHEMA as WINDOW_SCHEMA

REGIME_DERIVED_SCHEMA = causal_regime.CONTRACT
MECHANICS_DERIVED_SCHEMA = causal_mechanics.CONTRACT
REGIME_FEATURE = causal_regime.FEATURE
MECHANICS_FEATURE = causal_mechanics.FEATURE
TAKER_FEATURE = 'MarketMetrics/TakerBuySellRatio'
EXP51_MECHANICS_INPUTS = (TAKER_FEATURE,)
BUNDLE_FEATURES = tuple(EXPECTED_FEATURES)
REGIME_WINDOW_BARS = 81

REGIME_DERIVATION_RULE_ID = 'exp51-regime-role-v2'
MECHANICS_TAKER_DERIVATION_RULE_ID = 'exp51-mechanics-taker-v1'

DERIVED_AVAILABILITY_RULE = (
    'available_at = max(computed_at, max(dependency.available_at)); '
    'event_time <= received_at <= computed_at <= available_at <= cutoff; '
    'never backdated to event/slot/source-publication/raw-capture time'
)

REGIME_DERIVATION_RULE_HASH = digest((REGIME_DERIVATION_RULE_ID, REGIME_DERIVED_SCHEMA,
    REGIME_FEATURE, WINDOW_SCHEMA, REGIME_WINDOW_BARS, DERIVED_AVAILABILITY_RULE))
MECHANICS_TAKER_DERIVATION_RULE_HASH = digest((MECHANICS_TAKER_DERIVATION_RULE_ID,
    MECHANICS_DERIVED_SCHEMA, MECHANICS_FEATURE, BUNDLE_FEATURES, EXP51_MECHANICS_INPUTS,
    DERIVED_AVAILABILITY_RULE))
DERIVED_SNAPSHOT_SCHEMA_HASH = digest((REGIME_DERIVED_SCHEMA, MECHANICS_DERIVED_SCHEMA,
    REGIME_FEATURE, MECHANICS_FEATURE, WINDOW_SCHEMA, BUNDLE_FEATURES))
DERIVED_ADMISSION_RULE_HASH = digest(('observations_v2', DERIVED_AVAILABILITY_RULE,
    'append-only-hash-chain', 'idempotent-identical-identity', 'conflict-reject',
    'no-backfill-or-retroactive-availability'))

# Experiment 51 arm -> required admitted derived snapshots (P0 stays independent).
ARMS = {
    'P0': (),
    'PR': ('REGIME',),
    'PM': ('MECHANICS_TAKER',),
    'PRM': ('REGIME', 'MECHANICS_TAKER'),
}

_REASONS = ('PRICE_HISTORY_NOT_READY', 'METRICS_HISTORY_NOT_READY', 'RAW_INPUT_NOT_ADMITTED',
            'AUTHORITY_MISMATCH', 'ROLE_MISMATCH', 'PUBLICATION_NOT_CAUSAL',
            'DERIVATION_NOT_AVAILABLE', 'BUNDLE_NOT_ATOMIC')

_REGIME_MAP = (
    ('explicit supported dataset role required', 'ROLE_MISMATCH'),
    ('exactly 81 unique prices required', 'PRICE_HISTORY_NOT_READY'),
    ('ordered contiguous H1 prices required', 'PRICE_HISTORY_NOT_READY'),
    ('missing, late or invalid role attestation', 'AUTHORITY_MISMATCH'),
    ('role price certificate mismatch', 'AUTHORITY_MISMATCH'),
    ('certificate reconstruction failed', 'AUTHORITY_MISMATCH'),
    ('raw BTCUSDT price dependency required', 'RAW_INPUT_NOT_ADMITTED'),
    ('wrong price contract', 'RAW_INPUT_NOT_ADMITTED'),
    ('price unavailable at cutoff', 'RAW_INPUT_NOT_ADMITTED'),
    ('price capture is not contemporaneous', 'RAW_INPUT_NOT_ADMITTED'),
    ('exact H1 boundary required', 'RAW_INPUT_NOT_ADMITTED'),
    ('conflicting price in certified interval', 'RAW_INPUT_NOT_ADMITTED'),
    ('computation precedes input cutoff', 'PUBLICATION_NOT_CAUSAL'),
)

_MECHANICS_MAP = (
    ('explicit supported dataset role required', 'ROLE_MISMATCH'),
    ('no causal evidence; cannot persist empty mechanics', 'METRICS_HISTORY_NOT_READY'),
    ('missing derived regime dependency', 'RAW_INPUT_NOT_ADMITTED'),
    ('non-finite factual input', 'RAW_INPUT_NOT_ADMITTED'),
    ('computation precedes input cutoff', 'PUBLICATION_NOT_CAUSAL'),
)


class DerivedSnapshotRejected(ValueError):
    """Fail-closed rejection carrying an explicit machine-readable reason."""

    def __init__(self, reason, detail):
        if reason not in _REASONS:
            raise ValueError('unsupported rejection reason')
        self.reason = reason
        self.detail = detail
        super().__init__(reason + ': ' + detail)


def _reason(error, table):
    text = str(error)
    for needle, reason in table:
        if needle in text:
            return reason
    return 'DERIVATION_NOT_AVAILABLE'


@dataclass(frozen=True, slots=True)
class AdmissionOutcome:
    kind: str
    status: str
    reason: str
    observation_id: str | None
    detail: str

    @property
    def admitted(self):
        return self.status == 'ADMITTED'


def _now(clock):
    return _utc(clock() if clock else datetime.now(timezone.utc))


def admit_regime(ledger, certificate, *, dataset_role, clock=None):
    """Attempt one prospective Regime snapshot admission. Never writes on failure."""
    if dataset_role not in ROLES:
        return AdmissionOutcome('REGIME', 'REJECTED', 'ROLE_MISMATCH', None, str(dataset_role))
    try:
        row = append_causal_regime(ledger, certificate, clock=clock)
    except Exception as error:                      # noqa: BLE001 - translated, fail closed
        return AdmissionOutcome('REGIME', 'REJECTED', _reason(error, _REGIME_MAP), None, str(error))
    known, _ = observation_snapshot(ledger, read_only=True)
    validate_causal_regime(known, known[row['id']], dataset_role=dataset_role, cutoff=_now(clock))
    return AdmissionOutcome('REGIME', 'ADMITTED', 'OK', row['id'],
                            'regime snapshot admitted from certified 81-slot window')


def admit_taker_mechanics(ledger, *, dataset_role, cutoff, regime_id=None, clock=None):
    """Attempt one prospective Taker-Mechanics admission. Never writes on failure."""
    if dataset_role not in ROLES:
        return AdmissionOutcome('MECHANICS_TAKER', 'REJECTED', 'ROLE_MISMATCH', None, str(dataset_role))
    known, _ = observation_snapshot(ledger, read_only=True)
    from .causal_mechanics import build_causal_mechanics
    try:
        view = build_causal_mechanics(ledger, dataset_role=dataset_role, cutoff=cutoff,
                                     regime_id=regime_id)
    except Exception as error:                      # noqa: BLE001 - translated, fail closed
        return AdmissionOutcome('MECHANICS_TAKER', 'REJECTED', _reason(error, _MECHANICS_MAP), None, str(error))
    metrics = tuple(key for key in view['raw_values'] if key.startswith('MarketMetrics/'))
    if set(metrics) != set(BUNDLE_FEATURES) or not set(EXP51_MECHANICS_INPUTS) <= set(metrics):
        return AdmissionOutcome('MECHANICS_TAKER', 'REJECTED', 'BUNDLE_NOT_ATOMIC', None,
                                'six-value atomic bundle required: ' + repr(sorted(metrics)))
    if view['regime'] is not None or 'FundingRate/Published' in view['raw_values']:
        return AdmissionOutcome('MECHANICS_TAKER', 'REJECTED', 'RAW_INPUT_NOT_ADMITTED', None,
                                'Experiment 51 Taker information set is isolated')
    try:
        row = append_causal_mechanics(ledger, dataset_role=dataset_role, cutoff=cutoff,
                                      regime_id=regime_id, clock=clock)
    except Exception as error:                      # noqa: BLE001 - translated, fail closed
        return AdmissionOutcome('MECHANICS_TAKER', 'REJECTED', _reason(error, _MECHANICS_MAP), None, str(error))
    validate_causal_mechanics(ledger, known.get(row['id'], row), dataset_role=dataset_role,
                              cutoff=_now(clock))
    return AdmissionOutcome('MECHANICS_TAKER', 'ADMITTED', 'OK', row['id'],
                            'taker mechanics snapshot admitted from atomic authenticated bundle')


def require_admitted_regime(ledger, *, dataset_role, cutoff, regime_id):
    """Return the exact admitted Regime row Experiment 51 PR/PRM must consume."""
    if dataset_role not in ROLES:
        raise DerivedSnapshotRejected('ROLE_MISMATCH', str(dataset_role))
    known, _ = observation_snapshot(ledger, read_only=True)
    row = known.get(regime_id)
    if row is None:
        raise DerivedSnapshotRejected('RAW_INPUT_NOT_ADMITTED', 'unknown regime id')
    try:
        return validate_causal_regime(known, row, dataset_role=dataset_role, cutoff=cutoff)
    except Exception as error:                      # noqa: BLE001 - fail closed
        raise DerivedSnapshotRejected(_reason(error, _REGIME_MAP), str(error)) from None


def require_admitted_taker_mechanics(ledger, *, dataset_role, cutoff, mechanics_id):
    """Return the exact admitted Taker-Mechanics row PM/PRM must consume."""
    if dataset_role not in ROLES:
        raise DerivedSnapshotRejected('ROLE_MISMATCH', str(dataset_role))
    known, _ = observation_snapshot(ledger, read_only=True)
    row = known.get(mechanics_id)
    if row is None:
        raise DerivedSnapshotRejected('RAW_INPUT_NOT_ADMITTED', 'unknown mechanics id')
    try:
        validated = validate_causal_mechanics(ledger, row, dataset_role=dataset_role, cutoff=cutoff)
    except Exception as error:                      # noqa: BLE001 - fail closed
        raise DerivedSnapshotRejected(_reason(error, _MECHANICS_MAP), str(error)) from None
    metrics = tuple(key for key in validated['payload']['raw_values'] if key.startswith('MarketMetrics/'))
    if set(metrics) != set(BUNDLE_FEATURES):
        raise DerivedSnapshotRejected('BUNDLE_NOT_ATOMIC', repr(sorted(metrics)))
    return validated


def arm_requirements(arm):
    if arm not in ARMS:
        raise ValueError('unsupported Experiment 51 arm')
    return ARMS[arm]


def verify():
    """Fail-closed verification of the binding against live contracts. No I/O to journals."""
    if REGIME_DERIVED_SCHEMA != 'causal-role-regime-v2' or REGIME_FEATURE != 'Regime/Role/v2':
        raise ValueError('REGIME_CONTRACT_MISMATCH')
    if MECHANICS_DERIVED_SCHEMA != 'causal-descriptive-mechanics-v1' or MECHANICS_FEATURE != 'Mechanics/Descriptive/v1':
        raise ValueError('MECHANICS_CONTRACT_MISMATCH')
    if WINDOW_SCHEMA != 'price-81h-role-certificate-v1':
        raise ValueError('WINDOW_SCHEMA_MISMATCH')
    if len(BUNDLE_FEATURES) != 6 or TAKER_FEATURE not in BUNDLE_FEATURES:
        raise ValueError('BUNDLE_FEATURES_MISMATCH')
    if set(EXP51_MECHANICS_INPUTS) != {TAKER_FEATURE}:
        raise ValueError('TAKER_ONLY_INPUT_MISMATCH')
    if tuple(sorted(ARMS)) != ('P0', 'PM', 'PR', 'PRM'):
        raise ValueError('ARM_COVERAGE_MISMATCH')
    return commitment_bundle()


def commitment_bundle():
    return dict(
        schema='experiment51-derived-snapshot-commitment-v1',
        regime_derived_schema=REGIME_DERIVED_SCHEMA,
        mechanics_derived_schema=MECHANICS_DERIVED_SCHEMA,
        regime_feature=REGIME_FEATURE,
        mechanics_feature=MECHANICS_FEATURE,
        regime_derivation_rule_id=REGIME_DERIVATION_RULE_ID,
        regime_derivation_rule_hash=REGIME_DERIVATION_RULE_HASH,
        mechanics_taker_derivation_rule_id=MECHANICS_TAKER_DERIVATION_RULE_ID,
        mechanics_taker_derivation_rule_hash=MECHANICS_TAKER_DERIVATION_RULE_HASH,
        derived_snapshot_schema_hash=DERIVED_SNAPSHOT_SCHEMA_HASH,
        derived_admission_rule_hash=DERIVED_ADMISSION_RULE_HASH,
        derived_availability_rule=DERIVED_AVAILABILITY_RULE,
        taker_only_inputs=EXP51_MECHANICS_INPUTS,
        atomic_bundle_features=BUNDLE_FEATURES,
        regime_window_bars=REGIME_WINDOW_BARS,
        arms=ARMS,
        append_only=True,
        backfill=False,
        historical_rewrite=False,
    )


def bundle_commitment():
    return digest(commitment_bundle())
