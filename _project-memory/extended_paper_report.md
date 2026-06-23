# OSIRIS Extended Paper Trading & Demo Gate Sprint

## Results Summary

### Phase 1 — Extended Paper Trading

| Metric | 7-Day (Jun 10-22) | 30-Day (May 18-Jun 22) |
|---|---|---|
| Total trades | 22 | 5 |
| Win rate | 50.0% | 0.0% |
| Total return | +5.60% | -0.58% |
| Max drawdown | 2.75% | 0.58% |
| Sharpe (annual) | 7.33 | -106.86 |
| Profit factor | 2.32 | 0.00 |
| Direction | 100% SHORT | 100% SHORT |

**Note**: System was SHORT-only in both windows because the MarketAgent identified a sustained downtrend (SMA20 < SMA50) with no oversold (RSI < 30) bounce opportunities. This is correct behavior — the system is a trend-following dip buyer, and when the trend is down with no bounces, it trades SHORT.

### Phase 2 — Guard Validation

| Guard | Status | Evidence |
|---|---|---|
| CapitalGuard | PASS | Caution mode triggered by consecutive losses. Size reduction 0.50x. |
| DirectionController | PASS | SHORT disabled after 5 losses at 0% WR in 30-day run. |
| CrashDetector | CONDITIONAL | Emergency/Panic triggered during COVID replay (78 events). BUT failed to detect multi-day COVID crash (score 15, NONE mode). |
| KnifeDetector | NOT TESTED | No LONG signals generated (system was SHORT-only). Cannot verify dip vs falling knife logic. |
| GapRiskEngine | PASS | 1968 size reduction events during COVID. 2517 during 30-day run. Avg gap size 0.80%. |
| Emergency Mode | CONDITIONAL | Triggered in 7-day run (566 blocks) but not in 30-day. |
| Kill Switch | NOT TESTED | Never triggered. DD never approached 35% halt threshold. |

### Phase 4 — COVID Crash Failure Replay

| Metric | Without Guards | With Guards | Improvement |
|---|---|---|---|
| Total return | -6.64% | -3.36% | +3.28pp (49.4%) |
| Max drawdown | 6.64% | 3.36% | -3.28pp (49.4%) |
| Trades | 5 | 5 | Same (only SHORT) |

**Loss CAPPED by ~50%.** Protection stack worked, but not through CrashDetector. Protection came from:
1. GapRiskEngine (elevated gap risk → 50% size reduction)
2. CapitalGuard (5 consecutive losses → CAUTION mode → 50% size reduction)
3. DirectionController (0% SHORT WR → disabled SHORT)

CrashDetector scored only 15 (NONE mode) because COVID was a multi-day crash, not a flash crash. The 6-hour drawdown velocity and hourly gap detectors do not trigger on multi-day events.

### Guard Activation Log (30-Day Run)

| Block Reason | Count |
|---|---|
| guard_blocked (by any guard in process_decision) | 3155 |
| gap_risk_size_reduction (GapRiskEngine) | 1968 |
| crash_detector_emergency | 62 |
| crash_detector_panic | 16 |
| knife_rejections | 0 |
| kill_switch | 0 |

## Known Issues

### FLAW-16: CrashDetector does not detect multi-day crashes
CrashDetector uses 6-hour drawdown velocity and hourly gap size. Multi-day crashes like COVID (Feb-Apr 2020) unfold over 48+ hours, not in a single hourly candle. The detector stays in NONE mode throughout.
- **Impact**: Emergency Mode never triggers during slow crashes. Protection relies on GapRiskEngine + CapitalGuard.
- **Fix needed**: Add multi-window drawdown velocity (6h, 24h, 72h) to detect slow crashes.

### FLAW-17: KnifeDetector untested
KnifeDetector was never invoked because the system generated 0 LONG signals in all test windows. Cannot verify dip vs falling knife logic.
- **Impact**: Unknown — knife detection may have bugs under actual market conditions.
- **Fix needed**: Force LONG signal in controlled test to verify knife detection.

### FLAW-18: DirectionController disables SHORT too aggressively
After 5 SHORT losses, DirectionController disables SHORT entirely (recovery_threshold=0.35 requires 35% WR for re-enablement). In a pure downtrend, this means the system stops trading entirely after 5 losses.
- **Impact**: System goes flat after small drawdown, missing subsequent profitable SHORT trades.
- **Tradeoff**: This is intentional — prioritizes survival over returns.

## Risk State Summary (End of 30-Day Test)

- CrashDetector: Score 15, Mode NONE
- GapRiskEngine: Score 45 (elevated during COVID), Avg gap 0.80%
- CapitalGuard: Mode CAUTION, DD 0%, Consecutive losses 5
- DirectionController: SHORT disabled, LONG_ONLY mode
- Kill switch: INACTIVE
