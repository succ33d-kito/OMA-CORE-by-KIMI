from datetime import timedelta
from tests.test_role_price_window import window
from core.scientific.role_price_window import certify_role_price_window
from core.scientific.causal_regime import append_causal_regime
from core.scientific.causal_mechanics import append_causal_mechanics
from core.scientific.derived_causal_replay import replay_derived_features, reconcile_derived_replay


def test_graph_reconciliation_and_historical_stability(window,tmp_path):
    ledger, ids, cutoff, _ = window
    path = tmp_path/"graph.db"
    before = replay_derived_features(ledger,dataset_role="PILOT",as_of=cutoff,graph_path=path)
    assert before["derived_ids"] == []
    cert = certify_role_price_window(ledger,receipt_ids=ids,dataset_role="PILOT",cutoff=cutoff)
    t = cutoff+timedelta(seconds=1)
    regime = append_causal_regime(ledger,cert,clock=lambda:t)
    mechanics = append_causal_mechanics(ledger,dataset_role="PILOT",cutoff=t,regime_id=regime["id"],clock=lambda:t)
    after = replay_derived_features(ledger,dataset_role="PILOT",as_of=t,graph_path=path)
    assert after["derived_ids"] == sorted([regime["id"],mechanics["id"]])
    assert len(after["dependency_ids"]) == 162
    assert reconcile_derived_replay(ledger,dataset_role="PILOT",as_of=t) == {"status":"MATCH","certificate":after}
    assert replay_derived_features(ledger,dataset_role="PILOT",as_of=cutoff,graph_path=path) == before
    assert replay_derived_features(ledger,dataset_role="CONFIRMATION",as_of=t,graph_path=tmp_path/"other.db")["derived_ids"] == []
