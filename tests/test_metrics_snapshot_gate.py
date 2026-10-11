from copy import deepcopy
from datetime import timedelta
import pytest
from core.scientific.metrics_snapshot_gate import metrics_snapshot_available
from core.scientific.prospective_receipts import observation_snapshot
from core.scientific import causal_observation_snapshot as fabric
from tests.test_causal_replay import prepare_ledger
from tests.test_metrics_continuity import state,S


def prepared(state,tmp_path):
    ledger=prepare_ledger(state,tmp_path)
    rows,_=observation_snapshot(ledger,read_only=True)
    return ledger,rows,next(iter(rows))


def test_complete_bundle_and_requested_subset(state,tmp_path):
    ledger,rows,identity=prepared(state,tmp_path)
    assert all(metrics_snapshot_available(rows,key,S+timedelta(minutes=5)) for key in rows)
    before=ledger.read_bytes()
    result=fabric.load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=S+timedelta(minutes=5),
                                      features=('MarketMetrics/OpenInterest',))
    assert len(result.observations)==1 and ledger.read_bytes()==before
    assert not metrics_snapshot_available(rows,identity,S+timedelta(minutes=4))


@pytest.mark.parametrize('mutation',['missing','role','availability','payload','source','contract','metadata'])
def test_one_inconsistent_member_excludes_entire_bundle(state,tmp_path,monkeypatch,mutation):
    ledger,rows,identity=prepared(state,tmp_path)
    changed=deepcopy(rows); other=next(key for key in changed if key!=identity); row=changed[other]
    if mutation=='missing': del changed[other]
    elif mutation=='role': row['provenance']['dataset_role']='CONFIRMATION'
    elif mutation=='availability': row['available_at']=(S+timedelta(minutes=6)).isoformat()
    elif mutation=='payload': row['payload']['value']+=1
    elif mutation=='source': row['source']='unverified'
    elif mutation=='contract': row['provenance']['contract']='other'
    else: row['provenance']['component_metadata']['http_status']=451
    assert not metrics_snapshot_available(changed,identity,S+timedelta(minutes=7))
    monkeypatch.setattr(fabric,'observation_snapshot',lambda *a,**k:(changed,[]))
    snapshot=fabric.load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=S+timedelta(minutes=7))
    assert snapshot.observations==()
