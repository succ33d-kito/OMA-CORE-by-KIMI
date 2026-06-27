#!/usr/bin/env python3
"""O.M.A.-C.O.R.E. Historical Learning Replay CLI

Offline replay of historical trade records → scientific learning objects.

Usage:
  python scripts/historical_learning_replay.py --dry-run
  python scripts/historical_learning_replay.py --commit
  python scripts/historical_learning_replay.py --source oma_core.db --dry-run
  python scripts/historical_learning_replay.py --source fixtures/trades.json --dry-run
  python scripts/historical_learning_replay.py --limit 50 --report-md --dry-run
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.scientific.historical_replay import HistoricalReplay, REPORT_DIR


def main():
    parser = argparse.ArgumentParser(
        description="O.M.A.-C.O.R.E. Historical Learning Replay",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source", default=None,
        help="Path to source data (SQLite DB or JSON/JSONL file). Default: oma_core.db"
    )
    parser.add_argument(
        "--dry-run", dest="dry_run", action="store_true", default=True,
        help="Run in dry-run mode — no writes to scientific.db (default)"
    )
    parser.add_argument(
        "--commit", dest="dry_run", action="store_false",
        help="Commit mode — writes to scientific.db"
    )
    parser.add_argument(
        "--limit", type=int, default=100,
        help="Maximum number of records to process (default: 100)"
    )
    parser.add_argument(
        "--report-md", action="store_true", default=False,
        help="Also generate a Markdown report alongside JSON"
    )
    parser.add_argument(
        "--report-dir", default=None,
        help="Custom report output directory (default: _project-memory/learning_replay/)"
    )

    args = parser.parse_args()

    source = args.source or "oma_core.db"
    report_dir = Path(args.report_dir) if args.report_dir else REPORT_DIR

    mode = "DRY RUN" if args.dry_run else "COMMIT"
    print(f"\n  Historical Learning Replay — {mode}")
    print(f"  Source: {source}")
    print(f"  Limit:  {args.limit}")
    print()

    replay = HistoricalReplay(
        source=source,
        is_dry_run=args.dry_run,
        limit=args.limit,
    )

    session = replay.run()
    session.print_summary()

    report_path = session.save_report(report_dir=report_dir)
    print(f"  Report saved: {report_path}")

    if args.report_md:
        md_path = report_path.with_suffix(".md")
        _save_md_report(session, md_path)
        print(f"  Markdown report: {md_path}")

    if args.dry_run:
        print(f"  → Run with --commit to write to scientific.db")

    sys.exit(0 if session.comparisons_created > 0 else 1)


def _save_md_report(session, path: Path) -> None:
    d = session.to_dict()
    lines = [
        f"# Learning Replay Report",
        f"",
        f"**Session:** `{d['session_id'][:16]}...`  ",
        f"**Timestamp:** {d['timestamp']}  ",
        f"**Source:** {d['source']}  ",
        f"**Mode:** {d['mode']}  ",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Records Read | {d['records_read']} |",
        f"| Hypotheses Created | {d['hypotheses_created']} |",
        f"| Comparisons Created | {d['comparisons_created']} |",
        f"| Knowledge Created | {d['knowledge_created']} |",
        f"| Criterion Deltas Proposed | {d['criterion_deltas_proposed']} |",
        f"",
        f"## Verdict Distribution",
        f"",
    ]
    for v, c in sorted(d['verdict_distribution'].items()):
        lines.append(f"- **{v}**: {c}")
    if d['error_type_distribution']:
        lines.extend(["", "## Error Type Distribution", ""])
        for e, c in sorted(d['error_type_distribution'].items()):
            lines.append(f"- **{e}**: {c}")
    if d['missing_fields_summary']:
        lines.extend(["", "## Missing Fields", ""])
        for f, c in sorted(d['missing_fields_summary'].items()):
            lines.append(f"- **{f}**: {c}")
    if d['warnings']:
        lines.extend(["", "## Warnings", ""])
        for w in d['warnings']:
            lines.append(f"- ⚠ {w}")
    lines.extend([
        "",
        f"## Recommended Next Action",
        f"",
        f"{d['recommended_next_action']}",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
