"""Relationship hypotheses only; no fitted association or validated edge."""
from dataclasses import dataclass,field,asdict
from datetime import datetime
from enum import Enum
from .world_state import WorldState,_normalize
from .multi_market_capture import commitment,SYMBOLS
from .nuisance_pilot_contracts import utc


class RelationshipFamily(Enum):
    RETURN_RELATIVE='RETURN_RELATIVE'
    LEAD_LAG_CANDIDATE='LEAD_LAG_CANDIDATE'
    CORRELATION_CANDIDATE='CORRELATION_CANDIDATE'
    VOLATILITY_TRANSMISSION_CANDIDATE='VOLATILITY_TRANSMISSION_CANDIDATE'
    EVENT_PROPAGATION_CANDIDATE='EVENT_PROPAGATION_CANDIDATE'


@dataclass(frozen=True,slots=True)
class MarketNode:
    universe_id: str
    symbol: str
    role: str = 'PILOT'
    venue: str = 'Binance USDⓈ-M'
    product: str = 'linear perpetual'
    node_id: str = field(init=False)

    def __post_init__(self):
        if self.symbol not in SYMBOLS or (self.role,self.venue,self.product)!=('PILOT','Binance USDⓈ-M','linear perpetual'):
            raise ValueError('unsupported node scope')
        object.__setattr__(self,'node_id',commitment((self.universe_id,self.symbol,self.role,self.venue,self.product)))


@dataclass(frozen=True,slots=True)
class CrossMarketObservation:
    world_state_id: str
    nodes: tuple[MarketNode,...]
    evidence_refs: tuple[str,...]
    available_at: datetime
    observation_id: str = field(init=False)

    def __post_init__(self):
        utc(self.available_at)
        if type(self.nodes) is not tuple or len(self.nodes)<2 or any(type(n) is not MarketNode for n in self.nodes):
            raise TypeError('immutable market nodes required')
        if tuple(sorted(set(n.symbol for n in self.nodes)))!=tuple(n.symbol for n in self.nodes) or len({n.universe_id for n in self.nodes})!=1:
            raise ValueError('node ordering/identity conflict')
        if type(self.evidence_refs) is not tuple or not self.evidence_refs or tuple(sorted(set(self.evidence_refs)))!=self.evidence_refs:
            raise ValueError('canonical evidence required')
        object.__setattr__(self,'observation_id',commitment((self.world_state_id,tuple(n.node_id for n in self.nodes),self.evidence_refs,self.available_at.isoformat())))


@dataclass(frozen=True,slots=True)
class RelationshipCandidate:
    observation: CrossMarketObservation
    family: RelationshipFamily
    hypothesis_ref: str
    created_at: datetime
    lag_candidate_seconds: int | None = None
    status: str = 'UNVALIDATED'
    candidate_id: str = field(init=False)

    def __post_init__(self):
        utc(self.created_at)
        if type(self.observation) is not CrossMarketObservation or type(self.family) is not RelationshipFamily:
            raise TypeError('closed relationship types required')
        if self.status!='UNVALIDATED' or self.created_at<self.observation.available_at or type(self.hypothesis_ref) is not str or not self.hypothesis_ref:
            raise ValueError('invalid hypothesis status/time/reference')
        if self.lag_candidate_seconds is not None and (self.family is not RelationshipFamily.LEAD_LAG_CANDIDATE or type(self.lag_candidate_seconds) is not int or self.lag_candidate_seconds<0):
            raise ValueError('lag is only a proposed nonnegative lead-lag parameter')
        object.__setattr__(self,'candidate_id',commitment((self.observation.observation_id,self.family.value,self.hypothesis_ref,self.created_at.isoformat(),self.lag_candidate_seconds,self.status)))


def observe_cross_market(world,*,symbols):
    if type(world) is not WorldState: raise TypeError('WorldState required')
    selected=tuple(sorted(set(symbols))); known={m.symbol:m for m in world.markets}
    if len(selected)<2 or set(selected)-known.keys(): raise ValueError('at least two known markets required')
    refs=[]
    for s in selected:
        evidence=[e for e in (known[s].book,known[s].premium) if e is not None]
        if not evidence: raise ValueError('market not observed')
        refs.extend(e.observation_id for e in evidence)
    nodes=tuple(MarketNode(world.universe_id,s,world.role) for s in selected)
    return CrossMarketObservation(world.world_state_id,nodes,tuple(sorted(set(refs))),world.as_of)
