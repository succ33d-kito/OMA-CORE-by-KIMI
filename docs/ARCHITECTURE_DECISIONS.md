# Architecture Decisions — O.M.A.-C.O.R.E.

**Status:** Canonical Architecture Decision Registry

**Version:** 1.0

**Governance Scope:** Append-only architecture decision records

---

# 1. Purpose

This document is the canonical Architecture Decision Record registry for O.M.A.-C.O.R.E.

It exists to preserve architectural decisions chronologically, prevent history rewriting, and make future implementation decisions auditable.

Architecture Decisions are not implementation plans. They record binding architectural choices and the evidence or context that justified them.

---

# 2. Governance Rules

- Architecture Decisions are append-only.
- Decision IDs are chronological and never reused.
- Accepted decisions are immutable.
- Historical entries are never rewritten.
- Corrections are introduced through later Architecture Decisions.
- Lower-level sprint work may not redefine an accepted Architecture Decision.
- If a future implementation conflicts with an accepted decision, implementation must stop and escalate.

---

# 3. Decision Status Values

Allowed statuses:

- `ACCEPTED`
- `SUPERSEDED`
- `DEPRECATED`
- `PROPOSED`
- `REJECTED`

A `SUPERSEDED` or `DEPRECATED` status must reference the later decision that changed its authority.

---

# 4. Architecture Decision Template

Every future entry must contain exactly these fields:

- Decision ID
- Title
- Status
- Date
- Context
- Decision
- Alternatives Considered
- Consequences
- Evidence
- Affected Documents
- Affected Modules
- Future Impact

---

# 5. Decision Registry

---

## AD-001 — Execution Engine owns execution

**Decision ID:** AD-001

**Title:** Execution Engine owns execution

**Status:** ACCEPTED

**Date:** June 2026

### Context

`INTEGRATION_ARCHITECTURE_V1.md` originally treated external integration and TradingView Paper Trading as the primary execution path.

A later architectural conflict was detected when Sprint 15A shifted toward an internal Execution Engine with simulation as the default execution mode.

O.M.A.-C.O.R.E. required a clear owner for execution flow, portfolio, positions, orders, execution ledger, and execution metrics.

### Decision

Execution Engine is the canonical execution subsystem.

It owns:

- execution flow;
- virtual portfolio;
- virtual positions;
- virtual orders;
- execution ledger;
- execution metrics.

Integration Layer no longer owns execution. Integration Layer is optional future infrastructure for external broker connectivity.

### Alternatives Considered

1. Keep Integration Layer as execution owner.
2. Keep TradingView Paper Trading as the primary execution target.
3. Split execution ownership between Integration Layer and Execution Engine.
4. Make Execution Engine the single execution owner.

### Consequences

- Execution ownership is explicit.
- Integration becomes optional and future-facing.
- Sprint 15 can proceed without broker connectivity.
- Simulation becomes the primary default mode.
- Future brokers cannot bypass Execution Engine.

### Evidence

- `docs/INTEGRATION_ARCHITECTURE_V1.1.md`
- `docs/OBJECT_MODEL_V1.md`
- `docs/IMPLEMENTATION_STRATEGY_V1.md`
- `docs/SPRINT15A_ENGINEERING_REVIEW.md`

### Affected Documents

- `docs/INTEGRATION_ARCHITECTURE_V1.1.md`
- `docs/OBJECT_MODEL_V1.md`
- `docs/IMPLEMENTATION_STRATEGY_V1.md`

### Affected Modules

- `core/execution_engine/`

### Future Impact

All execution-related future work must occur through Execution Engine unless a later accepted Architecture Decision supersedes this rule.

---

## AD-002 — ExecutionSignal remains canonical

**Decision ID:** AD-002

**Title:** ExecutionSignal remains canonical

**Status:** ACCEPTED

**Date:** June 2026

### Context

A conflict appeared between Pipeline V2, which defined `ExecutionSignal` as the canonical pipeline object, and later internal Execution Engine planning, which introduced `ExecutionRequest`.

The ambiguity was whether `ExecutionRequest` replaced `ExecutionSignal` or existed inside the Execution Engine.

### Decision

`ExecutionSignal` remains the canonical Pipeline object.

It represents the approved intention to execute a decision.

It is produced by the Approval Layer and consumed by the Execution Engine.

Inside Execution Engine, `ExecutionSignal` may be transformed into Engine-owned internal objects:

ExecutionSignal → ExecutionRequest → ExecutionOrder → ExecutionPosition → ExecutionLedgerRecord → ExecutionResult

`ExecutionRequest` does not replace `ExecutionSignal`.

### Alternatives Considered

1. Replace `ExecutionSignal` with `ExecutionRequest`.
2. Treat `ExecutionRequest` as an alias for `ExecutionSignal`.
3. Keep `ExecutionSignal` canonical and define `ExecutionRequest` as internal Engine-owned structure.

### Consequences

- Pipeline V2 remains unchanged.
- Integration Architecture V1.1 remains unchanged.
- Execution Engine internals stay isolated.
- Internal Engine objects must not leak into upstream Pipeline ownership.

### Evidence

- `docs/PIPELINE_V2.md`
- `docs/OBJECT_MODEL_V1.md`
- `docs/IMPLEMENTATION_STRATEGY_V1.md`

### Affected Documents

- `docs/PIPELINE_V2.md`
- `docs/OBJECT_MODEL_V1.md`
- `docs/IMPLEMENTATION_STRATEGY_V1.md`

### Affected Modules

- `core/execution_engine/schemas/`

### Future Impact

Sprint 15B must validate the boundary:

ApprovedDecision → ExecutionSignal → ExecutionRequest → ExecutionResult

without replacing or mutating `ExecutionSignal`.

---

## AD-003 — Scientific Layer never produces orders

**Decision ID:** AD-003

**Title:** Scientific Layer never produces orders

**Status:** ACCEPTED

**Date:** June 2026

### Context

O.M.A.-C.O.R.E. separates operational flow from scientific learning flow.

The Scientific Layer learns from Outcomes but must never drive execution directly.

This boundary protects traceability, prevents hidden autonomy, and preserves the authority of Approval Layer and Execution Engine.

### Decision

Scientific Layer consumes Outcomes and produces Evidence, Knowledge, Criterion, or related scientific artifacts according to the canonical pipeline.

Scientific Layer never produces:

- orders;
- ExecutionSignals;
- ExecutionRequests;
- broker instructions;
- position changes;
- approval decisions.

### Alternatives Considered

1. Allow Scientific Layer to produce execution recommendations.
2. Allow Scientific Layer to modify future execution signals directly.
3. Restrict Scientific Layer to downstream learning only.

### Consequences

- Learning remains downstream.
- Execution remains controlled by Approval Layer and Execution Engine.
- Scientific discoveries must influence future decisions only through approved architecture paths.
- Autonomy cannot increase through scientific shortcuts.

### Evidence

- `docs/ENGINEERING_MANIFESTO.md`
- `docs/PIPELINE_V2.md`
- `docs/OBJECT_MODEL_V1.md`
- `docs/INTEGRATION_ARCHITECTURE_V1.1.md`

### Affected Documents

- `docs/PIPELINE_V2.md`
- `docs/OBJECT_MODEL_V1.md`
- `docs/INTEGRATION_ARCHITECTURE_V1.1.md`

### Affected Modules

- `core/scientific/`
- `core/execution_engine/`

### Future Impact

Future Scientific Layer work must prove that it does not mutate operational objects or emit execution instructions.

---

## AD-004 — Canonical ownership rule

**Decision ID:** AD-004

**Title:** Canonical ownership rule

**Status:** ACCEPTED

**Date:** June 2026

### Context

O.M.A.-C.O.R.E. requires traceable object ownership across a long-lived decision intelligence pipeline.

Multiple creators or multiple owners for the same object would make the system difficult to audit and maintain.

### Decision

Every canonical object has exactly one creator and exactly one owner.

Objects may have many consumers.

Consumption, audit access, or read-only reference access does not imply ownership.

Objects may never have multiple creators or multiple owners.

### Alternatives Considered

1. Permit shared ownership across related components.
2. Permit ownership transfer without explicit lifecycle rules.
3. Enforce exactly one creator and exactly one owner per object.

### Consequences

- Object authority is explicit.
- Pipeline boundaries are easier to verify.
- Future implementation can test ownership violations.
- Cross-layer mutation is forbidden unless a later architecture decision explicitly changes ownership.

### Evidence

- `docs/OBJECT_MODEL_V1.md`
- `docs/PIPELINE_V2.md`
- `docs/ENGINEERING_CONSTITUTION.md`

### Affected Documents

- `docs/OBJECT_MODEL_V1.md`
- `docs/PIPELINE_V2.md`
- `docs/ENGINEERING_CONSTITUTION.md`

### Affected Modules

All future modules that create or consume canonical objects.

### Future Impact

Every future sprint must report object ownership compliance in its engineering review.

---

## AD-005 — Execution Engine Foundation validated by Sprint 15A

**Decision ID:** AD-005

**Title:** Execution Engine Foundation validated by Sprint 15A

**Status:** ACCEPTED

**Date:** June 2026

### Context

Sprint 15A tested the hypothesis:

“The Execution Engine foundation can be implemented without violating the canonical architecture.”

Sprint 15A was foundation-only and explicitly excluded execution behavior.

### Decision

Sprint 15A is accepted as validating the Execution Engine foundation.

The Execution Engine foundation exists as an isolated subsystem and is ready for Sprint 15B, subject to continued compliance with canonical architecture and evidence gates.

### Alternatives Considered

1. Reject Sprint 15A and redesign the Execution Engine boundary.
2. Accept Sprint 15A only with conditions.
3. Accept Sprint 15A as ready for Sprint 15B.

### Consequences

- Sprint 15B may begin after governance review.
- Sprint 15B must validate minimal internal flow only.
- Sprint 15B must not add portfolio, positions, PnL, broker integration, or scientific ingestion.
- Execution Engine isolation remains mandatory.

### Evidence

- `docs/SPRINT15A_ENGINEERING_REVIEW.md`
- Targeted structural tests: 4 passed.
- Full regression suite: 869 passed, 3 warnings.
- No forbidden dependencies found.

### Affected Documents

- `docs/SPRINT15A_ENGINEERING_REVIEW.md`
- `docs/ENGINEERING_METRICS.md`
- `docs/IMPLEMENTATION_STRATEGY_V1.md`

### Affected Modules

- `core/execution_engine/`
- `tests/test_execution_engine_foundation.py`

### Future Impact

Sprint 15B should begin with the minimal flow:

ApprovedDecision → ExecutionSignal → ExecutionRequest → ExecutionResult

and must preserve all Sprint 15A isolation guarantees.

---

## AD-007 — Introduce Hypothesis as an Internal Scientific Object

**Decision ID:** AD-007

**Title:** Introduce Hypothesis as an Internal Scientific Object

**Status:** PROPOSED

**Date:** June 2026

### Context

The current canonical scientific handoff defined by Scientific Bridge Architecture V1 is:

Outcome → Scientific Bridge → Evidence → Scientific Layer → Knowledge → Criterion

During definition of the Scientific Bridge, the system clarified that Evidence and Knowledge represent different abstraction levels.

Evidence consists only of factual, traceable observations.

Knowledge represents validated conclusions produced downstream by the Scientific Layer.

This creates a possible architectural gap inside the Scientific Layer: an intermediate object may be useful to represent scientific assumptions before they become validated Knowledge.

This entry is recorded as `AD-007` because the proposal was submitted under that identifier. At the time of entry, no architectural authority is granted by the numbering itself; status remains `PROPOSED`.

### Decision

No architectural change is approved.

No implementation is authorized.

The proposal is to consider introducing an internal Scientific Layer object named `Hypothesis` during a future Scientific Layer implementation phase.

The proposed internal scientific flow would be:

Evidence → Hypothesis → Validation → Knowledge → Criterion

If accepted in the future, `Hypothesis` would be internal to the Scientific Layer only.

It would not become:

- a Pipeline object;
- an Execution Engine object;
- a Scientific Bridge object;
- an operational object;
- an object consumed by operational components.

Until this proposal is accepted by a later architecture decision, the canonical architecture remains unchanged.

### Alternatives Considered

1. Keep the current flow unchanged: Evidence → Scientific Layer → Knowledge → Criterion.
2. Introduce `Hypothesis` as a canonical Pipeline object.
3. Introduce `Hypothesis` as a Scientific Bridge object.
4. Introduce `Hypothesis` as an internal Scientific Layer object only.
5. Reject the intermediate object and require Knowledge generation directly from Evidence.

### Consequences

Because this decision is only `PROPOSED`, there are no immediate architecture, implementation, module, or pipeline consequences.

If accepted later, the proposal may:

- separate factual observations from scientific assumptions;
- improve explainability between Evidence and Knowledge;
- increase scientific traceability;
- reduce coupling between Evidence ingestion and Knowledge generation;
- require Scientific Layer validation rules;
- require additional governance around hypothesis lifecycle and immutability.

Risks if accepted prematurely:

- duplicate concepts already present in historical reasoning documentation;
- naming conflict with existing or prior `Hypothesis` schemas;
- accidental promotion of `Hypothesis` into a Pipeline object;
- leakage into operational decision or execution components;
- increased complexity before future sprint evidence justifies it.

### Evidence

- `docs/SCIENTIFIC_BRIDGE_ARCHITECTURE_V1.md`
- Architecture Decision Proposal submitted for `AD-007`
- Existing architectural distinction between Evidence and Knowledge

No implementation evidence exists yet.

Future sprint evidence is required before this proposal may be accepted or rejected.

### Affected Documents

Potential future affected documents if accepted:

- `docs/SCIENTIFIC_BRIDGE_ARCHITECTURE_V1.md`
- `docs/PIPELINE_V2.md`
- `docs/OBJECT_MODEL_V1.md`
- `docs/IMPLEMENTATION_STRATEGY_V1.md`
- future Scientific Layer architecture documents

This proposed entry does not modify those documents.

### Affected Modules

None at proposal time.

Potential future affected modules if accepted:

- `core/scientific/`
- scientific tests associated with future Scientific Layer implementation

No operational modules may consume `Hypothesis` under this proposal.

### Future Impact

This proposal must be reviewed during the Scientific Layer implementation phase.

Only evidence gathered during future sprints may justify accepting or rejecting it.

Until then:

- no architectural changes are approved;
- no implementation is authorized;
- `Hypothesis` does not become a Pipeline object;
- `Hypothesis` does not belong to the Scientific Bridge;
- `Hypothesis` does not belong to Execution Engine;
- operational components must not consume `Hypothesis`.

---

## AD-008 — Recognition of the Outcome Domain

**Decision ID:** AD-008

**Title:** Recognition of the Outcome Domain

**Status:** ACCEPTED

**Date:** June 2026

### Context

Sprint 15E implementation was correctly stopped when an architectural ambiguity was detected.

The ambiguity concerned whether Outcome was owned by the Execution Engine, owned by the Scientific Layer, or owned by the already documented Outcome Collector.

The canonical documents already stated:

- `PIPELINE_V2.md` defines `ExecutionResult → Outcome → Scientific Learning`.
- `OBJECT_MODEL_V1.md` defines Outcome creator and owner as Outcome Collector.
- `SCIENTIFIC_BRIDGE_ARCHITECTURE_V1.md` defines `Outcome → Scientific Bridge → Evidence` and states that Outcome Collector owns Outcome creation.

The contradiction was not caused by wrong canonical architecture.

It was caused by an implicit domain boundary that had not yet been named explicitly.

### Decision

O.M.A.-C.O.R.E. recognizes the Outcome Domain as an independent architectural domain between Operational Domain and Scientific Domain.

The canonical domain sequence is:

```text
Operational Domain
↓
Outcome Domain
↓
Scientific Domain
```

Outcome Domain owns the responsibility for:

- Outcome creation;
- Outcome validation;
- Outcome completeness;
- Outcome publication;
- Outcome ownership;
- Outcome lifecycle.

Within Outcome Domain, Outcome Collector remains the canonical creator and owner of Outcome.

This decision explicitly states:

- no ownership changes;
- no pipeline changes;
- no object model changes;
- no execution changes;
- no scientific changes;
- no implementation authorization.

The decision only formalizes an already existing architectural separation.

### Alternatives Considered

1. Make Outcome an Execution Engine-owned capability.
2. Make Outcome a Scientific Layer-owned capability.
3. Modify Pipeline V2 to add a new object or new layer.
4. Modify Object Model V1 to change Outcome ownership.
5. Recognize an explicit Outcome Domain while preserving existing Pipeline V2, Object Model V1, and Scientific Bridge Architecture V1.

Alternative 5 is accepted.

### Consequences

- Outcome ownership is no longer ambiguous.
- Execution Engine remains inside Operational Domain and ends its Outcome-facing responsibility at ExecutionResult.
- Outcome Collector owns Outcome inside the Outcome Domain.
- Scientific Bridge consumes Outcome read-only and creates Evidence.
- Scientific Layer owns Knowledge and downstream scientific reasoning.
- Future Outcome implementation must target Outcome Domain / Outcome Collector, not Execution Engine.
- ExecutionState or ExecutionLedger may be referenced only as read-only audit references if a future implementation requires them; they are not canonical Outcome inputs and not ownership dependencies.

### Evidence

- `docs/PIPELINE_V2.md`
- `docs/OBJECT_MODEL_V1.md`
- `docs/SCIENTIFIC_BRIDGE_ARCHITECTURE_V1.md`
- `docs/IMPLEMENTATION_STRATEGY_V1.md`
- Sprint 15E pre-implementation escalation that stopped implementation due to Outcome ownership and input-flow ambiguity.
- `docs/OUTCOME_ARCHITECTURE_V1.md`

### Affected Documents

- `docs/OUTCOME_ARCHITECTURE_V1.md`
- `docs/ARCHITECTURE_DECISIONS.md`

No modification is made to:

- `docs/PIPELINE_V2.md`
- `docs/OBJECT_MODEL_V1.md`
- `docs/SCIENTIFIC_BRIDGE_ARCHITECTURE_V1.md`
- `docs/IMPLEMENTATION_STRATEGY_V1.md`

### Affected Modules

None.

No implementation is authorized.

No Python package, schema, API, test, or code module is created by this decision.

### Future Impact

Future Outcome work must be scoped as Outcome Domain work.

The canonical implementation direction for future work is:

```text
ExecutionResult
↓
Outcome Collector
↓
Outcome
↓
Scientific Bridge
↓
Evidence
↓
Scientific Layer
↓
Knowledge
↓
Criterion
```

Future missions must not describe Outcome as Execution Engine-owned or Scientific Layer-owned unless a later accepted Architecture Decision explicitly supersedes AD-008.

Future Outcome implementation remains blocked from:

- Scientific Bridge implementation;
- Evidence generation;
- Knowledge generation;
- Criterion generation;
- broker integrations;
- Paper Trading;
- Shadow Mode;
- Live Trading;
- Pipeline redesign;
- Object Model redesign.
