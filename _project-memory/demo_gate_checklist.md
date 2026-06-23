# OSIRIS Demo Gate Checklist

## Objective Requirements for Demo Activation

---

### Section A — Runtime Stability

| # | Requirement | Status | Notes |
|---|---|---|---|
| A1 | No unhandled exceptions during 30-day paper run | PASS | 0 critical errors |
| A2 | ProcessDecision returns Optional[TradeSignal] (never crashes) | PASS | Structured |
| A3 | CheckPositions handles missing prices gracefully | PASS | Skips assets with None |
| A4 | Engine survives full 30-day run without memory leaks | PASS | 2517 events, stable |
| A5 | No silent data corruption in any component | PASS | All trades consistent |

### Section B — Risk Control

| # | Requirement | Min Threshold | Actual | Status |
|---|---|---|---|---|
| B1 | Max drawdown | < 15% | 3.36% (COVID) | PASS |
| B2 | Max daily loss | < 10% | 3.36% | PASS |
| B3 | Max weekly loss | < 20% | 3.36% | PASS |
| B4 | Open risk | < 25% | 0% (end) | PASS |
| B5 | Consecutive loss limit | Triggers at 7 | 5 (COVID) | CONDITIONAL |
| B6 | Kill switch activates at 35% DD | Tested | Not triggered | NOT TESTED |

### Section C — Guard Integration

| # | Requirement | Status | Notes |
|---|---|---|---|
| C1 | CapitalGuard: Summary exposes mode, drawdown, losses | PASS | Verified in portfolio summary |
| C2 | DirectionController: Blocks/enables based on WR | PASS | SHORT disabled at 0% WR |
| C3 | CrashDetector: Computes score on BTC-only data | PASS | Single-asset tracking fixed |
| C4 | CrashDetector: Flash crash detection (gap/velocity) | PASS | Emergency triggered on BTC gaps >3% |
| C5 | CrashDetector: Multi-day crash detection | FAIL | Needs multi-window velocity (FLAW-16) |
| C6 | KnifeDetector: Dip vs falling knife logic | NOT TESTED | No LONG signals in test windows |
| C7 | GapRiskEngine: Stop cushion adjustment | PASS | Mult 1.0-1.5x based on gap risk |
| C8 | GapRiskEngine: Size reduction | PASS | 0.5-1.0x based on gap risk |
| C9 | Emergency Mode: Blocks new entries | PASS | 566 blocks in 7-day run |
| C10 | Kill Switch: Stops all trading | NOT TESTED | 35% DD never approached |

### Section D — Traceability

| # | Requirement | Status | Notes |
|---|---|---|---|
| D1 | All trades recorded in PerformanceMemory | PASS | 27 total across runs |
| D2 | Guard activation logs complete (reason, asset, ts) | PASS | GuardLogger captures all |
| D3 | Portfolio summary exposes risk state | PASS | crash_score, gap_risk_score, guard_mode, kill_switch |
| D4 | Equity curve reconstructable from closed trades | PASS | Timestamps + PnL |
| D5 | Exit reasons logged per trade | PASS | STOP_LOSS / TAKE_PROFIT / TIME_EXPIRY |
| D6 | Agent opinions recorded per trade | PASS | Through PerformanceMemory |

### Section E — Data Integrity

| # | Requirement | Status | Notes |
|---|---|---|---|
| E1 | Crash/Gap detectors use single-asset (BTC) data | PASS | Fixed during sprint |
| E2 | SlippageEngine applies per-asset spread | PASS | BTC=1bps, ETH=2bps, SOL=3bps |
| E3 | Position sizing uses _risk_base (max 0.1% growth/trade) | PASS | Verified |
| E4 | DirectionController rolling window correct | PASS | 20-trade window |
| E5 | CapitalGuard date-based tracking correct | PASS | Daily/weekly loss separation |

---

## Gate Verdict

### Critical Blockers for Demo Activation

1. **CrashDetector multi-day crash failure (C5)** — COVID-style crashes not detected. Must add multi-window drawdown velocity.
2. **KnifeDetector untested (C6)** — Cannot verify dip vs falling knife logic without LONG signal coverage.
3. **Kill switch untested (C10)** — Cannot verify 35% DD halt without controlled drawdown test.

### Conditional Requirements

1. **Tighten CapitalGuard daily loss to 5%** (from 10%) in demo mode.
2. **Accept 12.5% gap-down failure probability** — COVID crash remains the only failure mode.
3. **Paper trading ≥7 days before demo switch** — Verify no silent failures.

### Final Gate Status

**GATE: NOT PASSED**

3 critical blockers remain. Recommend fixing CrashDetector multi-day detection and running controlled drawdown test before demo activation.
