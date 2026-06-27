#!/usr/bin/env python3
"""O.M.A.-C.O.R.E. Read-Only Operational Integration CLI

Connects the Scientific Learning Laboratory to real operational data sources
in read-only mode. Defaults to AUDIT mode — no writes, no transformations.

Modes:
  --audit     Inspect sources, list tables/files, no transformations, no writes.
  --dry-run   Read + transform in-memory learning objects, no writes.
  --commit    Read + transform + write to scientific.db (requires explicit flag).

Usage:
  python scripts/read_only_operational_integration.py --audit
  python scripts/read_only_operational_integration.py --dry-run --source oma_core.db
  python scripts/read_only_operational_integration.py --commit --source fixtures/sample_trades.json
  python scripts/read_only_operational_integration.py --dry-run --auto-discover --limit 100
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.scientific.operational_reader import (
    OperationalReader, OperationalDataInventory, OperationalLearningSession,
    REPORT_DIR,
)


def main():
    parser = argparse.ArgumentParser(
        description="O.M.A.-C.O.R.E. Read-Only Operational Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--audit", action="store_true", help="AUDIT mode: inspect sources only (default)")
    mode_group.add_argument("--dry-run", action="store_true", help="DRY RUN mode: read + transform in-memory only")
    mode_group.add_argument("--commit", action="store_true", help="COMMIT mode: read + transform + write to scientific.db")

    parser.add_argument("--source", action="append", dest="sources", help="Path to operational data source (repeatable)")
    parser.add_argument("--auto-discover", action="store_true", help="Auto-discover operational data sources")
    parser.add_argument("--limit", type=int, default=5000, help="Max records to process (default: 5000)")
    parser.add_argument("--report-dir", type=str, default=None, help="Output directory for reports")
    parser.add_argument("--no-reports", action="store_true", help="Skip report file generation")

    args = parser.parse_args()

    print(f"{'=' * 55}")
    print(f"  O.M.A.-C.O.R.E. Read-Only Operational Integration")
    print(f"{'=' * 55}")
    print()
    print(f"  MODE: ", end="")

    if args.commit:
        print("COMMIT")
        print(f"  WARNING: This will write to scientific.db!")
        print(f"  WARNING: Ensure oma_core.db is NOT in the source list.")
        print()
        confirm = input("  Type 'commit' to confirm: ")
        if confirm.strip().lower() != "commit":
            print("  Aborted.")
            return 1
    elif args.dry_run:
        print("DRY RUN")
    else:
        print("AUDIT")

    if args.commit:
        mode = "commit"
    elif args.dry_run:
        mode = "dry_run"
    else:
        mode = "audit"

    reader = OperationalReader(limit=args.limit)

    if args.sources:
        for src in args.sources:
            reader.add_source(src)

    if args.auto_discover:
        discovered = reader.auto_discover()
        print(f"\n  Auto-discovered {len(discovered)} source(s):")
        for d in discovered:
            print(f"    - {d}")

    print(f"\n  Running {mode.upper()}...")

    if mode == "audit":
        inventory = reader.run_audit()
        inventory.print_summary()
        if not args.no_reports:
            path = inventory.save(Path(args.report_dir) if args.report_dir else None)
            print(f"  Report saved: {path}")
    else:
        session = reader.run(mode=mode)
        session.print_summary()
        if not args.no_reports:
            json_path = session.save_json(Path(args.report_dir) if args.report_dir else None)
            md_path = session.save_markdown(Path(args.report_dir) if args.report_dir else None)
            print(f"  JSON report:    {json_path}")
            print(f"  Markdown report: {md_path}")

    print(f"\n  {'=' * 55}")
    print(f"  Stage 9 — Read-Only Operational Integration Complete")
    print(f"  {'=' * 55}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
