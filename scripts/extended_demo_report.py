"""OSIRIS Extended Demo — Report Generator

Generates daily, weekly, guard, failure, performance, and health reports
from extended demo telemetry data.

Usage:
  python scripts/extended_demo_report.py                    # Latest reports
  python scripts/extended_demo_report.py --output _project-memory/extended_demo
  python scripts/extended_demo_report.py --all              # All available telemetry
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Optional

sys.path.insert(0, ".")

from core.monitoring.telemetry import TelemetryRecorder, GuardAuditRecorder
from core.monitoring.failure_classifier import FailureClassifier
from core.monitoring.health import HealthMonitor, HealthStatus


OUT_DIR = "_extended_demo"
REPORT_DIR = "_project-memory/extended_demo"


def load_telemetry() -> list[dict[str, Any]]:
    return TelemetryRecorder(OUT_DIR).read_all()


def load_guard_audit() -> list[dict[str, Any]]:
    return GuardAuditRecorder(OUT_DIR).read_all()


def load_failures() -> list[dict[str, Any]]:
    return FailureClassifier(OUT_DIR).read_all()


# ── Daily Report ───────────────────────────────────────────────────────

def generate_daily_report(telemetry: list[dict[str, Any]]) -> dict[str, Any]:
    if not telemetry:
        return {"error": "No telemetry data"}

    days: dict[str, list[dict]] = defaultdict(list)
    for t in telemetry:
        day = t.get("timestamp", "")[:10]
        days[day].append(t)

    daily: dict[str, Any] = {}
    for day, entries in sorted(days.items()):
        daily[day] = {
            "cycles": len(entries),
            "events": sum(e.get("events_collected", 0) for e in entries),
            "signals": sum(e.get("signals_generated", 0) for e in entries),
            "trades_opened": sum(e.get("trades_opened", 0) for e in entries),
            "trades_closed": sum(e.get("trades_closed", 0) for e in entries),
            "open_positions": entries[-1].get("open_positions", 0) if entries else 0,
            "equity_end": entries[-1].get("current_equity", 0) if entries else 0,
            "max_drawdown": max(e.get("max_drawdown", 0) for e in entries),
            "guard_blocks": sum(e.get("guard_blocks", 0) for e in entries),
            "execution_blocks": sum(e.get("execution_blocks", 0) for e in entries),
            "runtime_errors": sum(e.get("runtime_errors", 0) for e in entries),
            "data_failures": sum(e.get("data_failures", 0) for e in entries),
        }
    return daily


def write_daily_report_md(daily: dict[str, Any], out: Path):
    lines = [
        "# Extended Demo — Daily Report",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}\n",
        "| Date | Cycles | Events | Signals | Trades Opened | Trades Closed | Open Pos | Equity | Max DD | Guard Blocks | Errors |",
        "|------|--------|--------|---------|---------------|---------------|----------|--------|--------|-------------|--------|",
    ]
    for day, d in sorted(daily.items(), reverse=True)[:30]:
        lines.append(
            f"| {day} | {d['cycles']} | {d['events']} | {d['signals']} | "
            f"{d['trades_opened']} | {d['trades_closed']} | {d['open_positions']} | "
            f"${d['equity_end']:.2f} | {d['max_drawdown']:.2f}% | "
            f"{d['guard_blocks']} | {d['runtime_errors']} |"
        )
    (out / "daily_report.md").write_text("\n".join(lines) + "\n")


# ── Weekly Report ──────────────────────────────────────────────────────

def generate_weekly_report(telemetry: list[dict[str, Any]]) -> dict[str, Any]:
    if not telemetry:
        return {"error": "No telemetry data"}

    weeks: dict[str, list[dict]] = defaultdict(list)
    for t in telemetry:
        ts = t.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            week = dt.strftime("%Y-W%W")
        except Exception:
            week = ts[:7]
        weeks[week].append(t)

    weekly: dict[str, Any] = {}
    for week, entries in sorted(weeks.items()):
        pnls = [e.get("daily_pnl", 0) for e in entries if e.get("daily_pnl") is not None]
        weekly[week] = {
            "cycles": len(entries),
            "total_events": sum(e.get("events_collected", 0) for e in entries),
            "total_signals": sum(e.get("signals_generated", 0) for e in entries),
            "trades_opened": sum(e.get("trades_opened", 0) for e in entries),
            "trades_closed": sum(e.get("trades_closed", 0) for e in entries),
            "equity_start": entries[0].get("current_equity", 0),
            "equity_end": entries[-1].get("current_equity", 0),
            "weekly_pnl": sum(pnls),
            "max_drawdown": max(e.get("max_drawdown", 0) for e in entries),
            "guard_blocks": sum(e.get("guard_blocks", 0) for e in entries),
            "runtime_errors": sum(e.get("runtime_errors", 0) for e in entries),
        }
    return weekly


def write_weekly_report_md(weekly: dict[str, Any], out: Path):
    lines = [
        "# Extended Demo — Weekly Report",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}\n",
        "| Week | Cycles | Events | Signals | Trades | Closed | Equity Start | Equity End | Weekly PnL | Max DD | Guard Blocks | Errors |",
        "|------|--------|--------|---------|--------|--------|-------------|-----------|-----------|--------|-------------|--------|",
    ]
    for week, w in sorted(weekly.items(), reverse=True):
        pnl_str = f"${w['weekly_pnl']:.2f}" if w['weekly_pnl'] else "-"
        lines.append(
            f"| {week} | {w['cycles']} | {w['total_events']} | {w['total_signals']} | "
            f"{w['trades_opened']} | {w['trades_closed']} | "
            f"${w['equity_start']:.2f} | ${w['equity_end']:.2f} | "
            f"{pnl_str} | {w['max_drawdown']:.2f}% | "
            f"{w['guard_blocks']} | {w['runtime_errors']} |"
        )
    (out / "weekly_report.md").write_text("\n".join(lines) + "\n")


# ── Guard Report ───────────────────────────────────────────────────────

def generate_guard_report() -> dict[str, Any]:
    entries = load_guard_audit()
    if not entries:
        return {"error": "No guard audit data"}

    by_source: dict[str, int] = defaultdict(int)
    by_reason: dict[str, int] = defaultdict(int)
    by_asset: dict[str, int] = defaultdict(int)

    for e in entries:
        by_source[e.get("guard_source", "unknown")] += 1
        by_reason[e.get("block_reason", "unknown")] += 1
        by_asset[e.get("asset", "unknown")] += 1

    return {
        "total_interventions": len(entries),
        "by_source": dict(by_source),
        "by_reason": dict(by_reason),
        "by_asset": dict(by_asset),
        "recent": entries[-20:] if len(entries) > 20 else entries,
    }


def write_guard_report_md(report: dict[str, Any], out: Path):
    if "error" in report:
        (out / "guard_report.md").write_text(f"# Guard Report\n\n{report['error']}\n")
        return

    lines = [
        "# Extended Demo — Guard Report",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}\n",
        f"**Total interventions:** {report['total_interventions']}\n",
        "## By Guard Source",
    ]
    for source, count in sorted(report["by_source"].items(), key=lambda x: -x[1]):
        lines.append(f"- {source}: {count}")
    lines.append("\n## By Block Reason")
    for reason, count in sorted(report["by_reason"].items(), key=lambda x: -x[1]):
        lines.append(f"- {reason}: {count}")
    lines.append("\n## By Asset")
    for asset, count in sorted(report["by_asset"].items(), key=lambda x: -x[1]):
        lines.append(f"- {asset}: {count}")
    lines.append("\n## Recent (last 20)")
    lines.append("| Timestamp | Asset | Direction | Block Reason | Guard Source |")
    lines.append("|-----------|-------|-----------|-------------|-------------|")
    for e in report["recent"]:
        lines.append(
            f"| {str(e.get('timestamp', ''))[:19]} | {e.get('asset', '?')} | "
            f"{e.get('direction', '?')} | {e.get('block_reason', '?')} | "
            f"{e.get('guard_source', '?')} |"
        )
    (out / "guard_report.md").write_text("\n".join(lines) + "\n")


# ── Failure Report ─────────────────────────────────────────────────────

def generate_failure_report() -> dict[str, Any]:
    entries = load_failures()
    if not entries:
        return {"error": "No failure data"}

    by_category: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)
    by_type: dict[str, int] = defaultdict(int)
    unresolved = 0

    for e in entries:
        by_category[e.get("category", "unknown")] += 1
        by_severity[e.get("severity", "info")] += 1
        by_type[e.get("exception_type", "unknown")] += 1
        if not e.get("resolved", True):
            unresolved += 1

    return {
        "total_failures": len(entries),
        "by_category": dict(by_category),
        "by_severity": dict(by_severity),
        "by_exception_type": dict(by_type),
        "unresolved": unresolved,
        "critical": [e for e in entries if e.get("severity") == "critical"],
        "recent": entries[-20:] if len(entries) > 20 else entries,
    }


def write_failure_report_md(report: dict[str, Any], out: Path):
    if "error" in report:
        (out / "failure_report.md").write_text(f"# Failure Report\n\n{report['error']}\n")
        return

    lines = [
        "# Extended Demo — Failure Report",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}\n",
        f"**Total failures:** {report['total_failures']}",
        f"**Unresolved:** {report['unresolved']}\n",
        "## By Category",
    ]
    for cat, count in sorted(report["by_category"].items(), key=lambda x: -x[1]):
        lines.append(f"- {cat}: {count}")
    lines.append("\n## By Severity")
    for sev, count in sorted(report["by_severity"].items(), key=lambda x: -x[1]):
        lines.append(f"- {sev}: {count}")
    lines.append("\n## Critical Failures")
    if report["critical"]:
        for e in report["critical"]:
            lines.append(
                f"- `{e.get('exception_type', '?')}`: {e.get('message', '')[:100]} "
                f"({e.get('timestamp', '')[:19]})"
            )
    else:
        lines.append("- None")
    (out / "failure_report.md").write_text("\n".join(lines) + "\n")


# ── Performance Report ─────────────────────────────────────────────────

def generate_performance_report(telemetry: list[dict[str, Any]]) -> dict[str, Any]:
    if not telemetry:
        return {"error": "No telemetry data"}

    first = telemetry[0]
    last = telemetry[-1]
    equity_start = first.get("current_equity", 0)
    equity_end = last.get("current_equity", 0)
    total_return = ((equity_end - equity_start) / equity_start * 100) if equity_start else 0

    total_events = sum(e.get("events_collected", 0) for e in telemetry)
    total_signals = sum(e.get("signals_generated", 0) for e in telemetry)
    total_trades = sum(e.get("trades_opened", 0) for e in telemetry)
    total_closed = sum(e.get("trades_closed", 0) for e in telemetry)
    max_dd = max(e.get("max_drawdown", 0) for e in telemetry)
    total_errors = sum(e.get("runtime_errors", 0) for e in telemetry)

    equity_curve = [e.get("current_equity", 0) for e in telemetry if e.get("current_equity") is not None]

    returns = []
    for i in range(1, len(equity_curve)):
        if equity_curve[i - 1] > 0:
            returns.append((equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1])

    sharpe = 0
    if len(returns) > 1 and stdev(returns) > 0:
        sharpe = mean(returns) / stdev(returns) * (365 * 24 * 3600 / 3600) ** 0.5

    return {
        "cycles": len(telemetry),
        "duration_days": round((datetime.fromisoformat(last["timestamp"]) - datetime.fromisoformat(first["timestamp"])).total_seconds() / 86400, 1) if first.get("timestamp") and last.get("timestamp") else 0,
        "equity_start": equity_start,
        "equity_end": equity_end,
        "total_return_pct": round(total_return, 2),
        "total_events": total_events,
        "total_signals": total_signals,
        "total_trades_opened": total_trades,
        "total_trades_closed": total_closed,
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
        "total_errors": total_errors,
        "avg_cycle_events": round(total_events / len(telemetry), 2) if telemetry else 0,
    }


def write_performance_report_md(report: dict[str, Any], out: Path):
    if "error" in report:
        (out / "performance_report.md").write_text(f"# Performance Report\n\n{report['error']}\n")
        return

    lines = [
        "# Extended Demo — Performance Report",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}\n",
        "## Summary Metrics",
        f"- **Duration:** {report['duration_days']} days",
        f"- **Cycles:** {report['cycles']}",
        f"- **Events:** {report['total_events']}",
        f"- **Signals:** {report['total_signals']}",
        f"- **Trades Opened:** {report['total_trades_opened']}",
        f"- **Trades Closed:** {report['total_trades_closed']}\n",
        "## Capital Metrics",
        f"- **Starting Equity:** ${report['equity_start']:.2f}",
        f"- **Final Equity:** ${report['equity_end']:.2f}",
        f"- **Total Return:** {report['total_return_pct']:.2f}%",
        f"- **Max Drawdown:** {report['max_drawdown_pct']:.2f}%",
        f"- **Sharpe Ratio:** {report['sharpe_ratio']:.2f}\n",
        "## System Metrics",
        f"- **Runtime Errors:** {report['total_errors']}",
        f"- **Avg Events/Cycle:** {report['avg_cycle_events']}",
    ]
    (out / "performance_report.md").write_text("\n".join(lines) + "\n")


# ── Health Report ──────────────────────────────────────────────────────

def generate_health_report(telemetry: list[dict[str, Any]]) -> dict[str, Any]:
    if not telemetry:
        return {"error": "No telemetry data"}

    last = telemetry[-1]
    guard_mode = last.get("capital_guard_mode", "unknown")
    crash_mode = last.get("crash_mode", "unknown")
    gap_risk = last.get("gap_risk_score", 0)
    errors_total = sum(e.get("runtime_errors", 0) for e in telemetry)

    health = HealthMonitor()
    equity = last.get("current_equity", 0)
    results = health.run_all(
        equity=equity,
        initial_capital=equity or 10000,
        guard_mode=guard_mode,
        crash_mode=crash_mode,
        open_trades=[],
        all_trades=[],
        engine=None,
        symbols=[],
        recent_telemetry=telemetry[-10:],
    )
    status = health.overall_status(results)

    return {
        "status": status.value,
        "guard_mode": guard_mode,
        "crash_mode": crash_mode,
        "gap_risk_score": gap_risk,
        "equity": equity,
        "total_errors": errors_total,
        "checks": [r.to_dict() for r in results],
    }


def write_health_report_md(report: dict[str, Any], out: Path):
    if "error" in report:
        (out / "health_report.md").write_text(f"# Health Report\n\n{report['error']}\n")
        return

    status_emoji = {"healthy": "✅", "degraded": "⚠️", "critical": "🚫"}
    emoji = status_emoji.get(report["status"], "❓")

    lines = [
        "# Extended Demo — Health Report",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}\n",
        f"**Overall Status:** {emoji} {report['status'].upper()}\n",
        "## Current State",
        f"- **Guard Mode:** {report['guard_mode']}",
        f"- **Crash Mode:** {report['crash_mode']}",
        f"- **Gap Risk Score:** {report['gap_risk_score']}",
        f"- **Equity:** ${report['equity']:.2f}",
        f"- **Total Runtime Errors:** {report['total_errors']}\n",
        "## Health Checks",
        "| Check | Status | Message |",
        "|-------|--------|---------|",
    ]
    for c in report["checks"]:
        s = c.get("status", "?")
        icon = {"healthy": "✅", "degraded": "⚠️", "critical": "🚫"}.get(s, "❓")
        lines.append(f"| {c.get('check_name', '?')} | {icon} {s} | {c.get('message', '')} |")
    (out / "health_report.md").write_text("\n".join(lines) + "\n")


# ── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OSIRIS Extended Demo — Report Generator")
    parser.add_argument("--output", type=str, default=REPORT_DIR,
                        help=f"Output directory (default: {REPORT_DIR})")
    parser.add_argument("--all", action="store_true",
                        help="Generate all reports regardless of data age")
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Generating reports in {out}/")
    print(f"Reading telemetry from {OUT_DIR}/")

    tel = load_telemetry()
    print(f"  Telemetry entries: {len(tel)}")

    # Daily
    daily = generate_daily_report(tel)
    write_daily_report_md(daily, out)
    print(f"  ✓ daily_report.md ({len(daily)} days)")

    # Weekly
    weekly = generate_weekly_report(tel)
    write_weekly_report_md(weekly, out)
    print(f"  ✓ weekly_report.md ({len(weekly)} weeks)")

    # Guard
    guard = generate_guard_report()
    write_guard_report_md(guard, out)
    print(f"  ✓ guard_report.md ({guard.get('total_interventions', 0)} interventions)")

    # Failure
    failure = generate_failure_report()
    write_failure_report_md(failure, out)
    print(f"  ✓ failure_report.md ({failure.get('total_failures', 0)} failures)")

    # Performance
    perf = generate_performance_report(tel)
    write_performance_report_md(perf, out)
    print(f"  ✓ performance_report.md")

    # Health
    health = generate_health_report(tel)
    write_health_report_md(health, out)
    print(f"  ✓ health_report.md ({health.get('status', 'unknown')})")

    print(f"\nAll reports written to {out}/")


if __name__ == "__main__":
    main()
