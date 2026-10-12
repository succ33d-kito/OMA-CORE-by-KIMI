"""Print read-only evidence coverage; no initialization, network or exports."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
import json
from datetime import datetime, timezone
from core.scientific.experiment51_readiness import check_readiness


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('price-state','metrics-state','funding-state'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    result = check_readiness(**vars(args), repo_root=Path(__file__).resolve().parents[1], checked_at=datetime.now(timezone.utc))
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
