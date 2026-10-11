from copy import deepcopy
from datetime import timedelta
import pytest
from tests.test_role_price_window import window
from core.scientific.role_price_window import certify_role_price_window
from core.scientific.causal_regime import append_causal_regime, load_causal_regimes, validate_causal_regime
from core.scientific.prospective_receipts import observation_snapshot


def test_regime_persistence_replay_and_roles(window):
    ledger, ids, cutoff, _ = window
    cert = certify_role_price_window(ledger, receipt_ids=ids, dataset_role="PILOT", cutoff=cutoff)
    now = cutoff+timedelta(seconds=1)
    row = append_causal_regime(ledger, cert, clock=lambda:now)
    assert row["provenance"]["regime_method"] == "er20-vol20-vs-prior60-v1"
    assert row["provenance"]["semantic_status"] == "DESCRIPTIVE_HEURISTIC_NOT_PROBABILITY"
    assert len(row["dependencies"]) == 162
    assert load_causal_regimes(ledger, dataset_role="PILOT", as_of=cutoff) == ()
    assert load_causal_regimes(ledger, dataset_role="DISCOVERY", as_of=now) == ()
    assert load_causal_regimes(ledger, dataset_role="PILOT", as_of=now) == (row,)
    assert append_causal_regime(ledger, cert, clock=lambda:now+timedelta(seconds=1)) == row
    known, _ = observation_snapshot(ledger, read_only=True)
    for field, value in (("payload", {}), ("source", "fake"), ("dependencies", ids), ("id", "fake")):
        altered = {**row, field:value}
        with pytest.raises(ValueError):
            validate_causal_regime(known, altered, dataset_role="PILOT", cutoff=now)
    with pytest.raises(ValueError):
        validate_causal_regime(known, row, dataset_role="CONFIRMATION", cutoff=now)
    with pytest.raises(ValueError):
        append_causal_regime(ledger, cert, clock=lambda:cutoff-timedelta(seconds=1))
