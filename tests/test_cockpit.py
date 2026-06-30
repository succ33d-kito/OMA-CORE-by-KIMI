"""Tests for O.M.A.-C.O.R.E. Live Cockpit"""
import json
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

from scripts.oma_live_cockpit import (
    load_jsonl,
    load_json,
    safe_get,
    safe_float,
    fmt_float,
    fmt_pct,
    age_from_iso,
    parse_timestamp,
    derive_health,
    derive_bottleneck,
    extract_signal_candidates,
    fmt_dc_state,
    brain_interpretation,
    learning_interpretation,
    alerts_section,
    render_plain,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_telemetry() -> dict:
    return {
        "timestamp": "2026-06-26T06:21:44.193626+00:00",
        "cycle_id": 224,
        "events_collected": 2,
        "events_processed": 2,
        "signals_generated": 2,
        "trades_opened": 0,
        "trades_closed": 0,
        "open_positions": 3,
        "current_equity": 10113.27,
        "daily_pnl": 0,
        "weekly_pnl": 0,
        "max_drawdown": 0.98,
        "capital_guard_mode": "normal",
        "crash_mode": "none",
        "gap_risk_score": 0.0,
        "runtime_errors": 0,
        "data_failures": 5,
        "guard_blocks": 0,
        "execution_blocks": 2,
        "cumulative_signals": 320,
        "cumulative_trades_opened": 14,
        "cumulative_trades_closed": 11,
        "cumulative_guard_blocks": 123,
        "cumulative_execution_blocks": 306,
        "cumulative_errors": 0,
        "_recorded_at": "2026-06-26T06:21:44.193703+00:00",
        "direction_controller_state": {
            "long_window": 5,
            "long_wr": 0.4,
            "long_pf": 0.91,
            "short_window": 6,
            "short_wr": 0.667,
            "short_pf": 2.98,
            "allowed": "both",
            "disable_short": False,
            "disable_long": False,
        },
    }


@pytest.fixture
def sample_exec_audit() -> list[dict]:
    return [
        {
            "timestamp": "2026-06-26T06:06:42.694864+00:00",
            "cycle_id": 223,
            "asset": "ETH",
            "direction": "short",
            "signal_type": "sell",
            "conviction": 93.69,
            "risk_score": 0.3565,
            "block_reason": "execution_capacity_limit",
        },
        {
            "timestamp": "2026-06-26T06:21:44.187481+00:00",
            "cycle_id": 224,
            "asset": "BTC",
            "direction": "short",
            "signal_type": "sell",
            "conviction": 93.69,
            "risk_score": 0.306,
            "block_reason": "execution_capacity_limit",
        },
        {
            "timestamp": "2026-06-26T06:21:44.192538+00:00",
            "cycle_id": 224,
            "asset": "ETH",
            "direction": "short",
            "signal_type": "sell",
            "conviction": 93.69,
            "risk_score": 0.3565,
            "block_reason": "execution_capacity_limit",
        },
    ]


@pytest.fixture
def sample_guard_audit() -> list[dict]:
    return [
        {
            "timestamp": "2026-06-23T22:00:00+00:00",
            "cycle_id": 1,
            "asset": "BTC",
            "direction": "flat",
            "signal_type": "watch",
            "conviction": 58.83,
            "block_reason": "guard_risk_limit",
            "guard_source": "RiskGuard",
        }
    ]


@pytest.fixture
def sample_failures() -> list[dict]:
    return [
        {
            "timestamp": "2026-06-23T23:28:05.923757+00:00",
            "cycle_id": 5,
            "severity": "warning",
            "exception_type": "ConnectionError",
            "impact": "ohlcv_data_unavailable",
        }
    ]


# ── JSONL loading ────────────────────────────────────────────────────────────


def test_load_jsonl(tmp_path):
    f = tmp_path / "test.jsonl"
    f.write_text('{"a": 1}\n{"b": 2}\n')
    assert load_jsonl(f) == [{"a": 1}, {"b": 2}]


def test_load_jsonl_missing(tmp_path):
    assert load_jsonl(tmp_path / "nope.jsonl") == []


def test_load_jsonl_malformed_line(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('{"a": 1}\nnot json\n{"c": 3}\n')
    result = load_jsonl(f)
    assert result == [{"a": 1}, {"c": 3}]


def test_load_json(tmp_path):
    f = tmp_path / "state.json"
    f.write_text('{"cycle_id": 100}')
    assert load_json(f) == {"cycle_id": 100}


def test_load_json_missing(tmp_path):
    assert load_json(tmp_path / "nope.json") == {}


# ── Safe accessors ───────────────────────────────────────────────────────────


def test_safe_get():
    assert safe_get({"a": 1}, "a") == 1
    assert safe_get({"a": 1}, "b") is None
    assert safe_get({"a": 1}, "b", "default") == "default"
    assert safe_get(None, "a") is None
    assert safe_get("notadict", "a") is None


def test_safe_float():
    assert safe_float(3.14) == 3.14
    assert safe_float("3.14") == 3.14
    assert safe_float(None) == 0.0
    assert safe_float(math.inf) == 0.0
    assert safe_float(float("nan")) == 0.0
    assert safe_float("notanumber") == 0.0


def test_fmt_float():
    assert fmt_float(3.14159, 2) == "3.14"
    assert fmt_float(math.inf) == "\u221e"
    assert fmt_float(None) == "0.00"


def test_fmt_pct():
    assert fmt_pct(0.956) == "0.96%"


def test_age_from_iso():
    old = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
    assert "s" in age_from_iso(old)
    assert age_from_iso("") == "unknown"
    assert age_from_iso(None) == "unknown"


def test_parse_timestamp():
    ts = "2026-06-26T06:21:44.193626+00:00"
    assert parse_timestamp(ts) == "06:21:44"
    assert parse_timestamp("") == ""
    assert parse_timestamp(None) == ""


# ── Health derivation ────────────────────────────────────────────────────────


def test_derive_health_runtime_error():
    tel = {"runtime_errors": 1, "crash_mode": "none", "data_failures": 0}
    h, _ = derive_health(tel, {})
    assert h == "CRITICAL"


def test_derive_health_crash_mode():
    tel = {"runtime_errors": 0, "crash_mode": "panic", "data_failures": 0}
    h, _ = derive_health(tel, {})
    assert h == "CRITICAL"


def test_derive_health_data_failures():
    tel = {"runtime_errors": 0, "crash_mode": "none", "data_failures": 3}
    h, _ = derive_health(tel, {})
    assert h == "DEGRADED"


def test_derive_health_healthy():
    tel = {"runtime_errors": 0, "crash_mode": "none", "data_failures": 0}
    h, _ = derive_health(tel, {})
    assert h == "HEALTHY"


# ── Bottleneck derivation ────────────────────────────────────────────────────


def test_bottleneck_exec_capacity(sample_exec_audit):
    tel = {"cumulative_execution_blocks": 300, "cumulative_guard_blocks": 100}
    b = derive_bottleneck(tel, sample_exec_audit, [])
    assert "Execution Capacity Limit" in b


def test_bottleneck_guard(sample_guard_audit):
    tel = {"cumulative_execution_blocks": 0, "cumulative_guard_blocks": 10}
    b = derive_bottleneck(tel, [], sample_guard_audit)
    assert "Guard" in b


def test_bottleneck_data_failures():
    tel = {
        "cumulative_execution_blocks": 0,
        "cumulative_guard_blocks": 0,
        "data_failures": 5,
    }
    b = derive_bottleneck(tel, [], [])
    assert "Data Issues" in b


def test_bottleneck_none():
    tel = {
        "cumulative_execution_blocks": 0,
        "cumulative_guard_blocks": 0,
        "data_failures": 0,
    }
    b = derive_bottleneck(tel, [], [])
    assert "No Major" in b


# ── Signal candidate extraction ──────────────────────────────────────────────


def test_extract_signal_candidates(sample_exec_audit):
    data = {"exec_audit": sample_exec_audit}
    candidates = extract_signal_candidates(data, limit=5)
    assert len(candidates) <= 5
    assert len(candidates) > 0
    # ETH/short/sell at 93.69 appears twice in audit but should be deduplicated
    eth_short_sell = [
        c for c in candidates if c["asset"] == "ETH" and c["direction"] == "short"
    ]
    assert len(eth_short_sell) == 1


def test_extract_signal_candidates_empty():
    assert extract_signal_candidates({"exec_audit": []}, limit=5) == []


def test_extract_signal_candidates_falls_back_to_guard(sample_guard_audit):
    data = {"exec_audit": [], "guard_audit": sample_guard_audit}
    candidates = extract_signal_candidates(data, limit=5)
    assert len(candidates) > 0


# ── Direction controller ─────────────────────────────────────────────────────


def test_fmt_dc_state():
    state = {
        "allowed": "short_only",
        "long_wr": 0.35,
        "long_pf": 0.91,
        "short_wr": 0.667,
        "short_pf": 2.98,
        "disable_long": True,
        "disable_short": False,
    }
    parts = fmt_dc_state(state)
    assert any("short_only" in p for p in parts)
    assert any("0.35%" in p for p in parts)


def test_fmt_dc_state_empty():
    assert fmt_dc_state(None) == ["(no data)"]
    assert fmt_dc_state({}) != ["(no data)"]


# ── Brain interpretation ─────────────────────────────────────────────────────


def test_brain_exec_capacity(sample_telemetry):
    interp = brain_interpretation(sample_telemetry)
    assert "execution capacity" in interp


def test_brain_no_signals():
    tel = {"events_processed": 5, "signals_generated": 0, "trades_opened": 0}
    assert "not producing signals" in brain_interpretation(tel)


def test_brain_executing():
    tel = {"signals_generated": 3, "trades_opened": 1}
    assert "executing normally" in brain_interpretation(tel)


def test_brain_idle():
    assert "idle" in brain_interpretation({})


# ── Learning interpretation ──────────────────────────────────────────────────


def test_learning_interpretation(sample_telemetry):
    lines = learning_interpretation(sample_telemetry)
    assert any("bottleneck detected" in l for l in lines)
    assert any("stability is good" in l for l in lines)
    assert any("reliability needs" in l for l in lines)


def test_learning_empty():
    lines = learning_interpretation({})
    assert len(lines) > 0


# ── Alerts ───────────────────────────────────────────────────────────────────


def test_alerts_not_integrated(sample_telemetry):
    warns = alerts_section(sample_telemetry, Path("."), {"tel_file": None})
    assert any("Scientific layer" in w for w in warns)
    assert any("Outcome bridge" in w for w in warns)


# ── Render ───────────────────────────────────────────────────────────────────


def test_render_plain(sample_telemetry, sample_exec_audit):
    data = {
        "latest_tel": sample_telemetry,
        "run_state": {},
        "exec_audit": sample_exec_audit,
        "latest_exec": sample_exec_audit[-1],
        "guard_audit": [],
        "latest_guard": {},
        "failures": [],
        "tel_file": Path("telemetry_xxx.jsonl"),
        "exec_file": Path("exec_audit_xxx.jsonl"),
        "guard_file": None,
        "fail_file": None,
    }
    output = render_plain(data)
    assert "O.M.A.-C.O.R.E. LIVE COCKPIT" in output
    assert "Cycle: 224" in output
    assert "ETH" in output
    assert "execution_capacity_limit" in output
