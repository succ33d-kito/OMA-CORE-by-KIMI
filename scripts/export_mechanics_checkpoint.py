"""Export portable provenance for 2024 observations, without raw data or outcomes."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.market_mechanics.microstructure import sha256

REPO = Path(__file__).resolve().parents[1]


def export(root, output):
    root, output = root.resolve(), output.resolve()
    report = json.loads((output / 'DATA_GATE.json').read_text(encoding='utf-8'))
    # Never reclassify this report's scientific permission while exporting it.
    for item in report['artifacts']:
        if sha256(item['path']) != item['sha256']:
            raise ValueError('observation artifact changed since Data Gate')
    for group in ['sources', 'artifacts']:
        for item in report[group]:
            path = Path(item.pop('path')).resolve()
            if path.is_relative_to(root):
                item['root'] = 'external_2024_data'
                item['relative_path'] = path.relative_to(root).as_posix()
            elif path.is_relative_to(REPO):
                item['root'] = 'repository'
                item['relative_path'] = path.relative_to(REPO).as_posix()
            else:
                raise ValueError('unregistered manifest root')
    receipts = []
    for kind in ['aggTrades', 'metrics', 'fundingRate']:
        for path in sorted((root / kind).glob('*.receipt.json')):
            receipt = json.loads(path.read_text(encoding='utf-8'))
            if '/BTCUSDT/' not in receipt['url'] or '-2024-' not in receipt['url']:
                raise ValueError('unexpected source outside discovery')
            receipts.append(receipt)
    report['primary_receipts'] = receipts
    report['root_mapping'] = {'repository': 'Git checkout root', 'external_2024_data': 'Value passed to --root, outside Git'}
    report['exporter_sha256'] = sha256(Path(__file__))
    report['reproduction_scripts_sha256'] = {name: sha256(REPO / 'scripts' / name) for name in
        ['download_mechanics_v2.py', 'mechanics_v2_pilot.py', 'mechanics_v2_data_gate.py']}
    report['external_archive_bytes'] = sum(x['bytes'] for x in receipts)
    (output / 'PORTABLE_MANIFEST.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return {'receipts': len(receipts), 'external_archive_bytes': report['external_archive_bytes'], 'status': report['status']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--out', type=Path, default=REPO / 'research/edge_discovery/mechanics_v2')
    args = p.parse_args()
    print(json.dumps(export(args.root, args.out)))
