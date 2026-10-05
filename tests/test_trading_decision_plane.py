from dataclasses import replace,FrozenInstanceError
from datetime import timedelta
import pytest
from decimal import Decimal
from core.scientific import trading_decision_plane as t
from tests.test_world_state import world
from tests.test_opportunity_candidate import candidate


def thesis(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch); c=candidate(w)
    return t.Thesis(c,w,w.as_of,w.as_of,'REFERENCE hypothesis only',c.evidence_refs,(),
        ('Evidence is descriptive',),('No calibrated model',),('Input invalidated',),'a'*64)


def test_thesis_identity_and_contradiction_preserved(tmp_path,monkeypatch):
    a=thesis(tmp_path,monkeypatch)
    assert replace(a)==a and a.role=='PILOT' and a.candidate_horizon==3600
    b=replace(a,contradicting_evidence_refs=a.supporting_evidence_refs)
    assert b.contradiction_state=='CONFLICTING' and b.thesis_id!=a.thesis_id
    assert b.contradicting_evidence_refs==a.supporting_evidence_refs
    with pytest.raises(FrozenInstanceError): b.premises=()


def test_thesis_causality_and_closed_fields(tmp_path,monkeypatch):
    a=thesis(tmp_path,monkeypatch)
    with pytest.raises(ValueError): replace(a,supporting_evidence_refs=('unknown',))
    with pytest.raises(ValueError): replace(a,created_at=a.created_at-timedelta(seconds=1))
    with pytest.raises(ValueError): replace(a,available_at=a.available_at-timedelta(seconds=1))
    with pytest.raises(TypeError): replace(a,pnl=1)
    with pytest.raises(TypeError): replace(a,premises=['mutable'])


def forecast(a,**changes):
    args=dict(thesis=a,kind=t.ForecastKind.RAW_SCORE,value=Decimal('0.72'),calibration=t.CalibrationState.UNKNOWN,
        method_id='REFERENCE-NON_VALIDATED',method_provenance_commitment='b'*64,evidence_refs=a.supporting_evidence_refs,
        created_at=a.available_at,available_at=a.available_at)
    args.update(changes); return t.Forecast(**args)


def test_score_not_probability_and_unknown_not_neutral(tmp_path,monkeypatch):
    a=thesis(tmp_path,monkeypatch); f=forecast(a)
    assert f.unit=='ARBITRARY_SCORE' and f.economic_probability is None
    p=forecast(a,kind=t.ForecastKind.PROBABILITY,calibration=t.CalibrationState.UNCALIBRATED)
    assert p.value==Decimal('0.72') and p.economic_probability is None and p.forecast_id!=f.forecast_id
    assert forecast(a,kind=t.ForecastKind.PROBABILITY,value=None).value is None
    assert forecast(a,kind=t.ForecastKind.EXPECTED_RETURN,value=None).value is None
    with pytest.raises(ValueError): forecast(a,kind=t.ForecastKind.EXPECTED_RETURN)
    with pytest.raises(ValueError): replace(p,calibration=t.CalibrationState.CALIBRATED)


def test_forecast_causality_units_and_distribution(tmp_path,monkeypatch):
    a=thesis(tmp_path,monkeypatch)
    with pytest.raises(TypeError): forecast(a,value=0.72)
    with pytest.raises(ValueError): forecast(a,kind=t.ForecastKind.PROBABILITY,value=Decimal('72'))
    with pytest.raises(ValueError): forecast(a,evidence_refs=('unknown',))
    with pytest.raises(ValueError): forecast(a,available_at=a.available_at-timedelta(seconds=1))
    f=forecast(a,kind=t.ForecastKind.DISTRIBUTION,calibration=t.CalibrationState.UNCALIBRATED,
        value=((Decimal('-0.01'),Decimal('0.5')),(Decimal('0.01'),Decimal('0.5'))))
    assert f.economic_probability is None and f.horizon_seconds==3600
    with pytest.raises(ValueError): replace(f,value=((Decimal('0'),Decimal('0.8')),))


def ranked(tmp_path,monkeypatch):
    from tests.test_opportunity_radar import config
    from core.scientific.opportunity_radar import scan
    from tests.test_multi_market_capture import T
    w=world(tmp_path,monkeypatch); radar=scan(w,config(),generated_at=w.as_of)
    monkeypatch.setattr(t.capture,'_now',lambda:T+timedelta(seconds=10))
    t.register_ranking_policy(tmp_path/'ranking',criteria=(t.RankingCriterion.COMPLETENESS,t.RankingCriterion.CONTRADICTIONS,t.RankingCriterion.EVIDENCE_BREADTH))
    r=t.GlobalOpportunityRanker.rank(w,radar,tmp_path/'ranking',available_at=w.as_of)
    return w,radar,r


def test_global_ranking_all_candidates_factual_deterministic(tmp_path,monkeypatch):
    w,radar,r=ranked(tmp_path,monkeypatch)
    assert len(r.ordered)==len(radar.candidates)==2
    assert r.label=='PILOT_PRIORITY' and all(v.contradictions is None for v in r.vectors)
    assert all(v.calibration is t.CalibrationState.UNKNOWN for v in r.vectors)
    assert r==t.GlobalOpportunityRanker.rank(w,radar,tmp_path/'ranking',available_at=w.as_of)
    assert r.ordered==tuple(sorted(r.ordered))
    later=t.GlobalOpportunityRanker.rank(w,radar,tmp_path/'ranking',available_at=w.as_of+timedelta(seconds=10))
    assert later.vectors[0].freshness_seconds==r.vectors[0].freshness_seconds+10
    with pytest.raises(FrozenInstanceError): r.ordered=()


def test_ranking_config_mutation_and_foreign_candidate_blocked(tmp_path,monkeypatch):
    w,radar,r=ranked(tmp_path,monkeypatch)
    bad=replace(radar,world_state_id='f'*64)
    with pytest.raises(ValueError): t.GlobalOpportunityRanker.rank(w,bad,tmp_path/'ranking',available_at=w.as_of)
    p=tmp_path/'ranking'/'parameters.json'; p.write_bytes(p.read_bytes().replace(b'LAST',b'FIRST'))
    with pytest.raises(ValueError): t.GlobalOpportunityRanker.rank(w,radar,tmp_path/'ranking',available_at=w.as_of)


def portfolio(at,positions=()):
    return t.PortfolioState(at,at,t.CapitalAmount(t.CapitalUnit.USD_NOTIONAL,Decimal('10000')),
        t.CapitalAmount(t.CapitalUnit.RISK_UNIT,Decimal('10')),positions,'c'*64)


def test_shadow_capital_units_unknown_and_overlaps(tmp_path,monkeypatch):
    a=thesis(tmp_path,monkeypatch)
    x=t.Exposure('x',t.CandidateFamily.CROSS_MARKET,(t.ExposureLeg('BTCUSDT',t.Direction.LONG),),t.CapitalAmount(t.CapitalUnit.RISK_UNIT,None))
    y=t.Exposure('y',t.CandidateFamily.CROSS_MARKET,(t.ExposureLeg('BTCUSDT',t.Direction.LONG),t.ExposureLeg('ETHUSDT',t.Direction.SHORT)),t.CapitalAmount(t.CapitalUnit.RISK_UNIT,Decimal('2')))
    p=portfolio(a.available_at,(x,)); g=t.build_exposure_graph(p,proposals=(y,))
    assert p.provenance=='SHADOW_CONFIG' and x.risk.value is None
    assert g.correlation_state=='UNKNOWN' and g.links[0].correlation is None
    assert set(g.links[0].overlaps)=={'SAME_INSTRUMENT','SAME_UNDERLYING','SAME_DIRECTION','SHARED_MULTI_LEG','VENUE_PRODUCT','CANDIDATE_FAMILY'}
    with pytest.raises(ValueError): replace(p,provenance='BROKER_OBSERVED')
    with pytest.raises(ValueError): t.CapitalAmount(t.CapitalUnit.FRACTION_OF_CAPITAL,Decimal('10'))
    with pytest.raises(TypeError): t.CapitalAmount(t.CapitalUnit.USD_NOTIONAL,1.0)


def risk_policy(at,**changes):
    args=dict(registered_at=at,unit=t.CapitalUnit.RISK_UNIT,position_limit=Decimal('2'),aggregate_limit=Decimal('10'),
        max_positions=5,max_age_seconds=Decimal('10000'),max_instrument_positions=1,max_family_positions=5,max_venue_product_positions=5,
        require_book=True,required_future_controls=(),label='PILOT_SYNTHETIC_LIMITS')
    args.update(changes); return t.RiskPolicy(**args)


def authorization(w,c,**changes):
    p=portfolio(w.as_of); request=t.Exposure(c.candidate_id,c.family,tuple(t.ExposureLeg(s,t.Direction.LONG) for s in c.markets),t.CapitalAmount(t.CapitalUnit.RISK_UNIT,Decimal('3')))
    args=dict(candidate=c,world=w,portfolio=p,request=request,policy=risk_policy(w.as_of),kill_switch=False,available_at=w.as_of)
    args.update(changes); return t.authorize_risk(**args)


def test_risk_halt_unknown_reduce_and_no_forgery(tmp_path,monkeypatch):
    w,radar,r=ranked(tmp_path,monkeypatch); c=radar.candidates[0]
    a=authorization(w,c)
    assert a.state is t.RiskState.REDUCE and a.cap.value==2<a.request.risk.value
    t.verify_authorization(a)
    assert authorization(w,c,kill_switch=True).state is t.RiskState.HALT
    assert authorization(w,c,kill_switch=None).state is t.RiskState.DEFER
    assert authorization(w,c,policy=risk_policy(w.as_of,position_limit=None)).state is t.RiskState.DEFER
    assert authorization(w,c,policy=risk_policy(w.as_of,required_future_controls=(t.FutureRiskControl.EXECUTION_COST,))).state is t.RiskState.DEFER
    assert authorization(w,c,policy=risk_policy(w.as_of,max_positions=0)).state is t.RiskState.REJECT
    with pytest.raises(ValueError): t.verify_authorization(replace(a,cap=t.CapitalAmount(t.CapitalUnit.RISK_UNIT,Decimal('99'))))


def test_unknown_position_risk_is_not_zero(tmp_path,monkeypatch):
    w,radar,r=ranked(tmp_path,monkeypatch); c=radar.candidates[0]
    old=t.Exposure('old',c.family,(t.ExposureLeg('BTCUSDT',t.Direction.LONG),),t.CapitalAmount(t.CapitalUnit.RISK_UNIT,None))
    assert authorization(w,c,portfolio=portfolio(w.as_of,(old,))).state is t.RiskState.DEFER


def allocation(tmp_path,monkeypatch,*,budget=Decimal('3'),max_positions=5,halt=False):
    w,radar,r=ranked(tmp_path,monkeypatch)
    auths=tuple(authorization(w,c,policy=risk_policy(w.as_of,max_positions=max_positions),kill_switch=(halt and i==0)) for i,c in enumerate(radar.candidates))
    return t.allocate_capital(r,portfolio(w.as_of),auths,t.CapitalAmount(t.CapitalUnit.RISK_UNIT,budget),t.AllocationPolicy(w.as_of,True),available_at=w.as_of)


def test_allocation_joint_budget_halt_and_unknown(tmp_path,monkeypatch):
    p=allocation(tmp_path/'normal',monkeypatch)
    assert [r.amount.value for r in p.rows]==[Decimal('2'),Decimal('1')] and p.unallocated.value==0
    t.verify_allocation(p)
    h=allocation(tmp_path/'halt',monkeypatch,halt=True)
    assert all(r.amount.value==0 and r.reason=='HALTED' for r in h.rows) and h.unallocated.value==3
    unknown=allocation(tmp_path/'unknown',monkeypatch,budget=None)
    assert all(r.amount.value==0 for r in unknown.rows) and unknown.unallocated.value is None


def test_joint_position_limit_and_tamper(tmp_path,monkeypatch):
    p=allocation(tmp_path,monkeypatch,max_positions=1)
    assert sum(r.amount.value for r in p.rows)==2 and p.unallocated.value==1
    assert p.rows[1].reason=='PORTFOLIO_RISK_REJECTED'
    bad=replace(p,rows=(replace(p.rows[0],amount=t.CapitalAmount(t.CapitalUnit.RISK_UNIT,Decimal('99'))),p.rows[1]))
    with pytest.raises(ValueError): t.verify_allocation(bad)
    with pytest.raises(ValueError): t.allocate_capital(p.ranking,p.portfolio,p.authorizations[:1],p.budget,p.policy,available_at=p.available_at)


def shadow(tmp_path,monkeypatch):
    w,radar,_=ranked(tmp_path,monkeypatch)
    theses=tuple(t.Thesis(c,w,w.as_of,w.as_of,'REFERENCE only',c.evidence_refs,(),('descriptive',),('unvalidated',),('invalid input',),'a'*64) for c in radar.candidates)
    forecasts=tuple(forecast(a,kind=t.ForecastKind.DIRECTIONAL_VIEW,value=t.Direction.UNSPECIFIED) for a in theses)
    ranking=t.GlobalOpportunityRanker.rank(w,radar,tmp_path/'ranking',theses=theses,forecasts=forecasts,available_at=w.as_of)
    auths=tuple(authorization(w,c) for c in radar.candidates)
    plan=t.allocate_capital(ranking,portfolio(w.as_of),auths,t.CapitalAmount(t.CapitalUnit.RISK_UNIT,Decimal('3')),t.AllocationPolicy(w.as_of,True),available_at=w.as_of)
    return t.ShadowCapitalDecision(w,radar,theses,forecasts,plan,w.as_of,'d'*64)


def test_shadow_frozen_complete_chain_and_new_config_identity(tmp_path,monkeypatch):
    d=shadow(tmp_path,monkeypatch)
    assert d.state is t.ShadowState.WOULD_ALLOCATE and replace(d)==d
    assert replace(d,configuration_commitment='e'*64).decision_id!=d.decision_id
    with pytest.raises(FrozenInstanceError): d.state=t.ShadowState.HALTED
    with pytest.raises(TypeError): replace(d,pnl=1)
    with pytest.raises(ValueError): replace(d,available_at=d.available_at-timedelta(seconds=1))
    with pytest.raises(ValueError): replace(d,theses=())
    altered=replace(d.theses[0],assumptions=('different assumptions',))
    with pytest.raises(ValueError): replace(d,theses=(altered,)+d.theses[1:])
