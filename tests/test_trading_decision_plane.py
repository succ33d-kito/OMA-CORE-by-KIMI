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
