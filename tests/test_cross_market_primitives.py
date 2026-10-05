from dataclasses import FrozenInstanceError
from datetime import timedelta
import pytest
from core.scientific.cross_market_primitives import observe_cross_market,RelationshipCandidate,RelationshipFamily
from tests.test_world_state import world


def test_nodes_and_relationship_identity(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch); symbols=[m.symbol for m in w.markets[:2]]
    o=observe_cross_market(w,symbols=symbols)
    assert o==observe_cross_market(w,symbols=symbols[::-1])
    assert len(o.evidence_refs)==4 and all(n.role=='PILOT' for n in o.nodes)
    a=RelationshipCandidate(o,RelationshipFamily.LEAD_LAG_CANDIDATE,'hypothesis-only',w.as_of,60)
    assert a.status=='UNVALIDATED'
    assert a==RelationshipCandidate(o,RelationshipFamily.LEAD_LAG_CANDIDATE,'hypothesis-only',w.as_of,60)
    with pytest.raises(FrozenInstanceError): a.status='VALIDATED'


def test_no_promotions_or_outcomes(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch); o=observe_cross_market(w,symbols=[m.symbol for m in w.markets[:2]])
    with pytest.raises(ValueError): RelationshipCandidate(o,RelationshipFamily.CORRELATION_CANDIDATE,'h',w.as_of,status='VALIDATED')
    with pytest.raises(ValueError): RelationshipCandidate(o,RelationshipFamily.RETURN_RELATIVE,'h',w.as_of-timedelta(seconds=1))
    with pytest.raises(TypeError): RelationshipCandidate(o,RelationshipFamily.RETURN_RELATIVE,'h',w.as_of,future_return=1)


def test_missing_market_not_invented(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch)
    from core.scientific.world_state import load_world
    empty=load_world(tmp_path/'universe',as_of=w.as_of)
    with pytest.raises(ValueError): observe_cross_market(empty,symbols=[m.symbol for m in w.markets[:2]])
