from datetime import timedelta

from core.scientific.causal_replay import (
    replay_causal_state,
)
from core.scientific.replay_reconciliation import (
    reconcile_causal_replay,
)
from tests.test_causal_price_role_snapshot import (
    build_attested_price,
)
from tests.test_price_role_attestation import T


FEATURES = ("Price/OHLCV",)


def replay(
    ledger,
    graph_path,
    *,
    role,
    cutoff=None,
):
    return replay_causal_state(
        ledger,
        graph_path,
        instrument="BTCUSDT",
        as_of=(
            T + timedelta(seconds=5)
            if cutoff is None
            else cutoff
        ),
        features=FEATURES,
        dataset_role=role,
    )


def reconcile(
    ledger,
    *,
    role,
    cutoff=None,
):
    return reconcile_causal_replay(
        ledger,
        instrument="BTCUSDT",
        as_of=(
            T + timedelta(seconds=5)
            if cutoff is None
            else cutoff
        ),
        features=FEATURES,
        dataset_role=role,
    )


def test_authenticated_price_survives_role_scoped_replay_and_reconciliation(
    tmp_path,
    monkeypatch,
):
    ledger, price, _ = build_attested_price(
        tmp_path,
        monkeypatch,
        role="PILOT",
    )

    certificate = replay(
        ledger,
        tmp_path / "pilot-price-graph.db",
        role="PILOT",
    )

    assert certificate.dataset_role == "PILOT"
    assert certificate.observation_ids == (
        price["id"],
    )
    assert certificate.missing_features == ()

    result = reconcile(
        ledger,
        role="PILOT",
    )

    assert result.status == "MATCH"

    body = result.to_dict()

    assert (
        body["left"]["dataset_role"]
        == body["right"]["dataset_role"]
        == "PILOT"
    )

    assert (
        body["left"]["observation_ids"]
        == body["right"]["observation_ids"]
        == [price["id"]]
    )

    assert (
        body["left"]["missing_features"]
        == body["right"]["missing_features"]
        == []
    )


def test_wrong_price_role_remains_missing_through_replay_and_reconciliation(
    tmp_path,
    monkeypatch,
):
    ledger, price, _ = build_attested_price(
        tmp_path,
        monkeypatch,
        role="PILOT",
    )

    certificate = replay(
        ledger,
        tmp_path / "wrong-role-graph.db",
        role="DISCOVERY",
    )

    assert certificate.dataset_role == "DISCOVERY"
    assert certificate.observation_ids == ()
    assert certificate.missing_features == (
        "Price/OHLCV",
    )
    assert price["id"] not in certificate.observation_ids

    result = reconcile(
        ledger,
        role="DISCOVERY",
    )

    assert result.status == "MATCH"

    body = result.to_dict()

    for side in ("left", "right"):
        assert body[side]["dataset_role"] == "DISCOVERY"
        assert body[side]["observation_ids"] == []
        assert body[side]["missing_features"] == [
            "Price/OHLCV"
        ]


def test_price_attestation_after_cutoff_remains_missing_through_replay(
    tmp_path,
    monkeypatch,
):
    ledger, price, _ = build_attested_price(
        tmp_path,
        monkeypatch,
        role="PILOT",
    )

    cutoff = T + timedelta(
        milliseconds=3500
    )

    certificate = replay(
        ledger,
        tmp_path / "early-cutoff-graph.db",
        role="PILOT",
        cutoff=cutoff,
    )

    assert certificate.observation_ids == ()
    assert certificate.missing_features == (
        "Price/OHLCV",
    )
    assert price["id"] not in certificate.observation_ids

    result = reconcile(
        ledger,
        role="PILOT",
        cutoff=cutoff,
    )

    assert result.status == "MATCH"

    body = result.to_dict()

    for side in ("left", "right"):
        assert body[side]["observation_ids"] == []
        assert body[side]["missing_features"] == [
            "Price/OHLCV"
        ]
