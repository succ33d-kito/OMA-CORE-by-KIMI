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
from .opportunity_candidate import CandidateFamily


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


class CapitalUnit(Enum):
    FRACTION_OF_CAPITAL='FRACTION_OF_CAPITAL'
    USD_NOTIONAL='USD_NOTIONAL'
    USD_MAX_LOSS='USD_MAX_LOSS'
    RISK_UNIT='RISK_UNIT'


@dataclass(frozen=True,slots=True)
class CapitalAmount:
    unit: CapitalUnit
    value: Decimal | None

    def __post_init__(self):
        if type(self.unit) is not CapitalUnit: raise TypeError('explicit capital unit required')
        if self.value is not None:
            _finite(self.value)
            if self.value<0 or (self.unit is CapitalUnit.FRACTION_OF_CAPITAL and self.value>1): raise ValueError('invalid amount in declared units')


@dataclass(frozen=True,slots=True)
class ExposureLeg:
    symbol: str
    direction: Direction
    venue: str = 'Binance USDⓈ-M'
    product: str = 'linear perpetual'

    def __post_init__(self):
        if self.symbol not in capture.SYMBOLS or type(self.direction) is not Direction or (self.venue,self.product)!=('Binance USDⓈ-M','linear perpetual'):
            raise ValueError('invalid exposure leg')

    @property
    def underlying(self): return self.symbol[:-4]


@dataclass(frozen=True,slots=True)
class Exposure:
    reference_id: str
    family: CandidateFamily
    legs: tuple[ExposureLeg,...]
    risk: CapitalAmount

    def __post_init__(self):
        if type(self.reference_id) is not str or not self.reference_id or type(self.family) is not CandidateFamily or type(self.risk) is not CapitalAmount:
            raise TypeError('explicit exposure identity/family/risk required')
        if type(self.legs) is not tuple or not self.legs or any(type(x) is not ExposureLeg for x in self.legs) or len(set(self.legs))!=len(self.legs): raise ValueError('immutable distinct legs required')


@dataclass(frozen=True,slots=True)
class PortfolioState:
    as_of: datetime
    available_at: datetime
    equity: CapitalAmount
    available_risk_budget: CapitalAmount
    positions: tuple[Exposure,...]
    configuration_commitment: str
    provenance: str = 'SHADOW_CONFIG'
    role: str = 'PILOT'
    portfolio_id: str = field(init=False)

    def __post_init__(self):
        utc(self.as_of); utc(self.available_at); _hash(self.configuration_commitment)
        if self.as_of>self.available_at or self.provenance!='SHADOW_CONFIG' or self.role!='PILOT': raise ValueError('shadow-only causal portfolio required')
        if type(self.equity) is not CapitalAmount or self.equity.unit is not CapitalUnit.USD_NOTIONAL or type(self.available_risk_budget) is not CapitalAmount: raise TypeError('explicit shadow capital/budget required')
        if type(self.positions) is not tuple or any(type(p) is not Exposure for p in self.positions) or len({p.reference_id for p in self.positions})!=len(self.positions): raise ValueError('immutable distinct positions required')
        _seal(self,'portfolio_id')


@dataclass(frozen=True,slots=True)
class ExposureLink:
    left: str
    right: str
    overlaps: tuple[str,...]
    correlation: None = None


@dataclass(frozen=True,slots=True)
class ExposureGraph:
    portfolio_id: str
    references: tuple[str,...]
    links: tuple[ExposureLink,...]
    venue_product_counts: tuple[tuple[str,str,int],...]
    family_counts: tuple[tuple[str,int],...]
    correlation_state: str = 'UNKNOWN'
    graph_id: str = field(init=False)

    def __post_init__(self): _seal(self,'graph_id')


def build_exposure_graph(portfolio,*,proposals=()):
    if type(portfolio) is not PortfolioState or type(proposals) is not tuple or any(type(p) is not Exposure for p in proposals): raise TypeError('explicit portfolio/proposals required')
    all_exposures=tuple(sorted(portfolio.positions+proposals,key=lambda x:x.reference_id))
    if len({p.reference_id for p in all_exposures})!=len(all_exposures): raise ValueError('duplicate exposure identity')
    links=[]; venue={}; families={}
    for i,p in enumerate(all_exposures):
        families[p.family.value]=families.get(p.family.value,0)+1
        for key in {(l.venue,l.product) for l in p.legs}: venue[key]=venue.get(key,0)+1
        for other in all_exposures[i+1:]:
            reasons=[]; shared={l.symbol for l in p.legs}&{l.symbol for l in other.legs}
            if shared: reasons.append('SAME_INSTRUMENT')
            if {l.underlying for l in p.legs}&{l.underlying for l in other.legs}: reasons.append('SAME_UNDERLYING')
            if {l.direction for l in p.legs if l.direction is not Direction.UNSPECIFIED}&{l.direction for l in other.legs if l.direction is not Direction.UNSPECIFIED}: reasons.append('SAME_DIRECTION')
            if shared and (len(p.legs)>1 or len(other.legs)>1): reasons.append('SHARED_MULTI_LEG')
            if {(l.venue,l.product) for l in p.legs}&{(l.venue,l.product) for l in other.legs}: reasons.append('VENUE_PRODUCT')
            if p.family is other.family: reasons.append('CANDIDATE_FAMILY')
            if reasons: links.append(ExposureLink(p.reference_id,other.reference_id,tuple(reasons)))
    return ExposureGraph(portfolio.portfolio_id,tuple(p.reference_id for p in all_exposures),tuple(links),
        tuple((v,p,n) for (v,p),n in sorted(venue.items())),tuple(sorted(families.items())))


class RiskState(Enum):
    APPROVE='APPROVE'
    REDUCE='REDUCE'
    DEFER='DEFER'
    REJECT='REJECT'
    HALT='HALT'


class FutureRiskControl(Enum):
    DRAWDOWN='DRAWDOWN'
    DAILY_LOSS='DAILY_LOSS'
    EVENT_CONCENTRATION='EVENT_CONCENTRATION'
    VOLATILITY='VOLATILITY'
    EXECUTION_COST='EXECUTION_COST'
    CORRELATION='CORRELATION'


@dataclass(frozen=True,slots=True)
class RiskPolicy:
    registered_at: datetime
    unit: CapitalUnit
    position_limit: Decimal | None
    aggregate_limit: Decimal | None
    max_positions: int | None
    max_age_seconds: Decimal | None
    max_instrument_positions: int | None
    max_family_positions: int | None
    max_venue_product_positions: int | None
    require_book: bool
    required_future_controls: tuple[FutureRiskControl,...]
    label: str
    policy_id: str = field(init=False)

    def __post_init__(self):
        utc(self.registered_at)
        if type(self.unit) is not CapitalUnit or self.label!='PILOT_SYNTHETIC_LIMITS' or type(self.require_book) is not bool: raise ValueError('explicit synthetic risk policy required')
        for v in (self.position_limit,self.aggregate_limit,self.max_age_seconds):
            if v is not None:
                _finite(v)
                if v<0: raise ValueError('negative risk limit')
        for v in (self.max_positions,self.max_instrument_positions,self.max_family_positions,self.max_venue_product_positions):
            if v is not None and (type(v) is not int or v<0): raise ValueError('nonnegative explicit count required')
        if type(self.required_future_controls) is not tuple or any(type(x) is not FutureRiskControl for x in self.required_future_controls): raise TypeError('closed required risk controls')
        _seal(self,'policy_id')


@dataclass(frozen=True,slots=True)
class RiskAuthorization:
    candidate: OpportunityCandidate
    world: WorldState
    portfolio: PortfolioState
    request: Exposure
    policy: RiskPolicy
    kill_switch: bool | None
    available_at: datetime
    state: RiskState
    cap: CapitalAmount
    reasons: tuple[str,...]
    authorization_id: str = field(init=False)

    def __post_init__(self): _seal(self,'authorization_id')


def authorize_risk(candidate,world,portfolio,request,policy,*,kill_switch,available_at):
    if (type(candidate),type(world),type(portfolio),type(request),type(policy))!=(OpportunityCandidate,WorldState,PortfolioState,Exposure,RiskPolicy): raise TypeError('closed risk inputs required')
    utc(available_at)
    if not policy.registered_at<=world.as_of<=available_at or candidate.available_at>available_at or portfolio.available_at>available_at:
        raise ValueError('noncausal risk inputs')
    if candidate.world_state_id!=world.world_state_id or request.reference_id!=candidate.candidate_id or request.family is not candidate.family or {l.symbol for l in request.legs}!=set(candidate.markets):
        raise ValueError('risk request scope mismatch')
    if kill_switch is not None and type(kill_switch) is not bool: raise TypeError('explicit kill switch state required')
    def result(state,cap,reason):
        return RiskAuthorization(candidate,world,portfolio,request,policy,kill_switch,available_at,state,CapitalAmount(policy.unit,cap),(reason,))
    if kill_switch is True: return result(RiskState.HALT,Decimal(0),'KILL_SWITCH')
    if kill_switch is None: return result(RiskState.DEFER,None,'KILL_SWITCH_UNKNOWN')
    if policy.required_future_controls: return result(RiskState.DEFER,None,'UNOBSERVED_REQUIRED_CONTROLS:'+','.join(x.value for x in policy.required_future_controls))
    limits=(policy.position_limit,policy.aggregate_limit,policy.max_positions,policy.max_age_seconds,
            policy.max_instrument_positions,policy.max_family_positions,policy.max_venue_product_positions)
    if any(x is None for x in limits): return result(RiskState.DEFER,None,'LIMIT_UNKNOWN')
    if portfolio.equity.value is None or request.risk.value is None or portfolio.available_risk_budget.value is None or any(p.risk.value is None for p in portfolio.positions):
        return result(RiskState.DEFER,None,'CAPITAL_OR_RISK_UNKNOWN')
    if request.risk.unit is not policy.unit or portfolio.available_risk_budget.unit is not policy.unit or any(p.risk.unit is not policy.unit for p in portfolio.positions):
        return result(RiskState.DEFER,None,'INCOMPATIBLE_RISK_UNITS')
    if any(l.direction not in (Direction.LONG,Direction.SHORT) for l in request.legs): return result(RiskState.DEFER,None,'DIRECTION_UNKNOWN')
    if candidate.status is CandidateStatus.REJECTED: return result(RiskState.REJECT,Decimal(0),'CANDIDATE_REJECTED')
    markets={m.symbol:m for m in world.markets}
    for symbol in candidate.markets:
        m=markets[symbol]
        if policy.require_book and m.book is None: return result(RiskState.DEFER,None,'EXECUTION_EVIDENCE_UNKNOWN')
        ages=[(available_at-e.exchange_at).total_seconds() if e.exchange_at is not None else None for e in (m.book,m.premium) if e is not None]
        if not ages or any(a is None for a in ages): return result(RiskState.DEFER,None,'FRESHNESS_UNKNOWN')
        if max(Decimal(str(a)) for a in ages)>policy.max_age_seconds: return result(RiskState.DEFER,None,'STALE_EVIDENCE')
    if len(portfolio.positions)>=policy.max_positions: return result(RiskState.REJECT,Decimal(0),'MAX_POSITIONS')
    for leg in request.legs:
        if sum(any(l.symbol==leg.symbol for l in p.legs) for p in portfolio.positions)>=policy.max_instrument_positions:
            return result(RiskState.REJECT,Decimal(0),'INSTRUMENT_CONCENTRATION')
        if sum(any((l.venue,l.product)==(leg.venue,leg.product) for l in p.legs) for p in portfolio.positions)>=policy.max_venue_product_positions:
            return result(RiskState.REJECT,Decimal(0),'VENUE_PRODUCT_CONCENTRATION')
    if sum(p.family is request.family for p in portfolio.positions)>=policy.max_family_positions: return result(RiskState.REJECT,Decimal(0),'FAMILY_CONCENTRATION')
    from decimal import localcontext
    with localcontext() as ctx:
        ctx.prec=100
        remaining=policy.aggregate_limit-sum((p.risk.value for p in portfolio.positions),Decimal(0))
        cap=max(Decimal(0),min(request.risk.value,policy.position_limit,remaining,portfolio.available_risk_budget.value))
    if cap==0: return result(RiskState.REJECT,cap,'NO_RISK_CAPACITY')
    return result(RiskState.REDUCE if cap<request.risk.value else RiskState.APPROVE,cap,'EXPLICIT_SYNTHETIC_LIMITS')


def verify_authorization(auth):
    if type(auth) is not RiskAuthorization: raise TypeError('risk authorization required')
    expected=authorize_risk(auth.candidate,auth.world,auth.portfolio,auth.request,auth.policy,kill_switch=auth.kill_switch,available_at=auth.available_at)
    if auth!=expected: raise ValueError('risk authorization cannot be forged or overridden')
