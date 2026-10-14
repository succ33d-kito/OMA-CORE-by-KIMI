"""Separate derived-feature graph and replay certificate; raw 49A stays unchanged."""
from pathlib import Path
from tempfile import TemporaryDirectory
from core.intelligence_graph.store import EvidenceGraph, Node, Edge
from .causal_regime import FEATURE as REGIME, validate_causal_regime
from .causal_mechanics import FEATURE as MECHANICS, validate_causal_mechanics
from .price_role_activation import ROLES
from .regime_observation import _utc
from .prospective_receipts import observation_hash
from .metrics_publication import observation_snapshot, publication_for
from .metrics_snapshot_gate import metrics_snapshot_available


def replay_derived_features(ledger, *, dataset_role, as_of, graph_path):
    if dataset_role not in ROLES:
        raise ValueError("explicit supported dataset role required")
    cutoff = _utc(as_of)
    known, _ = observation_snapshot(ledger, read_only=True)
    selected = []
    for row in known.values():
        if row["feature"] not in (REGIME, MECHANICS) or row["available_at"] is None or _utc(row["available_at"]) > cutoff:
            continue
        if row["provenance"].get("dataset_role") != dataset_role:
            continue
        if row["feature"] == REGIME:
            validate_causal_regime(known,row,dataset_role=dataset_role,cutoff=cutoff)
        else:
            validate_causal_mechanics(ledger,row,dataset_role=dataset_role,cutoff=cutoff)
        selected.append(row["id"])
    nodes, edges, visited = [], [], set()
    def visit(identity):
        if identity in visited:
            return
        visited.add(identity)
        row = known[identity]
        if row['feature'].startswith('MarketMetrics/'):
            if not metrics_snapshot_available(known, identity, cutoff):
                raise ValueError('Metrics publication unavailable')
            publication = publication_for(known, row['provenance']['bundle_id'])
            row = {**row, 'available_at': max(_utc(row['available_at']), _utc(publication['published_at'])).isoformat(),
                   'provenance': {**row['provenance'], 'durable_publication': publication}}
        if row["available_at"] is None or _utc(row["available_at"]) > cutoff:
            raise ValueError("graph dependency unavailable")
        kind = "market_state" if row["feature"] in (REGIME,MECHANICS) else "evidence" if row["derived"] else "source"
        nodes.append(Node(identity,kind,_utc(row["event_time"]),_utc(row["available_at"]),
            "observations_v2:"+observation_hash(row),row))
        for dep in row["dependencies"]:
            visit(dep)
            edge_id = observation_hash(["derived-feature-edge-v1",identity,dep])
            edges.append(Edge(edge_id,identity,dep,"derived_feature_from",_utc(row["available_at"])))
    for identity in sorted(selected):
        visit(identity)
    graph = EvidenceGraph(graph_path)
    graph.append(nodes=nodes,edges=edges)
    # Certificate commits the exact reconstructed subgraph, independent of prior store contents.
    content = {"nodes": [n.to_dict() for n in sorted(nodes,key=lambda n:n.id)],
        "edges": [e.to_dict() for e in sorted(edges,key=lambda e:e.id)]}
    result = {"schema":"derived-causal-replay-v1","dataset_role":dataset_role,
        "as_of":cutoff.isoformat(),"derived_ids":sorted(selected),
        "dependency_ids":sorted(visited-set(selected)),"graph_hash":observation_hash(content),
        "regime_available":any(known[i]["feature"] == REGIME for i in selected),
        "mechanics_available":any(known[i]["feature"] == MECHANICS for i in selected)}
    return {**result,"replay_id":observation_hash(result)}


def reconcile_derived_replay(ledger, *, dataset_role, as_of):
    with TemporaryDirectory() as first, TemporaryDirectory() as second:
        left = replay_derived_features(ledger,dataset_role=dataset_role,as_of=as_of,graph_path=Path(first)/"graph.db")
        right = replay_derived_features(ledger,dataset_role=dataset_role,as_of=as_of,graph_path=Path(second)/"graph.db")
    if left != right:
        raise ValueError("derived replay reconciliation mismatch")
    return {"status":"MATCH","certificate":left}
