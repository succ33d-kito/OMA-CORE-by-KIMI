# PIPELINE V2 — O.M.A.-C.O.R.E.

**Project:** O.M.A.-C.O.R.E.

**Version:** 1.0

**Status:** CANONICAL SPECIFICATION

**Date:** June 2026

**Scope:** Architecture only

---

# 1. Purpose

Pipeline V2 defines the complete Decision Intelligence Pipeline of O.M.A.-C.O.R.E.

It exists to make explicit how the system transforms external reality into accumulated Criterion without confusing operational execution, scientific learning, and resource feedback.

Pipeline V2 answers the architectural questions that every implementation must respect:

- what each layer receives;
- what each layer produces;
- which component owns each layer;
- which component consumes each output;
- which objects are immutable;
- which state transitions are allowed;
- which identifiers must propagate;
- which shortcuts are forbidden.

The canonical transformation is:

Reality → Event → OpportunityCandidate → EvaluatedOpportunity → Decision → ApprovedDecision → ExecutionSignal → ExecutionResult → Outcome → Knowledge → Criterion → ResourceState

Execution is only one stage in this pipeline. It is not the purpose of the system.

The purpose of the system is to develop Criterion: the accumulated ability to judge what matters, validated through explicit outcomes and transformed into better future decisions.

Pipeline V2 sits alongside `ARCHITECTURE_V2.md` and `INTEGRATION_ARCHITECTURE_V1.md`. Where this document speaks about pipeline contracts, object flow, object ownership, and mandatory propagation, it is canonical.

---

# 2. Architectural Principles

The following principles are mandatory.

## P1 — Single responsibility per layer

Every layer has exactly one architectural responsibility.

A layer may validate its own input and publish its own output, but it must not perform the responsibility of another layer.

## P2 — Exactly one output object per layer

Every layer publishes exactly one canonical output object.

Operational logs, telemetry, metrics, and diagnostics may exist, but they are not pipeline outputs.

## P3 — No layer bypass

Layers never bypass each other.

A downstream layer may only consume the canonical object produced by its immediate upstream layer unless this document explicitly defines a read-only reference dependency.

## P4 — Published objects are immutable

Objects are immutable after publication.

Corrections, revisions, enrichments, and results must be represented by later objects, not by mutating earlier objects.

## P5 — Learning never modifies operational decisions

Scientific learning may evaluate previous operational decisions, but it must never rewrite, delete, or retroactively modify them.

## P6 — Execution never modifies scientific knowledge

Execution produces execution facts and outcomes.

Execution does not create Knowledge, modify Knowledge, or interpret scientific meaning.

## P7 — Scientific Layer consumes outcomes but never produces orders

The Scientific Layer consumes Outcome objects and produces Knowledge.

It never produces ExecutionSignal objects, broker orders, position changes, or execution instructions.

## P8 — Approval is mandatory before execution

No decision may reach execution unless it has passed the Approval layer and produced an ApprovedDecision.

## P9 — Broker agnosticism

The pipeline must remain broker-agnostic.

Broker-specific behavior belongs behind the integration adapter boundary defined by `INTEGRATION_ARCHITECTURE_V1.md`.

## P10 — Evidence before autonomy

Autonomy may not increase because the pipeline exists.

The pipeline exists to generate traceable evidence before autonomy is expanded.

## P11 — One-person maintainability

The pipeline must remain understandable, auditable, and maintainable by one person.

Architectural clarity has priority over cleverness.

## P12 — Criterion is the goal

Profit, execution frequency, and signal volume are not the final goal.

Criterion development is the final architectural objective.

---

# 3. Complete Pipeline

The complete canonical pipeline is:

Reality

↓

Observation

↓

Interpretation

↓

Evaluation

↓

Deliberation

↓

Approval

↓

Execution Laboratory

↓

Execution

↓

Outcome

↓

Scientific Learning

↓

Criterion

↓

Resource Loop

Each layer is defined below.

---

## 3.1 Reality

**Purpose**

Represent the external world from which the system receives information.

Reality includes markets, macro data, news, geopolitical conditions, liquidity, volatility, social sentiment, and any external condition that may become observable.

**Owner**

External world. No internal component owns Reality.

**Input**

None.

**Output**

Reality.

**Consumers**

Observation layer.

**Responsibilities**

- Exist independently of the system.
- Provide observable conditions.
- Remain outside system control.

**Forbidden responsibilities**

- Making decisions.
- Producing signals.
- Producing hypotheses.
- Producing execution instructions.

---

## 3.2 Observation

**Purpose**

Transform observable Reality into structured Events.

**Owner**

Collectors.

**Input**

Reality.

**Output**

Event.

**Consumers**

Interpretation layer.

**Responsibilities**

- Observe external sources.
- Normalize observations into Events.
- Preserve source, timestamp, asset, type, urgency, confidence, and data quality context.
- Publish the Event as the only canonical output of the layer.

**Forbidden responsibilities**

- Scoring opportunities.
- Producing Decisions.
- Producing ExecutionSignals.
- Calling brokers.
- Creating Knowledge.

---

## 3.3 Interpretation

**Purpose**

Transform an Event into an OpportunityCandidate.

Interpretation answers: “What might this Event mean?”

**Owner**

Opportunity Engine.

**Input**

Event.

**Output**

OpportunityCandidate.

**Consumers**

Evaluation layer.

**Responsibilities**

- Interpret the Event within current system context.
- Identify possible opportunity direction, asset relevance, and candidate thesis.
- Preserve uncertainty.
- Preserve the originating event_id.

**Forbidden responsibilities**

- Final scoring.
- Approval.
- Execution.
- Outcome interpretation.
- Knowledge extraction.

---

## 3.4 Evaluation

**Purpose**

Transform an OpportunityCandidate into an EvaluatedOpportunity.

Evaluation answers: “How strong is this opportunity according to current scoring and evidence context?”

**Owner**

Score Engine.

**Input**

OpportunityCandidate.

**Output**

EvaluatedOpportunity.

**Consumers**

Deliberation layer.

**Responsibilities**

- Evaluate score.
- Evaluate conviction.
- Attach evaluation rationale.
- Preserve data quality and scientific quality context where available.
- Preserve event_id and opportunity_id.

**Forbidden responsibilities**

- Making final decisions.
- Approval.
- Dispatching signals.
- Broker communication.
- Scientific learning.

---

## 3.5 Deliberation

**Purpose**

Transform an EvaluatedOpportunity into a Decision.

Deliberation answers: “What course of action does the system choose, if any?”

**Owner**

Council.

**Input**

EvaluatedOpportunity.

**Output**

Decision.

**Consumers**

Approval layer.

**Responsibilities**

- Compare perspectives.
- Produce a decision recommendation.
- Record reasoning, alternatives, dissent, confidence, and constraints.
- Preserve event_id, opportunity_id, and decision_id lineage.

**Forbidden responsibilities**

- Approving execution.
- Sending orders.
- Bypassing Approval.
- Modifying scores.
- Writing scientific conclusions.

---

## 3.6 Approval

**Purpose**

Transform a Decision into an ApprovedDecision or an explicit non-approved terminal approval result.

Approval answers: “Is this Decision permitted to proceed?”

**Owner**

Approval Layer.

**Input**

Decision.

**Output**

ApprovedDecision.

**Consumers**

Execution Laboratory layer.

**Responsibilities**

- Apply mandatory approval checks.
- Determine approval state.
- Record who or what approved the decision.
- Record rejection or manual-review reason when applicable.
- Preserve event_id, opportunity_id, decision_id, and approval_id.

**Forbidden responsibilities**

- Executing orders.
- Calling brokers.
- Creating outcomes.
- Creating Knowledge.
- Increasing autonomy.

---

## 3.7 Execution Laboratory

**Purpose**

Transform an ApprovedDecision into an ExecutionSignal prepared for a controlled execution environment.

Execution Laboratory answers: “What execution instruction should be sent to the broker-agnostic execution boundary?”

**Owner**

Signal Dispatcher and integration boundary.

**Input**

ApprovedDecision.

**Output**

ExecutionSignal.

**Consumers**

Execution layer.

**Responsibilities**

- Convert an ApprovedDecision into a broker-agnostic ExecutionSignal.
- Preserve approval lineage.
- Select the configured execution adapter through the integration boundary.
- Maintain Paper Trading limitation until explicitly changed by architecture.

**Forbidden responsibilities**

- Changing the approved decision.
- Recalculating risk.
- Recalculating score.
- Creating broker-specific business logic in the core pipeline.
- Creating scientific conclusions.

---

## 3.8 Execution

**Purpose**

Transform an ExecutionSignal into an ExecutionResult.

Execution answers: “What happened when the approved signal reached the execution environment?”

**Owner**

Execution Adapter and Execution Monitor.

**Input**

ExecutionSignal.

**Output**

ExecutionResult.

**Consumers**

Outcome layer.

**Responsibilities**

- Send the signal to the active execution environment.
- Track acknowledgement, fill, active position, exit, close, cancellation, or failure.
- Record broker_order_id, position_id, trade_id, latency, retry, and error classification.
- Preserve all upstream identifiers.

**Forbidden responsibilities**

- Making decisions.
- Approving decisions.
- Modifying hypotheses.
- Producing Knowledge.
- Mutating Decision or ApprovedDecision objects.

---

## 3.9 Outcome

**Purpose**

Transform an ExecutionResult into an Outcome.

Outcome answers: “What was the final result of the action?”

**Owner**

Outcome Collector.

**Input**

ExecutionResult.

**Output**

Outcome.

**Consumers**

Scientific Learning layer.

**Responsibilities**

- Record final result facts.
- Record entry, exit, duration, PnL, MAE, MFE, slippage, fees, close reason, and timestamps where applicable.
- Preserve execution and decision lineage.
- Publish a factual Outcome.

**Forbidden responsibilities**

- Interpreting whether the hypothesis was good.
- Creating Knowledge.
- Modifying execution state.
- Modifying operational decisions.
- Modifying scientific history.

---

## 3.10 Scientific Learning

**Purpose**

Transform an Outcome into Knowledge.

Scientific Learning answers: “What did the system learn from comparing what happened to what was expected?”

**Owner**

Scientific Layer.

**Input**

Outcome.

**Output**

Knowledge.

**Consumers**

Criterion layer.

**Responsibilities**

- Compare outcomes to hypotheses and evidence where lineage exists.
- Produce validated, provisional, contradicted, or rejected knowledge according to evidence quality.
- Preserve outcome_id and upstream traceability.
- Store learning in scientific storage only.

**Forbidden responsibilities**

- Sending orders.
- Modifying operational database records.
- Modifying Decisions.
- Modifying ExecutionSignals.
- Modifying historical Outcomes.

---

## 3.11 Criterion

**Purpose**

Transform Knowledge into Criterion.

Criterion answers: “How has the system’s ability to judge what matters changed?”

**Owner**

Criterion Engine.

**Input**

Knowledge.

**Output**

Criterion.

**Consumers**

Resource Loop layer and future decision intelligence improvements.

**Responsibilities**

- Convert accumulated Knowledge into criterion deltas.
- Measure changes in judgment quality.
- Preserve knowledge_id and criterion_delta_id.
- Distinguish durable Criterion from provisional learning.

**Forbidden responsibilities**

- Producing orders.
- Rewriting Knowledge.
- Rewriting Outcomes.
- Rewriting Decisions.
- Optimizing for capital alone.

---

## 3.12 Resource Loop

**Purpose**

Transform Criterion into ResourceState.

Resource Loop answers: “How does improved Criterion affect scarce resources and future system capacity?”

**Owner**

Resource Loop.

**Input**

Criterion.

**Output**

ResourceState.

**Consumers**

Future Observation, Interpretation, Evaluation, and strategic planning processes.

**Responsibilities**

- Represent the state of scarce resources affected by decisions.
- Make resource consequences visible.
- Feed strategic context into future cycles without mutating prior objects.
- Preserve criterion lineage.

**Forbidden responsibilities**

- Executing trades.
- Approving decisions.
- Creating Events.
- Rewriting Criterion.
- Rewriting historical resource states.

---

# 4. Canonical Pipeline Objects

The canonical pipeline objects are exactly the following.

| Object | Purpose | Producer | Consumers | Mutable or Immutable | Persistent or Ephemeral | Lifecycle |
|---|---|---|---|---|---|---|
| Reality | External world conditions that can become observable. | External world | Observation | Immutable from system perspective | Ephemeral from system perspective | Exists independently before observation |
| Event | Structured record that something happened. | Observation / Collectors | Interpretation | Immutable after publication | Persistent | Created → Published → Consumed → Archived |
| OpportunityCandidate | Candidate interpretation of an Event as a possible opportunity. | Interpretation / Opportunity Engine | Evaluation | Immutable after publication | Persistent | Created → Published → Evaluated or Discarded |
| EvaluatedOpportunity | Scored and contextualized opportunity candidate. | Evaluation / Score Engine | Deliberation | Immutable after publication | Persistent | Created → Published → Deliberated or Rejected |
| Decision | Council commitment or non-action recommendation based on an EvaluatedOpportunity. | Deliberation / Council | Approval | Immutable after publication | Persistent | Created → Published → Submitted for Approval |
| ApprovedDecision | Approval result authorizing controlled execution. | Approval Layer | Execution Laboratory | Immutable after publication | Persistent | Submitted → Approved or Rejected or Manual Review |
| ExecutionSignal | Broker-agnostic execution instruction derived from an ApprovedDecision. | Execution Laboratory / Signal Dispatcher | Execution | Immutable after publication | Persistent | Created → Validated → Dispatched or Failed |
| ExecutionResult | Factual execution record returned by the execution environment. | Execution Adapter / Execution Monitor | Outcome | Immutable after publication | Persistent | Acknowledged → Filled or Cancelled or Failed → Closed when applicable |
| Outcome | Factual final result of an executed or attempted action. | Outcome Collector | Scientific Learning | Immutable after publication | Persistent | Created → Published → Compared → Archived |
| Knowledge | Scientific learning extracted from Outcome comparison. | Scientific Learning / Scientific Layer | Criterion | Immutable after publication; superseded by later Knowledge if needed | Persistent | Proposed → Validated or Contradicted or Rejected → Applied or Archived |
| Criterion | Accumulated judgment delta derived from Knowledge. | Criterion Engine | Resource Loop and future decision context | Immutable after publication; accumulated by later deltas | Persistent | Created → Measured → Applied → Superseded by newer Criterion state |
| ResourceState | Snapshot of scarce resource state influenced by Criterion and decisions. | Resource Loop | Future strategic planning and future cycle context | Immutable after publication | Persistent | Created → Reviewed → Used as context → Superseded by later ResourceState |

---

# 5. Ownership Matrix

| Layer | Owner Component | Produced Object | Consumed By | Forbidden Access |
|---|---|---|---|---|
| Reality | External world | Reality | Observation | Council; Approval; Execution; Scientific Layer |
| Observation | Collectors | Event | Interpretation | Execution; Broker; Scientific Layer as writer |
| Interpretation | Opportunity Engine | OpportunityCandidate | Evaluation | Broker; Execution; Approval |
| Evaluation | Score Engine | EvaluatedOpportunity | Deliberation | Broker; Execution Adapter; Scientific writer access |
| Deliberation | Council | Decision | Approval | Broker; Execution Adapter; Scientific writer access |
| Approval | Approval Layer | ApprovedDecision | Execution Laboratory | Broker direct access; Scientific Layer as approver |
| Execution Laboratory | Signal Dispatcher / Integration Boundary | ExecutionSignal | Execution | Score Engine modification; Council modification; Scientific modification |
| Execution | Execution Adapter / Execution Monitor | ExecutionResult | Outcome | Council; Score Engine; Scientific Knowledge writer |
| Outcome | Outcome Collector | Outcome | Scientific Learning | Score Engine; Council; Broker; Execution Adapter mutation |
| Scientific Learning | Scientific Layer | Knowledge | Criterion | Broker; ExecutionSignal production; Operational DB mutation |
| Criterion | Criterion Engine | Criterion | Resource Loop | Broker; Execution; Historical Outcome mutation |
| Resource Loop | Resource Loop | ResourceState | Future strategic context | Broker; Event creation; Historical Criterion mutation |

---

# 6. Object Flow

The exact canonical object flow is:

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

ExecutionResult

↓

Outcome

↓

Knowledge

↓

Criterion

Reality precedes Event.

ResourceState follows Criterion.

No object may skip layers.

The following shortcuts are explicitly forbidden:

- Event → Decision.
- Event → ExecutionSignal.
- Event → Execution.
- OpportunityCandidate → Decision.
- EvaluatedOpportunity → ExecutionSignal.
- Decision → ExecutionSignal without ApprovedDecision.
- Decision → Broker.
- ApprovedDecision → Broker without ExecutionSignal.
- ExecutionResult → Knowledge without Outcome.
- Outcome → Criterion without Knowledge.
- Knowledge → Execution.
- Criterion → Broker.

Every object must be consumed only by its defined downstream consumer unless it is being read for audit, traceability, or diagnostics.

Audit reads never authorize bypass.

---

# 7. State Machines

This section defines architectural state machines only.

No state transition may move backward.

Corrections require a new object, a superseding object, or an explicit terminal state.

---

## 7.1 Opportunity State Machine

Applies to OpportunityCandidate and EvaluatedOpportunity lifecycle.

Allowed states:

- CANDIDATE_CREATED
- CANDIDATE_PUBLISHED
- EVALUATION_PENDING
- EVALUATED
- DELIBERATION_PENDING
- DISCARDED
- EXPIRED

Allowed transitions:

- CANDIDATE_CREATED → CANDIDATE_PUBLISHED
- CANDIDATE_PUBLISHED → EVALUATION_PENDING
- EVALUATION_PENDING → EVALUATED
- EVALUATED → DELIBERATION_PENDING
- CANDIDATE_PUBLISHED → DISCARDED
- EVALUATION_PENDING → DISCARDED
- EVALUATED → DISCARDED
- CANDIDATE_PUBLISHED → EXPIRED
- EVALUATED → EXPIRED

Forbidden transitions:

- EVALUATED → CANDIDATE_CREATED
- DISCARDED → EVALUATED
- EXPIRED → DELIBERATION_PENDING
- Any Opportunity state → ExecutionSignal

---

## 7.2 Decision State Machine

Applies to Decision and ApprovedDecision lifecycle.

Allowed states:

- DECISION_CREATED
- DECISION_PUBLISHED
- APPROVAL_PENDING
- APPROVED
- REJECTED
- MANUAL_REVIEW
- EXPIRED

Allowed transitions:

- DECISION_CREATED → DECISION_PUBLISHED
- DECISION_PUBLISHED → APPROVAL_PENDING
- APPROVAL_PENDING → APPROVED
- APPROVAL_PENDING → REJECTED
- APPROVAL_PENDING → MANUAL_REVIEW
- DECISION_PUBLISHED → EXPIRED
- MANUAL_REVIEW → APPROVED
- MANUAL_REVIEW → REJECTED
- MANUAL_REVIEW → EXPIRED

Forbidden transitions:

- REJECTED → APPROVED
- EXPIRED → APPROVED
- APPROVED → DECISION_CREATED
- DECISION_CREATED → ExecutionSignal
- DECISION_PUBLISHED → ExecutionSignal without APPROVED state

---

## 7.3 ExecutionSignal State Machine

Applies to ExecutionSignal lifecycle.

Allowed states:

- CREATED
- VALIDATED
- APPROVED
- DISPATCHED
- ACKNOWLEDGED
- FILLED
- ACTIVE
- EXITING
- CLOSED
- FAILED
- CANCELLED
- REJECTED

Allowed transitions:

- CREATED → VALIDATED
- VALIDATED → APPROVED
- APPROVED → DISPATCHED
- DISPATCHED → ACKNOWLEDGED
- ACKNOWLEDGED → FILLED
- FILLED → ACTIVE
- ACTIVE → EXITING
- EXITING → CLOSED
- CREATED → REJECTED
- VALIDATED → REJECTED
- DISPATCHED → FAILED
- ACKNOWLEDGED → FAILED
- ACKNOWLEDGED → CANCELLED
- ACTIVE → FAILED
- ACTIVE → CANCELLED

Forbidden transitions:

- Any later state → any earlier state.
- FAILED → DISPATCHED.
- CANCELLED → ACTIVE.
- CLOSED → ACTIVE.
- REJECTED → APPROVED.

---

## 7.4 Outcome State Machine

Applies to Outcome lifecycle.

Allowed states:

- OUTCOME_CREATED
- OUTCOME_PUBLISHED
- COMPARISON_PENDING
- COMPARED
- ARCHIVED
- INVALIDATED_BY_AUDIT

Allowed transitions:

- OUTCOME_CREATED → OUTCOME_PUBLISHED
- OUTCOME_PUBLISHED → COMPARISON_PENDING
- COMPARISON_PENDING → COMPARED
- COMPARED → ARCHIVED
- OUTCOME_PUBLISHED → INVALIDATED_BY_AUDIT
- COMPARISON_PENDING → INVALIDATED_BY_AUDIT

Forbidden transitions:

- ARCHIVED → COMPARISON_PENDING.
- INVALIDATED_BY_AUDIT → COMPARED.
- COMPARED → OUTCOME_CREATED.
- Outcome → ExecutionSignal.

Invalidation does not delete or rewrite the Outcome. It marks that the Outcome must not be used as valid evidence without review.

---

## 7.5 Knowledge State Machine

Applies to Knowledge lifecycle.

Allowed states:

- PROPOSED
- UNDER_REVIEW
- VALIDATED
- CONTRADICTED
- REJECTED
- APPLIED
- SUPERSEDED
- ARCHIVED

Allowed transitions:

- PROPOSED → UNDER_REVIEW
- UNDER_REVIEW → VALIDATED
- UNDER_REVIEW → CONTRADICTED
- UNDER_REVIEW → REJECTED
- VALIDATED → APPLIED
- VALIDATED → SUPERSEDED
- CONTRADICTED → ARCHIVED
- REJECTED → ARCHIVED
- APPLIED → SUPERSEDED
- SUPERSEDED → ARCHIVED

Forbidden transitions:

- REJECTED → VALIDATED.
- ARCHIVED → APPLIED.
- SUPERSEDED → VALIDATED as the same object.
- Knowledge → ExecutionSignal.
- Knowledge → Broker.

---

## 7.6 Criterion State Machine

Applies to Criterion lifecycle.

Allowed states:

- CRITERION_DELTA_CREATED
- MEASURED
- ACCEPTED
- APPLIED_TO_CONTEXT
- SUPERSEDED
- ARCHIVED

Allowed transitions:

- CRITERION_DELTA_CREATED → MEASURED
- MEASURED → ACCEPTED
- ACCEPTED → APPLIED_TO_CONTEXT
- ACCEPTED → SUPERSEDED
- APPLIED_TO_CONTEXT → SUPERSEDED
- SUPERSEDED → ARCHIVED

Forbidden transitions:

- ARCHIVED → APPLIED_TO_CONTEXT.
- SUPERSEDED → ACCEPTED as the same object.
- Criterion → ExecutionSignal.
- Criterion → Broker.
- Criterion → historical Outcome mutation.

---

# 8. Traceability

Every pipeline cycle must preserve traceability from the originating Event to the resulting Criterion and ResourceState.

The minimum mandatory identifiers are:

- event_id
- opportunity_id
- decision_id
- approval_id
- execution_signal_id
- broker_order_id
- position_id
- trade_id
- outcome_id
- knowledge_id
- criterion_delta_id

## 8.1 Propagation Rules

**event_id**

Created by Observation. Propagates to OpportunityCandidate, EvaluatedOpportunity, Decision, ApprovedDecision, ExecutionSignal, ExecutionResult, Outcome, Knowledge, and Criterion when lineage exists.

**opportunity_id**

Created by Interpretation. Propagates to EvaluatedOpportunity, Decision, ApprovedDecision, ExecutionSignal, ExecutionResult, Outcome, Knowledge, and Criterion.

**decision_id**

Created by Deliberation. Propagates to ApprovedDecision, ExecutionSignal, ExecutionResult, Outcome, Knowledge, and Criterion.

**approval_id**

Created by Approval. Propagates to ApprovedDecision, ExecutionSignal, ExecutionResult, Outcome, Knowledge, and Criterion.

**execution_signal_id**

Created by Execution Laboratory. Propagates to ExecutionResult, Outcome, Knowledge, and Criterion.

**broker_order_id**

Created or returned by the Execution environment. Propagates to ExecutionResult and Outcome. It may be referenced by Knowledge only as factual lineage, never as a scientific cause by itself.

**position_id**

Created or returned by the Execution environment when a position exists. Propagates to ExecutionResult and Outcome.

**trade_id**

Created when a trade record exists. Propagates to ExecutionResult and Outcome.

**outcome_id**

Created by Outcome Collector. Propagates to Knowledge and Criterion.

**knowledge_id**

Created by Scientific Learning. Propagates to Criterion and ResourceState.

**criterion_delta_id**

Created by Criterion Engine. Propagates to ResourceState and future cycle context.

## 8.2 Traceability Requirements

A complete trace must answer:

- which Event originated the cycle;
- which OpportunityCandidate was produced;
- how it was evaluated;
- which Decision was made;
- whether and how it was approved;
- which ExecutionSignal was dispatched;
- what the execution environment returned;
- what Outcome was recorded;
- what Knowledge was extracted;
- what Criterion changed;
- what ResourceState was affected.

If any identifier is unavailable, the object must explicitly record that the identifier is absent and why.

Silent trace gaps are forbidden.

---

# 9. Layer Contracts

Each layer has a fixed architectural contract.

---

## 9.1 Reality Contract

**Allowed Inputs**

None.

**Allowed Outputs**

Reality.

**Allowed Side Effects**

None controlled by the system.

**Forbidden Operations**

- Decision production.
- Execution production.
- Knowledge production.

**Dependencies**

None.

---

## 9.2 Observation Contract

**Allowed Inputs**

Reality.

**Allowed Outputs**

Event.

**Allowed Side Effects**

- Source access.
- Collection telemetry.
- Data quality diagnostics.

**Forbidden Operations**

- Producing OpportunityCandidate directly from anything other than Event publication.
- Producing Decision.
- Producing ExecutionSignal.
- Broker access.
- Scientific writes.

**Dependencies**

- External data sources.
- Collector configuration.
- Data validation rules.

---

## 9.3 Interpretation Contract

**Allowed Inputs**

Event.

**Allowed Outputs**

OpportunityCandidate.

**Allowed Side Effects**

- Interpretation telemetry.
- Candidate rejection record.

**Forbidden Operations**

- Final scoring.
- Approval.
- Execution.
- Broker access.
- Knowledge extraction.

**Dependencies**

- Event schema.
- Current read-only context where permitted.

---

## 9.4 Evaluation Contract

**Allowed Inputs**

OpportunityCandidate.

**Allowed Outputs**

EvaluatedOpportunity.

**Allowed Side Effects**

- Evaluation telemetry.
- Score audit record.

**Forbidden Operations**

- Making final Decisions.
- Approval.
- ExecutionSignal creation.
- Broker access.
- Mutating OpportunityCandidate.

**Dependencies**

- Score Engine.
- Data quality context.
- Read-only historical calibration context where permitted.

---

## 9.5 Deliberation Contract

**Allowed Inputs**

EvaluatedOpportunity.

**Allowed Outputs**

Decision.

**Allowed Side Effects**

- Council reasoning record.
- Dissent and alternatives record.

**Forbidden Operations**

- Approval.
- Broker access.
- ExecutionSignal creation.
- Score mutation.
- Scientific writes.

**Dependencies**

- Council.
- Agent opinions or equivalent decision perspectives.
- EvaluatedOpportunity lineage.

---

## 9.6 Approval Contract

**Allowed Inputs**

Decision.

**Allowed Outputs**

ApprovedDecision.

**Allowed Side Effects**

- Approval audit record.
- Manual review record.
- Rejection record.

**Forbidden Operations**

- Broker access.
- Order creation.
- Outcome creation.
- Knowledge creation.
- Decision mutation.

**Dependencies**

- Approval criteria.
- Risk constraints.
- Cooldown constraints.
- Capital constraints.
- Duplicate checks.
- Market-open checks.
- Data quality checks.
- Scientific quality checks.

---

## 9.7 Execution Laboratory Contract

**Allowed Inputs**

ApprovedDecision.

**Allowed Outputs**

ExecutionSignal.

**Allowed Side Effects**

- Dispatch telemetry.
- Adapter selection record.
- Signal validation record.

**Forbidden Operations**

- Changing approved direction, size, or intent.
- Recalculating score.
- Re-approving the decision.
- Creating broker-specific rules in the core pipeline.
- Creating Knowledge.

**Dependencies**

- Integration configuration.
- Signal Dispatcher.
- Execution adapter boundary.

---

## 9.8 Execution Contract

**Allowed Inputs**

ExecutionSignal.

**Allowed Outputs**

ExecutionResult.

**Allowed Side Effects**

- Paper Trading order submission.
- Broker-agnostic execution tracking.
- Execution telemetry.
- Error classification.
- Retry record.

**Forbidden Operations**

- Decision making.
- Approval.
- Scientific learning.
- Knowledge mutation.
- Historical Outcome mutation.

**Dependencies**

- Execution Adapter.
- Execution Monitor.
- Active Paper Trading environment.
- Integration safety constraints.

---

## 9.9 Outcome Contract

**Allowed Inputs**

ExecutionResult.

**Allowed Outputs**

Outcome.

**Allowed Side Effects**

- Outcome persistence.
- Outcome audit record.

**Forbidden Operations**

- Hypothesis verdict assignment as final Knowledge.
- Decision mutation.
- Execution mutation.
- Broker access.
- Criterion mutation.

**Dependencies**

- ExecutionResult lineage.
- Outcome Collector.
- Required trace identifiers.

---

## 9.10 Scientific Learning Contract

**Allowed Inputs**

Outcome.

**Allowed Outputs**

Knowledge.

**Allowed Side Effects**

- scientific.db writes.
- Hypothesis comparison record.
- Evidence association record.
- Knowledge lifecycle record.

**Forbidden Operations**

- Operational DB mutation.
- Broker access.
- ExecutionSignal creation.
- Decision mutation.
- Outcome mutation.

**Dependencies**

- Scientific Store.
- Hypothesis lineage where available.
- Evidence lineage where available.
- Outcome comparison rules.

---

## 9.11 Criterion Contract

**Allowed Inputs**

Knowledge.

**Allowed Outputs**

Criterion.

**Allowed Side Effects**

- Criterion measurement record.
- Criterion delta record.

**Forbidden Operations**

- Broker access.
- ExecutionSignal creation.
- Historical Knowledge mutation.
- Historical Outcome mutation.
- Capital-only optimization.

**Dependencies**

- Knowledge lifecycle state.
- Criterion measurement rules.
- Historical Criterion context as read-only reference.

---

## 9.12 Resource Loop Contract

**Allowed Inputs**

Criterion.

**Allowed Outputs**

ResourceState.

**Allowed Side Effects**

- Resource state snapshot.
- Strategic context update.

**Forbidden Operations**

- Broker access.
- Event creation.
- Decision approval.
- Historical Criterion mutation.
- Historical ResourceState mutation.

**Dependencies**

- Criterion lineage.
- Scarce resource definitions.
- Strategic context rules.

---

# 10. Architectural Constraints

The following constraints are mandatory.

## 10.1 Forbidden direct paths

The architecture explicitly forbids:

- Direct Event → Execution.
- Direct Event → Broker.
- Direct Council → Broker.
- Direct Score → Broker.
- Direct EvaluatedOpportunity → Broker.
- Direct Decision → Broker.
- Direct Decision → Execution without Approval.
- Direct Scientific Layer → Broker.
- Direct Knowledge → ExecutionSignal.
- Direct Criterion → ExecutionSignal.

## 10.2 Forbidden authority violations

The architecture explicitly forbids:

- Scientific Layer modifying the operational pipeline.
- Broker modifying Decisions.
- Broker modifying ApprovedDecisions.
- Broker modifying ExecutionSignals.
- Execution modifying hypotheses.
- Execution modifying Knowledge.
- Knowledge modifying historical Outcomes.
- Criterion modifying historical Knowledge.
- Resource Loop modifying historical Criterion.

## 10.3 Forbidden storage violations

The architecture explicitly forbids:

- Scientific learning writes to the operational database.
- Operational execution writes to scientific knowledge stores except through the Outcome → Scientific Learning boundary.
- Broker-specific state becoming canonical pipeline state.
- Silent deletion of canonical objects.

## 10.4 Forbidden autonomy expansion

The architecture explicitly forbids:

- Auto-approval without explicit architecture approval.
- Real capital execution.
- Execution without Approval Layer.
- Treating Paper Trading success as permission for live trading.

---

# 11. Validation Rules

Pipeline V2 is complete only if all acceptance criteria are satisfied.

## 11.1 Layer validation

- Every layer has exactly one responsibility.
- Every layer has exactly one canonical output object.
- Every layer has explicit allowed inputs.
- Every layer has explicit forbidden operations.
- Every layer has an owner.
- Every layer has defined consumers.

## 11.2 Object validation

- Every object has exactly one producer.
- Every object has explicit consumers.
- Every object has a mutability rule.
- Every object has a persistence rule.
- Every object has a lifecycle.

## 11.3 Flow validation

- Every transition is traceable.
- No object skips a layer.
- No shortcut path exists.
- No circular dependencies exist.
- Audit reads do not become control flow.

## 11.4 Traceability validation

- event_id propagates from Event onward.
- opportunity_id propagates from OpportunityCandidate onward.
- decision_id propagates from Decision onward.
- approval_id propagates from ApprovedDecision onward.
- execution_signal_id propagates from ExecutionSignal onward.
- broker_order_id, position_id, and trade_id are recorded when produced by execution.
- outcome_id propagates from Outcome onward.
- knowledge_id propagates from Knowledge onward.
- criterion_delta_id propagates from Criterion onward.
- Missing identifiers are explicit and explained.

## 11.5 Architecture-only validation

This document contains no implementation details.

It does not define APIs.

It does not define classes.

It does not define interfaces.

It does not define schemas.

It does not define configuration-file content.

It does not define Python.

It defines architecture only.

## 11.6 Success definition

Pipeline V2 succeeds when a full cycle is architecturally reconstructible:

Reality → Event → OpportunityCandidate → EvaluatedOpportunity → Decision → ApprovedDecision → ExecutionSignal → ExecutionResult → Outcome → Knowledge → Criterion → ResourceState

The success of the pipeline is not more execution.

The success of the pipeline is complete, auditable transformation from Reality into Criterion, with execution treated as one controlled evidence-producing stage.
