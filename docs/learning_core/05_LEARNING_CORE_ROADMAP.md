# Learning Core Roadmap

*Version 1.0 — June 2026*
*From current USB state to working Learning Core*

---

## Context

The Learning Core is the set of components that turn experience into better Criterion. It spans Layers 5–12 of the Architecture V2 layered model:

- Layer 5: Reasoning Engine
- Layer 6: Scientific Layer (Hypothesis + Evidence — exists)
- Layer 10: Outcome Bridge
- Layer 11: Validated Knowledge
- Layer 12: Criterion Evolution

The following roadmap stages move from the current USB state to a working Learning Core without destabilizing the operational MVP. Each stage has a clear objective, risk assessment, validation gate, and go/no-go condition.

---

## Stage 0 — Current State

| Aspect | Status | Details |
|--------|--------|---------|
| Hypothesis schema | Implemented | `core/schemas/hypothesis_schema.py` — 6 fields, 4-state lifecycle |
| Evidence schema | Implemented | `core/schemas/evidence_schema.py` — direction, weight, source, lifecycle |
| Scientific Store | Implemented | `core/scientific/scientific_store.py` — separate SQLite, full CRUD |
| Missed Opportunity System | Spec exists | `docs/scientific/01_MISSED_OPPORTUNITY_SYSTEM.md` — not implemented |
| Architecture V2 | Published | `docs/ARCHITECTURE_V2.md` — canonical reference |
| Innovation Engine | Published | `docs/innovation/` — full innovation management |
| Learning Core docs | Not yet | This sprint creates them |
| Reasoning Engine | None | Not designed, not implemented |
| Knowledge Object | None | Not designed, not implemented |
| Criterion Evolution | None | Not designed, not implemented |
| Outcome Bridge | None | Not designed, not implemented |
| Tests | 303 passing | 23 scientific layer tests |
| Operational MVP | Running | Extended Demo on laptop version |

**Key constraint:** The operational MVP must continue running on the laptop version throughout all stages.

---

## Stage 1 — Knowledge Object Spec

**Objective:** Design the Knowledge Object — what it means for O.M.A.-C.O.R.E. to "know" something.

**Files affected:**
- `docs/learning_core/02_KNOWLEDGE_OBJECT.md` ✅ Created
- No code changes

**Risk level:** None (documentation only)

**Validation gate:** Document reviewed and accepted. Must be internally consistent with Hypothesis schema, Evidence schema, and Missed Opportunity System spec.

**What must NOT be touched:**
- No code in core/
- No tests
- No databases
- No schemas

**Estimated effort:** Already completed as part of this sprint.

**Go/no-go condition:** Document is complete and consistent. GO.

---

## Stage 2 — Reasoning Engine Spec

**Objective:** Design how Events become Hypotheses. The Reasoning Engine wraps agent outputs into testable hypotheses.

**Files affected:**
- `docs/learning_core/01_REASONING_ENGINE.md` ✅ Created
- No code changes

**Risk level:** None (documentation only)

**Validation gate:** Document reviewed and accepted. Must describe the full pipeline from Event to Hypothesis candidate. Must define falsifiability requirements, novelty/duplicate detection, and filter criteria.

**What must NOT be touched:**
- No code in core/
- No tests
- No databases
- No schemas

**Estimated effort:** Already completed as part of this sprint.

**Go/no-go condition:** Document is complete and consistent. GO.

---

## Stage 3 — Outcome Bridge Spec

**Objective:** Design how outcomes (executed and missed) are compared to hypotheses and produce verdicts.

**Files affected:**
- `docs/learning_core/04_OUTCOME_BRIDGE.md` ✅ Created
- No code changes

**Risk level:** None (documentation only)

**Validation gate:** Document reviewed and accepted. Must define verdict taxonomy, error taxonomy, comparison method, and integration points with PaperTrading and Missed Opportunity System.

**What must NOT be touched:**
- No code in core/
- No tests
- No databases
- No schemas

**Estimated effort:** Already completed as part of this sprint.

**Go/no-go condition:** Document is complete and consistent. GO.

---

## Stage 4 — Criterion Evolution Spec

**Objective:** Design how Criterion changes over time — measurable dimensions, delta rules, minimum evidence thresholds.

**Files affected:**
- `docs/learning_core/03_CRITERION_EVOLUTION.md` ✅ Created
- No code changes

**Risk level:** None (documentation only)

**Validation gate:** Document reviewed and accepted. Must clearly establish Criterion as emergent (not a component). Must define measurable dimensions and minimum evidence thresholds.

**What must NOT be touched:**
- No code in core/
- No tests
- No databases
- No schemas

**Estimated effort:** Already completed as part of this sprint.

**Go/no-go condition:** Document is complete and consistent. GO.

---

## Stage 5 — Minimal Schemas

**Objective:** Create the minimal schema/object definitions needed to start implementing the Learning Core.

**Files affected:**
- `core/schemas/knowledge_schema.py` — Knowledge dataclass and SQL table
- `core/schemas/outcome_comparison_schema.py` — OutcomeComparison dataclass and SQL table
- `core/schemas/criterion_delta_schema.py` — CriterionDelta dataclass and SQL table
- `core/schemas/__init__.py` — exports

**Risk level:** LOW — new schemas in `core/schemas/`, no existing module modified (except `__init__.py` for exports)

**Validation gate:** Unit tests on schema creation, serialization, deserialization, field validation. All existing 303 tests continue to pass.

**What must NOT be touched:**
- No trading logic
- No execution code
- No agents
- No council
- No collectors
- No existing operational schemas (Event, Trade, Agent, CouncilDecision)
- No existing scientific schemas (Hypothesis, Evidence)
- No existing `oma_core.db`

**Estimated effort:** 1–2 days for all three schemas

**Go/no-go condition:** All spec documents (Stages 1–4) are accepted. GO.

---

## Stage 6 — Tests

**Objective:** Write tests for the new schemas and their lifecycles, before any implementation logic is written.

**Files affected:**
- `tests/test_learning_core.py` — New test file

**Risk level:** LOW — tests only, no implementation code yet

**Validation gate:** All tests pass. Tests cover:
- Knowledge lifecycle (EXTRACTED → PROVISIONAL → VALIDATED → ...)
- OutcomeComparison creation, verdict assignment, error classification
- CriterionDelta creation, evidence thresholds
- Integration: Knowledge ← OutcomeComparison ← Hypothesis

**What must NOT be touched:**
- No trading logic
- No execution code
- No agents
- No council
- No collectors
- No existing test files

**Estimated effort:** 1–2 days

**Go/no-go condition:** Stage 5 complete (schemas exist). GO.

---

## Stage 7 — CLI-Only Manual Workflow

**Objective:** Implement the Learning Core as CLI commands only — no automation, no pipeline integration. The user manually runs commands to create knowledge, compare outcomes, and view Criterion metrics.

**Files affected:**
- `core/scientific/knowledge_lifecycle.py` — Knowledge state machine
- `core/scientific/outcome_comparison.py` — Outcome comparison logic
- `core/scientific/criterion_evolution.py` — Criterion delta logic
- `core/cli/main.py` — New CLI commands (additive)
- No operational code changes

**Risk level:** LOW-MEDIUM — new modules only, CLI changes are additive. All existing functionality preserved.

**Validation gate:** CLI commands work correctly. User can:
- Create Knowledge from comparison results
- Compare an outcome to a hypothesis manually
- View Criterion metrics
- All existing 303 tests pass

**What must NOT be touched:**
- No trading logic
- No execution code
- No agents
- No council
- No collectors
- No opertional database
- No automated pipeline integration

**Estimated effort:** 4–6 days

**Go/no-go condition:** Stages 5–6 complete. GO.

---

## Stage 8 — Historical Replay

**Objective:** Run the Learning Core on historical data (from telemetry, stored trades, past signals) to validate that it produces useful knowledge and meaningful Criterion metrics.

**Files affected:**
- New replay script (not in core/) or Jupyter notebook
- No operational code changes

**Risk level:** LOW — replay is read-only. It reads historical data but does not write.

**Validation gate:** Replay produces:
- Knowledge items that appear plausible and useful
- Criterion metrics that show trends (even if noisy)
- Error type distributions that make sense
- No crashes, no infinite loops, no data corruption

**What must NOT be touched:**
- No operational code
- No databases (read-only)
- No pipeline integration

**Estimated effort:** 2–3 days

**Go/no-go condition:** Stage 7 complete. GO.

---

## Stage 9 — Read-Only Operational Integration

**Objective:** Connect the Learning Core to the operational pipeline as a read-only observer. The Outcome Bridge starts reading trade outcomes automatically. The Reasoning Engine starts reading events and agent opinions.

**Files affected:**
- Read-only hooks in event processing pipeline
- Outcome Bridge reads from PaperTradingEngine (trade close events)
- Reasoning Engine reads from EventBus (event + agent opinion topics)
- No writes from these hooks

**Risk level:** MEDIUM — first integration with operational pipeline. Must be read-only with strict boundaries.

**Validation gate:**
- Reasoning Engine produces hypotheses from real events (user reviews and approves before they enter the store)
- Outcome Bridge produces comparisons from real trade outcomes
- No operational latency increase (>1ms per read-only operation)
- All existing 303 tests pass
- Laptop version continues running without interruption

**What must NOT be touched:**
- No writes to operational modules
- No changes to trade execution
- No changes to agents or council logic
- No changes to collectors
- No changes to guard layers

**Estimated effort:** 5–7 days

**Go/no-go condition:** Stage 8 validation shows Learning Core produces meaningful output. GO.

---

## Stage 10 — Cockpit Visibility

**Objective:** Add Learning Core metrics to the Terminal Cockpit (IN-007). The user can see:
- Active hypotheses and their status
- Recent outcome comparisons
- Knowledge items extracted
- Criterion dimension trends
- Missed Opportunity summary

**Files affected:**
- `core/cli/main.py` — New display commands
- No operational code changes

**Risk level:** LOW — CLI display changes only

**Validation gate:** New commands display correct data from the Scientific Store and Learning Core tables.

**What must NOT be touched:**
- No trading logic
- No execution code
- No agents, council, collectors
- No pipeline integration

**Estimated effort:** 2–3 days

**Go/no-go condition:** Stage 9 complete (data flowing). GO.

---

## Stage 11 — Decision Approval Readiness

**Objective:** Evaluate whether the system has enough evidence to begin designing the Decision Approval Engine (ARCHITECTURE V2 Layer 8). This is NOT implementing the Approval Engine — it is assessing readiness.

**Files affected:**
- `docs/approval/READINESS_ASSESSMENT.md` — New document
- No code changes

**Risk level:** None (documentation)

**Validation gate:** Assessment document answers:
- How many hypotheses have been evaluated?
- How many outcomes have been compared?
- What is the calibration score?
- What is the error recurrence rate?
- Is there sufficient evidence to begin Approval Engine design?

**Minimum thresholds for YES (from `03_CRITERION_EVOLUTION.md` §18):**
- 50+ evaluated hypotheses
- 30+ outcomes with completed comparisons
- Confirmation rate between 30% and 70%
- Calibration Brier score < 0.3
- Knowledge yield > 0.3 per outcome
- No single error type > 40%

**What must NOT be touched:**
- No operational pipeline
- No execution changes
- No agents, council, collectors

**Estimated effort:** 1 day

**Go/no-go condition:** Stage 9 complete, minimum evidence thresholds met. GO for Approval Engine design (NOT implementation).

---

## Implementation Clock Diagram

```
Now (spec phase)
    │
    ├── Stage 1: Knowledge spec ────── 0d (done)
    ├── Stage 2: Reasoning spec ────── 0d (done)
    ├── Stage 3: Outcome Bridge spec ── 0d (done)
    ├── Stage 4: Criterion spec ─────── 0d (done)
    │
    ├── Stage 5: Minimal schemas ────── 1-2d
    ├── Stage 6: Tests ──────────────── 1-2d
    ├── Stage 7: CLI manual workflow ── 4-6d
    ├── Stage 8: Historical replay ──── 2-3d
    ├── Stage 9: Read-only integration ─ 5-7d
    ├── Stage 10: Cockpit visibility ─── 2-3d
    └── Stage 11: Approval readiness ─── 1d
                                        ─────
                    Total spec phase:   0d (done)
                    Total impl phase:  16-23d
                    Total post-impl:    1d
                    ─────
                    Grand total:       17-24d to working Learning Core
```

---

## Risk Summary

| Risk | Stage | Likelihood | Impact | Mitigation |
|------|-------|------------|--------|------------|
| **Operational pipeline destabilization** | 9 | Low | Critical | Read-only hooks only. Strict boundaries. Test on USB before laptop integration. |
| **Learning Core produces no useful knowledge** | 8 | Medium | High | Historical replay reveals this early. If useless, redesign before investing in Stages 9-11. |
| **Schema changes require scientific.db migration** | 5 | Low | Medium | Scientific.db is separate and USB-only. Migration affects nothing operational. |
| **One-person maintainability exceeded** | 7-10 | Low | Medium | Monitor cognitive load. If Learning Core becomes too complex, simplify before Stage 9. |
| **Tests become flaky due to Learning Core integration** | 9 | Medium | Medium | Keep Learning Core tests independent from existing tests. No shared test fixtures. |

---

## Recommended First Implementation After Specs

**The recommended first implementation step is Stage 5 — Minimal Schemas.**

Rationale:
1. Specs are now complete (Stages 1-4 of this sprint)
2. Schemas are the foundation everything else builds on
3. No operational risk (new files only)
4. Quick validation (1-2 days)
5. Unblocks all subsequent stages

The first schema to implement should be **OutcomeComparison**, followed by **Knowledge**, followed by **CriterionDelta**. This order reflects the data flow: outcomes are compared first, knowledge is extracted from comparisons, and Criterion deltas are derived from knowledge.

---

## Summary

| Stage | Name | Effort | Risk | Go/No-Go |
|-------|------|--------|------|----------|
| 0 | Current state | — | — | — |
| 1 | Knowledge spec | 0d (done) | None | GO |
| 2 | Reasoning spec | 0d (done) | None | GO |
| 3 | Outcome Bridge spec | 0d (done) | None | GO |
| 4 | Criterion Evolution spec | 0d (done) | None | GO |
| 5 | Minimal schemas | 1-2d | LOW | After specs accepted |
| 6 | Tests | 1-2d | LOW | After schemas |
| 7 | CLI manual workflow | 4-6d | LOW-MED | After tests |
| 8 | Historical replay | 2-3d | LOW | After CLI |
| 9 | Read-only operational integration | 5-7d | MEDIUM | After replay validated |
| 10 | Cockpit visibility | 2-3d | LOW | After integration |
| 11 | Decision Approval readiness | 1d | None | After Criterion data exists |
| **Total** | | **16-23d impl** | | |

---
