"""Explicit read-only ledger reconstruction with exclusive certificate export."""
import argparse
from datetime import datetime
import os
from pathlib import Path
import sys

REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0,str(REPO_ROOT))
from core.scientific.replay_reconciliation import reconcile_causal_replay


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger',required=True)
    parser.add_argument('--instrument',required=True)
    parser.add_argument('--as-of',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--feature',action='append')
    parser.add_argument('--role',choices=('PILOT','DISCOVERY','CONFIRMATION'))
    args=parser.parse_args(argv)
    ledger=Path(args.ledger).resolve(strict=True)
    output=Path(args.output)
    if not ledger.is_file(): raise ValueError('existing ledger file required')
    if output.exists() or output.is_symlink(): raise FileExistsError('output already exists')
    if not output.parent.is_dir(): raise ValueError('existing output parent required')
    cutoff=datetime.fromisoformat(args.as_of.replace('Z','+00:00'))
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError('aware cutoff required')
    kwargs={} if args.feature is None else {'features':tuple(args.feature)}
    result=reconcile_causal_replay(ledger,instrument=args.instrument,as_of=cutoff,dataset_role=args.role,**kwargs)
    # Exclusive creation protects existing evidence; interrupted writes remain
    # visibly incomplete JSON and must never be interpreted as certificates.
    with output.open('xb') as handle:
        handle.write(result.canonical_json.encode('utf-8'))
        handle.flush()
        os.fsync(handle.fileno())
    print(result.status+' '+result.reconciliation_id)
    return 0 if result.status=='MATCH' else 2


if __name__=='__main__':
    raise SystemExit(main())
