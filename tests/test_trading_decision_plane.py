from dataclasses import replace,FrozenInstanceError
from datetime import timedelta
import pytest
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
