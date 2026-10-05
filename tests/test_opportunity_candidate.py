from dataclasses import FrozenInstanceError
from datetime import timedelta
import pytest
from core.scientific.opportunity_candidate import make_candidate,CandidateFamily,CandidateStatus,Direction
from tests.test_world_state import world


def candidate(w,**changes):
    args=dict(family=CandidateFamily.RELATIVE_VALUE,markets=[w.markets[0].symbol],created_at=w.as_of,
        available_at=w.as_of,thesis_ref='PILOT-descriptive-v0',horizon_seconds=3600,evidence_refs=[w.markets[0].book.observation_id])
    args.update(changes)
    return make_candidate(w,**args)


def test_deterministic_immutable_candidate(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch); a=candidate(w); b=candidate(w)
    assert a==b and a.candidate_id==b.candidate_id and a.world_state_id==w.world_state_id
    assert a.role=='PILOT' and a.status is CandidateStatus.OBSERVED and a.direction is Direction.UNSPECIFIED
    with pytest.raises(FrozenInstanceError): a.status=CandidateStatus.WATCH
    assert candidate(w,status=CandidateStatus.WATCH).candidate_id!=a.candidate_id


@pytest.mark.parametrize('change',[{'family':'ALPHA'},{'markets':['FAKE']},{'evidence_refs':['future']},
                                 {'horizon_seconds':True},{'status':'WINNER'},{'quality':{'pnl':1}}])
def test_closed_model(tmp_path,monkeypatch,change):
    w=world(tmp_path,monkeypatch)
    with pytest.raises((TypeError,ValueError)): candidate(w,**change)


def test_temporal_and_outcome_firewall(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch)
    with pytest.raises(ValueError): candidate(w,created_at=w.as_of-timedelta(seconds=1))
    with pytest.raises(ValueError): candidate(w,available_at=w.as_of-timedelta(seconds=1))
    for key in ('future_return','pnl','score','outcome'):
        with pytest.raises(TypeError): candidate(w,**{key:1})


def test_input_order_canonicalized(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch); symbols=[m.symbol for m in w.markets[:2]]
    refs=[m.book.observation_id for m in w.markets[:2]]
    assert candidate(w,markets=symbols,evidence_refs=refs)==candidate(w,markets=symbols[::-1],evidence_refs=refs[::-1])
