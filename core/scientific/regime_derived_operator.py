"""Prospective Regime derived-snapshot producer for Experiment 51.

Fail-closed until an exactly-81-slot, role-authenticated, contiguous H1 Price
window naturally exists. It never scans history, never catches up, never repairs,
never replays and never emits a placeholder, UNKNOWN or neutral snapshot: before
readiness it writes nothing at all.

Candidate rule (no arbitrary "latest 81 rows"):
* primary candidate = ``floor(now, H1)`` — the most recent H1 boundary whose Price
  kline is closed (``event_time`` is the kline close and capture lands ~+4 min);
* bounded grace of exactly one slot: ``floor(now, H1) - 1H`` is considered only if
  the primary is not yet evidenced, so a delayed invocation cannot silently skip an
  opportunity. Nothing older than that is ever eligible, so no historical window can
  be admitted.

Determinism: the window certificate is taken at ``terminal + 5 min`` (the frozen
``S+5m`` raw cutoff of Experiment 51), not at the wall-clock instant of the run.
The same terminal therefore always yields the same certificate id and source, which
makes re-runs idempotent instead of duplicating snapshots.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

from .derived_snapshot_admission import (admit_regime, verify as verify_binding,
    REGIME_DERIVED_SCHEMA, REGIME_DERIVATION_RULE_HASH)
from .price_role_activation import ROLES
from .price_role_attestation import verified_price_role_attestation
from .prospective_receipts import observation_snapshot, snapshot_causally_available
from .regime_observation import _utc, INSTRUMENT, PRICE_FEATURE
from .role_price_window import SCHEMA as WINDOW_SCHEMA, certify_role_price_window

HOUR = timedelta(hours=1)
WINDOW_BARS = 81
WINDOW_CUTOFF_DELAY = timedelta(minutes=5)
GRACE_SLOTS = 1
SCHEMA = 'experiment51-regime-producer-v1'
DIAGNOSTIC_SCHEMA = 'experiment51-regime-producer-status-v1'

# Frozen binding from the qualified cut (must not drift).
# NOTE: the derived-snapshot schema hash was corrected on 2026-10-16 to a canonical
# (sorted) bundle-feature order; the earlier value depended on frozenset iteration
# order and therefore on PYTHONHASHSEED. regime/admission rule hashes are unchanged.
FROZEN_RULE_HASH = 'a3abeb1ad28f92af921464562fb37da587c0f4b01fd994b6ae81eb8bcab8d368'
FROZEN_SNAPSHOT_SCHEMA_HASH = 'f3b218c7da8510929a88ab56da041592282503b6aa8fcba624c4c2b47fef8faa'
FROZEN_ADMISSION_RULE_HASH = 'cea20f9ed9a60070f53cabe63eda25f007d32a011cd64cc461bc8a85c2319bcc'
FROZEN_WINDOW_SCHEMA = 'price-81h-role-certificate-v1'

REASONS = ('PRICE_HISTORY_NOT_READY', 'PRICE_GAP', 'PRICE_ROLE_NOT_AUTHENTICATED',
           'AUTHORITY_MISMATCH', 'ROLE_MISMATCH', 'RAW_INPUT_NOT_CAUSAL', 'WINDOW_CONFLICT',
           'DERIVATION_RULE_MISMATCH', 'ALREADY_ADMITTED', 'NOT_YET_CAUSAL')

# Non-failure statuses: not-ready is the expected fail-closed state before 81 slots.
OK_STATUSES = ('PRODUCED', 'ALREADY_ADMITTED', 'NOT_READY')

_WINDOW_MAP = (
    ('exactly 81 unique prices required', 'PRICE_HISTORY_NOT_READY'),
    ('ordered contiguous H1 prices required', 'PRICE_GAP'),
    ('missing, late or invalid role attestation', 'PRICE_ROLE_NOT_AUTHENTICATED'),
    ('role price certificate mismatch', 'AUTHORITY_MISMATCH'),
    ('certificate reconstruction failed', 'AUTHORITY_MISMATCH'),
    ('raw BTCUSDT price dependency required', 'RAW_INPUT_NOT_CAUSAL'),
    ('wrong price contract', 'RAW_INPUT_NOT_CAUSAL'),
    ('price unavailable at cutoff', 'RAW_INPUT_NOT_CAUSAL'),
    ('price capture is not contemporaneous', 'RAW_INPUT_NOT_CAUSAL'),
    ('exact H1 boundary required', 'RAW_INPUT_NOT_CAUSAL'),
    ('conflicting price in certified interval', 'WINDOW_CONFLICT'),
)


def _now():
    return datetime.now(timezone.utc)


def floor_hour(moment):
    return _utc(moment).replace(minute=0, second=0, microsecond=0)


def candidate_slot(now):
    """Primary prospective terminal slot: the current closed H1 boundary."""
    return floor_hour(now)


def candidates(now):
    """Primary candidate plus the bounded one-slot grace. Never older, never a scan."""
    primary = floor_hour(now)
    return tuple(primary - index * HOUR for index in range(GRACE_SLOTS + 1))


def window_cutoff(terminal):
    """Deterministic per-terminal cutoff: the frozen Experiment 51 S+5m raw cutoff."""
    return _utc(terminal) + WINDOW_CUTOFF_DELAY


def _window_map(error):
    text = str(error)
    for needle, reason in _WINDOW_MAP:
        if needle in text:
            return reason
    return 'DERIVATION_RULE_MISMATCH'


class RegimeDerivedOperatorV1:
    """Stateless (source-derived) prospective producer: no private streak state."""

    def __init__(self, root):
        self.root = Path(root)

    # -- state access -------------------------------------------------------
    @property
    def ledger(self):
        return self.root / 'observations.db'

    def config(self):
        path = self.root / 'config.json'
        if not path.exists():
            raise ValueError('AUTHORITY_MISMATCH')
        return json.loads(path.read_text(encoding='utf-8'))

    def role(self):
        return self.config().get('dataset_role')

    def _known(self):
        # Missing ledger is missing evidence: fail closed without creating any file.
        if not self.ledger.exists():
            return {}
        known, _ = observation_snapshot(self.ledger, read_only=True)
        return known

    def _prices(self, known):
        return [row for row in known.values()
                if row.get('feature') == PRICE_FEATURE and row.get('derived') is False
                and row.get('instrument') == INSTRUMENT and row.get('available_at') is not None]

    # -- window construction ------------------------------------------------
    def window_status(self, known, terminal, role, cutoff):
        """Return (ids, reason). Never invents a slot; missing means not ready."""
        prices = self._prices(known)
        if len(prices) < WINDOW_BARS:
            return None, 'PRICE_HISTORY_NOT_READY'
        by_slot = {}
        for row in prices:
            by_slot.setdefault(_utc(row['event_time']), []).append(row)
        first_slot = min(by_slot)
        ids = []
        for offset in range(WINDOW_BARS - 1, -1, -1):
            slot = _utc(terminal) - offset * HOUR
            rows = by_slot.get(slot, [])
            if not rows:
                return None, 'PRICE_HISTORY_NOT_READY' if slot < first_slot else 'PRICE_GAP'
            if len(rows) > 1:
                return None, 'WINDOW_CONFLICT'
            row = rows[0]
            if not snapshot_causally_available(known, row['id'], cutoff):
                return None, 'RAW_INPUT_NOT_CAUSAL'
            if verified_price_role_attestation(known, row, role, cutoff) is None:
                return None, 'PRICE_ROLE_NOT_AUTHENTICATED'
            ids.append(row['id'])
        return tuple(ids), 'OK'

    def current_streak(self, known, role, cutoff):
        """Consecutive role-authenticated slots ending at the newest evidenced slot."""
        prices = sorted(self._prices(known), key=lambda r: _utc(r['event_time']))
        streak, previous = 0, None
        for row in prices:
            slot = _utc(row['event_time'])
            authenticated = (snapshot_causally_available(known, row['id'], cutoff)
                             and verified_price_role_attestation(known, row, role, cutoff) is not None)
            if authenticated and previous is not None and slot - previous == HOUR:
                streak += 1
            else:
                streak = 1 if authenticated else 0
            previous = slot if authenticated else None
        return streak, (prices[-1]['event_time'] if prices else None)

    # -- binding guard ------------------------------------------------------
    def _binding_ok(self):
        try:
            binding = verify_binding()
        except Exception as error:                      # noqa: BLE001 - fail closed
            return False, str(error)
        if (binding['regime_derivation_rule_hash'] != FROZEN_RULE_HASH
                or binding['derived_snapshot_schema_hash'] != FROZEN_SNAPSHOT_SCHEMA_HASH
                or binding['derived_admission_rule_hash'] != FROZEN_ADMISSION_RULE_HASH
                or WINDOW_SCHEMA != FROZEN_WINDOW_SCHEMA):
            return False, 'frozen binding drift'
        return True, 'OK'

    # -- operations ---------------------------------------------------------
    def once(self, *, now=None, clock=None):
        """One prospective attempt. Writes nothing unless every gate passes."""
        moment = _utc(now if now is not None else _now())
        tick = clock if clock is not None else (lambda: moment)
        tried = candidates(moment)
        base = dict(schema=SCHEMA, observed_at=moment.isoformat(), window_bars=WINDOW_BARS,
                    candidates=[slot.isoformat() for slot in tried], regime_snapshot_created=False)
        ok, detail = self._binding_ok()
        if not ok:
            return {**base, 'status': 'REJECTED', 'reason': 'DERIVATION_RULE_MISMATCH', 'detail': detail}
        try:
            role = self.role()
        except Exception as error:                      # noqa: BLE001 - fail closed
            return {**base, 'status': 'REJECTED', 'reason': 'AUTHORITY_MISMATCH', 'detail': str(error)}
        if role not in ROLES:
            return {**base, 'status': 'REJECTED', 'reason': 'ROLE_MISMATCH', 'detail': str(role)}
        known = self._known()
        streak, newest = self.current_streak(known, role, moment)
        base.update(dataset_role=role, price_current_streak=streak,
                    price_slots_to_81=max(0, WINDOW_BARS - streak), newest_evidenced_slot=newest)
        first_reason = None
        for terminal in tried:
            cutoff = window_cutoff(terminal)
            if moment < cutoff:
                first_reason = first_reason or 'NOT_YET_CAUSAL'
                continue
            ids, reason = self.window_status(known, terminal, role, cutoff)
            if ids is None:
                first_reason = first_reason or reason
                continue
            attempt = {**base, 'candidate_slot': terminal.isoformat()}
            try:
                certificate = certify_role_price_window(self.ledger, receipt_ids=ids,
                                                        dataset_role=role, cutoff=cutoff)
            except Exception as error:                  # noqa: BLE001 - fail closed, no write
                first_reason = first_reason or _window_map(error)
                continue
            source = 'oma://scientific/' + REGIME_DERIVED_SCHEMA + '/' + certificate['certificate_id']
            existing = [row for row in known.values() if row.get('source') == source]
            attempt.update(certificate_id=certificate['certificate_id'],
                           window_cutoff=cutoff.isoformat(),
                           window_first_slot=certificate['first_event_time'],
                           window_last_slot=certificate['last_event_time'])
            if existing:
                return {**attempt, 'status': 'ALREADY_ADMITTED', 'reason': 'ALREADY_ADMITTED',
                        'regime_id': existing[0]['id']}
            outcome = admit_regime(self.ledger, certificate, dataset_role=role, clock=tick)
            if not outcome.admitted:
                first_reason = first_reason or outcome.reason
                continue
            return {**attempt, 'status': 'PRODUCED', 'reason': 'OK',
                    'regime_id': outcome.observation_id, 'regime_snapshot_created': True}
        return {**base, 'status': 'NOT_READY', 'reason': first_reason or 'PRICE_HISTORY_NOT_READY'}

    def status(self, *, now=None):
        """Read-only diagnostics: never writes, never derives."""
        moment = _utc(now if now is not None else _now())
        tried = candidates(moment)
        payload = dict(schema=DIAGNOSTIC_SCHEMA, observed_at=moment.isoformat(),
                       window_bars=WINDOW_BARS, candidates=[slot.isoformat() for slot in tried],
                       grace_slots=GRACE_SLOTS, window_cutoff_delay_seconds=int(WINDOW_CUTOFF_DELAY.total_seconds()))
        try:
            role = self.role()
        except Exception:                               # noqa: BLE001 - diagnostics only
            return {**payload, 'status': 'REJECTED', 'reason': 'AUTHORITY_MISMATCH'}
        known = self._known()
        streak, newest = self.current_streak(known, role, moment)
        detail = {}
        for terminal in tried:
            cutoff = window_cutoff(terminal)
            ids, reason = self.window_status(known, terminal, role, cutoff)
            detail[terminal.isoformat()] = dict(cutoff=cutoff.isoformat(),
                                                eligible=ids is not None,
                                                reason='OK' if ids is not None else reason)
        primary = tried[0].isoformat()
        admitted = [row for row in known.values() if row.get('feature') == 'Regime/Role/v2']
        payload.update(dataset_role=role, price_current_streak=streak,
                       price_slots_to_81=max(0, WINDOW_BARS - streak), newest_evidenced_slot=newest,
                       primary_candidate=primary, candidate_detail=detail,
                       current_candidate_eligible=detail[primary]['eligible'],
                       current_candidate_reason=detail[primary]['reason'],
                       regime_snapshots_admitted=len(admitted),
                       latest_regime_id=(sorted(admitted, key=lambda r: r['event_time'])[-1]['id']
                                         if admitted else None))
        return payload


def main(root, *, command='once', now=None, stream=None):
    """Deterministic CLI body; returns the process exit code."""
    import sys
    operator = RegimeDerivedOperatorV1(root)
    if command == 'status':
        output = operator.status(now=now)
        code = 0
    else:
        output = operator.once(now=now)
        code = 0 if output['status'] in OK_STATUSES else 1
    (stream or sys.stdout).write(json.dumps(output, sort_keys=True, separators=(',', ':')) + '\n')
    return code
