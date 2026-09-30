"""Local ingress for provider adapters; no Binance credentials or networking."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.scientific.prospective_receipts import record,export_verified

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('record');a.add_argument('ledger',type=Path);a.add_argument('kind',choices=('bar','metric'));a.add_argument('--source',required=True)
    b=s.add_parser('export');b.add_argument('ledger',type=Path);b.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.command=='record':
        payload=json.load(sys.stdin);print(json.dumps(record(args.ledger,args.kind,payload,source=args.source)))
    else:print(json.dumps(export_verified(args.ledger,args.out)))
if __name__=='__main__':main()
