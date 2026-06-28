# O.M.A.-C.O.R.E. Intelligence Health Report

**Date**: 2026-06-28  
**Sprint**: 14 (Audit & Diagnostics)  
**Overall Grade**: **B**

---

## 1. Architecture

```
Internet ─► Collectors (7) ─► EventBus ─► Pipeline ─► DB ─► CLI / Telegram
                │                            │
                ▼                            ▼
           WorldMonitorV2             ScoreEngine → OpportunityEngine
                                          │
                                    ┌─────┴─────┐
                                    ▼           ▼
                              Priority      Conviction
                                    │
                              ┌─────┴─────┐
                              ▼           ▼
                         Telegram     Scientific
                         Notifier     Layer (empty)
```

### Layer Health

| Layer | Grade | Notes |
|-------|-------|-------|
| Collection | A | 7 collectors, all producing data. Yahoo guard blocks bad data. FRED operational. |
| Pipeline | B | Functional. 71.5% backlog. 225 duplicates detected. 115 expired events. |
| Scoring | B+ | Sprint 13 recalibration successful. No score 100 on new data. Correlation 0.403. |
| Priority | B | 96.6% consistent. WATCHLIST_ADD→CRITICAL (2 cases) is known issue. |
| Conviction | C | 53/177 unique (29.9%). SHORT_SETUP has 1 conviction value for 52 opps. Correlation 0.403. |
| Telegram | A | Fully operational. Structured format. Quality gate. Learning Core stats displayed (0). |
| Scientific | C | All code written and tested. 5 tables, 0 records. No pipeline integration. Stage 10 missing. |
| CLI | A | Full command set. Scientific commands functional but data shows zeros. |

---

## 2. Current Strengths

1. **Score diversity restored**: 0% score 100 on new data (was 55.3%).
2. **CRITICAL now meaningful**: 3.1% on new data vs 51.8% pre-calibration.
3. **Conviction decoupled**: Spearman correlation dropped from 0.9246 → 0.403 (Sprint 13).
4. **Priority consistency**: 96.6% of 177 opportunities have type-appropriate priority.
5. **Yahoo Data Guard**: Blocks bad data at collection time (observed: 4 EURUSD=X blocked).
6. **FRED operational**: Macro data flowing (18 events).
7. **Telegram**: Reliable structured notification with quality gate and diagnostics.
8. **Test suite**: 761 passing, 3 warnings only.

---

## 3. Weaknesses

### Critical

| Issue | Severity | Impact |
|-------|----------|--------|
| **443 unprocessed events (71.5%)** | HIGH | Events accumulate faster than pipeline processes. Backlog is 2× processed count. |
| **225 duplicate events** | HIGH | Same source_id stored multiple times. Inflates counts and wastes processing. |
| **115 expired unprocessed events** | HIGH | Events >24h old that were never processed. May contain stale signals. |
| **Scientific Layer empty** | HIGH | 5 tables, 0 records after 14 sprints. No learning loop operational. |

### Moderate

| Issue | Severity | Impact |
|-------|----------|--------|
| **Conviction clustering (SHORT_SETUP)** | MEDIUM | 52 opps, 1 conviction value (84.0). No variance at all. |
| **Conviction only 29.9% unique** | MEDIUM | 53 unique values for 177 opps. Clustering across Yahoo/FRED events. |
| **WATCHLIST_ADD → CRITICAL (2 cases)** | MEDIUM | Observational type should never be CRITICAL. Evidence gate allows through. |
| **Score/Conviction correlation 0.403** | MEDIUM | Partial coupling remains. Target < 0.3. |

### Minor

| Issue | Severity | Impact |
|-------|----------|--------|
| **63 pre-guard artifacts in DB** | LOW | Historical data inflates overall metrics. Ready for cleanup. |
| **Pipeline processes 200 at a time** | LOW | Could increase batch size to 500 to reduce backlog. |
| **Estimated 12h to clear backlog** | LOW | Achievable with 2 pipeline runs. |
| **FRED events have static conviction (67.5)** | LOW | Not a problem — FRED data is consistently structured. |

---

## 4. Data Quality

| Metric | Value | Assessment |
|--------|-------|------------|
| Total events | 620 | Growing |
| Total opportunities | 177 | Includes 63 pre-guard artifacts |
| Duplicate events | 225 (36%) | **Warning**: high dedup needed |
| Expired unprocessed | 115 (26% of backlog) | **Warning**: stale data |
| Pre-guard artifacts | 63 (36% of opps) | Ready for cleanup |
| Score 100 on new data | 0% | ✅ |
| Priority consistency | 96.6% | ✅ |
| Conviction unique ratio | 29.9% | Needs improvement |

---

## 5. Pipeline Health

| Metric | Value |
|--------|-------|
| Collection rate | ~88 events/day |
| Processing rate | ~200 events/run, ~4 runs/day possible |
| Backlog | 443 unprocessed (71.5%) |
| Backlog growth | +162 events since Sprint 12.5 (from 281 to 443) |
| Time to clear at current rate | 12 hours |
| Events per pipeline run | 200 |
| Opportunities per run | ~35 |

**Diagnosis**: The pipeline is collecting faster than it processes. Each run clears ~200 events but collectors add ~88/day (running hourly). The backlog grew from 281 (Sprint 12.5) to 443 (Sprint 14) — a 58% increase in ~24 hours.

---

## 6. Learning Health

| Metric | Value | Assessment |
|--------|-------|------------|
| Scientific hypotheses | 0 | ❌ No learning started |
| Evidence records | 0 | ❌ |
| Outcome comparisons | 0 | ❌ |
| Knowledge items | 0 | ❌ |
| Criterion deltas | 0 | ❌ |
| Auto-learning pipeline (Stage 10) | Not implemented | ❌ |
| Pipeline → Scientific bridge | Not implemented | ❌ |
| CLI scientific commands | Functional | ✅ |
| Telegram learning stats | Displayed as 0 | ❌ |

**Diagnosis**: The Scientific Layer is fully built but completely unused. The system has been running for 14 sprints without logging a single hypothesis, piece of evidence, or knowledge item.

---

## 7. Score Layer Health

| Metric | Before (Sprint 12.5) | After (Sprint 13) | Target |
|--------|---------------------|-------------------|--------|
| Score 100 % | 55.3% | 0% (new data) | <15% ✅ |
| CRITICAL % | 51.8% | 3.1% (new data) | <20% ✅ |
| Score/Conviction correlation | 0.9246 | 0.403 | <0.3 ⚠ |
| Score diversity | 12/114 (10.5%) | 32/32 (100%) | >50% ✅ |
| Score mean | 90.64 | 65.56 (new data) | 50-75 ✅ |

**Diagnosis**: Sprint 13 recalibration was highly effective. Score saturation is eliminated. CRITICAL is now rare and meaningful. Conviction decoupling is partially complete (correlation 0.403, target <0.3).

---

## 8. Priority Layer Health

| Metric | Value | Assessment |
|--------|-------|------------|
| Overall consistency | 96.6% | ✅ |
| Over-priority | 2 cases (both WATCHLIST_ADD→CRITICAL) | ⚠ Known issue |
| Under-priority | 4 cases (SENTIMENT_TURN_BEAR too low) | ⚠ |
| Most consistent types | SHORT_SETUP, MONITOR_MACRO, NEWS_DRIVEN | ✅ |
| Least consistent | SENTIMENT_TURN_BEAR (40% consistent) | ⚠ |

**Diagnosis**: Priority consistency is strong (96.6%). The 2 over-priority cases are WATCHLIST_ADD→CRITICAL (MSFT +5.71%) — the critical evidence gate should exclude observational types. The 4 under-priority cases are SENTIMENT_TURN_BEAR at MEDIUM — extreme fear sentiment should be HIGH.

---

## 9. Technical Debt

| Item | Priority | Effort | Description |
|------|----------|--------|-------------|
| Pre-guard artifact cleanup | HIGH | 1h | 63 artifacts ready for deletion. Script exists. |
| Deduplication in pipeline | HIGH | 4h | 225 duplicate events. Add source_id dedup in collector layer. |
| Conviction variance for Yahoo events | MEDIUM | 2h | All Yahoo events get conviction=88.75. Add variance source. |
| WATCHLIST_ADD → CRITICAL gate fix | MEDIUM | 1h | Exclude observational types from critical gate. |
| SENTIMENT_TURN_BEAR priority fix | LOW | 1h | Raise to HIGH for extreme sentiment. |
| Pipeline batch size increase | LOW | 0.5h | Change from 200 to 500. |
| Scientific Layer bridge | HIGH | 2-3 sprints | Full Stage 10 implementation. |
| Score/Conviction correlation < 0.3 | MEDIUM | 1 sprint | Further decouple conviction variance. |

---

## 10. Overall Score Calculation

| Category | Weight | Grade | Weighted |
|----------|--------|-------|----------|
| Collection | 15% | A (4.0) | 0.60 |
| Pipeline | 15% | B (3.0) | 0.45 |
| Scoring | 15% | B+ (3.3) | 0.50 |
| Priority | 10% | B (3.0) | 0.30 |
| Conviction | 10% | C (2.0) | 0.20 |
| Telegram | 5% | A (4.0) | 0.20 |
| Scientific | 15% | C (2.0) | 0.30 |
| CLI | 5% | A (4.0) | 0.20 |
| Data Quality | 10% | C+ (2.3) | 0.23 |
| **Total** | **100%** | | **2.98** |

**Overall Grade: B** (2.98/4.0)

---

## 11. Sprint 15 Recommendation

### Priority 1: Clean Data Foundation
1. **Run `cleanup_pre_guard_artifacts.py --execute`** to remove 63 historical artifacts
2. **Add source_id deduplication** to collector pipeline (eliminate 225 duplicates)
3. **Increase pipeline batch size** from 200 to 500 to reduce backlog

### Priority 2: Close the Learning Loop
4. **Run Stage 9 OperationalReader in COMMIT mode** to populate scientific.db
5. **Add Pipeline → Scientific bridge** (post-processing hook in Pipeline.run())
6. **Implement auto-knowledge extraction** from opportunity outcomes

### Priority 3: Fine-Tune Scoring
7. **Fix WATCHLIST_ADD → CRITICAL** gate exclusion
8. **Add conviction variance** for Yahoo/FRED events
9. **Reduce score/conviction correlation** to <0.3

### No-Go For Sprint 15
- ❌ No new collectors
- ❌ No new agents
- ❌ No execution changes
- ❌ No trading logic changes
- ❌ No EventBus changes
- ❌ No paper trading changes

---

## 12. Sprint 14 Audit Summary

| Objective | Result | Key Finding |
|-----------|--------|-------------|
| O1: Historical Cleanup | ✅ 63 artifacts identified, script ready for --execute | All at score=100, pre-guard Yahoo data |
| O2: Priority Consistency | ✅ 96.6% consistent, 6 anomalies | WATCHLIST_ADD→CRITICAL (2), SENTIMENT_TURN_BEAR under (4) |
| O3: Conviction Audit | ✅ 0.403 correlation, 29.9% unique | SHORT_SETUP: 52 opps, 1 conviction (84.0) |
| O4: Pipeline Backlog | ✅ 443 unprocessed, 225 duplicates, 115 expired | Backlog growing 58% in 24h |
| O5: Scientific Readiness | ✅ PARTIAL GO | All code complete, 0 records, Stage 10 missing |
| O6: Intelligence Report | ✅ Grade B (2.98/4.0) | 8 strengths, 5 critical weaknesses |

---

## 13. Safety Confirmation

**No execution, trading, risk, capital allocation, or database schema was modified during Sprint 14.**

All audits are **read-only**. The cleanup script requires `--execute` and is off by default.

| Area | Status |
|------|--------|
| Execution logic | ✅ Not touched |
| Trading logic | ✅ Not touched |
| Collectors | ✅ Not touched |
| Council/Agents | ✅ Not touched |
| Risk guards | ✅ Not touched |
| Paper trading | ✅ Not touched |
| EventBus | ✅ Not touched |
| Database schema | ✅ Not touched |
| Database data | ✅ Not modified (read-only audits) |
| Telegram notifier | ✅ Not touched |
| Yahoo data guard | ✅ Not touched |

---

*Report generated by Sprint 14 audit cycle. See individual reports for detail.*
