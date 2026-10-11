"""Deterministic causal replay over observations_v2.

STEP 49B.1.

Replay is reconstruction, never repair. The source observation ledger is opened
read-only through CausalObservationSnapshot. A deterministic EvidenceGraph
projection may be materialized separately.

Later evidence may affect a later cutoff but must never alter an earlier replay.
No network, capture, backfill, outcome access, trading action, or knowledge
promotion occurs here.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from core.intelligence_graph import EvidenceGraph

from .causal_evidence_graph import (
    EvidenceGraphProjection,
    append_causal_market_state,
)
from .causal_latent_context import (
    project_latent_context,
)
from .causal_observation_snapshot import (
    BTC_CAUSAL_FEATURES,
    load_causal_snapshot,
)
from .prospective_receipts import (
    observation_hash,
)


REPLAY_SCHEMA = "causal-replay-certificate-v1"


def _projected_subgraph(
    view,
    projection,
):
    node_ids = {
        projection.market_state_id,
        *projection.source_node_ids,
    }

    edge_ids = set(
        projection.edge_ids
    )

    nodes = tuple(
        node
        for node in view["nodes"]
        if node["id"] in node_ids
    )

    edges = tuple(
        edge
        for edge in view["edges"]
        if edge["id"] in edge_ids
    )

    if {
        node["id"]
        for node in nodes
    } != node_ids:
        raise ValueError(
            "replay graph missing projected node"
        )

    if {
        edge["id"]
        for edge in edges
    } != edge_ids:
        raise ValueError(
            "replay graph missing projected edge"
        )

    return {
        "nodes": list(nodes),
        "edges": list(edges),
    }


@dataclass(frozen=True, slots=True)
class CausalReplayCertificate:
    instrument: str
    as_of: datetime

    snapshot_id: str
    latent_projection_id: str
    evidence_projection_id: str
    market_state_id: str

    observation_ids: tuple[str, ...]
    source_node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]

    missing_features: tuple[str, ...]
    latent_unknown_axes: tuple[str, ...]
    unconsumed_features: tuple[str, ...]

    subgraph_sha256: str

    replay_id: str = field(init=False)

    def __post_init__(self):
        if (
            not self.instrument
            or self.as_of.tzinfo is None
            or self.as_of.utcoffset() is None
        ):
            raise ValueError(
                "instrument and aware cutoff required"
            )

        identities = (
            self.snapshot_id,
            self.latent_projection_id,
            self.evidence_projection_id,
            self.market_state_id,
            self.subgraph_sha256,
        )

        if any(
            not value
            for value in identities
        ):
            raise ValueError(
                "complete replay identities required"
            )

        for values in (
            self.observation_ids,
            self.source_node_ids,
            self.edge_ids,
        ):
            if type(values) is not tuple:
                raise TypeError(
                    "immutable replay identity tuple required"
                )

            if len(values) != len(set(values)):
                raise ValueError(
                    "duplicate replay identity"
                )

        if (
            len(self.observation_ids)
            != len(self.source_node_ids)
            or len(self.source_node_ids)
            != len(self.edge_ids)
        ):
            raise ValueError(
                "observation lineage cardinality mismatch"
            )

        payload = {
            "schema":
                REPLAY_SCHEMA,
            "instrument":
                self.instrument,
            "as_of":
                self.as_of.isoformat(),
            "snapshot_id":
                self.snapshot_id,
            "latent_projection_id":
                self.latent_projection_id,
            "evidence_projection_id":
                self.evidence_projection_id,
            "market_state_id":
                self.market_state_id,
            "observation_ids":
                list(self.observation_ids),
            "source_node_ids":
                list(self.source_node_ids),
            "edge_ids":
                list(self.edge_ids),
            "missing_features":
                list(self.missing_features),
            "latent_unknown_axes":
                list(self.latent_unknown_axes),
            "unconsumed_features":
                list(self.unconsumed_features),
            "subgraph_sha256":
                self.subgraph_sha256,
        }

        object.__setattr__(
            self,
            "replay_id",
            observation_hash(payload),
        )

    def to_dict(self):
        return {
            "schema":
                REPLAY_SCHEMA,
            "replay_id":
                self.replay_id,
            "instrument":
                self.instrument,
            "as_of":
                self.as_of.isoformat(),
            "snapshot_id":
                self.snapshot_id,
            "latent_projection_id":
                self.latent_projection_id,
            "evidence_projection_id":
                self.evidence_projection_id,
            "market_state_id":
                self.market_state_id,
            "observation_ids":
                list(self.observation_ids),
            "source_node_ids":
                list(self.source_node_ids),
            "edge_ids":
                list(self.edge_ids),
            "missing_features":
                list(self.missing_features),
            "latent_unknown_axes":
                list(self.latent_unknown_axes),
            "unconsumed_features":
                list(self.unconsumed_features),
            "subgraph_sha256":
                self.subgraph_sha256,
        }


def replay_causal_state(
    ledger,
    graph_path,
    *,
    instrument,
    as_of,
    features=BTC_CAUSAL_FEATURES,
):
    """Reconstruct one causal state and return its deterministic certificate."""

    snapshot = load_causal_snapshot(
        ledger,
        instrument=instrument,
        as_of=as_of,
        features=features,
    )

    latent = project_latent_context(
        snapshot
    )

    graph_path = Path(
        graph_path
    )

    graph_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    graph = EvidenceGraph(
        graph_path
    )

    evidence = append_causal_market_state(
        graph,
        snapshot,
        latent,
    )

    if type(evidence) is not EvidenceGraphProjection:
        raise TypeError(
            "unexpected graph projection"
        )

    view = graph.as_of(
        snapshot.as_of
    )

    subgraph = _projected_subgraph(
        view,
        evidence,
    )

    subgraph_sha256 = observation_hash(
        subgraph
    )

    return CausalReplayCertificate(
        instrument=
            snapshot.instrument,
        as_of=
            snapshot.as_of,
        snapshot_id=
            snapshot.snapshot_id,
        latent_projection_id=
            latent.projection_id,
        evidence_projection_id=
            evidence.projection_id,
        market_state_id=
            evidence.market_state_id,
        observation_ids=tuple(
            item.id
            for item in snapshot.observations
        ),
        source_node_ids=
            evidence.source_node_ids,
        edge_ids=
            evidence.edge_ids,
        missing_features=
            snapshot.missing_features,
        latent_unknown_axes=
            latent.context.unknown_axes,
        unconsumed_features=
            latent.unconsumed_features,
        subgraph_sha256=
            subgraph_sha256,
    )