#!/usr/bin/env python3
"""
audit_conviction.py — Read-only conviction audit.

Measures conviction distribution, correlation with score, priority,
and opportunity type. Produces tables and recommendations.

Does NOT modify the database.
"""
import argparse
import json
import os
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import math


REPORT_DIR = Path(__file__).resolve().parent.parent / "_project-memory" / "conviction_audit"
PRIORITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def spearman_rank_correlation(xs: List[float], ys: List[float]) -> float:
    """Compute Spearman rank correlation coefficient."""
    n = min(len(xs), len(ys))
    if n < 3:
        return 0.0
    x_ranks = {v: i for i, v in enumerate(sorted(set(xs)))}
    y_ranks = {v: i for i, v in enumerate(sorted(set(ys)))}
    sr = [x_ranks[xs[i]] for i in range(n)]
    cr = [y_ranks[ys[i]] for i in range(n)]
    sm = sum(sr) / n
    cm = sum(cr) / n
    num = sum((sr[i] - sm) * (cr[i] - cm) for i in range(n))
    den_s = sum((sr[i] - sm) ** 2 for i in range(n)) ** 0.5
    den_c = sum((cr[i] - cm) ** 2 for i in range(n)) ** 0.5
    if den_s * den_c == 0:
        return 0.0
    return round(num / (den_s * den_c), 4)


def audit_conviction(db_path: str) -> Dict[str, Any]:
    if not os.path.exists(db_path):
        return {"error": f"Database not found: {db_path}"}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT score, conviction, priority, opportunity_type, "
        "risk_level, timestamp FROM opportunities ORDER BY timestamp"
    ).fetchall()
    conn.close()

    if not rows:
        return {"error": "No opportunities found"}

    scores = [r["score"] for r in rows]
    convs = [r["conviction"] for r in rows]
    priorities = [r["priority"] for r in rows]
    types = [r["opportunity_type"] for r in rows]
    risks = [r["risk_level"] for r in rows]
    n = len(rows)

    # Basic distribution
    sorted_convs = sorted(convs)
    conv_mean = sum(convs) / n
    conv_median = sorted_convs[n // 2] if n % 2 else (sorted_convs[n // 2 - 1] + sorted_convs[n // 2]) / 2
    conv_min = min(convs)
    conv_max = max(convs)

    # Histogram buckets
    buckets = [(0, 20), (20, 40), (40, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 100)]
    conv_hist = {}
    for lo, hi in buckets:
        label = f"{lo}-{hi}" if hi < 100 else f"{lo}-100"
        conv_hist[label] = sum(1 for c in convs if lo <= c < hi or (hi == 100 and c == 100))

    # Score vs Conviction
    score_conv_corr = spearman_rank_correlation(scores, convs)

    # By priority
    conv_by_priority: Dict[str, List[float]] = defaultdict(list)
    for p, c in zip(priorities, convs):
        conv_by_priority[p].append(c)

    # By type
    conv_by_type: Dict[str, List[float]] = defaultdict(list)
    for t, c in zip(types, convs):
        conv_by_type[t].append(c)

    # By risk level
    conv_by_risk: Dict[str, List[float]] = defaultdict(list)
    for r, c in zip(risks, convs):
        conv_by_risk[r].append(c)

    # Unique conviction values
    unique_convs = len(set(convs))
    repeated = Counter(convs)
    most_repeated = {str(k): v for k, v in repeated.most_common(5) if v > 1}

    # Static detection: are many convictions identical?
    # Count how many distinct values
    conv_by_source_static = {}
    for r in rows:
        src = r["opportunity_type"]
        if src not in conv_by_source_static:
            conv_by_source_static[src] = {"values": set(), "count": 0}
        conv_by_source_static[src]["values"].add(r["conviction"])
        conv_by_source_static[src]["count"] += 1

    static_types = {}
    for t, d in conv_by_source_static.items():
        if len(d["values"]) <= 2 and d["count"] > 3:
            static_types[t] = {
                "count": d["count"],
                "unique_conviction_values": len(d["values"]),
                "values": sorted(d["values"]),
            }

    def _stats(vals):
        if not vals:
            return None
        s = sorted(vals)
        return {
            "mean": round(sum(vals) / len(vals), 2),
            "median": s[len(s) // 2],
            "min": min(vals),
            "max": max(vals),
            "count": len(vals),
        }

    return {
        "database": db_path,
        "total_opportunities": n,
        "conviction_distribution": {
            "mean": round(conv_mean, 2),
            "median": round(conv_median, 2),
            "min": conv_min,
            "max": conv_max,
            "histogram": conv_hist,
            "unique_values": unique_convs,
            "total_values": n,
            "value_repeat_ratio": round(unique_convs / n * 100, 1),
            "most_repeated_values": most_repeated,
        },
        "score_conviction_correlation": score_conv_corr,
        "conviction_by_priority": {k: _stats(v) for k, v in sorted(conv_by_priority.items())},
        "conviction_by_type": {k: _stats(v) for k, v in sorted(conv_by_type.items())},
        "conviction_by_risk": {k: _stats(v) for k, v in sorted(conv_by_risk.items())},
        "static_conviction_types": static_types,
    }


def print_report(result: Dict[str, Any]) -> None:
    print()
    print("=" * 60)
    print("  Conviction Audit")
    print("=" * 60)
    print(f"  Database: {result.get('database')}")
    print(f"  Total opportunities: {result.get('total_opportunities')}")
    print()

    d = result.get("conviction_distribution", {})
    print("--- Conviction Distribution ---")
    print(f"  Mean: {d.get('mean')}  Median: {d.get('median')}")
    print(f"  Range: {d.get('min')} - {d.get('max')}")
    print(f"  Unique values: {d.get('unique_values')}/{d.get('total_values')} "
          f"({d.get('value_repeat_ratio')}%)")
    print(f"  Histogram: {d.get('histogram')}")
    print(f"  Most repeated: {d.get('most_repeated_values')}")
    print()

    print("--- Score vs Conviction Correlation ---")
    corr = result.get("score_conviction_correlation", 0)
    print(f"  Spearman rank correlation: {corr}")
    if abs(corr) < 0.3:
        print("  ✓ Low correlation — conviction is well decoupled from score.")
    elif abs(corr) < 0.7:
        print("  ⚠ Moderate correlation — partial coupling remains.")
    else:
        print("  ✗ High correlation — conviction still mirrors score.")
    print()

    print("--- Conviction by Priority ---")
    for p in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        info = result.get("conviction_by_priority", {}).get(p)
        if info:
            print(f"  {p:10s} mean={info['mean']:6.2f}  range={info['min']:5.1f}-{info['max']:5.1f}  n={info['count']}")
    print()

    print("--- Conviction by Opportunity Type (top 10 by count) ---")
    by_type = result.get("conviction_by_type", {})
    for t, info in sorted(by_type.items(), key=lambda x: -x[1]["count"])[:10]:
        print(f"  {t:25s} mean={info['mean']:6.2f}  range={info['min']:5.1f}-{info['max']:5.1f}  n={info['count']}")
    print()

    print("--- Static Conviction Types (>3 opps, ≤2 unique conviction values) ---")
    static = result.get("static_conviction_types", {})
    if static:
        for t, info in sorted(static.items(), key=lambda x: -x[1]["count"]):
            print(f"  ⚠ {t:25s} count={info['count']:3d}  unique_convictions={info['unique_conviction_values']}  "
                  f"values={info['values']}")
        print()
        print("  Recommendation: Add variance sources to conviction formula for these types.")
    else:
        print("  ✓ No significant conviction clustering detected.")
    print()

    print("--- Conviction by Risk Level ---")
    for r in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]:
        info = result.get("conviction_by_risk", {}).get(r)
        if info:
            print(f"  {r:10s} mean={info['mean']:6.2f}  range={info['min']:5.1f}-{info['max']:5.1f}  n={info['count']}")
    print()

    print("  [audit] Read-only. No data was modified.")


def save_report(result: Dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"conviction_audit_{ts}.md"

    lines = [
        "# Conviction Audit Report",
        "",
        f"**Database**: {result.get('database')}",
        f"**Timestamp**: {datetime.now(timezone.utc).isoformat()}",
        f"**Total opportunities**: {result.get('total_opportunities')}",
        "",
        "## Conviction Distribution",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    d = result.get("conviction_distribution", {})
    for k, v in d.items():
        if k != "histogram" and k != "most_repeated_values":
            lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("**Histogram**: " + str(d.get("histogram", {})))
    lines.append("")
    lines.append("**Most repeated values**: " + str(d.get("most_repeated_values", {})))
    lines.append("")

    lines.append("## Score vs Conviction Correlation")
    lines.append("")
    corr = result.get("score_conviction_correlation", 0)
    lines.append(f"**Spearman rank correlation**: {corr}")
    if abs(corr) < 0.3:
        lines.append("*Low correlation — conviction is well decoupled.*")
    elif abs(corr) < 0.7:
        lines.append("*Moderate correlation — partial coupling remains.*")
    else:
        lines.append("*High correlation — conviction still mirrors score.*")
    lines.append("")

    lines.append("## Conviction by Priority")
    lines.append("")
    lines.append("| Priority | Mean | Median | Min | Max | Count |")
    lines.append("|---|---|---|---|---|---|")
    for p in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        info = result.get("conviction_by_priority", {}).get(p)
        if info:
            lines.append(f"| {p} | {info['mean']} | {info['median']} | {info['min']} | {info['max']} | {info['count']} |")
    lines.append("")

    lines.append("## Conviction by Type")
    lines.append("")
    lines.append("| Type | Mean | Median | Min | Max | Count |")
    lines.append("|---|---|---|---|---|---|")
    for t, info in sorted(result.get("conviction_by_type", {}).items(), key=lambda x: -x[1]["count"]):
        lines.append(f"| {t} | {info['mean']} | {info['median']} | {info['min']} | {info['max']} | {info['count']} |")
    lines.append("")

    lines.append("## Static Conviction Types")
    lines.append("")
    static = result.get("static_conviction_types", {})
    if static:
        for t, info in sorted(static.items(), key=lambda x: -x[1]["count"]):
            lines.append(f"- **{t}**: {info['count']} opps, only {info['unique_conviction_values']} unique values: {info['values']}")
        lines.append("")
        lines.append("**Recommendation**: Add variance sources to conviction formula.")
    else:
        lines.append("No significant clustering detected.")
    lines.append("")

    lines.append("## Conviction by Risk Level")
    lines.append("")
    lines.append("| Risk | Mean | Median | Min | Max | Count |")
    lines.append("|---|---|---|---|---|---|")
    for r in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]:
        info = result.get("conviction_by_risk", {}).get(r)
        if info:
            lines.append(f"| {r} | {info['mean']} | {info['median']} | {info['min']} | {info['max']} | {info['count']} |")
    lines.append("")

    lines.append("---")
    lines.append("*Report generated by audit_conviction.py*")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[conviction] Report saved: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Conviction Audit (read-only)"
    )
    parser.add_argument("--db", default="oma_core.db",
                        help="Path to oma_core.db")
    parser.add_argument("--save", action="store_true",
                        help="Save report to _project-memory/conviction_audit/")
    args = parser.parse_args()

    result = audit_conviction(args.db)
    if "error" in result:
        print(f"[conviction] Error: {result['error']}")
        return

    print_report(result)

    if args.save:
        save_report(result)


if __name__ == "__main__":
    main()
