"""PILOT shadow decision contracts. No broker, outcomes, or demonstrated Edge."""
from dataclasses import dataclass,field,fields,is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from .world_state import WorldState,_normalize
from .opportunity_candidate import OpportunityCandidate
from .opportunity_candidate import Direction
from .multi_market_capture import commitment
from .nuisance_pilot_contracts import utc
from . import multi_market_capture as capture
from pathlib import Path
from .opportunity_radar import RadarResult
from .opportunity_candidate import CandidateStatus


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


class ForecastKind(Enum):
    RAW_SCORE='RAW_SCORE'
    PROBABILITY='PROBABILITY'
    EXPECTED_RETURN='EXPECTED_RETURN'
    DISTRIBUTION='DISTRIBUTION'
    DIRECTIONAL_VIEW='DIRECTIONAL_VIEW'


class CalibrationState(Enum):
    UNKNOWN='UNKNOWN'
    UNCALIBRATED='UNCALIBRATED'
    CALIBRATED='CALIBRATED'


def _finite(value):
    if type(value) is not Decimal or not value.is_finite(): raise TypeError('finite Decimal required; no implicit unit conversion')


@dataclass(frozen=True,slots=True)
class Forecast:
    thesis: Thesis
    kind: ForecastKind
    value: Decimal | Direction | tuple | None
    calibration: CalibrationState
    method_id: str
    method_provenance_commitment: str
    evidence_refs: tuple[str,...]
    created_at: datetime
    available_at: datetime
    uncertainty_interval: tuple[Decimal,Decimal] | None = None
    forecast_id: str = field(init=False)

    def __post_init__(self):
        if type(self.thesis) is not Thesis or type(self.kind) is not ForecastKind or type(self.calibration) is not CalibrationState: raise TypeError('closed forecast types required')
        utc(self.created_at); utc(self.available_at)
        if not self.thesis.available_at<=self.created_at<=self.available_at: raise ValueError('noncausal forecast')
        _hash(self.method_provenance_commitment); _refs(self.evidence_refs,empty=False)
        if type(self.method_id) is not str or not self.method_id: raise ValueError('identified method required')
        known=evidence_times(self.thesis.world)
        if any(r not in known or known[r]>self.available_at for r in self.evidence_refs): raise ValueError('unknown/future forecast evidence')
        if self.calibration is CalibrationState.CALIBRATED:
            raise ValueError('v0 has no accredited calibration proof adapter; CALIBRATED unavailable')
        probabilistic=self.kind in (ForecastKind.PROBABILITY,ForecastKind.DISTRIBUTION)
        if not probabilistic and self.calibration is not CalibrationState.UNKNOWN: raise ValueError('calibration applies to probability/distribution')
        if self.kind is ForecastKind.EXPECTED_RETURN and self.value is not None:
            raise ValueError('expected return UNKNOWN: no accredited forecasting method registered in v0')
        if self.value is not None:
            if self.kind is ForecastKind.DIRECTIONAL_VIEW:
                if type(self.value) is not Direction: raise TypeError('explicit directional view required')
            elif self.kind is ForecastKind.DISTRIBUTION:
                if type(self.value) is not tuple or not self.value: raise TypeError('immutable discrete distribution required')
                from decimal import localcontext
                with localcontext() as ctx:
                    ctx.prec=100
                    total=Decimal(0); outcomes=[]
                    for point in self.value:
                        if type(point) is not tuple or len(point)!=2: raise TypeError('scenario return fraction, probability pairs required')
                        x,p=point; _finite(x); _finite(p)
                        if not 0<=p<=1: raise ValueError('probability outside [0,1]')
                        total+=p; outcomes.append(x)
                    if total!=1 or len(set(outcomes))!=len(outcomes): raise ValueError('invalid distribution mass/scenarios')
            else:
                _finite(self.value)
                if self.kind is ForecastKind.PROBABILITY and not 0<=self.value<=1: raise ValueError('probability outside [0,1]')
        if self.uncertainty_interval is not None:
            if self.kind in (ForecastKind.DIRECTIONAL_VIEW,ForecastKind.DISTRIBUTION) or type(self.uncertainty_interval) is not tuple or len(self.uncertainty_interval)!=2:
                raise TypeError('explicit scalar uncertainty interval required')
            low,high=self.uncertainty_interval; _finite(low); _finite(high)
            if low>high or (self.value is not None and not low<=self.value<=high): raise ValueError('invalid uncertainty bounds')
            if self.kind is ForecastKind.PROBABILITY and not 0<=low<=high<=1: raise ValueError('probability interval outside [0,1]')
        _seal(self,'forecast_id')

    @property
    def role(self): return self.thesis.role
    @property
    def horizon_seconds(self): return self.thesis.candidate_horizon
    @property
    def economic_probability(self): return None  # No accredited calibration in v0.
    @property
    def unit(self):
        return {ForecastKind.RAW_SCORE:'ARBITRARY_SCORE',ForecastKind.PROBABILITY:'PROBABILITY_FRACTION',
            ForecastKind.EXPECTED_RETURN:'RETURN_FRACTION',ForecastKind.DISTRIBUTION:'RETURN_FRACTION_PROBABILITY_MASS',
            ForecastKind.DIRECTIONAL_VIEW:'DIRECTION'}[self.kind]


class RankingCriterion(Enum):
    COMPLETENESS='COMPLETENESS'
    CONTRADICTIONS='CONTRADICTIONS'
    EVIDENCE_BREADTH='EVIDENCE_BREADTH'
    FRESHNESS='FRESHNESS'
    FORECAST_AVAILABLE='FORECAST_AVAILABLE'
    EXECUTION_OBSERVED='EXECUTION_OBSERVED'
    CANDIDATE_AGE='CANDIDATE_AGE'


@dataclass(frozen=True,slots=True)
class RankingPolicy:
    criteria: tuple[RankingCriterion,...]
    registered_at: datetime
    policy_id: str
    label: str = 'PILOT_PRIORITY'


def register_ranking_policy(directory,*,criteria):
    if type(criteria) is not tuple or not criteria or any(type(c) is not RankingCriterion for c in criteria) or len(set(criteria))!=len(criteria):
        raise ValueError('explicit unique ranking criteria required')
    root=Path(directory); root.mkdir(parents=True,exist_ok=False)
    params=dict(criteria=[c.value for c in criteria],label='PILOT_PRIORITY',tie_break='CANDIDATE_ID_ASC',unknown='LAST')
    capture._write(root/'parameters.json',capture._json(params))
    at=capture._now(); utc(at)
    payload=dict(parameters=params,registered_at=at.isoformat())
    capture._write(root/'policy.json',capture._json(dict(payload=payload,commitment=commitment(payload))))
    return load_ranking_policy(root)


def load_ranking_policy(directory):
    root=Path(directory); saved=capture._read_json(root/'policy.json'); p=saved['payload']
    if set(saved)!={'payload','commitment'} or saved['commitment']!=commitment(p) or set(p)!={'parameters','registered_at'}:
        raise ValueError('ranking registration mismatch')
    params=capture._read_json(root/'parameters.json')
    if p['parameters']!=params or set(params)!={'criteria','label','tie_break','unknown'} or (params['label'],params['tie_break'],params['unknown'])!=('PILOT_PRIORITY','CANDIDATE_ID_ASC','LAST'):
        raise ValueError('ranking policy changed')
    criteria=tuple(RankingCriterion(x) for x in params['criteria'])
    if not criteria or len(set(criteria))!=len(criteria): raise ValueError('invalid ranking criteria')
    at=datetime.fromisoformat(p['registered_at']); utc(at)
    return RankingPolicy(criteria,at,saved['commitment'])


@dataclass(frozen=True,slots=True)
class OpportunityQualityVector:
    candidate_id: str
    completeness: Decimal
    contradictions: int | None
    evidence_breadth: int
    freshness_seconds: float | None
    forecast_available: bool
    calibration: CalibrationState
    execution_observed: bool
    candidate_age_seconds: float


@dataclass(frozen=True,slots=True)
class GlobalRanking:
    radar_id: str
    world_state_id: str
    candidate_set_commitment: str
    candidate_ids: tuple[str,...]
    ordered: tuple[str,...]
    vectors: tuple[OpportunityQualityVector,...]
    excluded: tuple[tuple[str,str],...]
    policy: RankingPolicy
    available_at: datetime
    label: str = 'PILOT_PRIORITY'
    ranking_id: str = field(init=False)

    def __post_init__(self): _seal(self,'ranking_id')


class GlobalOpportunityRanker:
    @staticmethod
    def rank(world,radar,policy_directory,*,theses=(),forecasts=(),available_at):
        if type(world) is not WorldState or type(radar) is not RadarResult or type(theses) is not tuple or type(forecasts) is not tuple:
            raise TypeError('immutable world/radar/theses/forecasts required')
        utc(available_at); policy=load_ranking_policy(policy_directory)
        if not policy.registered_at<=world.as_of<=radar.generated_at<=available_at or radar.world_state_id!=world.world_state_id:
            raise ValueError('noncausal ranking or changed world')
        candidates={c.candidate_id:c for c in radar.candidates}
        if len(candidates)!=len(radar.candidates): raise ValueError('duplicate candidate')
        tm={x.candidate_id:x for x in theses}; fm={x.thesis.candidate_id:x for x in forecasts}
        if len(tm)!=len(theses) or len(fm)!=len(forecasts) or (set(tm)|set(fm))-candidates.keys(): raise ValueError('duplicate/foreign thesis or forecast')
        for x in theses+forecasts:
            thesis=x if type(x) is Thesis else x.thesis
            if thesis.world_state_id!=world.world_state_id or x.available_at>available_at: raise ValueError('future/foreign ranking evidence')
        market={m.symbol:m for m in world.markets}; vectors=[]; excluded=[]
        from decimal import localcontext
        with localcontext() as ctx:
            ctx.prec=100
            for cid,c in sorted(candidates.items()):
                if c.world_state_id!=world.world_state_id or c.available_at>available_at: raise ValueError('future/foreign candidate')
                ms=[market[s] for s in c.markets]; present=sum(e is not None for m in ms for e in (m.book,m.premium))
                ages=[a for m in ms for a,e in ((m.book_age_seconds,m.book),(m.premium_age_seconds,m.premium)) if e is not None]
                v=OpportunityQualityVector(cid,Decimal(present)/Decimal(2*len(ms)),
                    len(tm[cid].contradicting_evidence_refs) if cid in tm else None,len(c.evidence_refs),
                    max(ages)+(available_at-world.as_of).total_seconds() if ages and all(a is not None for a in ages) else None,cid in fm,
                    fm[cid].calibration if cid in fm else CalibrationState.UNKNOWN,
                    all(m.book is not None for m in ms),(available_at-c.created_at).total_seconds())
                vectors.append(v)
                if c.status is CandidateStatus.REJECTED: excluded.append((cid,'CANDIDATE_REJECTED'))
                elif cid in tm and tm[cid].expiry is not None and tm[cid].expiry<=available_at: excluded.append((cid,'THESIS_EXPIRED'))
        def key(v):
            values={RankingCriterion.COMPLETENESS:(v.completeness,True),RankingCriterion.CONTRADICTIONS:(v.contradictions,False),
                RankingCriterion.EVIDENCE_BREADTH:(v.evidence_breadth,True),RankingCriterion.FRESHNESS:(v.freshness_seconds,False),
                RankingCriterion.FORECAST_AVAILABLE:(int(v.forecast_available),True),RankingCriterion.EXECUTION_OBSERVED:(int(v.execution_observed),True),
                RankingCriterion.CANDIDATE_AGE:(v.candidate_age_seconds,False)}
            result=[]
            for criterion in policy.criteria:
                value,descending=values[criterion]; result.append((value is None,0 if value is None else (-value if descending else value)))
            return (*result,v.candidate_id)
        excluded_ids={cid for cid,_ in excluded}; ordered=tuple(v.candidate_id for v in sorted(vectors,key=key) if v.candidate_id not in excluded_ids)
        ids=tuple(sorted(candidates))
        return GlobalRanking(radar.radar_id,world.world_state_id,commitment(ids),ids,ordered,tuple(vectors),tuple(excluded),policy,available_at)
