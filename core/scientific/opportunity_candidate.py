"""Closed candidate representation. A candidate is not an order or validated edge."""
from dataclasses import dataclass,asdict,field
from datetime import datetime
from enum import Enum
from .world_state import WorldState,_normalize
from .multi_market_capture import commitment
from .nuisance_pilot_contracts import utc


class CandidateFamily(Enum):
    DIRECTIONAL='DIRECTIONAL'
    RELATIVE_VALUE='RELATIVE_VALUE'
    CROSS_MARKET='CROSS_MARKET'
    EVENT_DRIVEN='EVENT_DRIVEN'
    MECHANICS='MECHANICS'
    CARRY='CARRY'


class CandidateStatus(Enum):
    OBSERVED='OBSERVED'
    WATCH='WATCH'
    REJECTED='REJECTED'
    ELIGIBLE_FOR_RANKING='ELIGIBLE_FOR_RANKING'


class Direction(Enum):
    UNSPECIFIED='UNSPECIFIED'
    LONG='LONG'
    SHORT='SHORT'
    RELATIVE='RELATIVE'


@dataclass(frozen=True,slots=True)
class OpportunityCandidate:
    family: CandidateFamily
    created_at: datetime
    available_at: datetime
    world_state_id: str
    markets: tuple[str,...]
    direction: Direction
    evidence_refs: tuple[str,...]
    thesis_ref: str
    horizon_seconds: int
    quality: tuple[str,str]
    role: str
    status: CandidateStatus
    candidate_id: str = field(init=False)

    def __post_init__(self):
        utc(self.created_at); utc(self.available_at)
        if self.available_at<self.created_at: raise ValueError('availability before creation')
        if type(self.family) is not CandidateFamily or type(self.direction) is not Direction or type(self.status) is not CandidateStatus:
            raise TypeError('closed candidate enums required')
        if self.role!='PILOT' or type(self.horizon_seconds) is not int or self.horizon_seconds<=0:
            raise ValueError('PILOT and positive horizon required')
        for values in (self.markets,self.evidence_refs):
            if type(values) is not tuple or not values or tuple(sorted(set(values)))!=values or any(type(v) is not str or not v for v in values):
                raise ValueError('canonical immutable references required')
        if type(self.quality) is not tuple or len(self.quality)!=2 or any(q not in ('COMPLETE','INCOMPLETE') for q in self.quality):
            raise ValueError('closed factual quality required')
        if type(self.thesis_ref) is not str or not self.thesis_ref or type(self.world_state_id) is not str or len(self.world_state_id)!=64:
            raise ValueError('world/thesis reference required')
        payload={k:getattr(self,k) for k in self.__dataclass_fields__ if k!='candidate_id'}
        object.__setattr__(self,'candidate_id',commitment(_normalize(payload)))


def make_candidate(world,*,family,markets,created_at,available_at,thesis_ref,horizon_seconds,
                   evidence_refs,direction=Direction.UNSPECIFIED,status=CandidateStatus.OBSERVED):
    if type(world) is not WorldState: raise TypeError('WorldState required')
    utc(created_at); utc(available_at)
    if created_at<world.as_of: raise ValueError('candidate predates world cutoff')
    markets=tuple(sorted(set(markets))); refs=tuple(sorted(set(evidence_refs)))
    known={m.symbol:m for m in world.markets}
    if not markets or set(markets)-known.keys(): raise ValueError('unknown candidate market')
    allowed={world.world_state_id}
    for s in markets:
        allowed.update(e.observation_id for e in (known[s].book,known[s].premium) if e is not None)
    if not refs or set(refs)-allowed: raise ValueError('evidence not in causal world/markets')
    return OpportunityCandidate(family,created_at,available_at,world.world_state_id,markets,direction,refs,
        thesis_ref,horizon_seconds,(world.book_quality.state,world.premium_quality.state),world.role,status)
