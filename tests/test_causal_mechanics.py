from datetime import timedelta
import pytest
from tests.test_role_price_window import window
from core.scientific.causal_mechanics import build_causal_mechanics, append_causal_mechanics, validate_causal_mechanics, UNSUPPORTED
from core.scientific.causal_regime import append_causal_regime
from core.scientific.role_price_window import certify_role_price_window


def test_descriptive_mechanics_unknowns_and_replay(window):
    ledger, ids, cutoff, _ = window
    original = build_causal_mechanics(ledger, dataset_role="PILOT", cutoff=cutoff)
    assert original["unknown_dimensions"] == dict.fromkeys(UNSUPPORTED)
    assert original["regime"] is None
    assert list(original["raw_values"]) == ["Price/OHLCV"]
    assert original == build_causal_mechanics(ledger, dataset_role="PILOT", cutoff=cutoff)
    other = build_causal_mechanics(ledger, dataset_role="DISCOVERY", cutoff=cutoff)
    assert other["raw_values"] == {} and other["dependencies"] == []
    with pytest.raises(ValueError):
        append_causal_mechanics(ledger, dataset_role="DISCOVERY", cutoff=cutoff, clock=lambda:cutoff)
    row = append_causal_mechanics(ledger, dataset_role="PILOT", cutoff=cutoff, clock=lambda:cutoff)
    assert validate_causal_mechanics(ledger,row,dataset_role="PILOT",cutoff=cutoff) == row
    assert build_causal_mechanics(ledger,dataset_role="PILOT",cutoff=cutoff) == original
    assert append_causal_mechanics(ledger,dataset_role="PILOT",cutoff=cutoff,clock=lambda:cutoff) == row
    with pytest.raises(ValueError):
        validate_causal_mechanics(ledger,{**row,"payload":{}},dataset_role="PILOT",cutoff=cutoff)


def test_exact_derived_dependency(window):
    ledger, ids, cutoff, _ = window
    cert = certify_role_price_window(ledger,receipt_ids=ids,dataset_role="PILOT",cutoff=cutoff)
    later = cutoff+timedelta(seconds=1)
    regime = append_causal_regime(ledger,cert,clock=lambda:later)
    for role, when in (("PILOT",cutoff),("DISCOVERY",later)):
        with pytest.raises(ValueError):
            build_causal_mechanics(ledger,dataset_role=role,cutoff=when,regime_id=regime["id"])
    view = build_causal_mechanics(ledger,dataset_role="PILOT",cutoff=later,regime_id=regime["id"])
    assert regime["id"] in view["dependencies"]
    assert view["regime"]["source_id"] == regime["id"]
    row = append_causal_mechanics(ledger,dataset_role="PILOT",cutoff=later,
        regime_id=regime["id"],clock=lambda:later)
    assert validate_causal_mechanics(ledger,row,dataset_role="PILOT",cutoff=later) == row


from tests.test_metrics_continuity import state, S
from tests.test_causal_latent_context import admit_metrics


def test_authenticated_metrics_preserve_levels_and_ratios(state,tmp_path):
    ledger = tmp_path/"metrics.db"
    admit_metrics(state,ledger)
    cutoff = S+timedelta(minutes=5)
    view = build_causal_mechanics(ledger,dataset_role="PILOT",cutoff=cutoff)
    assert "MarketMetrics/OpenInterest" in view["raw_values"]
    assert "MarketMetrics/TakerBuySellRatio" in view["raw_values"]
    assert view["unknown_dimensions"]["open_interest_change"] is None
    assert view["unknown_dimensions"]["aggressor_imbalance"] is None
    row = append_causal_mechanics(ledger,dataset_role="PILOT",cutoff=cutoff,clock=lambda:cutoff)
    assert validate_causal_mechanics(ledger,row,dataset_role="PILOT",cutoff=cutoff) == row
    assert append_causal_mechanics(ledger,dataset_role="PILOT",cutoff=cutoff,clock=lambda:cutoff) == row
    assert build_causal_mechanics(ledger,dataset_role="CONFIRMATION",cutoff=cutoff)["raw_values"] == {}
