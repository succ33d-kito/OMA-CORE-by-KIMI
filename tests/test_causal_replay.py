from unittest.mock import patch
from datetime import timedelta
import sqlite3

import pytest

from core.intelligence_graph import (
    EvidenceGraph,
    Node,
)

from core.scientific.causal_replay import (
    replay_causal_state,
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


def prepare_ledger(
    state,
    tmp_path,
):
    ledger = tmp_path / "scientific.db"

    capture(state)

    with patch('core.scientific.metrics_publication._now', return_value=S + timedelta(minutes=5)):
        admit_verified_metrics_bundle(
            ledger,
            state[0],
            S,
            repo_root=state[1],
            now=S + timedelta(minutes=5),
            clock=lambda:
                S + timedelta(minutes=5),
        )

    return ledger


def test_same_ledger_and_cutoff_produce_same_replay_certificate(
    state,
    tmp_path,
):
    ledger = prepare_ledger(
        state,
        tmp_path,
    )

    first = replay_causal_state(
        ledger,
        tmp_path / "graph-a.db",
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    second = replay_causal_state(
        ledger,
        tmp_path / "graph-b.db",
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    assert first == second
    assert first.replay_id == second.replay_id
    assert first.snapshot_id == second.snapshot_id
    assert (
        first.latent_projection_id
        == second.latent_projection_id
    )
    assert (
        first.market_state_id
        == second.market_state_id
    )
    assert (
        first.subgraph_sha256
        == second.subgraph_sha256
    )


def test_replay_does_not_modify_source_ledger(
    state,
    tmp_path,
):
    ledger = prepare_ledger(
        state,
        tmp_path,
    )

    before = ledger.read_bytes()

    replay_causal_state(
        ledger,
        tmp_path / "graph.db",
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    after = ledger.read_bytes()

    assert before == after


def test_same_replay_graph_is_idempotent(
    state,
    tmp_path,
):
    ledger = prepare_ledger(
        state,
        tmp_path,
    )

    graph = tmp_path / "graph.db"

    first = replay_causal_state(
        ledger,
        graph,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    view_before = EvidenceGraph(
        graph
    ).as_of(
        S + timedelta(minutes=5)
    )

    second = replay_causal_state(
        ledger,
        graph,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    view_after = EvidenceGraph(
        graph
    ).as_of(
        S + timedelta(minutes=5)
    )

    assert first == second
    assert view_before == view_after


def test_later_evidence_cannot_change_earlier_replay(
    state,
    tmp_path,
):
    ledger = prepare_ledger(
        state,
        tmp_path,
    )

    before = replay_causal_state(
        ledger,
        tmp_path / "before.db",
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    append_observation(
        ledger,
        source="test-funding",
        instrument="BTCUSDT",
        feature="FundingRate/Published",
        event_time=S,
        source_metric_at=S,
        received_at=
            S + timedelta(minutes=5, seconds=30),
        payload={
            "funding_rate": "-0.000125"
        },
        provenance={
            "contract":
                "later-evidence-test"
        },
        clock=lambda:
            S + timedelta(minutes=6),
    )

    after = replay_causal_state(
        ledger,
        tmp_path / "after.db",
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    assert before == after
    assert before.replay_id == after.replay_id


def test_later_cutoff_cannot_legitimize_unverified_funding(
    state,
    tmp_path,
):
    ledger = prepare_ledger(
        state,
        tmp_path,
    )

    early = replay_causal_state(
        ledger,
        tmp_path / "early.db",
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    funding = append_observation(
        ledger,
        source="test-funding",
        instrument="BTCUSDT",
        feature="FundingRate/Published",
        event_time=S,
        source_metric_at=S,
        received_at=
            S + timedelta(minutes=5, seconds=30),
        payload={
            "funding_rate": "-0.000125"
        },
        provenance={
            "contract":
                "later-cutoff-test"
        },
        clock=lambda:
            S + timedelta(minutes=6),
    )

    later = replay_causal_state(
        ledger,
        tmp_path / "later.db",
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=6),
    )

    assert early.replay_id != later.replay_id

    assert funding["id"] not in (
        early.observation_ids
    )

    assert funding["id"] not in (
        later.observation_ids
    )

    assert (
        "FundingRate/Published"
        in early.missing_features
    )

    assert (
        "FundingRate/Published"
        in later.missing_features
    )


def test_unrelated_graph_content_does_not_change_certificate(
    state,
    tmp_path,
):
    ledger = prepare_ledger(
        state,
        tmp_path,
    )

    clean = replay_causal_state(
        ledger,
        tmp_path / "clean.db",
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    noisy_path = tmp_path / "noisy.db"

    graph = EvidenceGraph(
        noisy_path
    )

    graph.append([
        Node(
            id="unrelated",
            kind="source",
            observed_at=S,
            available_at=S,
            provenance="test:unrelated",
            payload={"unrelated": True},
        )
    ])

    noisy = replay_causal_state(
        ledger,
        noisy_path,
        instrument="BTCUSDT",
        as_of=S + timedelta(minutes=5),
    )

    assert clean == noisy
    assert (
        clean.subgraph_sha256
        == noisy.subgraph_sha256
    )


def test_corrupt_observation_ledger_fails_closed(
    state,
    tmp_path,
):
    ledger = prepare_ledger(
        state,
        tmp_path,
    )

    with sqlite3.connect(
        ledger
    ) as con:
        con.execute(
            "DROP TRIGGER observations_v2_no_update"
        )

        con.execute(
            """
            UPDATE observations_v2
            SET receipt_hash=?
            WHERE seq=1
            """,
            ("f" * 64,),
        )

    with pytest.raises(
        ValueError,
        match="observation chain integrity failure",
    ):
        replay_causal_state(
            ledger,
            tmp_path / "graph.db",
            instrument="BTCUSDT",
            as_of=S + timedelta(minutes=5),
        )