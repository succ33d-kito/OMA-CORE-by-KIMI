from unittest.mock import patch
from datetime import timedelta

import pytest

from core.scientific.causal_latent_context import (
    project_latent_context,
)
from core.scientific.causal_observation_snapshot import (
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

    with patch('core.scientific.metrics_publication._now', return_value=S + timedelta(minutes=5)):
        return admit_verified_metrics_bundle(
            ledger,
            state[0],
            S,
            repo_root=state[1],
            now=S + timedelta(minutes=5),
            clock=lambda:
                S + timedelta(minutes=5),
        )


def metrics_snapshot(state, tmp_path):
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

    return ledger, snapshot


def test_global_positioning_maps_directly_to_long_short_ratio(
    state,
    tmp_path,
):
    _, snapshot = metrics_snapshot(
        state,
        tmp_path,
    )

    projection = project_latent_context(
        snapshot
    )

    global_observation = next(
        item
        for item in snapshot.observations
        if item.feature
        == "MarketMetrics/GlobalPositioning"
    )

    expected = float(
        global_observation.to_dict()[
            "payload"
        ]["value"]
    )

    assert (
        projection.context.long_short_ratio
        == expected
    )

    assert (
        "long_short_ratio"
        in projection.context.available_axes
    )

    assert len(
        projection.used_observation_ids
    ) == 1

    assert (
        projection.used_observation_ids[0]
        == global_observation.id
    )


def test_levels_and_taker_ratio_are_not_silently_reinterpreted(
    state,
    tmp_path,
):
    _, snapshot = metrics_snapshot(
        state,
        tmp_path,
    )

    projection = project_latent_context(
        snapshot
    )

    context = projection.context

    assert context.open_interest_change is None
    assert context.taker_imbalance is None

    assert (
        "open_interest_change"
        in context.unknown_axes
    )

    assert (
        "taker_imbalance"
        in context.unknown_axes
    )

    assert (
        "MarketMetrics/OpenInterest"
        in projection.unconsumed_features
    )

    assert (
        "MarketMetrics/TakerBuySellRatio"
        in projection.unconsumed_features
    )


def test_unverified_funding_is_not_mapped(
    state,
    tmp_path,
):
    ledger, _ = metrics_snapshot(
        state,
        tmp_path,
    )

    funding = append_observation(
        ledger,
        source="test-funding",
        instrument="BTCUSDT",
        feature="FundingRate/Published",
        event_time=S,
        source_metric_at=S,
        received_at=S + timedelta(minutes=1),
        payload={
            "funding_rate": "-0.000125"
        },
        provenance={
            "contract": "test-funding"
        },
        clock=lambda:
            S + timedelta(minutes=6),
    )

    snapshot = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=6),
    )

    projection = project_latent_context(
        snapshot
    )

    assert (
        projection.context.funding_rate
        is None
    )

    assert (
        "funding_rate"
        in projection.context.unknown_axes
    )

    assert funding["id"] not in (
        projection.used_observation_ids
    )


def test_malformed_direct_payload_fails_closed(
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
        received_at=S + timedelta(seconds=1),
        payload={
            "funding_rate": "not-a-number"
        },
        provenance={
            "contract": "malformed-test"
        },
        clock=lambda:
            S + timedelta(minutes=1),
    )

    snapshot = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=2),
        features=(
            "FundingRate/Published",
        ),
    )

    assert snapshot.observations == ()
    assert project_latent_context(snapshot).context.funding_rate is None



def test_projection_is_deterministic(
    state,
    tmp_path,
):
    _, snapshot = metrics_snapshot(
        state,
        tmp_path,
    )

    first = project_latent_context(
        snapshot
    )

    second = project_latent_context(
        snapshot
    )

    assert first == second

    assert (
        first.projection_id
        == second.projection_id
    )

    assert (
        first.to_dict()
        == second.to_dict()
    )