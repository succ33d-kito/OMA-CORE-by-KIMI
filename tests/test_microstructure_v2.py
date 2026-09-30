from pathlib import Path
import hashlib
import zipfile

import numpy as np
import pandas as pd
import pytest

from core.market_mechanics.microstructure import (
    AGG_COLUMNS, aggregate_chunks, aggregate_archive, causal_derivatives,
    funding_asof, load_funding, verified_archive, assert_discovery_allowed,
)

T = pd.Timestamp('2024-01-01', tz='UTC')


def test_cache_migration_removes_unsupported_estimators_only():
    from core.market_mechanics.microstructure import migrate_v1_count_diagnostics
    new, _ = aggregate_chunks([trades()], T, T + pd.Timedelta(hours=2))
    old = new.rename(columns={'underlying_id_span_count': 'trade_count'}).copy()
    old['trade_intensity_per_second'] = old.trade_count / 3600
    old['mean_trade_size'] = (old.aggressive_buy_volume + old.aggressive_sell_volume) / old.trade_count
    pd.testing.assert_frame_equal(new, migrate_v1_count_diagnostics(old))
    with pytest.raises(ValueError):
        migrate_v1_count_diagnostics(new)


def trades():
    ms = T.value // 1_000_000
    return pd.DataFrame([
        [10, 100, 2, 20, 21, ms, False],
        [11, 101, 3, 22, 24, ms + 3_599_999, True],
        [12, 102, 4, 25, 25, ms + 3_600_000, False],
    ], columns=AGG_COLUMNS)


def zipped(tmp_path, name, frame):
    path = tmp_path / name
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('data.csv', frame.to_csv(index=False))
    Path(str(path) + '.CHECKSUM').write_text(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + name)
    return path


def test_true_means_seller_aggressor_and_hour_boundary():
    h, audit = aggregate_chunks([trades()], T, T + pd.Timedelta(hours=2))
    assert h.aggressive_buy_volume.tolist() == [2, 4]
    assert h.aggressive_sell_volume.tolist() == [3, 0]
    assert h.signed_volume.tolist() == [-1, 4]
    assert h.aggressor_imbalance.tolist() == [-.2, 1]
    assert h.underlying_id_span_count.tolist() == [5, 1]
    assert h.aggregate_trade_count.tolist() == [2, 1]
    assert 'mean_trade_size' not in h
    assert 'trade_intensity_per_second' not in h
    assert h.mean_aggregate_size.tolist() == [2.5, 4]
    assert h.aggregate_intensity_per_second.iloc[0] == 2 / 3600
    assert h.available_at.isna().all()
    assert audit['missing_aggregate_ids'] == 0


def test_chunk_boundaries_do_not_change_result():
    d = trades()
    a, x = aggregate_chunks([d], T, T + pd.Timedelta(hours=2))
    b, y = aggregate_chunks([d.iloc[:1], d.iloc[1:2], d.iloc[2:]], T, T + pd.Timedelta(hours=2))
    pd.testing.assert_frame_equal(a, b)
    assert x == y


@pytest.mark.parametrize('column,value', [
    ('agg_trade_id', 10), ('agg_trade_id', 10.5), ('transact_time', 0),
    ('price', float('inf')), ('quantity', -1), ('is_buyer_maker', 'maybe'),
    ('last_trade_id', 0),
])
def test_malformed_trades_rejected(column, value):
    d = trades().astype(object)
    d.loc[1, column] = value
    with pytest.raises(ValueError):
        aggregate_chunks([d], T, T + pd.Timedelta(hours=2))


def test_cross_chunk_duplicate_rejected():
    d = trades()
    with pytest.raises(ValueError, match='IDs'):
        aggregate_chunks([d, d], T, T + pd.Timedelta(hours=2))


def test_future_trade_is_not_in_closed_hour():
    with pytest.raises(ValueError, match='outside'):
        aggregate_chunks([trades()], T, T + pd.Timedelta(hours=1))


def test_id_gap_and_missing_hours_remain_explicit():
    d = trades().iloc[[0, 2]]
    h, audit = aggregate_chunks([d], T, T + pd.Timedelta(hours=3))
    assert audit['missing_aggregate_ids'] == 1
    assert h.coverage_status.iloc[-1] == 'unknown'
    assert np.isnan(h.aggressive_buy_volume.iloc[-1])


def test_verified_archive_and_corruption(tmp_path):
    p = zipped(tmp_path, 'test.zip', trades())
    h, audit = aggregate_archive(p, T, T + pd.Timedelta(hours=2), chunksize=1)
    assert audit['rows'] == 3 and len(h) == 2
    p.write_bytes(p.read_bytes() + b'corrupt')
    with pytest.raises(ValueError, match='checksum mismatch'):
        verified_archive(p)


def test_funding_preserves_unknown_availability(tmp_path):
    d = pd.DataFrame({'calc_time': [T.value // 1_000_000], 'funding_interval_hours': [8], 'last_funding_rate': [.001]})
    f, sources = load_funding([zipped(tmp_path, 'funding.zip', d)])
    assert sources[0]['rows'] == 1
    assert f.available_at.isna().all()
    assert funding_asof(pd.date_range(T, periods=24, freq='h'), f).isna().all()


def test_funding_availability_asof_never_next_rate():
    f = pd.DataFrame({'funding_at': [T, T + pd.Timedelta(hours=8)],
                      'available_at': [T + pd.Timedelta(minutes=1), T + pd.Timedelta(hours=8, minutes=2)],
                      'last_funding_rate': [.001, -.002]})
    x = funding_asof([T, T + pd.Timedelta(minutes=1), T + pd.Timedelta(hours=8), T + pd.Timedelta(hours=9)], f)
    assert np.isnan(x.iloc[0])
    assert x.iloc[1:].tolist() == [.001, .001, -.002]


def test_funding_late_old_receipt_cannot_replace_newer_rate():
    f = pd.DataFrame({'funding_at': [T, T + pd.Timedelta(hours=8)],
                      'available_at': [T + pd.Timedelta(hours=10), T + pd.Timedelta(hours=9)],
                      'last_funding_rate': [.001, -.002]})
    assert funding_asof([T + pd.Timedelta(hours=11)], f).iloc[0] == -.002


def test_funding_impossible_receipt_rejected():
    f = pd.DataFrame({'funding_at': [T], 'available_at': [T - pd.Timedelta(seconds=1)], 'last_funding_rate': [0.]})
    with pytest.raises(ValueError, match='precedes'):
        funding_asof([T], f)


def test_derivatives_use_only_history_and_break_on_gaps():
    h, _ = aggregate_chunks([trades()], T, T + pd.Timedelta(hours=3))
    result = causal_derivatives(h)
    changed = h.copy()
    changed.loc[2, 'aggressor_imbalance'] = 99
    pd.testing.assert_frame_equal(result.iloc[:2], causal_derivatives(changed).iloc[:2])
    assert np.isnan(result.imbalance_change_1h.iloc[2])


def test_gate_blocks_outcomes_and_modified_artifacts(tmp_path):
    with pytest.raises(ValueError, match='no verified artifacts'):
        assert_discovery_allowed({'status': 'PASS', 'outcome_testing_allowed': True})
    with pytest.raises(ValueError, match='forbidden'):
        assert_discovery_allowed({'status': 'FAIL', 'outcome_testing_allowed': False})
    p = tmp_path / 'data.csv'
    p.write_text('original')
    m = {'status': 'PASS', 'outcome_testing_allowed': True,
         'artifacts': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}]}
    assert_discovery_allowed(m)
    p.write_text('changed')
    with pytest.raises(ValueError, match='changed'):
        assert_discovery_allowed(m)


@pytest.mark.parametrize('kind,period', [('aggTrades', 13), ('fundingRate', 0), ('metrics', '2025-01-01')])
def test_downloader_rejects_holdout_requests(tmp_path, kind, period):
    from scripts.download_mechanics_v2 import acquire
    with pytest.raises(ValueError):
        acquire(tmp_path, kind, period)
