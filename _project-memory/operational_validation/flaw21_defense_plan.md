# FLAW-21: Defense-in-Depth Plan

Generated: 2026-06-23

## Current Risk

`Trade.close()` at `core/schemas/trade_schema.py:92-111` has NO idempotency guard:

```python
def close(self, exit_price: float, reason: ExitReason, exit_time: Optional[datetime] = None) -> None:
    self.exit_price = exit_price
    self.exit_reason = reason
    self.exit_time = exit_time or datetime.now(timezone.utc)
    self.status = TradeStatus.CLOSED
    # ... recomputes PnL ...
```

If called twice:
1. First call: sets `exit_price`, `exit_reason`, `exit_time`, `status = CLOSED`, computes PnL
2. Second call: OVERWRITES `exit_price`, may recompute wrong PnL if price changed

## Existing Protection Paths

| Protection | Mechanism | Reliability |
|------------|-----------|-------------|
| Trade removed from `self.positions` before close | Caller removes trade from positions list | ✅ Strong — same trade cannot be found again |
| Single close path per trade | `check_positions()` closes via SL/TP/time; `close_position()` for manual | ✅ Strong — different code paths for different scenarios |
| Trade status not checked before close | No guard (this is the bug) | ❌ Weak — relies on caller discipline |

## Why Risk Is Low

The `_record_trade_result()` method (the sole caller chain for closing trades) always removes the trade from `self.positions` before the next iteration. Code review confirms:

1. `check_positions()` iterates `self.positions`, closes qualifying trades, removes from list (by rebuilding the list without closed trades)
2. `close_position()` removes from list directly
3. No code path exists where the same trade could be passed to `close()` twice

## Minimal Idempotency Patch Proposal

```python
def close(self, exit_price: float, reason: ExitReason, exit_time: Optional[datetime] = None) -> None:
    if self.status == TradeStatus.CLOSED:
        return  # Idempotency guard — already closed
    self.exit_price = exit_price
    ...
```

## Tests Required

| Test | Description |
|------|-------------|
| `test_close_idempotent` | Call `close()` twice, verify PnL unchanged on second call |
| `test_close_normal` | Verify normal close still works (regression) |
| `test_close_twice_different_price` | Call with price1 then price2, verify first price is kept |

## Impact Assessment

| Aspect | Current | Patched |
|--------|---------|---------|
| Double-close prevention | ❌ No guard | ✅ Status check prevents overwrite |
| Backward compatibility | N/A | ✅ Fully backward compatible |
| Regression risk | — | ✅ Near-zero — single early return |

## Should It Block Extended Demo?

**NO.** This is defense-in-depth for a risk that has no practical exploitation path. The 7-day smoke run should proceed without this fix.

## Recommendation

**Apply at convenience before Micro Capital.** Low priority. Single-line change with 3 test cases.

**Priority:** LOW — does not block Extended Demo or Micro Capital.
