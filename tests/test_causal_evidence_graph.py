from datetime import timedelta

from core.intelligence_graph import (
    EvidenceGraph,
)

from core.scientific.causal_evidence_graph import (
    append_causal_market_state,
)
from core.scientific.causal_latent_context import (
    LatentContextProjection,
    project_latent_context,
)
from core.scientific.causal_observation_snapshot import (
    load_causal_snapshot,
)
from core.scientific.metrics_observation_admission import (
    admit_verified_metrics_bundle,
)
from tests.test_metrics_continuity import (
    S,
    capture,
    state,
)


def build_case(state, tmp_path):
    ledger = tmp_path / "scientific.db"

    capture(state)

    admit_verified_metrics_bundle(
        ledger,
        state[0],
        S,
        repo_root=state[1],
        now=S + timedelta(minutes=5),
        clock=lambda:
            S + timedelta(minutes=5),
    )

    snapshot = load_causal_snapshot(
        ledger,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    latent = project_latent_context(
        snapshot
    )

    graph = EvidenceGraph(
        tmp_path / "graph.db"
    )

    return snapshot, latent, graph


def test_snapshot_and_context_append_as_temporal_market_state(
    state,
    tmp_path,
):
    snapshot, latent, graph = build_case(
        state,
        tmp_path,
    )

    projection = append_causal_market_state(
        graph,
        snapshot,
        latent,
    )

    view = graph.as_of(
        snapshot.as_of
    )

    assert len(view["nodes"]) == 7
    assert len(view["edges"]) == 6

    market = next(
        node
        for node in view["nodes"]
        if node["id"]
        == projection.market_state_id
    )

    assert market["kind"] == "market_state"

    assert (
        market["payload"]["snapshot"][
            "snapshot_id"
        ]
        == snapshot.snapshot_id
    )

    assert (
        market["payload"]["latent_context"][
            "projection_id"
        ]
        == latent.projection_id
    )


def test_every_observation_has_exact_lineage_edge(
    state,
    tmp_path,
):
    snapshot, latent, graph = build_case(
        state,
        tmp_path,
    )

    projection = append_causal_market_state(
        graph,
        snapshot,
        latent,
    )

    view = graph.as_of(
        snapshot.as_of
    )

    assert (
        len(projection.source_node_ids)
        == len(snapshot.observations)
        == 6
    )

    derived = [
        edge
        for edge in view["edges"]
        if edge["relation"]
        == "derived_from"
    ]

    assert len(derived) == 6

    assert {
        edge["source"]
        for edge in derived
    } == {
        projection.market_state_id
    }

    assert {
        edge["target"]
        for edge in derived
    } == set(
        projection.source_node_ids
    )


def test_source_visibility_respects_original_availability(
    state,
    tmp_path,
):
    snapshot, latent, graph = build_case(
        state,
        tmp_path,
    )

    projection = append_causal_market_state(
        graph,
        snapshot,
        latent,
    )

    before_state = graph.as_of(
        snapshot.as_of
        - timedelta(microseconds=1)
    )

    assert all(
        node["id"]
        != projection.market_state_id
        for node in before_state["nodes"]
    )

    at_state = graph.as_of(
        snapshot.as_of
    )

    assert any(
        node["id"]
        == projection.market_state_id
        for node in at_state["nodes"]
    )


def test_bridge_is_idempotent_and_reproducible(
    state,
    tmp_path,
):
    snapshot, latent, graph = build_case(
        state,
        tmp_path,
    )

    first = append_causal_market_state(
        graph,
        snapshot,
        latent,
    )

    bytes_before = graph.as_of(
        snapshot.as_of
    )

    second = append_causal_market_state(
        graph,
        snapshot,
        latent,
    )

    bytes_after = graph.as_of(
        snapshot.as_of
    )

    assert first == second
    assert (
        first.projection_id
        == second.projection_id
    )
    assert bytes_before == bytes_after


def test_forged_latent_projection_is_rejected_before_write(
    state,
    tmp_path,
):
    snapshot, latent, graph = build_case(
        state,
        tmp_path,
    )

    forged = LatentContextProjection(
        snapshot_id=
            latent.snapshot_id,
        instrument=
            latent.instrument,
        as_of=
            latent.as_of,
        context=
            latent.context,
        used_observation_ids=(),
        unconsumed_features=
            latent.unconsumed_features,
    )

    try:
        append_causal_market_state(
            graph,
            snapshot,
            forged,
        )
    except ValueError as exc:
        assert (
            "does not match causal snapshot"
            in str(exc)
        )
    else:
        raise AssertionError(
            "forged projection accepted"
        )

    assert graph.as_of(
        snapshot.as_of
    ) == {
        "nodes": [],
        "edges": [],
    }


def test_graph_payload_preserves_unknown_and_unconsumed_semantics(
    state,
    tmp_path,
):
    snapshot, latent, graph = build_case(
        state,
        tmp_path,
    )

    projection = append_causal_market_state(
        graph,
        snapshot,
        latent,
    )

    market = next(
        node
        for node in graph.as_of(
            snapshot.as_of
        )["nodes"]
        if node["id"]
        == projection.market_state_id
    )

    context = market["payload"][
        "latent_context"
    ]["context"]

    assert (
        context["open_interest_change"]
        is None
    )

    assert (
        context["taker_imbalance"]
        is None
    )

    assert (
        "open_interest_change"
        in context["unknown_axes"]
    )

    assert (
        "MarketMetrics/OpenInterest"
        in market["payload"][
            "latent_context"
        ]["unconsumed_features"]
    )