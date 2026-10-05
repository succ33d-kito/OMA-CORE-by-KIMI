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
