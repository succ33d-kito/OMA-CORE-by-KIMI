#!/usr/bin/env python3
"""
cleanup_pre_guard_artifacts.py — Read-only cleanup planner for pre-Sprint 12 artifacts.

Identifies historical invalid opportunities generated before the Yahoo Data Guard
(Sprint 12) was active. These artifacts include:

  - score=100 saturation from broken Yahoo data
  - -100% change events (API failure interpreted as total loss)
  - $0.00 price events (missing price data)
  - [DATA_QUALITY] flagged opportunities

Requires --execute to perform deletion. Default is dry-run.
Does NOT modify the database unless --execute is passed.
"""
import argparse
import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPORT_DIR = Path(__file__).resolve().parent.parent / "_project-memory" / "cleanup"
IDENTIFY_QUERY = """
    SELECT id, event_id, title, description, score, conviction, priority,
           opportunity_type, asset_class, timestamp
    FROM opportunities
    WHERE score >= 100
       OR description LIKE '%-100%'
       OR description LIKE '%$0.00%'
       OR (title LIKE '%DATA_QUALITY%')
    ORDER BY timestamp ASC
"""

COUNT_QUERY = """
    SELECT COUNT(*) as cnt FROM opportunities
    WHERE score >= 100
       OR description LIKE '%-100%'
       OR description LIKE '%$0.00%'
       OR (title LIKE '%DATA_QUALITY%')
"""

DELETE_QUERY = """
    DELETE FROM opportunities
    WHERE score >= 100
       OR description LIKE '%-100%'
       OR description LIKE '%$0.00%'
       OR (title LIKE '%DATA_QUALITY%')
"""


def identify_artifacts(db_path: str) -> List[Dict[str, Any]]:
    """Read-only: identify artifact opportunities in the database."""
    if not os.path.exists(db_path):
        print(f"[cleanup] Database not found: {db_path}")
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(IDENTIFY_QUERY).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def compute_summary(artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary statistics for identified artifacts."""
    total = len(artifacts)
    reasons: Dict[str, int] = Counter()
    score_100 = 0
    minus_100 = 0
    price_zero = 0
    dq_flagged = 0
    priorities: Dict[str, int] = Counter()
    types: Dict[str, int] = Counter()
    sources: Dict[str, int] = Counter()
    scores = []
    timestamps = []

    for a in artifacts:
        score = a.get("score", 0)
        desc = a.get("description", "") or ""
        title = a.get("title", "") or ""
        scores.append(score)

        if score >= 100:
            score_100 += 1
            reasons["score_100"] += 1
        if "-100" in desc or "-100" in title:
            minus_100 += 1
            reasons["negative_100_percent"] += 1
        if "$0.00" in desc:
            price_zero += 1
            reasons["price_zero"] += 1
        if title.startswith("[DATA_QUALITY]"):
            dq_flagged += 1
            reasons["data_quality_flagged"] += 1

        priorities[a.get("priority", "UNKNOWN")] += 1
        types[a.get("opportunity_type", "UNKNOWN")] += 1
        ts = a.get("timestamp", "")
        if ts:
            timestamps.append(ts)

    return {
        "total_artifacts": total,
        "score_100_count": score_100,
        "negative_100_count": minus_100,
        "price_zero_count": price_zero,
        "data_quality_flagged": dq_flagged,
        "reason_breakdown": dict(reasons),
        "priority_breakdown": dict(priorities),
        "type_breakdown": dict(types),
        "mean_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "score_range": [min(scores), max(scores)] if scores else [0, 0],
        "earliest_timestamp": min(timestamps) if timestamps else "",
        "latest_timestamp": max(timestamps) if timestamps else "",
    }


def build_sql_preview(db_path: str) -> str:
    """Build a human-readable SQL DELETE preview."""
    return (
        "-- PREVIEW: This SQL would be executed if --execute is passed\n"
        "-- Database: " + db_path + "\n"
        "BEGIN TRANSACTION;\n"
        + DELETE_QUERY.strip() + ";\n"
        "-- Rows affected: see COUNT above\n"
        "-- WARNING: This operation CANNOT be undone.\n"
        "COMMIT;\n"
    )


def save_markdown_report(artifacts: List[Dict[str, Any]], summary: Dict[str, Any],
                          db_path: str, dry_run: bool) -> str:
    """Save a markdown report to REPORT_DIR."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    mode = "dry_run" if dry_run else "executed"
    path = REPORT_DIR / f"pre_guard_cleanup_{mode}_{ts}.md"

    lines = [
        "# Pre-Guard Artifact Cleanup Report",
        "",
        f"**Mode**: {'Dry Run' if dry_run else 'Executed'}",
        f"**Database**: {db_path}",
        f"**Timestamp**: {datetime.now(timezone.utc).isoformat()}",
        f"**Total artifacts identified**: {summary['total_artifacts']}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Score >= 100 | {summary['score_100_count']} |",
        f"| -100% change | {summary['negative_100_count']} |",
        f"| $0.00 price | {summary['price_zero_count']} |",
        f"| DATA_QUALITY flagged | {summary['data_quality_flagged']} |",
        f"| Mean score | {summary['mean_score']} |",
        f"| Score range | {summary['score_range'][0]} - {summary['score_range'][1]} |",
        f"| Earliest artifact | {summary['earliest_timestamp']} |",
        f"| Latest artifact | {summary['latest_timestamp']} |",
        "",
        "## Reason Breakdown",
        "",
    ]
    for reason, count in sorted(summary.get("reason_breakdown", {}).items(),
                                  key=lambda x: -x[1]):
        lines.append(f"- **{reason}**: {count}")
    lines.append("")

    lines.append("## Priority Breakdown")
    lines.append("")
    for pri, count in sorted(summary.get("priority_breakdown", {}).items(),
                              key=lambda x: -x[1]):
        lines.append(f"- **{pri}**: {count}")
    lines.append("")

    lines.append("## Type Breakdown")
    lines.append("")
    for t, count in sorted(summary.get("type_breakdown", {}).items(),
                            key=lambda x: -x[1]):
        lines.append(f"- **{t}**: {count}")
    lines.append("")

    if artifacts:
        lines.append("## First 10 Artifacts")
        lines.append("")
        lines.append("| ID | Score | Priority | Type | Reason Indicators |")
        lines.append("|---|---|---|---|---|")
        for a in artifacts[:10]:
            desc = a.get("description", "") or ""
            title = a.get("title", "") or ""
            indicators = []
            if a.get("score", 0) >= 100:
                indicators.append("score=100")
            if "-100" in desc or "-100" in title:
                indicators.append("-100%")
            if "$0.00" in desc:
                indicators.append("$0.00")
            if title.startswith("[DATA_QUALITY]"):
                indicators.append("DATA_QUALITY")
            lines.append(
                f"| {a['id'][:12]} | {a['score']} | {a['priority']} | "
                f"{a['opportunity_type']} | {', '.join(indicators)} |"
            )
        lines.append("")

    lines.append("## SQL Preview")
    lines.append("")
    lines.append("```sql")
    lines.append(build_sql_preview(db_path))
    lines.append("```")
    lines.append("")

    if not dry_run:
        lines.append("## Execution Result")
        lines.append("")
        lines.append(f"Successfully deleted **{summary['total_artifacts']}** artifacts.")
        lines.append("")

    lines.append("---")
    lines.append("*Report generated by cleanup_pre_guard_artifacts.py*")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[cleanup] Report saved: {path}")
    return str(path)


def perform_delete(db_path: str) -> int:
    """Execute the DELETE operation. Requires --execute to reach here."""
    conn = sqlite3.connect(db_path)
    conn.execute("BEGIN TRANSACTION")
    rows = conn.execute(COUNT_QUERY).fetchone()[0]
    conn.execute(DELETE_QUERY)
    conn.commit()
    conn.close()
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Pre-Guard Artifact Cleanup (read-only by default)"
    )
    parser.add_argument("--db", default="oma_core.db",
                        help="Path to oma_core.db")
    parser.add_argument("--execute", action="store_true",
                        help="REQUIRED to actually delete. Default is dry-run.")
    parser.add_argument("--save-report", action="store_true",
                        help="Save markdown report to _project-memory/cleanup/")
    args = parser.parse_args()

    print(f"[cleanup] Reading database: {args.db}")
    artifacts = identify_artifacts(args.db)
    print(f"[cleanup] Artifacts identified: {len(artifacts)}")

    if not artifacts:
        print("[cleanup] No artifacts found. Nothing to do.")
        return

    summary = compute_summary(artifacts)
    print()
    print("=" * 60)
    print("  Pre-Guard Artifact Cleanup")
    print("=" * 60)
    print(f"  Total artifacts:          {summary['total_artifacts']}")
    print(f"  Score >= 100:             {summary['score_100_count']}")
    print(f"  -100% change:             {summary['negative_100_count']}")
    print(f"  $0.00 price:              {summary['price_zero_count']}")
    print(f"  DATA_QUALITY flagged:     {summary['data_quality_flagged']}")
    print(f"  Mean score of artifacts:  {summary['mean_score']}")
    print(f"  Score range:              {summary['score_range']}")
    print()

    print("  Priority breakdown:")
    for pri, cnt in sorted(summary["priority_breakdown"].items(),
                            key=lambda x: -x[1]):
        print(f"    {pri}: {cnt}")
    print()

    print("  Type breakdown:")
    for t, cnt in sorted(summary["type_breakdown"].items(),
                          key=lambda x: -x[1]):
        print(f"    {t}: {cnt}")
    print()

    if args.save_report:
        save_markdown_report(artifacts, summary, args.db, not args.execute)

    if args.execute:
        print(f"[cleanup] ⚠️  --execute passed. Deleting {len(artifacts)} artifacts...")
        deleted = perform_delete(args.db)
        print(f"[cleanup] ✅ Deleted {deleted} artifacts.")
        if args.save_report:
            save_markdown_report(artifacts, summary, args.db, dry_run=False)
        print("[cleanup] Cleanup complete. Database was modified.")
    else:
        print()
        print("  SQL Preview:")
        print(build_sql_preview(args.db))
        print()
        print("[cleanup] DRY RUN — no data was modified.")
        print("[cleanup] Pass --execute to perform deletion.")
        print("[cleanup] This operation CANNOT be undone.")


if __name__ == "__main__":
    main()
