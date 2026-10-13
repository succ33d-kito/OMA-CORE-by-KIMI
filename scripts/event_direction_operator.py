"""Prospective EventDirection operator: explicit assertions only; no capture/outcomes."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
import json
from dataclasses import asdict
from enum import Enum
from datetime import datetime
from core.scientific import event_direction_operator as operator
from core.scientific.event_direction_v1 import ClassAssertion, EventClass
from core.scientific.nuisance_pilot_contracts import DatasetRole


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--role', required=True, choices=[r.value for r in DatasetRole])
    sub = parser.add_subparsers(dest='command', required=True)
    activation = sub.add_parser('activate'); activation.add_argument('--event-journal', required=True)
    attestation = sub.add_parser('attest')
    attestation.add_argument('--receipt-id', required=True)
    attestation.add_argument('--assertion-json', required=True)
    for name in ('status', 'bind'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--controls-json', required=name == 'bind')
        cmd.add_argument('--price-ledger')
    args = parser.parse_args(argv); role = DatasetRole(args.role)
    if args.command == 'activate':
        result = operator.activate(args.root, args.event_journal, role=role)
    elif args.command == 'attest':
        data = json.loads(Path(args.assertion_json).read_text(encoding='utf-8'))
        data['event_class'] = EventClass(data['event_class'])
        record = operator.attest(args.root, args.receipt_id, ClassAssertion(**data), role=role)
        result = dict(asdict(record), record_id=record.record_id)
    else:
        controls = operator.controls_from_json(args.controls_json) if args.controls_json else None
        if args.command == 'status':
            result = operator.inspect(args.root, role=role, controls=controls, price_ledger=args.price_ledger)
        else:
            result = json.loads(operator.bind(args.root, controls, role=role, price_ledger=args.price_ledger).to_json())
    def encode(value):
        if isinstance(value, Enum): return value.value
        if isinstance(value, datetime): return value.isoformat()
        raise TypeError('unsupported output')
    print(json.dumps(result, default=encode, sort_keys=True, indent=2, allow_nan=False))
    return result


if __name__ == '__main__':
    main()
