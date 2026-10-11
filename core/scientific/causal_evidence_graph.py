"""Deterministic bridge from causal observation state into EvidenceGraph.

STEP 49A.3.

Raw observations become temporal source nodes. The authenticated causal snapshot
plus its semantically conservative LatentMarketContext projection becomes one
market_state node.

No hypothesis, decision, outcome, knowledge promotion, trading signal, network
access, capture, or observation admission occurs here.
"""

from dataclasses import dataclass, field

from core.intelligence_graph import (
    Edge,
    EvidenceGraph,
    Node,
)

from .causal_latent_context import (
    LatentContextProjection,
    project_latent_context,
)
from .causal_observation_snapshot import (
    CausalObservationSnapshot,
)
from .prospective_receipts import (
    observation_hash,
)


BRIDGE_SCHEMA = "causal-evidence-graph-bridge-v1"


def _source_node_id(observation_id):
    return observation_hash([
        BRIDGE_SCHEMA,
        "source",
        observation_id,
    ])


def _market_state_node_id(
    snapshot_id,
    projection_id,
):
    return observation_hash([
        BRIDGE_SCHEMA,
        "market_state",
        snapshot_id,
        projection_id,
    ])


def _edge_id(
    market_state_id,
    source_id,
):
    return observation_hash([
        BRIDGE_SCHEMA,
        "derived_from",
        market_state_id,
        source_id,
    ])


@dataclass(frozen=True, slots=True)
class EvidenceGraphProjection:
    snapshot_id: str
    latent_projection_id: str
    market_state_id: str
    source_node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    projection_id: str = field(init=False)

    def __post_init__(self):
        for value in (
            self.snapshot_id,
            self.latent_projection_id,
            self.market_state_id,
        ):
            if not value:
                raise ValueError(
                    "non-empty projection identities required"
                )

        if type(self.source_node_ids) is not tuple:
            raise TypeError(
                "immutable source-node tuple required"
            )

        if type(self.edge_ids) is not tuple:
            raise TypeError(
                "immutable edge tuple required"
            )

        if len(set(self.source_node_ids)) != len(
            self.source_node_ids
        ):
            raise ValueError(
                "duplicate source node"
            )

        if len(set(self.edge_ids)) != len(
            self.edge_ids
        ):
            raise ValueError(
                "duplicate graph edge"
            )

        if len(self.source_node_ids) != len(
            self.edge_ids
        ):
            raise ValueError(
                "one lineage edge per source required"
            )

        object.__setattr__(
            self,
            "projection_id",
            observation_hash({
                "schema": BRIDGE_SCHEMA,
                "snapshot_id":
                    self.snapshot_id,
                "latent_projection_id":
                    self.latent_projection_id,
                "market_state_id":
                    self.market_state_id,
                "source_node_ids":
                    list(self.source_node_ids),
                "edge_ids":
                    list(self.edge_ids),
            }),
        )

    def to_dict(self):
        return {
            "schema": BRIDGE_SCHEMA,
            "projection_id":
                self.projection_id,
            "snapshot_id":
                self.snapshot_id,
            "latent_projection_id":
                self.latent_projection_id,
            "market_state_id":
                self.market_state_id,
            "source_node_ids":
                list(self.source_node_ids),
            "edge_ids":
                list(self.edge_ids),
        }


def append_causal_market_state(
    graph,
    snapshot,
    latent_projection,
):
    """Append exact causal sources + one market_state, atomically."""

    if type(graph) is not EvidenceGraph:
        raise TypeError(
            "EvidenceGraph required"
        )

    if type(snapshot) is not CausalObservationSnapshot:
        raise TypeError(
            "CausalObservationSnapshot required"
        )

    if type(latent_projection) is not LatentContextProjection:
        raise TypeError(
            "LatentContextProjection required"
        )

    # Do not trust a caller-created projection merely because IDs line up.
    # Recompute the semantic projection from the authenticated snapshot.
    expected_projection = project_latent_context(
        snapshot
    )

    if latent_projection != expected_projection:
        raise ValueError(
            "latent projection does not match causal snapshot"
        )

    if (
        latent_projection.snapshot_id
        != snapshot.snapshot_id
        or latent_projection.instrument
        != snapshot.instrument
        or latent_projection.as_of
        != snapshot.as_of
    ):
        raise ValueError(
            "cross-snapshot latent projection"
        )

    source_nodes = []
    source_ids = []

    for observation in snapshot.observations:
        source_id = _source_node_id(
            observation.id
        )

        source_ids.append(
            source_id
        )

        source_nodes.append(
            Node(
                id=source_id,
                kind="source",
                observed_at=
                    observation.source_metric_at,
                available_at=
                    observation.available_at,
                provenance=(
                    "observations_v2:"
                    + observation.id
                ),
                payload={
                    "schema":
                        "causal-observation-source-v1",
                    "observation":
                        observation.to_dict(),
                },
            )
        )

    market_state_id = _market_state_node_id(
        snapshot.snapshot_id,
        latent_projection.projection_id,
    )

    market_state = Node(
        id=market_state_id,
        kind="market_state",
        observed_at=snapshot.as_of,
        available_at=snapshot.as_of,
        provenance=(
            "causal-observation-snapshot:"
            + snapshot.snapshot_id
        ),
        payload={
            "schema":
                "causal-market-state-v1",
            "instrument":
                snapshot.instrument,
            "snapshot":
                snapshot.to_dict(),
            "latent_context":
                latent_projection.to_dict(),
        },
    )

    edges = tuple(
        Edge(
            id=_edge_id(
                market_state_id,
                source_id,
            ),
            source=market_state_id,
            target=source_id,
            relation="derived_from",
            available_at=snapshot.as_of,
        )
        for source_id in source_ids
    )

    # Existing EvidenceGraph transaction provides all-or-nothing append.
    graph.append(
        nodes=[
            *source_nodes,
            market_state,
        ],
        edges=edges,
    )

    return EvidenceGraphProjection(
        snapshot_id=snapshot.snapshot_id,
        latent_projection_id=
            latent_projection.projection_id,
        market_state_id=
            market_state_id,
        source_node_ids=
            tuple(source_ids),
        edge_ids=
            tuple(edge.id for edge in edges),
    )