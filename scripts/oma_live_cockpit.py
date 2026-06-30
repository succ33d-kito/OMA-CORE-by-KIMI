#!/usr/bin/env python3
"""O.M.A.-C.O.R.E. Live Cockpit — Terminal observability tool.

Usage:
    python3 scripts/oma_live_cockpit.py            # live refresh every 5s
    python3 scripts/oma_live_cockpit.py --once      # single snapshot
    python3 scripts/oma_live_cockpit.py --interval 10
    python3 scripts/oma_live_cockpit.py --path _extended_demo
    python3 scripts/oma_live_cockpit.py --plain     # force plain text

Reads telemetry_*.jsonl, execution_audit_*.jsonl, guard_audit_*.jsonl,
failures_*.jsonl, and run_state.json from the telemetry directory.
"""

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── Rich import (graceful fallback) ──────────────────────────────────────────

HAS_RICH = False
try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.text import Text
    from rich.panel import Panel
    from rich.layout import Layout
    from rich import box

    HAS_RICH = True
except ImportError:
    pass

# ── File loading ─────────────────────────────────────────────────────────────


def latest_file(directory: Path, pattern: str) -> Optional[Path]:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def load_jsonl(path: Path) -> list[dict]:
    records = []
    if not path or not path.exists():
        return records
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records


def load_json(path: Path) -> dict:
    if path and path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def safe_get(d: Any, key: str, default: Any = None) -> Any:
    if isinstance(d, dict):
        return d.get(key, default)
    return default


def safe_float(v: Any) -> float:
    if v is None:
        return 0.0
    try:
        f = float(v)
        if math.isinf(f) or math.isnan(f):
            return 0.0
        return f
    except (ValueError, TypeError):
        return 0.0


def fmt_float(v: Any, decimals: int = 2) -> str:
    if v is None:
        return "0.00"
    try:
        f = float(v)
        if math.isinf(f):
            return "\u221e"
        if math.isnan(f):
            return "NaN"
        return f"{f:.{decimals}f}"
    except (ValueError, TypeError):
        return str(v)


def fmt_pct(v: Any) -> str:
    return fmt_float(v, 2) + "%"


def age_from_iso(iso_str: str) -> str:
    if not iso_str:
        return "unknown"
    try:
        dt = datetime.fromisoformat(iso_str)
        delta = datetime.now(timezone.utc) - dt
        total = delta.total_seconds()
        if total < 60:
            return f"{int(total)}s"
        if total < 3600:
            return f"{int(total // 60)}m {int(total % 60)}s"
        if total < 86400:
            return f"{int(total // 3600)}h {int((total % 3600) // 60)}m"
        return f"{int(total // 86400)}d {int((total % 86400) // 3600)}h"
    except (ValueError, TypeError):
        return "unknown"


def parse_timestamp(ts: Any) -> str:
    if not ts:
        return ""
    s = str(ts)
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return s[:19] if len(s) > 19 else s


# ── Health / bottleneck derivation ───────────────────────────────────────────


def derive_health(telemetry: dict, run_state: dict) -> tuple[str, str]:
    rt_err = safe_get(telemetry, "runtime_errors", 0) or safe_get(run_state, "runtime_errors", 0)
    crash = safe_get(telemetry, "crash_mode", "none")
    data_fail = safe_get(telemetry, "data_failures", 0) or safe_get(run_state, "data_failures", 0)

    if rt_err > 0 or crash != "none":
        return "CRITICAL", "CRITICAL"
    if data_fail > 0:
        return "DEGRADED", "DEGRADED"
    return "HEALTHY", "HEALTHY"


def derive_bottleneck(
    telemetry: dict, exec_audit: list[dict], guard_audit: list[dict]
) -> str:
    exec_blocks = safe_get(telemetry, "cumulative_execution_blocks", 0)
    guard_blocks = safe_get(telemetry, "cumulative_guard_blocks", 0)

    if exec_audit:
        last_exec = exec_audit[-1]
        if safe_get(last_exec, "block_reason") == "execution_capacity_limit":
            return "Execution Capacity Limit"
        if safe_get(last_exec, "block_reason"):
            return f"Execution Blocked: {last_exec['block_reason']}"

    if guard_audit:
        last_guard = guard_audit[-1]
        br = safe_get(last_guard, "block_reason", "")
        if br and br != "unknown":
            return f"Guard: {br}"

    if safe_get(telemetry, "data_failures", 0) > 0:
        return "Data Issues"

    return "No Major Bottleneck"


# ── Data loading ─────────────────────────────────────────────────────────────


def load_all(directory: Path) -> dict:
    tel_file = latest_file(directory, "telemetry_*.jsonl")
    exec_file = latest_file(directory, "execution_audit_*.jsonl")
    guard_file = latest_file(directory, "guard_audit_*.jsonl")
    fail_file = latest_file(directory, "failures_*.jsonl")
    run_state_file = directory / "run_state.json"

    tel_records = load_jsonl(tel_file)
    exec_records = load_jsonl(exec_file)
    guard_records = load_jsonl(guard_file)
    fail_records = load_jsonl(fail_file)
    run_state = load_json(run_state_file)

    latest_tel = tel_records[-1] if tel_records else {}
    return {
        "telemetry": tel_records,
        "latest_tel": latest_tel,
        "exec_audit": exec_records,
        "latest_exec": exec_records[-1] if exec_records else {},
        "guard_audit": guard_records,
        "latest_guard": guard_records[-1] if guard_records else {},
        "failures": fail_records,
        "run_state": run_state,
        "tel_file": tel_file,
        "exec_file": exec_file,
        "guard_file": guard_file,
        "fail_file": fail_file,
    }


# ── Signal candidate extraction (deduplicated) ───────────────────────────────


def extract_signal_candidates(data: dict, limit: int = 5) -> list[dict]:
    records = data.get("exec_audit", [])
    if not records:
        records = data.get("guard_audit", [])
    if not records:
        return []

    seen = set()
    candidates = []
    for r in reversed(records):
        asset = safe_get(r, "asset", "?")
        direction = safe_get(r, "direction", "?")
        signal_type = safe_get(r, "signal_type", "?")
        conviction = round(safe_float(r.get("conviction", 0)), 1)
        block_reason = safe_get(r, "block_reason", "?")
        key = (asset, direction, signal_type, conviction, block_reason)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            {
                "asset": asset,
                "direction": direction,
                "signal_type": signal_type,
                "conviction": conviction,
                "risk_score": safe_get(r, "risk_score", "?"),
                "block_reason": block_reason,
            }
        )
        if len(candidates) >= limit:
            break
    return candidates


# ── Direction controller formatting ──────────────────────────────────────────


def fmt_dc_state(state: Any) -> list[str]:
    if not isinstance(state, dict):
        return ["(no data)"]
    parts = []
    parts.append(f"Allowed: {safe_get(state, 'allowed', '?')}")
    long_wr = safe_get(state, "long_wr")
    parts.append(f"Long WR: {fmt_pct(long_wr) if long_wr is not None else '?'}")
    long_pf = safe_get(state, "long_pf")
    parts.append(f"Long PF: {fmt_float(long_pf) if long_pf is not None else '?'}")
    short_wr = safe_get(state, "short_wr")
    parts.append(f"Short WR: {fmt_pct(short_wr) if short_wr is not None else '?'}")
    short_pf = safe_get(state, "short_pf")
    parts.append(f"Short PF: {fmt_float(short_pf) if short_pf is not None else '?'}")
    parts.append(f"Disable Long: {safe_get(state, 'disable_long', '?')}")
    parts.append(f"Disable Short: {safe_get(state, 'disable_short', '?')}")
    return parts


# ── Interpretation strings ───────────────────────────────────────────────────


def brain_interpretation(tel: dict) -> str:
    signals = safe_get(tel, "signals_generated", 0)
    opened = safe_get(tel, "trades_opened", 0)
    events_proc = safe_get(tel, "events_processed", 0)
    cum_exec_blocks = safe_get(tel, "cumulative_execution_blocks", 0)
    open_pos = safe_get(tel, "open_positions", 0)

    if cum_exec_blocks > 0 and open_pos >= 3:
        return "System is generating signals but execution capacity is limiting action"
    if events_proc > 0 and signals == 0:
        return "System is active but not producing signals"
    if opened > 0:
        return "System is executing normally"
    return "System is idle"


def learning_interpretation(tel: dict) -> list[str]:
    lines = []
    cum_sig = safe_get(tel, "cumulative_signals", 0)
    cum_open = safe_get(tel, "cumulative_trades_opened", 0)
    cum_close = safe_get(tel, "cumulative_trades_closed", 0)
    cum_exec_blocks = safe_get(tel, "cumulative_execution_blocks", 0)
    cum_guard_blocks = safe_get(tel, "cumulative_guard_blocks", 0)
    rt_err = safe_get(tel, "runtime_errors", 0)
    data_fail = safe_get(tel, "data_failures", 0)

    exec_block_ratio = cum_exec_blocks / cum_sig if cum_sig > 0 else 0
    guard_block_ratio = cum_guard_blocks / cum_sig if cum_sig > 0 else 0
    capture_ratio = cum_open / cum_sig if cum_sig > 0 else 0
    close_ratio = cum_close / cum_open if cum_open > 0 else 0

    if exec_block_ratio > 0.5:
        lines.append("Capital allocation bottleneck detected.")
    if guard_block_ratio > 0.3:
        lines.append("Guard intervention rate is high.")
    if capture_ratio < 0.1 and cum_sig > 0:
        lines.append("Many signals are not becoming trades.")
    if rt_err == 0:
        lines.append("Operational stability is good.")
    if data_fail > 0:
        lines.append("Data reliability needs review.")
    if not lines:
        lines.append("(awaiting more data for interpretation)")
    return lines


def alerts_section(tel: dict, directory: Path, data: dict) -> list[str]:
    warns = []

    tel_file = data.get("tel_file")
    if tel_file:
        tel_path = Path(tel_file) if not isinstance(tel_file, Path) else tel_file
        age = age_from_iso(str(data.get("latest_tel", {}).get("_recorded_at", "")))
        warns.append(f"Telemetry age: {age}")
    else:
        warns.append("No telemetry file found.")

    exec_file = data.get("exec_file")
    if not exec_file:
        warns.append("No execution audit file found.")

    fail_file = data.get("fail_file")
    if not fail_file:
        warns.append("No failures file found.")

    if safe_get(tel, "cumulative_execution_blocks", 0) > 100:
        warns.append("Repeated execution_capacity_limit detected.")

    warns.append("Scientific layer not integrated yet.")
    warns.append("Outcome bridge not active yet.")

    return warns


# ── Plain text rendering ─────────────────────────────────────────────────────


def render_plain(data: dict) -> str:
    tel = data["latest_tel"]
    run_state = data["run_state"]
    exec_audit = data["exec_audit"]
    guard_audit = data["guard_audit"]
    failures = data["failures"]

    health, _ = derive_health(tel, run_state)
    bottleneck = derive_bottleneck(tel, exec_audit, guard_audit)

    recorded_at = str(safe_get(tel, "_recorded_at", ""))
    age = age_from_iso(recorded_at)
    cycle_id = safe_get(tel, "cycle_id", safe_get(run_state, "cycle_id", "?"))
    latest_ts = parse_timestamp(safe_get(tel, "timestamp", ""))

    lines = []
    sep = "=" * 60

    # HEADER
    lines.append(sep)
    lines.append("O.M.A.-C.O.R.E. LIVE COCKPIT")
    lines.append(sep)
    lines.append(
        f"  Status: RUNNING    Cycle: {cycle_id}    "
        f"Latest: {latest_ts}    Age: {age}"
    )
    lines.append(f"  Health: {health}    Bottleneck: {bottleneck}")
    lines.append("")

    # TOP OPPORTUNITIES
    lines.append("── TOP OPPORTUNITIES / SIGNALS ──────────────────────────────")
    candidates = extract_signal_candidates(data, limit=5)
    if candidates:
        lines.append(
            f"  {'Asset':<8} {'Dir':<8} {'Type':<10} "
            f"{'Conv':<8} {'Risk':<8} {'Block Reason'}"
        )
        lines.append(
            f"  {'─'*6:<8} {'─'*6:<8} {'─'*8:<10} "
            f"{'─'*6:<8} {'─'*6:<8} {'─'*20}"
        )
        for c in candidates:
            lines.append(
                f"  {c['asset']:<8} {c['direction']:<8} {c['signal_type']:<10} "
                f"{c['conviction']:<8} {c['risk_score']:<8} {c['block_reason']}"
            )
    else:
        lines.append("  No recent opportunity/signal data available.")
    lines.append("")

    # BRAIN
    lines.append("── BRAIN / REASONING STATE ──────────────────────────────────")
    fields = [
        ("Events Collected", "events_collected", ""),
        ("Events Processed", "events_processed", ""),
        ("Signals (this cycle)", "signals_generated", ""),
        ("Cumulative Signals", "cumulative_signals", ""),
        ("Trades Opened", "trades_opened", ""),
        ("Trades Closed", "trades_closed", ""),
        ("Cumulative Opened", "cumulative_trades_opened", ""),
        ("Cumulative Closed", "cumulative_trades_closed", ""),
        ("Open Positions", "open_positions", ""),
        ("Exec Blocks (cycle)", "execution_blocks", ""),
        ("Cumulative Exec Blocks", "cumulative_execution_blocks", ""),
        ("Guard Blocks (cycle)", "guard_blocks", ""),
        ("Cumulative Guard Blocks", "cumulative_guard_blocks", ""),
    ]
    for label, key, _ in fields:
        val = safe_get(tel, key, safe_get(run_state, key, "?"))
        lines.append(f"  {label:<30} {val}")
    lines.append(f"  {'─'*40}")
    lines.append(f"  >> {brain_interpretation(tel)}")
    lines.append("")

    # WORLD
    lines.append("── WORLD STATE / EVENT FLOW ─────────────────────────────────")
    for label, key in [
        ("Events Collected", "events_collected"),
        ("Events Processed", "events_processed"),
        ("Data Failures", "data_failures"),
        ("Gap Risk Score", "gap_risk_score"),
        ("Crash Mode", "crash_mode"),
        ("Capital Guard Mode", "capital_guard_mode"),
    ]:
        lines.append(f"  {label:<25} {safe_get(tel, key, safe_get(run_state, key, '?'))}")
    lines.append("")

    # EXECUTION / PORTFOLIO
    lines.append("── EXECUTION / PORTFOLIO ────────────────────────────────────")
    for label, key in [
        ("Current Equity", "current_equity"),
        ("Max Drawdown", "max_drawdown"),
        ("Daily PnL", "daily_pnl"),
        ("Weekly PnL", "weekly_pnl"),
        ("Open Positions", "open_positions"),
        ("Capital Guard Mode", "capital_guard_mode"),
    ]:
        lines.append(f"  {label:<25} {safe_get(tel, key, '?')}")
    last_exec = data.get("latest_exec", {})
    if last_exec:
        lines.append(
            f"  Latest Exec Block Reason: {safe_get(last_exec, 'block_reason', '?')}"
        )
        lines.append(
            f"  Latest Blocked Asset/Dir: "
            f"{safe_get(last_exec, 'asset', '?')} / "
            f"{safe_get(last_exec, 'direction', '?')} / "
            f"Conv {safe_get(last_exec, 'conviction', '?')}"
        )
    lines.append("")

    # DIRECTION CONTROLLER
    lines.append("── DIRECTION CONTROLLER ─────────────────────────────────────")
    dc = safe_get(tel, "direction_controller_state", {})
    for l in fmt_dc_state(dc):
        lines.append(f"  {l}")
    lines.append("")

    # LEARNING / CRITERION READINESS
    lines.append("── LEARNING / CRITERION READINESS ───────────────────────────")
    cum_sig = safe_get(tel, "cumulative_signals", 0)
    cum_open = safe_get(tel, "cumulative_trades_opened", 0)
    cum_close = safe_get(tel, "cumulative_trades_closed", 0)
    cum_exec_blocks = safe_get(tel, "cumulative_execution_blocks", 0)
    cum_guard_blocks = safe_get(tel, "cumulative_guard_blocks", 0)

    capture_ratio = cum_open / cum_sig if cum_sig > 0 else 0
    exec_block_ratio = cum_exec_blocks / cum_sig if cum_sig > 0 else 0
    guard_block_ratio = cum_guard_blocks / cum_sig if cum_sig > 0 else 0
    close_ratio = cum_close / cum_open if cum_open > 0 else 0

    lines.append(f"  Opportunity Capture Ratio:    {fmt_pct(capture_ratio)}")
    lines.append(f"  Execution Block Ratio:        {fmt_pct(exec_block_ratio)}")
    lines.append(f"  Guard Block Ratio:            {fmt_pct(guard_block_ratio)}")
    lines.append(f"  Closed Trade Ratio:           {fmt_pct(close_ratio)}")
    lines.append(f"  {'─'*40}")
    for l in learning_interpretation(tel):
        lines.append(f"  >> {l}")
    lines.append("")

    # ALERTS / DIAGNOSTICS
    lines.append("── ALERTS / DIAGNOSTICS ─────────────────────────────────────")
    for w in alerts_section(tel, Path("."), data):
        lines.append(f"  ! {w}")
    lines.append("")

    # FOOTER
    lines.append(sep)
    lines.append(
        f"  Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    lines.append(sep)

    return "\n".join(lines)


# ── Rich rendering ───────────────────────────────────────────────────────────


def make_rich_layout(data: dict, console: "Console") -> "Layout":
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    tel = data["latest_tel"]
    run_state = data["run_state"]
    exec_audit = data["exec_audit"]
    guard_audit = data["guard_audit"]

    health, _ = derive_health(tel, run_state)
    bottleneck = derive_bottleneck(tel, exec_audit, guard_audit)

    recorded_at = str(safe_get(tel, "_recorded_at", ""))
    age = age_from_iso(recorded_at)
    cycle_id = safe_get(tel, "cycle_id", safe_get(run_state, "cycle_id", "?"))
    latest_ts = parse_timestamp(safe_get(tel, "timestamp", ""))

    health_style = "bold green" if health == "HEALTHY" else "bold yellow" if health == "DEGRADED" else "bold red"

    # HEADER
    header = Table.grid(padding=(0, 1))
    header.add_column()
    header.add_row(
        Text(
            f"O.M.A.-C.O.R.E. LIVE COCKPIT  |  "
            f"Cycle: {cycle_id}  |  "
            f"Latest: {latest_ts}  |  "
            f"Age: {age}  |  "
            f"Health: ",
            style="bold white",
        ),
        Text(health, style=health_style),
        Text(f"  |  Bottleneck: {bottleneck}", style="bold white"),
    )

    # TOP OPPORTUNITIES
    opp_table = Table(box=box.SIMPLE, header_style="bold cyan", title="Top Opportunities / Signals")
    opp_table.add_column("Asset", style="white")
    opp_table.add_column("Dir", style="yellow")
    opp_table.add_column("Type", style="cyan")
    opp_table.add_column("Conv", justify="right", style="green")
    opp_table.add_column("Risk", justify="right", style="magenta")
    opp_table.add_column("Block Reason", style="red")

    candidates = extract_signal_candidates(data, limit=5)
    if candidates:
        for c in candidates:
            opp_table.add_row(
                c["asset"],
                c["direction"],
                c["signal_type"],
                str(c["conviction"]),
                str(c["risk_score"]),
                c["block_reason"],
            )
    else:
        opp_table.add_row("(no data)", "", "", "", "", "")

    # BRAIN
    brain_table = Table(box=box.SIMPLE, header_style="bold cyan", title="Brain / Reasoning State")
    brain_table.add_column("Metric", style="white")
    brain_table.add_column("Value", justify="right", style="green")
    for label, key in [
        ("Events Collected", "events_collected"),
        ("Events Processed", "events_processed"),
        ("Signals (cycle)", "signals_generated"),
        ("Cumulative Signals", "cumulative_signals"),
        ("Trades Opened", "trades_opened"),
        ("Trades Closed", "trades_closed"),
        ("Cumulative Opened", "cumulative_trades_opened"),
        ("Cumulative Closed", "cumulative_trades_closed"),
        ("Open Positions", "open_positions"),
        ("Exec Blocks (cycle)", "execution_blocks"),
        ("Cumul Exec Blocks", "cumulative_execution_blocks"),
        ("Guard Blocks (cycle)", "guard_blocks"),
        ("Cumul Guard Blocks", "cumulative_guard_blocks"),
    ]:
        brain_table.add_row(label, str(safe_get(tel, key, safe_get(run_state, key, "?"))))

    # INTERPRETATION
    interp_text = Text(f"  >> {brain_interpretation(tel)}", style="bold yellow")

    # WORLD
    world_table = Table(box=box.SIMPLE, header_style="bold cyan", title="World State / Event Flow")
    world_table.add_column("Metric", style="white")
    world_table.add_column("Value", justify="right", style="green")
    for label, key in [
        ("Events Collected", "events_collected"),
        ("Events Processed", "events_processed"),
        ("Data Failures", "data_failures"),
        ("Gap Risk Score", "gap_risk_score"),
        ("Crash Mode", "crash_mode"),
        ("Capital Guard", "capital_guard_mode"),
    ]:
        world_table.add_row(label, str(safe_get(tel, key, safe_get(run_state, key, "?"))))

    # EXECUTION / PORTFOLIO
    exec_table = Table(box=box.SIMPLE, header_style="bold cyan", title="Execution / Portfolio")
    exec_table.add_column("Metric", style="white")
    exec_table.add_column("Value", justify="right", style="green")
    for label, key in [
        ("Equity", "current_equity"),
        ("Max Drawdown", "max_drawdown"),
        ("Daily PnL", "daily_pnl"),
        ("Weekly PnL", "weekly_pnl"),
        ("Open Positions", "open_positions"),
        ("Guard Mode", "capital_guard_mode"),
    ]:
        exec_table.add_row(label, str(safe_get(tel, key, "?")))
    last_exec = data.get("latest_exec", {})
    if last_exec:
        exec_table.add_row("Block Reason", str(safe_get(last_exec, "block_reason", "?")))
        exec_table.add_row(
            "Blocked Asset/Dir",
            f"{safe_get(last_exec, 'asset', '?')} / {safe_get(last_exec, 'direction', '?')}",
        )

    # DIRECTION CONTROLLER
    dc_table = Table(box=box.SIMPLE, header_style="bold cyan", title="Direction Controller")
    dc_table.add_column("Setting", style="white")
    dc_table.add_column("Value", style="yellow")
    dc_state = safe_get(tel, "direction_controller_state", {})
    for l in fmt_dc_state(dc_state):
        k, _, v = l.partition(": ")
        if k and v:
            dc_table.add_row(k.strip(), v.strip())

    # LEARNING
    cum_sig = safe_get(tel, "cumulative_signals", 0)
    cum_open = safe_get(tel, "cumulative_trades_opened", 0)
    cum_close = safe_get(tel, "cumulative_trades_closed", 0)
    cum_exec_blocks = safe_get(tel, "cumulative_execution_blocks", 0)
    cum_guard_blocks = safe_get(tel, "cumulative_guard_blocks", 0)

    capture_ratio = cum_open / cum_sig if cum_sig > 0 else 0
    exec_block_ratio = cum_exec_blocks / cum_sig if cum_sig > 0 else 0
    guard_block_ratio = cum_guard_blocks / cum_sig if cum_sig > 0 else 0
    close_ratio = cum_close / cum_open if cum_open > 0 else 0

    learn_table = Table(box=box.SIMPLE, header_style="bold cyan", title="Learning / Criterion Readiness")
    learn_table.add_column("Metric", style="white")
    learn_table.add_column("Value", justify="right", style="green")
    learn_table.add_row("Opportunity Capture", fmt_pct(capture_ratio))
    learn_table.add_row("Execution Block Ratio", fmt_pct(exec_block_ratio))
    learn_table.add_row("Guard Block Ratio", fmt_pct(guard_block_ratio))
    learn_table.add_row("Closed Trade Ratio", fmt_pct(close_ratio))

    learn_interp = Text("\n".join(f"  >> {l}" for l in learning_interpretation(tel)), style="bold yellow")

    # ALERTS
    alert_text = Text("\n".join(f"  ! {w}" for w in alerts_section(tel, Path("."), data)), style="bold red")

    # Build layout
    layout = Layout()
    layout.split_column(
        Layout(Panel(header, style="bold blue"), size=3),
        Layout(
            Layout.split_row(
                Layout(
                    Layout.split_column(
                        Layout(Panel(opp_table, title="Top Opportunities / Signals")),
                        Layout(Panel(brain_table)),
                        Layout(interp_text, size=2),
                    ),
                ),
                Layout(
                    Layout.split_column(
                        Layout(Panel(world_table)),
                        Layout(Panel(exec_table)),
                    ),
                ),
            ),
        ),
        Layout(
            Layout.split_row(
                Layout(Panel(dc_table)),
                Layout(
                    Layout.split_column(
                        Layout(Panel(learn_table)),
                        Layout(Panel(learn_interp)),
                        Layout(Panel(alert_text, title="Alerts / Diagnostics")),
                    ),
                ),
            ),
        ),
        Layout(
            Text(
                f"  Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC  |  "
                f"--once to exit  |  Ctrl+C to quit",
                style="dim white",
            ),
            size=2,
        ),
    )
    return layout


# ── Main ─────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="O.M.A.-C.O.R.E. Live Cockpit")
    p.add_argument("--once", action="store_true", help="Print one snapshot and exit")
    p.add_argument("--interval", type=int, default=5, help="Refresh interval (seconds)")
    p.add_argument(
        "--path", default="_extended_demo", help="Telemetry directory path"
    )
    p.add_argument("--plain", action="store_true", help="Force plain text output")
    p.add_argument("--limit", type=int, default=5, help="Max signal candidates")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    directory = Path(args.path)

    if not directory.exists():
        print(f"ERROR: Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    use_rich = HAS_RICH and not args.plain

    if use_rich:
        console = Console()
        if args.once:
            data = load_all(directory)
            console.print(render_plain(data))
            return
        try:
            with Live(refresh_per_second=1 / args.interval, screen=True) as live:
                while True:
                    data = load_all(directory)
                    layout = make_rich_layout(data, console)
                    live.update(layout)
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
    else:
        try:
            while True:
                data = load_all(directory)
                output = render_plain(data)
                if args.once:
                    print(output)
                    return
                os.system("clear" if os.name == "posix" else "cls")
                print(output)
                if args.once:
                    break
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
