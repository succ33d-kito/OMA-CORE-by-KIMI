"""Download only BTCUSDT USD-M 2024 primary archives; never read holdouts.

Verified objects are immutable locally. Interrupted downloads resume with HTTP
Range only when the server explicitly accepts the requested range.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import time

import requests

BASE = 'https://data.binance.vision/data/futures/um/monthly'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def acquire(root, kind, month):
    if kind == 'metrics' or (kind == 'aggTrades' and isinstance(month, str)):
        day = date.fromisoformat(str(month))
        if day.year != 2024:
            raise ValueError('Only 2024 discovery inputs are allowed')
        period, base = day.isoformat(), BASE.replace('/monthly', '/daily')
    elif kind in ('fundingRate', 'aggTrades') and month in range(1, 13):
        period, base = f'2024-{month:02d}', BASE
    else:
        raise ValueError('Only the registered 2024 discovery inputs are allowed')
    folder = root / kind
    folder.mkdir(parents=True, exist_ok=True)
    name = f'BTCUSDT-{kind}-{period}.zip'
    url = f'{base}/{kind}/BTCUSDT/{name}'
    target = folder / name
    checksum = folder / (name + '.CHECKSUM')
    receipt = folder / (name + '.receipt.json')
    with requests.Session() as session:
        if not checksum.exists():
            response = session.get(url + '.CHECKSUM', timeout=(20, 60))
            response.raise_for_status()
            checksum.write_bytes(response.content)
        fields = checksum.read_text().split()
        expected = fields[0]
        if len(expected) != 64 or any(c not in '0123456789abcdefABCDEF' for c in expected):
            raise ValueError('Malformed checksum')
        if len(fields) < 2 or fields[1].lstrip('*') != name:
            raise ValueError('Checksum filename mismatch')
        if target.exists():
            if sha(target) != expected.lower():
                raise ValueError(f'Existing archive conflicts with checksum: {target}')
        else:
            partial = folder / (name + '.part')
            info = session.head(url, timeout=(20, 60))
            info.raise_for_status()
            size = int(info.headers['Content-Length'])
            # Bounded ranges avoid intermediaries buffering a 500+ MB response.
            while not partial.exists() or partial.stat().st_size < size:
                offset = partial.stat().st_size if partial.exists() else 0
                end = min(offset + 8 * 1024 * 1024, size) - 1
                for attempt in range(5):
                    try:
                        response = session.get(url, headers={'Range': f'bytes={offset}-{end}'}, timeout=(20, 60))
                        response.raise_for_status()
                        if response.status_code == 206:
                            if response.headers.get('Content-Range') != f'bytes {offset}-{end}/{size}':
                                raise ValueError('Invalid range response')
                        elif not (response.status_code == 200 and offset == 0 and end == size - 1):
                            raise ValueError('Server did not honor bounded range')
                        if len(response.content) != end - offset + 1:
                            raise ValueError('Incomplete range')
                        with partial.open('ab') as f:
                            f.write(response.content)
                        break
                    except requests.RequestException:
                        if attempt == 4:
                            raise
                        time.sleep(2 ** attempt)
            if sha(partial) != expected.lower():
                raise ValueError(f'Archive checksum failure: {partial}')
            partial.replace(target)
    result = {'url': url, 'checksum_url': url + '.CHECKSUM', 'sha256': expected.lower(),
              'bytes': target.stat().st_size, 'status': 'CHECKSUM_VERIFIED',
              'retrieved_at': datetime.now(timezone.utc).isoformat(),
              'historical_available_at': None,
              'availability_note': 'Archive retrieval is not original market-time receipt.'}
    if not receipt.exists():
        receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    else:
        result = json.loads(receipt.read_text(encoding='utf-8'))
    print(json.dumps({'archive': name, 'bytes': result['bytes'], 'status': result['status']}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--kind', choices=['fundingRate', 'aggTrades', 'metrics', 'all'], default='all')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--pilot-day', choices=['2024-01-01'], help='Predetermined parser pilot, not full-year coverage')
    args = parser.parse_args()
    kinds = ['fundingRate', 'aggTrades', 'metrics'] if args.kind == 'all' else [args.kind]
    jobs = [(kind, period) for kind in kinds for period in
            ([date(2024, 1, 1) + timedelta(days=n) for n in range(366)] if kind == 'metrics' else range(1, 13))]
    if args.pilot_day:
        if args.kind != 'aggTrades':
            parser.error('--pilot-day requires --kind aggTrades')
        jobs = [('aggTrades', args.pilot_day)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda job: acquire(args.root, *job), jobs))
    suffix = '_pilot' if args.pilot_day else ''
    (args.root / f'{args.kind}{suffix}_download_manifest.json').write_text(
        json.dumps(results, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
