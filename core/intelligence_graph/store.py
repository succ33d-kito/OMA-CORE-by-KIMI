"""Immutable, provider-neutral evidence snapshots and typed temporal links."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3

KINDS = {'source', 'event', 'hypothesis', 'evidence', 'market_state', 'decision', 'outcome', 'knowledge_candidate'}
RELATIONS = {
    'observes': ({'source'}, {'event'}),
    'motivates': ({'event'}, {'hypothesis'}),
    'derived_from': ({'evidence', 'market_state'}, {'source', 'event'}),
    'supports': ({'evidence'}, {'hypothesis'}),
    'contradicts': ({'evidence'}, {'hypothesis'}),
    'informs': ({'source', 'event', 'hypothesis', 'evidence', 'market_state'}, {'decision'}),
    'produces': ({'decision'}, {'outcome'}),
    'candidate_from': ({'outcome', 'evidence'}, {'knowledge_candidate'}),
}

def utc(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('timezone required')
    return value.astimezone(timezone.utc).isoformat()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    observed_at: datetime
    available_at: datetime
    provenance: str
    payload: dict

    def to_dict(self):
        if not self.id or self.kind not in KINDS or not self.provenance:
            raise ValueError('id, supported kind and explicit provenance required')
        observed, available = utc(self.observed_at), utc(self.available_at)
        if available < observed:
            raise ValueError('availability precedes observation')
        if self.kind == 'knowledge_candidate' and self.payload.get('promoted', False):
            raise ValueError('graph cannot promote knowledge')
        return dict(id=self.id, kind=self.kind, observed_at=observed,
                    available_at=available, provenance=self.provenance, payload=self.payload)

@dataclass(frozen=True)
class Edge:
    id: str
    source: str
    target: str
    relation: str
    available_at: datetime

    def to_dict(self):
        if not self.id or self.relation not in RELATIONS:
            raise ValueError('id and supported relation required')
        return dict(id=self.id, source=self.source, target=self.target,
                    relation=self.relation, available_at=utc(self.available_at))

class EvidenceGraph:
    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS graph_nodes (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS graph_edges (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')

    @staticmethod
    def _insert(db, table, obj):
        payload = canonical(obj)
        old = db.execute(f'SELECT payload FROM {table} WHERE id=?', (obj['id'],)).fetchone()
        if old and old[0] != payload:
            raise ValueError('immutable id conflicts with existing snapshot')
        if not old:
            db.execute(f'INSERT INTO {table} VALUES (?,?)', (obj['id'], payload))

    def append(self, nodes=(), edges=()):
        """All-or-nothing append; no placeholders for unknown references."""
        with sqlite3.connect(self.path) as db:
            for node in nodes:
                self._insert(db, 'graph_nodes', node.to_dict())
            known = {row[0]: json.loads(row[1]) for row in db.execute('SELECT * FROM graph_nodes')}
            existing = [json.loads(row[0]) for row in db.execute('SELECT payload FROM graph_edges')]
            for edge in edges:
                obj = edge.to_dict()
                if obj['source'] not in known or obj['target'] not in known:
                    raise ValueError('unknown endpoint')
                src, dst = known[obj['source']], known[obj['target']]
                left, right = RELATIONS[obj['relation']]
                if src['kind'] not in left or dst['kind'] not in right:
                    raise ValueError('invalid endpoint kinds')
                if obj['available_at'] < max(src['available_at'], dst['available_at']):
                    raise ValueError('link unavailable before its endpoints')
                if obj['relation'] == 'informs' and obj['available_at'] > dst['observed_at']:
                    raise ValueError('future information cannot inform decision')
                if obj['relation'] == 'produces' and dst['observed_at'] < src['observed_at']:
                    raise ValueError('outcome precedes decision')
                if obj['relation'] in {'supports', 'contradicts'}:
                    if any(e['source'] == obj['source'] and e['relation'] in {'supports', 'contradicts'}
                           and (e['target'] != obj['target'] or e['relation'] != obj['relation']) for e in existing):
                        raise ValueError('evidence belongs to one hypothesis and direction')
                self._insert(db, 'graph_edges', obj)
                existing.append(obj)

    def as_of(self, at):
        cutoff = utc(at)
        with sqlite3.connect(self.path) as db:
            nodes = [json.loads(r[0]) for r in db.execute('SELECT payload FROM graph_nodes ORDER BY id')]
            edges = [json.loads(r[0]) for r in db.execute('SELECT payload FROM graph_edges ORDER BY id')]
        nodes = [n for n in nodes if n['available_at'] <= cutoff]
        ids = {n['id'] for n in nodes}
        return {'nodes': nodes, 'edges': [e for e in edges if e['available_at'] <= cutoff and e['source'] in ids and e['target'] in ids]}

    def record_decision(self, decision, provenance):
        """Consume DecisionRecord; reject absent evidence rather than inventing it."""
        node = Node(decision.decision_id, 'decision', decision.decided_at,
                    decision.decided_at, provenance, decision.to_dict())
        refs = [decision.event_id, *decision.evidence_ids, *decision.source_ids]
        refs += [x for x in (decision.hypothesis_id, decision.market_state_id) if x]
        edges = [Edge(f'{decision.decision_id}:informs:{ref}', ref, decision.decision_id,
                      'informs', decision.decided_at) for ref in dict.fromkeys(refs)]
        self.append([node], edges)

    def record_outcome(self, outcome, available_at, provenance):
        self.append([Node(outcome.outcome_id, 'outcome', outcome.observed_at,
                          available_at, provenance, outcome.to_dict())],
                    [Edge(f'{outcome.decision_id}:produces:{outcome.outcome_id}',
                          outcome.decision_id, outcome.outcome_id, 'produces', available_at)])
