"""Outcome-free 2024 data gate. Missing inputs/availability fail closed."""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.market_mechanics.microstructure import (
    VERSION, aggregate_archive, causal_derivatives, funding_asof, load_funding,
    sha256, verified_archive, migrate_v1_count_diagnostics,
)
from core.market_mechanics.reconciliation import reconcile_klines
from core.market_mechanics.state import build_market_state
from core.market_mechanics.regime import classify_regime

REPO = Path(__file__).resolve().parents[1]
GRID = pd.date_range('2024-01-01', '2025-01-01', freq='h', inclusive='left', tz='UTC')
METRICS = ['sum_open_interest', 'sum_open_interest_value',
           'count_toptrader_long_short_ratio', 'sum_toptrader_long_short_ratio',
           'count_long_short_ratio', 'sum_taker_long_short_vol_ratio']


def write_csv(frame, path):
    frame.to_csv(path, index=False, lineterminator='\n', float_format='%.15g')


def price_2024():
    """Read only official monthly 2024 OHLCV, no mixed-year source."""
    folder = REPO / 'research/metrics_2024_2025/official_2024'
    parts, sources = [], []
    for month in range(1, 13):
        path = folder / f'BTCUSDT-1h-2024-{month:02d}.zip'
        digest = verified_archive(path)
        with zipfile.ZipFile(path) as archive:
            with archive.open(archive.namelist()[0]) as handle:
                raw = pd.read_csv(handle)
        d = raw.iloc[:, :6].copy()
        d.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        d.time = pd.to_datetime(d.time, unit='ms', utc=True)
        parts.append(d)
        sources.append({'path': str(path.resolve()), 'sha256': digest})
    bars = pd.concat(parts, ignore_index=True)
    if len(bars) != 8784 or not (bars.time.array == GRID).all():
        raise ValueError('OHLCV must contain the exact ordered 8784 UTC hours')
    records = bars.to_dict('records')
    close = GRID[-1] + pd.Timedelta(hours=1)
    build_market_state('BTCUSDT', records, source_id='binance:um:official:2024', observed_at=close, as_of=close)
    return bars, sources


def metrics_2024(root):
    parts, sources = [], []
    for n in range(366):
        day = date(2024, 1, 1) + timedelta(days=n)
        path = root / 'metrics' / f'BTCUSDT-metrics-{day}.zip'
        digest = verified_archive(path)
        with zipfile.ZipFile(path) as archive:
            with archive.open(archive.namelist()[0]) as handle:
                d = pd.read_csv(handle)
        if 'symbol' in d and not d.symbol.eq('BTCUSDT').all():
            raise ValueError('metrics instrument mismatch')
        t = pd.to_datetime(d.create_time, utc=True)
        if not t.dt.date.eq(day).all():
            raise ValueError('metrics outside source day')
        v = d[METRICS].astype(float)
        if np.isinf(v.to_numpy()).any() or (v < 0).any().any():
            raise ValueError('invalid metrics values')
        v['metric_observed_at'] = t
        parts.append(v)
        sources.append({'path': str(path.resolve()), 'sha256': digest,
                        'raw_ordered': bool(t.is_monotonic_increasing)})
    all_rows = pd.concat(parts, ignore_index=True)
    t = all_rows.metric_observed_at
    if t.duplicated().any():
        raise ValueError('duplicate primary metrics')
    # Official files can contain shuffled rows. Canonical ordering does not
    # change values or fill observations; raw-order anomalies stay in manifests.
    all_rows = all_rows.sort_values('metric_observed_at', kind='stable').reset_index(drop=True)
    t = all_rows.metric_observed_at
    all_rows['time'] = t.dt.floor('h')
    hourly = all_rows.groupby('time', sort=True).tail(1).copy()
    hourly['metric_available_at'] = pd.NaT
    hourly['metric_availability_status'] = 'unknown_historical_receipt'
    return hourly, sources


def run(root, output, *, reduce=True):
    output.mkdir(parents=True, exist_ok=True)
    sources, issues, artifacts = [], ['PRICE_HISTORICAL_AVAILABILITY_UNKNOWN'], []
    panel, prices = price_2024()
    sources.extend(prices)
    panel['decision_at'] = panel.time + pd.Timedelta(hours=1)
    panel['price_available_at'] = pd.NaT
    records = panel[['time', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
    regimes = [None] * 80
    for i in range(80, len(records)):
        at = panel.decision_at.iloc[i]
        state = build_market_state('BTCUSDT', records[i-80:i+1], source_id='binance:um:2024', observed_at=at, as_of=at)
        regime = classify_regime(state)
        regimes.append(f'{regime.structure}_{regime.direction}_{regime.volatility}')
    panel['regime'] = regimes
    try:
        funding_paths = [root / 'fundingRate' / f'BTCUSDT-fundingRate-2024-{m:02d}.zip' for m in range(1, 13)]
        funding, funding_sources = load_funding(funding_paths)
        if not funding.funding_at.dt.year.eq(2024).all():
            raise ValueError('funding outside discovery year')
        write_csv(funding, output / 'funding_2024.csv')
        sources.extend({'path': str(p.resolve()), 'sha256': s['sha256']} for p, s in zip(funding_paths, funding_sources))
        panel['funding_rate_known'] = funding_asof(panel.decision_at, funding).to_numpy()
        funding_report = {'rows': len(funding), 'first': str(funding.funding_at.iloc[0]),
                          'last': str(funding.funding_at.iloc[-1]),
                          'missing_available_at': int(funding.available_at.isna().sum())}
        if funding.available_at.isna().any():
            issues.append('FUNDING_HISTORICAL_AVAILABILITY_UNKNOWN')
    except (ValueError, FileNotFoundError) as error:
        funding_report = {'error': str(error)}
        issues.append('FUNDING_INPUT_INCOMPLETE_OR_INVALID')
        panel['funding_rate_known'] = np.nan
    try:
        metrics, metric_sources = metrics_2024(root)
        panel = panel.merge(metrics, on='time', how='left', validate='one_to_one')
        sources.extend(metric_sources)
        panel['oi_change_1h'] = panel.sum_open_interest.diff()
        if panel[METRICS].isna().any().any():
            issues.append('METRICS_MISSING_VALUES')
        issues.append('METRICS_HISTORICAL_AVAILABILITY_UNKNOWN')
        metric_report = {'archives': 366, 'hourly_rows': len(metrics),
                         'raw_unordered_archives': sum(not x['raw_ordered'] for x in metric_sources),
                         'unknown_values_by_field': panel[METRICS].isna().sum().to_dict()}
    except (ValueError, FileNotFoundError) as error:
        issues.append('PRIMARY_METRICS_INCOMPLETE_OR_INVALID')
        metric_report = {'error': str(error)}
    monthly, agg_report = [], []
    for month in range(1, 13):
        archive = root / 'aggTrades' / f'BTCUSDT-aggTrades-2024-{month:02d}.zip'
        cached = output / f'aggtrades_2024_{month:02d}.csv'
        audit_path = output / f'aggtrades_2024_{month:02d}.json'
        if not archive.exists():
            agg_report.append({'month': month, 'status': 'MISSING_VERIFIED_ARCHIVE'})
            continue
        start = pd.Timestamp(year=2024, month=month, day=1, tz='UTC')
        end = start + pd.offsets.MonthBegin(1)
        try:
            if cached.exists() and audit_path.exists():
                audit = json.loads(audit_path.read_text())
                if audit['source_sha256'] != verified_archive(archive) or audit['output_sha256'] != sha256(cached):
                    raise ValueError('aggregate cache identity mismatch')
                data = pd.read_csv(cached, parse_dates=['time'])
                if audit['version'] == 'mechanics-v2-observations-1':
                    data = migrate_v1_count_diagnostics(data)
                    audit['migration'] = {'from_version': audit['version'],
                                          'previous_output_sha256': audit['output_sha256'],
                                          'change': 'ID span diagnostic only; remove unsupported individual trade estimators'}
                    audit['version'] = VERSION
                    write_csv(data, cached)
                    audit['output_sha256'] = sha256(cached)
                    audit_path.write_text(json.dumps(audit, indent=2) + '\n')
                elif audit['version'] != VERSION:
                    raise ValueError('aggregate cache version mismatch')
            elif reduce:
                data, audit = aggregate_archive(archive, start, end)
                write_csv(data, cached)
                audit['output_sha256'] = sha256(cached)
                audit_path.write_text(json.dumps(audit, indent=2) + '\n')
            else:
                agg_report.append({'month': month, 'status': 'NOT_REDUCED'})
                continue
            klines_path = REPO / f'research/metrics_2024_2025/official_2024/BTCUSDT-1h-2024-{month:02d}.zip'
            with zipfile.ZipFile(klines_path) as z:
                with z.open(z.namelist()[0]) as f:
                    reconciliation = reconcile_klines(data, pd.read_csv(f))
            audit['reconciliation'] = reconciliation
            if reconciliation['status'] != 'PASS':
                issues.append('AGGTRADES_KLINES_RECONCILIATION_FAILED')
            monthly.append(data)
            sources.append({'path': str(archive.resolve()), 'sha256': audit['source_sha256']})
            agg_report.append({'month': month, 'status': 'REDUCED', **audit})
            print(f'aggTrades month {month}: {audit["rows"]} rows', flush=True)
        except (ValueError, KeyError) as error:
            agg_report.append({'month': month, 'status': 'INVALID', 'error': str(error)})
    if len(monthly) != 12:
        issues.append('AGGTRADES_YEAR_INCOMPLETE')
    if monthly:
        all_agg = causal_derivatives(pd.concat(monthly, ignore_index=True))
        panel = panel.merge(all_agg, on='time', how='left', validate='one_to_one')
        if panel.aggressive_buy_volume.isna().any():
            issues.append('AGGTRADES_UNKNOWN_HOURS')
        if any(x.get('missing_aggregate_ids', 0) for x in agg_report):
            issues.append('AGGTRADES_ID_GAPS')
        reduced = [x for x in agg_report if x['status'] == 'REDUCED']
        if any(b['first_id'] != a['last_id'] + 1 for a, b in zip(reduced, reduced[1:])):
            issues.append('AGGTRADES_CROSS_MONTH_ID_GAPS')
        issues.append('AGGTRADES_HISTORICAL_AVAILABILITY_UNKNOWN')
    else:
        panel['aggressor_imbalance'] = np.nan
    write_csv(panel, output / 'observations_2024.csv')
    for path in sorted(output.glob('*.csv')):
        artifacts.append({'path': str(path.resolve()), 'sha256': sha256(path)})
    report = {'version': VERSION, 'status': 'FAIL' if issues else 'PASS',
              'outcome_testing_allowed': not issues, 'issues': sorted(set(issues)),
              'expected_hours': 8784, 'price_hours': len(panel),
              'first_hour_utc': str(panel.time.iloc[0]), 'last_hour_utc': str(panel.time.iloc[-1]),
              'regime_warmup_unknown_hours': int(panel.regime.isna().sum()),
              'funding': funding_report, 'metrics': metric_report, 'aggtrades': agg_report,
              'sources': sources, 'artifacts': artifacts,
              'code_sha256': {str(p.relative_to(REPO)): sha256(p) for p in
                  [Path(__file__), REPO / 'core/market_mechanics/microstructure.py',
                   REPO / 'core/market_mechanics/regime.py', REPO / 'core/market_mechanics/state.py',
                   REPO / 'core/market_mechanics/reconciliation.py']},
              'holdouts': {'Binance_2025': 'NO_NEW_OUTCOME_ANALYSIS_LEGACY_MIXED_YEAR_FIXTURE_READ_BY_TESTS_AND_NOW_REMOVED',
                           'Kraken_Q2_2026': 'NOT_OPENED_THIS_SPRINT_PRIOR_ARTIFACTS_EXIST'},
              'promotion': 'NONE', 'outcomes_computed': False}
    (output / 'DATA_GATE.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['status', 'issues', 'price_hours', 'outcomes_computed']}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=REPO / 'research/edge_discovery/mechanics_v2')
    parser.add_argument('--no-reduce', action='store_true')
    args = parser.parse_args()
    run(args.root, args.out, reduce=not args.no_reduce)
