from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from math import sqrt
from types import SimpleNamespace

import pytest

from core.market_mechanics import build_market_state
from core.decision_domain import DecisionJournal
from core.decision_domain.paper_adapter import record_paper_signal
from tests.test_paper_decision_adapter import signal


T = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)


def bars():
    data = [dict(time=T - timedelta(hours=21-i), open=100, high=101,
                 low=99, close=100, volume=10) for i in range(21)]
    data[-1].update(high=105, close=104, volume=20)
    return data


def state(data=None, **kwargs):
    args = dict(source_id="fixture:spot:BTC:1h", observed_at=T, as_of=T)
    args.update(kwargs)
    return build_market_state("BTC", bars() if data is None else data, **args)


def test_range_excludes_current_bar_and_volume_uses_prior_baseline():
    s = state()
    assert s.prior_high == 101
    assert s.prior_low == 99
    assert s.range_status == "above_prior_range"
    assert s.volume_ratio == 2
    assert s.last_return == pytest.approx(0.04)
    assert s.return_volatility == pytest.approx(0.04 / sqrt(20))
    assert s.state_id == state().state_id
    assert "order_flow" in s.unknown_dimensions
    assert len(s.input_bars) == 21


@pytest.mark.parametrize("mutation", [
    lambda b: b[-1].update(time=T),
    lambda b: b[-1].update(time=b[-2]["time"]),
    lambda b: b[-1].update(close=float("nan")),
    lambda b: b[-1].update(volume=-1),
    lambda b: b[-1].update(high=90),
    lambda b: b[-1].update(time=T.replace(tzinfo=None)),
    lambda b: b.pop(5),
])
def test_rejects_unusable_or_future_input(mutation):
    data = bars()
    mutation(data)
    with pytest.raises(ValueError):
        state(data)


def test_available_time_staleness_and_missing_volume_baseline():
    with pytest.raises(ValueError, match="available"):
        state(observed_at=T + timedelta(seconds=1))
    with pytest.raises(ValueError, match="stale"):
        state(as_of=T + timedelta(hours=3))
    data = bars()
    for b in data:
        b["volume"] = 0
    assert state(data).volume_ratio is None


def test_decision_keeps_reproducible_snapshot_without_promoting_it_to_evidence(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    data = bars()
    s = state(data)
    sig = signal()
    did = record_paper_signal(journal, SimpleNamespace(id="e1", source="demo", source_id=None),
                              None, sig, market_state=s)
    data[-1]["close"] = 999
    saved, _ = journal.history(did)
    frozen = json.loads(saved["market_state_snapshot"])
    assert frozen["last_close"] == 104
    assert saved["market_state_id"] == s.state_id
    assert saved["evidence_ids"] == []
    assert "market_state_id" not in saved["missing_information"]
    assert "derivatives" in saved["missing_information"]
    sig.asset = "ETH"
    with pytest.raises(ValueError, match="asset/time"):
        record_paper_signal(journal, SimpleNamespace(id="e1", source="demo", source_id=None),
                            None, sig, market_state=s)


def test_demo_filters_open_bar_and_drops_stale_cached_prices(tmp_path, monkeypatch):
    import scripts.extended_demo_realtime as demo
    monkeypatch.setattr(demo, "OUT_DIR", str(tmp_path))
    monkeypatch.setattr(demo, "STATE_FILE", str(tmp_path / "run_state.json"))
    harness = demo.DemoHarness(symbols=["BTC"])
    rows = [[int((T - timedelta(hours=60-i)).timestamp()*1000), 100, 101, 99, 100, 10]
            for i in range(61)]
    monkeypatch.setattr(demo.req, "get", lambda *a, **k: SimpleNamespace(status_code=200, json=lambda: rows))
    harness._refresh_market_data()
    assert len(harness._agent_ohlcv["BTC"]) == 60
    assert harness._market_states["BTC"].last_bar_closed_at == T.isoformat()
    monkeypatch.setattr(harness, "_fetch_ohlcv", lambda symbol: None)
    harness._refresh_market_data()
    assert harness._last_prices == {}
    assert harness._market_states == {}
