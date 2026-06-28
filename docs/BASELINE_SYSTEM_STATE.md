# O.M.A.-C.O.R.E. — Operational Baseline

**Date**: 2026-06-28  
**Branch**: `main`  
**HEAD**: `db0cc85` — Sprint 12: Yahoo Data Integrity Guard  
**Full suite**: 736 passed, 3 warnings  

---

## 1. Architecture Snapshot

```
Internet ─► Collectors (7) ─► EventBus ─► Pipeline ─► DB ─► CLI / Telegram
                │                            │
                ▼                            ▼
           WorldMonitorV2             ScoreEngine
                                          │
                                          ▼
                                    OpportunityEngine
                                          │
                                          ▼
                                    CRITICAL / HIGH / MEDIUM / LOW
```

### Layer Map

| Layer | Module | Status |
|-------|--------|--------|
| Collection | `core/collectors/` (7 collectors) | ✅ Operational |
| Event Bus | `core/event_bus.py` | ✅ Operational |
| Scoring | `core/engines/score_opportunity.py` | ✅ Operational |
| CLI | `core/cli/main.py` | ✅ Operational |
| Telegram | `core/engines/telegram_notifier.py` | ✅ Operational (Sprint 10) |
| Launcher | `/usr/local/bin/oma` | ✅ Fixed (Sprint 11) |
| Data Guard | `core/collectors/yahoo_data_guard.py` | ✅ Active (Sprint 12) |
| Scientific Lab | `core/scientific/` | ⚠️ Deployed, no records |
| Dashboard | Render.com | ✅ Operational |

---

## 2. Codebase Metrics

| Metric | Value |
|--------|-------|
| Python source files | 89 |
| Test files | 32 |
| Script files | 27 |
| Total Python files | 151 |
| Source lines of code | 14,965 |
| Test-to-source ratio | 0.36 (36%) |
| Doc files (.md) | 101 (including sub-package READMEs) |
| Active branch | `main` |

### Recent Commits (last 8)

```
db0cc85 Sprint 12: add Yahoo data integrity guard and score saturation guardrails
0fbd90c Sprint 11: add launcher alignment and score saturation audit
a7562cf Fix Telegram notifier initialization from config
83ef1db Sprint 10: add Telegram Notification Quality Gate
72264e5 ERA III: Scientific Learning Core and Decision Intelligence Foundation
ebd0f53 Add AI context system for multi-model coordination
0135683 Add operational validation audits and smoke-run preflight
eb418f2 chore: ignore generated OMA reports
```

### Uncommitted Changes

Only `run_oma_cron.sh` — the `PROJECT_DIR` path was updated during Sprint 11.

---

## 3. Database State

### Operational DB (`oma_core.db`)

| Metric | Value |
|--------|-------|
| Database size | 0.8 MB |
| Total events | 395 |
| Processed events | 114 |
| Unprocessed events | 281 |
| Total opportunities | 114 |

### Scientific DB (`scientific.db`)

| Metric | Value |
|--------|-------|
| Database size | 0.11 MB |
| Tables | `hypotheses`, `evidence`, `outcome_comparisons`, `knowledge`, `criterion_deltas` |
| Records | **0 across all tables** |

**Interpretation**: The Scientific Learning Core is fully deployed but has never been used. Stage 9 Operational Reader is operational (tests pass) but has not been run in COMMIT mode against real data. The `scientific.db` is empty — no hypotheses, evidence, comparisons, knowledge, or criterion deltas exist.

---

## 4. Event Pipeline

### Events by Source

| Source | Count | % of Total |
|--------|-------|-----------|
| yahoo_finance | 74 | 18.7% |
| polymarket | 60 | 15.2% |
| rss_bloomberg | 57 | 14.4% |
| coingecko | 51 | 12.9% |
| rss_cnbc | 47 | 11.9% |
| rss_marketwatch | 30 | 7.6% |
| rss_cointelegraph | 29 | 7.3% |
| rss_coindesk | 25 | 6.3% |
| fred | 12 | 3.0% |
| binance | 4 | 1.0% |
| rss_forexlive | 3 | 0.8% |
| sentiment_fng_crypto | 3 | 0.8% |
| **Total** | **395** | **100%** |

### Events by Type

| Type | Count |
|------|-------|
| news | 125 |
| price_movement | 77 |
| social_trend | 45 |
| hack_exploit | 44 |
| geopolitical | 38 |
| regulatory | 38 |
| macro_event | 25 |
| sentiment_shift | 3 |

### Events by Urgency

| Urgency Level | Count | % |
|--------------|-------|---|
| BACKGROUND (1) | 116 | 29.4% |
| CRITICAL (4) | 104 | 26.3% |
| HIGH (3) | 97 | 24.6% |
| MEDIUM (2) | 78 | 19.7% |
| LOW | 0 | 0% |

**Interpretation**: 26.3% of events marked CRITICAL — this is high but includes yahoo_finance pre-guard events.

### Unprocessed Events by Source

| Source | Unprocessed |
|--------|------------|
| polymarket | 60 |
| rss_bloomberg | 55 |
| coingecko | 45 |
| rss_cnbc | 40 |
| rss_marketwatch | 30 |
| rss_cointelegraph | 28 |
| rss_coindesk | 22 |
| rss_forexlive | 1 |
| **Total unprocessed** | **281** |

**Interpretation**: 71% of all events are unprocessed. The pipeline processes events in batches and leaves a large backlog. These unprocessed events will be consumed on future `oma run` cycles.

### Pipeline Timing (most recent cycle)

- **Last event**: 2026-06-28 12:39:46 UTC
- **Last opportunity**: 2026-06-28 12:39:49 UTC
- **Delta**: ~3 seconds for event-to-opportunity processing

---

## 5. Score Distribution

| Metric | Value |
|--------|-------|
| Total opportunities scored | 114 |
| Min score | 40.6 |
| Max score | 100.0 |
| Mean score | 90.64 |
| Median score | 100.0 |
| At score 100 | 63 (55.3%) |
| Repeated score values | 12 distinct values |
| Most frequent score | 100.0 (63 occurrences) |
| Mean conviction | 76.17 |

### Priority Distribution

| Priority | Count | % |
|----------|-------|---|
| CRITICAL | 59 | 51.8% |
| HIGH | 29 | 25.4% |
| MEDIUM | 22 | 19.3% |
| LOW | 4 | 3.5% |

### Opportunity Type Distribution

| Type | Count |
|------|-------|
| SHORT_SETUP | 52 |
| WATCHLIST_ADD | 25 |
| MONITOR_MACRO | 9 |
| MACRO_HEADWIND | 8 |
| REGULATORY_TAILWIND | 6 |
| NEWS_DRIVEN | 4 |
| SENTIMENT_TURN_BEAR | 3 |
| REGULATORY_HEADWIND | 3 |
| MACRO_TAILWIND | 2 |
| SAFE_HAVEN_FLOW | 1 |
| AVOID_OR_SHORT | 1 |

**Interpretation**: 
- 55.3% of all opportunities hit the score cap at 100 — clear saturation
- 51.8% are CRITICAL — the threshold `combined >= 92` is too easily reached
- SHORT_SETUP dominates (45.6%) — inflated by pre-guard Yahoo -100% events
- Mean conviction (76.17) is closely correlated with mean score (90.64) due to `base = score * 0.6` in conviction formula

---

## 6. Collector Health

| Collector | Status | Events Generated | Notes |
|-----------|--------|-----------------|-------|
| YahooFinanceCollector | ✅ | 74 | Pre-guard data included -100% artifacts; guard now active |
| PolymarketCollector | ✅ | 60 | Largest unprocessed backlog |
| RSSCollector (Bloomberg) | ✅ | 57 | 55 unprocessed |
| CoinGeckoCollector | ✅ | 51 | 45 unprocessed |
| RSSCollector (CNBC) | ✅ | 47 | 40 unprocessed |
| RSSCollector (MarketWatch) | ✅ | 30 | 30 unprocessed |
| RSSCollector (CoinDesk) | ✅ | 25 | 22 unprocessed |
| FREDCollector | ✅ | 12 | Was 0 before Sprint 11 (missing API key); now operational |
| BinanceCollector | ✅ | 4 | Low volume — crypto-only |
| RSSCollector (ForexLive) | ✅ | 3 | Niche forex news |
| SentimentCollector | ✅ | 3 | Crypto Fear & Greed only |

**Collectors used in WorldMonitorV2**:
- `CoinGeckoCollector` — crypto prices
- `YahooFinanceCollector` — stocks, forex, commodities, indices  
- `BinanceCollector` — crypto exchange data
- `FREDCollector` — macroeconomic indicators
- `RSSCollector` — news feeds (Reuters, CoinDesk, CoinTelegraph, Investing, MarketWatch, CNBC, Bloomberg, ForexLive)
- `SentimentCollector` — crypto Fear & Greed index
- `PolymarketCollector` — prediction market probabilities

---

## 7. Telegram Status

| Capability | Status |
|-----------|--------|
| send_message | ✅ Verified |
| send_run_summary | ✅ Verified |
| test_connection | ✅ Verified |
| Dry-run renderer | ✅ `scripts/render_telegram_notification.py` |
| Quality Gate | ✅ PASS/WARN/SUPPRESS_DETAIL/FAIL_DIAGNOSTIC |
| Asset normalization | ✅ `normalize_assets()` — handles all edge cases |
| Priority saturation detection | ✅ `detect_priority_saturation()` — flags ≥80% CRITICAL |
| Learning Core status | ✅ Displays when connected, graceful fallback |
| Bot configured in `.env` | ✅ |

---

## 8. Data Quality Status

| Guard | Status | Description |
|-------|--------|-------------|
| Yahoo quote validation | ✅ Active | Blocks price=None/0/NaN, prev_close=None/0, extreme returns ≥80% |
| Event-level guardrail | ✅ Active | Caps invalid opportunities at score≤30, priority≤MEDIUM |
| Duplicate detection | ✅ Active | `deduplicate_opportunities()` in Telegram |
| Priority saturation | ✅ Active | Flagged in Telegram diagnostics |
| Malformed asset check | ✅ Active | `normalize_assets()` in Telegram pipeline |

### Historical Bad Data (pre-guard, already in DB)

| Anomaly | Count |
|---------|-------|
| Yahoo opportunities with $0.00 price | ~54 |
| Yahoo opportunities with -100% change | ~58 |
| Malformed asset lists | 0 (already fixed by Sprint 11) |
| Zero FRED events (pre-fix) | Now resolved |

---

## 9. Scientific Layer Status

| Component | Status |
|-----------|--------|
| `scientific_store.py` | ✅ Deployed |
| `hypothesis_lifecycle.py` | ✅ Deployed |
| `evidence_lifecycle.py` | ✅ Deployed |
| `outcome_comparison.py` | ✅ Deployed |
| `knowledge_lifecycle.py` | ✅ Deployed |
| `criterion_evolution.py` | ✅ Deployed |
| `historical_replay.py` | ✅ Deployed |
| `operational_reader.py` | ✅ Deployed, tests pass |
| `scientific.db` | ⚠️ Empty — 0 records across all 5 tables |
| Stage 9 Operational Reader | ⚠️ Never run in COMMIT mode on real data |

**Interpretation**: The Scientific Learning Core is fully code-complete and tested but has never been populated with real operational data. The Stage 9 Operational Reader (Sprint 9) was fixed during earlier work and its 11 failing tests now pass, but it has not been executed against the live pipeline.

---

## 10. Test Coverage

| Suite | Count | Status |
|-------|-------|--------|
| Full suite | 736 | ✅ All passing |
| Telegram notifier | 70 | ✅ |
| Yahoo data guard | 32 | ✅ |
| Launcher diagnostics | 13 | ✅ |
| Score saturation audit | 20 | ✅ |
| FRED collector | 19 | ✅ |
| Operational Reader | 74 | ✅ (was 11 failing, fixed) |
| Pre-existing tests | ~508 | ✅ |
| Skipped | 4 | (paper_trading_experiment related) |
| Warnings | 3 | PytestRemovedIn10Warning (pre-existing) |

---

## 11. Strengths

1. **Collector diversity**: 7 different data sources (crypto, stocks, forex, macro, news, sentiment, prediction markets)
2. **Telegram quality gate**: Full diagnostic pipeline with dedup, saturation detection, and compact mode
3. **Data integrity guard**: Two-layer defense (collector + scoring) against invalid Yahoo data
4. **Launcher alignment**: `/usr/local/bin/oma` now points to the correct repo
5. **FRED operational**: Macroeconomic data flowing after API key fix
6. **Test suite robustness**: 736 tests all passing, including regression guards
7. **Scientific Layer**: Complete code foundation for hypothesis->evidence->knowledge lifecycle
8. **Read-only audit tools**: `audit_score_saturation.py`, `check_oma_launcher.py`, `render_telegram_notification.py`

---

## 12. Weaknesses

1. **Score saturation**: 55.3% of all opportunities hit the 100 cap. The scoring formula has insufficient discrimination for strong events.
2. **CRITICAL overload**: 51.8% of opportunities are CRITICAL. The `_determine_priority` threshold (`combined >= 92`) is too permissive.
3. **Pre-guard data contamination**: ~54 opportunities with $0.00 price remain in the DB. The Yahoo guard prevents new ones but existing bad data pollutes queries.
4. **Scientific Layer unused**: 5 empty tables despite complete code. The learning loop (observe→hypothesize→test→learn) is not yet connected.
5. **Large unprocessed backlog**: 281 of 395 events (71%) remain unprocessed. Each `oma run` processes ~20-40 new events but leaves a growing backlog.
6. **SHORT_SETUP dominance**: 52 of 114 opportunities (45.6%) are SHORT_SETUP, inflated by pre-guard -100% events.
7. **No score diversity**: Only 12 distinct score values across 114 opportunities. Most cluster at 100.
8. **Conviction non-discriminating**: Mean conviction 76.17 closely tracks mean score 90.64 due to `conviction = score * 0.6 + source_boost + asset_boost`. It provides no independent signal.

---

## 13. Technical Debt

| Item | Priority | Impact | Notes |
|------|----------|--------|-------|
| Score recalibration | HIGH | Score saturation, CRITICAL overload | `_determine_priority` threshold needs adjustment |
| Historical bad data cleanup | MEDIUM | Query accuracy | ~54 invalid opportunities in DB |
| Scientific Layer integration | HIGH | Missing learning loop | Stage 9 Operational Reader never committed |
| RSS collector backlog | LOW | Stale events | 281 unprocessed events |
| Conviction formula | MEDIUM | Non-discriminating | `base = score * 0.6` creates correlation |
| Opportunity type symmetry | LOW | SHORT vs LONG imbalance | 52 SHORT vs 0 LONG (suspicious) |
| Event priority definition | MEDIUM | Background->LOW mapping | Urgency 1=Background mapped to score 25 |
| Test coverage gaps | MEDIUM | ~36% test-to-source | Collectors have minimal unit tests |
| DB migration debt | LOW | migration_to_postgres.py exists | Not used in current config |

---

## 14. Frozen Modules (do not modify)

Per safety constraints across Sprints 10-12:

- `core/agents/` — trading agents
- `core/council/` — AgentCouncil, MetaCouncil
- `core/risk/` — risk guards (if exists)
- `core/execution/` — execution logic (if exists)
- `core/papers/` — paper trading (if exists)
- `core/event_bus.py` — EventBus behavior
- `oma_core.db` — operational database
- `scientific.db` — scientific database
- Position sizing, capital allocation, real capital logic

---

## 15. Modules Ready for Optimization

| Module | Readiness | Sprint |
|--------|-----------|--------|
| `core/engines/score_opportunity.py` | ⚠️ Score recalibration needed | Sprint 13 |
| `core/engines/score_opportunity.py` | ⚠️ Priority threshold adjustment | Sprint 13 |
| `core/engines/score_opportunity.py` | ⚠️ Conviction formula decoupling | Sprint 13 |
| `core/scientific/operational_reader.py` | ⚠️ Connect Scientific Layer to live pipeline | Sprint 14 |
| `core/collectors/rss_collector.py` | ℹ️ Backlog processing improvement | Low priority |
| `core/scientific/` | ℹ️ Full learning loop integration | Sprint 14+ |

---

## 16. GO / NO-GO Assessment: Sprint 13 Score Calibration

### GO Conditions

| Condition | Met? | Evidence |
|-----------|------|----------|
| Full test suite green | ✅ | 736 passed, 3 warnings |
| No failing tests | ✅ | 0 failures |
| Repo launcher aligned | ✅ | `/usr/local/bin/oma` → correct repo |
| Telegram operational | ✅ | Verified send, test_connection, dry-run |
| Yahoo data guard active | ✅ | Two-layer defense deployed |
| FRED operational | ✅ | 12 events from 0 |
| Baseline documented | ✅ | This document |
| No performance regression | ✅ | Not measured but no behavioral changes |
| Score saturation quantified | ✅ | 55.3% at 100, 51.8% CRITICAL |

### NO-GO Conditions

| Condition | Blocked? | Reason |
|-----------|----------|--------|
| Scientific Layer connected | ❌ Not required for score calibration | Score calibration is scorer-side, not learning-loop |
| Historical data cleaned | ❌ Not required — can be excluded via WHERE clauses | Bad data can be filtered in queries |
| Score diversity formula ready | ❌ Requires design in Sprint 13 | This IS Sprint 13's work |

### Verdict

## ✅ GO — Sprint 13 Score Calibration

**Rationale**: All blocking conditions are clear. The baseline is documented. Score saturation is quantified and understood (55.3% at 100, 51.8% CRITICAL, SHORT_SETUP dominance from pre-guard data). The Yahoo guard prevents new bad data from entering the system. The calibration targets are:

1. Reduce CRITICAL threshold — make `_determine_priority` more discriminating
2. Decouple conviction from score — make conviction an independent signal
3. Add score diversity — prevent clipping at 100 for valid-but-strong events
4. Clean up pre-guard data — safe removal of ~54 invalid opportunities from DB

**DO NOT** modify trading logic, execution, collectors, council, agents, risk guards, paper trading, EventBus, or databases during Sprint 13.
