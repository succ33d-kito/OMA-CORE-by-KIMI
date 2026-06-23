# OSIRIS Extended Demo — Regression Report

## Summary

- **Date:** 2026-06-23
- **Test count:** 270
- **Passed:** 270
- **Failed:** 0
- **Warnings:** 3 (existing PytestRemovedIn10Warning — pre-existing, not from this sprint)
- **Duration:** 26.11s

## Test Categories

| Category | Count | Status |
|----------|-------|--------|
| Agent Council | 4 | ✅ ALL PASS |
| Agent Schema | 4 | ✅ ALL PASS |
| Backtest v2 | 6 | ✅ ALL PASS |
| Council v2 | 4 | ✅ ALL PASS |
| Crash Detector v2 | 14 | ✅ ALL PASS |
| Crypto Regression | 42 | ✅ ALL PASS |
| Event Bus | 6 | ✅ ALL PASS |
| Extended Demo Telemetry | 14 | ✅ ALL PASS (NEW) |
| Failure Classifier | 15 | ✅ ALL PASS (NEW) |
| Health Monitor | 34 | ✅ ALL PASS (NEW) |
| Integration | 13 | ✅ ALL PASS |
| Kill Switch | 9 | ✅ ALL PASS |
| Knife Detector | 9 | ✅ ALL PASS |
| Market Agent | 5 | ✅ ALL PASS |
| Market Agent Signal Integrity | 13 | ✅ ALL PASS |
| Memory | 7 | ✅ ALL PASS |
| Paper Trading Experiment | 13 | ✅ ALL PASS |
| Performance Memory | 6 | ✅ ALL PASS |
| Profiles | 8 | ✅ ALL PASS |
| Risk Agent | 5 | ✅ ALL PASS |
| Survival Replay | 8 | ✅ ALL PASS |
| Trade Schema | 6 | ✅ ALL PASS |

## Baseline Comparison

| Metric | Baseline | Current | Delta |
|--------|----------|---------|-------|
| Test count | 200 | 270 | +70 |
| Pass rate | 100% | 100% | 0% |
| Failures | 0 | 0 | 0 |

## New Tests Added

- `tests/test_health_monitor.py` — 34 tests covering HealthMonitor checks for equity sanity, guard/crash modes, open positions, position sizes, trade consistency, cycle diversity, skip detection, and overall status.
- `tests/test_failure_classifier.py` — 15 tests covering failure classification by category, severity assignment, file I/O, and summary generation.
- `tests/test_extended_demo_telemetry.py` — 14 tests covering TelemetryRecorder and GuardAuditRecorder for append-only JSONL recording, reading, summaries, and file path creation.

## Validation

- **No trading logic changed:** MarketAgent, RiskAgent, Council v1/v2, PaperTradingEngine, CapitalGuard, CrashDetector, KnifeDetector, GapRiskEngine, DirectionController, PerformanceMemory — all untouched.
- **No risk/survival logic changed:** All survival and protection components unchanged.
- **Crypto Profile v1 remains frozen:** No new agents, indicators, collectors, or asset classes activated.
- **Monitoring is non-invasive:** HealthMonitor, TelemetryRecorder, GuardAuditRecorder, FailureClassifier observe and report only.

## Verdict

**REGRESSION GATE: PASS** — All 270 tests pass. System is ready for Extended Demo.
