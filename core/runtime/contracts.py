"""Immutable observations with explicit unknowns and recoverable provenance."""
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import hashlib
import json


def timestamp(value):
    at = datetime.fromisoformat(value)
    if at.utcoffset() is None: raise ValueError('aware timestamp required')
    return at


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)


class State(str, Enum):
    AVAILABLE='AVAILABLE'
    UNKNOWN='UNKNOWN'
    UNAVAILABLE='UNAVAILABLE'
    STALE='STALE'
    INVALID='INVALID'


@dataclass(frozen=True, slots=True)
class DataSourceStatus:
    name: str
    state: State = State.UNAVAILABLE
    source: str | None = None
    source_at: str | None = None
    commitment: str | None = None
    details_json: str = '{}'
    reason: str = 'NOT_CONFIGURED'
    freshness: str = 'UNKNOWN'

    def __post_init__(self):
        if type(self.state) is not State: raise TypeError('closed state required')
        if self.source_at is not None: timestamp(self.source_at)
        data = json.loads(self.details_json)
        if type(data) is not dict or canonical(data)!=self.details_json: raise ValueError('canonical immutable details required')
        if self.freshness not in ('UNKNOWN','CURRENT','STALE'): raise ValueError('invalid freshness')
        if self.state in (State.AVAILABLE,State.STALE) and (not self.source or not self.commitment):
            raise ValueError('available data requires provenance')


@dataclass(frozen=True, slots=True)
class NodeStatus:
    node_id: str
    runtime_state: str = field(init=False,default='UNVERIFIED')


@dataclass(frozen=True, slots=True)
class CollectorStatus(DataSourceStatus):
    pass


@dataclass(frozen=True, slots=True)
class DecisionStatus(DataSourceStatus):
    pass


@dataclass(frozen=True, slots=True)
class ExecutionStatus(DataSourceStatus):
    execution_claim: str = field(init=False,default='NO_EXECUTION_EVIDENCE')


@dataclass(frozen=True, slots=True)
class PositionStatus(DataSourceStatus):
    open_position_claim: str = field(init=False,default='NO_FACTUAL_OPEN_POSITION_EVIDENCE')


@dataclass(frozen=True, slots=True)
class ScientificStatus:
    price_pit: DataSourceStatus
    edge: str = field(init=False,default='NOT DEMONSTRATED')
    regime: str = field(init=False,default='NOT VALIDATED')
    mechanics: str = field(init=False,default='NOT VALIDATED')
    policy_winner: str = field(init=False,default='NONE')
    confirmation: str = field(init=False,default='UNKNOWN_NOT_INSPECTED')


@dataclass(frozen=True, slots=True)
class SystemSnapshot:
    snapshot_at: str
    node: NodeStatus
    sources: tuple[DataSourceStatus, ...]
    decisions: DecisionStatus
    execution: ExecutionStatus
    positions: PositionStatus
    science: ScientificStatus
    system_id: str = field(init=False,default='OMA-CORE')
    mode: str = field(init=False,default='UNKNOWN')
    snapshot_id: str = field(init=False)

    def __post_init__(self):
        timestamp(self.snapshot_at)
        if type(self.sources) is not tuple or len({s.name for s in self.sources})!=len(self.sources):
            raise ValueError('unique immutable sources required')
        object.__setattr__(self,'sources',tuple(sorted(self.sources,key=lambda s:s.name)))
        data={k:asdict(getattr(self,k)) for k in ('node','decisions','execution','positions','science')}
        data.update(snapshot_at=self.snapshot_at,system_id=self.system_id,mode=self.mode,sources=[asdict(s) for s in self.sources])
        object.__setattr__(self,'snapshot_id',hashlib.sha256(canonical(data).encode()).hexdigest())

    def to_dict(self):
        data=asdict(self)
        for row in list(data['sources'])+[data['decisions'],data['execution'],data['positions'],data['science']['price_pit']]:
            row['details']=json.loads(row.pop('details_json'))
        return data
