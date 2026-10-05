"""Deterministic aggregation only. No operational actions on inspection."""
from dataclasses import dataclass, replace, fields
import json
from .contracts import (DataSourceStatus,DecisionStatus,ExecutionStatus,PositionStatus,
                        NodeStatus,ScientificStatus,SystemSnapshot,State,canonical,timestamp)
from .readers import Source,read_source,read_json


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    node_id: str
    sources: tuple[Source, ...] = ()

    def __post_init__(self):
        if type(self.node_id) is not str or not self.node_id or type(self.sources) is not tuple:
            raise ValueError('explicit node and immutable source descriptors required')
        if any(type(s) is not Source or s.node_id!=self.node_id for s in self.sources):
            raise ValueError('independent nodes require separate snapshots; no ledger merging')
        if len({s.name for s in self.sources})!=len(self.sources) or len({s.kind for s in self.sources})!=len(self.sources):
            raise ValueError('ambiguous source selection')


def load_config(path=None):
    if path is None: return RuntimeConfig('LOCAL_UNCONFIGURED')
    data=read_json(path)
    if set(data)!={'node_id','sources'} or type(data['sources']) is not list:
        raise ValueError('invalid runtime configuration')
    return RuntimeConfig(data['node_id'],tuple(Source(**s) for s in data['sources']))


def _typed(cls, source):
    return cls(**{f.name:getattr(source,f.name) for f in fields(DataSourceStatus)})


def build_system_snapshot(config, *, snapshot_at):
    if type(config) is not RuntimeConfig: raise TypeError('RuntimeConfig required')
    at=timestamp(snapshot_at)
    kinds=('price','collector','book','premium','events','world','radar','shadow','execution','position')
    observed={kind:DataSourceStatus(kind) for kind in kinds}
    for source in config.sources:
        observed[source.kind]=replace(read_source(source,snapshot_at=snapshot_at),name=source.kind)
    shadow=observed['shadow']
    if shadow.state in (State.AVAILABLE,State.STALE):
        data=json.loads(shadow.details_json)
        for kind in ('world','radar'):
            if observed[kind].reason=='NOT_CONFIGURED' and kind in data:
                source_at=data[kind].get('as_of',shadow.source_at)
                # A derived projection does not make old world evidence fresh.
                max_age=next(s.max_age_seconds for s in config.sources if s.kind=='shadow')
                fresh='UNKNOWN' if max_age is None or source_at is None else ('STALE' if (at-timestamp(source_at)).total_seconds()>max_age else 'CURRENT')
                observed[kind]=DataSourceStatus(kind,State.STALE if fresh=='STALE' else shadow.state,
                    shadow.source+'#'+kind,source_at,shadow.commitment,canonical(data[kind]),'PROJECTION_OF_VERIFIED_SHADOW_ARTIFACT',fresh)
    price=observed['price']
    readiness=json.loads(price.details_json)
    readiness['81h_input_readiness']=readiness.get('regime_input_ready') if price.state is State.AVAILABLE and price.freshness=='CURRENT' else None
    science=ScientificStatus(replace(price,details_json=canonical(readiness)))
    return SystemSnapshot(snapshot_at,NodeStatus(config.node_id),tuple(observed.values()),
        _typed(DecisionStatus,shadow),_typed(ExecutionStatus,observed['execution']),
        _typed(PositionStatus,observed['position']),science)
