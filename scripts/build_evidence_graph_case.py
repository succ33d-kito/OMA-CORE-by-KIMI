"""Reproduce a retrospective governance case; never an ex-ante market forecast."""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.intelligence_graph import EvidenceGraph, Node, Edge
from core.decision_domain.record import DecisionRecord, DecisionOutcome

def build(root, output, recorded_at):
    root, output = Path(root), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = root/'research/metrics_2024_2025/CONFIRMATORY_2024_2025_REPORT.md'
    digest = hashlib.sha256(report.read_bytes()).hexdigest()
    # This is a current import of a historical report, not availability in 2024.
    t = recorded_at
    provenance = f'repo:{report.relative_to(root)}#sha256={digest}'
    g = EvidenceGraph(output/'case.sqlite')
    nodes = [Node('metrics-report','source',t,t,provenance,{'sha256':digest}),
             Node('review','event',t,t,provenance,{'mode':'retrospective_review'}),
             Node('stability','hypothesis',t,t,provenance,{'claim':'derivatives improve incremental stability', 'status':'historical_rejected_claim'}),
             Node('negative-gate','evidence',t,t,provenance,{'direction':'contradicts','gate':'FAIL','scope':'2024 versus 2025; no causal identification'})]
    edges = [Edge('source-review','metrics-report','review','observes',t),
             Edge('review-claim','review','stability','motivates',t),
             Edge('evidence-source','negative-gate','metrics-report','derived_from',t),
             Edge('evidence-claim','negative-gate','stability','contradicts',t)]
    g.append(nodes,edges)
    d = DecisionRecord('no-promotion','review','stability',t,t,'KEEP_RESEARCH_ONLY',
                       ('PROMOTE',),('negative-gate',),('metrics-report',),None,
                       'No Knowledge/Criterion/trading promotion from this gate',
                       'New independent evidence requires its own frozen protocol',(),
                       ('eligible prospective live feed',),rationale='Retrospective documentation of failed gate')
    g.record_decision(d,provenance)
    later=t+timedelta(microseconds=1)
    g.record_outcome(DecisionOutcome(d.decision_id,'recorded-result',later,
                                    ('Negative result retained in graph; no promotion action exists in this component',)),later,provenance)
    g.append([Node('lesson-candidate','knowledge_candidate',later,later,provenance,
                   {'promoted':False,'status':'unreviewed','claim':'Fragmentation and multiplicity must be controlled; extra significant cells alone do not establish improvement'})],
             [Edge('result-candidate','recorded-result','lesson-candidate','candidate_from',later)])
    snapshot=g.as_of(later)
    data=(json.dumps(snapshot,sort_keys=True,indent=2)+'\n').encode()
    (output/'case.json').write_bytes(data)
    manifest={'mode':'retrospective_governance_case','recorded_at':t.isoformat(),
              'report_sha256':digest,'snapshot_sha256':hashlib.sha256(data).hexdigest(),
              'nodes':len(snapshot['nodes']),'edges':len(snapshot['edges']),
              'promotion':'NONE','command':'python scripts/build_evidence_graph_case.py --recorded-at '+t.isoformat()}
    (output/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--recorded-at',required=True,help='Explicit timezone-aware import time; never backdate to market period')
    p.add_argument('--output',default='research/evidence_graph_case')
    a=p.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[1],a.output,datetime.fromisoformat(a.recorded_at)),indent=2))
