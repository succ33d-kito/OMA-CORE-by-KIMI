#!/usr/bin/env python3
"""
audit_priority_consistency.py — Read-only priority consistency audit.

Checks whether the priority assigned to each opportunity is consistent
with the opportunity type. Outputs a consistency score and lists all
mismatches with recommendations.

Does NOT modify the database.
"""
import argparse
import json
import os
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


REPORT_DIR = Path(__file__).resolve().parent.parent / "_project-memory" / "priority_audit"


# Expected priority ranges for each opportunity type.
# Key: opportunity_type → (min_acceptable, max_acceptable)
# CRITICAL should only appear for types that represent urgent/actionable signals.
EXPECTED_PRIORITY_RANGES: Dict[str, Tuple[str, str]] = {
    # Actionable — may be CRITICAL under extreme conditions
    "AVOID_OR_SHORT":          ("MEDIUM", "CRITICAL"),
    "RISK_OFF":                ("MEDIUM", "CRITICAL"),
    "SAFE_HAVEN_FLOW":         ("HIGH", "CRITICAL"),
    "SHORT_SETUP":             ("HIGH", "CRITICAL"),
    "LONG_SETUP":              ("HIGH", "CRITICAL"),
    "POST_EARNINGS_RUN":       ("HIGH", "CRITICAL"),
    "POST_EARNINGS_DROP":      ("HIGH", "CRITICAL"),
    "MACRO_HEADWIND":          ("HIGH", "CRITICAL"),
    "MACRO_TAILWIND":          ("HIGH", "CRITICAL"),
    "REGULATORY_HEADWIND":     ("HIGH", "CRITICAL"),
    "REGULATORY_TAILWIND":     ("HIGH", "CRITICAL"),
    "SENTIMENT_TURN_BEAR":     ("HIGH", "CRITICAL"),
    "SENTIMENT_TURN_BULL":     ("HIGH", "CRITICAL"),
    "WHALE_ACCUMULATION":      ("HIGH", "CRITICAL"),
    "WHALE_DISTRIBUTION":      ("HIGH", "CRITICAL"),
    "TECHNICAL_BREAKOUT":      ("HIGH", "CRITICAL"),
    "TECHNICAL_BREAKDOWN":     ("HIGH", "CRITICAL"),
    "ARB_OPPORTUNITY":         ("HIGH", "CRITICAL"),
    "MOMENTUM_PLAY":           ("MEDIUM", "CRITICAL"),

    # Observational — should rarely be CRITICAL
    "WATCHLIST_ADD":           ("LOW", "HIGH"),
    "NEWS_DRIVEN":             ("LOW", "HIGH"),
    "MONITOR_MACRO":           ("LOW", "HIGH"),
    "MONITOR_COMPLIANCE":      ("LOW", "MEDIUM"),
    "MONITOR_GEO":             ("LOW", "MEDIUM"),
    "VIRAL_MOMENTUM":          ("MEDIUM", "HIGH"),
    "EARNINGS_NEUTRAL":        ("LOW", "MEDIUM"),
    "SENTIMENT_WATCH":         ("LOW", "MEDIUM"),
    "TECHNICAL_WATCH":         ("LOW", "MEDIUM"),
    "WHALE_WATCH":             ("LOW", "MEDIUM"),
}

PRIORITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def priority_value(p: str) -> int:
    return PRIORITY_ORDER.get(p, -1)


def check_consistency(opp_type: str, priority: str,
                      score: float, conviction: float) -> Dict[str, Any]:
    """Check if an opportunity's priority is consistent with its type."""
    expected = EXPECTED_PRIORITY_RANGES.get(opp_type)
    if expected is None:
        return {
            "consistent": True,
            "severity": "info",
            "message": f"Unknown opportunity type '{opp_type}' — no consistency rules",
        }

    min_pri, max_pri = expected
    p_val = priority_value(priority)
    min_val = priority_value(min_pri)
    max_val = priority_value(max_pri)

    if p_val < min_val:
        return {
            "consistent": False,
            "severity": "under_priority",
            "message": (f"Type '{opp_type}' expects at least {min_pri}, "
                        f"but got {priority} (score={score}, conv={conviction})"),
        }
    if p_val > max_val:
        return {
            "consistent": False,
            "severity": "over_priority",
            "message": (f"Type '{opp_type}' expects at most {max_pri}, "
                        f"but got {priority} (score={score}, conv={conviction})"),
        }
    return {
        "consistent": True,
        "severity": "ok",
        "message": "",
    }


PRIORITY_LADDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def audit_consistency(db_path: str) -> Dict[str, Any]:
    """Run the full consistency audit."""
    if not os.path.exists(db_path):
        return {"error": f"Database not found: {db_path}"}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, score, conviction, priority, opportunity_type, "
        "title, risk_level, action_suggested, timestamp "
        "FROM opportunities ORDER BY timestamp"
    ).fetchall()
    conn.close()

    results = []
    consistent_count = 0
    inconsistent_count = 0
    over_priority_count = 0
    under_priority_count = 0
    type_priority_matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: Counter())
    type_counts: Dict[str, int] = Counter()
    over_priority_examples: List[Dict] = []
    under_priority_examples: List[Dict] = []
    type_consistency: Dict[str, Dict] = {}

    for r in rows:
        r = dict(r)
        check = check_consistency(
            r["opportunity_type"], r["priority"],
            r["score"], r["conviction"]
        )
        type_priority_matrix[r["opportunity_type"]][r["priority"]] += 1
        type_counts[r["opportunity_type"]] += 1

        result = {
            "id": r["id"],
            "score": r["score"],
            "conviction": r["conviction"],
            "priority": r["priority"],
            "type": r["opportunity_type"],
            "title": (r.get("title") or "")[:60],
            "risk_level": r["risk_level"],
            "action": (r.get("action_suggested") or "")[:30],
            "consistent": check["consistent"],
            "severity": check["severity"],
            "message": check["message"],
        }
        results.append(result)

        if not check["consistent"]:
            inconsistent_count += 1
            if check["severity"] == "over_priority":
                over_priority_count += 1
                if len(over_priority_examples) < 20:
                    over_priority_examples.append(result)
            else:
                under_priority_count += 1
                if len(under_priority_examples) < 20:
                    under_priority_examples.append(result)
        else:
            consistent_count += 1

    total = consistent_count + inconsistent_count
    consistency_pct = round(consistent_count / total * 100, 1) if total else 100.0

    # Per-type consistency
    for t in type_counts:
        total_t = type_counts[t]
        consistent_t = sum(1 for r in results if r["type"] == t and r["consistent"])
        type_consistency[t] = {
            "count": total_t,
            "consistent": consistent_t,
            "inconsistent": total_t - consistent_t,
            "pct": round(consistent_t / total_t * 100, 1) if total_t else 100.0,
        }

    return {
        "database": db_path,
        "total_opportunities": total,
        "consistent": consistent_count,
        "inconsistent": inconsistent_count,
        "consistency_pct": consistency_pct,
        "over_priority": over_priority_count,
        "under_priority": under_priority_count,
        "over_priority_examples": over_priority_examples,
        "under_priority_examples": under_priority_examples,
        "type_consistency": type_consistency,
        "type_priority_matrix": {k: dict(v) for k, v in type_priority_matrix.items()},
        "type_counts": dict(type_counts),
    }


def print_report(result: Dict[str, Any]) -> None:
    print()
    print("=" * 60)
    print("  Priority Consistency Audit")
    print("=" * 60)
    print(f"  Database: {result.get('database')}")
    print(f"  Total opportunities: {result.get('total_opportunities')}")
    print(f"  Consistent: {result.get('consistent')} "
          f"({result.get('consistency_pct')}%)")
    print(f"  Inconsistent: {result.get('inconsistent')}")
    print(f"    Over-priority (too high): {result.get('over_priority')}")
    print(f"    Under-priority (too low): {result.get('under_priority')}")
    print()

    # Type consistency table
    tc = result.get("type_consistency", {})
    print("--- Per-Type Consistency ---")
    print(f"  {'Type':25s} {'Count':6s} {'Consistent':11s} {'%':5s}")
    print(f"  {'-'*25} {'-'*6} {'-'*11} {'-'*5}")
    for t, info in sorted(tc.items(), key=lambda x: -x[1]["count"]):
        bar = "✓" if info["pct"] >= 90 else "⚠" if info["pct"] >= 50 else "✗"
        print(f"  {bar} {t:23s} {info['count']:6d} {info['consistent']:5d}/{info['inconsistent']:5d} {info['pct']:5.1f}%")
    print()

    # Type-Priority Matrix
    matrix = result.get("type_priority_matrix", {})
    print("--- Type vs Priority Matrix ---")
    header = f"  {'Type':25s}"
    for p in PRIORITY_LADDER:
        header += f" {p:10s}"
    print(header)
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    for t in sorted(matrix.keys()):
        row = f"  {t:25s}"
        for p in PRIORITY_LADDER:
            row += f" {matrix[t].get(p, 0):10d}"
        print(row)
    print()

    if result.get("over_priority_examples"):
        print("--- Over-Priority Examples (type doesn't warrant this priority) ---")
        for ex in result["over_priority_examples"]:
            print(f"  [{ex['priority']}] {ex['type']:22s} score={ex['score']:6.2f} "
                  f"conv={ex['conviction']:5.2f}  {ex['title'][:50]}")
        print()

    if result.get("under_priority_examples"):
        print("--- Under-Priority Examples (type warrants higher priority) ---")
        for ex in result["under_priority_examples"]:
            print(f"  [{ex['priority']}] {ex['type']:22s} score={ex['score']:6.2f} "
                  f"conv={ex['conviction']:5.2f}  {ex['title'][:50]}")
        print()

    print(f"  Overall consistency: {result.get('consistency_pct')}%")
    if result.get("consistency_pct", 100) < 90:
        print("  ⚠️  Consistency below 90% — review invalid mappings.")
    if result.get("over_priority", 0) > 0:
        print(f"  ⚠️  {result['over_priority']} opportunities have inflated priority.")
    print("  [audit] Read-only. No data was modified.")


def save_report(result: Dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"priority_consistency_audit_{ts}.md"

    lines = [
        "# Priority Consistency Audit Report",
        "",
        f"**Database**: {result.get('database')}",
        f"**Timestamp**: {datetime.now(timezone.utc).isoformat()}",
        f"**Total opportunities**: {result.get('total_opportunities')}",
        f"**Consistency**: {result.get('consistent')}/{result.get('total_opportunities')} "
        f"({result.get('consistency_pct')}%)",
        f"**Over-priority**: {result.get('over_priority')}",
        f"**Under-priority**: {result.get('under_priority')}",
        "",
        "## Per-Type Consistency",
        "",
        "| Type | Count | Consistent | % |",
        "|---|---|---|---|",
    ]
    for t, info in sorted(result.get("type_consistency", {}).items(),
                           key=lambda x: -x[1]["count"]):
        lines.append(f"| {t} | {info['count']} | {info['consistent']}/{info['inconsistent']} "
                      f"| {info['pct']}% |")
    lines.append("")

    lines.append("## Type vs Priority Matrix")
    lines.append("")
    lines.append(f"| {'Type':25s} | {'LOW':10s} | {'MEDIUM':10s} | {'HIGH':10s} | {'CRITICAL':10s} |")
    lines.append(f"| {'-'*25} | {'-'*10} | {'-'*10} | {'-'*10} | {'-'*10} |")
    matrix = result.get("type_priority_matrix", {})
    for t in sorted(matrix.keys()):
        lines.append(f"| {t:25s} | {matrix[t].get('LOW', 0):10d} | "
                      f"{matrix[t].get('MEDIUM', 0):10d} | "
                      f"{matrix[t].get('HIGH', 0):10d} | "
                      f"{matrix[t].get('CRITICAL', 0):10d} |")
    lines.append("")

    if result.get("over_priority_examples"):
        lines.append("## Over-Priority Examples")
        lines.append("")
        for ex in result["over_priority_examples"]:
            lines.append(f"- [{ex['priority']}] {ex['type']}: {ex['title'][:60]} "
                          f"(score={ex['score']}, conv={ex['conviction']})")
        lines.append("")

    if result.get("under_priority_examples"):
        lines.append("## Under-Priority Examples")
        lines.append("")
        for ex in result["under_priority_examples"]:
            lines.append(f"- [{ex['priority']}] {ex['type']}: {ex['title'][:60]} "
                          f"(score={ex['score']}, conv={ex['conviction']})")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    if result.get("consistency_pct", 100) < 90:
        lines.append("- Review all over-priority mappings and adjust thresholds.")
    if result.get("over_priority", 0) > 0:
        lines.append("- WATCHLIST_ADD should not be CRITICAL. Consider capping priority for observational types.")
        lines.append("- Check if the critical evidence gate is too permissive for observational types.")
    if result.get("under_priority", 0) > 0:
        lines.append("- Some actionable types are under-prioritized. Review score thresholds.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by audit_priority_consistency.py*")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[audit] Report saved: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Priority Consistency Audit (read-only)"
    )
    parser.add_argument("--db", default="oma_core.db",
                        help="Path to oma_core.db")
    parser.add_argument("--save", action="store_true",
                        help="Save report to _project-memory/priority_audit/")
    args = parser.parse_args()

    result = audit_consistency(args.db)
    if "error" in result:
        print(f"[audit] Error: {result['error']}")
        sys.exit(1)

    print_report(result)

    if args.save:
        save_report(result)


if __name__ == "__main__":
    main()
