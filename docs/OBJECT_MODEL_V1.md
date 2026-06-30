# OBJECT_MODEL_V1 — O.M.A.-C.O.R.E.

**Project:** O.M.A.-C.O.R.E.

**Version:** 1.0

**Status:** CANONICAL SPECIFICATION

**Date:** June 2026

**Scope:** Architecture only

---

# 1. Purpose

OBJECT_MODEL_V1 freezes the canonical object language of O.M.A.-C.O.R.E.

Architecture depends on canonical objects because every layer of the system communicates through named, owned, traceable objects. Without a frozen object model, the same concept can be implemented under multiple names, multiple components can claim authority over the same data, and the pipeline can lose traceability.

This document defines:

- the canonical domain objects of the system;
- the internal Execution Engine objects introduced by Integration Architecture V1.1;
- the creator, owner, consumers, lifecycle, persistence, and immutability contract of each object;
- the naming rules future implementations must follow.

This document is aligned with `ARCHITECTURE_V2.md`, `PIPELINE_V2.md`, and `INTEGRATION_ARCHITECTURE_V1.1.md`.

Relationship with Pipeline V2:

- Pipeline V2 defines the canonical pipeline object flow.
- OBJECT_MODEL_V1 defines the complete object contract for those objects and the Engine-owned internal objects required by the Execution Engine.
- ExecutionSignal remains the canonical Pipeline object.
- ExecutionRequest does not replace ExecutionSignal.
- ExecutionRequest, ExecutionOrder, ExecutionPosition, ExecutionPortfolio, and ExecutionLedgerRecord are internal Engine objects.
- ExecutionResult exits the Execution Engine and returns to the canonical Pipeline.

The resolved execution distinction is:

ExecutionSignal

↓

ExecutionRequest

↓

ExecutionOrder

↓

ExecutionPosition

↓

ExecutionLedgerRecord

↓

ExecutionResult

ExecutionSignal and ExecutionResult are canonical pipeline boundary objects.

ExecutionRequest, ExecutionOrder, ExecutionPosition, ExecutionPortfolio, and ExecutionLedgerRecord are internal Execution Engine objects.

---

# 2. Canonical Ownership Rule

Every object must have exactly one creator and exactly one owner.

Objects may have one or more consumers.

Objects may never have multiple creators.

Objects may never have multiple owners.

Ownership means architectural authority over the object's lifecycle, mutation rules, persistence policy, and state transitions.

Consumption does not imply ownership.

Audit access does not imply ownership.

Read-only reference access does not imply ownership.

## 2.1 Ownership Table

| Object | Category | Creator | Owner | Consumers | Persistence | Lifecycle |
|---|---|---|---|---|---|---|
| Reality | Canonical Domain Object | External world | External world | Collectors | Transient from system perspective | Exists → Observed |
| Event | Canonical Domain Object | Collectors | Observation Layer | Opportunity Engine | Operational DB or event archive | Created → Published → Consumed → Archived |
| OpportunityCandidate | Canonical Domain Object | Opportunity Engine | Opportunity Engine | Score Engine | Operational DB | Created → Published → Evaluated or Discarded |
| EvaluatedOpportunity | Canonical Domain Object | Score Engine | Score Engine | Council | Operational DB | Created → Published → Deliberated or Rejected |
| Decision | Canonical Domain Object | Council | Council | Approval Layer | Operational DB | Created → Published → Submitted for Approval → Archived |
| ApprovedDecision | Canonical Domain Object | Approval Layer | Approval Layer | Execution Engine | Operational DB or approval store | Approval Pending → Approved or Rejected or Manual Review |
| ExecutionSignal | Canonical Domain Object | Approval Layer | Approval Layer | Execution Engine | Execution Storage and audit archive | Created → Validated → Dispatched or Rejected |
| ExecutionRequest | Internal Engine Object | Execution Engine | Execution Engine | Orders domain | Execution Storage | Created → Accepted or Rejected → Archived |
| ExecutionOrder | Internal Engine Object | Execution Engine | Execution Engine | Positions domain, Ledger domain, Metrics domain | Execution Storage | NEW → PENDING → FILLED or PARTIAL or CANCELLED or REJECTED or EXPIRED |
| ExecutionPosition | Internal Engine Object | Execution Engine | Execution Engine | Portfolio domain, Ledger domain, Metrics domain | Execution Storage | OPEN → CLOSING → CLOSED |
| ExecutionPortfolio | Internal Engine Object | Execution Engine | Execution Engine | Engine, Metrics domain, Reports | Execution Storage and archive snapshots | Created → Active → Snapshot → Archived |
| ExecutionLedgerRecord | Internal Engine Object | Execution Engine | Execution Engine | Outcome Collector, Metrics domain, Reports, Audit | Execution Storage append-only archive | Created → Appended → Archived |
| ExecutionResult | Canonical Pipeline Boundary Object | Execution Engine | Execution Engine | Outcome Collector | Execution Storage and Operational DB handoff | Created → Published → Consumed → Archived |
| Outcome | Canonical Domain Object | Outcome Collector | Outcome Collector | Scientific Layer | Operational DB handoff and Scientific DB reference | Created → Published → Compared → Archived |
| Evidence | Canonical Scientific Object | Scientific Layer | Scientific Layer | Scientific Learning, Knowledge extraction | Scientific DB | Proposed → Active → Superseded or Archived |
| Knowledge | Canonical Scientific Object | Scientific Layer | Scientific Layer | Criterion Engine | Scientific DB | Proposed → Under Review → Validated or Contradicted or Rejected → Applied or Archived |
| Criterion | Canonical Strategic Object | Criterion Engine | Criterion Engine | Resource Loop and future decision context | Scientific DB or Criterion archive | Created → Measured → Applied → Superseded |
| CriterionDelta | Canonical Strategic Object | Criterion Engine | Criterion Engine | Resource Loop and future decision context | Scientific DB or Criterion archive | Created → Measured → Accepted or Rejected → Applied or Archived |
| ResourceState | Canonical Strategic Object | Resource Loop | Resource Loop | Future strategic context | Archive | Created → Reviewed → Used as Context → Superseded |

---

# 3. Canonical Objects

OBJECT_MODEL_V1 defines two object categories.

## 3.1 Canonical Domain Objects

Canonical Domain Objects are part of the system-wide architecture and may cross component boundaries.

They are:

- Reality
- Event
- OpportunityCandidate
- EvaluatedOpportunity
- Decision
- ApprovedDecision
- ExecutionSignal
- ExecutionResult
- Outcome
- Evidence
- Knowledge
- Criterion
- CriterionDelta
- ResourceState

## 3.2 Internal Engine Objects

Internal Engine Objects belong exclusively to the Execution Engine.

They support the internal transformation from ExecutionSignal to ExecutionResult.

They are not Pipeline objects.

They must not be consumed directly by Council, Score Engine, Collectors, Scientific Layer as control input, or brokers.

They are:

- ExecutionRequest
- ExecutionOrder
- ExecutionPosition
- ExecutionPortfolio
- ExecutionLedgerRecord

---

# 4. Object Specification

Every object follows the same architecture template.

---

## 4.1 Reality

### Purpose

Represent external world conditions before system observation.

### Description

Reality is the external environment: markets, news, macro data, geopolitical events, volatility, liquidity, sentiment, and other observable conditions.

### Producer

External world.

### Owner

External world.

### Consumers

Collectors.

### Inputs

None.

### Outputs

Observable conditions that may become Events.

### Relationships

Reality is the parent source of Events.

### Parent Objects

None.

### Child Objects

Event.

### Lifecycle

Exists → Observed.

### State Machine

No internal state machine. Reality is outside system control.

### Persistence

Transient from system perspective. The system persists Events, not Reality itself.

### Traceability

reality_id may be assigned when a collection cycle or external condition cluster needs explicit traceability.

### Validation Rules

Reality is not validated directly. Observations are validated by Collectors.

### Required Fields

None at system level.

### Optional Fields

reality_id, source_context, observed_time_window.

### Immutable Fields

All captured references to Reality are immutable once included in an Event.

### Forbidden Modifications

The system must not rewrite Reality.

### Versioning Strategy

Reality is not versioned directly. Captured observations are versioned through Event records.

### Architectural Notes

Reality does not decide, score, approve, execute, or learn.

---

## 4.2 Event

### Purpose

Represent that something observable happened.

### Description

Event is the first canonical system-owned representation of Reality.

### Producer

Collectors.

### Owner

Observation Layer.

### Consumers

Opportunity Engine.

### Inputs

Reality observations.

### Outputs

Event.

### Relationships

Event is derived from Reality and is the parent of OpportunityCandidate.

### Parent Objects

Reality.

### Child Objects

OpportunityCandidate.

### Lifecycle

Created → Published → Consumed → Archived.

### State Machine

CREATED → PUBLISHED → CONSUMED → ARCHIVED.

### Persistence

Operational DB or event archive.

### Traceability

event_id is mandatory. reality_id is optional when available.

### Validation Rules

Must preserve source, timestamp, observed subject, event type, and data quality context.

### Required Fields

event_id, source, timestamp, event_type, title or description, data_quality_context.

### Optional Fields

reality_id, assets, urgency, confidence, sentiment, source_url, raw_reference.

### Immutable Fields

event_id, source, timestamp, event_type, original observed content.

### Forbidden Modifications

Events may not be rewritten to fit later decisions or outcomes.

### Versioning Strategy

Corrections require a new Event or an audit annotation, not mutation of the original Event.

### Architectural Notes

Event never bypasses OpportunityCandidate and may never directly create execution.

---

## 4.3 OpportunityCandidate

### Purpose

Represent a possible opportunity interpreted from an Event before evaluation.

### Description

OpportunityCandidate captures what an Event might mean without claiming final score, approval, or execution readiness.

### Producer

Opportunity Engine.

### Owner

Opportunity Engine.

### Consumers

Score Engine.

### Inputs

Event.

### Outputs

OpportunityCandidate.

### Relationships

Child of Event. Parent of EvaluatedOpportunity.

### Parent Objects

Event.

### Child Objects

EvaluatedOpportunity.

### Lifecycle

Created → Published → Evaluated or Discarded or Expired.

### State Machine

CANDIDATE_CREATED → CANDIDATE_PUBLISHED → EVALUATION_PENDING → EVALUATED.

Alternative terminal states: DISCARDED, EXPIRED.

### Persistence

Operational DB.

### Traceability

opportunity_id and event_id are mandatory.

### Validation Rules

Must reference exactly one originating Event.

### Required Fields

opportunity_id, event_id, candidate_thesis, asset_context, created_at.

### Optional Fields

candidate_direction, confidence_hint, time_horizon, uncertainty_notes.

### Immutable Fields

opportunity_id, event_id, candidate_thesis at publication.

### Forbidden Modifications

May not be changed after evaluation. Reinterpretation requires a new OpportunityCandidate.

### Versioning Strategy

New interpretation equals new candidate with lineage to the same event_id.

### Architectural Notes

OpportunityCandidate does not approve, score finally, or execute.

---

## 4.4 EvaluatedOpportunity

### Purpose

Represent an OpportunityCandidate after scoring and contextual evaluation.

### Description

EvaluatedOpportunity is the Score Engine's canonical output and the Council's input.

### Producer

Score Engine.

### Owner

Score Engine.

### Consumers

Council.

### Inputs

OpportunityCandidate.

### Outputs

EvaluatedOpportunity.

### Relationships

Child of OpportunityCandidate. Parent of Decision.

### Parent Objects

OpportunityCandidate.

### Child Objects

Decision.

### Lifecycle

Created → Published → Deliberated or Rejected or Archived.

### State Machine

EVALUATION_STARTED → EVALUATED → PUBLISHED → DELIBERATION_PENDING.

Alternative terminal states: REJECTED, ARCHIVED.

### Persistence

Operational DB.

### Traceability

evaluation_id, opportunity_id, and event_id are mandatory.

### Validation Rules

Must be produced from exactly one OpportunityCandidate.

### Required Fields

evaluation_id, opportunity_id, event_id, score, conviction, evaluation_rationale, created_at.

### Optional Fields

risk_context, data_quality_context, scientific_quality_context, calibration_context.

### Immutable Fields

evaluation_id, opportunity_id, score, conviction, evaluation_rationale at publication.

### Forbidden Modifications

Score Engine may not modify the candidate after publishing the evaluation. Council may not mutate evaluation fields.

### Versioning Strategy

Re-evaluation creates a new EvaluatedOpportunity with a new evaluation_id.

### Architectural Notes

EvaluatedOpportunity may never directly create execution.

---

## 4.5 Decision

### Purpose

Represent the Council's commitment or non-action recommendation based on an EvaluatedOpportunity.

### Description

Decision records deliberation output, including rationale, dissent, alternatives, and confidence.

### Producer

Council.

### Owner

Council.

### Consumers

Approval Layer.

### Inputs

EvaluatedOpportunity.

### Outputs

Decision.

### Relationships

Child of EvaluatedOpportunity. Parent of ApprovedDecision.

### Parent Objects

EvaluatedOpportunity.

### Child Objects

ApprovedDecision.

### Lifecycle

Created → Published → Submitted for Approval → Archived.

### State Machine

DECISION_CREATED → DECISION_PUBLISHED → APPROVAL_PENDING.

Alternative terminal state: EXPIRED.

### Persistence

Operational DB.

### Traceability

decision_id, evaluation_id, opportunity_id, and event_id are mandatory.

### Validation Rules

Must be derived from exactly one EvaluatedOpportunity.

### Required Fields

decision_id, evaluation_id, opportunity_id, event_id, decision_type, rationale, created_at.

### Optional Fields

alternatives, dissent, confidence, constraints, hypothesis_id when available.

### Immutable Fields

decision_id, decision_type, rationale, upstream identifiers.

### Forbidden Modifications

Approval Layer and Execution Engine may not change Decision content.

### Versioning Strategy

A changed decision requires a new decision_id.

### Architectural Notes

Decision is not permission to execute. Approval is mandatory.

---

## 4.6 ApprovedDecision

### Purpose

Represent Approval Layer authorization or non-authorization of a Decision.

### Description

ApprovedDecision captures the approval outcome and approval trace for a Decision.

### Producer

Approval Layer.

### Owner

Approval Layer.

### Consumers

Execution Engine.

### Inputs

Decision.

### Outputs

ApprovedDecision.

### Relationships

Child of Decision. Parent of ExecutionSignal.

### Parent Objects

Decision.

### Child Objects

ExecutionSignal.

### Lifecycle

Approval Pending → Approved or Rejected or Manual Review → Archived.

### State Machine

APPROVAL_PENDING → APPROVED.

Alternative states: REJECTED, MANUAL_REVIEW, EXPIRED.

### Persistence

Operational DB or approval store.

### Traceability

approval_id, decision_id, evaluation_id, opportunity_id, and event_id are mandatory.

### Validation Rules

Must reference exactly one Decision.

### Required Fields

approval_id, decision_id, approval_state, approval_rationale, approved_at or reviewed_at.

### Optional Fields

approver_id, rejection_reason, manual_review_reason, risk_checks, data_quality_checks, scientific_quality_checks.

### Immutable Fields

approval_id, decision_id, approval_state after publication, approval rationale.

### Forbidden Modifications

Execution Engine may not alter approval state. Scientific Layer may not approve decisions.

### Versioning Strategy

A changed approval requires a new approval record linked to the same decision_id.

### Architectural Notes

Only ApprovedDecision in APPROVED state may produce ExecutionSignal.

---

## 4.7 ExecutionSignal

### Purpose

Represent the approved intention to execute a Decision.

### Description

ExecutionSignal is the canonical Pipeline object between Approval Layer and Execution Engine. It is not replaced by ExecutionRequest.

### Producer

Approval Layer.

### Owner

Approval Layer.

### Consumers

Execution Engine.

### Inputs

ApprovedDecision.

### Outputs

ExecutionSignal.

### Relationships

Child of ApprovedDecision. Parent of ExecutionRequest inside Execution Engine.

### Parent Objects

ApprovedDecision.

### Child Objects

ExecutionRequest.

### Lifecycle

Created → Validated → Dispatched or Rejected → Archived.

### State Machine

CREATED → VALIDATED → APPROVED → DISPATCHED.

Alternative terminal states: REJECTED, FAILED, CANCELLED.

### Persistence

Execution Storage and audit archive.

### Traceability

execution_signal_id, approval_id, decision_id, opportunity_id, and event_id are mandatory.

### Validation Rules

Must originate from an ApprovedDecision in APPROVED state.

### Required Fields

execution_signal_id, approval_id, decision_id, intended_action, created_at.

### Optional Fields

symbol, quantity_intent, direction, constraints, hypothesis_id, execution_mode.

### Immutable Fields

execution_signal_id, approval_id, decision_id, intended_action, upstream identifiers.

### Forbidden Modifications

Execution Engine may not change the approved intention. It may only transform it into internal ExecutionRequest.

### Versioning Strategy

Any changed intent requires a new ExecutionSignal from Approval Layer.

### Architectural Notes

ExecutionSignal remains canonical in Pipeline V2 and Integration Architecture V1.1.

---

## 4.8 ExecutionRequest

### Purpose

Represent the Execution Engine's internal request derived from an ExecutionSignal.

### Description

ExecutionRequest is an internal Engine-owned implementation object. It does not replace ExecutionSignal and is not a Pipeline object.

### Producer

Execution Engine.

### Owner

Execution Engine.

### Consumers

Orders domain.

### Inputs

ExecutionSignal.

### Outputs

ExecutionRequest.

### Relationships

Child of ExecutionSignal. Parent of ExecutionOrder.

### Parent Objects

ExecutionSignal.

### Child Objects

ExecutionOrder.

### Lifecycle

Created → Accepted or Rejected → Archived.

### State Machine

REQUEST_CREATED → REQUEST_ACCEPTED.

Alternative terminal state: REQUEST_REJECTED.

### Persistence

Execution Storage.

### Traceability

execution_request_id and execution_signal_id are mandatory. All upstream identifiers must propagate.

### Validation Rules

Must reference exactly one ExecutionSignal.

### Required Fields

execution_request_id, execution_signal_id, requested_action, execution_mode, created_at.

### Optional Fields

request_notes, internal_constraints, simulation_context.

### Immutable Fields

execution_request_id, execution_signal_id, requested_action, execution_mode.

### Forbidden Modifications

May not modify ExecutionSignal or ApprovedDecision.

### Versioning Strategy

New internal translation requires a new ExecutionRequest.

### Architectural Notes

Internal Engine object only. Not consumed directly by Scientific Layer, Council, Score Engine, or Collectors.

---

## 4.9 ExecutionOrder

### Purpose

Represent an internal order object managed by the Execution Engine.

### Description

ExecutionOrder is the Engine's internal representation of an order lifecycle in SIMULATION or future modes.

### Producer

Execution Engine.

### Owner

Execution Engine.

### Consumers

Positions domain, Ledger domain, Metrics domain.

### Inputs

ExecutionRequest.

### Outputs

ExecutionOrder.

### Relationships

Child of ExecutionRequest. Parent of ExecutionPosition and ExecutionLedgerRecord.

### Parent Objects

ExecutionRequest.

### Child Objects

ExecutionPosition, ExecutionLedgerRecord.

### Lifecycle

NEW → PENDING → FILLED or PARTIAL or CANCELLED or REJECTED or EXPIRED → Archived.

### State Machine

NEW → PENDING → FILLED.

Alternative states: PARTIAL, CANCELLED, REJECTED, EXPIRED.

### Persistence

Execution Storage.

### Traceability

execution_order_id and execution_request_id are mandatory. execution_signal_id and upstream identifiers must propagate.

### Validation Rules

Must reference exactly one ExecutionRequest.

### Required Fields

execution_order_id, execution_request_id, order_state, created_at.

### Optional Fields

symbol, side, quantity, order_constraints, internal_notes.

### Immutable Fields

execution_order_id, execution_request_id, creation intent.

### Forbidden Modifications

Order history may not be rewritten. State changes must be captured by ledger records.

### Versioning Strategy

Corrections require a new ledger record or new order, not mutation of historical order facts.

### Architectural Notes

No matching, algorithmic execution, or broker connectivity is implied by this object.

---

## 4.10 ExecutionPosition

### Purpose

Represent an internal virtual position managed by the Execution Engine.

### Description

ExecutionPosition captures position lifecycle state inside the Execution Engine.

### Producer

Execution Engine.

### Owner

Execution Engine.

### Consumers

Portfolio domain, Ledger domain, Metrics domain.

### Inputs

ExecutionOrder.

### Outputs

ExecutionPosition.

### Relationships

Child of ExecutionOrder. Parent of ExecutionLedgerRecord and ExecutionResult.

### Parent Objects

ExecutionOrder.

### Child Objects

ExecutionLedgerRecord, ExecutionResult.

### Lifecycle

OPEN → CLOSING → CLOSED → Archived.

### State Machine

OPEN → CLOSING → CLOSED.

### Persistence

Execution Storage.

### Traceability

execution_position_id and execution_order_id are mandatory. Upstream identifiers must propagate.

### Validation Rules

Must originate from Engine-owned order state.

### Required Fields

execution_position_id, execution_order_id, position_state, opened_at.

### Optional Fields

closed_at, symbol, quantity, direction, internal_position_notes.

### Immutable Fields

execution_position_id, execution_order_id, opened_at, originating order reference.

### Forbidden Modifications

Position history may not be rewritten. Closing is a state transition, not deletion.

### Versioning Strategy

Corrections are represented through ledger records.

### Architectural Notes

No PnL calculation is required by the architecture at this stage.

---

## 4.11 ExecutionPortfolio

### Purpose

Represent the virtual portfolio state owned by the Execution Engine.

### Description

ExecutionPortfolio is the internal object representing cash, equity, buying power, realized pnl, unrealized pnl, and portfolio statistics architecture.

### Producer

Execution Engine.

### Owner

Execution Engine.

### Consumers

Engine, Metrics domain, Reports.

### Inputs

ExecutionPosition and ExecutionLedgerRecord references.

### Outputs

ExecutionPortfolio snapshot.

### Relationships

Related to ExecutionPosition and ExecutionLedgerRecord. Parent of portfolio reports and summaries.

### Parent Objects

ExecutionLedgerRecord as factual source of portfolio-changing events.

### Child Objects

ExecutionSummary, ExecutionReport where future architecture defines them.

### Lifecycle

Created → Active → Snapshot → Archived.

### State Machine

PORTFOLIO_CREATED → PORTFOLIO_ACTIVE → SNAPSHOT_CREATED → SNAPSHOT_ARCHIVED.

### Persistence

Execution Storage and archive snapshots.

### Traceability

Portfolio snapshots must reference the ledger range or ledger record identifiers from which they were derived.

### Validation Rules

Portfolio state must not exist without ledger traceability.

### Required Fields

portfolio_id, snapshot_time, execution_mode, ledger_reference.

### Optional Fields

virtual_cash, virtual_equity, buying_power, realized_pnl, unrealized_pnl, statistics_reference.

### Immutable Fields

portfolio_id, snapshot_time, ledger_reference.

### Forbidden Modifications

Historical snapshots may not be overwritten.

### Versioning Strategy

New snapshot creates a new portfolio state version.

### Architectural Notes

ExecutionPortfolio is internal to Execution Engine and must not be used by Council as decision authority in Sprint 15A.

---

## 4.12 ExecutionLedgerRecord

### Purpose

Represent an immutable append-only execution history entry.

### Description

ExecutionLedgerRecord is the factual audit trail of Execution Engine operations.

### Producer

Execution Engine.

### Owner

Execution Engine.

### Consumers

Outcome Collector, Metrics domain, Reports, Audit.

### Inputs

ExecutionRequest, ExecutionOrder, ExecutionPosition, ExecutionPortfolio, or ExecutionResult events.

### Outputs

ExecutionLedgerRecord.

### Relationships

Child of Engine-owned execution events. Parent evidence source for ExecutionResult and audit reports.

### Parent Objects

ExecutionRequest, ExecutionOrder, ExecutionPosition, ExecutionPortfolio, ExecutionResult.

### Child Objects

ExecutionResult references and audit/report records.

### Lifecycle

Created → Appended → Archived.

### State Machine

LEDGER_RECORD_CREATED → LEDGER_RECORD_APPENDED → LEDGER_RECORD_ARCHIVED.

### Persistence

Execution Storage append-only archive.

### Traceability

execution_ledger_record_id is mandatory. Relevant upstream identifiers must propagate.

### Validation Rules

Must be append-only. Must reference the operation it records.

### Required Fields

execution_ledger_record_id, record_type, created_at, source_object_id, upstream_trace.

### Optional Fields

previous_record_id, correction_of_record_id, metadata, operator_context.

### Immutable Fields

All fields after append.

### Forbidden Modifications

No deletion. No mutation. No in-place correction.

### Versioning Strategy

Corrections are new ledger records referencing prior records.

### Architectural Notes

ExecutionLedgerRecord is the strongest immutability contract in the Execution Engine.

---

## 4.13 ExecutionResult

### Purpose

Represent the factual result produced by Execution Engine.

### Description

ExecutionResult is the canonical pipeline boundary object exiting Execution Engine and entering Outcome Collector.

### Producer

Execution Engine.

### Owner

Execution Engine.

### Consumers

Outcome Collector.

### Inputs

ExecutionLedgerRecord and final Engine execution state.

### Outputs

ExecutionResult.

### Relationships

Child of ExecutionSignal through internal Engine objects. Parent of Outcome.

### Parent Objects

ExecutionSignal, ExecutionRequest, ExecutionOrder, ExecutionPosition, ExecutionLedgerRecord.

### Child Objects

Outcome.

### Lifecycle

Created → Published → Consumed → Archived.

### State Machine

RESULT_CREATED → RESULT_PUBLISHED → RESULT_CONSUMED → RESULT_ARCHIVED.

Alternative state: RESULT_FAILED.

### Persistence

Execution Storage and Operational DB handoff.

### Traceability

execution_result_id, execution_signal_id, execution_request_id, execution_order_id where applicable, execution_position_id where applicable, and upstream identifiers are mandatory when applicable.

### Validation Rules

Must preserve full upstream lineage. Must not interpret scientific meaning.

### Required Fields

execution_result_id, execution_signal_id, result_state, created_at, ledger_reference.

### Optional Fields

execution_request_id, execution_order_id, execution_position_id, trade_id, error_classification, execution_mode.

### Immutable Fields

execution_result_id, execution_signal_id, result_state after publication, ledger_reference.

### Forbidden Modifications

Outcome Collector may not mutate ExecutionResult.

### Versioning Strategy

Corrections require a new ExecutionResult or ledger correction record, never mutation.

### Architectural Notes

ExecutionResult is the only Execution Engine output consumed by Outcome Collector.

---

## 4.14 Outcome

### Purpose

Represent the final factual result of an executed or attempted action.

### Description

Outcome is created downstream from ExecutionResult and becomes the input to Scientific Learning.

### Producer

Outcome Collector.

### Owner

Outcome Collector.

### Consumers

Scientific Layer.

### Inputs

ExecutionResult.

### Outputs

Outcome.

### Relationships

Child of ExecutionResult. Parent of Evidence and Knowledge derivation.

### Parent Objects

ExecutionResult.

### Child Objects

Evidence, Knowledge.

### Lifecycle

Created → Published → Compared → Archived.

### State Machine

OUTCOME_CREATED → OUTCOME_PUBLISHED → COMPARISON_PENDING → COMPARED → ARCHIVED.

Alternative state: INVALIDATED_BY_AUDIT.

### Persistence

Operational DB handoff and Scientific DB reference.

### Traceability

outcome_id and execution_result_id are mandatory. Upstream identifiers must propagate.

### Validation Rules

Must be factual and must not interpret whether a hypothesis was good.

### Required Fields

outcome_id, execution_result_id, created_at, result_facts.

### Optional Fields

entry_price, exit_price, duration, pnl, mae, mfe, slippage, fees, close_reason, hypothesis_id.

### Immutable Fields

outcome_id, execution_result_id, factual result fields after publication.

### Forbidden Modifications

Scientific Layer may not rewrite Outcome.

### Versioning Strategy

Audit invalidation marks status; correction creates new Outcome or audit record.

### Architectural Notes

Outcome bridges execution facts to scientific learning without itself creating Knowledge.

---

## 4.15 Evidence

### Purpose

Represent information relative to a hypothesis or outcome comparison.

### Description

Evidence supports, contradicts, or contextualizes hypotheses and learning.

### Producer

Scientific Layer.

### Owner

Scientific Layer.

### Consumers

Scientific Learning and Knowledge extraction.

### Inputs

Outcome, hypothesis context, external evidence sources when authorized.

### Outputs

Evidence.

### Relationships

May be child of Outcome or hypothesis context. Parent of Knowledge.

### Parent Objects

Outcome, hypothesis context when available.

### Child Objects

Knowledge.

### Lifecycle

Proposed → Active → Superseded or Archived.

### State Machine

EVIDENCE_PROPOSED → EVIDENCE_ACTIVE → EVIDENCE_ARCHIVED.

Alternative state: EVIDENCE_SUPERSEDED.

### Persistence

Scientific DB.

### Traceability

evidence_id is mandatory. outcome_id and hypothesis_id are mandatory when evidence is outcome-derived.

### Validation Rules

Must state source, direction, and relevance.

### Required Fields

evidence_id, evidence_source, evidence_direction, created_at.

### Optional Fields

outcome_id, hypothesis_id, weight, reliability, notes.

### Immutable Fields

evidence_id, evidence_source, original evidence content.

### Forbidden Modifications

Evidence may not rewrite Outcome or Decision.

### Versioning Strategy

Changed interpretation creates new Evidence or supersedes prior Evidence.

### Architectural Notes

Evidence belongs to Scientific Layer and never produces execution.

---

## 4.16 Knowledge

### Purpose

Represent scientific learning extracted from evidence and outcome comparison.

### Description

Knowledge is a generalizable lesson that may be validated, contradicted, rejected, applied, or archived.

### Producer

Scientific Layer.

### Owner

Scientific Layer.

### Consumers

Criterion Engine.

### Inputs

Outcome, Evidence, hypothesis comparison.

### Outputs

Knowledge.

### Relationships

Child of Evidence and Outcome comparison. Parent of Criterion and CriterionDelta.

### Parent Objects

Outcome, Evidence.

### Child Objects

Criterion, CriterionDelta.

### Lifecycle

Proposed → Under Review → Validated or Contradicted or Rejected → Applied or Archived.

### State Machine

PROPOSED → UNDER_REVIEW → VALIDATED → APPLIED.

Alternative states: CONTRADICTED, REJECTED, SUPERSEDED, ARCHIVED.

### Persistence

Scientific DB.

### Traceability

knowledge_id is mandatory. outcome_id and evidence_id are required when applicable.

### Validation Rules

Must preserve source outcome and evidence trace.

### Required Fields

knowledge_id, knowledge_statement, status, created_at.

### Optional Fields

outcome_id, evidence_id, hypothesis_id, confidence, applicability_scope.

### Immutable Fields

knowledge_id, original knowledge statement after publication.

### Forbidden Modifications

Knowledge may not modify historical Outcomes, Decisions, or Execution objects.

### Versioning Strategy

New learning supersedes previous Knowledge rather than mutating it.

### Architectural Notes

Knowledge never sends orders.

---

## 4.17 Criterion

### Purpose

Represent accumulated judgment derived from Knowledge.

### Description

Criterion is the system's accumulated ability to judge what matters.

### Producer

Criterion Engine.

### Owner

Criterion Engine.

### Consumers

Resource Loop and future decision context.

### Inputs

Knowledge.

### Outputs

Criterion.

### Relationships

Child of Knowledge. Parent of CriterionDelta and ResourceState.

### Parent Objects

Knowledge.

### Child Objects

CriterionDelta, ResourceState.

### Lifecycle

Created → Measured → Applied → Superseded.

### State Machine

CRITERION_CREATED → MEASURED → APPLIED → SUPERSEDED.

Alternative terminal state: ARCHIVED.

### Persistence

Scientific DB or Criterion archive.

### Traceability

criterion_id and knowledge_id are mandatory.

### Validation Rules

Must derive from Knowledge, not raw execution.

### Required Fields

criterion_id, knowledge_id, criterion_statement, created_at.

### Optional Fields

measurement_context, confidence, scope, trend_reference.

### Immutable Fields

criterion_id, knowledge_id, criterion statement after publication.

### Forbidden Modifications

Criterion may not rewrite Knowledge or Outcome.

### Versioning Strategy

Later Criterion supersedes prior Criterion.

### Architectural Notes

Criterion is not a single profit score and must not be reduced to capital performance alone.

---

## 4.18 CriterionDelta

### Purpose

Represent a discrete change in Criterion.

### Description

CriterionDelta records how validated learning changes the system's judgment over time.

### Producer

Criterion Engine.

### Owner

Criterion Engine.

### Consumers

Resource Loop and future decision context.

### Inputs

Criterion and Knowledge.

### Outputs

CriterionDelta.

### Relationships

Child of Criterion and Knowledge. Parent of ResourceState.

### Parent Objects

Criterion, Knowledge.

### Child Objects

ResourceState.

### Lifecycle

Created → Measured → Accepted or Rejected → Applied or Archived.

### State Machine

CRITERION_DELTA_CREATED → MEASURED → ACCEPTED → APPLIED_TO_CONTEXT.

Alternative states: REJECTED, SUPERSEDED, ARCHIVED.

### Persistence

Scientific DB or Criterion archive.

### Traceability

criterion_delta_id, criterion_id, and knowledge_id are mandatory.

### Validation Rules

Must identify the Knowledge that caused the delta.

### Required Fields

criterion_delta_id, criterion_id, knowledge_id, delta_statement, created_at.

### Optional Fields

delta_magnitude, confidence, scope, review_notes.

### Immutable Fields

criterion_delta_id, criterion_id, knowledge_id, delta_statement after publication.

### Forbidden Modifications

CriterionDelta may not modify Knowledge or historical ResourceState.

### Versioning Strategy

Corrections create new CriterionDelta or supersede prior delta.

### Architectural Notes

CriterionDelta is the bridge from learning to strategic resource context.

---

## 4.19 ResourceState

### Purpose

Represent the state of scarce resources influenced by Criterion and decisions.

### Description

ResourceState is a strategic snapshot of resources such as capital, time, attention, knowledge, relationships, mobility, health, and freedom of decision.

### Producer

Resource Loop.

### Owner

Resource Loop.

### Consumers

Future strategic context and future cycle planning.

### Inputs

CriterionDelta and Criterion.

### Outputs

ResourceState.

### Relationships

Child of CriterionDelta. Provides context for future cycles without mutating past objects.

### Parent Objects

CriterionDelta, Criterion.

### Child Objects

Future cycle context references.

### Lifecycle

Created → Reviewed → Used as Context → Superseded.

### State Machine

RESOURCE_STATE_CREATED → REVIEWED → USED_AS_CONTEXT → SUPERSEDED.

Alternative terminal state: ARCHIVED.

### Persistence

Archive.

### Traceability

resource_state_id and criterion_delta_id are mandatory when derived from a delta.

### Validation Rules

Must not optimize capital at the expense of other resources without explicit architectural review.

### Required Fields

resource_state_id, created_at, resource_snapshot, context_scope.

### Optional Fields

criterion_delta_id, criterion_id, capital_context, time_context, attention_context, health_context.

### Immutable Fields

resource_state_id, created_at, snapshot values after publication.

### Forbidden Modifications

Historical ResourceState may not be rewritten.

### Versioning Strategy

New state creates a new ResourceState snapshot.

### Architectural Notes

ResourceState closes the strategic loop but does not create Events or Decisions directly.

---

# 5. Object Relationships

Canonical relationship map:

Reality

↓

Event

↓

OpportunityCandidate

↓

EvaluatedOpportunity

↓

Decision

↓

ApprovedDecision

↓

ExecutionSignal

↓

ExecutionRequest

↓

ExecutionOrder

↓

ExecutionPosition

↓

ExecutionLedgerRecord

↓

ExecutionResult

↓

Outcome

↓

Evidence

↓

Knowledge

↓

Criterion

↓

CriterionDelta

↓

ResourceState

## Relationship Explanations

Reality produces observable conditions, not system decisions.

Event is the system-owned observation of Reality.

OpportunityCandidate is the interpreted possibility derived from Event.

EvaluatedOpportunity is the scored and contextualized candidate.

Decision is the Council's deliberation output based on EvaluatedOpportunity.

ApprovedDecision is the Approval Layer's authorization result for Decision.

ExecutionSignal is the canonical approved intention to execute.

ExecutionRequest is the Execution Engine's internal request derived from ExecutionSignal.

ExecutionOrder is the Engine's internal order representation derived from ExecutionRequest.

ExecutionPosition is the Engine's virtual position representation derived from ExecutionOrder.

ExecutionLedgerRecord is the append-only record of Engine operations.

ExecutionResult is the canonical Engine output produced from internal execution history.

Outcome is the factual result derived from ExecutionResult.

Evidence is scientific information associated with Outcome and hypothesis context.

Knowledge is learning extracted from Evidence and Outcome comparison.

Criterion is accumulated judgment derived from Knowledge.

CriterionDelta is a discrete change in Criterion.

ResourceState is the strategic resource snapshot influenced by CriterionDelta.

---

# 6. Object Ownership Matrix

| Object | Creator | Owner | Consumers | Persistent | Immutable | Lifecycle | Storage |
|---|---|---|---|---|---|---|---|
| Reality | External world | External world | Collectors | No | Yes from system perspective | Exists → Observed | Transient Memory |
| Event | Collectors | Observation Layer | Opportunity Engine | Yes | Yes after publication | Created → Published → Consumed → Archived | Operational DB / Archive |
| OpportunityCandidate | Opportunity Engine | Opportunity Engine | Score Engine | Yes | Yes after publication | Created → Published → Evaluated or Discarded | Operational DB |
| EvaluatedOpportunity | Score Engine | Score Engine | Council | Yes | Yes after publication | Created → Published → Deliberated or Rejected | Operational DB |
| Decision | Council | Council | Approval Layer | Yes | Yes after publication | Created → Published → Approval Pending | Operational DB |
| ApprovedDecision | Approval Layer | Approval Layer | Execution Engine | Yes | Yes after publication | Pending → Approved or Rejected or Manual Review | Operational DB / Approval Store |
| ExecutionSignal | Approval Layer | Approval Layer | Execution Engine | Yes | Yes after publication | Created → Validated → Dispatched or Rejected | Execution Storage / Archive |
| ExecutionRequest | Execution Engine | Execution Engine | Orders domain | Yes | Yes after publication | Created → Accepted or Rejected | Execution Storage |
| ExecutionOrder | Execution Engine | Execution Engine | Positions, Ledger, Metrics | Yes | History append-only | NEW → PENDING → terminal order state | Execution Storage |
| ExecutionPosition | Execution Engine | Execution Engine | Portfolio, Ledger, Metrics | Yes | History append-only | OPEN → CLOSING → CLOSED | Execution Storage |
| ExecutionPortfolio | Execution Engine | Execution Engine | Engine, Metrics, Reports | Yes | Snapshots immutable | Created → Active → Snapshot → Archived | Execution Storage / Archive |
| ExecutionLedgerRecord | Execution Engine | Execution Engine | Outcome Collector, Metrics, Reports, Audit | Yes | Fully immutable | Created → Appended → Archived | Execution Storage append-only |
| ExecutionResult | Execution Engine | Execution Engine | Outcome Collector | Yes | Yes after publication | Created → Published → Consumed → Archived | Execution Storage / Operational Handoff |
| Outcome | Outcome Collector | Outcome Collector | Scientific Layer | Yes | Yes after publication | Created → Published → Compared → Archived | Operational Handoff / Scientific DB reference |
| Evidence | Scientific Layer | Scientific Layer | Scientific Learning, Knowledge extraction | Yes | Yes after publication | Proposed → Active → Superseded or Archived | Scientific DB |
| Knowledge | Scientific Layer | Scientific Layer | Criterion Engine | Yes | Yes after publication | Proposed → Reviewed → Validated or Rejected → Applied | Scientific DB |
| Criterion | Criterion Engine | Criterion Engine | Resource Loop | Yes | Yes after publication | Created → Measured → Applied → Superseded | Scientific DB / Criterion Archive |
| CriterionDelta | Criterion Engine | Criterion Engine | Resource Loop | Yes | Yes after publication | Created → Measured → Accepted or Rejected → Applied | Scientific DB / Criterion Archive |
| ResourceState | Resource Loop | Resource Loop | Future strategic context | Yes | Yes after publication | Created → Reviewed → Used → Superseded | Archive |

---

# 7. Lifecycle Definitions

Every object must define Birth, Active, Archived, and Deleted policy.

## 7.1 Birth

Birth occurs when the creator publishes the object or records it as the canonical output of its layer.

An object is not architecturally born before its creator has assigned its identifier and ownership.

## 7.2 Active

Active means the object may be consumed by its defined downstream consumers.

Active does not mean mutable.

Most objects are immutable while active.

## 7.3 Archived

Archived means the object is retained for traceability, audit, and scientific review but is no longer part of active control flow.

Archival must preserve identifiers and relationships.

## 7.4 Deleted

Deletion is not allowed for canonical objects except where retention policy outside the architecture requires redaction for legal, privacy, or security reasons.

Even then, deletion must preserve an audit tombstone with identifier, deletion reason, timestamp, and authority.

ExecutionLedgerRecord may never be deleted under normal operation.

## 7.5 Retention Policy

Operational objects are retained for operational audit and traceability.

Execution objects are retained for execution audit and outcome reconstruction.

Scientific objects are retained for learning lineage.

Strategic objects are retained for Criterion and ResourceState evolution.

## 7.6 Archival Rules

Objects may be archived only after all required downstream consumption has occurred or after a terminal state is reached.

Archived objects remain queryable for audit.

## 7.7 Persistence Rules

Persistent objects must preserve their required identifiers and parent-child relationships.

Transient objects may only be used when they do not break traceability.

---

# 8. State Machines

This section defines architecture-only state machines.

## 8.1 Reality

No internal state machine.

## 8.2 Event

CREATED → PUBLISHED → CONSUMED → ARCHIVED.

## 8.3 OpportunityCandidate

CANDIDATE_CREATED → CANDIDATE_PUBLISHED → EVALUATION_PENDING → EVALUATED.

Terminal alternatives: DISCARDED, EXPIRED.

## 8.4 EvaluatedOpportunity

EVALUATION_STARTED → EVALUATED → PUBLISHED → DELIBERATION_PENDING.

Terminal alternatives: REJECTED, ARCHIVED.

## 8.5 Decision

DECISION_CREATED → DECISION_PUBLISHED → APPROVAL_PENDING.

Terminal alternative: EXPIRED.

## 8.6 ApprovedDecision

APPROVAL_PENDING → APPROVED.

Alternatives: REJECTED, MANUAL_REVIEW, EXPIRED.

## 8.7 ExecutionSignal

CREATED → VALIDATED → APPROVED → DISPATCHED.

Alternatives: FAILED, CANCELLED, REJECTED.

## 8.8 ExecutionRequest

REQUEST_CREATED → REQUEST_ACCEPTED.

Alternative: REQUEST_REJECTED.

## 8.9 ExecutionOrder

NEW → PENDING → FILLED.

Alternatives: PARTIAL, CANCELLED, REJECTED, EXPIRED.

## 8.10 ExecutionPosition

OPEN → CLOSING → CLOSED.

## 8.11 ExecutionPortfolio

PORTFOLIO_CREATED → PORTFOLIO_ACTIVE → SNAPSHOT_CREATED → SNAPSHOT_ARCHIVED.

## 8.12 ExecutionLedgerRecord

LEDGER_RECORD_CREATED → LEDGER_RECORD_APPENDED → LEDGER_RECORD_ARCHIVED.

## 8.13 ExecutionResult

RESULT_CREATED → RESULT_PUBLISHED → RESULT_CONSUMED → RESULT_ARCHIVED.

Alternative: RESULT_FAILED.

## 8.14 Outcome

OUTCOME_CREATED → OUTCOME_PUBLISHED → COMPARISON_PENDING → COMPARED → ARCHIVED.

Alternative: INVALIDATED_BY_AUDIT.

## 8.15 Evidence

EVIDENCE_PROPOSED → EVIDENCE_ACTIVE → EVIDENCE_ARCHIVED.

Alternative: EVIDENCE_SUPERSEDED.

## 8.16 Knowledge

PROPOSED → UNDER_REVIEW → VALIDATED → APPLIED.

Alternatives: CONTRADICTED, REJECTED, SUPERSEDED, ARCHIVED.

## 8.17 Criterion

CRITERION_CREATED → MEASURED → APPLIED → SUPERSEDED.

Alternative: ARCHIVED.

## 8.18 CriterionDelta

CRITERION_DELTA_CREATED → MEASURED → ACCEPTED → APPLIED_TO_CONTEXT.

Alternatives: REJECTED, SUPERSEDED, ARCHIVED.

## 8.19 ResourceState

RESOURCE_STATE_CREATED → REVIEWED → USED_AS_CONTEXT → SUPERSEDED.

Alternative: ARCHIVED.

---

# 9. Traceability

Traceability is mandatory from Reality observation through ResourceState.

## 9.1 Mandatory Identifiers

Minimum identifiers:

- reality_id
- event_id
- opportunity_id
- evaluation_id
- decision_id
- approval_id
- execution_signal_id
- execution_request_id
- execution_order_id
- execution_position_id
- execution_result_id
- outcome_id
- evidence_id
- knowledge_id
- criterion_id
- criterion_delta_id
- resource_state_id

## 9.2 Identifier Propagation

reality_id is optional until Reality is captured but must propagate if assigned.

event_id is created by Event and propagates through all downstream objects.

opportunity_id is created by OpportunityCandidate and propagates through all downstream decision, execution, outcome, and learning objects.

evaluation_id is created by EvaluatedOpportunity and propagates through Decision, Approval, Execution, Outcome, and Learning objects.

decision_id is created by Decision and propagates through ApprovedDecision, ExecutionSignal, internal Engine objects, ExecutionResult, Outcome, Evidence, Knowledge, Criterion, CriterionDelta, and ResourceState where lineage exists.

approval_id is created by ApprovedDecision and propagates through ExecutionSignal and all downstream execution and outcome objects.

execution_signal_id is created by ExecutionSignal and propagates through ExecutionRequest, ExecutionOrder, ExecutionPosition, ExecutionLedgerRecord, ExecutionResult, Outcome, and downstream learning objects where applicable.

execution_request_id is created inside Execution Engine and remains Engine-owned but must be referenced by ExecutionResult when applicable.

execution_order_id is created inside Execution Engine and remains Engine-owned but must be referenced by ledger records and ExecutionResult when applicable.

execution_position_id is created inside Execution Engine and remains Engine-owned but must be referenced by ledger records and ExecutionResult when applicable.

execution_result_id is created by Execution Engine and propagates to Outcome.

outcome_id is created by Outcome Collector and propagates to Evidence, Knowledge, Criterion, and CriterionDelta when applicable.

evidence_id is created by Scientific Layer and propagates to Knowledge.

knowledge_id is created by Scientific Layer and propagates to Criterion and CriterionDelta.

criterion_id is created by Criterion Engine and propagates to CriterionDelta and ResourceState.

criterion_delta_id is created by Criterion Engine and propagates to ResourceState.

resource_state_id is created by Resource Loop and closes the cycle snapshot.

## 9.3 Missing Identifier Rule

If an identifier is unavailable, the object must record the absence explicitly and explain why.

Silent trace gaps are forbidden.

---

# 10. Immutability Rules

## 10.1 Immutable Fields

All identifiers are immutable.

All parent references are immutable.

All creator and owner fields are immutable.

All publication timestamps are immutable.

All original factual observations are immutable.

All published decisions, approvals, execution signals, ledger records, outcomes, knowledge statements, criterion statements, criterion deltas, and resource snapshots are immutable.

## 10.2 Append-only Objects

ExecutionLedgerRecord is append-only.

Execution history is append-only.

Outcome audit history is append-only.

Scientific learning history is append-only by supersession, not mutation.

Criterion evolution is append-only by deltas and supersession.

## 10.3 Ownership Transfer Rules

Ownership does not transfer when an object is consumed.

Execution Engine consumes ExecutionSignal but does not own it.

Outcome Collector consumes ExecutionResult but does not own Execution Engine internals.

Scientific Layer consumes Outcome but does not own Outcome.

Criterion Engine consumes Knowledge but does not own Knowledge.

Resource Loop consumes CriterionDelta but does not own CriterionDelta.

## 10.4 Correction Rules

Corrections must be represented as:

- new objects;
- superseding objects;
- audit annotations;
- append-only ledger correction records.

In-place mutation is forbidden after publication.

---

# 11. Persistence Rules

| Object | Operational DB | Scientific DB | Execution Storage | Transient Memory | Archive |
|---|---|---|---|---|---|
| Reality | No | No | No | Yes | Optional reference only |
| Event | Yes | No | No | Optional | Yes |
| OpportunityCandidate | Yes | No | No | Optional | Yes |
| EvaluatedOpportunity | Yes | No | No | Optional | Yes |
| Decision | Yes | No | No | Optional | Yes |
| ApprovedDecision | Yes or approval store | No | Reference allowed | Optional | Yes |
| ExecutionSignal | Reference allowed | No | Yes | Optional | Yes |
| ExecutionRequest | No | No | Yes | Optional | Yes |
| ExecutionOrder | No | No | Yes | Optional | Yes |
| ExecutionPosition | No | No | Yes | Optional | Yes |
| ExecutionPortfolio | No | No | Yes | Optional | Yes |
| ExecutionLedgerRecord | No | No | Yes append-only | No after append | Yes |
| ExecutionResult | Handoff reference allowed | No | Yes | Optional | Yes |
| Outcome | Handoff reference allowed | Reference allowed | Reference allowed | Optional | Yes |
| Evidence | No | Yes | No | Optional | Yes |
| Knowledge | No | Yes | No | Optional | Yes |
| Criterion | No | Yes or Criterion archive | No | Optional | Yes |
| CriterionDelta | No | Yes or Criterion archive | No | Optional | Yes |
| ResourceState | No | Optional reference | No | Optional | Yes |

No implementation detail is prescribed by this table.

The table defines architectural storage authority only.

---

# 12. Architectural Constraints

The architecture explicitly forbids:

- multiple creators for one object;
- multiple owners for one object;
- circular ownership;
- objects changing type;
- aliases that create duplicated concepts;
- Execution objects modifying Scientific objects;
- Scientific objects modifying operational objects;
- Council modifying Execution objects;
- Execution Engine modifying Decisions;
- Execution Engine modifying ApprovedDecisions;
- Execution Engine modifying ExecutionSignals;
- Score Engine producing Execution objects;
- Collectors producing Decision objects;
- Scientific Layer producing orders;
- Resource Loop producing Events;
- Knowledge modifying historical Outcomes;
- Broker or Integration Layer owning execution objects;
- Integration Layer replacing Execution Engine;
- ExecutionRequest replacing ExecutionSignal.

---

# 13. Canonical Naming Rules

## 13.1 Singular Object Names

Object names are singular.

Correct:

- Event
- Decision
- ExecutionOrder
- Knowledge

Incorrect:

- Events
- Decisions
- Orders as canonical object name
- Knowledges

## 13.2 One Meaning Per Word

Each canonical name has exactly one meaning.

Event means observed reality record.

Decision means Council output.

ApprovedDecision means Approval Layer output.

ExecutionSignal means approved intention to execute.

ExecutionRequest means Execution Engine internal request.

ExecutionResult means Execution Engine output.

Outcome means factual downstream result collected for learning.

Knowledge means scientific learning.

Criterion means accumulated judgment.

## 13.3 No Synonyms

Do not introduce synonyms for canonical concepts.

Do not use Signal when ExecutionSignal is meant.

Do not use Request when ExecutionSignal is meant.

Do not use TradeResult when ExecutionResult or Outcome is meant.

Do not use Lesson when Knowledge is meant.

Do not use Score when Criterion is meant.

## 13.4 Prefix Rules

Execution-prefixed objects belong to the execution boundary.

Internal Engine execution objects use the Execution prefix but remain Engine-owned.

Scientific objects do not use the Execution prefix.

## 13.5 Duplicated Concepts

No new object may duplicate an existing object's purpose.

If an object seems necessary, first determine whether it is:

- a field;
- a state;
- a ledger record;
- a report;
- a new canonical object.

---

# 14. Future Compatibility

## 14.1 Introducing New Objects

A new object may be introduced only by an explicit architecture decision.

The decision must define:

- purpose;
- creator;
- owner;
- consumers;
- lifecycle;
- persistence;
- identifiers;
- relationships;
- immutability rules;
- compatibility with Pipeline V2.

## 14.2 Backward Compatibility

Existing object identifiers must remain valid.

Existing object meanings must not be silently changed.

A new object must not replace a canonical object without revising the relevant canonical architecture documents.

## 14.3 Deprecation Policy

Deprecation requires:

- explicit replacement object or removal reason;
- migration strategy;
- archival strategy;
- compatibility statement;
- approval in canonical architecture.

Deprecated objects remain readable for audit.

## 14.4 Extension Policy

Fields may be added if they do not change object ownership, creator, lifecycle, or meaning.

New optional fields must preserve backward compatibility.

New required fields require a versioned architecture revision.

---

# 15. Validation Checklist

OBJECT_MODEL_V1 is complete only if:

- every object has exactly one creator;
- every object has exactly one owner;
- every object has consumers;
- every object has a lifecycle;
- every object has persistence rules;
- every object has identifiers;
- every object has relationships;
- every object has architectural notes;
- canonical domain objects and internal Engine objects are explicitly distinguished;
- ExecutionSignal remains canonical;
- ExecutionRequest does not replace ExecutionSignal;
- ExecutionResult returns to the canonical Pipeline;
- no contradictions exist with `ARCHITECTURE_V2.md`;
- no contradictions exist with `PIPELINE_V2.md`;
- no contradictions exist with `INTEGRATION_ARCHITECTURE_V1.1.md`;
- no object has multiple creators;
- no object has multiple owners;
- no circular ownership exists;
- no implementation details are introduced.

This document performs no implementation.

It defines architecture only.
