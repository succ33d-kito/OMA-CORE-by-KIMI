"""Additive exact-81H, role-authenticated certificate; no capture or backfill."""
import json
from datetime import datetime, timedelta

from .price_role_activation import ROLES
from .price_role_attestation import verified_price_role_attestation
from .prospective_receipts import observation_hash, observation_snapshot, snapshot_causally_available
from .regime_observation import _utc, INSTRUMENT, PRICE_FEATURE, PRICE_CONTRACT

SCHEMA = "price-81h-role-certificate-v1"


def _build(known, receipt_ids, dataset_role, cutoff):
    cutoff = _utc(cutoff)
    ids = tuple(receipt_ids)
    if dataset_role not in ROLES:
        raise ValueError("explicit supported dataset role required")
    if len(ids) != 81 or len(set(ids)) != 81:
        raise ValueError("exactly 81 unique prices required")
    rows, attestations, times = [], [], []
    for identity in ids:
        row = known.get(identity)
        if not row or row.get("derived") is not False or row.get("instrument") != INSTRUMENT or row.get("feature") != PRICE_FEATURE:
            raise ValueError("raw BTCUSDT price dependency required")
        if row.get("provenance", {}).get("contract") != PRICE_CONTRACT:
            raise ValueError("wrong price contract")
        if not snapshot_causally_available(known, identity, cutoff):
            raise ValueError("price unavailable at cutoff")
        attestation = verified_price_role_attestation(known, row, dataset_role, cutoff)
        if attestation is None:
            raise ValueError("missing, late or invalid role attestation")
        event = _utc(row["event_time"])
        if event.minute or event.second or event.microsecond:
            raise ValueError("exact H1 boundary required")
        provenance = row["provenance"]
        server_time = datetime.fromtimestamp(
            json.loads(provenance["raw_server_time"])["serverTime"] / 1000,
            tz=event.tzinfo,
        )
        for timestamp in (row["received_at"], provenance["klines_requested_at"], server_time):
            if _utc(timestamp).replace(minute=0, second=0, microsecond=0) != event:
                raise ValueError("price capture is not contemporaneous")
        rows.append(row)
        attestations.append(attestation)
        times.append(event)
    if any(b-a != timedelta(hours=1) for a,b in zip(times,times[1:])):
        raise ValueError("ordered contiguous H1 prices required")
    for row in known.values():
        if (row.get("feature") == PRICE_FEATURE and row.get("instrument") == INSTRUMENT
                and row.get("derived") is False and row.get("available_at") is not None
                and _utc(row["available_at"]) <= cutoff
                and times[0] <= _utc(row["event_time"]) <= times[-1]
                and row["id"] not in ids):
            raise ValueError("conflicting price in certified interval")
    result = {
        "schema": SCHEMA, "instrument": INSTRUMENT, "contract": PRICE_CONTRACT,
        "dataset_role": dataset_role, "cutoff": cutoff.isoformat(),
        "receipt_ids": list(ids), "attestation_ids": [r["id"] for r in attestations],
        "price_commitment": observation_hash(rows),
        "attestation_commitment": observation_hash(attestations),
        "first_event_time": times[0].isoformat(), "last_event_time": times[-1].isoformat(),
        "input_available_at": max(_utc(r["available_at"]) for r in rows+attestations).isoformat(),
        "number_of_bars": 81, "gaps": 0, "conflicts": 0,
        "authorization_claim": "authorization strictly precedes earliest persisted capture evidence",
    }
    return {**result, "certificate_id": observation_hash(result)}


def certify_role_price_window(ledger, *, receipt_ids, dataset_role, cutoff):
    known, _ = observation_snapshot(ledger, read_only=True)
    return _build(known, receipt_ids, dataset_role, cutoff)


def verify_role_price_window(ledger, certificate):
    """Rebuild from authenticated ledger, never trust caller hashes or role labels."""
    if type(certificate) is not dict:
        raise TypeError("certificate must be a dict")
    expected = certify_role_price_window(
        ledger, receipt_ids=certificate.get("receipt_ids", ()),
        dataset_role=certificate.get("dataset_role"), cutoff=certificate.get("cutoff"),
    )
    if certificate != expected:
        raise ValueError("role price certificate mismatch")
    return expected
