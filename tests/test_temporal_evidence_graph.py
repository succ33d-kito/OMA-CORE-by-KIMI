from datetime import datetime, timedelta, timezone
import pytest
from core.intelligence_graph import EvidenceGraph, Node, Edge
from core.decision_domain.record import DecisionRecord, DecisionOutcome

T = datetime(2026, 9, 29, tzinfo=timezone.utc)
def node(id, kind, time=T, **payload):
    return Node(id, kind, time, time, 'test:synthetic', payload)

def test_complete_case_and_temporal_visibility(tmp_path):
    graph = EvidenceGraph(tmp_path/'graph.db')
    graph.append([node('s','source'),node('e','event'),node('h','hypothesis'),node('v','evidence')],
                 [Edge('se','s','e','observes',T),Edge('eh','e','h','motivates',T),Edge('vs','v','s','derived_from',T),Edge('vh','v','h','supports',T)])
    decision = DecisionRecord('d','e','h',T,T,'WAIT',('REJECT',),('v',),('s',),None,'observe','missing feed',(),('feed',))
    graph.record_decision(decision,'test:journal')
    graph.record_decision(decision,'test:journal')
    later=T+timedelta(hours=1)
    graph.record_outcome(DecisionOutcome('d','o',later,('still blocked',)),later,'test:receipt')
    assert len(graph.as_of(T)['nodes']) == 5
    assert len(graph.as_of(later)['nodes']) == 6
    assert any(e['relation']=='produces' for e in graph.as_of(later)['edges'])
    assert EvidenceGraph(tmp_path/'graph.db').as_of(later)==graph.as_of(later)

@pytest.mark.parametrize('failure', ['unknown','future','kind','conflict','outcome','direction'])
def test_invalid_batch_rolls_back(tmp_path, failure):
    g=EvidenceGraph(tmp_path/'g.db')
    g.append([node('s','source'),node('h','hypothesis'),node('v','evidence'),node('d','decision')])
    edges=[]; nodes=[node('new','event')]
    if failure=='unknown': edges=[Edge('x','missing','d','informs',T)]
    if failure=='future':
        nodes.append(node('future','evidence',T+timedelta(hours=1)))
        edges=[Edge('x','future','d','informs',T+timedelta(hours=1))]
    if failure=='kind': edges=[Edge('x','s','h','supports',T)]
    if failure=='conflict': nodes.append(node('s','source',different=True))
    if failure=='outcome':
        nodes.append(node('o','outcome',T-timedelta(hours=1)))
        edges=[Edge('x','d','o','produces',T)]
    if failure=='direction': edges=[Edge('x','v','h','supports',T),Edge('y','v','h','contradicts',T)]
    with pytest.raises(ValueError): g.append(nodes,edges)
    assert len(g.as_of(T+timedelta(days=1))['nodes'])==4

def test_missing_decision_refs_and_no_promotion(tmp_path):
    g=EvidenceGraph(tmp_path/'g.db')
    d=DecisionRecord('d','absent',None,T,T,'WAIT',(),(),(),None,'x','y',(),())
    with pytest.raises(ValueError): g.record_decision(d,'test')
    with pytest.raises(ValueError): g.append([node('k','knowledge_candidate',promoted=True)])
    with pytest.raises(ValueError): g.append([Node('n','source',T.replace(tzinfo=None),T,'test',{})])
    assert not g.as_of(T)['nodes']

def test_bundled_case_is_reproducible_and_retrospective(tmp_path):
    from pathlib import Path
    from scripts.build_evidence_graph_case import build
    import json
    root=Path(__file__).resolve().parents[1]
    first=build(root,tmp_path,T)
    original=(tmp_path/'case.json').read_bytes()
    assert build(root,tmp_path,T)==first
    assert (tmp_path/'case.json').read_bytes()==original
    assert first['promotion']=='NONE'
    case=json.loads(original)
    assert len(case['nodes'])==7
    assert all(n['available_at'] >= T.isoformat() for n in case['nodes'])
