"""Historical observations, not participant identities or causal identification.

All intervals are [open, close). Unknown receipt times remain unknown. Neither
archive timestamps nor checksums prove when a trading system could see a value.
"""
from pathlib import Path
import hashlib
import json
import zipfile

import numpy as np
import pandas as pd

VERSION = 'mechanics-v2-observations-2'
AGG_COLUMNS = ['agg_trade_id', 'price', 'quantity', 'first_trade_id',
               'last_trade_id', 'transact_time', 'is_buyer_maker']


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verified_archive(path):
    path = Path(path)
    fields = Path(str(path) + '.CHECKSUM').read_text().split()
    if len(fields) != 2 or fields[1].lstrip('*') != path.name:
        raise ValueError('checksum identity mismatch')
    digest = sha256(path)
    if fields[0].lower() != digest:
        raise ValueError('checksum mismatch')
    return digest


def aggregate_chunks(chunks, start, end):
    """Stream validated aggTrade rows into hourly sufficient statistics.

    underlying_id_span_count is diagnostic, NOT an exact trade count.
    aggregate_trade_count counts archive rows; intensity/mean size refer only
    to these directly observed aggregates, never an inferred individual count.
    ID gaps are reported and block completeness rather than filled synthetically.
    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError('aware ordered bounds required')
    pieces = []
    last_id = last_time = None
    rows = gaps = 0
    first_id = first_time = None
    for chunk in chunks:
        chunk = chunk.rename(columns={'aggregate_trade_id': 'agg_trade_id'})
        if list(chunk.columns) != AGG_COLUMNS:
            raise ValueError('unexpected aggTrades schema')
        if chunk.empty:
            continue
        ints = {}
        for col in ['agg_trade_id', 'first_trade_id', 'last_trade_id', 'transact_time']:
            numeric = pd.to_numeric(chunk[col], errors='raise')
            if numeric.isna().any() or (numeric < 0).any() or (numeric % 1 != 0).any():
                raise ValueError('invalid integer ID/timestamp')
            ints[col] = numeric.to_numpy(dtype=np.int64)
        ids, times = ints['agg_trade_id'], ints['transact_time']
        if np.any(np.diff(ids) <= 0) or (last_id is not None and ids[0] <= last_id):
            raise ValueError('duplicate or unordered aggregate IDs')
        if np.any(np.diff(times) < 0) or (last_time is not None and times[0] < last_time):
            raise ValueError('unordered trade timestamps')
        gaps += int(np.maximum(np.diff(ids) - 1, 0).sum())
        if last_id is not None:
            gaps += max(0, int(ids[0]) - last_id - 1)
        t = pd.to_datetime(times, unit='ms', utc=True)
        if (t < start).any() or (t >= end).any():
            raise ValueError('trades outside registered interval / unclosed interval')
        price = pd.to_numeric(chunk.price, errors='raise').to_numpy(float)
        quantity = pd.to_numeric(chunk.quantity, errors='raise').to_numpy(float)
        if not np.isfinite(price).all() or not np.isfinite(quantity).all() or np.any(price <= 0) or np.any(quantity <= 0):
            raise ValueError('invalid trade price/quantity')
        maker = chunk.is_buyer_maker.astype(str).str.lower()
        if not maker.isin(['true', 'false']).all():
            raise ValueError('invalid isBuyerMaker; refusing truthiness conversion')
        count = ints['last_trade_id'] - ints['first_trade_id'] + 1
        if np.any(count <= 0):
            raise ValueError('invalid underlying trade span')
        buy = maker.eq('false').to_numpy()
        frame = pd.DataFrame({'time': t.floor('h'),
                              'aggressive_buy_volume': np.where(buy, quantity, 0.),
                              'aggressive_sell_volume': np.where(buy, 0., quantity),
                              'quote_volume': price * quantity,
                              'underlying_id_span_count': count, 'aggregate_trade_count': 1})
        pieces.append(frame.groupby('time', sort=True).sum())
        if first_id is None:
            first_id, first_time = int(ids[0]), int(times[0])
        last_id, last_time = int(ids[-1]), int(times[-1])
        rows += len(chunk)
    if not pieces:
        raise ValueError('empty aggTrades source')
    totals = pd.concat(pieces).groupby(level=0, sort=True).sum()
    grid = pd.date_range(start, end, freq='h', inclusive='left')
    totals = totals.reindex(grid)
    totals.index.name = 'time'
    totals['coverage_status'] = np.where(totals.aggregate_trade_count.notna(), 'observed', 'unknown')
    volume = totals.aggressive_buy_volume + totals.aggressive_sell_volume
    totals['signed_volume'] = totals.aggressive_buy_volume - totals.aggressive_sell_volume
    totals['aggressor_imbalance'] = totals.signed_volume / volume
    totals['aggregate_intensity_per_second'] = totals.aggregate_trade_count / 3600.
    totals['mean_aggregate_size'] = volume / totals.aggregate_trade_count
    totals['bar_closed_at'] = totals.index + pd.Timedelta(hours=1)
    totals['available_at'] = pd.NaT
    totals['availability_status'] = 'unknown_historical_receipt'
    return totals.reset_index(), {'rows': rows, 'first_id': first_id, 'last_id': last_id,
                                  'first_transact_ms': first_time, 'last_transact_ms': last_time,
                                  'missing_aggregate_ids': gaps,
                                  'unknown_hours': int(totals.aggregate_trade_count.isna().sum())}


def aggregate_archive(path, start, end, chunksize=500_000):
    digest = verified_archive(path)
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        if len(members) != 1 or not members[0].endswith('.csv'):
            raise ValueError('expected exactly one CSV')
        with archive.open(members[0]) as handle:
            result, audit = aggregate_chunks(pd.read_csv(handle, chunksize=chunksize), start, end)
    audit.update({'source_sha256': digest, 'version': VERSION})
    return result, audit


def causal_derivatives(hourly):
    """Reindex first: a missing hour must break differences and rolling history."""
    d = hourly.copy()
    t = pd.to_datetime(d.time, utc=True)
    if t.duplicated().any() or not t.is_monotonic_increasing:
        raise ValueError('ordered unique hours required')
    d.index = t
    d = d.drop(columns='time').reindex(pd.date_range(t.iloc[0], t.iloc[-1], freq='h'))
    volume = d.aggressive_buy_volume + d.aggressive_sell_volume
    d['imbalance_change_1h'] = d.aggressor_imbalance.diff()
    d['volume_change_1h'] = volume.diff()
    d['volume_vs_prior_24h'] = volume / volume.shift(1).rolling(24, min_periods=24).mean()
    d.index.name = 'time'
    return d.reset_index()


def load_funding(paths):
    frames, manifests = [], []
    for path in sorted(map(Path, paths)):
        digest = verified_archive(path)
        with zipfile.ZipFile(path) as archive:
            if len(archive.namelist()) != 1:
                raise ValueError('expected one funding CSV')
            with archive.open(archive.namelist()[0]) as handle:
                d = pd.read_csv(handle)
        if list(d.columns) != ['calc_time', 'funding_interval_hours', 'last_funding_rate']:
            raise ValueError('unexpected funding schema')
        if not np.isfinite(d.to_numpy(float)).all() or (d.funding_interval_hours <= 0).any():
            raise ValueError('invalid funding data')
        d['funding_at'] = pd.to_datetime(d.calc_time, unit='ms', utc=True)
        d['source_sha256'] = digest
        d['available_at'] = pd.NaT
        d['availability_status'] = 'unknown_historical_receipt'
        frames.append(d)
        manifests.append({'path': path.name, 'sha256': digest, 'rows': len(d)})
    if not frames:
        raise ValueError('no funding archives')
    result = pd.concat(frames, ignore_index=True)
    if result.funding_at.duplicated().any() or not result.funding_at.is_monotonic_increasing:
        raise ValueError('duplicate or unordered funding timestamps')
    return result, manifests


def funding_asof(decisions, funding):
    """Use only recorded availability, never infer it from settlement time.

    Late receipt of an older settlement cannot replace a newer known settlement.
    Missing receipts and pre-first-observation decisions remain unknown.
    """
    decisions = pd.to_datetime(decisions, utc=True)
    d = funding.copy()
    d['funding_at'] = pd.to_datetime(d.funding_at, utc=True)
    d['available_at'] = pd.to_datetime(d.available_at, utc=True)
    if (d.available_at.notna() & (d.available_at < d.funding_at)).any():
        raise ValueError('funding receipt precedes settlement')
    values = []
    for at in decisions:
        eligible = d[(d.available_at <= at) & (d.funding_at <= at)]
        values.append(np.nan if eligible.empty else float(eligible.sort_values('funding_at').iloc[-1].last_funding_rate))
    return pd.Series(values, dtype=float)


def assert_discovery_allowed(manifest):
    if manifest.get('status') != 'PASS' or manifest.get('outcome_testing_allowed') is not True:
        raise ValueError('Data Gate not PASS: outcome testing is forbidden')
    if not manifest.get('artifacts'):
        raise ValueError('Data Gate has no verified artifacts')
    for item in manifest['artifacts']:
        if sha256(item['path']) != item['sha256']:
            raise ValueError('Data Gate artifact changed after validation')


def migrate_v1_count_diagnostics(frame):
    """Lossless relabel plus removal of unsupported derived trade estimators.

    Call only after verifying a version-1 cache and its source checksum.
    No raw trade values or directly observed aggregate statistics change.
    """
    required = {'trade_count', 'trade_intensity_per_second', 'mean_trade_size'}
    if not required.issubset(frame.columns) or 'underlying_id_span_count' in frame:
        raise ValueError('not a version-1 count schema')
    return frame.rename(columns={'trade_count': 'underlying_id_span_count'}).drop(
        columns=['trade_intensity_per_second', 'mean_trade_size'])
