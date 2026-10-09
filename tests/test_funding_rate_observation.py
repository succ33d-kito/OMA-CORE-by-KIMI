import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

import core.scientific.premium_index_capture as capture
from core.scientific.funding_rate_observation import (
    CONTRACT,
    FEATURE,
    SEMANTIC_STATUS,
    append_verified_funding_rate_observation,
)
from core.scientific.prospective_receipts import (
    is_causally_available,
)


T = datetime(
    2026,
    10,
    9,
    10,
    0,
    0,
    tzinfo=timezone.utc,
)


def _json_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def verified_capture(
    tmp_path,
    *,
    name="capture",
    next_funding_delta=timedelta(hours=8),
):
    root = tmp_path / name
    root.mkdir()

    received = T + timedelta(seconds=1)
    available = T + timedelta(seconds=2)

    raw = {
        "symbol": "BTCUSDT",
        "markPrice": "60000.00",
        "indexPrice": "59990.00",
        "estimatedSettlePrice": "59995.00",
        "lastFundingRate": "-0.0001",
        "interestRate": "0.0001",
        "nextFundingTime": int(
            (
                T
                + next_funding_delta
            ).timestamp()
            * 1000
        ),
        "time": int(
            T.timestamp() * 1000
        ),
    }

    raw_bytes = _json_bytes(raw)

    meta = {
        "schema":
            capture.SCHEMA,
        "source":
            capture.ENDPOINT,
        "request_url":
            capture.URL,
        "response_url":
            capture.URL,
        "instrument":
            "BTCUSDT",
        "venue":
            "Binance USDⓈ-M",
        "product":
            "linear perpetual",
        "role":
            "PILOT",
        "request_started_at":
            T.isoformat(),
        "received_at":
            received.isoformat(),
        "response_status":
            200,
        "content_type":
            "application/json",
        "content_length":
            str(len(raw_bytes)),
        "raw_sha256":
            hashlib.sha256(
                raw_bytes
            ).hexdigest(),
        "request_elapsed_seconds":
            1.0,
    }

    receipt_id = capture._commit(meta)

    ready = {
        "receipt_id":
            receipt_id,
        "available_at":
            available.isoformat(),
    }

    ready["provenance_sha256"] = (
        capture.digest(
            (
                receipt_id,
                ready["available_at"],
            )
        )
    )

    (root / "response.raw").write_bytes(
        raw_bytes
    )

    (root / "receipt.json").write_bytes(
        _json_bytes(meta)
    )

    (root / "available.json").write_bytes(
        _json_bytes(ready)
    )

    # Fixture itself must be accepted by the pre-existing trusted loader.
    observation = capture.load_premium(
        root
    )

    assert len(observation.receipts) == 1

    return (
        root,
        raw,
        received,
        available,
    )


def test_verified_capture_appends_causal_published_rate(
    tmp_path,
):
    (
        root,
        raw,
        received,
        capture_available,
    ) = verified_capture(tmp_path)

    ledger = tmp_path / "ledger.db"

    ledger_available = (
        capture_available
        + timedelta(seconds=1)
    )

    result = (
        append_verified_funding_rate_observation(
            ledger,
            root,
            clock=lambda:
                ledger_available,
        )
    )

    assert result["feature"] == FEATURE
    assert result["derived"] is False
    assert result["dependencies"] == []

    assert result["event_time"] == (
        T.isoformat()
    )

    assert result["source_metric_at"] == (
        T.isoformat()
    )

    assert result["received_at"] == (
        received.isoformat()
    )

    assert result["available_at"] == (
        ledger_available.isoformat()
    )

    assert (
        result["provenance"][
            "capture_available_at"
        ]
        == capture_available.isoformat()
    )

    assert (
        result["provenance"]["contract"]
        == CONTRACT
    )

    assert (
        result["provenance"][
            "semantic_status"
        ]
        == SEMANTIC_STATUS
    )

    assert result["payload"] == {
        "funding_rate":
            raw["lastFundingRate"],
        "mark_price":
            raw["markPrice"],
        "index_price":
            raw["indexPrice"],
        "exchange_at":
            T.isoformat(),
        "next_funding_at":
            (
                T
                + timedelta(hours=8)
            ).isoformat(),
    }

    assert is_causally_available(
        ledger,
        result["id"],
        ledger_available,
    )

    forbidden = {
        "funding_payment",
        "funding_cashflow",
        "realized_cost",
        "total_cost",
        "pnl",
        "outcome",
    }

    assert not (
        forbidden
        & set(result["payload"])
    )

    assert not (
        forbidden
        & set(result["provenance"])
    )


def test_verified_capture_adapter_is_idempotent(
    tmp_path,
):
    (
        root,
        _,
        _,
        capture_available,
    ) = verified_capture(tmp_path)

    ledger = tmp_path / "ledger.db"

    first = (
        append_verified_funding_rate_observation(
            ledger,
            root,
            clock=lambda:
                capture_available
                + timedelta(seconds=1),
        )
    )

    second = (
        append_verified_funding_rate_observation(
            ledger,
            root,
            clock=lambda:
                capture_available
                + timedelta(seconds=2),
        )
    )

    assert second == first


def test_invalid_next_funding_fails_before_persistence(
    tmp_path,
):
    (
        root,
        _,
        _,
        capture_available,
    ) = verified_capture(
        tmp_path,
        next_funding_delta=timedelta(0),
    )

    ledger = tmp_path / "ledger.db"

    with pytest.raises(
        ValueError,
        match="published funding-rate contract",
    ):
        append_verified_funding_rate_observation(
            ledger,
            root,
            clock=lambda:
                capture_available
                + timedelta(seconds=1),
        )

    assert not ledger.exists()


def test_raw_capture_tampering_fails_before_ledger(
    tmp_path,
):
    (
        root,
        _,
        _,
        capture_available,
    ) = verified_capture(tmp_path)

    raw_path = root / "response.raw"

    original = raw_path.read_bytes()

    tampered = original.replace(
        b'"markPrice":"60000.00"',
        b'"markPrice":"60000.01"',
        1,
    )

    assert tampered != original
    assert len(tampered) == len(original)

    raw_path.write_bytes(
        tampered
    )

    ledger = tmp_path / "ledger.db"

    with pytest.raises(
        ValueError,
        match="raw content hash mismatch",
    ):
        append_verified_funding_rate_observation(
            ledger,
            root,
            clock=lambda:
                capture_available
                + timedelta(seconds=1),
        )

    assert not ledger.exists()


def test_availability_tampering_fails_before_ledger(
    tmp_path,
):
    (
        root,
        _,
        _,
        capture_available,
    ) = verified_capture(tmp_path)

    ready_path = (
        root / "available.json"
    )

    ready = json.loads(
        ready_path.read_text(
            encoding="utf-8"
        )
    )

    ready["available_at"] = (
        capture_available
        + timedelta(seconds=10)
    ).isoformat()

    # Do not recompute provenance_sha256.
    ready_path.write_bytes(
        _json_bytes(ready)
    )

    ledger = tmp_path / "ledger.db"

    with pytest.raises(
        ValueError,
        match="availability/provenance mismatch",
    ):
        append_verified_funding_rate_observation(
            ledger,
            root,
            clock=lambda:
                capture_available
                + timedelta(seconds=11),
        )

    assert not ledger.exists()


def test_old_capture_is_not_backfilled(
    tmp_path,
):
    (
        root,
        _,
        _,
        _,
    ) = verified_capture(tmp_path)

    ledger = tmp_path / "ledger.db"

    with pytest.raises(
        ValueError,
        match="historical backfill",
    ):
        append_verified_funding_rate_observation(
            ledger,
            root,
            clock=lambda:
                T + timedelta(days=2),
        )

def test_ledger_admission_cannot_precede_verified_capture_availability(
    tmp_path,
):
    from core.scientific.prospective_receipts import (
        load_observations,
    )

    (
        root,
        _,
        received,
        capture_available,
    ) = verified_capture(tmp_path)

    ledger = tmp_path / "ledger.db"

    impossible_admission = (
        received
        + timedelta(milliseconds=500)
    )

    assert (
        impossible_admission
        < capture_available
    )

    with pytest.raises(
        ValueError,
        match=(
            "ledger admission precedes verified "
            "capture availability"
        ),
    ):
        append_verified_funding_rate_observation(
            ledger,
            root,
            clock=lambda:
                impossible_admission,
        )

    assert load_observations(
        ledger
    ) == {}


def test_ledger_admission_equal_to_capture_availability_is_valid(
    tmp_path,
):
    (
        root,
        _,
        _,
        capture_available,
    ) = verified_capture(tmp_path)

    ledger = tmp_path / "ledger.db"

    result = (
        append_verified_funding_rate_observation(
            ledger,
            root,
            clock=lambda:
                capture_available,
        )
    )

    assert (
        result["available_at"]
        == capture_available.isoformat()
    )

    assert (
        result["provenance"][
            "capture_available_at"
        ]
        == capture_available.isoformat()
    )

    assert is_causally_available(
        ledger,
        result["id"],
        capture_available,
    )
