from copy import deepcopy
from dataclasses import replace

import pytest

from core.scientific.mechanics_comparison import (
    ComparisonProtocol, candidate_rows, compare, simulate_long,
)
from scripts.compare_market_mechanics import synthetic_bars


def test_future_changes_do_not_change_earlier_candidates():
    bars = synthetic_bars(180)
    original = candidate_rows(bars, "BTC", "fixture", ComparisonProtocol())
    changed = deepcopy(bars)
    for bar in changed[150:]:
        for key in ("open", "high", "low", "close"):
            bar[key] *= 10
    altered = candidate_rows(changed, "BTC", "fixture", ComparisonProtocol())
    assert [r for r in original if r["index"] < 150] == [r for r in altered if r["index"] < 150]


def test_next_open_costs_and_ambiguous_bar_use_stop():
    bars = synthetic_bars(5)
    bars[0].update(open=1, high=1, low=1, close=1)
    bars[1].update(open=100, high=110, low=90, close=102)
    p = ComparisonProtocol(horizon=2, slippage_bps_per_side=0, fee_bps_per_side=10)
    trade = simulate_long(bars, 0, p)
    assert trade["entry"] == 100
    assert trade["exit"] == 98
    assert trade["reason"] == "stop"
    assert trade["net_return"] == pytest.approx(-.02 - .001*1.98)


def test_gap_stop_uses_gap_open_and_costs_reduce_return():
    bars = synthetic_bars(4)
    bars[1].update(open=100, high=101, low=99, close=100)
    bars[2].update(open=90, high=91, low=89, close=90)
    p = ComparisonProtocol(horizon=2, fee_bps_per_side=0, slippage_bps_per_side=0)
    trade = simulate_long(bars, 0, p)
    assert trade["exit"] == 90
    assert trade["reason"] == "gap_stop"
    assert simulate_long(bars, 0, replace(p, fee_bps_per_side=10))["net_return"] < trade["net_return"]


def test_splits_no_overlap_no_boundary_crossing_and_reproducibility():
    bars = synthetic_bars(360)
    a = compare(bars, symbol="BTC", source_id="fixture", data_kind="synthetic")
    assert a == compare(bars, symbol="BTC", source_id="fixture", data_kind="synthetic")
    assert a["verdict"] == "synthetic_smoke_only"
    for policy in ("baseline", "mechanics_filter"):
        dev = a["results"]["development"][policy]["trades"]
        holdout = a["results"]["holdout"][policy]["trades"]
        assert all(t["exit_index"] < a["split_index"] for t in dev)
        assert all(t["signal_index"] >= a["split_index"]+24 for t in holdout)
        for trades in (dev, holdout):
            assert all(right["entry_index"] > left["exit_index"] for left, right in zip(trades, trades[1:]))
    assert all(not r["mechanics_filter"] or r["baseline"] for r in a["candidates"])
