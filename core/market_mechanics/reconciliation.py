"""Observation-only cross-checks. Source discrepancies are never filled away."""
import numpy as np
import pandas as pd


def reconcile_klines(agg, klines):
    a = agg.set_index(pd.to_datetime(agg.time, utc=True))
    k = klines.set_index(pd.to_datetime(klines.open_time, unit='ms', utc=True))
    if not a.index.equals(k.index) or a.index.has_duplicates:
        raise ValueError('reconciliation requires identical unique UTC hours')
    checks = {}
    for label, actual, official, atol in [
        ('base_volume', a.aggressive_buy_volume + a.aggressive_sell_volume, k.volume, 1e-6),
        ('buy_volume', a.aggressive_buy_volume, k.taker_buy_volume, 1e-6),
        ('quote_volume', a.quote_volume, k.quote_volume, .01),
        ('underlying_id_span_diagnostic', a.underlying_id_span_count, k['count'], 0),
    ]:
        valid = np.isfinite(actual) & np.isfinite(official)
        equal = valid & np.isclose(actual, official, atol=atol, rtol=1e-10)
        checks[label] = {'mismatched_hours': int((~equal).sum()),
                         'max_absolute_difference': float((actual - official).abs().max()),
                         'absolute_tolerance': atol, 'relative_tolerance': 1e-10}
    return {'hours': len(a), 'checks': checks,
            'status': 'FAIL' if any(x['mismatched_hours'] for x in checks.values()) else 'PASS',
            'note': 'ID spans are diagnostic only, not an exact trade count. Aggregate record count is directly observed.'}
