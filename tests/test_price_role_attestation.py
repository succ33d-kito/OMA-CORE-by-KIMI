from pathlib import Path
from datetime import datetime, timedelta, timezone
import json

import pytest

import core.scientific.price_role_activation as activation
import core.scientific.price_role_attestation as attestation

from core.scientific.price_role_activation import activate
from core.scientific.price_role_attestation import (
    attest_price_observation,
    authorize_capture,
    load_authorization,
    price_role_authenticated,
    verified_price_role_attestation,
)
from core.scientific.prospective_receipts import (
    append_observation,
    observation_snapshot,
)


T = datetime(
    2026,
    10,
    11,
    18,
    0,
    tzinfo=timezone.utc,
)


def repo_root():
    return Path(__file__).resolve().parents[1]


def create_activation(
    tmp_path,
    monkeypatch,
    role="PILOT",
    name="price-role",
):
    monkeypatch.setattr(
        activation,
        "_now",
        lambda: T - timedelta(minutes=2),
    )

    state = tmp_path / name

    activate(
        state_root=state,
        repo_root=repo_root(),
        dataset_role=role,
    )

    return state


def append_price(ledger):
    start = int(
        (T - timedelta(hours=1)).timestamp()
        * 1000
    )

    row = [
        start,
        "100",
        "101",
        "99",
        "100",
        "5",
        start + 3_599_999,
        "500",
        2,
        "2",
        "200",
        "0",
    ]

    return append_observation(
        ledger,
        source=(
            "https://fapi.binance.com"
            "/fapi/v1/klines"
        ),
        instrument="BTCUSDT",
        feature="Price/OHLCV",
        event_time=T,
        source_metric_at=T
        - timedelta(milliseconds=1),
        received_at=T + timedelta(seconds=2),
        payload={
            "time":
                (T - timedelta(hours=1))
                .isoformat(),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 5.0,
            "open_time_ms": start,
            "close_time_ms":
                start + 3_599_999,
        },
        provenance={
            "contract":
                "binance-usdm-h1-rest-v1",
            "bar_closed": True,
            "raw_server_time":
                json.dumps({
                    "serverTime":
                        int(T.timestamp() * 1000)
                }),
            "raw_klines":
                json.dumps([row]),
            "server_received_at":
                (
                    T + timedelta(seconds=1)
                ).isoformat(),
            "klines_requested_at":
                (
                    T + timedelta(seconds=1)
                ).isoformat(),
        },
        clock=lambda:
            T + timedelta(seconds=3),
    )


def authorize(state, monkeypatch, when=None):
    when = (
        T + timedelta(milliseconds=250)
        if when is None
        else when
    )

    monkeypatch.setattr(
        attestation,
        "_now",
        lambda: when,
    )

    return authorize_capture(
        state,
        repo_root=repo_root(),
        expected_event_time=T,
    )


def test_price_role_attestation_round_trip(
    tmp_path,
    monkeypatch,
):
    state = create_activation(
        tmp_path,
        monkeypatch,
    )

    authorization = authorize(
        state,
        monkeypatch,
    )

    ledger = tmp_path / "price-role.db"
    price = append_price(ledger)

    monkeypatch.setattr(
        attestation,
        "_now",
        lambda:
            T + timedelta(seconds=4),
    )

    role_row = attest_price_observation(
        state,
        ledger,
        repo_root=repo_root(),
        slot_id=authorization["slot_id"],
        observation_id=price["id"],
    )

    rows, _ = observation_snapshot(
        ledger,
        read_only=True,
    )

    assert role_row["derived"] is True
    assert role_row["dependencies"] == [
        price["id"]
    ]
    assert (
        role_row["payload"]["dataset_role"]
        == "PILOT"
    )

    assert price_role_authenticated(
        rows,
        rows[price["id"]],
        "PILOT",
        T + timedelta(seconds=5),
    )

    assert not price_role_authenticated(
        rows,
        rows[price["id"]],
        "DISCOVERY",
        T + timedelta(seconds=5),
    )

    assert (
        verified_price_role_attestation(
            rows,
            rows[price["id"]],
            "PILOT",
            T + timedelta(seconds=5),
        )["id"]
        == role_row["id"]
    )

    assert (
        "dataset_role"
        not in rows[price["id"]]["provenance"]
    )


def test_price_without_pre_capture_authorization_cannot_be_attested(
    tmp_path,
    monkeypatch,
):
    state = create_activation(
        tmp_path,
        monkeypatch,
    )

    ledger = tmp_path / "price-no-auth.db"
    price = append_price(ledger)

    monkeypatch.setattr(
        attestation,
        "_now",
        lambda:
            T + timedelta(seconds=4),
    )

    with pytest.raises(
        ValueError,
        match="authorization not found",
    ):
        attest_price_observation(
            state,
            ledger,
            repo_root=repo_root(),
            slot_id="0" * 64,
            observation_id=price["id"],
        )


def test_post_capture_authorization_fails_closed(
    tmp_path,
    monkeypatch,
):
    state = create_activation(
        tmp_path,
        monkeypatch,
    )

    ledger = tmp_path / "late-auth.db"
    price = append_price(ledger)

    authorization = authorize(
        state,
        monkeypatch,
        T + timedelta(seconds=2),
    )

    monkeypatch.setattr(
        attestation,
        "_now",
        lambda:
            T + timedelta(seconds=4),
    )

    with pytest.raises(
        ValueError,
        match="strictly precede earliest persisted capture evidence",
    ):
        attest_price_observation(
            state,
            ledger,
            repo_root=repo_root(),
            slot_id=authorization["slot_id"],
            observation_id=price["id"],
        )


def test_authorization_tamper_fails_closed(
    tmp_path,
    monkeypatch,
):
    state = create_activation(
        tmp_path,
        monkeypatch,
    )

    authorization = authorize(
        state,
        monkeypatch,
    )

    path = (
        state
        / "authorizations"
        / f"{authorization['slot_id']}.json"
    )

    body = json.loads(
        path.read_text(encoding="utf-8")
    )

    body["dataset_role"] = "DISCOVERY"

    path.write_text(
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_authorization(
            state,
            authorization["slot_id"],
            repo_root=repo_root(),
        )


def test_one_price_cannot_receive_two_dataset_roles(
    tmp_path,
    monkeypatch,
):
    pilot = create_activation(
        tmp_path,
        monkeypatch,
        role="PILOT",
        name="pilot-role",
    )

    discovery = create_activation(
        tmp_path,
        monkeypatch,
        role="DISCOVERY",
        name="discovery-role",
    )

    pilot_auth = authorize(
        pilot,
        monkeypatch,
        T + timedelta(milliseconds=200),
    )

    discovery_auth = authorize(
        discovery,
        monkeypatch,
        T + timedelta(milliseconds=300),
    )

    ledger = tmp_path / "single-role.db"
    price = append_price(ledger)

    monkeypatch.setattr(
        attestation,
        "_now",
        lambda:
            T + timedelta(seconds=4),
    )

    attest_price_observation(
        pilot,
        ledger,
        repo_root=repo_root(),
        slot_id=pilot_auth["slot_id"],
        observation_id=price["id"],
    )

    monkeypatch.setattr(
        attestation,
        "_now",
        lambda:
            T + timedelta(seconds=5),
    )

    with pytest.raises(
        ValueError,
        match="conflicting observation",
    ):
        attest_price_observation(
            discovery,
            ledger,
            repo_root=repo_root(),
            slot_id=discovery_auth["slot_id"],
            observation_id=price["id"],
        )


def test_authorization_equal_to_first_persisted_capture_evidence_fails_closed(
    tmp_path,
    monkeypatch,
):
    state = create_activation(
        tmp_path,
        monkeypatch,
    )

    authorization = authorize(
        state,
        monkeypatch,
        T + timedelta(seconds=1),
    )

    ledger = tmp_path / "equal-auth.db"
    price = append_price(ledger)

    monkeypatch.setattr(
        attestation,
        "_now",
        lambda:
            T + timedelta(seconds=4),
    )

    with pytest.raises(
        ValueError,
        match="strictly precede earliest persisted capture evidence",
    ):
        attest_price_observation(
            state,
            ledger,
            repo_root=repo_root(),
            slot_id=authorization["slot_id"],
            observation_id=price["id"],
        )
