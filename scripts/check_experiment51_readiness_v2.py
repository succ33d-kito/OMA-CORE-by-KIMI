"""Read-only Experiment 51 phase and capture readiness; no execution command."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse,json
from datetime import datetime,timezone
from core.scientific.experiment51_readiness_v2 import check
from core.scientific.event_direction_operator import controls_from_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('event-root','price-state','metrics-state','funding-state'):
        parser.add_argument('--'+key,required=True)
    parser.add_argument('--phase-path');parser.add_argument('--controls-json')
    args=vars(parser.parse_args());source=args.pop('controls_json')
    result=check(**args,controls=controls_from_json(source) if source else None,
                 repo_root=Path(__file__).resolve().parents[1],checked_at=datetime.now(timezone.utc))
    print(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))


if __name__=='__main__': main()
