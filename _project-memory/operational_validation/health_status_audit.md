# Health Status Audit Report

Generated: 2026-06-23
Source: `core/monitoring/health.py` and `_extended_demo/telemetry_*.jsonl`

## 1. All Checks and Trigger Conditions

| # | Check Name | Returns | DEGRADED When | CRITICAL When | Type |
|---|------------|---------|---------------|---------------|------|
| 1 | `process_alive` | HEALTHY | Never | Never (always HEALTHY) | 🧊 Informational |
| 2 | `equity_sanity` | HEALTHY / CRITICAL | Never | equity ≤ 0 or equity > 10× initial_capital | 🛑 Blocking |
| 3 | `capital_guard_mode` | HEALTHY / DEGRADED / CRITICAL | Guard mode = CAUTION | Guard mode = HALT or EMERGENCY | 🛑 Blocking |
| 4 | `crash_mode` | HEALTHY / DEGRADED / CRITICAL | Crash mode = WARNING | Crash mode = PANIC or EMERGENCY | 🛑 Blocking |
| 5 | `open_positions` | HEALTHY / CRITICAL | Never | Position held beyond max_holding_hours (72h) | 🛑 Blocking |
| 6 | `position_sizes` | HEALTHY / CRITICAL | Never | Any position with size < 0 | 🛑 Blocking |
| 7 | `trade_consistency` | HEALTHY / CRITICAL | Never | Closed trade missing PnL, or open trade missing entry price | 🛑 Blocking |
| 8 | `price_data` | HEALTHY / DEGRADED | Price data unavailable for at least one symbol | Never | ⚠️ Non-blocking |
| 9 | `cycle_diversity` | HEALTHY / DEGRADED | Last 3 cycles have identical event & signal counts | Never | ⚠️ Non-blocking |
| 10 | `excessive_skips` | HEALTHY / DEGRADED / CRITICAL | At least 1 skipped cycle (0 events + errors > 0) | > 5 skipped cycles | 🛑 Blocking at CRITICAL |

## 2. DEGRADED State Analysis

### Which checks can produce DEGRADED?

| Check | DEGRADED Condition | Operational Impact | Acceptable? |
|-------|-------------------|-------------------|-------------|
| `capital_guard_mode` | CAUTION mode | Trading restricted but continues | ✅ Acceptable — guard is doing its job |
| `crash_mode` | WARNING mode | Position sizes reduced 50% | ✅ Acceptable — crash detection working |
| `price_data` | Missing price for 1+ symbol | Monitoring alert, no trade impact | ✅ Acceptable — may self-resolve |
| `cycle_diversity` | Repeated event/signal counts | Monitoring alert, no trade impact | ✅ Acceptable — may be normal in low-volatility |
| `excessive_skips` | 1-5 skipped cycles | Monitoring alert | ✅ Acceptable — auto-recovery expected |

### Historical DEGRADED Occurrences

**No DEGRADED events detected across all 55 telemetry cycles.**
All cycles ran with guard=normal, crash=none, gap_risk=0.0.

## 3. CRITICAL State Analysis

### Which checks can produce CRITICAL?

| Check | CRITICAL Condition | Operational Impact | Gate Blocker? |
|-------|--------------------|-------------------|---------------|
| `equity_sanity` | equity ≤ 0 or > 10× initial | Trading impossible | ✅ YES |
| `capital_guard_mode` | HALT or EMERGENCY | All trading blocked | ✅ YES |
| `crash_mode` | PANIC or EMERGENCY | All trading blocked or severely restricted | ✅ YES |
| `open_positions` | Stale beyond 72h | Position stuck — manual intervention needed | ✅ YES |
| `position_sizes` | Negative size | Impossible state — data corruption | ✅ YES |
| `trade_consistency` | Closed trade missing PnL | Data inconsistency | ✅ YES |
| `excessive_skips` | > 5 skipped cycles | Pipeline may be stalled | ✅ YES |

## 4. Extended Demo Gate Relevance

| Check | Gate Blocker? | Gate Criteria Reference |
|-------|---------------|------------------------|
| `process_alive` | Informational only | N/A |
| `equity_sanity` | ✅ YES — equity ≤ 0 impossible | Criterion #7 (drawdown) |
| `capital_guard_mode` | ✅ YES — HALT/EMERGENCY blocks gate | Criteria #3, #10 |
| `crash_mode` | ✅ YES — PANIC/EMERGENCY blocks gate | Criteria #3, #11 |
| `open_positions` | ✅ YES — stale positions block gate | Criterion #5 |
| `position_sizes` | ✅ YES — impossible state | Criterion #8 (NO-GO) |
| `trade_consistency` | ✅ YES — data corruption | Criterion #6 (NO-GO) |
| `price_data` | ⚠️ CONDITIONAL (self-resolving) | CONDITIONAL #3 |
| `cycle_diversity` | ⚠️ CONDITIONAL (informational) | CONDITIONAL #3 |
| `excessive_skips` | ✅ YES only at CRITICAL (>5 skips) | CONDITIONAL #3, NO-GO #9 |

## 5. Verdict

### Extended Demo Gate Blockers

| Check | Would Block Gate? | Blocks If |
|-------|------------------|-----------|
| `equity_sanity` | 🛑 BLOCKING | CRITICAL (equity ≤ 0 or > 10×) |
| `capital_guard_mode` | 🛑 BLOCKING | CRITICAL (HALT/EMERGENCY) |
| `crash_mode` | 🛑 BLOCKING | CRITICAL (PANIC/EMERGENCY) |
| `open_positions` | 🛑 BLOCKING | CRITICAL (stale > 72h) |
| `position_sizes` | 🛑 BLOCKING | CRITICAL (negative size) |
| `trade_consistency` | 🛑 BLOCKING | CRITICAL (inconsistent) |
| `excessive_skips` | 🛑 BLOCKING | CRITICAL (> 5 skips) |
| `price_data` | ⚠️ CONDITIONAL | DEGRADED (acceptable if self-resolving) |
| `cycle_diversity` | ⚠️ CONDITIONAL | DEGRADED (informational only) |
| `process_alive` | ✅ NON-BLOCKING | Never returns non-HEALTHY |

### Current State (55 Telemetry Cycles)

- All 10 checks return HEALTHY
- No DEGRADED or CRITICAL events have occurred
- All guard modes: nominal (normal/none)
- No stale positions, no negative sizes, no trade inconsistencies
- No skipped cycles, no price data issues

**HealthMonitor is operational and correctly reporting HEALTHY.**