from datetime import timedelta
import sqlite3

import pytest

from core.scientific.causal_observation_snapshot import (
    BTC_CAUSAL_FEATURES,
    load_causal_snapshot,
)
from core.scientific.metrics_observation_admission import (
    admit_verified_metrics_bundle,
)
from core.scientific.prospective_receipts import (
    append_observation,
)
from tests.test_metrics_continuity import (
    S,
    capture,
    state,
)


def admit_metrics(state, ledger):
    capture(state)

    return admit_verified_metrics_bundle(
        ledger,
        state[0],
        S,
        repo_root=state[1],
        now=S + timedelta(minutes=5),
        clock=lambda:
            S + timedelta(minutes=5),
    )


def test_metrics_projection_is_visible_only_after_ledger_availability(
    state,
    tmp_path,
):
    ledger = tmp_path / "scientific.db"

    admit_metrics(
        state,
        ledger,
    )

    before = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=4),
    )

    assert before.observations == ()
    assert before.missing_features == BTC_CAUSAL_FEATURES

    after = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    assert len(after.observations) == 6

    assert set(
        x.feature
        for x in after.observations
    ) == {
        x
        for x in BTC_CAUSAL_FEATURES
        if x.startswith("MarketMetrics/")
    }

    assert after.missing_features == (
        "Price/OHLCV",
        "FundingRate/Published",
    )


def test_missing_is_preserved_not_imputed(
    state,
    tmp_path,
):
    ledger = tmp_path / "scientific.db"

    admit_metrics(
        state,
        ledger,
    )

    snapshot = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    values = {
        item.feature:
            item.to_dict()["payload"]
        for item in snapshot.observations
    }

    assert "Price/OHLCV" not in values
    assert "FundingRate/Published" not in values

    assert snapshot.missing_features == (
        "Price/OHLCV",
        "FundingRate/Published",
    )


def test_snapshot_is_deterministic_and_read_only(
    state,
    tmp_path,
):
    ledger = tmp_path / "scientific.db"

    admit_metrics(
        state,
        ledger,
    )

    before = ledger.read_bytes()

    first = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    second = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    after = ledger.read_bytes()

    assert first == second
    assert (
        first.snapshot_id
        == second.snapshot_id
    )
    assert before == after


def test_later_available_observation_cannot_leak_into_past_snapshot(
    tmp_path,
):
    ledger = tmp_path / "scientific.db"

    append_observation(
        ledger,
        source="test-funding",
        instrument="BTCUSDT",
        feature="FundingRate/Published",
        event_time=S,
        source_metric_at=S,
        received_at=S + timedelta(minutes=1),
        payload={"funding_rate": "0.001"},
        provenance={"contract": "test"},
        clock=lambda:
            S + timedelta(minutes=2),
    )

    past = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=1),
        features=("FundingRate/Published",),
    )

    present = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=2),
        features=("FundingRate/Published",),
    )

    assert past.observations == ()
    assert past.missing_features == (
        "FundingRate/Published",
    )

    assert len(present.observations) == 1
    assert present.missing_features == ()


def test_same_feature_same_metric_time_from_two_sources_is_ambiguous(
    tmp_path,
):
    ledger = tmp_path / "scientific.db"

    for n, source in enumerate(
        ("source-a", "source-b"),
        start=1,
    ):
        append_observation(
            ledger,
            source=source,
            instrument="BTCUSDT",
            feature="FundingRate/Published",
            event_time=S,
            source_metric_at=S,
            received_at=S + timedelta(seconds=n),
            payload={"funding_rate": str(n)},
            provenance={"contract": source},
            clock=lambda n=n:
                S + timedelta(minutes=1, seconds=n),
        )

    with pytest.raises(
        ValueError,
        match="ambiguous latest observation",
    ):
        load_causal_snapshot(
            ledger,
            instrument="BTCUSDT",
            as_of=S + timedelta(minutes=2),
            features=("FundingRate/Published",),
        )


def test_corrupt_observation_chain_fails_closed(
    state,
    tmp_path,
):
    ledger = tmp_path / "scientific.db"

    admit_metrics(
        state,
        ledger,
    )

    # Tamper only after disabling the append-only UPDATE trigger.
    with sqlite3.connect(ledger) as con:
        con.execute(
            "DROP TRIGGER observations_v2_no_update"
        )
        con.execute(
            """
            UPDATE observations_v2
            SET receipt_hash=?
            WHERE seq=1
            """,
            ("0" * 64,),
        )

    with pytest.raises(
        ValueError,
        match="observation chain integrity failure",
    ):
        load_causal_snapshot(
            ledger,
            instrument="BTCUSDT",
            as_of=S + timedelta(minutes=5),
        )