"""Role-authenticated Regime v2: additive derived observations, never raw input."""
from datetime import datetime, timezone
from core.market_mechanics.state import build_market_state
from core.market_mechanics.regime import classify_regime
from .role_price_window import _build, verify_role_price_window
from .regime_observation import _utc
from .prospective_receipts import append_observation, observation_snapshot, observation_hash, snapshot_causally_available

FEATURE = "Regime/Role/v2"
CONTRACT = "causal-role-regime-v2"
STATUS = "DESCRIPTIVE_HEURISTIC_NOT_PROBABILITY"


def _derive(known, certificate):
    cert = _build(known, certificate["receipt_ids"], certificate["dataset_role"], certificate["cutoff"])
    if certificate != cert:
        raise ValueError("certificate reconstruction failed")
    rows = [known[i] for i in cert["receipt_ids"]]
    bars = [{"time": _utc(r["payload"]["time"]), **{k:r["payload"][k] for k in ("open","high","low","close","volume")}} for r in rows]
    state = build_market_state("BTCUSDT", bars, source_id=cert["certificate_id"],
        observed_at=_utc(cert["input_available_at"]), as_of=_utc(cert["cutoff"]),
        timeframe_seconds=3600, lookback=20)
    regime = classify_regime(state)
    payload = {"regime": regime.to_dict(), "market_state": state.to_dict()}
    provenance = {"contract": CONTRACT, "dataset_role": cert["dataset_role"],
        "semantic_status": STATUS, "certificate": cert,
        "regime_method": regime.method, "market_state_algorithm": state.algorithm_version}
    # Normalize immutable tuple fields to their actual JSON storage representation.
    import json
    payload = json.loads(json.dumps(payload, allow_nan=False))
    return payload, provenance, cert["receipt_ids"] + cert["attestation_ids"]


def append_causal_regime(ledger, certificate, *, clock=None):
    cert = verify_role_price_window(ledger, certificate)
    known, _ = observation_snapshot(ledger, read_only=True)
    payload, provenance, dependencies = _derive(known, cert)
    now = _utc(clock() if clock else datetime.now(timezone.utc))
    if now < _utc(cert["cutoff"]):
        raise ValueError("computation precedes input cutoff")
    source = "oma://scientific/" + CONTRACT + "/" + cert["certificate_id"]
    # Validate replay before the generic writer's payload-only idempotence shortcut.
    for row in known.values():
        if row["source"] == source:
            validate_causal_regime(known, row, dataset_role=cert["dataset_role"], cutoff=now)
            return row
    return append_observation(ledger, source=source, instrument="BTCUSDT", feature=FEATURE,
        event_time=_utc(cert["last_event_time"]), source_metric_at=_utc(cert["last_event_time"]),
        received_at=now, payload=payload, provenance=provenance,
        dependencies=dependencies, derived=True, clock=lambda: now)


def validate_causal_regime(known, row, *, dataset_role, cutoff):
    if row.get("feature") != FEATURE or row.get("instrument") != "BTCUSDT" or row.get("derived") is not True:
        raise ValueError("wrong derived regime contract")
    if known.get(row["id"]) != row:
        raise ValueError("regime is not the exact persisted row")
    cert = row["provenance"]["certificate"]
    if cert["dataset_role"] != dataset_role:
        raise ValueError("regime dataset role mismatch")
    payload, provenance, dependencies = _derive(known, cert)
    source = "oma://scientific/" + CONTRACT + "/" + cert["certificate_id"]
    expected_id = observation_hash([source, "BTCUSDT", FEATURE, cert["last_event_time"],
        cert["last_event_time"], dependencies, True])
    if (row["id"] != expected_id or row["source"] != source or row["payload"] != payload
            or row["payload_hash"] != observation_hash(payload) or row["provenance"] != provenance
            or row["dependencies"] != dependencies or row["event_time"] != cert["last_event_time"]
            or row["source_metric_at"] != cert["last_event_time"]
            or _utc(row["computed_at"]) < _utc(cert["cutoff"])
            or not snapshot_causally_available(known, row["id"], _utc(cutoff))):
        raise ValueError("derived regime failed reconstruction or causal availability")
    return row


def load_causal_regimes(ledger, *, dataset_role, as_of):
    from .price_role_activation import ROLES
    if dataset_role not in ROLES:
        raise ValueError("explicit supported dataset role required")
    cutoff = _utc(as_of)
    known, _ = observation_snapshot(ledger, read_only=True)
    selected = []
    for row in known.values():
        if row["feature"] != FEATURE or row["available_at"] is None or _utc(row["available_at"]) > cutoff:
            continue
        if row["provenance"].get("dataset_role") != dataset_role:
            continue
        selected.append(validate_causal_regime(known, row, dataset_role=dataset_role, cutoff=cutoff))
    return tuple(sorted(selected, key=lambda r:(r["event_time"],r["id"])))
