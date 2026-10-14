"""Explicit prospective admission operator; no HTTP or source retry."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse
import json
from core.scientific.metrics_admission_operator import MetricsAdmissionAuthorityV1


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('activate');a.add_argument('--capture-root',required=True)
    for name in ('once','status','inventory'): sub.add_parser(name)
    args=p.parse_args(argv)
    if args.command=='activate':
        result=MetricsAdmissionAuthorityV1.activate(args.root,args.capture_root).body
    else:
        a=MetricsAdmissionAuthorityV1(args.root)
        result=getattr(a,args.command)()
    print(json.dumps(result,sort_keys=True,indent=2))
    if args.command=='once' and any(x['status'] not in ('ADMITTED','ALREADY_ADMITTED') for x in result['results']):
        return 1
    return 0


if __name__=='__main__': raise SystemExit(main())
