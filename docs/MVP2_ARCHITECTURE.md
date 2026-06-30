# MVP v2 Architecture

## Integrating the Scientific Layer into the Operational MVP

*Version 1.0 — June 2026*

---

## 1. Executive Summary

MVP v2 is the integration of the current operational MVP (a working event-to-action signal engine) with the Scientific Layer developed in the USB candidate version (hypothesis lifecycle, evidence tracking, scientific memory).

The core innovation is a new chain:

```
Event → Hypothesis → Evidence → Decision → Outcome → Validated Knowledge → Criterion
```

This chain replaces the older conceptual chain (`Event → Evidence → Hypothesis`) because evidence is meaningless without a hypothesis to support or contradict, and learning cannot occur without the full arc from hypothesis formation through outcome comparison to knowledge extraction.

MVP v2 does **not** modify the operational pipeline. Collectors continue ingesting. Agents continue forming opinions. The Council continues voting. PaperTrading continues executing. The Scientific Layer runs in parallel — isolated in its own database, its own package, its own lifecycle.

The recommendation of this document is:

- **GO** for documentation and monitoring (Stage 0-1)
- **GO** for isolated Scientific Layer integration (Stage 2-4)
- **PAUSE** for Outcome Bridge until architecture is reviewed (Stage 5)
- **NO-GO** for changing execution or capital allocation now

---

## 2. Why MVP v2 Exists

### 2.1 The Original MVP Answered One Question

The original MVP asked: *"Can we build a system that detects events, generates signals, and executes trades safely?"*

That question has been answered. The MVP demonstrates:
- Reliable event detection from 8+ collectors
- Signal generation through agent voting (5 agents, weighted council)
- Safe execution through 6 guard layers
- Outcome recording with agent-level attribution

But the current MVP cannot answer the next question: *"Is the system developing criterion over time?"*

### 2.2 The Gap

The current MVP has:
- No hypotheses (AgentOpinion is a static recommendation, not a testable belief)
- No evidence tracking (evidence lists are flat text strings without direction, weight, or decay)
- No hypothesis-to-decision linking (CouncilDecision does not reference a hypothesis)
- No outcome-to-hypothesis comparison (Trade PnL is not compared to a predicted consequence)
- No knowledge extraction (PerformanceMemory tracks agent accuracy, not generalizable lessons)
- No criterion measurement (no metrics for hypothesis quality, calibration, error recurrence)

MVP v2 fills this gap by introducing the Scientific Layer — a parallel system that wraps each operational cycle in a scientific context without touching the operational pipeline.

### 2.3 The Strategic Rationale

The project uses trading as its first validation domain, but the project's identity is a scientific research program. MVP v2 makes this identity operational by adding:
- A unit of learning (the hypothesis)
- A measurement instrument (evidence tracking)
- A learning signal (outcome comparison)
- A memory (scientific store)
- An output (validated knowledge → criterion)

---

## 3. Current Operational MVP

### 3.1 Architecture

```
Collectors → EventBus → Agents → Council → PaperTrading → Outcome
                ↑                                            │
                └────────── PerformanceMemory ←──────────────┘
```

### 3.2 Component Summary

| Component | Purpose | Scientific Relevance |
|-----------|---------|---------------------|
| 8 Collectors | Ingest market, news, macro data | Raw input; no hypothesis framing |
| 5 Agents | Form opinions with confidence | Static rules; no lifecycle |
| Council | Weighted voting, computes consensus | Aggregates opinions, not hypotheses |
| PaperTrading | Simulated execution | Produces trades, not scientific records |
| Guards | Capital protection | No scientific relevance |
| PerformanceMemory | Agent track records | Primitive learning signal |
| Telemetry | Operational logging | Operational data, not scientific |

### 3.3 Schema Inventory

The operational repo has 3 schema files:
- `event_schema.py` — Event, EventType, Asset, AssetClass, Sentiment, Urgency
- `agent_schema.py` — AgentOpinion, CouncilDecision, Recommendation, AgentRole, CouncilTier
- `trade_schema.py` — TradeSignal, Trade, TradeDirection, TradeStatus, ExitReason

No Hypothesis schema. No Evidence schema. No Knowledge schema. No DecisionRecord.

### 3.4 Test Inventory

23 test files covering agents, council, event bus, execution, memory, monitoring, and integration. 277 tests pass, 4 skipped (network-dependent). 0 failures.

### 3.5 Smoke Run Status

A continuous smoke run is in progress (started June 23, cycle count increasing). 0 runtime errors, 0 data failures. This validates operational stability.

---

## 4. USB Scientific Layer

### 4.1 Location

The Scientific Layer exists in `~/Projects/OMA_COMPARE/usb_version/` under:
- `core/scientific/` — ScientificStore, HypothesisLifecycle, EvidenceLifecycle, `__init__.py`
- `core/schemas/hypothesis_schema.py` — Hypothesis dataclass, HypothesisStatus enum, SQL schema
- `core/schemas/evidence_schema.py` — Evidence dataclass, EvidenceDirection/Status enums, SQL schema
- `tests/test_scientific_layer.py` — 23 tests, all passing

### 4.2 Component Summary

| Component | Purpose |
|-----------|---------|
| ScientificStore | Separate SQLite database (`scientific.db`), CRUD for hypotheses and evidence, stats |
| HypothesisLifecycle | 4-state state machine: FORMULATED → ACTIVE → EVALUATED → ARCHIVED |
| EvidenceLifecycle | 4-state state machine: COLLECTED → ACTIVE → EXPIRED / SUPERSEDED |
| Hypothesis schema | 10 fields (id, title, description, predicted_consequence, conditions, invalidation_conditions, confidence, status, created_at, updated_at, status_history) |
| Evidence schema | 12 fields (id, hypothesis_id, direction, weight, content, source_id, source_reliability, collected_at, independence_score, status, superseded_by) |

### 4.3 Key Design Decisions (from IMPLEMENTATION_DECISIONS.md)

| ID | Decision | Rationale |
|----|----------|-----------|
| ID-001 | Hypothesis + Evidence merged into one iteration | Conceptually connected; building them separately produces orphan records |
| ID-002 | 4-state lifecycle (reduced from 7) | CANDIDATE and terminal verdicts collapsed; simpler, same traceability |
| ID-003 | Separate scientific database | Zero regression risk, independent schema evolution, trivial rollback |
| ID-004 | Scientific Layer as new package | Clear boundary, easy to find, easy to replace |
| ID-006 | DecisionRecord deferred | Cannot aggregate objects that do not yet exist |
| ID-007 | ResearchProposal deferred | Premature; no hypotheses yet exist to group |

### 4.4 Test Summary

23 tests covering:
- Hypothesis CRUD (create, get, list, update, delete)
- State transitions (FORMULATED → ACTIVE → EVALUATED → ARCHIVED)
- Invalid transitions (raises ValueError)
- Evidence lifecycle (COLLECTED → ACTIVE → EXPIRED / SUPERSEDED)
- Supersede chain (evidence supersedes previous evidence)
- Confidence boundaries (clamped to 0.0–1.0)
- Weight, source_reliability, independence_score boundaries
- Store persistence (data survives store re-instantiation)
- Store isolation (separate database, independent of operational data)

All 23 tests pass.

---

## 5. New Core Chain

### 5.1 The Chain

```
Event
  │  A discrete observation: price movement, news headline, macro release
  ▼
Hypothesis
  │  A testable belief about a consequence, with invalidation conditions
  ▼
Evidence
  │  Supporting and contradicting observations, tracked independently
  ▼
Decision
  │  A choice to act, wait, monitor, or ignore, linked to a hypothesis
  ▼
Outcome
  │  What actually happened, recorded objectively before interpretation
  ▼
Validated Knowledge
  │  A generalizable lesson extracted from comparing outcome to hypothesis
  ▼
Criterion
  │  Accumulated ability to judge what matters (emergent, not stored)
```

### 5.2 Why This Replaces Event → Evidence → Hypothesis

The older chain (from CRITERION_AND_CONSEQUENCE_THESIS.md) was:

```
Event → Correlation → Cluster → Consequence → Hypothesis → Opportunity → Action → Outcome → Memory → Knowledge → Criterion
```

And an even earlier version was `Event → Evidence → Hypothesis`.

The new chain corrects two fundamental errors:

**Evidence requires a hypothesis.** Evidence is defined relative to a belief. There is no "supporting evidence" without a hypothesis to support. Placing Evidence before Hypothesis in the chain implies evidence exists independently — it does not. The new chain places Hypothesis first: an event triggers a hypothesis, then evidence is collected for or against it.

**Learning requires the full arc.** The older chains had no explicit Decision node and no Validated Knowledge step. An Outcome was recorded but not compared to a Hypothesis. Knowledge was mentioned but not operationalized. The new chain makes learning explicit: Outcome → comparison to Hypothesis → Validated Knowledge → Criterion update.

The new chain is a 7-node minimal path from observation to accumulated judgment. Every node is required. No node can be skipped without breaking the learning mechanism.

---

## 6. Object Definitions

### Event

- **Source:** Collectors (CoinGecko, YahooFinance, Binance, FRED, RSS, Sentiment, Polymarket)
- **Schema:** `event_schema.py` — Event dataclass with type, source, assets, sentiment, urgency
- **Lifecycle:** Detected → Processed (binary; no scientific lifecycle)
- **Note:** Events are operational inputs. They become data for hypotheses but are not managed as scientific objects.

### Hypothesis

- **Source:** USB Scientific Layer (`hypothesis_schema.py`, `hypothesis_lifecycle.py`)
- **Schema:** 10 fields — id, title, description, predicted_consequence, conditions, invalidation_conditions, confidence, status, created_at, updated_at, status_history
- **Lifecycle:** FORMULATED → ACTIVE → EVALUATED → ARCHIVED
- **Store:** `ScientificStore` in `scientific.db` (separate from `oma_core.db`)
- **Note:** The hypothesis is the unit of learning. It must be falsifiable, time-bound, and linked to an expected consequence.

### Evidence

- **Source:** USB Scientific Layer (`evidence_schema.py`, `evidence_lifecycle.py`)
- **Schema:** 12 fields — id, hypothesis_id, direction (supports/contradicts), weight, content, source_id, source_reliability, collected_at, independence_score, status, superseded_by
- **Lifecycle:** COLLECTED → ACTIVE → EXPIRED / SUPERSEDED
- **Store:** `ScientificStore` in `scientific.db`
- **Note:** Evidence always belongs to exactly one hypothesis. Direction and weight are tracked separately. Source reliability and independence score are recorded for quality weighting.

### Decision

- **Source:** Currently `CouncilDecision` (operational); will gain hypothesis link
- **Schema (future):** Extends CouncilDecision with hypothesis_id, competing_hypothesis_ids, expected_scenario
- **Lifecycle:** FORMED → MADE → EXECUTED → EVALUATED (conceptual; not yet implemented)
- **Note:** In MVP v2, decisions are created by the Council as before. The scientific layer records the hypothesis link without changing Council logic.

### Outcome

- **Source:** Currently `Trade` (operational); will gain hypothesis comparison
- **Schema (future):** Extends Trade with hypothesis_id, hypothesis_verdict, error_type
- **Lifecycle:** PENDING → OBSERVED → RECORDED (conceptual; not yet implemented)
- **Note:** In MVP v2, outcomes are recorded by PaperTradingEngine as before. The Outcome Bridge adds the hypothesis comparison as a post-processing step.

### Validated Knowledge

- **Source:** New concept; not yet implemented in either repo
- **Schema (proposed):** id, statement, source_hypothesis_ids, conditions, confidence, status (PROVISIONAL → VALIDATED / REVISED / INVALIDATED → ARCHIVED), created_at, last_applied_at
- **Note:** Knowledge becomes "validated" when the same lesson is confirmed across multiple hypotheses. A single outcome produces provisional knowledge. Multiple confirmations produce validated knowledge.

### Criterion

- **Source:** Philosophical concept; measured through CriterionSnapshot
- **Note:** Criterion is not a stored object. It is an emergent property measured periodically from completed hypothesis lifecycles. It exists as a trend across many cycles, not as a record in a database.

---

## 7. What Changes from MVP v1

### New Code (No Existing Code Modified)

| Addition | Location | Purpose |
|----------|----------|---------|
| `core/scientific/` package | New package | Hypothesis lifecycle, evidence lifecycle, scientific store |
| `hypothesis_schema.py` | `core/schemas/` | Hypothesis dataclass + SQL schema |
| `evidence_schema.py` | `core/schemas/` | Evidence dataclass + SQL schema |
| `scientific.db` | Project root | Separate SQLite database for scientific records |
| Scientific tests | `tests/` | 23 tests for hypotheses, evidence, lifecycle, store |

### Configuration Changes

| New Config | Purpose |
|------------|---------|
| `scientific.db_path` | Path to the separate scientific database |
| Hypothesis lifecycle defaults | Confidence default (0.5), evidence defaults |

### Pipeline Additions (Future Stages)

| Stage | Addition | When |
|-------|----------|------|
| Hypothesis creation | CLI command to create hypotheses | Stage 2 |
| Evidence collection | CLI command to add evidence | Stage 2 |
| Hypothesis-decision link | Council records hypothesis_id | Stage 4 |
| Outcome comparison | Trade closure triggers hypothesis comparison | Stage 5 |
| Knowledge extraction | Post-outcome knowledge extraction | Stage 6 |

---

## 8. What Does NOT Change

### Unchanged Components

| Component | Status | Rationale |
|-----------|--------|-----------|
| Collectors (all 8) | Untouched | They produce raw data; scientific layer consumes data, does not change production |
| EventBus | Untouched | Publishing/subscribing continues unchanged |
| Agents (all 5) | Untouched | AgentOpinion remains; it becomes input for hypothesis formation but is not modified |
| Council | Untouched | CouncilDecision continues; hypothesis link is additive, not modificatory |
| PaperTradingEngine | Untouched | Execution continues; Outcome Bridge is post-processing |
| Guards (all 6) | Untouched | Capital protection is independent of scientific layer |
| PerformanceMemory | Untouched | Continues tracking agent accuracy; parallel to scientific tracking |
| Telemetry | Untouched | Operational logging continues; scientific records are separate |
| HealthMonitor | Untouched | Operational health checks continue |
| CLI (existing commands) | Untouched | New scientific commands are additions, not changes |
| `oma_core.db` | Untouched | Scientific data lives in `scientific.db` |
| Existing schemas | Untouched | Event, AgentOpinion, CouncilDecision, Trade remain as-is |

### Unchanged Behaviors

- Event ingestion timing and reliability
- Agent polling frequency and opinion formation
- Council voting mechanics and conviction computation
- Trade execution, position management, and guard enforcement
- Telemetry logging format and frequency
- PerformanceMemory update cycle
- Health checking schedule and alerting

### Unchanged Tests

All 277 existing tests continue to pass unchanged. New tests for the Scientific Layer (23) run in addition.

---

## 9. Integration Stages

### Stage 0 — Backup

Before any integration:
- Clone the operational repository
- Run full test suite (277+ tests) to establish baseline
- Document current system behavior (trade count, PnL, error rates)
- Verify `scientific.db` does not exist (clean slate)

### Stage 1 — Documentation Transfer

Copy USB documentation into the operational repo:
- `docs/era2/` (4 documents: MVP Redefinition, Scientific Object Model, Implementation Bridge, Decision Log)
- `docs/first_principles/14-18` (Hypothesis Lifecycle, Readiness Audit, Decision Science, Validation Framework, Research Protocol)
- `research/` (judgment_dimensions.md, judgment_landscape.md)

No code changes. This establishes shared vocabulary.

### Stage 2 — Schema Integration

- Add `hypothesis_schema.py` to `core/schemas/`
- Add `evidence_schema.py` to `core/schemas/`
- These are pure dataclass + SQL schema files with no runtime side effects
- Run all existing tests to confirm zero regression
- Run 23 scientific layer tests to confirm they pass in the operational environment

### Stage 3 — Scientific Store Integration

- Add `core/scientific/` package with `__init__.py`, `scientific_store.py`, `hypothesis_lifecycle.py`, `evidence_lifecycle.py`
- ScientificStore uses a separate `scientific.db` — zero impact on `oma_core.db`
- Store creates its own tables on initialization via `executescript`
- Run all tests (existing + scientific) to confirm isolation

### Stage 4 — CLI Visibility

- Add scientific commands to CLI: `hypothesis create`, `hypothesis list`, `hypothesis transition`, `evidence add`, `evidence list`, `science stats`
- These commands operate only on `scientific.db` — no operational impact
- Enables manual hypothesis creation and evidence tracking during smoke run
- First scientific data enters the system

### Stage 5 — Outcome Bridge

- Post-processing step: when a `Trade` closes, create a hypothesis verdict (CONFIRMED / REJECTED / INCONCLUSIVE)
- Compare outcome to the hypothesis's `predicted_consequence`
- Classify error type (WRONG_HYPOTHESIS, WRONG_TIMING, POOR_EXECUTION, EXTERNAL_SHOCK, CORRECT)
- **PAUSE recommended before this stage** — the architecture for linking trades to hypotheses must be reviewed

### Stage 6 — Knowledge Extraction

- After each hypothesis is evaluated, extract one or more generalizable lessons
- Store as knowledge entries in `scientific.db`
- Track knowledge → hypothesis provenance
- Enable knowledge querying by conditions, domain, confidence

### Stage 7 — Criterion Metrics

- Compute criterion snapshots from completed hypothesis lifecycles
- Dimensions: hypothesis quality, evidence quality, calibration, error recurrence rate, knowledge yield
- Trend analysis across rolling windows
- Report alongside existing health monitoring

### Stage 8 — Telemetry Link

- Populate hypotheses from real telemetry data
- Hypothesis formation becomes partially automated
- This is the validation gate: until hypotheses are populated from live data, the Scientific Layer cannot be validated

---

## 10. Outcome Bridge Concept

### 10.1 What It Is

The Outcome Bridge is the mechanism that links a closed `Trade` back to the `Hypothesis` that produced it, enabling outcome comparison.

### 10.2 The Problem

Currently, the chain is:
```
Event → Agents → Council → TradeSignal → Trade → PnL
```

There is no hypothesis anywhere in this chain. When a trade closes, the system knows PnL, exit reason, and holding time — but it does not know what belief was being tested.

### 10.3 The Solution (Conceptual)

The Outcome Bridge is a post-processing step that runs after a trade closes:

```
Trade closes
  ↓
Look up the hypothesis_id associated with the CouncilDecision that created this trade
  ↓
Retrieve the hypothesis's predicted_consequence, conditions, time horizon
  ↓
Compare actual outcome to predicted consequence
  ↓
Assign verdict: CONFIRMED / REJECTED / INCONCLUSIVE
  ↓
Classify error type if rejected
  ↓
Record verdict on the hypothesis in scientific.db
```

### 10.4 What It Requires

- A `hypothesis_id` field on `CouncilDecision` (or a mapping table)
- A `hypothesis_id` field on `TradeSignal` (propagated from CouncilDecision)
- A comparison function: outcome vs. predicted_consequence within tolerance
- An error type taxonomy
- A verdict recording mechanism (writes to ScientificStore)

### 10.5 Why PAUSE

The Outcome Bridge requires modifying the operational pipeline at minimum to propagate `hypothesis_id` from CouncilDecision through TradeSignal to Trade. This is the first point where operational and scientific data must intersect. The architecture of this intersection must be reviewed before implementation.

The risk is coupling: if the scientific layer cannot find the hypothesis for a closed trade, does the system crash? Or does it gracefully skip? The error handling must be designed, not hacked.

---

## 11. Validated Knowledge Concept

### 11.1 What It Is

Validated Knowledge is a generalizable lesson derived from one or more completed hypothesis lifecycles. It answers: *"Under what conditions, what actions produce what outcomes with what confidence?"*

### 11.2 The Knowledge Ladder

| Level | Definition | Example |
|-------|-----------|---------|
| **Observation** | A single data point | "Gold moved up 2% after rate cut" |
| **Hypothesis Outcome** | One test result | "Hypothesis H-042 was CONFIRMED: rate cut → gold up 2-4% in 5 days" |
| **Provisional Knowledge** | One lesson from one outcome | "Rate cuts in low-inflation environments predict gold rallies" |
| **Validated Knowledge** | Same lesson across 3+ outcomes | Same statement, confirmed across 3+ distinct episodes |
| **Criterion Rule** | Embedded in system behavior | System weights gold-positive hypotheses higher after rate cuts |

### 11.3 Lifecycle

```
EXTRACTED → PROVISIONAL → VALIDATED / REVISED / INVALIDATED → ARCHIVED
```

- **EXTRACTED:** A lesson is recorded from a single hypothesis outcome
- **PROVISIONAL:** The lesson is available for use but has not been cross-validated
- **VALIDATED:** The lesson has been confirmed across 3+ independent hypothesis outcomes
- **REVISED:** The lesson was updated with new evidence
- **INVALIDATED:** The lesson was proven incorrect
- **ARCHIVED:** The lesson is preserved for historical analysis

### 11.4 Validation Criteria

A knowledge entry is considered VALIDATED when:
1. At least 3 independent hypothesis outcomes support the same lesson
2. The supporting hypotheses span different temporal windows (not all from the same week)
3. No contradictory hypothesis outcomes exist (or contradictions are explained by specific conditions)
4. The lesson is specific enough to be actionable
5. The lesson has a measurable condition scope

---

## 12. Criterion as Emergent Property

### 12.1 Criterion Is Not an Object

The object model (02_SCIENTIFIC_OBJECT_MODEL.md) explicitly excludes Criterion as a stored object. CriterionSnapshot (now a computed view, not a stored entity) measures criterion metrics from completed DecisionRecords.

### 12.2 What Criterion Measures

Criterion is the system's accumulated ability to judge what matters. It is measured across dimensions:

| Dimension | What It Measures |
|-----------|-----------------|
| Hypothesis Quality | Precision, falsifiability, evidence grounding — trended over time |
| Evidence Quality | Relevance, independence, source reliability — trended over time |
| Calibration | Alignment between confidence and accuracy |
| Error Recurrence | Proportion of hypotheses repeating previous error types |
| Knowledge Yield | Average lessons per hypothesis, knowledge applicability rate |
| Learning Velocity | Time from outcome to knowledge extraction |
| Decision Utility | Retrospective decision quality independent of outcome |

### 12.3 How It Emerges

Criterion is not built. It accumulates. Each hypothesis lifecycle produces a data point. Each knowledge extraction updates the system's implicit judgment. Over hundreds of cycles, patterns emerge:
- Hypotheses become more precise
- Calibration converges
- Error types shift from fundamental (wrong consequence) to marginal (wrong timing)
- Knowledge entries become more generalizable and more durable

### 12.4 The Compounding Effect

The strategic thesis of MVP v2 is that criterion compounds while models plateau. A model retrains and returns to approximately the same performance baseline. Criterion accumulates: every tested hypothesis, every classified error, every extracted knowledge entry becomes permanent infrastructure for better future decisions.

This is why the Scientific Layer is architecture-critical: not because it adds immediate capability, but because it starts the compounding clock. Every day without hypothesis tracking is a day of evidence not captured, knowledge not extracted, and criterion not measured.

---

## 13. Risks

### 13.1 Scientific Store Concurrency

**Risk:** `ScientificStore` uses a new `sqlite3.connect()` per operation with no connection pooling, no WAL mode, no retry logic. The operational `OMACoreDatabase` has connection pooling and error handling — if ScientificStore is ever called from concurrent contexts, it will fail.

**Mitigation:** ScientificStore is called only from CLI commands (single-threaded) in Stages 2-4. The concurrency risk only materializes in Stage 5+ when automated processes write to it. A redesign to match `OMACoreDatabase`'s pattern should precede Stage 5.

### 13.2 In-Place Mutation

**Risk:** `hypothesis_lifecycle.py` mutates the hypothesis object in place (`hypothesis.status = ...`) rather than returning a new instance. This side-effect pattern may conflict with operational code that expects immutable objects.

**Mitigation:** The lifecycle functions are called only from CLI or explicit lifecycle transitions. No operational code path calls them. If automated lifecycle transitions are added in Stage 6+, the mutation pattern should be reviewed.

### 13.3 API Inconsistency

**Risk:** `activate_evidence` and `expire_evidence` use different parameter styles. `activate_evidence(evidence)` takes an Evidence object, while `expire_evidence(evidence_id)` takes a string ID. This inconsistency is already present in the USB version.

**Mitigation:** Standardize to object-based parameters (like `activate_evidence`) before the API surface grows.

### 13.4 Outcome Bridge Coupling

**Risk:** The Outcome Bridge (Stage 5) is the first point where operational and scientific data intersect. If the bridge fails to find a hypothesis for a closed trade, the system must handle this gracefully. If not designed properly, a scientific layer failure could crash the operational pipeline.

**Mitigation:** Use a two-phase approach: (1) post-process only — the bridge runs after the trade is fully closed, with no impact on execution; (2) failure is silent — if hypothesis lookup fails, the trade is recorded without a verdict (graceful degradation).

### 13.5 Premature Automation

**Risk:** Automating hypothesis formation (Stage 8) before manually created hypotheses establish a quality baseline will produce low-quality hypotheses that teach nothing.

**Mitigation:** Follow the Implementation Bridge decision (ID-005): manual hypothesis creation through Stage 4. Automated formation only after at least 50 manually created hypotheses exist.

### 13.6 Scope Creep

**Risk:** The Scientific Layer has a rich philosophical foundation. The temptation to implement all 7 scientific objects (from the object model) immediately must be resisted.

**Mitigation:** Implement only what serves the core chain: Hypothesis, Evidence, Decision (link only), Outcome (comparison only), Knowledge (basic). Defer ResearchProposal, full DecisionRecord, and CriterionSnapshot until the core chain proves useful.

### 13.7 Smoke Run Interference

**Risk:** The Scientific Layer's separate database or CLI commands could inadvertently affect the smoke run.

**Mitigation:** Scientific Layer writes only to `scientific.db`. The smoke run reads only from `oma_core.db` and operational memory. They share no files, no tables, and no connections. The only shared resource is the Python process, which should not be affected by importing new modules.

---

## 14. Validation Requirements

### 14.1 Pre-Integration Requirements

Before any integration begins:

| Requirement | Verification |
|-------------|-------------|
| Full test suite passes | `pytest tests/ -v` — 277+ passed, 0 failed |
| Smoke run is healthy | 0 runtime errors, 0 data failures, minimum 100 cycles |
| Operational baseline documented | Trade count, PnL, error rates, cycle distribution |
| `scientific.db` does not exist | No interference from previous attempts |
| USB version tests pass | `pytest tests/test_scientific_layer.py -v` — 23/23 passed |

### 14.2 Stage Requirements

| Stage | Verification | Gate |
|-------|-------------|------|
| Stage 1 (Docs) | Documents readable, no code changes | Manual review |
| Stage 2 (Schemas) | All 300+ tests pass, schemas import cleanly | `pytest tests/ -v` |
| Stage 3 (Store) | `ScientificStore` creates `scientific.db`, all CRUD works | 23 scientific tests pass |
| Stage 4 (CLI) | `hypothesis create` produces valid entry, `science stats` returns data | Manual + test |
| Stage 5 (Bridge) | Outcome Bridge returns correct verdict for known hypothesis | Integration test |
| Stage 6 (Knowledge) | Knowledge entries linked to source hypotheses | Integration test |
| Stage 7 (Metrics) | CriterionSnapshot computation returns valid dimensions | Integration test |
| Stage 8 (Telemetry) | Hypotheses populated from live data, validation run | 30-day validation |

### 14.3 Post-Integration Monitoring

| Monitor | What to Watch | Alert Threshold |
|---------|---------------|-----------------|
| Scientific DB size | Growth rate | > 10 MB / week unexpected |
| Hypothesis creation rate | Hypotheses per week | < 3 / week or > 50 / week |
| Hypothesis completion rate | EVALUATED / FORMULATED ratio | < 20% after 4 weeks |
| Evidence per hypothesis | Mean evidence count | < 1.0 after 2 weeks |
| Outcome Bridge success | % of trades linked to hypotheses | < 50% after Stage 5 |
| Test suite | Regression detection | Any failure = stop |
| Smoke run health | Runtime errors | Any increase = stop |

---

## 15. GO / PAUSE / NO-GO Recommendation

### GO — Documentation and Monitor

**Verdict: GO**

- Stage 0 (Backup) can proceed immediately
- Stage 1 (Documentation Transfer) can proceed immediately
- No code changes, no runtime impact, no risk
- Establishes shared vocabulary before any engineering begins

**Condition:** Run full test suite first. Verify smoke run health. Document baseline.

### GO — Isolated Scientific Layer Integration

**Verdict: GO**

- Stages 2-4 (Schema, Store, CLI) can proceed
- Scientific Layer is completely isolated in `scientific.db`
- Zero impact on operational pipeline
- 23 tests validate correctness
- Manual CLI only — no automated processes write to scientific data

**Condition:** Implement Stages 2-4 in a branch. Run all tests before merging. Do not merge until smoke run reaches 7 days without errors.

### PAUSE — Outcome Bridge

**Verdict: PAUSE**

- Stage 5 (Outcome Bridge) is the first point where operational and scientific data intersect
- Requires propagating hypothesis_id through CouncilDecision → TradeSignal → Trade
- This is the first modificación to operational code paths
- Risk of coupling: scientific layer failure could leak into operational pipeline

**Condition:** Before proceeding to Stage 5:
1. Review the architecture of the hypothesis_id propagation
2. Design error handling for missing hypotheses (graceful degradation)
3. Implement a design document specifically for the Outcome Bridge
4. Run the Outcome Bridge in dry-run mode for at least 100 trades before activating verdict recording

### NO-GO — Changing Execution or Capital Allocation

**Verdict: NO-GO**

- The following are explicitly excluded from MVP v2:
  - Using hypothesis confidence to modify position sizing
  - Using evidence quality to override Council decisions
  - Using knowledge to modify guard parameters
  - Using criterion metrics to adjust capital allocation
  - Any change to PaperTradingEngine, CapitalGuard, or any execution component

**Rationale:** The Scientific Layer must prove it produces reliable knowledge before that knowledge influences execution. Premature coupling would add risk to the operational pipeline and conflate learning with acting before learning is validated.

**Condition for re-evaluation:** After at least 100 hypotheses have completed the full lifecycle (FORMULATED → EVALUATED) AND at least 20 knowledge entries have reached VALIDATED status AND criterion metrics show positive trends across 3+ consecutive measurement windows.

---

*End of MVP2_ARCHITECTURE.md — Version 1.0 — June 2026*
