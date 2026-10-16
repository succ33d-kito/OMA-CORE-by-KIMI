"""Prospective Regime derived-snapshot producer boundary. No catch-up, no repair.

One invocation checks the single current prospective candidate slot and writes a
Regime snapshot only if an exactly-81-slot role-authenticated contiguous window
naturally exists. Before that it writes nothing and reports the exact reason.
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.scientific.regime_derived_operator import RegimeDerivedOperatorV1, main as _main  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, help='Price role state root')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('once')
    commands.add_parser('status')
    args = parser.parse_args(argv)
    return _main(args.root, command=args.command)


if __name__ == '__main__':
    raise SystemExit(main())
