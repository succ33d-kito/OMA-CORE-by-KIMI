# Scientific Layer Readiness Report

**Date**: 2026-06-28  
**Assessor**: Sprint 14 Audit  

---

## 1. Architecture Position

The Scientific Layer implements the **Criterion Laboratory** — an isolated scientific memory that is designed to observe the operational pipeline without interfering with it. It lives at `core/scientific/` with a separate database (`scientific.db`) and its own schema.

```
Operational Pipeline (oma_core.db)    Scientific Layer (scientific.db)
┌─────────────────────────────┐      ┌──────────────────────────────┐
│ Collectors → Events → Opps  │      │ Hypotheses → Evidence →     │
│ ScoreEngine → Priority      │◄────►│ Outcome → Knowledge →       │
│ TelegramNotifier            │ read │ Criterion Deltas            │
│ CLI (oma)                   │ only │ CLI (oma)                   │
└─────────────────────────────┘      │ scripts/ offline tools      │
                                     └──────────────────────────────┘
```

---

## 2. Stage Completeness

| Stage | Module | Status | Lines | Tests | Notes |
|-------|--------|--------|-------|-------|-------|
| Stage 7a — Hypothesis Lifecycle | `hypothesis_lifecycle.py` | ✅ Complete | 64 | ✅ | State machine: FORMULATED→ACTIVE→EVALUATED→ARCHIVED |
| Stage 7b — Evidence Lifecycle | `evidence_lifecycle.py` | ✅ Complete | 75 | ✅ | State machine: COLLECTED→ACTIVE→EXPIRED/SUPERSEDED |
| Stage 7c — Outcome Comparison | `outcome_comparison.py` | ✅ Complete | 144 | ✅ | Auto-detect verdict, classify error |
| Stage 7d — Knowledge Lifecycle | `knowledge_lifecycle.py` | ✅ Complete | 222 | ✅ | EXTRACTED→PROVISIONAL→VALIDATED/REVISED/INVALIDATED→ARCHIVED |
| Stage 7e — Criterion Evolution | `criterion_evolution.py` | ✅ Complete | 158 | ✅ | 8 dimensions, NEVER auto-applied |
| Stage 7f — Scientific Store | `scientific_store.py` | ✅ Complete | 508 | ✅ | Full CRUD for all 5 entity types |
| Stage 8 — Historical Learning Replay | `historical_replay.py` | ✅ Complete | 517 | ✅ | Offline replay engine + CLI script |
| Stage 9 — Operational Reader | `operational_reader.py` | ✅ Complete | 962 | ✅ | AUDIT/DRY_RUN/COMMIT modes + CLI script |
| **Stage 10 — Auto-Learning Pipeline** | — | ❌ **MISSING** | 0 | ❌ | **No code exists** |

---

## 3. CLI Integration

| Command | Status | Notes |
|---------|--------|-------|
| `oma hypothesis` | ✅ | Create, list, show, transition, archive |
| `oma evidence` | ✅ | Add evidence, list |
| `oma scientific` | ✅ | Show stats |
| `oma lab compare` | ✅ | Compare hypothesis to outcome |
| `oma lab knowledge` | ✅ | List, show, extract, transition |
| `oma lab criterion` | ✅ | List, propose, apply, reject, metrics |
| `scripts/historical_learning_replay.py` | ✅ | Offline batch tool |
| `scripts/read_only_operational_integration.py` | ✅ | Read-only integration tool |

---

## 4. Missing Connectors

### Critical Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| **Pipeline → Scientific bridge** | No automated learning from pipeline results | Need `Pipeline.run()` to call Stage 9 OperationalReader in DRY_RUN mode |
| **Event → Hypothesis mapping** | No hypotheses are auto-generated from events | Need a mapping layer between Event → Hypothesis |
| **Outcome → Knowledge extraction** | No automated knowledge extraction from opportunity outcomes | Need post-pipeline hook to extract knowledge |
| **Score recalibration feedback loop** | ScoreEngine doesn't use Scientific Layer insights | No mechanism to feed criterion deltas back into scoring thresholds |
| **Telemetry → Evidence** | No evidence logging from pipeline execution | Need telemetry bridge |

### Minor Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| No persistent hypothesis from new events | Scientific DB stays empty | Manual CLI commands needed |
| No auto-comparison of past opportunities | No outcome tracking | Requires storing actual outcomes |
| No automated criterion delta proposal | No scoring improvement loop | Human-in-the-loop via CLI only |

---

## 5. Data Status

| Table | Records | Last Write | Status |
|-------|---------|------------|--------|
| `hypotheses` | **0** | Never | 🟡 Empty |
| `evidence` | **0** | Never | 🟡 Empty |
| `outcome_comparisons` | **0** | Never | 🟡 Empty |
| `knowledge` | **0** | Never | 🟡 Empty |
| `criterion_deltas` | **0** | Never | 🟡 Empty |

**Interpretation**: `scientific.db` is fully deployed, properly connected, and ready for use. It has never been populated because:
- No automated bridge connects the pipeline to the Scientific Layer
- CLI commands require manual invocation
- Stage 9 OperationalReader has never been run in COMMIT mode
- Stage 8 HistoricalReplay requires external trade data

---

## 6. Telegram Integration Status

The Telegram notifier (`telegram_notifier.py:268`) has a `get_learning_core_stats()` function that lazily imports `ScientificStore` and queries `outcome_comparisons`, `knowledge`, and `criterion_deltas` counts for display. Currently all display as `0`. The integration is:
- ✅ Optional (graceful fallback if import fails)
- ✅ Read-only display only
- ❌ **Never shows non-zero values** due to empty database

---

## 7. Test Coverage

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/test_scientific_layer.py` | ~20 | ✅ |
| `tests/test_lab.py` | ~60 | ✅ |
| `tests/test_historical_learning_replay.py` | ~30 | ✅ |
| `tests/test_read_only_operational_integration.py` | ~40 | ✅ |
| **Pipeline integration tests** | **0** | ❌ |

There are no integration tests that connect the operational pipeline to the Scientific Layer. This is consistent with the current architecture (no bridge exists yet).

---

## 8. Readiness Verdict

| Component | Ready? | Condition |
|-----------|--------|-----------|
| State machines (5 lifecycles) | ✅ GO | Fully coded, tested, and deployed |
| Persistence (scientific_store) | ✅ GO | CRUD complete, 5 tables defined |
| Offline learning tools | ✅ GO | Historical replay + operational reader scripts exist |
| CLI interface | ✅ GO | 6 command groups, all functional |
| Telegram readout | ✅ GO | Display integration exists |
| Database deployment | ✅ GO | `scientific.db` exists, schema created |
| Automated learning loop | ❌ NO GO | Stage 10 not implemented |
| Pipeline integration bridge | ❌ NO GO | No connector code exists |
| ScoreEngine ↔ Scientific feedback | ❌ NO GO | No mechanism to use criterion insights |

---

## 9. Roadmap to GO

| Step | Effort | Priority | Description |
|------|--------|----------|-------------|
| 1. Run Stage 9 in COMMIT mode | Low | Immediate | Execute OperationalReader against existing oma_core.db to populate initial hypotheses |
| 2. Create Pipeline → Scientific bridge | Medium | Sprint 15 | Add post-processing hook in `score_opportunity.py` to call OperationalReader in DRY_RUN mode |
| 3. Auto-extract knowledge from outcomes | Medium | Sprint 15 | Track opportunity outcomes and extract knowledge automatically |
| 4. Feedback score calibration from criterion | High | Sprint 16 | Use criterion delta insights to adjust scoring thresholds |
| 5. Implement Stage 10 Auto-Learning Pipeline | High | Sprint 17 | Full automated learning loop |

---

## 10. Overall Verdict

# PARTIAL GO

**The Scientific Layer is code-complete, tested, and deployed. It is ready for integration but has never been populated with real data. The automated learning loop (Stage 10) does not exist.**

All state machines, persistence, CLI commands, and offline tools are fully functional. The missing piece is a bridge from the operational pipeline into the Scientific Layer. Once that bridge exists, the Scientific Layer can begin accumulating data immediately.
