#!/usr/bin/env python3
"""Extended Demo Pre-Flight Check — verifies readiness for 7-day smoke run."""

import json
import sys
from pathlib import Path


def check(condition: bool, description: str, fix_hint: str = "") -> tuple[bool, str, str]:
    if condition:
        return (True, description, "")
    return (False, description, fix_hint)


def main():
    output_dir = Path("_project-memory/operational_validation")
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[tuple[bool, str, str]] = []
    failures = 0
    warnings = 0

    # 1. Required directories
    print("[1/10] Checking required directories...")
    results.append(check(
        Path("_extended_demo").is_dir(),
        "Directory `_extended_demo/` exists",
        "Run: mkdir _extended_demo"
    ))
    results.append(check(
        Path("core/monitoring").is_dir(),
        "Directory `core/monitoring/` exists",
        "Check git status — should exist in main branch"
    ))
    results.append(check(
        Path("scripts").is_dir(),
        "Directory `scripts/` exists",
        "Check git status"
    ))

    # 2. Required scripts
    print("[2/10] Checking required scripts...")
    required_scripts = [
        ("scripts/extended_demo_realtime.py", "Extended demo real-time harness"),
        ("scripts/extended_demo_report.py", "Report generator"),
    ]
    for script_path, desc in required_scripts:
        results.append(check(
            Path(script_path).is_file(),
            f"Script `{script_path}` ({desc}) exists",
            f"Check git status — {script_path} missing"
        ))

    # 3. Required monitoring modules
    print("[3/10] Checking monitoring modules...")
    required_modules = [
        ("core/monitoring/health.py", "HealthMonitor"),
        ("core/monitoring/telemetry.py", "Telemetry recorders"),
        ("core/monitoring/failure_classifier.py", "FailureClassifier"),
    ]
    for mod_path, desc in required_modules:
        results.append(check(
            Path(mod_path).is_file(),
            f"Module `{mod_path}` ({desc}) exists",
            f"Check git status — {mod_path} missing"
        ))

    # 4. Required telemetry recorders (verify classes inside telemetry.py)
    print("[4/10] Checking telemetry recorder classes...")
    try:
        sys.path.insert(0, ".")
        from core.monitoring.telemetry import TelemetryRecorder, GuardAuditRecorder, ExecutionAuditRecorder
        results.append(check(True, "TelemetryRecorder class exists", ""))
        results.append(check(True, "GuardAuditRecorder class exists", ""))
        results.append(check(True, "ExecutionAuditRecorder class exists", ""))
    except ImportError as e:
        results.append(check(False, f"Telemetry classes importable: {e}", "Check core/monitoring/telemetry.py"))
    except Exception as e:
        results.append(check(False, f"Telemetry classes error: {e}", "Investigate import error"))

    # 5. Required report generator
    print("[5/10] Checking report generator...")
    results.append(check(
        Path("scripts/extended_demo_report.py").is_file(),
        "Report generator script exists",
        "Check scripts/ directory"
    ))

    # 6. Tests pass check
    print("[6/10] Checking test status...")
    test_report = Path("_project-memory/operational_validation/test_reconciliation_report.md")
    results.append(check(
        test_report.is_file(),
        f"Test reconciliation report exists at {test_report}",
        "Run: python -m pytest tests/ -v --tb=no"
    ))
    if test_report.is_file():
        content = test_report.read_text()
        if "281 passed" in content and "0 failed" in content:
            results.append(check(True, "Test report confirms 281 passed, 0 failed", ""))
        else:
            results.append(check(False, "Test report does not show 281/0 status", "Re-run test suite"))

    # 7. Gate document
    print("[7/10] Checking gate documents...")
    gate_doc = Path("_project-memory/extended_demo/extended_demo_gate.md")
    results.append(check(
        gate_doc.is_file(),
        f"Gate document exists at {gate_doc}",
        "Check _project-memory/extended_demo/"
    ))

    # 8. .gitignore for runtime JSONL/logs
    print("[8/10] Checking .gitignore...")
    gitignore = Path(".gitignore")
    if gitignore.is_file():
        content = gitignore.read_text()
        has_jsonl = "_extended_demo/*.jsonl" in content or "_extended_demo/" in content
        has_logs = "logs/" in content
        results.append(check(has_jsonl, ".gitignore covers _extended_demo/*.jsonl", "Add `_extended_demo/*.jsonl` to .gitignore"))
        results.append(check(has_logs, ".gitignore covers logs/", "Add `logs/` to .gitignore"))
    else:
        results.append(check(False, ".gitignore file exists", "Create .gitignore"))

    # 9. Stale run_state conflict
    print("[9/10] Checking for stale run_state...")
    run_state = Path("_extended_demo/run_state.json")
    if run_state.is_file():
        try:
            data = json.loads(run_state.read_text())
            cycle_id = data.get("cycle_id", 0)
            if cycle_id > 0:
                results.append(check(
                    True,
                    f"Run state exists with cycle_id={cycle_id} — resume possible (use --resume)",
                    ""
                ))
            else:
                results.append(check(True, "Run state exists with 0 cycles — fresh start", ""))
        except (json.JSONDecodeError, Exception):
            results.append(check(False, "Run state exists but is corrupted", "Delete _extended_demo/run_state.json"))
    else:
        results.append(check(True, "No existing run_state — fresh start", ""))

    # 10. No real capital mode
    print("[10/10] Checking for real capital mode...")
    # Check env vars
    import os
    real_capital_env = os.environ.get("OSIRIS_REAL_CAPITAL", "false").lower()
    broker_key = os.environ.get("BINANCE_API_KEY", "")
    broker_secret = os.environ.get("BINANCE_API_SECRET", "")
    using_api_keys = bool(broker_key) and bool(broker_secret)

    results.append(check(
        real_capital_env != "true",
        f"OSIRIS_REAL_CAPITAL env var is '{real_capital_env}' (expected 'false')",
        "Unset OSIRIS_REAL_CAPITAL or set to 'false'"
    ))
    if using_api_keys:
        results.append(check(
            False,
            f"Binance API keys detected in environment — risk of real trading",
            "Unset BINANCE_API_KEY and BINANCE_API_SECRET for demo mode"
        ))
    else:
        results.append(check(
            True,
            "No Binance API keys in environment — safe for demo",
            ""
        ))

    # Summary
    print("\n" + "=" * 60)
    print("EXTENDED DEMO PRE-FLIGHT SUMMARY")
    print("=" * 60)

    passed = sum(1 for ok, _, _ in results if ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks passed")

    for ok, desc, hint in results:
        status = "✅" if ok else "❌"
        if not ok:
            failures += 1
        print(f"  {status}  {desc}")
        if not ok and hint:
            print(f"       Fix: {hint}")

    # Final verdict
    print("\n" + "-" * 60)
    if failures == 0 and warnings == 0:
        print("VERDICT: GO_FOR_7D_SMOKE")
        print(f"\nNext command:")
        print(f"  python scripts/extended_demo_realtime.py --smoke")
    elif failures > 0:
        print(f"VERDICT: NO_GO — {failures} check(s) failed")
    else:
        print("VERDICT: CONDITIONAL_GO — resolve warnings above")

    # Write report
    lines = []
    lines.append("# Extended Demo Pre-Flight Check Report")
    lines.append("")
    lines.append(f"Generated: 2026-06-23")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append(f"| # | Check | Status |")
    lines.append(f"|---|-------|--------|")
    for i, (ok, desc, _) in enumerate(results, 1):
        status = "✅ PASS" if ok else "❌ FAIL"
        lines.append(f"| {i} | {desc} | {status} |")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    if failures == 0 and warnings == 0:
        lines.append("**GO_FOR_7D_SMOKE**")
        lines.append("")
        lines.append("All checks pass. Ready for 7-day smoke run.")
    elif failures > 0:
        lines.append(f"**NO_GO** — {failures} check(s) must be resolved first")
        for desc, hint in [(desc, hint) for ok, desc, hint in results if not ok]:
            lines.append(f"")
            lines.append(f"- ❌ {desc}")
            if hint:
                lines.append(f"  Fix: {hint}")
    else:
        lines.append("**CONDITIONAL_GO**")
        lines.append("")
        lines.append("Resolve warnings before proceeding.")

    output_path = output_dir / "extended_demo_preflight.md"
    output_path.write_text("\n".join(lines) + "\n")
    print(f"\nReport written to {output_path}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
