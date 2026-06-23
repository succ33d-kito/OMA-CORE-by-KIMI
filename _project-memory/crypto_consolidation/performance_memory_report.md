# OSIRIS PerformanceMemory Audit Report
> Generated: 2026-06-23 02:43:02 UTC

## Overview

- Total trades recorded in PerformanceMemory: 74
- Total agent outcome records: 148
- Closed trades in engine: 37
- Issues found: 1

## Consistency Check

**Trade count matches?**
❌ Mismatch
  Memory: 74, Engine: 37

**All trades have valid PnL?**
✅ Yes

**All trades have exit reasons?**
✅ Yes

## Agent Accuracy

| Agent | Accuracy |
|---|---|
| market_agent | 40.5% |
| risk_agent | 40.5% |

## Performance by Asset

| Asset | Avg PnL% |
|---|---|
| BTC | +5.82 |
| ETH | +7.53 |

## Performance by Direction

- LONG avg PnL: 9.32
- SHORT avg PnL: -14.97
- LONG count: 66
- SHORT count: 8

## Agent Confidence Calibration

### market_agent
- Avg confidence: 0.682
- Actual accuracy: 0.405
- Bias: 0.277
- Overconfidence: True
- Underconfidence: False

### risk_agent
- Avg confidence: 0.623
- Actual accuracy: 0.405
- Bias: 0.218
- Overconfidence: True
- Underconfidence: False


## Recommendation Success Rates

| Recommendation | Success Rate |
|---|---|
| hedge | 0.0% |
| buy | 45.5% |
| avoid | 40.5% |

## Issues Found

- ❌ Trade count mismatch: memory=74, engine=37

## Persistence Status

PerformanceMemory is in-memory only. Trades live in Python object lifetime. MemoryStore.long_term.store() is called per trade but no query/load mechanism exists in current codebase. Persistence status: IN-MEMORY ONLY — data is lost on process exit.

| Aspect | Status |
|---|---|
| Trade recording | ✅ All trades recorded |
| Agent attribution | ✅ Per-agent outcome tracking |
| Performance by asset | ✅ Tracked |
| Performance by direction | ✅ Tracked |
| Recommendation success | ✅ Tracked |
| Confidence calibration | ✅ Tracked (requires 5+ records) |
| Persistence to disk | ❌ NOT PERSISTED — in-memory only |
| Recovery on restart | ❌ Not supported |
