# ARCHITECTURE V2 — O.M.A.-C.O.R.E.

## 1. Executive Summary

Architecture V2 replaces the execution-centered architecture that defined the MVP through ERA I. The old architecture — Sources → Collectors → Events → Agents → Council → Trade Signals → Execution → Risk → Monitoring — accurately described a working trading prototype. It remains valid as the **Operational MVP map** but does not represent the full project vision.

The project has evolved from a trading prototype to a **decision intelligence system**. Its purpose is no longer producing trades. Its purpose is producing Criterion — the accumulated ability to judge what matters — and converting that Criterion into scarce resources through better decisions.

Architecture V2 defines three interdependent flows that together describe what O.M.A.-C.O.R.E. is, what it does, and why it exists:

1. **Operational Flow** — the real-time event-to-action pipeline (mostly implemented)
2. **Scientific Learning Flow** — how the system learns from every cycle (partially implemented)
3. **Strategic Resource Flow** — why the system exists and what it produces (entirely in design)

This document serves as the canonical architecture reference. It replaces `MVP2_ARCHITECTURE.md` (which never existed in the USB version) and supersedes the pipeline descriptions in `03_IMPLEMENTATION_BRIDGE.md` where they conflict.

---

## 2. Architectural Thesis

O.M.A.-C.O.R.E. is a **decision intelligence system** designed to develop **Criterion** through validated experience and convert better decisions into **scarce resources**.

The system does not predict. It judges. It does not optimize for profit. It optimizes for learning. Profit is expected to be a consequence of sustained Criterion development, not the primary objective.

The central hypothesis that justifies the project's existence:

> A system develops Criterion when its future hypotheses become consistently better because its previous hypotheses were explicitly tested, evaluated, and transformed into reusable knowledge.

Everything in Architecture V2 serves this hypothesis. Every component must trace back to it.

---

## 3. Canonical Core Loop

The following loop is the canonical representation of O.M.A.-C.O.R.E. It is a loop, not a linear pipeline. Each cycle feeds the next. Criterion compounds.

```
     Reality
        ↓
   Observation
        ↓
      Event
        ↓
    Reasoning
        ↓
   Hypothesis
        ↓
    Evidence
        ↓
    Decision
        ↓
    Approval
        ↓
Execution / Action
        ↓
    Outcome
        ↓
Validated Knowledge
        ↓
    Criterion
        ↓
 Scarce Resources
        ↓
  Reinvestment
        ↓
Stronger Criterion ───→ (loop back to Reasoning)
```

### Node Definitions

| Node | Purpose | Status | Existing Implementation | Missing Pieces | Validation Method |
|------|---------|--------|------------------------|----------------|-------------------|
| **Reality** | The external world. Markets, news, geopolitics, data. | IMPLEMENTED | External data feeds (Binance, Yahoo, FRED, RSS, Polymarket, CoinGecko, Sentiment) | None — reality is assumed to exist independently | N/A |
| **Observation** | Raw data collection. Sensors that detect changes in reality. | IMPLEMENTED | 8 collectors in `core/collectors/` with BaseCollector abstraction, WorldMonitorV2 orchestration | No source reliability tracking beyond static assignment | Collector uptime, data freshness, coverage |
| **Event** | A structured notification that something happened. Carries source, type, timestamp, assets, urgency, confidence. | IMPLEMENTED | `Event` schema in `core/schemas/event_schema.py`, EventBus in `core/event_bus/bus.py`, published as `EventData` objects | No hypothesis link, no consequence prediction | Event volume, latency, schema completeness |
| **Reasoning** | The cognitive layer that interprets events, generates possible consequences, and formulates hypotheses. | MISSING | No standalone component. Reasoning traces exist as text in AgentOpinion.reasoning fields. | **Reasoning Engine** — does not exist. No structured reasoning from event to hypothesis. | To be defined when implemented |
| **Hypothesis** | A structured, testable belief about a consequence. The unit of learning. | PARTIAL | Hypothesis schema (`core/schemas/hypothesis_schema.py`), lifecycle state machine (`core/scientific/hypothesis_lifecycle.py`), persistence (`core/scientific/scientific_store.py`), CLI commands | No automated creation. No link to events (event_id). No link to decisions (deferred to Iteration 2). | 23 integration tests passing. Hypothesis CRUD and lifecycle transitions verified. |
| **Evidence** | Information relative to a hypothesis. Supports or contradicts. | PARTIAL | Evidence schema (`core/schemas/evidence_schema.py`), lifecycle (`core/scientific/evidence_lifecycle.py`), store integration | No automated collection. No source reliability evolution. No decay mechanism. All evidence is manually added. | 23 integration tests passing. Evidence CRUD and state transitions verified. |
| **Decision** | Commitment to a course of action based on hypothesis evaluation. | PARTIAL | CouncilDecision schema in `core/schemas/agent_schema.py`, AgentCouncil produces weighted consensus | No hypothesis link. No alternative comparison. No expected scenario recording. No decision quality evaluation. | Council voting tests exist. No post-decision evaluation. |
| **Approval** | Validation that a decision meets threshold criteria before execution. | MISSING | **Decision Approval Engine** — does not exist. Current MVP uses guards (CapitalGuard, CrashDetector) as operational gates, not scientific approval. | Approval Engine, Auto-Approval Readiness Score, Notification Quality Gate | To be defined |
| **Execution / Action** | Carrying out the decision in the world. | IMPLEMENTED | PaperTradingEngine (`core/execution/paper_trading.py`), risk guards, position management | No hypothesis link on trades. Exit reasons are operational, not scientific. | Full execution and guard test coverage |
| **Outcome** | The result of an action. What actually happened. | PARTIAL | Trade records in `oma_core.db`, PerformanceMemory agent tracking | No comparison to hypothesis. No verdict assignment (confirmed/rejected/inconclusive). No error classification. | Trade record tests exist. No outcome-to-hypothesis comparison. |
| **Validated Knowledge** | A generalizable lesson extracted from comparing outcome to hypothesis. | MISSING | No Knowledge schema, no lifecycle, no extraction mechanism | Entire concept is in design phase only | To be defined (Iteration 6) |
| **Criterion** | The emergent accumulated ability to judge what matters. | EMERGENT | Not stored as a table, class, or model. Criterion is measured, not built. | CriterionSnapshot computation does not exist. Trend analysis does not exist. | To be defined (Iteration 7) |
| **Scarce Resources** | Capital, time, attention, knowledge, relationships, mobility, health, freedom of decision. | RESEARCH | Mentioned in NORTH_STAR.md and CRITERION_VALIDATION_FRAMEWORK.md | No formal model. No ScarceResource schema. No allocation logic. No resource efficiency metrics. | To be defined |
| **Reinvestment** | Using acquired scarce resources to strengthen the next cycle of Criterion development. | RESEARCH | Not designed | No concept of resource reinvestment beyond capital compounding | To be defined |

---

## 4. Three Flows

### 4.1 Operational Flow

**Purpose:** What the current MVP does in real time — detect events, generate signals, execute trades safely, record outcomes.

**Flow:**

```
Sources (8 data feeds)
    ↓
Collectors (CoinGecko, Yahoo, Binance, FRED, RSS, Sentiment, Polymarket, WorldMonitorV2)
    ↓
Validation (error handling, retry, rate limiting, stats)
    ↓
Event Schema → EventBus → EventTopics
    ↓
Agents (Market, News, Macro, Risk, Trend) → AgentOpinions
    ↓
Council (AgentCouncil + MetaCouncil) → CouncilDecision
    ↓
TradeSignal → Guard Layer:
    ├── CapitalGuard (kill switch, loss limits, drawdown)
    ├── DirectionController (direction disabled?)
    ├── CrashDetector (crash mode?)
    ├── KnifeDetector (dip vs falling knife)
    ├── GapRisk (weekend gap)
    └── SlippageEngine
    ↓
PaperTradingEngine → Position Management → Trade Record
    ↓
Telemetry / Monitoring / Memory
```

**Status:** MOSTLY IMPLEMENTED. All components exist and are operational. The Extended Demo runs continuously on the laptop version.

**Limitations:**
- No hypothesis link on any trade
- No evidence formation from events
- Agents are static rules — no learning
- Exit reasons are operational (stop_loss, take_profit) not scientific
- Council weights agents by accuracy, not hypothesis quality

### 4.2 Scientific Learning Flow

**Purpose:** How the system learns from every operational cycle — from raw event to accumulated Criterion.

**Flow:**

```
Event
    ↓
Reasoning ──────────────── MISSING (no Reasoning Engine)
    ↓
Hypothesis ─────────────── PARTIAL (schema + lifecycle exist, no event link)
    ↓
Evidence ───────────────── PARTIAL (schema + lifecycle exist, no auto-collection)
    ↓
Decision ───────────────── PARTIAL (Council exists, no hypothesis link)
    ↓
Approval ───────────────── MISSING (no Decision Approval Engine)
    ↓
Outcome ────────────────── PARTIAL (trades recorded, no hypothesis comparison)
    ↓
Validated Knowledge ────── MISSING (no schema, no extraction)
    ↓
Criterion ──────────────── EMERGENT (measured, not built; no CriterionSnapshot yet)
```

**Status:** HYPOTHESIS + EVIDENCE EXIST. Everything else is PARTIAL or MISSING.

### 4.3 Strategic Resource Flow

**Purpose:** Why the system exists — converting Criterion into scarce resources and reinvesting them to strengthen Criterion.

**Flow:**

```
Criterion (accumulated judgment)
    ↓
Better Decisions (choices that allocate resources more wisely)
    ↓
Scarce Resources (capital, time, attention, knowledge, relationships, mobility, health, freedom)
    ↓
Reinvestment (resources feed back into observation, reasoning, and hypothesis formation)
    ↓
Stronger Criterion (next cycle starts from a higher baseline)
```

**Status:** ENTIRELY IN DESIGN. The concept is documented in `05_NORTH_STAR.md` (scarce resources list) and `17_CRITERION_VALIDATION_FRAMEWORK.md` (validation layers), but no formal model exists. Money is the first and most measurable resource, but the system must eventually optimize across all eight.

**Key insight:** A system that optimizes only for capital will eventually sacrifice time, attention, and health — making it unsustainable. The Scarce Resources model must prevent this by design.

---

## 5. Layered Architecture V2

| Layer | Name | Role | Status | Key Files/Modules | Must Never Do | Near-Term Priority |
|-------|------|------|--------|-------------------|---------------|-------------------|
| 0 | **First Principles** | Philosophical foundation: what the project believes, rejects, assumes, questions | IMPLEMENTED | `docs/first_principles/00`–`18` | Never become unchangeable dogma | Maintained |
| 1 | **Reality / Source** | The external world and data feeds | IMPLEMENTED | External APIs (Binance, Yahoo, FRED, etc.) | Never be filtered by bias | Maintained |
| 2 | **Observation / Collector** | Raw data collection and sensor management | IMPLEMENTED | `core/collectors/`, `WorldMonitorV2` | Never bypass validation | Maintained |
| 3 | **Validation / Quality** | Data validation, error handling, rate limiting, source reliability | IMPLEMENTED | BaseCollector retry/error logic, collector stats | Never silently drop data | Maintained |
| 4 | **Event** | Structured event representation and distribution | IMPLEMENTED | `core/schemas/event_schema.py`, `core/event_bus/bus.py` | Never lose causality chain | Maintained |
| 5 | **Reasoning** | Event interpretation, consequence generation, hypothesis formation | MISSING | — | Never produce untestable conclusions | High — design first |
| 6 | **Scientific** | Hypothesis lifecycle, evidence tracking, scientific memory | PARTIAL | `core/schemas/hypothesis_schema.py`, `core/schemas/evidence_schema.py`, `core/scientific/` | Never modify operational database | Maintained and extend |
| 7 | **Decision Intelligence** | Hypothesis evaluation, alternative comparison, decision quality | PARTIAL | `core/council/council.py` (primitive) | Never overweigh confidence without evidence | Medium — Iteration 3 |
| 8 | **Approval** | Threshold validation before execution, readiness scoring, notification gating | MISSING | — | Never approve without explainable criteria | High — design after Innovation System |
| 9 | **Execution / Action** | Carrying out decisions with risk management | IMPLEMENTED | `core/execution/paper_trading.py`, risk guards | Never use real capital without evidence-based approval | Maintained. No real capital. |
| 10 | **Outcome** | Outcome recording, hypothesis comparison, verdict assignment, error classification | PARTIAL | `core/execution/performance_memory.py` (primitive agent tracking) | Never attribute outcome to wrong hypothesis | Medium — Iteration 4 |
| 11 | **Validated Knowledge** | Knowledge extraction from outcomes, lifecycle, application tracking | MISSING | — | Never treat provisional knowledge as settled | Low — Iteration 6 |
| 12 | **Criterion** | Criterion measurement, trend analysis, CriterionSnapshot | EMERGENT | `docs/first_principles/08_CRITERION.md` (philosophy only) | Never be reduced to a single score | Low — Iteration 7 |
| 13 | **Scarce Resources** | Resource model, allocation optimization, efficiency metrics | RESEARCH | `docs/first_principles/05_NORTH_STAR.md` (concept only) | Never optimize capital at the expense of other resources | Medium — design after Criterion measurement |
| 14 | **Innovation System** | Structured experimentation, research proposals, hypothesis generation | PLANNED | — | Never destabilize operational MVP | High — next after architecture alignment |
| 15 | **Interface** | CLI, cockpit, notifications, dashboard | PARTIAL | `core/cli/main.py`, Telegram notifier | Never present speculation as fact | Maintained |

---

## 6. Component Status Matrix

| Component | Status | Notes |
|-----------|--------|-------|
| Sources (data feeds) | IMPLEMENTED | 8 external data sources: Binance, Yahoo, CoinGecko, FRED, RSS, Sentiment, Polymarket, WorldMonitorV2 |
| Collectors | IMPLEMENTED | 8 collector classes with BaseCollector abstraction |
| Validation (data quality) | IMPLEMENTED | Error handling, retry, rate limiting in BaseCollector |
| Event Schema | IMPLEMENTED | `core/schemas/event_schema.py` — source, type, title, timestamp, assets, sentiment, urgency, confidence |
| EventBus | IMPLEMENTED | `core/event_bus/bus.py` — pub/sub with EventTopics |
| Agents | IMPLEMENTED | 5 agents (Market, News, Macro, Risk, Trend) — static rules, no learning |
| Council | IMPLEMENTED | AgentCouncil with weighted voting, MetaCouncil for cross-profile comparison |
| Trade Signal | IMPLEMENTED | CouncilDecision → TradeSignal schema |
| Paper Trading | IMPLEMENTED | `core/execution/paper_trading.py` — position management, SL/TP, order types |
| Risk Guards | IMPLEMENTED | CapitalGuard, CrashDetector, KnifeDetector, DirectionController, GapRisk, SlippageEngine |
| Monitoring | IMPLEMENTED | HealthMonitor (10 checks), FailureClassifier (9 error types) |
| Memory | IMPLEMENTED | Short-term (TTL), long-term (tagged, persistent), PerformanceMemory (agent tracking) |
| Scientific Store | IMPLEMENTED | `core/scientific/scientific_store.py` — separate `scientific.db`, full Hypothesis + Evidence CRUD |
| Hypothesis Schema | IMPLEMENTED | `core/schemas/hypothesis_schema.py` — 6 required fields, 4-state lifecycle |
| Evidence Schema | IMPLEMENTED | `core/schemas/evidence_schema.py` — direction, weight, source_id, 4-state lifecycle, FK to hypotheses |
| Reasoning Engine | MISSING | No component exists. No structured event-to-hypothesis interpretation. |
| Decision Approval Engine | MISSING | No component exists. No approval thresholds, readiness scoring, or explainable approval criteria. |
| Outcome Bridge | MISSING | No hypothesis-to-outcome comparison. No verdict assignment (confirmed/rejected/inconclusive). No error classification. |
| Validated Knowledge | MISSING | No Knowledge schema, lifecycle, extraction mechanism, or application tracking. |
| Criterion Metrics | RESEARCH | No CriterionSnapshot. No trend analysis. No calibration measurement. Concept exists in `17_CRITERION_VALIDATION_FRAMEWORK.md`. |
| Scarce Resources Model | RESEARCH | Listed in `05_NORTH_STAR.md`. No formal model, schema, or allocation logic. |
| Innovation System | PLANNED | Not yet added. Will formalize research proposals and structured experimentation. |
| Terminal Cockpit | IMPLEMENTED | CLI with 15+ commands (operational + scientific). Present in laptop version. |
| OSIRIS / Dashboard | LEGACY | "OSIRIS" branding in code (39 occurrences). Dashboard not present in USB version. OSIRIS may be retained as UI/operator name. |
| Telegram Notifications | IMPLEMENTED | `core/engines/telegram_notifier.py` — operational notifications. |
| CLI (scientific commands) | IMPLEMENTED | 7 commands: `hypothesis create/list/show/transition/archive`, `evidence add/list`, `scientific status`. |
| Missed Opportunity Ledger | MISSING | Not designed. No tracking of opportunities the system evaluated but did not act on. |
| Opportunity Uniqueness Score | MISSING | Not designed. No metric for how rare or replaceable an opportunity is. |
| Auto-Approval Readiness Score | MISSING | Not designed. No score indicating when a hypothesis-decision pair is safe for auto-approval. |
| Opportunity Cost Report | MISSING | Not designed. No report showing what was sacrificed by choosing one action over another. |
| Signal-to-Decision Audit | MISSING | Not designed. No audit trail from raw signal through hypothesis to decision. |
| Notification Quality Gate | MISSING | Not designed. No mechanism to prevent notification overload. |

---

## 7. Old Architecture vs Architecture V2

### What Is Preserved

The old architecture's operational components remain valid and continue to function:

- **Sources** — all 8 data feeds
- **Collectors** — all 8 collector classes
- **EventBus** — pub/sub event distribution
- **Agents** — 5 domain agents (will evolve to produce hypotheses, not opinions)
- **Council** — weighted voting (will evolve to evaluate competing hypotheses)
- **Execution** — PaperTradingEngine (will link trades to hypotheses)
- **Risk** — all guard layers (will incorporate scientific approval)
- **Monitoring** — HealthMonitor, FailureClassifier (will add criterion metrics)

### What Is Added

| Component | Old Architecture | Architecture V2 |
|-----------|-----------------|-----------------|
| Reasoning | Not present | New layer between Event and Hypothesis |
| Hypothesis | Not present | First-class object with lifecycle and persistence |
| Evidence | Flat text list in AgentOpinion | Structured object with direction, weight, source, lifecycle |
| Approval | Operational guards only | Decision Approval Engine with explainable criteria |
| Outcome Bridge | PnL recorded | Hypothesis comparison + verdict + error classification |
| Validated Knowledge | Not present | Extracted lessons with lifecycle |
| Criterion | Not measured | Emergent property tracked through CriterionSnapshot |
| Scarce Resources | Capital only (implicit) | 8 resource types with formal model |
| Innovation System | Not present | Research proposals, structured experimentation |

### What Is Reframed

| Element | Old Framing | Architecture V2 Framing |
|---------|-------------|------------------------|
| Trading | Primary purpose | First validation domain |
| Profit | Success metric | Expected consequence of Criterion |
| OSIRIS | Project identity | Interface/operator branding (LEGACY in code) |
| Dashboard | Intelligence core | Interface layer, not intelligence |
| Agents | Opinion producers | Future hypothesis formatters |
| Council | Decision maker | Future hypothesis evaluator |
| Memory | Operational storage | Future scientific record + semantic memory |

---

## 8. Current Gaps

| # | Gap | Why It Matters | Risk If Ignored | Suggested Next Action |
|---|-----|----------------|-----------------|----------------------|
| 1 | **Reasoning layer missing** | The pipeline cannot transform raw events into testable hypotheses. The system detects events but cannot interpret consequences. | The system processes information but does not think. Without reasoning, the gap between Event and Hypothesis remains unfilled. | Design Reasoning Engine spec. Define input (Event), output (Hypothesis), and transformation rules. |
| 2 | **Decision Approval Engine missing** | No mechanism validates that a decision is safe, evidence-based, and ready for execution. | Decisions execute based on council vote alone, not on evidence thresholds. The system acts before it knows whether it should. | Design approval criteria. Define readines thresholds. Build after Innovation System establishes evidence baselines. |
| 3 | **Outcome Bridge missing** | Outcomes are recorded but never compared to the hypothesis that produced them. No verdict assigned. | The learning signal is lost. The system cannot distinguish "correct hypothesis, lucky execution" from "wrong hypothesis, lucky outcome." | Extend Trade record with `hypothesis_id`. Build comparison logic between predicted consequence and actual outcome. |
| 4 | **Validated Knowledge missing** | No mechanism extracts generalizable lessons from outcomes. | Every cycle starts from zero. Learning does not compound. The system may trade for years without accumulating wisdom. | Design Knowledge schema and lifecycle. Align with Iteration 6 of implementation roadmap. |
| 5 | **Scarce Resources model missing** | The system optimizes for capital by default because no other resource is tracked. | Attention, time, and health degrade silently. The system becomes profitable at the cost of the user's well-being. | Define ScarceResource schema. Start with capital + time + attention as measurable resources. |
| 6 | **Innovation System missing** | No structured mechanism proposes, tracks, and validates project experiments. | The project relies on ad-hoc feature ideas. No systematic evidence accumulation about what works. | Design Innovation System after this architecture is adopted. |
| 7 | **Notification Quality Gate missing** | No mechanism prevents notification overload. Every signal generates attention demand. | The system consumes the user's attention — the most scarce resource — without justification. | Design notification priority tiers and user attention budget. |
| 8 | **Missed Opportunity Intelligence missing** | Opportunities the system evaluated but did not act on are not tracked. | The system cannot learn from opportunities it passed on. Selection bias distorts all performance analysis. | Design Missed Opportunity Ledger to track rejected and ignored opportunities with reasoning. |
| 9 | **Opportunity Uniqueness missing** | All opportunities are treated equally. No metric distinguishes rare opportunities from common ones. | The system cannot prioritize. Scarce capital and attention are allocated as if all opportunities have equal value. | Design Opportunity Uniqueness Score. Define baseline as "how often does an opportunity like this appear?" |
| 10 | **Canonical docs inconsistent** | Pipeline descriptions differ across `03_IMPLEMENTATION_BRIDGE.md`, `01_MVP_REDEFINITION.md`, and `CRITERION_AND_CONSEQUENCE_THESIS.md`. No single architecture document exists. | Future contributors (including future self) cannot determine which pipeline is canonical. | This document (`ARCHITECTURE_V2.md`) becomes the single canonical reference. Update conflicting docs to reference it. |
| 11 | **OSIRIS naming creates identity confusion** | 39 occurrences in `core/` code. Module docstrings, class names, user-facing messages use "OSIRIS" branding. | New readers see two identities (OSIRIS + O.M.A.-C.O.R.E.) and cannot tell which is current. | Refactor legacy branding when time permits. OSIRIS may remain as UI/operator interface name only. |

---

## 9. Near-Term Priority Map

Prioritization criteria (from project review protocol):
- **Improve Criterion** — does this component help the system learn?
- **Improve decision quality** — does this component help make better choices?
- **Improve learning** — does this component extract, store, or apply lessons?
- **Protect scarce resources** — does this component preserve capital, time, attention, health?
- **Preserve one-person maintainability** — can one person build and maintain this?
- **Avoid destabilizing operational MVP** — does this component touch operational code?

| Priority | Item | Rationale | Effort | Dependencies |
|----------|------|-----------|--------|--------------|
| **P0** | Canonical Architecture Alignment | No component should be built on an outdated foundation. This document must be adopted as canonical. | Low (documentation) | None |
| **P1** | Innovation System | Formalizes how the project improves itself. Creates the framework for all future experimentation. | Medium | P0 |
| **P2** | Missed Opportunity Ledger | Without this, performance analysis is selection-biased. Cannot evaluate decision quality. | Medium | P1 (provides tracking framework) |
| **P3** | Opportunity Uniqueness Score | Without this, the system cannot prioritize. Scarce resource allocation is blind. | Medium | P2 (ledger provides data) |
| **P4** | Notification Quality Gate | Attention is the most scarce resource. Without this gate, the system consumes attention without justification. | Low-Medium | None (can be implemented independently) |
| **P5** | Auto-Approval Readiness Score | Prerequisite for Level 2 autonomy. Requires evidence that approval criteria work. | Medium | P1, P3 (provides evidence baselines) |
| **P6** | Signal-to-Decision Audit | Traceability from raw signal through hypothesis to decision. Enables quality analysis. | Medium | P0, P2 (provides data structure) |
| **P7** | Reasoning Engine design | Fills the gap between Event and Hypothesis. Requires significant design work. | High (design only) | P0 (architecture alignment) |
| **P8** | Decision Approval Engine design | Fills the gap between Decision and Execution. Requires approval criteria definition. | High (design only) | P5, P7 |
| **P9** | Outcome Bridge design | Compares outcomes to hypotheses. Requires Hypothesis link on trades. | Medium (design only) | P0, existing Hypothesis implementation |

**Execution rules:**
- No execution logic changes until P8 is designed and validated.
- No real capital until Decision Approval Engine evidence exists (at least 100 approved decisions with known outcomes).
- No automatic execution until Level 2 autonomy criteria are met.

---

## 10. Automation Philosophy

### Autonomy Ladder

| Level | Name | Description | Current Status |
|-------|------|-------------|----------------|
| **Level 0** | Inform | System observes, analyzes, and reports. All decisions are human-made. | ✅ Achieved (laptop version with terminal cockpit) |
| **Level 1** | Recommend | System proposes actions with evidence and confidence. Human must approve. | ✅ Achieved (Council produces recommendations, human-in-loop) |
| **Level 2** | Auto-execute (Conditional) | System executes approved decision classes automatically. Must explain every action: why it acted, what evidence supported it, what risk it assumed, what outcome it produced. | 🟡 Target — not yet achieved. Requires Decision Approval Engine evidence. |
| **Level 3** | Autonomous Management | System manages its own resource allocation, learning cycles, and experiment design within defined boundaries. | ❌ Far future. Requires all layers operational. |

### Current Target: Level 2

The system should eventually execute approved decisions automatically, but only after:

1. The Decision Approval Engine has processed at least 100 decisions with known outcomes
2. Auto-Approval Readiness Score exceeds threshold for the specific hypothesis-decision pair
3. Every automatic action produces an explainable record: hypothesis chosen, evidence considered, alternatives rejected, risk assumed, expected outcome, actual outcome

### The Rule

> No automatic decision may exist if the system cannot explain why it acted, what evidence supported it, what risk it assumed, and what outcome it produced.

This rule is absolute. Any automatic execution that violates it must be immediately disabled.

---

## 11. One-Person Army Constraint

O.M.A.-C.O.R.E. is currently built and maintained by one person. Every architecture decision must respect this constraint.

### Implications

- **Every component must be buildable by one person** — no component should require a team to design, implement, test, or maintain
- **Every component must be understandable by one person** — no component should require a specialist to operate or debug
- **Every component must be testable by one person** — test suites must run in minutes, not hours
- **Every component must be maintainable by one person** — the bus factor is 1. Documentation, tests, and simplicity are survival requirements

### Rules

1. No component may be added only because it is interesting. Every addition must justify its existence against the project's criteria.
2. When two designs would both work, prefer the one with fewer components, fewer dependencies, and fewer assumptions. (Design Principle 3)
3. Complexity is debt. The default answer to any proposed addition is no. The proposer must demonstrate how the addition serves the project's principles. (Constitution Article 4)
4. The system must be maintainable with a text editor, a Python interpreter, and internet access. No proprietary tools, no paid services, no build pipelines that one person cannot manage.

### Current Health

| Metric | Status |
|--------|--------|
| Lines of Python code (core/) | ~8,000 |
| Total tests | 303 |
| Test run time | ~78s |
| External dependencies | Minimal (python-dotenv, aiohttp, requests, websocket, etc.) |
| Database | SQLite (zero-administration) |
| Deployment | Local execution |

This is healthy for a one-person project. The scientific layer added only ~500 lines. The constraint is working.

---

## 12. USB vs Operational Branch Strategy

### Branch Roles

| Branch | Role | Constraints | Who Runs It |
|--------|------|-------------|-------------|
| **USB (Innovation)** | Development, research, experiment design, scientific layer implementation | No real capital, no operational stability requirements | Developer |
| **Laptop (Operational)** | Stable validation, paper trading, Extended Demo, telemetry collection | Must stay operationally stable, must not introduce regressions | Operational system |

### Flow

```
Idea (anywhere)
    ↓
Design in USB (new feature document, schema, tests)
    ↓
Implement in USB (code, tests, CLI)
    ↓
Validate in USB (tests pass, no regression)
    ↓
Integrate into Operational Laptop (merge, run Extended Demo)
    ↓
Extended Demo (7+ days continuous operation)
    ↓
Stable deployment on laptop
    ↓
Real capital decision (only after Decision Approval evidence exists)
```

### Separation

- `scientific.db` lives on USB. `oma_core.db` lives on laptop. They are independent.
- The operational pipeline on the laptop does not depend on the scientific layer to function.
- The scientific layer on USB reads from but does not write to the operational database.
- This separation is an architecture invariant — operational stability must not be sacrificed for new features.

---

## 13. Architecture Invariants

These principles are untouchable. They survive every iteration, every refactoring, every technology migration. They define what O.M.A.-C.O.R.E. is.

### Invariant 1 — Criterion Is Emergent

Criterion is never a component, engine, or module. It is not built. It emerges from the interaction of hypotheses, evidence, decisions, outcomes, reflection, and knowledge over time. No single piece of code produces Criterion. Any design that treats Criterion as buildable is wrong.

### Invariant 2 — Evidence Only Exists Relative to a Hypothesis

Evidence without a hypothesis is noise. Every piece of evidence must be linked to exactly one hypothesis. Evidence has direction (supports or contradicts) and decays over time. Evidence that cannot be linked to a hypothesis should not be stored as evidence.

### Invariant 3 — Every Autonomous Action Must Be Explainable

No automatic decision may execute if the system cannot produce a record answering: why this action, what evidence supported it, what risk was assumed, what outcome is expected. Unexplainable actions are not allowed at any autonomy level.

### Invariant 4 — Every Important Decision Must Leave a Record

The record must capture: the hypothesis(es) considered, evidence available at decision time, alternatives evaluated, confidence at decision time, the actual decision, and the expected outcome. Records are immutable — they capture what was known when the decision was made, preventing hindsight bias.

### Invariant 5 — Learning Requires Outcomes

A hypothesis that is never tested produces no learning. A decision that is never executed produces no evidence. The system must close the loop: hypothesis → decision → action → outcome → reflection → knowledge. Cycles that do not close are wasted.

### Invariant 6 — Operational Stability Outranks Feature Growth

The operational MVP must continue functioning while the scientific layer is developed. No scientific feature may destabilize the event-to-action pipeline. If a feature requires destabilization, it must be designed to run independently until stable.

### Invariant 7 — Trading Validates the System but Does Not Define It

Trading is the first experimental domain. It provides fast feedback and measurable outcomes. But the system is not a trading system. Its architecture must not assume trading is its final identity. The same layers that support trading must support entrepreneurship, creation, and any domain where Criterion improves decisions.

### Invariant 8 — Scarce Resources Are the Strategic Output

The system's ultimate output is not profit — it is better access to scarce resources: capital, time, attention, knowledge, relationships, mobility, health, and freedom of decision. Profit is one resource among many. The architecture must not optimize a single resource at the expense of others.

### Invariant 9 — No Idea Is Sacred. Only Evidence Is.

Every concept, every component, every principle is provisional. When evidence contradicts a position, the position yields. The project is not attached to its own ideas. It is attached to its evidence.

### Invariant 10 — The System Must Protect Attention, Not Consume It

The user's attention is the most scarce resource. Every notification, every recommendation, every dashboard element consumes attention. The system must justify every unit of attention it consumes. If a feature consumes more attention than it saves, it is a net negative regardless of its other benefits.

---

## 14. ASCII Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        O.M.A.-C.O.R.E. — Architecture V2                     │
│               Decision Intelligence System — Canonical Architecture           │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────────────┐
                              │      REALITY / SOURCES       │
                              │  (Market, News, Macro, ...)  │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │        COLLECTORS            │
                              │  (8 data feeds, WorldMonitor) │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │     VALIDATION / QUALITY     │
                              │  (retry, rate limit, stats)  │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │         EVENT LAYER          │
                              │   (Event Schema, EventBus)   │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐  ┌──────────────────┐
                              │      REASONING LAYER         │  │  INNOVATION       │
                              │     (MISSING — design)       │  │  SYSTEM           │
                              └─────────────┬───────────────┘  │  (PLANNED)        │
                                            │                  └──────────────────┘
                              ┌─────────────▼───────────────┐
                              │      SCIENTIFIC LAYER        │
                              │  Hypothesis + Evidence Life- │
                              │  cycles, Scientific Store    │
                              │  (PARTIAL — implemented)     │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │    DECISION INTELLIGENCE     │
                              │  (Council, hypothesis eval)  │
                              │  (PARTIAL — no hypothesis    │
                              │   link yet)                  │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │        APPROVAL LAYER        │
                              │  (MISSING — Decision Approv- │
                              │   al Engine, Readiness Score)│
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │   EXECUTION / ACTION LAYER   │
                              │  PaperTrading, Risk Guards   │
                              │  (IMPLEMENTED — no real cap) │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐  ┌──────────────────┐
                              │        OUTCOME LAYER         │  │  MONITORING /     │
                              │  (PARTIAL — trades recorded, │  │  AUDIT            │
                              │   no hypothesis comparison)  │  │  Health, Failure, │
                              └─────────────┬───────────────┘  │  Telemetry        │
                                            │                  └──────────────────┘
                              ┌─────────────▼───────────────┐
                              │    VALIDATED KNOWLEDGE       │
                              │  (MISSING — no extraction)   │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │        CRITERION LAYER       │
                              │  (EMERGENT — measured, not   │
                              │   built. No CriterionSnapshot)│
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │     SCARCE RESOURCES LAYER   │
                              │  (RESEARCH — no formal model)│
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │       REINVESTMENT LOOP      │
                              │  (RESEARCH — not designed)   │
                              └─────────────┬───────────────┘
                                            │
                                            ▼
                              Back to Reasoning Layer
                          (stronger Criterion, better hypotheses)


┌─────────────────────────────────────────────────────────────────────────────┐
│                          SUPPORT / SIDE SYSTEMS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │    RISK / SURVIVAL  │  │     MEMORY        │  │      INTERFACES          │ │
│  │  CapitalGuard       │  │  Short-term       │  │  Terminal Cockpit (CLI) │ │
│  │  CrashDetector      │  │  Long-term        │  │  Telegram Notifications │ │
│  │  KnifeDetector      │  │  Performance      │  │  OSIRIS (legacy brand)  │ │
│  │  DirectionController │  │  Memory           │  │  Dashboard (planned)   │ │
│  │  GapRisk            │  │  Scientific Store │  │                         │ │
│  │  SlippageEngine     │  │  (separate DB)    │  │                         │ │
│  └────────────────────┘  └──────────────────┘  └──────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              DEPLOYMENT                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  USB (Innovation)           ──── merge ────▶  Laptop (Operational)           │
│  ├── Scientific Layer                        ├── Extended Demo running      │
│  ├── Hypothesis + Evidence                   ├── Paper trading active       │
│  ├── Design docs                             ├── Telemetry collection       │
│  └── Tests                                   └── No real capital            │
│                                                                              │
│  Neither branch uses real capital.                                          │
│  Real capital only after Decision Approval evidence exists.                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Recommendation

### Go / No-Go Decisions

| Action | Verdict | Rationale |
|--------|---------|-----------|
| **Adopt Architecture V2 as canonical** | **GO** | The USB version needs a single authoritative architecture document. This fills the gap left by missing MVP2_ARCHITECTURE.md and supersedes conflicting pipeline descriptions. |
| **Build Innovation System** | **GO** (after architecture adoption) | The Innovation System formalizes experimentation. It does not modify operational code. It is safe to build on USB while the laptop runs the Extended Demo. |
| **Observability and learning-oriented green-lane ideas** | **GO** | Missed Opportunity Ledger, Opportunity Uniqueness Score, Notification Quality Gate — these are additive, do not destabilize operations, and improve learning. |
| **Outcome Bridge** | **PAUSE** | Requires careful design. Touches the Trade record and operational pipeline. Must not destabilize the Extended Demo. Design first, implement after design review. |
| **Execution / capital allocation changes** | **NO-GO** | No changes to PaperTradingEngine, risk guards, or any execution path. The operational MVP must remain stable. Real capital is not authorized at any point. |
| **Real capital deployment** | **NO-GO** | Not authorized. Not designed. Not tested. Real capital requires Level 2 autonomy evidence (100+ approved decisions with verified outcomes). |

### Final Recommendation Summary

1. **Adopt this document** as the canonical architecture. Update `03_IMPLEMENTATION_BRIDGE.md` to reference it.
2. **Start Innovation System design** on USB. It formalizes the project's improvement process without touching operational code.
3. **Design (not implement)** Reasoning Engine and Decision Approval Engine specs. These are the next architectural gaps that need filling before any autonomy increase.
4. **Keep the laptop version running** the Extended Demo. Do not destabilize it. The USB version is where new components are built and tested.
5. **No real capital.** Not now. Not soon. Only after the Decision Approval Engine has processed at least 100 decisions with verified outcomes.

---
