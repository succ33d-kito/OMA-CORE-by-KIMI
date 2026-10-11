from dataclasses import replace
from datetime import timedelta

import pytest

import core.scientific.price_role_attestation as attestation

from core.scientific.causal_observation_snapshot import (
    load_causal_snapshot,
)
from core.scientific.price_role_attestation import (
    ATTESTATION_FEATURE,
    attest_price_observation,
)
from tests.test_price_role_attestation import (
    T,
    append_price,
    authorize,
    create_activation,
    repo_root,
)


def snapshot(ledger, role, cutoff=None, features=("Price/OHLCV",)):
    return load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=(
            T + timedelta(seconds=5)
            if cutoff is None
            else cutoff
        ),
        features=features,
        dataset_role=role,
    )


def build_attested_price(tmp_path, monkeypatch, role="PILOT"):
    state = create_activation(
        tmp_path,
        monkeypatch,
        role=role,
    )

    authorization = authorize(
        state,
        monkeypatch,
    )

    ledger = tmp_path / f"price-{role.lower()}.db"
    price = append_price(ledger)

    monkeypatch.setattr(
        attestation,
        "_now",
        lambda: T + timedelta(seconds=4),
    )

    role_row = attest_price_observation(
        state,
        ledger,
        repo_root=repo_root(),
        slot_id=authorization["slot_id"],
        observation_id=price["id"],
    )

    return ledger, price, role_row


def test_authenticated_price_enters_matching_role_only(
    tmp_path,
    monkeypatch,
):
    ledger, price, role_row = build_attested_price(
        tmp_path,
        monkeypatch,
        role="PILOT",
    )

    pilot = snapshot(ledger, "PILOT")

    assert len(pilot.observations) == 1
    assert pilot.observations[0].id == price["id"]
    assert (
        pilot.observations[0].feature
        == "Price/OHLCV"
    )

    projected = pilot.to_dict()["observations"][0]

    assert (
        projected["role_attestation"]["id"]
        == role_row["id"]
    )

    assert snapshot(
        ledger,
        "DISCOVERY",
    ).observations == ()

    assert snapshot(
        ledger,
        "CONFIRMATION",
    ).observations == ()


def test_unscoped_price_identity_ignores_later_role_attestation(
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

    ledger = tmp_path / "unscoped-stability.db"
    price = append_price(ledger)

    before = snapshot(
        ledger,
        None,
    )

    monkeypatch.setattr(
        attestation,
        "_now",
        lambda: T + timedelta(seconds=4),
    )

    attest_price_observation(
        state,
        ledger,
        repo_root=repo_root(),
        slot_id=authorization["slot_id"],
        observation_id=price["id"],
    )

    after = snapshot(
        ledger,
        None,
    )

    assert before.snapshot_id == after.snapshot_id
    assert (
        "role_attestation"
        not in after.to_dict()["observations"][0]
    )


def test_roleless_price_remains_unscoped_only(
    tmp_path,
):
    ledger = tmp_path / "legacy-price.db"
    price = append_price(ledger)

    unscoped = snapshot(
        ledger,
        None,
    )

    assert len(unscoped.observations) == 1
    assert unscoped.observations[0].id == price["id"]

    assert snapshot(
        ledger,
        "PILOT",
    ).observations == ()


def test_attestation_must_be_available_by_snapshot_cutoff(
    tmp_path,
    monkeypatch,
):
    ledger, _, _ = build_attested_price(
        tmp_path,
        monkeypatch,
    )

    early = snapshot(
        ledger,
        "PILOT",
        cutoff=T + timedelta(
            milliseconds=3500
        ),
    )

    assert early.observations == ()

    later = snapshot(
        ledger,
        "PILOT",
        cutoff=T + timedelta(seconds=5),
    )

    assert len(later.observations) == 1


def test_scoped_price_cannot_be_relabelled_or_strip_proof(
    tmp_path,
    monkeypatch,
):
    ledger, _, _ = build_attested_price(
        tmp_path,
        monkeypatch,
    )

    pilot = snapshot(
        ledger,
        "PILOT",
    )

    with pytest.raises(
        ValueError,
        match="role",
    ):
        replace(
            pilot,
            dataset_role="DISCOVERY",
        )

    stripped = replace(
        pilot.observations[0],
        role_attestation_json=None,
    )

    with pytest.raises(
        ValueError,
        match="role",
    ):
        replace(
            pilot,
            observations=(stripped,),
        )


def test_attestation_is_not_projected_as_market_feature(
    tmp_path,
    monkeypatch,
):
    ledger, _, _ = build_attested_price(
        tmp_path,
        monkeypatch,
    )

    internal = snapshot(
        ledger,
        None,
        features=(ATTESTATION_FEATURE,),
    )

    assert internal.observations == ()
    assert internal.missing_features == (
        ATTESTATION_FEATURE,
    )
