#!/usr/bin/env python3
"""
check_oma_launcher.py — Diagnostic script for OMA launcher alignment.

Prints:
  - current repo path
  - `which oma`
  - target PROJECT inside launcher
  - whether target matches current repo
  - whether .venv exists
  - whether python path is valid
  - whether TelegramNotifier comes from current repo
  - recommendation
"""

import os
import shutil
import subprocess
import sys


def get_expected_repo() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_which_oma() -> str:
    result = shutil.which("oma")
    if result is None:
        return "NOT FOUND"
    return result


def parse_launcher_project(launcher_path: str) -> str:
    """Parse PROJECT= line from a launcher script."""
    if not os.path.exists(launcher_path):
        return "N/A (not found)"
    try:
        with open(launcher_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("PROJECT="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception as e:
        return f"Error: {e}"
    return "PROJECT= not found"


def check_python_valid() -> bool:
    try:
        import core
        return True
    except ImportError:
        return False


def check_telegram_from_current_repo() -> bool:
    try:
        from core.engines import telegram_notifier as tn
        mod_path = getattr(tn, "__file__", "")
        expected = get_expected_repo()
        return expected in mod_path
    except Exception:
        return False


def main():
    expected = get_expected_repo()
    which_oma = get_which_oma()
    launcher_project = parse_launcher_project(which_oma) if which_oma != "NOT FOUND" else "N/A"
    has_venv = os.path.isdir(os.path.join(expected, ".venv")) or os.path.isdir(os.path.join(expected, "venv"))
    python_valid = check_python_valid()
    telegram_ok = check_telegram_from_current_repo()

    mismatch = (launcher_project != "N/A" and launcher_project != "PROJECT= not found"
                and os.path.abspath(launcher_project) != expected)

    print("=" * 60)
    print("  O.M.A.-C.O.R.E. Launcher Diagnostic")
    print("=" * 60)
    print()
    print(f"  Current repo (expected):  {expected}")
    print(f"  which oma:                {which_oma}")
    print(f"  Launcher PROJECT=:        {launcher_project}")
    print(f"  Match:                    {'✓ YES' if not mismatch else '✗ MISMATCH'}")
    print(f"  .venv exists:             {'✓' if has_venv else '✗'} ")
    print(f"  Python import valid:      {'✓' if python_valid else '✗'}")
    print(f"  Telegram from repo:       {'✓' if telegram_ok else '✗'}")
    print()

    recommendations = []
    if mismatch:
        recommendations.append(
            f"Run: sudo bash scripts/install_local_oma_launcher.sh\n"
            f"  This will backup and rewrite {which_oma} to point to {expected}."
        )
    if not has_venv:
        recommendations.append("Create a virtual environment: python3 -m venv .venv && pip install -r requirements.txt")
    if not python_valid:
        recommendations.append("Install dependencies: pip install -r requirements.txt")
    if not telegram_ok:
        recommendations.append("Ensure core/engines/telegram_notifier.py exists and is importable.")

    if recommendations:
        print("  Recommendations:")
        for r in recommendations:
            for line in r.split("\n"):
                print(f"    {line}")
        print()

    if mismatch:
        print("  STATUS: LAUNCHER MISALIGNED — `oma run` may execute different code.")
        print("  Run the install script above to fix.")
    else:
        print("  STATUS: OK — launcher is correctly aligned.")

    print("=" * 60)

    return 1 if mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
