import pandas as pd
import pytest
from core.market_mechanics.reconciliation import reconcile_klines


def test_discrepancies_cannot_be_silently_reclassified_as_complete():
    t = pd.Timestamp('2024-01-01', tz='UTC')
    agg = pd.DataFrame({'time': [t], 'aggressive_buy_volume': [2.], 'aggressive_sell_volume': [3.],
                        'quote_volume': [500.], 'underlying_id_span_count': [6]})
    k = pd.DataFrame({'open_time': [t.value // 1_000_000], 'volume': [5.],
                      'taker_buy_volume': [2.], 'quote_volume': [500.], 'count': [5]})
    report = reconcile_klines(agg, k)
    assert report['status'] == 'FAIL'
    assert report['checks']['base_volume']['mismatched_hours'] == 0
    assert report['checks']['underlying_id_span_diagnostic']['mismatched_hours'] == 1
    agg.loc[0, 'underlying_id_span_count'] = 5
    assert reconcile_klines(agg, k)['status'] == 'PASS'
    agg.loc[0, 'aggressive_buy_volume'] = 1.
    assert reconcile_klines(agg, k)['checks']['buy_volume']['mismatched_hours'] == 1
    k.loc[0, 'open_time'] += 3_600_000
    with pytest.raises(ValueError, match='identical'):
        reconcile_klines(agg, k)
