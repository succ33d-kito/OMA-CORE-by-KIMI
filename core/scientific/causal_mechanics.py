"""Descriptive Mechanics v1 from authenticated as-of inputs; no inferred flow."""
from datetime import datetime, timezone
import json
from math import isfinite
from .causal_observation_snapshot import load_causal_snapshot
from .causal_latent_context import project_latent_context
from .causal_regime import validate_causal_regime
from .price_role_activation import ROLES
from .regime_observation import _utc
from .prospective_receipts import observation_snapshot, observation_hash, append_observation

FEATURE = "Mechanics/Descriptive/v1"
CONTRACT = "causal-descriptive-mechanics-v1"
UNSUPPORTED = ("open_interest_change", "aggressor_flow", "aggressor_imbalance", "trade_intensity",
    "average_trade_size", "resting_liquidity", "absorption", "participant_identity", "participant_intent",
    "capital_flow", "realized_funding_payment")


def build_causal_mechanics(ledger, *, dataset_role, cutoff, regime_id=None):
    if dataset_role not in ROLES:
        raise ValueError("explicit supported dataset role required")
    cutoff = _utc(cutoff)
    snapshot = load_causal_snapshot(ledger, instrument="BTCUSDT", as_of=cutoff, dataset_role=dataset_role)
    known, _ = observation_snapshot(ledger, read_only=True)
    values, dependencies = {}, []
    for item in snapshot.observations:
        payload = json.loads(item.payload_json)
        dependencies.append(item.id)
        if item.role_attestation_json is not None:
            dependencies.append(json.loads(item.role_attestation_json)["id"])
        if item.feature == "Price/OHLCV":
            value = {k:payload[k] for k in ("open","high","low","close","volume")}
        else:
            field = "funding_rate" if item.feature == "FundingRate/Published" else "value"
            value = float(payload[field])
            if not isfinite(value):
                raise ValueError("non-finite factual input")
        values[item.feature] = {"value": value, "source_id": item.id,
            "source_metric_at": item.source_metric_at.isoformat(),
            "available_at": item.available_at.isoformat(), "semantics": item.feature}
    regime = None
    if regime_id is not None:
        row = known.get(regime_id)
        if row is None:
            raise ValueError("missing derived regime dependency")
        validate_causal_regime(known, row, dataset_role=dataset_role, cutoff=cutoff)
        dependencies.append(regime_id)
        regime = {"source_id": regime_id, "available_at": row["available_at"],
            "regime": row["payload"]["regime"], "market_state": row["payload"]["market_state"]}
    dependencies = sorted(set(dependencies))
    result = {"schema": CONTRACT, "dataset_role": dataset_role, "cutoff": cutoff.isoformat(),
        "snapshot_id": snapshot.snapshot_id, "raw_values": values,
        "latent_context": project_latent_context(snapshot).to_dict(), "regime": regime,
        "dependencies": dependencies, "missing_features": list(snapshot.missing_features),
        "unknown_dimensions": {key:None for key in UNSUPPORTED},
        "semantic_status": "DESCRIPTIVE_ONLY_NOT_VALIDATED",
        "input_available_at": max([v["available_at"] for v in values.values()] + ([regime["available_at"]] if regime else []), default=None)}
    result = json.loads(json.dumps(result, allow_nan=False))
    return {**result, "mechanics_id": observation_hash(result)}


def append_causal_mechanics(ledger, *, dataset_role, cutoff, regime_id=None, clock=None):
    payload = build_causal_mechanics(ledger, dataset_role=dataset_role, cutoff=cutoff, regime_id=regime_id)
    if not payload["dependencies"]:
        raise ValueError("no causal evidence; cannot persist empty mechanics")
    now = _utc(clock() if clock else datetime.now(timezone.utc))
    if now < _utc(cutoff):
        raise ValueError("computation precedes input cutoff")
    known, _ = observation_snapshot(ledger, read_only=True)
    source = "oma://scientific/" + CONTRACT + "/" + payload["mechanics_id"]
    for row in known.values():
        if row["source"] == source:
            validate_causal_mechanics(ledger, row, dataset_role=dataset_role, cutoff=now)
            return row
    event = max(_utc(known[i]["event_time"]) for i in payload["dependencies"])
    return append_observation(ledger, source=source, instrument="BTCUSDT", feature=FEATURE,
        event_time=event, source_metric_at=event, received_at=now, payload=payload,
        provenance={"contract": CONTRACT, "dataset_role": dataset_role},
        dependencies=payload["dependencies"], derived=True, clock=lambda:now)


def validate_causal_mechanics(ledger, row, *, dataset_role, cutoff):
    if row.get("feature") != FEATURE or row.get("derived") is not True or row.get("instrument") != "BTCUSDT":
        raise ValueError("wrong mechanics contract")
    original = row["payload"]
    if not isinstance(original, dict) or not {"dataset_role", "cutoff", "regime"} <= original.keys():
        raise ValueError("incomplete mechanics payload")
    if original["dataset_role"] != dataset_role:
        raise ValueError("mechanics role mismatch")
    expected = build_causal_mechanics(ledger, dataset_role=dataset_role, cutoff=original["cutoff"],
        regime_id=original["regime"]["source_id"] if original["regime"] else None)
    known, _ = observation_snapshot(ledger, read_only=True)
    if known.get(row["id"]) != row:
        raise ValueError("mechanics is not the exact persisted row")
    source = "oma://scientific/" + CONTRACT + "/" + expected["mechanics_id"]
    event = max(_utc(known[i]["event_time"]) for i in expected["dependencies"]).isoformat()
    identity = observation_hash([source,"BTCUSDT",FEATURE,event,event,expected["dependencies"],True])
    if (row["id"] != identity or row["source"] != source or row["payload"] != expected
            or row["payload_hash"] != observation_hash(expected)
            or row["provenance"] != {"contract":CONTRACT,"dataset_role":dataset_role}
            or row["dependencies"] != expected["dependencies"]
            or row["event_time"] != event or row["source_metric_at"] != event
            or _utc(row["computed_at"]) < _utc(expected["cutoff"])
            or not (_utc(event) <= _utc(row["received_at"]) <= _utc(row["computed_at"]) <= _utc(row["available_at"]) <= _utc(cutoff))
            or _utc(row["available_at"]) != max([_utc(row["computed_at"]), *[_utc(known[i]["available_at"]) for i in expected["dependencies"]]])):
        raise ValueError("mechanics reconstruction or availability failed")
    return row
