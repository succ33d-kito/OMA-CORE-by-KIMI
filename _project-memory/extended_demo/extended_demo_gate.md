# OSIRIS Extended Demo Gate

## Purpose

This document defines the criteria that OSIRIS must meet to pass the Extended Demo Gate — the final validation step before considering Micro Capital or future deployment.

## Gate Criteria

### GO — Minimum Requirements (ALL must pass)

| # | Criteria | Description | Pass/Fail |
|---|----------|-------------|-----------|
| 1 | 30 days continuous operation | No unplanned shutdowns or crash loops | ☐ |
| 2 | 0 critical runtime failures | No uncaught exceptions in pipeline | ☐ |
| 3 | 0 guard failures | CapitalGuard, CrashDetector, KnifeDetector, GapRisk all functional | ☐ |
| 4 | 0 uncontrolled exposure | Open positions never exceed risk limits | ☐ |
| 5 | 0 stale open positions | No position held beyond configured expiry | ☐ |
| 6 | 0 silent failures | Every anomaly classified and logged | ☐ |
| 7 | Drawdown within allowed limits | Max drawdown < 35% (CapitalGuard HALT threshold) | ☐ |
| 8 | Complete telemetry | Telemetry JSONL recorded for every cycle | ☐ |
| 9 | Complete failure logs | Every failure classified and persisted | ☐ |
| 10 | CapitalGuard functional | GuardMode transitions correctly and records interventions | ☐ |
| 11 | CrashDetector functional | Crash scores computed, modes transition correctly | ☐ |
| 12 | GapRisk functional | Gap risk scores computed at each cycle | ☐ |
| 13 | PerformanceMemory functional | Trades recorded, accuracy tracked, learning summary available | ☐ |
| 14 | HealthMonitor not stuck in CRITICAL | HealthMonitor must not remain CRITICAL without recovery | ☐ |
| 15 | No trading logic changed | MarketAgent, RiskAgent, Council, PaperTradingEngine, all guards untouched | ☐ |
| 16 | Crypto Profile v1 remains frozen | No new agents, indicators, collectors, or asset classes activated | ☐ |
| 17 | All regression tests pass | 200+ tests passing at baseline check | ☐ |

**GO verdict:** ALL 17 criteria pass.

### CONDITIONAL — Acceptable with documentation

| # | Criteria | Acceptable If |
|---|----------|---------------|
| 1 | Non-critical data/API failures occurred | Automatically recovered, no trading impact |
| 2 | Small gaps in telemetry | Less than 1% of cycles missing, no trading/risk data lost |
| 3 | Degraded health states | Resolved without manual intervention within 3 cycles |
| 4 | Guard interventions | Blocked trades explained in guard audit; no silent blocks |
| 5 | Runtime errors | All errors classified, none above WARNING severity |

### NO-GO — Immediate stop (ANY triggers NO-GO)

| # | Criteria |
|---|----------|
| 1 | Uncaught crash — process terminates unexpectedly |
| 2 | Guard failure — guard allows trade that should be blocked, or blocks trade that should execute |
| 3 | Risk limit violation — drawdown > 35%, exposure > 100% |
| 4 | Uncontrolled exposure — open positions exceed max_open_positions |
| 5 | Corrupted trade state — trade with inconsistent or impossible state |
| 6 | Missing critical logs — telemetry or guard audit gap > 1 hour |
| 7 | Repeated stale data — price data unavailable for > 6 consecutive cycles |
| 8 | Impossible equity/position state — negative equity, negative size, PnL inconsistency |
| 9 | Manual intervention required to avoid loss — operator had to step in |

## Gate Decision Process

1. Run `python scripts/extended_demo_realtime.py --smoke` for 7-day validation.
2. If smoke passes, run `python scripts/extended_demo_realtime.py --run` for 30-day validation.
3. Generate reports: `python scripts/extended_demo_report.py`
4. Run regression suite: `python -m pytest tests/ -v`
5. Evaluate all GO criteria. Document any CONDITIONAL items.
6. Publish gate verdict in `_project-memory/extended_demo/cto_extended_demo_report.md`.

## Readiness Matrix

| Stage | Status | Notes |
|-------|--------|-------|
| Paper Trading | ✅ GO | Validated in Live Paper Gate |
| Demo Trading | ✅ GO | Validated in Demo Gate |
| Extended Demo | ⏳ PENDING | This gate defines the criteria |
| Micro Capital | 🚫 NO-GO | Requires Extended Demo completion |
| Real Capital | 🚫 NO-GO | Requires Micro Capital completion |
| Forex Research Mode | ✅ GO | Collect-only, no trades |
