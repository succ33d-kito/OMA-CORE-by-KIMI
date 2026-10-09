import json
from datetime import datetime, timedelta, timezone

import pytest

from core.scientific.prospective_receipts import (
    append_observation,
    is_causally_available,
    observation_hash,
    observation_snapshot,
)

from core.scientific.regime_observation import (
    append_certified_regime_observation,
)


T = datetime(2026, 1, 1, tzinfo=timezone.utc)
SOURCE = "https://fapi.binance.com/fapi/v1/klines"
CONTRACT = "binance-usdm-h1-rest-v1"


def raw_price(ledger, index):
    opened = T + timedelta(hours=index)
    closed = opened + timedelta(hours=1)

    opened_ms = int(opened.timestamp() * 1000)
    close_ms = int(closed.timestamp() * 1000)

    price = 100.0 + index * 0.1

    row = [
        opened_ms,
        str(price),
        str(price + 1.0),
        str(price - 1.0),
        str(price + 0.2),
        "10.0",
        close_ms - 1,
    ]

    received = closed + timedelta(seconds=3)

    provenance = {
        "contract": CONTRACT,
        "bar_closed": True,
        "raw_klines": json.dumps([row]),
        "raw_server_time": json.dumps(
            {"serverTime": close_ms}
        ),
        "server_received_at": (
            closed + timedelta(seconds=1)
        ).isoformat(),
        "klines_requested_at": (
            closed + timedelta(seconds=2)
        ).isoformat(),
    }

    payload = {
        "time": opened.isoformat(),
        "open": price,
        "high": price + 1.0,
        "low": price - 1.0,
        "close": price + 0.2,
        "volume": 10.0,
        "open_time_ms": opened_ms,
        "close_time_ms": close_ms - 1,
    }

    return append_observation(
        ledger,
        source=SOURCE,
        instrument="BTCUSDT",
        feature="Price/OHLCV",
        event_time=closed,
        source_metric_at=closed - timedelta(milliseconds=1),
        received_at=received,
        payload=payload,
        provenance=provenance,
        clock=lambda: closed + timedelta(seconds=4),
    )


def certified_window(tmp_path):
    ledger = tmp_path / "receipts.db"

    rows = [
        raw_price(ledger, i)
        for i in range(81)
    ]

    known, prefixes = observation_snapshot(
        ledger,
        read_only=True,
    )

    ids = tuple(row["id"] for row in rows)

    selected = [
        known[identity]
        for identity in ids
    ]

    certificate = {
        "schema": "price-81h-certificate-v1",
        "instrument": "BTCUSDT",
        "feature": "Price/OHLCV",
        "first_event_time": selected[0]["event_time"],
        "last_event_time": selected[-1]["event_time"],
        "number_of_bars": 81,
        "receipt_ids": list(ids),
        "ledger_head": prefixes[-1],
        "ledger_observation_count": len(known),
        "certified_set_hash": observation_hash(selected),
        "certified_at": (
            T + timedelta(hours=81, seconds=5)
        ).isoformat(),
        "contract": CONTRACT,
        "causal_gate_code_hash": "fixture-causal-gate",
        "continuity_code_hash": "fixture-continuity",
        "gaps": 0,
        "conflicts": 0,
        "historical_backfill": False,
    }

    return ledger, certificate


def test_certified_regime_is_causal_and_derived(tmp_path):
    ledger, certificate = certified_window(tmp_path)

    computed = T + timedelta(hours=81, seconds=10)

    result = append_certified_regime_observation(
        ledger,
        certificate,
        clock=lambda: computed,
    )

    assert result["feature"] == "Regime"
    assert result["instrument"] == "BTCUSDT"
    assert result["derived"] is True
    assert len(result["dependencies"]) == 81

    assert result["payload"]["method"] == (
        "er20-vol20-vs-prior60-v1"
    )

    assert result["provenance"]["semantic_status"] == (
        "DESCRIPTIVE_HEURISTIC_NOT_PROBABILITY"
    )

    assert result["available_at"] == computed.isoformat()

    assert is_causally_available(
        ledger,
        result["id"],
        computed,
    )


def test_certified_regime_is_idempotent(tmp_path):
    ledger, certificate = certified_window(tmp_path)

    first = append_certified_regime_observation(
        ledger,
        certificate,
        clock=lambda: T + timedelta(hours=81, seconds=10),
    )

    second = append_certified_regime_observation(
        ledger,
        certificate,
        clock=lambda: T + timedelta(hours=81, seconds=11),
    )

    assert second["id"] == first["id"]
    assert second["payload_hash"] == first["payload_hash"]

    known, _ = observation_snapshot(
        ledger,
        read_only=True,
    )

    assert len(known) == 82


def test_tampered_certificate_hash_fails_closed(tmp_path):
    ledger, certificate = certified_window(tmp_path)

    certificate["certified_set_hash"] = "0" * 64

    with pytest.raises(
        ValueError,
        match="certificate set hash mismatch",
    ):
        append_certified_regime_observation(
            ledger,
            certificate,
            clock=lambda: T + timedelta(hours=81, seconds=10),
        )


def test_reordered_receipts_fail_closed(tmp_path):
    ledger, certificate = certified_window(tmp_path)

    certificate["receipt_ids"][0], certificate["receipt_ids"][1] = (
        certificate["receipt_ids"][1],
        certificate["receipt_ids"][0],
    )

    with pytest.raises(ValueError):
        append_certified_regime_observation(
            ledger,
            certificate,
            clock=lambda: T + timedelta(hours=81, seconds=10),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("gaps", 1),
        ("conflicts", 1),
        ("historical_backfill", True),
        ("number_of_bars", 80),
    ],
)
def test_certificate_safety_gates_fail_closed(
    tmp_path,
    field,
    value,
):
    ledger, certificate = certified_window(tmp_path)

    certificate[field] = value

    with pytest.raises(ValueError):
        append_certified_regime_observation(
            ledger,
            certificate,
            clock=lambda: T + timedelta(hours=81, seconds=10),
        )
