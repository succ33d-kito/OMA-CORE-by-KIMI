# OSIRIS Demo Gate — Final Recommendation

## Date: 2026-06-22

---

## Tier Assessment

| Tier | Status | Since |
|---|---|---|
| Paper Trading | **GO** | Sprint 6 |
| Demo Trading | **CONDITIONAL** | This sprint |
| Real Capital | **NO** | — |

---

## Sprint Deliverables

| Phase | Deliverable | Location |
|---|---|---|
| 1 | Extended Paper Trading Report | `_project-memory/extended_paper_report.md` |
| 2 | Guard Activation Report | Included in report above |
| 3 | Demo Gate Checklist | `_project-memory/demo_gate_checklist.md` |
| 4 | COVID Replay Report | Included in report above |
| 5 | Demo Deployment Plan | `_project-memory/demo_deployment_plan.md` |
| 6 | Final Recommendation | This document |

---

## Key Findings

### What Works (Verified)

1. **CapitalGuard** — Correctly triggers CAUTION mode on consecutive losses. Emergency mode blocks entries. 0.5x size reduction on losses.
2. **DirectionController** — SHORT disabled after 5 losses at 0% WR. LONG remains enabled.
3. **GapRiskEngine** — Size reduction based on historical gap risk. Avg gap 0.80%, max 5.26%.
4. **SlippageEngine** — Per-asset spread model integrated.
5. **Gap risk cushion** — Stop width increased by 1.0-1.5x based on gap risk score.
6. **Loss capping** — COVID loss reduced from -6.64% to -3.36% (50% improvement).

### What Needs Work (Blockers)

1. **CrashDetector: No multi-day crash detection** — COVID-style crashes unfold over 48+ hours. Current 6-hour velocity and hourly gap detectors stay in NONE mode. Need multi-window drawdown velocity (6h, 24h, 72h).
2. **KnifeDetector: Untested** — System generated 0 LONG signals across all test windows. Dip vs falling knife logic cannot be verified.
3. **Kill switch: Untested** — 35% DD threshold never approached. Cannot verify halt behavior.

### System Architecture Note

OSIRIS is structurally LONG-biased. In the May-Jun 2026 test window, the system was 100% SHORT because the MarketAgent correctly identified a sustained downtrend. **This is not a bug** — the system follows the trend. The concern is that in a crash, the system produces losing SHORT trades instead of profitable dip-buy LONG trades.

---

## Final Recommendation

### Demo Trading: CONDITIONAL YES

**Conditions that must be met before activation:**

1. Fix CrashDetector multi-day detection (multi-window drawdown velocity)
2. Run controlled drawdown test to verify kill switch at 35% DD
3. Force LONG signal in test to verify KnifeDetector logic
4. ≥7 days of paper trading with no silent failures
5. Tighten CapitalGuard daily loss to 5% (from 10%) in demo config

**Accepted risks:**

1. **12.5% gap-down failure probability** — COVID-style crash remains the only failure mode across 8 tested periods. Loss capped at -6.6% (without guards) or -3.4% (with guards).
2. **Zero LONG signals in test windows** — The system may remain SHORT-only for extended periods during downtrends. This is acceptable — survival over returns.

### Real Capital: NO

Not recommended until:
- CrashDetector handles multi-day crashes
- KnifeDetector verified in both dip and falling knife conditions
- Kill switch verified through controlled test
- ≥90 days of successful demo trading without issue
- ≥5 different market regimes tested in demo (not just backtest)

---

## Verdict

```
PAPER TRADING:  ✅ GO (since Sprint 6)
DEMO TRADING:   ⚠️ CONDITIONAL (3 blockers remain)
REAL CAPITAL:   ❌ NOT READY (12+ months minimum)
```
