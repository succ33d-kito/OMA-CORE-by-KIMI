"""SEC discovery operator. Explicit activation, one poll, read-only status/inbox, manual admission."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
import json
from core.scientific.event_discovery import SourceDiscoveryAuthorityV1, inbox
from core.scientific.real_event_receipt import RealEventStore, AdmissionEvidence
from core.scientific.nuisance_pilot_contracts import DatasetRole
from core.scientific.nuisance_pilot_sampling import Relation, ShockEvidence


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    sub=parser.add_subparsers(dest='command',required=True)
    act=sub.add_parser('activate');act.add_argument('--operator-root',required=True)
    for name in ('poll','status','inbox'): sub.add_parser(name)
    admit=sub.add_parser('admit');admit.add_argument('--receipt-id',required=True);admit.add_argument('--evidence-json',required=True)
    args=parser.parse_args(argv)
    if args.command=='activate':
        result=SourceDiscoveryAuthorityV1.activate(args.root,args.operator_root,role=DatasetRole.PILOT).status()
    elif args.command=='inbox': result=inbox(args.root)
    else:
        authority=SourceDiscoveryAuthorityV1(args.root)
        if args.command=='poll': result=authority.poll()
        elif args.command=='status': result=authority.status()
        else:
            data=json.loads(Path(args.evidence_json).read_text(encoding='utf-8'))
            data['relation']=Relation(data['relation']);data['shock_evidence']=ShockEvidence(data['shock_evidence'])
            RealEventStore(authority.source_path).admit(args.receipt_id,AdmissionEvidence(**data))
            result=inbox(args.root)
    print(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=True))
    return result


if __name__=='__main__': main()
