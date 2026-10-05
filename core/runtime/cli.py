"""Read-only CLI, independent from legacy runtime construction."""
import argparse
from datetime import datetime, timezone
import json
import os
from .snapshot import load_config, build_system_snapshot


def human(snapshot):
    data=snapshot.to_dict()
    rows=[f"OMA-CORE | node={data['node']['node_id']} | mode={data['mode']}",
          f"snapshot_at={data['snapshot_at']}",f"runtime={data['node']['runtime_state']}"]
    for source in data['sources']:
        rows.append(f"{source['name']}: {source['state'].value} | freshness={source['freshness']} | source_at={source['source_at'] or 'UNKNOWN'} | {source['reason']}")
        if source['details']: rows.append(json.dumps(source['details'],sort_keys=True,ensure_ascii=False))
    rows.extend(['NO EXECUTION EVIDENCE','NO FACTUAL OPEN POSITION EVIDENCE',
        'EDGE=NOT DEMONSTRATED | REGIME=NOT VALIDATED | MECHANICS=NOT VALIDATED | POLICY WINNER=NONE',
        '81H_INPUT_READINESS='+str(data['science']['price_pit']['details']['81h_input_readiness'] if data['science']['price_pit']['details']['81h_input_readiness'] is not None else 'UNKNOWN'),
        'Confirmation=UNKNOWN_NOT_INSPECTED'])
    return '\n'.join(rows)


def main(argv=None):
    parser=argparse.ArgumentParser(prog='oma system')
    parser.add_argument('command',choices=['status'])
    parser.add_argument('--config',default=os.environ.get('OMA_RUNTIME_CONFIG'))
    parser.add_argument('--json',action='store_true')
    parser.add_argument('--at',help='Explicit aware snapshot timestamp; default now UTC')
    args=parser.parse_args(argv)
    try:
        snapshot=build_system_snapshot(load_config(args.config),snapshot_at=args.at or datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        print(json.dumps(dict(status='INVALID',reason='RUNTIME_CONFIGURATION_ERROR',error_type=type(exc).__name__)))
        return 2
    print(json.dumps(snapshot.to_dict(),sort_keys=True,ensure_ascii=False) if args.json else human(snapshot))
    return 0


if __name__=='__main__': raise SystemExit(main())
