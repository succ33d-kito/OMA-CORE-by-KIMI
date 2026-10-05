"""Descriptive PILOT screening, not Alpha, ranking, or allocation."""
from dataclasses import dataclass,asdict,field
from datetime import datetime
from decimal import Decimal,localcontext
from enum import Enum
from .world_state import WorldState,_normalize
from .multi_market_capture import commitment
from .nuisance_pilot_contracts import utc
from .opportunity_candidate import make_candidate,CandidateFamily,OpportunityCandidate


class Primitive(Enum):
    MARK_INDEX_DISPLACEMENT='MARK_INDEX_DISPLACEMENT'
    FUNDING_DIVERGENCE='FUNDING_DIVERGENCE'
    SPREAD_DIVERGENCE='SPREAD_DIVERGENCE'
    MISSING_EVIDENCE='MISSING_EVIDENCE'


@dataclass(frozen=True,slots=True)
class RadarConfig:
    frozen_at: datetime
    mark_index_fraction: Decimal
    funding_fraction_difference: Decimal
    relative_spread_difference: Decimal
    max_candidates: int
    horizon_seconds: int
    version: str = 'PILOT-DESCRIPTIVE-v0'
    role: str = 'PILOT'
    config_id: str = field(init=False)

    def __post_init__(self):
        utc(self.frozen_at)
        if self.version!='PILOT-DESCRIPTIVE-v0' or self.role!='PILOT': raise ValueError('PILOT only')
        for v in (self.mark_index_fraction,self.funding_fraction_difference,self.relative_spread_difference):
            if type(v) is not Decimal or not v.is_finite() or v<=0: raise ValueError('explicit positive finite fractional threshold required')
        if type(self.max_candidates) is not int or not 1<=self.max_candidates<=5 or type(self.horizon_seconds) is not int or self.horizon_seconds<=0:
            raise ValueError('invalid population cap/horizon')
        values={k:getattr(self,k) for k in self.__dataclass_fields__ if k!='config_id'}
        object.__setattr__(self,'config_id',commitment(_normalize(values)))


@dataclass(frozen=True,slots=True)
class Finding:
    symbol: str
    primitive: Primitive
    value: Decimal | None
    threshold: Decimal | None
    triggered: bool
    evidence_refs: tuple[str,...]


@dataclass(frozen=True,slots=True)
class RadarResult:
    radar_id: str
    world_state_id: str
    universe_id: str
    version: str
    config_id: str
    generated_at: datetime
    universe: tuple[str,...]
    observed: tuple[str,...]
    missing: tuple[str,...]
    candidates: tuple[OpportunityCandidate,...]
    candidate_subjects: tuple[tuple[str,str],...]
    non_candidates: tuple[tuple[str,str],...]
    findings: tuple[Finding,...]
    role: str = 'PILOT'


def _median(values):
    values=sorted(values); n=len(values)
    return None if not n else (values[n//2] if n%2 else (values[n//2-1]+values[n//2])/2)


def scan(world,config,*,generated_at):
    if type(world) is not WorldState or type(config) is not RadarConfig: raise TypeError('closed world/config required')
    utc(generated_at)
    if not config.frozen_at<=world.as_of<=generated_at: raise ValueError('noncausal configuration/run')
    findings=[]; candidates=[]; subjects=[]; non=[]
    observed=tuple(m.symbol for m in world.markets if m.book is not None or m.premium is not None)
    with localcontext() as ctx:
        ctx.prec=100
        funding=[m.premium.funding_rate for m in world.markets if m.premium is not None]
        spreads=[m.spread/m.mid for m in world.markets if m.book is not None]
        fm=_median(funding); sm=_median(spreads)
        funding_refs=tuple(sorted(m.premium.observation_id for m in world.markets if m.premium is not None))
        spread_refs=tuple(sorted(m.book.observation_id for m in world.markets if m.book is not None))
        for m in world.markets:
            local=[]
            if m.premium is not None:
                v=(m.premium.mark-m.premium.index)/m.premium.index
                local.append(Finding(m.symbol,Primitive.MARK_INDEX_DISPLACEMENT,v,config.mark_index_fraction,abs(v)>=config.mark_index_fraction,(m.premium.observation_id,)))
                if len(funding)>=2:
                    v=m.premium.funding_rate-fm
                    local.append(Finding(m.symbol,Primitive.FUNDING_DIVERGENCE,v,config.funding_fraction_difference,abs(v)>=config.funding_fraction_difference,funding_refs))
            if m.book is not None and len(spreads)>=2:
                v=m.spread/m.mid-sm
                local.append(Finding(m.symbol,Primitive.SPREAD_DIVERGENCE,v,config.relative_spread_difference,abs(v)>=config.relative_spread_difference,spread_refs))
            if m.book is None or m.premium is None:
                local.append(Finding(m.symbol,Primitive.MISSING_EVIDENCE,None,None,True,(world.world_state_id,)))
            findings.extend(local)
            triggered=next((f for f in local if f.triggered),None)
            if triggered is None: non.append((m.symbol,'NO_DESCRIPTIVE_TRIGGER')); continue
            if len(candidates)>=config.max_candidates:
                non.append((m.symbol,'LEXICOGRAPHIC_CAP')); continue
            # Full involved cross-section is referenced for comparative primitives.
            involved=tuple(x.symbol for x in world.markets if (x.premium is not None if triggered.primitive is Primitive.FUNDING_DIVERGENCE else x.book is not None)) if triggered.primitive in (Primitive.FUNDING_DIVERGENCE,Primitive.SPREAD_DIVERGENCE) else (m.symbol,)
            candidates.append(make_candidate(world,family=CandidateFamily.CROSS_MARKET if len(involved)>1 or triggered.primitive is Primitive.MISSING_EVIDENCE else CandidateFamily.RELATIVE_VALUE,
                markets=involved,created_at=generated_at,available_at=generated_at,evidence_refs=triggered.evidence_refs,
                thesis_ref=f'{config.version}:{config.config_id}:{m.symbol}:{triggered.primitive.value}',horizon_seconds=config.horizon_seconds))
            subjects.append((m.symbol,candidates[-1].candidate_id))
    universe=tuple(m.symbol for m in world.markets); missing=tuple(s for s in universe if s not in observed)
    payload=dict(world=world.world_state_id,config=config.config_id,at=generated_at,findings=[asdict(f) for f in findings],
                 candidates=[c.candidate_id for c in candidates],non=non)
    return RadarResult(commitment(_normalize(payload)),world.world_state_id,world.universe_id,config.version,config.config_id,
        generated_at,universe,observed,missing,tuple(candidates),tuple(subjects),tuple(non),tuple(findings))
