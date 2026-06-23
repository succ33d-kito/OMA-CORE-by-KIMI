# FLAW-24: Non-Blocking Fix Plan

Generated: 2026-06-23

## Current Behavior

`crash_detector.summary()` at `core/execution/crash_detector.py:253-267`:

```python
def summary(self) -> Dict:
    return {
        "crash_score": round(self.crash_score(), 1),
        "mode": self.crash_mode(10000).value,       # <-- HARDCODED 10000
        "drawdown_velocity_6h": round(self.drawdown_velocity_6h(), 2),
        ...
    }
```

The `crash_mode(10000)` call uses a fixed equity of 10000 when determining the crash mode for reporting purposes.

## Why Safety Is Unaffected

All trade-blocking paths use the correct, actual equity:
- `paper_trading.py:95`: `crash_mode(self.capital)` — correct equity from engine
- `extended_demo_realtime.py`: `crash_mode(self.engine.capital)` — correct
- `position_size_multiplier()`: takes `current_equity` parameter — correct

The hardcoded call exists ONLY in `summary()`, which is a reporting method.

## Why Reporting Is Affected

If actual equity deviates from 10000:
- Equity = 5000 → drawdown % computed on 10000 is half what it should be → mode under-reports risk
- Equity = 20000 → drawdown % is doubled → mode over-reports risk

This affects:
- Portfolio summary reports (via `PaperTradingEngine.get_portfolio_summary()`)
- Extended demo daily/weekly reports
- Any external consumer of `summary()`

## Minimal Safe Patch Proposal

The fix is isolated to `crash_detector.py` and changes only the reporting path:

```python
def summary(self, current_equity: Optional[float] = None) -> Dict:
    equity = current_equity if current_equity is not None else 10000
    return {
        "crash_score": round(self.crash_score(), 1),
        "mode": self.crash_mode(equity).value,
        ...
    }
```

Then update callers of `summary()` to pass actual equity:
- `paper_trading.py:310` `get_portfolio_summary()` → `self.crash_detector.summary(self.capital)`
- `extended_demo_realtime.py` if it calls `summary()` → pass `engine.capital`

## Tests Required

| Test | Description |
|------|-------------|
| `test_summary_default_equity` | Verify `summary()` without argument uses 10000 (backward compat) |
| `test_summary_with_equity` | Verify `summary(5000)` correctly computes crash mode with lower equity |
| `test_summary_higher_equity` | Verify `summary(20000)` correctly computes crash mode with higher equity |
| `test_no_regression_crash_mode` | Verify existing crash mode tests still pass |

**Estimated effort:** 3 test cases + 2 file edits (crash_detector.py + paper_trading.py callers)

## Impact Assessment

| Aspect | Current | Patched |
|--------|---------|---------|
| Trade safety | ✅ Safe | ✅ Safe (unchanged) |
| Reporting accuracy | ❌ Wrong when equity ≠ 10000 | ✅ Correct for any equity |
| Backward compatibility | N/A | ✅ Preserved (default 10000) |
| Regression risk | — | Low — isolated to one function signature |

## Recommendation

**Apply after 7-day smoke run, before 30-day run.** The fix is low-risk and isolated, but applying it before the smoke run introduces unnecessary change. The smoke run can proceed with the current hardcoded state since trade safety is unaffected.

**Priority:** MEDIUM — non-blocking for Extended Demo.
