"""Reproduce the fixed 2024-01-01 pilot, without reading any outcomes."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.market_mechanics.microstructure import aggregate_archive, sha256
from scripts.mechanics_v2_data_gate import write_csv, REPO


def run(root, output):
    output.mkdir(parents=True, exist_ok=True)
    data, audit = aggregate_archive(root / 'aggTrades/BTCUSDT-aggTrades-2024-01-01.zip',
                                    pd.Timestamp('2024-01-01', tz='UTC'), pd.Timestamp('2024-01-02', tz='UTC'))
    target = output / 'pilot_2024_01_01.csv'
    write_csv(data, target)
    audit['output_sha256'] = sha256(target)
    audit['pilot_script_sha256'] = sha256(Path(__file__))
    (output / 'PILOT.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    monthly = output / 'aggtrades_2024_01.csv'
    if monthly.exists():
        a, b = pd.read_csv(monthly).iloc[:24], pd.read_csv(target)
        fields = ['aggressive_buy_volume', 'aggressive_sell_volume', 'aggregate_trade_count',
                  'underlying_id_span_count', 'quote_volume']
        matches = {k: bool(np.allclose(a[k], b[k], rtol=1e-12, atol=1e-6)) for k in fields}
        same_hours = a.time.tolist() == b.time.tolist()
        report = {'pilot_day': '2024-01-01', 'status': 'PASS' if same_hours and all(matches.values()) else 'FAIL',
                  'same_hours': same_hours, 'field_matches': matches,
                  'note': 'Daily vs monthly sources; not a proof of equality to the kline trade universe.'}
        (output / 'PILOT_MONTH_RECONCILIATION.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        if report['status'] != 'PASS':
            raise ValueError('daily/monthly pilot reconciliation failed')
    return audit


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--out', type=Path, default=REPO / 'research/edge_discovery/mechanics_v2')
    args = p.parse_args()
    print(json.dumps(run(args.root, args.out)))
