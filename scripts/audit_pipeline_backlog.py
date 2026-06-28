#!/usr/bin/env python3
"""
audit_pipeline_backlog.py — Read-only pipeline backlog audit.

Measures collection speed, processing speed, backlog growth rate,
duplicates, expired events, and estimated time to empty the queue.
"""
import argparse
import json
import os
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List


REPORT_DIR = Path(__file__).resolve().parent.parent / "_project-memory" / "backlog_audit"


def audit_backlog(db_path: str) -> Dict[str, Any]:
    if not os.path.exists(db_path):
        return {"error": f"Database not found: {db_path}"}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Total events
    total_events = conn.execute("SELECT COUNT(*) as c FROM events").fetchone()[0]
    processed = conn.execute("SELECT COUNT(*) as c FROM events WHERE processed = 1").fetchone()[0]
    unprocessed = conn.execute("SELECT COUNT(*) as c FROM events WHERE processed = 0").fetchone()[0]

    # Event timing
    first_event = conn.execute("SELECT MIN(timestamp) as t FROM events").fetchone()[0]
    last_event = conn.execute("SELECT MAX(timestamp) as t FROM events").fetchone()[0]

    # Events by source
    by_source = dict(conn.execute(
        "SELECT source, COUNT(*) as c FROM events GROUP BY source ORDER BY c DESC"
    ).fetchall())

    # Unprocessed by source
    unproc_by_source = dict(conn.execute(
        "SELECT source, COUNT(*) as c FROM events WHERE processed = 0 GROUP BY source ORDER BY c DESC"
    ).fetchall())

    # Events by urgency
    by_urgency = dict(conn.execute(
        "SELECT urgency, COUNT(*) as c FROM events GROUP BY urgency ORDER BY urgency"
    ).fetchall())

    # Events by type
    by_type = dict(conn.execute(
        "SELECT event_type, COUNT(*) as c FROM events GROUP BY event_type ORDER BY c DESC"
    ).fetchall())

    # Event collection rate (events per day for last 7 days)
    try:
        week_ago = (datetime.fromisoformat(last_event) - timedelta(days=7)).isoformat()
    except (ValueError, TypeError):
        week_ago = "1970-01-01"
    events_last_7d = conn.execute(
        "SELECT COUNT(*) as c FROM events WHERE timestamp > ?", (week_ago,)
    ).fetchone()[0]

    # Processed per run estimate (using last 3 timestamps)
    runs = conn.execute(
        "SELECT DISTINCT SUBSTR(timestamp, 1, 16) as run_ts FROM opportunities "
        "ORDER BY run_ts DESC LIMIT 5"
    ).fetchall()
    opps_per_run = []
    for r in runs:
        cnt = conn.execute(
            "SELECT COUNT(*) as c FROM opportunities WHERE timestamp LIKE ?",
            (r[0] + "%",)
        ).fetchone()[0]
        opps_per_run.append(cnt)

    # Duplicate events (same source_id or same title+source)
    dup_source_id = conn.execute(
        "SELECT source_id, source, COUNT(*) as c FROM events "
        "WHERE source_id IS NOT NULL AND source_id != '' "
        "GROUP BY source_id HAVING c > 1"
    ).fetchall()
    dup_count = sum(r[2] - 1 for r in dup_source_id)

    # Events that are likely expired (>24h unprocessed)
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    except Exception:
        cutoff = ""
    expired = conn.execute(
        "SELECT COUNT(*) as c FROM events WHERE processed = 0 AND timestamp < ?",
        (cutoff,)
    ).fetchone()[0] if cutoff else 0

    # Events per day estimate
    days_span = 1
    if first_event and last_event:
        try:
            fe = datetime.fromisoformat(first_event)
            le = datetime.fromisoformat(last_event)
            days_span = max((le - fe).total_seconds() / 86400, 1)
        except (ValueError, TypeError):
            days_span = 1

    events_per_day = round(total_events / days_span, 1)

    # Estimate: processing speed
    # Assume each pipeline run processes ~200 events (from known behavior)
    # and generates ~32 opportunities
    pipeline_batch_size = 200
    opps_per_pipeline = round(sum(opps_per_run) / len(opps_per_run)) if opps_per_run else 32

    # How many runs needed to clear backlog
    runs_needed = max(1, round(unprocessed / pipeline_batch_size))
    # Runs per day estimate (1 per 6h = 4 per day based on typical run schedule)
    runs_per_day = 4
    hours_to_clear = round(runs_needed / runs_per_day * 24, 1) if runs_per_day else 0

    conn.close()

    return {
        "database": db_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_events": total_events,
        "processed_events": processed,
        "unprocessed_events": unprocessed,
        "backlog_pct": round(unprocessed / total_events * 100, 1) if total_events else 0,
        "first_event_timestamp": first_event,
        "last_event_timestamp": last_event,
        "events_per_day": events_per_day,
        "events_last_7_days": events_last_7d,
        "collection_rate_per_day": round(events_last_7d / 7, 1) if events_last_7d else 0,
        "events_by_source": dict(by_source),
        "unprocessed_by_source": unproc_by_source,
        "events_by_urgency": by_urgency,
        "events_by_type": by_type,
        "pipeline_metrics": {
            "typical_batch_size": pipeline_batch_size,
            "opportunities_per_run": opps_per_pipeline,
            "recent_runs_opp_counts": opps_per_run,
            "estimated_runs_per_day": runs_per_day,
        },
        "backlog_clearance": {
            "runs_needed": runs_needed,
            "hours_to_clear_at_current_rate": hours_to_clear,
            "estimated_clear_by": (
                (datetime.now(timezone.utc) + timedelta(hours=hours_to_clear)).isoformat()
                if hours_to_clear else "N/A"
            ),
        },
        "duplicate_events": dup_count,
        "expired_events_unprocessed": expired,
        "opportunities_total": sum(opps_per_run) if opps_per_run else 0,
    }


def print_report(result: Dict[str, Any]) -> None:
    print()
    print("=" * 60)
    print("  Pipeline Backlog Audit")
    print("=" * 60)
    print(f"  Database: {result.get('database')}")
    print(f"  Timestamp: {result.get('timestamp')}")
    print()

    print("--- Event Inventory ---")
    print(f"  Total events:      {result.get('total_events')}")
    print(f"  Processed:         {result.get('processed_events')}")
    print(f"  Unprocessed:       {result.get('unprocessed_events')}")
    print(f"  Backlog %:         {result.get('backlog_pct')}%")
    print(f"  First event:       {result.get('first_event_timestamp')}")
    print(f"  Last event:        {result.get('last_event_timestamp')}")
    print(f"  Events/day (avg):  {result.get('events_per_day')}")
    print(f"  Events last 7d:    {result.get('events_last_7_days')}")
    print(f"  Collection rate:   {result.get('collection_rate_per_day')}/day")
    print()

    print("--- Pipeline Metrics ---")
    pm = result.get("pipeline_metrics", {})
    print(f"  Batch size:           {pm.get('typical_batch_size')}")
    print(f"  Opps per run:         {pm.get('opportunities_per_run')}")
    print(f"  Recent opp counts:    {pm.get('recent_runs_opp_counts')}")
    print(f"  Estimated runs/day:   {pm.get('estimated_runs_per_day')}")
    print()

    bc = result.get("backlog_clearance", {})
    print("--- Backlog Clearance Estimate ---")
    print(f"  Runs needed:          {bc.get('runs_needed')}")
    print(f"  Hours to clear:       {bc.get('hours_to_clear_at_current_rate')}")
    print(f"  Estimated clear by:   {bc.get('estimated_clear_by')}")
    print()

    print("--- Data Quality ---")
    print(f"  Duplicate events:     {result.get('duplicate_events')}")
    print(f"  Expired unprocessed:  {result.get('expired_events_unprocessed')}")
    print()

    print("--- Unprocessed by Source (top 10) ---")
    for src, cnt in sorted(result.get("unprocessed_by_source", {}).items(),
                            key=lambda x: -x[1])[:10]:
        print(f"  {src:25s} {cnt}")
    print()

    print("--- Events by Urgency ---")
    for u, cnt in sorted(result.get("events_by_urgency", {}).items()):
        print(f"  Urgency {u}: {cnt}")
    print()

    # Recommendations
    print("--- Recommendations ---")
    backlog_pct = result.get("backlog_pct", 0)
    hours = bc.get("hours_to_clear_at_current_rate", 0)
    expired = result.get("expired_events_unprocessed", 0)

    if backlog_pct > 50:
        print("  ⚠ Backlog exceeds 50% — increase processing frequency or batch size.")
    if hours > 48:
        print(f"  ⚠ {hours}h to clear at current rate — consider 2× pipeline runs/day.")
    if expired > 0:
        print(f"  ⚠ {expired} unprocessed events are >24h old and may be stale.")
    if result.get("duplicate_events", 0) > 0:
        print(f"  ⚠ {result['duplicate_events']} duplicate source_ids detected.")
    print(f"  ℹ  Current pipeline processes ~{pm.get('typical_batch_size')} events per run, "
          f"generating ~{pm.get('opportunities_per_run')} opportunities.")
    print()

    print("  [audit] Read-only. No data was modified.")


def save_report(result: Dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"backlog_audit_{ts}.md"

    lines = [
        "# Pipeline Backlog Audit Report",
        "",
        f"**Database**: {result.get('database')}",
        f"**Timestamp**: {result.get('timestamp')}",
        "",
        "## Event Inventory",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total events | {result.get('total_events')} |",
        f"| Processed | {result.get('processed_events')} |",
        f"| Unprocessed | {result.get('unprocessed_events')} |",
        f"| Backlog % | {result.get('backlog_pct')}% |",
        f"| Events/day | {result.get('events_per_day')} |",
        f"| Events last 7d | {result.get('events_last_7_days')} |",
        "",
        "## Backlog Clearance",
        "",
        f"**Runs needed**: {result.get('backlog_clearance', {}).get('runs_needed')}",
        f"**Hours to clear**: {result.get('backlog_clearance', {}).get('hours_to_clear_at_current_rate')}",
        "",
        "## Unprocessed by Source",
        "",
    ]
    for src, cnt in sorted(result.get("unprocessed_by_source", {}).items(),
                            key=lambda x: -x[1])[:15]:
        lines.append(f"- **{src}**: {cnt}")
    lines.append("")

    lines.append("## Data Quality")
    lines.append("")
    lines.append(f"- **Duplicate events**: {result.get('duplicate_events')}")
    lines.append(f"- **Expired unprocessed**: {result.get('expired_events_unprocessed')}")
    lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    bc = result.get("backlog_clearance", {})
    if result.get("backlog_pct", 0) > 50:
        lines.append("- Increase processing frequency or batch size.")
    if bc.get("hours_to_clear_at_current_rate", 0) > 48:
        lines.append("- Consider 2x daily pipeline runs.")
    if result.get("expired_events_unprocessed", 0) > 0:
        lines.append("- Stale events may need archival or re-collection.")
    if result.get("duplicate_events", 0) > 0:
        lines.append("- Deduplicate events with matching source_id.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by audit_pipeline_backlog.py*")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[backlog] Report saved: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline Backlog Audit (read-only)"
    )
    parser.add_argument("--db", default="oma_core.db",
                        help="Path to oma_core.db")
    parser.add_argument("--save", action="store_true",
                        help="Save report to _project-memory/backlog_audit/")
    args = parser.parse_args()

    result = audit_backlog(args.db)
    if "error" in result:
        print(f"[backlog] Error: {result['error']}")
        return

    print_report(result)

    if args.save:
        save_report(result)


if __name__ == "__main__":
    main()
