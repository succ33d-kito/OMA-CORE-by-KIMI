"""PILOT shadow decision contracts. No broker, outcomes, or demonstrated Edge."""
from dataclasses import dataclass,field,fields,is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from .world_state import WorldState,_normalize
from .opportunity_candidate import OpportunityCandidate
from .multi_market_capture import commitment
from .nuisance_pilot_contracts import utc


def _plain(value):
    if is_dataclass(value): return {f.name:_plain(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,dict): return {k:_plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [_plain(v) for v in value]
    return _normalize(value)


def _seal(item,name):
    value={f.name:_plain(getattr(item,f.name)) for f in fields(item) if f.name!=name}
    object.__setattr__(item,name,commitment(value))


def _refs(values,*,empty=True):
    if type(values) is not tuple or (not empty and not values) or any(type(v) is not str or not v for v in values):
        raise TypeError('immutable explicit text/reference tuple required')
    if len(set(values))!=len(values): raise ValueError('duplicate references')


def _hash(value):
    if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('provenance commitment required')


def evidence_times(world):
    result={world.world_state_id:world.as_of}
    for m in world.markets:
        for evidence in (m.book,m.premium):
            if evidence is not None: result[evidence.observation_id]=evidence.available_at
    return result


@dataclass(frozen=True,slots=True)
class Thesis:
    candidate: OpportunityCandidate
    world: WorldState
    created_at: datetime
    available_at: datetime
    expression: str
    supporting_evidence_refs: tuple[str,...]
    contradicting_evidence_refs: tuple[str,...]
    premises: tuple[str,...]
    assumptions: tuple[str,...]
    invalidation_conditions: tuple[str,...]
    configuration_commitment: str
    expiry: datetime | None = None
    thesis_id: str = field(init=False)

    def __post_init__(self):
        if type(self.candidate) is not OpportunityCandidate or type(self.world) is not WorldState:
            raise TypeError('candidate and causal world required')
        utc(self.created_at); utc(self.available_at); _hash(self.configuration_commitment)
        if self.candidate.world_state_id!=self.world.world_state_id or self.candidate.role!=self.world.role:
            raise ValueError('thesis scope mismatch')
        if not self.world.as_of<=self.candidate.available_at<=self.created_at<=self.available_at:
            raise ValueError('noncausal thesis')
        if type(self.expression) is not str or not self.expression: raise ValueError('explicit hypothesis required')
        for refs in (self.supporting_evidence_refs,self.contradicting_evidence_refs,self.premises,self.assumptions,self.invalidation_conditions): _refs(refs)
        if not self.supporting_evidence_refs or not self.premises or not self.invalidation_conditions: raise ValueError('support, premises and invalidation required')
        available=evidence_times(self.world)
        for ref in self.supporting_evidence_refs+self.contradicting_evidence_refs:
            if ref not in available or available[ref]>self.available_at: raise ValueError('unknown/future evidence')
        if self.expiry is not None:
            utc(self.expiry)
            if self.expiry<=self.available_at: raise ValueError('already expired thesis')
        _seal(self,'thesis_id')

    @property
    def candidate_id(self): return self.candidate.candidate_id
    @property
    def world_state_id(self): return self.world.world_state_id
    @property
    def role(self): return self.candidate.role
    @property
    def family(self): return self.candidate.family
    @property
    def candidate_horizon(self): return self.candidate.horizon_seconds
    @property
    def contradiction_state(self):
        return 'CONFLICTING' if set(self.supporting_evidence_refs)&set(self.contradicting_evidence_refs) else ('PRESENT' if self.contradicting_evidence_refs else 'NONE_DECLARED')
