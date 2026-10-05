from dataclasses import FrozenInstanceError, replace
import pytest
from core.runtime.contracts import *

AT='2026-10-05T12:00:00+00:00'


def test_contract_unknowns_immutable_no_scientific_promotions():
    source=DataSourceStatus('price')
    snap=SystemSnapshot(AT,NodeStatus('test'),(source,),DecisionStatus('shadow'),ExecutionStatus('execution'),PositionStatus('positions'),ScientificStatus(source))
    data=snap.to_dict()
    assert data['sources'][0]['details']=={} and data['mode']=='UNKNOWN'
    assert data['science']['edge']=='NOT DEMONSTRATED'
    assert replace(snap)==snap
    with pytest.raises(FrozenInstanceError): snap.mode='LIVE'
    with pytest.raises(ValueError): replace(snap.science,edge='VALIDATED')
    with pytest.raises(ValueError): replace(source,source_at='2026-10-05T12:00:00')
    with pytest.raises(ValueError): replace(source,state=State.AVAILABLE)
