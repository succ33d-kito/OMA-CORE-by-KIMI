#!/usr/bin/env python3
"""
audit_score_saturation.py — Read-only score calibration and data quality audit.

Inspects opportunities/events from oma_core.db and reports:
  - Priority distribution and saturation
  - Score distribution and anomalies
  - Asset/value anomalies (price=0, -100% change, etc.)
  - Source breakdown
  - Opportunity type breakdown
  - Suspicious patterns and root-cause hypotheses

Outputs:
  - Terminal report
  - JSON report: _project-memory/score_calibration/score_saturation_audit_<ts>.json
  - Markdown report: _project-memory/score_calibration/score_saturation_audit_<ts>.md

Does NOT modify the database.
"""

import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


REPORT_DIR = Path(__file__).resolve().parent.parent / "_project-memory" / "score_calibration"


def query_opportunities(db_path: str) -> List[Dict[str, Any]]:
    """Read opportunities from the database. Read-only."""
    if not os.path.exists(db_path):
        print(f"[audit] Database not found: {db_path}")
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM opportunities ORDER BY score DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_events(db_path: str) -> List[Dict[str, Any]]:
    """Read events from the database. Read-only."""
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM events ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def parse_assets(assets_str: Any) -> List[str]:
    """Safely parse the assets field from JSON string."""
    if assets_str is None:
        return []
    if isinstance(assets_str, list):
        return assets_str
    if isinstance(assets_str, str):
        try:
            return json.loads(assets_str)
        except (json.JSONDecodeError, TypeError):
            return [assets_str]
    return []


def compute_priority_distribution(opps: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for opp in opps:
        p = opp.get("priority", "UNKNOWN")
        counts[p] = counts.get(p, 0) + 1
    total = len(opps)
    critical_pct = round(counts.get("CRITICAL", 0) / total * 100, 1) if total else 0
    saturated = critical_pct >= 80 and total >= 5
    return {
        "total": total,
        "counts": counts,
        "critical_percentage": critical_pct,
        "saturated": saturated,
    }


def compute_score_distribution(opps: List[Dict[str, Any]]) -> Dict[str, Any]:
    scores = [o.get("score") for o in opps if o.get("score") is not None]
    convs = [o.get("conviction") for o in opps if o.get("conviction") is not None]
    if not scores:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None,
                "at_100": 0, "pct_at_100": 0, "repeated_scores": [], "histogram": {},
                "conviction_mean": None, "conviction_histogram": {}, "score_conviction_correlation": None}
    sorted_scores = sorted(scores)
    mean = sum(scores) / len(scores)
    median = sorted_scores[len(sorted_scores) // 2] if len(sorted_scores) % 2 else \
        (sorted_scores[len(sorted_scores) // 2 - 1] + sorted_scores[len(sorted_scores) // 2]) / 2
    at_100 = sum(1 for s in scores if s >= 100)
    score_counter = Counter(scores)
    repeated = {str(k): v for k, v in score_counter.items() if v > 1}
    
    # Histogram buckets
    buckets = [(0, 20), (20, 40), (40, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 100)]
    histogram = {}
    for lo, hi in buckets:
        label = f"{lo}-{hi}" if hi < 100 else f"{lo}-100"
        histogram[label] = sum(1 for s in scores if lo <= s < hi or (hi == 100 and s == 100))
    
    # Conviction histogram (same buckets)
    conv_histogram = {}
    for lo, hi in buckets:
        label = f"{lo}-{hi}" if hi < 100 else f"{lo}-100"
        conv_histogram[label] = sum(1 for c in convs if lo <= c < hi or (hi == 100 and c == 100))
    
    # Score vs conviction correlation (Spearman rank approximation)
    corr = None
    if len(scores) > 1 and len(convs) > 1:
        n = min(len(scores), len(convs))
        score_ranks = {v: i for i, v in enumerate(sorted(set(scores)))}
        conv_ranks = {v: i for i, v in enumerate(sorted(set(convs)))}
        s_ranks = [score_ranks[scores[i]] for i in range(n)]
        c_ranks = [conv_ranks[convs[i]] for i in range(n)]
        s_mean = sum(s_ranks) / n
        c_mean = sum(c_ranks) / n
        num = sum((s_ranks[i] - s_mean) * (c_ranks[i] - c_mean) for i in range(n))
        den_s = sum((s_ranks[i] - s_mean) ** 2 for i in range(n)) ** 0.5
        den_c = sum((c_ranks[i] - c_mean) ** 2 for i in range(n)) ** 0.5
        if den_s > 0 and den_c > 0:
            corr = round(num / (den_s * den_c), 4)
    
    return {
        "count": len(scores),
        "min": min(scores),
        "max": max(scores),
        "mean": round(mean, 2),
        "median": round(median, 2),
        "at_100": at_100,
        "pct_at_100": round(at_100 / len(scores) * 100, 1) if scores else 0,
        "repeated_scores": repeated,
        "histogram": histogram,
        "conviction_mean": round(sum(convs) / len(convs), 2) if convs else None,
        "conviction_histogram": conv_histogram,
        "score_conviction_correlation": corr,
    }


def detect_asset_anomalies(opps: List[Dict[str, Any]]) -> Dict[str, Any]:
    anomalies = {
        "price_zero": 0,
        "pct_negative_100": 0,
        "missing_price": 0,
        "missing_return": 0,
        "malformed_assets": 0,
        "asset_examples": [],
    }
    for opp in opps:
        desc = opp.get("description", "") or ""
        if "$0.00" in desc or "$0" in desc.replace(",", ""):
            anomalies["price_zero"] += 1
        if "-100.00%" in desc or "-100%" in desc:
            anomalies["pct_negative_100"] += 1
        if "$" not in desc and ("price" in desc.lower() or "pnl" in desc.lower()):
            anomalies["missing_price"] += 1
        assets = parse_assets(opp.get("assets"))
        if not assets:
            anomalies["missing_return"] += 1
        if isinstance(opp.get("assets"), str) and opp["assets"].startswith("[") and \
                any(c in opp["assets"] for c in ['"', ',']):
            parsed = parse_assets(opp["assets"])
            if any(len(a) == 1 for a in parsed):
                anomalies["malformed_assets"] += 1
                if len(anomalies["asset_examples"]) < 5:
                    anomalies["asset_examples"].append(opp["assets"])
    return anomalies


def compute_source_breakdown(events: List[Dict[str, Any]]) -> Dict[str, int]:
    sources: Dict[str, int] = {}
    for ev in events:
        s = ev.get("source", "unknown")
        sources[s] = sources.get(s, 0) + 1
    return sources


def compute_type_breakdown(opps: List[Dict[str, Any]]) -> Dict[str, int]:
    types: Dict[str, int] = {}
    for opp in opps:
        t = opp.get("opportunity_type", "UNKNOWN")
        types[t] = types.get(t, 0) + 1
    return types


def count_data_quality_issues(opps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Count opportunities with data quality markers."""
    result = {
        "data_quality_issues": 0,
        "data_quality_capped": 0,
        "yahoo_price_zero": 0,
        "yahoo_pct_negative_100": 0,
        "yahoo_malformed": 0,
    }
    for opp in opps:
        is_dq = opp.get("data_quality_reason", "") or opp.get("title", "").startswith("[DATA_QUALITY]")
        if is_dq:
            result["data_quality_issues"] += 1
        if opp.get("score", 100) <= 30 and opp.get("priority") in ("LOW", "MEDIUM"):
            result["data_quality_capped"] += 1
        if opp.get("source") == "yahoo_finance":
            desc = opp.get("description", "") or ""
            if "$0.00" in desc or "$0" in desc.replace(",", ""):
                result["yahoo_price_zero"] += 1
            if "-100.00%" in desc or "-100%" in desc:
                result["yahoo_pct_negative_100"] += 1
            assets = opp.get("assets", "")
            if isinstance(assets, str) and len(assets) > 1 and assets.startswith("["):
                result["yahoo_malformed"] += 1
    return result


def detect_pre_guard_artifacts(result: Dict[str, Any]) -> Dict[str, Any]:
    """Detect historical pre-guard data artifacts (read-only)."""
    dq = result.get("data_quality", {})
    anomalies = result.get("asset_anomalies", {})
    priority = result.get("priority_distribution", {})
    scores = result.get("score_distribution", {})
    
    # Estimate pre-guard artifacts:
    #   - price_zero opportunities that predate the Yahoo guard
    #   - opportunities with -100% change that predate the guard
    pre_guard_price_zero = max(
        dq.get("yahoo_price_zero", 0),
        anomalies.get("price_zero", 0)
    )
    pre_guard_negative_100 = max(
        dq.get("yahoo_pct_negative_100", 0),
        anomalies.get("pct_negative_100", 0)
    )
    pre_guard_score_100 = scores.get("at_100", 0)
    
    estimated_pre_guard_opportunities = max(
        pre_guard_price_zero, pre_guard_negative_100, pre_guard_score_100
    )
    
    return {
        "pre_guard_artifacts_detected": pre_guard_price_zero > 0 or pre_guard_negative_100 > 0,
        "estimated_pre_guard_opportunity_count": estimated_pre_guard_opportunities,
        "yahoo_price_zero_count": pre_guard_price_zero,
        "yahoo_negative_100_count": pre_guard_negative_100,
        "yahoo_score_100_count": pre_guard_score_100,
        "recommendation": (
            "Run a one-time purge script after score calibration to remove "
            "or reclassify pre-guard artifacts. See Sprint 13 final report."
        ),
        "action": "READ_ONLY — no data was modified",
    }


def detect_suspicious_patterns(opps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    patterns: List[Dict[str, Any]] = []
    for opp in opps[:50]:
        desc = opp.get("description", "") or ""
        score = opp.get("score", 0)
        conviction = opp.get("conviction", 0)
        if score >= 100 and ("$0.00" in desc or "$0" in desc.replace(",", "")):
            patterns.append({
                "id": opp.get("id"),
                "pattern": "score_100_plus_price_zero",
                "title": opp.get("title", "")[:80],
                "score": score,
            })
        if "-100.00%" in desc or "-100%" in desc:
            patterns.append({
                "id": opp.get("id"),
                "pattern": "negative_100_percent",
                "title": opp.get("title", "")[:80],
                "score": score,
            })
    # Check for repeated convictions
    conv_counter = Counter(o.get("conviction") for o in opps if o.get("conviction") is not None)
    for val, count in conv_counter.most_common(3):
        if count > 5:
            patterns.append({
                "pattern": "repeated_conviction",
                "value": val,
                "count": count,
            })
    return patterns


def build_hypotheses(anomalies: Dict[str, Any], priority: Dict[str, Any],
                     scores: Dict[str, Any], source_breakdown: Dict[str, int],
                     suspicious: List[Dict[str, Any]]) -> List[str]:
    hypotheses = []

    if anomalies.get("price_zero", 0) > 0:
        hypotheses.append(
            "Missing price data: Yahoo Finance or other price feeds returning $0.00. "
            "This inflates urgency/sentiment for price-movement events while the "
            "underlying data is invalid. Root cause: data source normalization bug "
            "or API rate limiting."
        )
    if anomalies.get("pct_negative_100", 0) > 0:
        hypotheses.append(
            "Failed data downloads treated as -100% returns: When Yahoo Finance "
            "fails to fetch price data, percent_change may be interpreted as -100%. "
            "This creates extreme bearish events that score highly."
        )
    if priority.get("saturated"):
        hypotheses.append(
            f"Priority saturation: {priority['critical_percentage']}% of all "
            f"opportunities are CRITICAL. The threshold in _determine_priority "
            f"(combined >= 92 → CRITICAL) is too easily reached when both score "
            f"and conviction are above ~85. Combined with stale events being "
            f"re-processed, almost every event becomes CRITICAL."
        )
    if scores.get("pct_at_100", 0) > 20:
        hypotheses.append(
            f"Score clipping: {scores['pct_at_100']}% of scores are 100. "
            f"The min(raw_score * multiplier, 100) cap in ScoreEngine is hit "
            f"too frequently. Events with CRITICAL urgency (100) + strong "
            f"sentiment + 1.3× macro multiplier exceed 100 before clipping."
        )
    if anomalies.get("malformed_assets", 0) > 0:
        hypotheses.append(
            "Malformed asset lists: Some assets stored as character-level JSON "
            "strings. Likely from a serialization/deserialization mismatch in "
            "the event pipeline."
        )
    if source_breakdown.get("fred", 0) == 0:
        hypotheses.append(
            "Zero FRED events: Missing FRED_API_KEY in .env causes HTTP 400 "
            "on all FRED requests. This reduces diversity of macro events."
        )
    if not hypotheses:
        hypotheses.append("No significant anomalies detected.")

    return hypotheses


def run_audit(db_path: str = "oma_core.db") -> Dict[str, Any]:
    print(f"[audit] Reading database: {db_path}")
    opps = query_opportunities(db_path)
    events = query_events(db_path)
    print(f"[audit] Opportunities: {len(opps)}, Events: {len(events)}")

    priority = compute_priority_distribution(opps)
    scores = compute_score_distribution(opps)
    anomalies = detect_asset_anomalies(opps)
    source_breakdown = compute_source_breakdown(events)
    type_breakdown = compute_type_breakdown(opps)
    suspicious = detect_suspicious_patterns(opps)
    data_quality = count_data_quality_issues(opps)
    hypotheses = build_hypotheses(anomalies, priority, scores, source_breakdown, suspicious)

    pre_guard = detect_pre_guard_artifacts({
        "data_quality": data_quality,
        "asset_anomalies": anomalies,
        "priority_distribution": priority,
        "score_distribution": scores,
    })

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_path,
        "total_opportunities": len(opps),
        "total_events": len(events),
        "priority_distribution": priority,
        "score_distribution": scores,
        "asset_anomalies": anomalies,
        "data_quality": data_quality,
        "source_breakdown": source_breakdown,
        "type_breakdown": type_breakdown,
        "suspicious_patterns": suspicious,
        "pre_guard_artifacts": pre_guard,
        "hypotheses": hypotheses,
    }
    return result


def print_terminal_report(result: Dict[str, Any]) -> None:
    print()
    print("=" * 60)
    print("  Score Saturation Audit Report")
    print("=" * 60)
    print(f"  Timestamp: {result['timestamp']}")
    print(f"  DB: {result['database']}")
    print(f"  Opportunities: {result['total_opportunities']}")
    print(f"  Events: {result['total_events']}")
    print()

    p = result["priority_distribution"]
    print("--- Priority Distribution ---")
    for pri, cnt in sorted(p.get("counts", {}).items()):
        print(f"  {pri}: {cnt}")
    print(f"  Critical: {p.get('critical_percentage')}%  Saturated: {p.get('saturated')}")
    print()

    s = result["score_distribution"]
    print("--- Score Distribution ---")
    print(f"  Count: {s.get('count')}  Min: {s.get('min')}  Max: {s.get('max')}")
    print(f"  Mean: {s.get('mean')}  Median: {s.get('median')}")
    print(f"  At 100: {s.get('at_100')} ({s.get('pct_at_100')}%)")
    print(f"  Repeated scores: {len(s.get('repeated_scores', {}))}")
    print(f"  Histogram: {s.get('histogram', {})}")
    if s.get("conviction_mean") is not None:
        print(f"  Mean conviction: {s['conviction_mean']}")
        print(f"  Conviction histogram: {s.get('conviction_histogram', {})}")
    if s.get("score_conviction_correlation") is not None:
        print(f"  Score/Conviction rank correlation: {s['score_conviction_correlation']}")
    print()

    a = result["asset_anomalies"]
    print("--- Asset Anomalies ---")
    print(f"  Price $0.00: {a.get('price_zero')}")
    print(f"  -100% change: {a.get('pct_negative_100')}")
    print(f"  Missing price: {a.get('missing_price')}")
    print(f"  Missing return: {a.get('missing_return')}")
    print(f"  Malformed assets: {a.get('malformed_assets')}")
    if a.get("asset_examples"):
        print("  Examples:")
        for ex in a["asset_examples"]:
            print(f"    {ex[:80]}")
    print()

    print("--- Source Breakdown ---")
    for src, cnt in sorted(result.get("source_breakdown", {}).items(), key=lambda x: -x[1]):
        print(f"  {src}: {cnt}")
    print()

    dq = result.get("data_quality", {})
    print("--- Data Quality ---")
    print(f"  Issues flagged:       {dq.get('data_quality_issues')}")
    print(f"  Score-capped (<=30):  {dq.get('data_quality_capped')}")
    print(f"  Yahoo price $0.00:    {dq.get('yahoo_price_zero')}")
    print(f"  Yahoo -100% change:   {dq.get('yahoo_pct_negative_100')}")
    print(f"  Yahoo guard status:   {'ACTIVE' if dq.get('data_quality_capped', 0) > 0 else 'NOT ACTIVE'}")
    print()

    pg = result.get("pre_guard_artifacts", {})
    print("--- Pre-Guard Artifacts (Read-Only Report) ---")
    print(f"  Pre-guard artifacts detected: {pg.get('pre_guard_artifacts_detected')}")
    print(f"  Estimated pre-guard count: {pg.get('estimated_pre_guard_opportunity_count')}")
    print(f"  Price-zero artifacts: {pg.get('yahoo_price_zero_count')}")
    print(f"  -100% change artifacts: {pg.get('yahoo_negative_100_count')}")
    print(f"  Score 100 artifacts: {pg.get('yahoo_score_100_count')}")
    print(f"  Recommendation: {pg.get('recommendation')}")
    print()

    print("--- Type Breakdown ---")
    for t, cnt in sorted(result.get("type_breakdown", {}).items(), key=lambda x: -x[1]):
        print(f"  {t}: {cnt}")
    print()

    print("--- Suspicious Patterns ---")
    for pat in result.get("suspicious_patterns", []):
        print(f"  {pat.get('pattern')}: {pat.get('title', '')} (score={pat.get('score')})")
    print()

    print("--- Root-Cause Hypotheses ---")
    for i, h in enumerate(result.get("hypotheses", []), 1):
        print(f"  {i}. {h}")
    print()
    print("=" * 60)


def save_reports(result: Dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    json_path = REPORT_DIR / f"score_saturation_audit_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"[audit] JSON report: {json_path}")

    md_path = REPORT_DIR / f"score_saturation_audit_{ts}.md"
    lines = [
        "# Score Saturation Audit Report",
        "",
        f"**Timestamp**: {result['timestamp']}",
        f"**Database**: {result['database']}",
        f"**Opportunities**: {result['total_opportunities']}",
        f"**Events**: {result['total_events']}",
        "",
        "## Priority Distribution",
        "",
    ]
    p = result["priority_distribution"]
    for pri, cnt in sorted(p.get("counts", {}).items()):
        lines.append(f"- **{pri}**: {cnt}")
    lines.append(f"- **Critical %**: {p.get('critical_percentage')}%")
    lines.append(f"- **Saturated**: {p.get('saturated')}")
    lines.append("")

    s = result["score_distribution"]
    lines.append("## Score Distribution")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Count | {s.get('count')} |")
    lines.append(f"| Min | {s.get('min')} |")
    lines.append(f"| Max | {s.get('max')} |")
    lines.append(f"| Mean | {s.get('mean')} |")
    lines.append(f"| Median | {s.get('median')} |")
    lines.append(f"| At 100 | {s.get('at_100')} ({s.get('pct_at_100')}%) |")
    lines.append(f"| Repeated score sets | {len(s.get('repeated_scores', {}))} |")
    lines.append("")

    a = result["asset_anomalies"]
    lines.append("## Asset Anomalies")
    lines.append("")
    for k, v in a.items():
        if k != "asset_examples":
            lines.append(f"- **{k}**: {v}")
    if a.get("asset_examples"):
        lines.append("- **Examples**:")
        for ex in a["asset_examples"]:
            lines.append(f"  - `{ex[:80]}`")
    lines.append("")

    lines.append("## Data Quality")
    lines.append("")
    dq = result.get("data_quality", {})
    for k, v in dq.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")

    lines.append("## Source Breakdown")
    lines.append("")
    for src, cnt in sorted(result.get("source_breakdown", {}).items(), key=lambda x: -x[1]):
        lines.append(f"- **{src}**: {cnt}")
    lines.append("")

    lines.append("## Type Breakdown")
    lines.append("")
    for t, cnt in sorted(result.get("type_breakdown", {}).items(), key=lambda x: -x[1]):
        lines.append(f"- **{t}**: {cnt}")
    lines.append("")

    lines.append("## Suspicious Patterns")
    lines.append("")
    for pat in result.get("suspicious_patterns", []):
        lines.append(f"- **{pat.get('pattern')}**: {pat.get('title', pat.get('value', ''))} (count={pat.get('count', 1)})")
    lines.append("")

    lines.append("## Root-Cause Hypotheses")
    lines.append("")
    for i, h in enumerate(result.get("hypotheses", []), 1):
        lines.append(f"{i}. {h}")
    lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[audit] Markdown report: {md_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Score Saturation Audit (read-only)")
    parser.add_argument("--db", default="oma_core.db", help="Path to oma_core.db")
    parser.add_argument("--save", action="store_true", help="Save reports to _project-memory/score_calibration/")
    args = parser.parse_args()

    result = run_audit(args.db)
    print_terminal_report(result)

    if args.save:
        save_reports(result)

    print()
    if result["priority_distribution"].get("saturated"):
        print("[audit] ⚠️  PRIORITY SATURATION DETECTED — scoring calibration review recommended.")
    if result["score_distribution"].get("pct_at_100", 0) > 20:
        print("[audit] ⚠️  SCORE SATURATION DETECTED — >20% of scores are maxed at 100.")
    pg = result.get("pre_guard_artifacts", {})
    if pg.get("pre_guard_artifacts_detected"):
        print(f"[audit] ⚠️  {pg.get('estimated_pre_guard_opportunity_count')} PRE-GUARD ARTIFACTS — see report section.")
    corr = result.get("score_distribution", {}).get("score_conviction_correlation")
    if corr is not None and abs(corr) > 0.7:
        print(f"[audit] ⚠️  Score/Conviction correlation = {corr} — conviction may not be fully decoupled.")
    print("[audit] Audit complete. No data was modified.")


if __name__ == "__main__":
    main()
