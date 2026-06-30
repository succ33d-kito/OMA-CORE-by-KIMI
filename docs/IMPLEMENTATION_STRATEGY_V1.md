# IMPLEMENTATION_STRATEGY_V1 — O.M.A.-C.O.R.E.

**Project:** O.M.A.-C.O.R.E.

**Version:** 1.0

**Status:** CANONICAL IMPLEMENTATION STRATEGY

**Date:** June 2026

**Scope:** Architecture and planning only

---

# 1. Purpose

IMPLEMENTATION_STRATEGY_V1 defines the recommended implementation order for O.M.A.-C.O.R.E. from the current architecture toward the long-term decision intelligence vision.

Implementation order matters because O.M.A.-C.O.R.E. is no longer a trading prototype. It is a decision intelligence system whose long-term value depends on traceability, evidence generation, scientific learning, and Criterion development. Building features out of order can create hidden coupling, partial subsystems, lost lineage, and premature autonomy.

The purpose of this document is not to maximize development speed.

The purpose is to maximize:

- architectural stability;
- evidence generation;
- long-term maintainability;
- one-person operability;
- measurable progress through complete capabilities.

Capabilities are more important than features.

A feature is an isolated behavior.

A capability is a complete, usable improvement that produces evidence and preserves architecture.

Every sprint must deliver one complete capability or one complete architectural foundation required by a capability. No sprint should leave a subsystem partially wired into the platform without a clear evidence gate and ownership boundary.

This document respects and does not redefine:

- `ARCHITECTURE_V2.md`
- `PIPELINE_V2.md`
- `INTEGRATION_ARCHITECTURE_V1.1.md`
- `OBJECT_MODEL_V1.md`

Sprint 15A remains exactly as defined by `INTEGRATION_ARCHITECTURE_V1.1.md`.

Sprint 15A is foundation only.

The first demonstrable execution flow capability begins in Sprint 15B.

---

# 2. Implementation Philosophy

The implementation philosophy is:

Architecture before implementation.

Capabilities before features.

Evidence before autonomy.

Stability before expansion.

One-person maintainability before system complexity.

## 2.1 Small vertical slices

Work should be organized into the smallest complete vertical slice that produces architectural evidence.

A vertical slice is preferred over a broad horizontal subsystem when it can prove an end-to-end contract earlier.

## 2.2 End-to-end capabilities

A capability is complete only when the object flow can be demonstrated through its intended boundary.

A skeleton may be useful, but a skeleton alone is not a capability unless the sprint is explicitly an architectural foundation sprint.

Sprint 15A is such a foundation sprint.

Sprint 15B is the first execution-flow capability sprint.

## 2.3 Incremental validation

Each sprint must define validation evidence before implementation begins.

Validation must prove that the intended architectural contract works, not merely that files exist.

## 2.4 Continuous architectural verification

Every sprint must verify:

- canonical object ownership;
- allowed module changes;
- forbidden module boundaries;
- traceability propagation;
- absence of circular dependencies;
- no bypass of Pipeline V2.

## 2.5 Minimal coupling

New components should depend only on upstream canonical objects and their own internal objects.

Downstream consumers may read outputs but may not own upstream data.

## 2.6 Maximum observability

Every meaningful transition should be observable through logs, reports, ledger records, tests, or explicit artifacts.

Observability is not optional because O.M.A.-C.O.R.E. depends on evidence.

## 2.7 No intentional technical debt

No sprint may introduce technical debt intentionally.

If a shortcut is required to unblock progress, it must be explicitly documented as an architectural risk and resolved before higher-level capabilities depend on it.

---

# 3. Capability Roadmap

Development is organized into capabilities, not features.

---

## Capability 01 — Canonical Architecture Baseline

**Objective**

Freeze the architectural documents that govern implementation.

**Business Value**

Prevents rework, ambiguity, and implementation drift.

**Architectural Value**

Establishes the canonical system language and module boundaries.

**Dependencies**

None.

**Evidence Produced**

- Architecture V2 exists.
- Pipeline V2 exists.
- Integration Architecture V1.1 exists.
- Object Model V1 exists.
- Implementation Strategy V1 exists.

**Definition of Done**

All canonical documents exist, do not contradict each other, and are used as implementation prerequisites.

---

## Capability 02 — Execution Engine Foundation

**Objective**

Create the isolated internal Execution Engine foundation.

**Business Value**

Provides the execution backbone without broker dependence.

**Architectural Value**

Separates execution ownership from integration and preserves internal simulation as the default mode.

**Dependencies**

Capability 01.

**Evidence Produced**

- Execution Engine directory and package structure.
- Internal object skeletons.
- Enums.
- Configuration structure.
- Exception hierarchy.
- Test organization.
- Documentation comments.

**Definition of Done**

Sprint 15A exit criteria are satisfied. No execution behavior exists yet.

---

## Capability 03 — Minimal Execution Flow

**Objective**

Demonstrate the minimal internal flow from approved intent to execution result.

**Business Value**

Proves that execution can be modeled internally before portfolio, positions, or broker integration.

**Architectural Value**

Validates the boundary:

ApprovedDecision → ExecutionSignal → ExecutionRequest → ExecutionResult

**Dependencies**

Capability 02.

**Evidence Produced**

- Minimal simulated flow test.
- Trace identifiers preserved.
- ExecutionResult produced without broker, portfolio, position, PnL, or Scientific Layer dependency.

**Definition of Done**

Sprint 15B exit criteria are satisfied.

---

## Capability 04 — Internal Order and Ledger Integrity

**Objective**

Introduce internal order lifecycle and append-only execution ledger integrity.

**Business Value**

Makes execution reconstructible.

**Architectural Value**

Validates that Engine-owned operations are recorded immutably.

**Dependencies**

Capability 03.

**Evidence Produced**

- ExecutionOrder lifecycle evidence.
- ExecutionLedgerRecord append-only evidence.
- No mutation of prior ledger records.

**Definition of Done**

Order state transitions and ledger append behavior are traceable and tested in simulation.

---

## Capability 05 — Virtual Position and Portfolio Consistency

**Objective**

Introduce virtual positions and portfolio state snapshots.

**Business Value**

Allows internal simulation to represent position and resource exposure.

**Architectural Value**

Validates ExecutionPosition and ExecutionPortfolio as Engine-owned internal objects.

**Dependencies**

Capability 04.

**Evidence Produced**

- Position lifecycle evidence.
- Portfolio snapshot evidence.
- Ledger-backed portfolio state trace.

**Definition of Done**

Position and portfolio state are internally consistent, reconstructible, and isolated from Council, Score Engine, and Scientific Layer.

---

## Capability 06 — Outcome Handoff

**Objective**

Connect ExecutionResult to Outcome Collector without Scientific interpretation.

**Business Value**

Converts execution facts into learning-ready outcomes.

**Architectural Value**

Validates the Pipeline V2 boundary:

ExecutionResult → Outcome

**Dependencies**

Capability 05.

**Evidence Produced**

- Outcome created from ExecutionResult.
- Trace identifiers preserved.
- No Knowledge created by Execution Engine.

**Definition of Done**

Outcome Collector consumes ExecutionResult and produces Outcome without mutating execution objects.

---

## Capability 07 — Scientific Ingestion from Outcomes

**Objective**

Allow Scientific Layer to consume Outcomes and produce Evidence or Knowledge according to existing scientific contracts.

**Business Value**

Turns internal simulation into learning material.

**Architectural Value**

Validates the separation between execution and learning.

**Dependencies**

Capability 06.

**Evidence Produced**

- Outcome comparison evidence.
- Evidence creation evidence.
- Knowledge extraction evidence where appropriate.

**Definition of Done**

Scientific Layer consumes Outcome downstream only and never produces orders or modifies execution.

---

## Capability 08 — Criterion Generation

**Objective**

Generate Criterion and CriterionDelta from validated Knowledge.

**Business Value**

Moves the system from recording outcomes to improving judgment.

**Architectural Value**

Validates the strategic purpose of Architecture V2.

**Dependencies**

Capability 07.

**Evidence Produced**

- Criterion objects.
- CriterionDelta objects.
- Traceability to Knowledge and Outcome.

**Definition of Done**

Criterion change is measurable, traceable, and not reduced to capital performance alone.

---

## Capability 09 — Resource Loop

**Objective**

Represent ResourceState from CriterionDelta.

**Business Value**

Connects decision intelligence to scarce resources.

**Architectural Value**

Completes the strategic loop.

**Dependencies**

Capability 08.

**Evidence Produced**

- ResourceState snapshots.
- Traceability to CriterionDelta.
- Explicit resource context.

**Definition of Done**

ResourceState exists as strategic context without creating Events or Decisions directly.

---

## Capability 10 — Future External Integration Readiness

**Objective**

Prepare optional integration infrastructure after internal execution proves stable.

**Business Value**

Allows future broker or platform connectivity without redesigning the core.

**Architectural Value**

Keeps Integration Layer optional and subordinate to Execution Engine.

**Dependencies**

Capabilities 02 through 06 at minimum. Capability 07 recommended.

**Evidence Produced**

- Adapter boundary design.
- No broker-specific coupling in Execution Engine.
- Simulation remains valid without external services.

**Definition of Done**

External integration can be added as an extension, not as a replacement for internal execution.

---

## Capability 11 — Controlled Paper or Shadow Mode

**Objective**

Introduce non-live external comparison or paper execution only after internal evidence is sufficient.

**Business Value**

Validates internal execution against external environments without capital risk.

**Architectural Value**

Tests broker-agnostic boundaries.

**Dependencies**

Capability 10 and explicit architectural approval.

**Evidence Produced**

- External telemetry.
- Adapter traceability.
- No Decision or ExecutionSignal mutation by external platform.

**Definition of Done**

Paper or Shadow mode operates without increasing autonomy and without compromising internal ledger integrity.

---

## Capability 12 — Live Trading Readiness Review

**Objective**

Determine whether live execution can ever be considered.

**Business Value**

Protects capital and system integrity.

**Architectural Value**

Ensures evidence before autonomy.

**Dependencies**

Capabilities 01 through 11 and a separate canonical architecture decision.

**Evidence Produced**

- Longitudinal simulation evidence.
- Paper or Shadow evidence if authorized.
- Ledger integrity evidence.
- Outcome and Criterion evidence.
- Risk and safety evidence.

**Definition of Done**

A formal readiness decision exists. LIVE remains prohibited until explicitly approved.

---

# 4. Sprint Roadmap

This roadmap recommends implementation order. It does not redefine already canonical sprint scopes.

---

## Sprint 15A — Execution Engine Foundation

**Objective**

Create the isolated foundation of the internal Execution Engine.

**Scope**

Foundation only.

**Modules allowed to change**

- New Execution Engine module paths only.
- New Execution Engine documentation if required.
- New Execution Engine test organization.

**Modules forbidden to change**

- Collectors.
- Pipeline.
- Council.
- Score Engine.
- Scientific Layer.
- Operational Database.
- Telegram.
- CLI.
- Integration Layer.

**Expected deliverables**

- Directory structure.
- Package structure.
- Canonical object skeletons.
- Enums.
- Configuration structure.
- Exception hierarchy.
- Documentation comments.
- Test organization.

**Evidence required**

- File tree evidence.
- Import/package organization evidence where applicable.
- No behavioral execution tests required.
- Verification that forbidden modules were not modified.

**Exit criteria**

Sprint 15A exits when the foundation exists and remains isolated.

Sprint 15A explicitly excludes execution behavior.

---

## Sprint 15B — Minimal Internal Execution Flow

**Objective**

Demonstrate the minimal internal execution flow.

**Scope**

ApprovedDecision → ExecutionSignal → ExecutionRequest → ExecutionResult

No portfolio.

No positions.

No PnL.

No broker integration.

No scientific ingestion.

**Modules allowed to change**

- Execution Engine only.
- Execution Engine tests only.

**Modules forbidden to change**

- Collectors.
- Council.
- Score Engine.
- Scientific Layer.
- Operational Database.
- Telegram.
- CLI unless a later architecture decision authorizes CLI exposure.
- Integration Layer.

**Expected deliverables**

- Minimal internal flow.
- ExecutionRequest produced from ExecutionSignal.
- ExecutionResult produced from ExecutionRequest.
- Trace identifiers preserved.
- Tests proving the flow.

**Evidence required**

- Test evidence for successful flow.
- Test evidence for rejected invalid input.
- Traceability evidence.
- No broker dependency evidence.

**Exit criteria**

The minimal simulated flow works and produces ExecutionResult without portfolio, positions, PnL, broker, or Scientific Layer dependencies.

---

## Sprint 15C — Orders and Ledger

**Objective**

Add internal order lifecycle and append-only ledger recording.

**Scope**

ExecutionOrder and ExecutionLedgerRecord.

**Modules allowed to change**

- Execution Engine orders domain.
- Execution Engine ledger domain.
- Execution Engine tests.

**Modules forbidden to change**

- Collectors.
- Council.
- Score Engine.
- Scientific Layer.
- Operational Database.
- Telegram.
- CLI unless explicitly authorized.
- Integration Layer.

**Expected deliverables**

- Order state architecture implemented.
- Ledger records created for Engine operations.
- Append-only behavior verified.

**Evidence required**

- Order transition evidence.
- Ledger append evidence.
- Ledger immutability evidence.

**Exit criteria**

Every internal execution operation can be reconstructed from the ledger.

---

## Sprint 15D — Positions and Portfolio Snapshots

**Objective**

Add virtual position lifecycle and portfolio state snapshots.

**Scope**

ExecutionPosition and ExecutionPortfolio.

**Modules allowed to change**

- Execution Engine positions domain.
- Execution Engine portfolio domain.
- Execution Engine metrics placeholders if required.
- Execution Engine tests.

**Modules forbidden to change**

- Collectors.
- Council.
- Score Engine.
- Scientific Layer.
- Operational Database.
- Telegram.
- Integration Layer.

**Expected deliverables**

- Position lifecycle.
- Portfolio snapshot model.
- Ledger-backed consistency checks.

**Evidence required**

- Position lifecycle evidence.
- Portfolio snapshot traceability evidence.
- No PnL optimization or strategy logic.

**Exit criteria**

Virtual position and portfolio state are internally consistent and ledger-traceable.

---

## Sprint 15E — Execution Engine End-to-End Simulation Validation

**Objective**

Validate the internal Execution Engine from ExecutionSignal through ExecutionResult with orders, positions, portfolio snapshots, and ledger evidence.

**Scope**

Internal simulation only.

**Modules allowed to change**

- Execution Engine.
- Execution Engine tests.
- Documentation associated with Execution Engine.

**Modules forbidden to change**

- Collectors.
- Council.
- Score Engine.
- Scientific Layer.
- Telegram.
- Integration Layer.
- Broker adapters.

**Expected deliverables**

- End-to-end internal simulation test.
- Complete trace evidence.
- Ledger evidence.
- Portfolio consistency evidence.
- ExecutionResult evidence.

**Evidence required**

- Execution correctness.
- Portfolio consistency.
- Ledger integrity.
- No external broker dependency.
- No Scientific Layer mutation.

**Exit criteria**

Execution Engine can produce auditable ExecutionResult in SIMULATION mode using internal Engine objects only.

---

## Sprint 16 — Outcome Handoff

**Objective**

Connect ExecutionResult to Outcome Collector.

**Scope**

ExecutionResult → Outcome.

**Modules allowed to change**

- Outcome Collector.
- Execution Engine handoff boundary if required.
- Tests for handoff.

**Modules forbidden to change**

- Council.
- Score Engine.
- Collectors.
- Telegram.
- Broker integration.

**Expected deliverables**

- Outcome produced from ExecutionResult.
- Trace IDs preserved.
- No Knowledge creation by Execution Engine.

**Evidence required**

- Outcome traceability test.
- No mutation of ExecutionResult.

**Exit criteria**

Outcome Collector can consume ExecutionResult and produce Outcome.

---

## Sprint 17 — Scientific Ingestion

**Objective**

Allow Scientific Layer to consume Outcomes and produce Evidence or Knowledge according to existing scientific contracts.

**Scope**

Outcome → Evidence → Knowledge.

**Modules allowed to change**

- Scientific Layer.
- Scientific tests.
- Documentation.

**Modules forbidden to change**

- Execution Engine internals unless handoff contract requires a documented read-only adjustment.
- Council.
- Score Engine.
- Collectors.

**Expected deliverables**

- Outcome comparison.
- Evidence association.
- Knowledge extraction where supported.

**Evidence required**

- Scientific ingestion test.
- No operational DB mutation by Scientific Layer.
- No orders produced by Scientific Layer.

**Exit criteria**

Scientific Layer learns downstream only.

---

## Sprint 18 — Criterion Generation

**Objective**

Generate Criterion and CriterionDelta from Knowledge.

**Scope**

Knowledge → Criterion → CriterionDelta.

**Modules allowed to change**

- Criterion Engine.
- Scientific or Criterion storage if architecture permits.
- Tests.

**Modules forbidden to change**

- Execution Engine.
- Council.
- Score Engine.
- Collectors.
- Integration Layer.

**Expected deliverables**

- Criterion objects.
- CriterionDelta objects.
- Traceability to Knowledge.

**Evidence required**

- Criterion generation evidence.
- CriterionDelta traceability evidence.

**Exit criteria**

Criterion development is measurable from Knowledge.

---

## Sprint 19 — Resource Loop

**Objective**

Create ResourceState from CriterionDelta.

**Scope**

CriterionDelta → ResourceState.

**Modules allowed to change**

- Resource Loop.
- Strategic context documentation and tests.

**Modules forbidden to change**

- Execution Engine.
- Council.
- Score Engine.
- Collectors.

**Expected deliverables**

- ResourceState snapshots.
- Resource traceability.

**Evidence required**

- ResourceState evidence.
- No direct Event or Decision creation from ResourceState.

**Exit criteria**

Strategic loop is represented without control-flow shortcuts.

---

## Sprint 20 — External Integration Readiness Review

**Objective**

Decide whether optional external integration infrastructure should be designed.

**Scope**

Architecture review only unless a new implementation sprint is explicitly approved.

**Modules allowed to change**

- Architecture documents if an architectural decision is made.

**Modules forbidden to change**

- Broker adapters.
- Live execution.
- Execution Engine behavior.

**Expected deliverables**

- Readiness report.
- Evidence review.
- Go or no-go decision for integration architecture work.

**Evidence required**

- Execution Engine stability evidence.
- Ledger evidence.
- Outcome evidence.
- Scientific evidence.

**Exit criteria**

External integration remains future work unless explicitly authorized.

---

# 5. Sprint 15

Sprint 15 is completely defined as:

**Execution Engine Foundation and Internal Simulation Backbone.**

Its goal is not paper trading.

Its goal is creating the execution backbone of O.M.A.-C.O.R.E.

Sprint 15 must not introduce broker connectivity.

Sprint 15 must not introduce TradingView.

Sprint 15 must not modify Scientific Layer.

Sprint 15 must not change Council, Score Engine, Collectors, Telegram, or the operational database.

---

## Sprint 15A — Foundation Only

**Purpose**

Create the isolated structure and architectural code foundation for the Execution Engine.

**Canonical status**

Defined by `INTEGRATION_ARCHITECTURE_V1.1.md`.

This document references it and does not modify it.

**Includes**

- Directory structure.
- Package structure.
- Canonical objects.
- Enums.
- Configuration structure.
- Exception hierarchy.
- Documentation comments.
- Test organization.

**Excludes**

- Execution behavior.
- Flow demonstration.
- Trading algorithms.
- Broker connectivity.
- External adapters.
- Market APIs.
- CLI integration.
- Scientific ingestion.

**Exit principle**

Sprint 15A ends when the Execution Engine foundation exists and is isolated.

---

## Sprint 15B — Minimal Flow Demonstration

**Purpose**

Introduce the first demonstrable execution capability.

**Flow**

ApprovedDecision

↓

ExecutionSignal

↓

ExecutionRequest

↓

ExecutionResult

**Includes**

- Minimal simulated flow.
- Traceability propagation.
- ExecutionResult creation.
- Tests proving the flow.

**Excludes**

- Portfolio.
- Positions.
- PnL.
- Broker integration.
- Scientific ingestion.
- Ledger completeness beyond minimal trace if not yet part of 15B scope.

**Exit principle**

Sprint 15B ends when the minimal flow works correctly in simulation and produces traceable ExecutionResult.

---

## Sprint 15C — Orders and Ledger

**Purpose**

Make internal execution reconstructible.

**Includes**

- ExecutionOrder lifecycle.
- ExecutionLedgerRecord append-only behavior.
- Ledger traceability tests.

**Excludes**

- Portfolio calculations.
- PnL.
- Scientific ingestion.
- Broker integration.

**Exit principle**

Sprint 15C ends when internal execution operations are ledger-traceable and append-only.

---

## Sprint 15D — Positions and Portfolio

**Purpose**

Represent virtual exposure and portfolio state.

**Includes**

- ExecutionPosition lifecycle.
- ExecutionPortfolio snapshots.
- Ledger-backed consistency.

**Excludes**

- Optimization.
- Live trading.
- Broker integration.
- Scientific ingestion.

**Exit principle**

Sprint 15D ends when virtual position and portfolio state can be reconstructed from Engine-owned records.

---

## Sprint 15E — Internal End-to-End Validation

**Purpose**

Validate the complete internal Execution Engine in SIMULATION mode.

**Includes**

- ExecutionSignal through ExecutionResult.
- ExecutionRequest.
- ExecutionOrder.
- ExecutionPosition.
- ExecutionPortfolio.
- ExecutionLedgerRecord.
- Execution metrics placeholders if needed for evidence.
- End-to-end tests.

**Excludes**

- Outcome ingestion.
- Scientific Learning.
- Broker adapters.
- Paper mode.
- Live mode.

**Exit principle**

Sprint 15E ends when the internal Execution Engine can produce an auditable ExecutionResult in SIMULATION mode without external dependencies.

---

# 6. Dependency Graph

Mandatory capability dependency graph:

Capability 01 — Canonical Architecture Baseline

↓

Capability 02 — Execution Engine Foundation

↓

Capability 03 — Minimal Execution Flow

↓

Capability 04 — Internal Order and Ledger Integrity

↓

Capability 05 — Virtual Position and Portfolio Consistency

↓

Capability 06 — Outcome Handoff

↓

Capability 07 — Scientific Ingestion from Outcomes

↓

Capability 08 — Criterion Generation

↓

Capability 09 — Resource Loop

↓

Capability 10 — Future External Integration Readiness

↓

Capability 11 — Controlled Paper or Shadow Mode

↓

Capability 12 — Live Trading Readiness Review

## Mandatory Prerequisites

- Minimal Execution Flow must not start before Execution Engine Foundation exists.
- Orders and Ledger must not start before Minimal Execution Flow works.
- Positions and Portfolio must not start before Ledger integrity exists.
- Outcome Handoff must not start before ExecutionResult is stable.
- Scientific Ingestion must not start before Outcome is traceable.
- Criterion Generation must not start before Knowledge is traceable.
- Resource Loop must not start before CriterionDelta is traceable.
- External Integration must not start before internal Execution Engine evidence exists.
- Paper or Shadow Mode must not start before external integration readiness is approved.
- Live Trading must not start before a separate canonical readiness decision.

## Explicit Prohibitions

Do not implement higher-level capabilities before prerequisites exist.

Do not introduce broker integration before internal simulation is stable.

Do not introduce scientific ingestion before Outcome traceability exists.

Do not introduce Criterion generation before Knowledge exists.

Do not introduce ResourceState before CriterionDelta exists.

---

# 7. Evidence Gates

Evidence gates are mandatory before progressing.

---

## Gate 01 — Architecture Consistency

**Acceptance Criteria**

- Implementation references canonical documents.
- No contradiction with Architecture V2, Pipeline V2, Integration Architecture V1.1, or Object Model V1.
- Forbidden modules are unchanged.

**Required Before**

Every sprint.

---

## Gate 02 — Execution Foundation Integrity

**Acceptance Criteria**

- Execution Engine exists as isolated module foundation.
- No execution behavior exists in Sprint 15A.
- No broker dependency exists.
- No Scientific Layer dependency exists.

**Required Before**

Sprint 15B.

---

## Gate 03 — Execution Correctness

**Acceptance Criteria**

- ApprovedDecision can be represented as upstream approved input.
- ExecutionSignal can be consumed by Execution Engine.
- ExecutionRequest can be created internally.
- ExecutionResult can be produced.
- Trace identifiers are preserved.

**Required Before**

Sprint 15C.

---

## Gate 04 — Ledger Integrity

**Acceptance Criteria**

- Every Engine operation requiring history creates a ledger record.
- Ledger records are append-only.
- No ledger record is modified or deleted.
- Corrections are represented by new records.

**Required Before**

Sprint 15D.

---

## Gate 05 — Portfolio Consistency

**Acceptance Criteria**

- Portfolio snapshots reference ledger records.
- Position state and portfolio state do not contradict each other.
- Historical portfolio snapshots are immutable.

**Required Before**

Sprint 15E completion and Outcome Handoff.

---

## Gate 06 — Outcome Traceability

**Acceptance Criteria**

- Outcome references ExecutionResult.
- Outcome preserves upstream execution and decision identifiers.
- Outcome is factual and does not create Knowledge.

**Required Before**

Scientific ingestion.

---

## Gate 07 — Scientific Ingestion

**Acceptance Criteria**

- Scientific Layer consumes Outcome downstream only.
- Evidence or Knowledge references Outcome.
- Scientific Layer does not modify operational or execution objects.
- Scientific Layer does not produce orders.

**Required Before**

Criterion generation.

---

## Gate 08 — Criterion Generation

**Acceptance Criteria**

- Criterion references Knowledge.
- CriterionDelta references Criterion and Knowledge.
- Criterion is not reduced to capital performance alone.

**Required Before**

Resource Loop.

---

## Gate 09 — Resource Loop

**Acceptance Criteria**

- ResourceState references CriterionDelta.
- ResourceState is a strategic snapshot.
- ResourceState does not create Events or Decisions directly.

**Required Before**

External integration readiness review.

---

## Gate 10 — External Integration Readiness

**Acceptance Criteria**

- Internal simulation evidence exists.
- Ledger integrity evidence exists.
- Outcome traceability evidence exists.
- Scientific learning evidence exists or the absence is explicitly justified.
- Integration remains optional and subordinate to Execution Engine.

**Required Before**

Any broker, Paper, Shadow, or Live work.

---

# 8. Definition of Done

Every sprint must satisfy the universal Definition of Done before completion.

## Universal Definition of Done

- Architecture respected.
- Scope completed.
- Forbidden modules not modified.
- Canonical object ownership preserved.
- Traceability preserved.
- Tests defined for the sprint scope.
- Tests executed when implementation exists.
- Documentation updated when behavior or architecture-facing contracts change.
- Evidence collected and recorded.
- No circular dependencies introduced.
- No new technical debt introduced intentionally.
- No autonomy increased without architecture approval.
- No external integration introduced unless explicitly in scope.
- No canonical document changed during implementation without an architectural decision.

## Sprint Completion Rule

A sprint is not complete because files exist.

A sprint is complete when its defined capability or foundation exit criteria are satisfied.

For Sprint 15A, foundation existence and isolation are sufficient because it is explicitly foundation only.

For Sprint 15B onward, behavioral evidence is required.

---

# 9. Risk Management

## Risk 01 — Architecture drift

**Rank**

Critical.

**Description**

Implementation diverges from canonical documents.

**Mitigation**

Begin every sprint by reading applicable canonical documents and listing forbidden modules.

## Risk 02 — Feature-first development

**Rank**

Critical.

**Description**

Developers implement visible features before completing the capability foundation.

**Mitigation**

Use capability roadmap and evidence gates as release blockers.

## Risk 03 — Partial subsystem implementation

**Rank**

High.

**Description**

A subsystem is partially wired and becomes depended upon before it is complete.

**Mitigation**

Do not allow downstream capabilities until exit criteria are satisfied.

## Risk 04 — Execution and Scientific coupling

**Rank**

High.

**Description**

Execution Engine begins creating Knowledge or Scientific Layer begins influencing execution.

**Mitigation**

Enforce object ownership rules and downstream-only learning.

## Risk 05 — Ledger mutation

**Rank**

High.

**Description**

Execution history is edited instead of appended.

**Mitigation**

Make append-only ledger integrity an evidence gate.

## Risk 06 — Premature broker integration

**Rank**

High.

**Description**

External integration begins before internal execution is stable.

**Mitigation**

Forbid broker work until External Integration Readiness Review.

## Risk 07 — Hidden autonomy increase

**Rank**

Critical.

**Description**

Automation expands without explicit approval.

**Mitigation**

Keep Approval mandatory and require architecture decision for autonomy changes.

## Risk 08 — Overcomplexity

**Rank**

Medium.

**Description**

The system becomes too complex for one-person maintainability.

**Mitigation**

Prefer small vertical slices, explicit ownership, and minimal coupling.

## Risk 09 — Traceability gaps

**Rank**

High.

**Description**

Identifiers are lost across object boundaries.

**Mitigation**

Make identifier propagation mandatory in tests and evidence gates.

## Risk 10 — Canonical naming drift

**Rank**

Medium.

**Description**

New synonyms or duplicate concepts appear.

**Mitigation**

Use OBJECT_MODEL_V1 naming rules and reject duplicate object names.

---

# 10. Architectural Constraints

The following are explicitly forbidden:

- Feature-first development.
- Partial subsystem implementation without an exit gate.
- Circular dependencies.
- Skipping evidence gates.
- Introducing autonomy before validation.
- Changing canonical documents during implementation without an architectural decision.
- Implementing broker integration during Sprint 15.
- Implementing TradingView integration during Sprint 15.
- Allowing Integration Layer to own execution.
- Allowing Execution Engine to modify Decisions.
- Allowing Execution Engine to modify ApprovedDecisions.
- Allowing Execution Engine to modify ExecutionSignals.
- Allowing Scientific Layer to produce orders.
- Allowing Council to modify Execution objects.
- Allowing Score Engine to produce Execution objects.
- Allowing ResourceState to create Events or Decisions directly.
- Treating tests as optional.
- Treating documentation as optional when contracts change.

---

# 11. Future Expansion

Future capabilities are introduced only through explicit architecture review.

## 11.1 New capability introduction

A new capability must define:

- objective;
- business value;
- architectural value;
- dependencies;
- allowed modules;
- forbidden modules;
- evidence produced;
- definition of done;
- risk profile;
- rollback or containment plan.

## 11.2 Future broker integrations

Broker integrations fit only after internal execution is stable.

They are optional infrastructure extensions.

They connect through Integration Layer.

They do not replace Execution Engine.

They do not own portfolio, orders, positions, ledger, metrics, ExecutionSignal, or ExecutionResult.

They must preserve broker agnosticism.

They must not change Decision or ApprovedDecision.

## 11.3 Paper and Shadow modes

Paper and Shadow modes require evidence from internal simulation first.

They require explicit architecture approval.

They must not increase autonomy.

They must preserve the same traceability and ledger standards as SIMULATION.

## 11.4 Live Trading

LIVE mode is not authorized.

Live Trading becomes possible only after sufficient evidence has been collected across:

- execution correctness;
- ledger integrity;
- portfolio consistency;
- outcome traceability;
- scientific ingestion;
- criterion generation;
- risk controls;
- autonomy governance;
- long-duration operational reliability.

Even then, LIVE requires a separate canonical architectural decision.

---

# 12. Final Roadmap

The complete recommended roadmap is:

## Priority 0 — Preserve canonical architecture

Maintain Architecture V2, Pipeline V2, Integration Architecture V1.1, Object Model V1, and Implementation Strategy V1 as the governing specifications.

## Priority 1 — Complete Sprint 15A

Build the Execution Engine foundation only.

No behavior.

No broker.

No Scientific Layer changes.

## Priority 2 — Complete Sprint 15B

Implement minimal simulated flow:

ApprovedDecision → ExecutionSignal → ExecutionRequest → ExecutionResult

## Priority 3 — Complete Sprint 15C

Add internal orders and append-only ledger integrity.

## Priority 4 — Complete Sprint 15D

Add virtual positions and portfolio snapshots.

## Priority 5 — Complete Sprint 15E

Validate internal end-to-end Execution Engine simulation.

## Priority 6 — Outcome Handoff

Connect ExecutionResult to Outcome Collector.

## Priority 7 — Scientific Ingestion

Allow Outcome to produce Evidence and Knowledge downstream.

## Priority 8 — Criterion Generation

Generate Criterion and CriterionDelta from Knowledge.

## Priority 9 — Resource Loop

Represent ResourceState from CriterionDelta.

## Priority 10 — External Integration Readiness Review

Review whether external integration should be designed.

No implementation unless approved.

## Priority 11 — Optional Paper or Shadow Mode

Only after readiness approval.

No live capital.

No autonomy expansion.

## Priority 12 — Live Trading Readiness Review

Only after extensive evidence.

LIVE remains prohibited unless a future canonical decision authorizes it.

---

# 13. Strategy Validation Checklist

This implementation strategy is valid only if:

- it does not redefine Sprint 15A;
- it moves first demonstrable execution flow to Sprint 15B;
- it preserves ExecutionSignal as canonical;
- it preserves Execution Engine ownership of internal execution;
- it keeps Integration Layer optional and future;
- it forbids broker integration during Sprint 15;
- it requires evidence gates before expansion;
- it preserves one-person maintainability;
- it prioritizes Criterion over execution volume;
- it introduces no implementation details.

This document performs no implementation.

It defines planning and execution order only.
