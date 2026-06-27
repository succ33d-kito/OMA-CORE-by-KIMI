# Scientific Object Model

## The Bridge Between Philosophy and Implementation

*Version 1.0 — June 2026*

---

## 0. Preamble

ERA I produced eighteen first-principles documents defining what O.M.A.-C.O.R.E. believes, rejects, assumes, and questions. These documents are philosophical. They define concepts, principles, and commitments. They are not implementable.

ERA II begins with a translation layer — the Scientific Object Model.

This document transforms every scientific concept from the first-principles corpus into an explicit operational object or intentionally discards it. Every concept that survives is a concept that must exist in implementation. Every concept that is removed is a concept that philosophy considered but the project will not build.

This is not a database schema. It is not a class diagram. It is not an API design. It is a conceptual map of what truly exists inside the project's universe — the fundamental entities from which all implementation derives.

---

## PART I: Why an Object Model Is Necessary

### 1.1 Concepts Alone Cannot Be Implemented

A concept is a philosophical abstraction. "Hypothesis" as defined in the Glossary — *"a structured, recorded belief about a consequence"* — is a definition, not a specification.

To implement a hypothesis, the project must know:
- When is it created? By what?
- What attributes must it carry?
- What are its valid states?
- How does it transition between states?
- What produces it? What consumes it?
- What happens when it is confirmed? Rejected? Inconclusive?
- How does it relate to evidence, decisions, outcomes, and knowledge?
- What is its lifecycle? When is it archived? When is it retired?
- What guarantees its integrity? Its immutability? Its queryability?

These questions are not answered by philosophical definitions. They are answered by an object model — a precise specification of what the concept is as an operational entity.

### 1.2 Implementation Without an Object Model Creates Ambiguity

When engineering begins without a precise object model, each engineer interprets the concepts differently. The result is:
- Inconsistent implementations of the same concept across different components
- Implicit relationships that are discovered too late
- Missing edges in the conceptual graph that are papered over with workarounds
- Technical debt that mirrors conceptual debt

The object model is the contract between philosophy and engineering. It ensures that what the philosophy describes is what the implementation builds.

### 1.3 Every Scientific Concept Must Become an Explicit Object or Be Discarded

A concept that is defined in philosophy but does not appear in the object model is a concept that the project does not truly intend to build. It is decoration.

This is a forcing function: if a concept cannot be specified precisely enough to become an object, it is not yet ready for implementation. It should remain in philosophy until it can be specified.

Conversely, any concept that survives into the object model is a concept the project commits to implementing. Every object has a cost — storage, processing, maintenance, cognitive load. Every object must justify its existence.

---

## PART II: Audit of Every Candidate Concept

### 2.1 Audit Method

Every document in the first-principles corpus (00–18 plus 01_MVP_REDEFINITION) was audited for candidate concepts. A candidate concept is any noun that:
- Appears in a definition or description of what the system is or does
- Has attributes, behaviors, or relationships to other concepts
- Could plausibly be represented as a data structure with identity and lifecycle

Each candidate was evaluated against these criteria:
1. **Independence:** Does it have its own identity, lifecycle, and behavior? Or is it an attribute of another concept?
2. **Necessity:** Does the project lose essential capability if this concept is not independently represented?
3. **Operationality:** Can this concept be observed, measured, or manipulated in the running system?
4. **Parsimony:** Does it add more clarity than complexity?

### 2.2 Complete Concept Inventory

The audit identified the following candidate concepts across all documents:

| # | Concept | Source Documents | Initial Assessment |
|---|---------|-----------------|-------------------|
| 1 | Need | 16, 18, 01 | Gap in criterion; triggers research |
| 2 | Question | 16, 18, 01 | Frames the inquiry |
| 3 | Hypothesis | 04, 08, 14, 15, 16, 17, 18, 01 | Central unit of learning |
| 4 | Evidence | 04, 14, 15, 16, 17, 18 | Information relative to a hypothesis |
| 5 | Decision | 04, 16, 17, 01 | Choice between alternatives |
| 6 | Outcome | 04, 14, 16, 17, 01 | Result of action |
| 7 | Reflection | 14, 16, 17, 18, 01 | Analysis comparing outcome to hypothesis |
| 8 | Knowledge | 04, 14, 16, 17, 18, 01 | Generalizable lesson |
| 9 | Pattern | 08, 16, 17 | Empirical observation, repeated validated knowledge |
| 10 | Scenario | 14, 16, 01 | Expected consequences if hypothesis is true |
| 11 | Conviction | 17, 01 | Strength of action based on confidence |
| 12 | ErrorType | 14, 15, 16, 17 | Taxonomy of decision failure categories |
| 13 | SourceReliability | 14, 15, 17 | Trustworthiness of an information source |
| 14 | ContextProfile | 08, 14, 15, 16 | Description of conditions at a point in time |
| 15 | ResearchProposal | 18, 01 | Defines what is being investigated |
| 16 | Experiment | 17, 18, 01 | Specific test design |
| 17 | DecisionRecord | 01 | Complete scientific record of one cycle |
| 18 | CriterionSnapshot | 15, 17 | Periodic measurement of criterion metrics |
| 19 | Memory | 04, 08, 14, 15, 01 | Storage of experience |
| 20 | Trust | 16, 17 | Confidence in sources or system (undefined) |
| 21 | Autonomy | 17 | Permission level for independent operation |
| 22 | Opportunity | 04, 08, 17 | Actionable consequence |
| 23 | Correlation | 04, 07, 08 | Relationship between events |
| 24 | Cluster | 04, 07, 08 | Group of related events |
| 25 | Consequence | 04, 07, 08, 14 | Possible future state |
| 26 | Wisdom | 04, 16 | Cross-domain criterion |
| 27 | Reliability | 04 | Trustworthiness of a source (redundant) |
| 28 | Signal | 04 | Validated predictive information |
| 29 | Noise | 04 | Non-predictive information |
| 30 | Information | 04, 16 | Data in context |
| 31 | Action | 04, 16, 01 | Execution of a decision |
| 32 | Event | 04, 07, 08 | Discrete occurrence producing information |
| 33 | Calibration | 08, 14, 16, 17 | Alignment between confidence and accuracy |
| 34 | Confidence | 04, 14, 16, 17 | Estimate of hypothesis correctness |
| 35 | Criterion | 08, 14, 15, 16, 17 | Accumulated ability to judge what matters |

### 2.3 Evaluation and Disposition

Each candidate was evaluated and assigned one of four dispositions:

**ACCEPT** — Exists as an independent object
**MERGE** — Combined into another existing object
**ATTRIBUTE** — Demoted to an attribute of another object
**REMOVE** — Not operational; does not justify independent existence

| # | Concept | Disposition | Rationale |
|---|---------|------------|-----------|
| 1 | Need | ATTRIBUTE | Part of ResearchProposal. A need is the reason a proposal exists, not an independent entity. |
| 2 | Question | ATTRIBUTE | Part of ResearchProposal. A question is a property of what is being investigated. |
| 3 | Hypothesis | **ACCEPT** | Central unit of learning. Independent lifecycle, identity, relationships. Cannot be merged. |
| 4 | Evidence | **ACCEPT** | Independent object with direction, weight, source, decay. Must be trackable per hypothesis. |
| 5 | Decision | **ACCEPT** | Independent object linked to hypothesis. Contains choice, rationale, alternatives considered. |
| 6 | Outcome | **ACCEPT** | Result of action. Independent object with temporal and quantitative properties. |
| 7 | Reflection | MERGE → DecisionRecord | Reflection is a stage within the DecisionRecord lifecycle; not independently useful. |
| 8 | Knowledge | **ACCEPT** | Independent object with lifecycle (extracted, applied, revised, invalidated). |
| 9 | Pattern | MERGE → Knowledge | A pattern is knowledge with lower confidence. Same structure, different label. |
| 10 | Scenario | ATTRIBUTE → Hypothesis | A scenario is a behavior of a hypothesis (16 Part V). It generates expected observations. |
| 11 | Conviction | ATTRIBUTE → Decision | Conviction is the strength with which a decision is executed. It is a numeric attribute. |
| 12 | ErrorType | **ACCEPT** | Taxonomy of failure categories. Has identity, hierarchy, and relationship to Knowledge. |
| 13 | SourceReliability | ATTRIBUTE → Evidence | Part of Evidence metadata. A source identifier and reliability score. |
| 14 | ContextProfile | ATTRIBUTE → Hypothesis | Conditions under which a hypothesis is formed. Property of Hypothesis and Knowledge. |
| 15 | ResearchProposal | **ACCEPT** | Groups experiments under a common research question. Has lifecycle. |
| 16 | Experiment | MERGE → DecisionRecord collection | An experiment is a set of DecisionRecords sharing a ResearchProposal and hypothesis. Not independently stored. |
| 17 | DecisionRecord | **ACCEPT** | Primary aggregate: bundles Hypothesis, Evidence, Decision, Outcome, Reflection, Knowledge for one cycle. |
| 18 | CriterionSnapshot | **ACCEPT** | Periodic measurement of aggregate criterion metrics. Has identity and temporal properties. |
| 19 | Memory | REMOVE | Infrastructure concern, not a domain object. The three memories are storage mechanisms. |
| 20 | Trust | REMOVE | Undefined concept. Appears in the causal chain but has no operational definition. |
| 21 | Autonomy | REMOVE | Policy level, not a runtime object. Autonomy is a configuration parameter, not a data entity. |
| 22 | Opportunity | REMOVE | A hypothesis with sufficiently high confidence to act. The distinction is a threshold, not an object. |
| 23 | Correlation | REMOVE | Statistical observation. Not a first-class object in the learning system. |
| 24 | Cluster | REMOVE | Query result — a group of events pointing to a common consequence. Generated, not stored. |
| 25 | Consequence | ATTRIBUTE → Hypothesis | Predicted future state. Part of the Hypothesis's prediction specification. |
| 26 | Wisdom | REMOVE | Cross-domain criterion is still criterion. Not operationally distinct. |
| 27 | Reliability | REMOVE | Redundant with SourceReliability. The Glossary definition is superseded. |
| 28 | Signal | REMOVE | Property of Information relative to a Hypothesis. Not a first-class object. |
| 29 | Noise | REMOVE | Property of Information relative to a Hypothesis. Not a first-class object. |
| 30 | Information | REMOVE | Transient intermediary between Data and Evidence. Not stored as an independent entity. |
| 31 | Action | ATTRIBUTE → Decision | Action is the executed decision. Part of Decision's lifecycle stage. |
| 32 | Event | REMOVE | Discrete observation. Events are raw inputs; they are not managed as learning objects. |
| 33 | Calibration | ATTRIBUTE → CriterionSnapshot | Calibration is a metric computed across many decisions, not a stored object. |
| 34 | Confidence | ATTRIBUTE → Hypothesis | Confidence is an attribute of a hypothesis at decision time. |
| 35 | Criterion | **ACCEPT** | The central concept. Criterion is the accumulated state of the system's judgment. |

### 2.4 Final Object Set

After audit, merging, demotion, and removal:

**ACCEPTED (8 objects):**

| # | Object | Disposition Source |
|---|--------|-------------------|
| 1 | **Hypothesis** | Hypothesis (3) |
| 2 | **Evidence** | Evidence (4) |
| 3 | **Decision** | Decision (5) + Action (31) + Conviction (11) |
| 4 | **Outcome** | Outcome (6) |
| 5 | **Knowledge** | Knowledge (8) + Pattern (9) |
| 6 | **ErrorType** | ErrorType (12) |
| 7 | **ResearchProposal** | ResearchProposal (15) + Need (1) + Question (2) |
| 8 | **CriterionSnapshot** | CriterionSnapshot (18) + Calibration (33) |

**AGGREGATE OBJECTS (formed by merging multiple accepted objects):**

| # | Object | Contains | Purpose |
|---|--------|----------|---------|
| 9 | **DecisionRecord** | Hypothesis (1), Evidence collection (2), Decision (3), Outcome (4), Reflection, Knowledge (5), ErrorType (6) | Complete scientific record of one operational cycle. The primary unit of analysis. |

**Total: 9 objects (8 independent + 1 aggregate)**

From 35 candidate concepts to 9 objects. Reduction: 74%.

Each removed or merged concept was evaluated against the question: "Would the project lose essential capability if this concept is not independently represented?" Only those that would lose essential capability survived.

---

## PART III: Object Definitions

Each object is defined from a scientific perspective — what it is, why it exists, what it produces, and how it contributes to criterion.

---

### Object 1: Hypothesis

**Purpose.** The hypothesis is the unit of learning. It is the smallest structure that can be tested, can be wrong in a specific way, can produce a generalizable lesson, and can be compared across contexts. Without hypotheses, the system has no mechanism for structured learning.

**Definition.** A testable belief about a consequence, formed from observed events and evidence, that specifies what is expected, under what conditions, within what time horizon, and what would disprove it.

**Inputs.** Events, observations, patterns from prior knowledge, human input.

**Outputs.** Predicted consequences, invalidation conditions, evidence requirements, decision contexts.

**Responsibilities.**
- State what future state is expected
- Specify conditions under which the expectation holds
- Define what evidence would confirm it
- Define what evidence would reject it
- Specify a time horizon for the expected consequence
- Maintain an evolving inventory of supporting and contradicting evidence
- Track confidence as evidence accumulates
- Record its own lifecycle state (see Part VI)

**Lifecycle.** CANDIDATE → FORMULATED → ACTIVE → EVALUATED → CONFIRMED / REJECTED / INCONCLUSIVE → ARCHIVED. (Simplified from 14's 10-state model. TESTING merges into ACTIVE. RETIRED merges into ARCHIVED. See Part V.)

**Owner.** The system's scientific layer. Hypotheses are created by the learning process, not by direct human instruction (though humans may seed initial hypotheses).

**Relationships.**
- Produced by: ResearchProposal (a proposal asks a question; hypotheses answer it)
- Consumed by: Decision (a decision selects a hypothesis to act on)
- Evaluated by: Outcome (outcome confirms or rejects)
- Produces: Knowledge (extracted from evaluated hypothesis)
- Depends on: Evidence (hypothesis is grounded in evidence)
- Related to: other hypotheses (competing, supporting, hierarchical)

**Evidence required for creation.** A hypothesis must have at least one piece of supporting evidence or a clearly stated assumption. A hypothesis with no evidence and no stated assumption is speculation.

**Success condition.** The hypothesis is confirmed and produces generalizable knowledge that improves future decisions.

**Failure condition.** The hypothesis is rejected or declared inconclusive. Even in failure, it produces knowledge if the failure is classified and the lesson is extracted.

---

### Object 2: Evidence

**Purpose.** Evidence is the bridge between observation and judgment. Without explicit evidence tracking, confidence is intuition and learning is impossible. Evidence connects what the system observes to what it believes.

**Definition.** A recorded observation that supports or contradicts a hypothesis, with explicit attribution of source, direction, weight, and reliability.

**Inputs.** Events, outcomes, external data, source reliability history.

**Outputs.** Direction (supports or contradicts), weight (magnitude of support), reliability (trustworthiness of source), recency, independence score.

**Responsibilities.**
- Record which hypothesis it supports or contradicts
- Identify its source with reliability metadata
- State the strength of its support or contradiction
- Track when it was collected (for decay calculations)
- Record its independence from other evidence items
- Support expiration when evidence decays

**Lifecycle.** COLLECTED → ACTIVE → EXPIRED / SUPERSEDED.

**Owner.** The system's operational layer. Evidence is collected in real time as the system observes the world.

**Relationships.**
- Belongs to: Hypothesis (evidence is always relative to a hypothesis)
- Sources: DecisionRecord (evidence is used to make decisions)
- Consumed by: Knowledge extraction (evidence quality affects lesson reliability)
- Depends on: SourceReliability (attribute)

**Evidence required for collection.** Evidence must satisfy: relevance to a hypothesis, specificity (measurable, not vague), source attribution, temporal ordering (before outcome), measurability.

**Success condition.** Evidence accurately predicts whether its hypothesis is confirmed or rejected.

**Failure condition.** Evidence is misleading — it supports a hypothesis that is later rejected or contradicts a hypothesis that is later confirmed.

---

### Object 3: Decision

**Purpose.** The decision is the moment where belief meets action. It is the commitment point — the system chooses a course of action based on a hypothesis and evidence. Every decision produces an outcome, and every outcome produces learning.

**Definition.** A recorded choice to act, wait, monitor, ignore, reduce, or replace, linked to the hypothesis that informed it, with the evidence available at decision time, the confidence in the hypothesis, and the conviction (resource allocation) determined.

**Inputs.** Hypothesis, evidence inventory, confidence estimate, available alternatives, resource constraints.

**Outputs.** Executed action, recorded reasoning, outcome expectation.

**Responsibilities.**
- Record which hypothesis was chosen
- Record which alternatives were considered and why they were rejected
- Record the evidence available at decision time
- Record confidence and conviction at decision time
- Record the expected scenario (what the system predicts will happen)
- Record the actual action taken (or explicit non-action)
- Enable evaluation of decision quality independent of outcome

**Lifecycle.** FORMED → MADE → EXECUTED → EVALUATED.

**Owner.** The system's operational layer. Decisions are made within operational cycles.

**Relationships.**
- Based on: Hypothesis (the chosen hypothesis)
- Informed by: Evidence (evidence available at decision time)
- Produces: Outcome (the result of the decision)
- Evaluated by: DecisionRecord (which compares decision to outcome)
- Depends on: ResearchProposal (the research context)

**Evidence required for decision.** A decision without evidence is a guess. Decisions should have at minimum one piece of supporting evidence or a documented assumption that the decision is based on prior knowledge.

**Success condition.** The decision produces a favorable outcome (profit, learning, or both) and is retrospectively evaluated as a good decision given the information available at the time.

**Failure condition.** The decision produces an unfavorable outcome and is retrospectively evaluated as a poor decision given the information available at the time. (A good decision can produce a bad outcome due to randomness — the decision is not necessarily wrong.)

---

### Object 4: Outcome

**Purpose.** The outcome is the feedback signal. It is the only connection between the system's beliefs and reality. Every outcome either confirms or contradicts the hypothesis that produced it, and every outcome is an opportunity to learn.

**Definition.** The observed result of an executed decision, recorded objectively before interpretation.

**Inputs.** Reality (market prices, engagement metrics, business results).

**Outputs.** Raw result data (profit/loss, win/loss, quantitative values), timing information, unexpected events.

**Responsibilities.**
- Record what actually happened
- Record when it happened (relative to hypothesis time horizon)
- Record unexpected events that affected the outcome
- Remain objective — outcome data precedes interpretation

**Lifecycle.** PENDING → OBSERVED → RECORDED.

**Owner.** The system's operational layer. Outcomes are observed and recorded by the execution infrastructure.

**Relationships.**
- Produced by: Decision (executed decision produces outcome)
- Consumed by: DecisionRecord (outcome is compared to hypothesis)
- Evaluates: Hypothesis (outcome confirms or rejects)
- Depends on: Time (outcomes are observed after sufficient time)

**Evidence required for recording.** The outcome must be measurable. If an outcome cannot be measured, the hypothesis cannot be evaluated. Some hypotheses produce ambiguous outcomes — this is itself a recorded result.

**Success condition.** The outcome clearly confirms or rejects the hypothesis that produced it.

**Failure condition.** The outcome is ambiguous, confounded by external events, or cannot be attributed to the hypothesis. In this case, the hypothesis is INCONCLUSIVE.

---

### Object 5: Knowledge

**Purpose.** Knowledge is the output of learning. It is what the system retains after a hypothesis is tested and evaluated. Knowledge is the mechanism by which individual outcomes improve future decisions. Without knowledge extraction, every cycle starts from zero.

**Definition.** A generalizable lesson extracted from a tested hypothesis, stated as a testable claim about the relationship between conditions, actions, and outcomes.

**Inputs.** Evaluated hypothesis (confirmed or rejected), outcome, error classification, reflection.

**Outputs.** A statement of the form: "Under conditions X, hypothesis type Y produces outcome Z with calibrated confidence C."

**Responsibilities.**
- State a generalizable relationship (not specific to a single event)
- Record the evidence that supports it (which hypotheses produced it)
- Record the conditions under which it applies
- Record the conditions under which it may not apply
- Remain provisional — knowledge is subject to revision
- Be actionable — knowledge should inform future hypothesis formation

**Lifecycle.** EXTRACTED → PROVISIONAL → VALIDATED / REVISED / INVALIDATED → ARCHIVED.

**Owner.** The system's learning layer. Knowledge is extracted during the reflection stage of each DecisionRecord.

**Relationships.**
- Produced by: DecisionRecord (reflection extracts knowledge from hypothesis-outcome comparison)
- Consumed by: Criterion (knowledge updates accumulated judgment)
- Consumed by: Hypothesis (knowledge informs new hypothesis formation)
- Related to: other Knowledge (supporting, contradicting, refining)
- Depends on: ErrorType (error classification enriches knowledge)

**Evidence required for extraction.** A single hypothesis outcome produces provisional knowledge. Multiple confirmations of similar hypotheses produce validated knowledge. Cross-domain replication produces robust knowledge.

**Success condition.** Knowledge improves future hypothesis quality, decision quality, or calibration.

**Failure condition.** Knowledge is misleading — it causes the system to make worse decisions when applied. Knowledge is always provisional and subject to falsification.

---

### Object 6: ErrorType

**Purpose.** ErrorType is the taxonomy that enables the system to learn from failure. Without error classification, every failure is a unique event. With error classification, the system can track which types of errors it makes most often and target improvements.

**Definition.** A category of decision failure, defined by the component of the decision process that was incorrect.

**Responsibilities.**
- Provide a stable taxonomy of failure categories
- Enable aggregation of failures by type
- Support trend analysis (is error type frequency declining?)
- Support root cause analysis (what type of hypothesis tends to produce this error?)

**Lifecycle.** DEFINED → APPLIED → REFINED (taxonomy evolves as the system encounters new error types).

**Owner.** The system's scientific layer. The taxonomy is defined by the research protocol and refined through experience.

**Relationships.**
- Applied to: DecisionRecord (each evaluated hypothesis receives error classification)
- Consumed by: Knowledge (error type enriches knowledge extraction)
- Consumed by: CriterionSnapshot (error type frequency is a criterion metric)

**ErrorType Taxonomy (initial):**
- WRONG_EVENT_INTERPRETATION — the triggering event was misunderstood
- WRONG_CORRELATION — the relationship between events was spurious
- WRONG_CONSEQUENCE — the consequence did not emerge despite correct events
- CORRECT_CONSEQUENCE_WRONG_TIMING — consequence happened outside predicted window
- CORRECT_HYPOTHESIS_POOR_EXECUTION — hypothesis correct, action poorly calibrated
- EXTERNAL_SHOCK — an unpredictable event intervened
- CORRECT_OUTCOME — no error occurred (confirmed hypothesis)
- INCONCLUSIVE — outcome could not be clearly evaluated

**Success condition.** The taxonomy captures all significant failure modes without excessive granularity.

**Failure condition.** The taxonomy is too coarse (all failures classified as "wrong") or too fine (every failure is a unique type, preventing aggregation).

---

### Object 7: ResearchProposal

**Purpose.** ResearchProposal groups experiments under a common scientific question. It prevents the system from testing hypotheses without a clear research purpose. Every experiment must belong to a proposal; every proposal must address a gap in criterion.

**Definition.** A documented plan to investigate a specific gap in the system's criterion, including the research question, the hypothesis to be tested, the expected impact, and the success and failure criteria.

**Inputs.** Identified gap in criterion, prior knowledge, open questions from previous cycles.

**Outputs.** Experiments, tested hypotheses, validated or invalidated claims, knowledge.

**Responsibilities.**
- State what gap in criterion is being addressed
- Frame the research question
- Propose one or more hypotheses to test
- Define success criteria (what would confirm the hypothesis)
- Define failure criteria (what would reject it)
- Specify the expected impact on criterion
- Track progress (how many experiments completed, what was learned)
- Generate new proposals from findings

**Lifecycle.** DRAFT → ACTIVE → EVALUATING → CONFIRMED / REJECTED / INCONCLUSIVE → ARCHIVED.

**Owner.** The system's research layer. ResearchProposals may be generated by the system (from detected gaps) or by human researchers.

**Relationships.**
- Produces: DecisionRecords (through the experiments it defines)
- Consumed by: CriterionSnapshot (proposal outcomes feed criterion metrics)
- Depends on: Knowledge (proposals are informed by existing knowledge)
- Modified by: Outcome (proposals may be refined based on early results)

**Evidence required for creation.** A proposal must identify a specific gap in criterion. Proposals without a clear gap are speculative and should be flagged as exploratory.

**Success condition.** The proposal produces validated knowledge that fills the identified criterion gap.

**Failure condition.** The proposal produces no knowledge (all experiments inconclusive) or produces misleading knowledge (confirmed hypothesis later invalidated).

---

### Object 8: CriterionSnapshot

**Purpose.** CriterionSnapshot is the measurement instrument. It operationalizes the abstract concept of "criterion" into measurable dimensions that can be tracked over time. Without CriterionSnapshot, criterion is a philosophical concept. With it, criterion is a scientific variable.

**Definition.** A periodic measurement of the system's accumulated judgment, computed from all completed DecisionRecords in the measurement window, reported across multiple independent dimensions.

**Inputs.** All completed DecisionRecords in the measurement period.

**Outputs.** Multi-dimensional criterion profile, trend indicators, calibration reports.

**Responsibilities.**
- Compute all criterion dimensions for the measurement period
- Report trends compared to previous snapshots
- Identify improvements and degradations
- Flag anomalies (unexpected changes in any dimension)
- Preserve historical snapshots for longitudinal analysis
- Provide the evidence base for autonomy level assessment

**Lifecycle.** GENERATED → REPORTED → ARCHIVED. Generated on a fixed schedule (e.g., weekly, monthly, quarterly).

**Owner.** The system's learning layer. Computation may be triggered by the system or by human review.

**Relationships.**
- Computed from: DecisionRecords (aggregate of all completed cycles)
- Evaluates: Knowledge (knowledge yield is a criterion dimension)
- Informs: ResearchProposal (criterion gaps trigger new proposals)
- Depends on: Time (requires sufficient sample size for statistical validity)

**Dimensions measured (initial set):**
- Hypothesis Quality (precision, falsifiability, evidence grounding — trended over time)
- Evidence Quality (relevance, independence, source reliability — trended)
- Calibration (confidence vs. accuracy — measured per confidence bucket)
- Error Recurrence Rate (proportion of hypotheses repeating previous error types)
- Knowledge Yield (average lessons per hypothesis, knowledge applicability rate)
- Learning Velocity (time from outcome to knowledge extraction)
- Decision Utility (retrospective evaluation of decision quality vs. outcome)

**Evidence required for validity.** A CriterionSnapshot requires a minimum sample size. With fewer than 30 DecisionRecords in the window, measurements should be flagged as preliminary.

**Success condition.** CriterionSnapshot shows positive trends across multiple dimensions over successive measurement periods.

**Failure condition.** CriterionSnapshot shows degradation or stagnation across all dimensions, indicating the system is not learning.

---

### Object 9: DecisionRecord (Aggregate)

**Purpose.** DecisionRecord is the primary aggregate of the system. It bundles a complete operational cycle — hypothesis, evidence, decision, outcome, reflection, and knowledge — into a single immutable record. DecisionRecord is the unit of analysis for all criterion measurement.

**Definition.** The complete scientific record of one operational cycle, from need identification through knowledge extraction, stored as an immutable temporal entity.

**Contains (embedded, not independent references):**
- Hypothesis (the belief being tested)
- Evidence collection (evidence available at decision time + evidence accumulated during testing)
- Decision (the choice made, with confidence, conviction, and rationale)
- Outcome (what actually happened, recorded objectively)
- Reflection (comparison of outcome to hypothesis, error classification)
- Knowledge extracted (lessons learned from this cycle)

**Does NOT contain (references, not embeddings):**
- Link to ResearchProposal (many DecisionRecords may belong to one proposal)
- Link to prior Knowledge (knowledge that informed the hypothesis)

**Responsibilities.**
- Preserve a complete, immutable record of one operational cycle
- Enable retrospective evaluation of decision quality independent of outcome
- Enable trend analysis across cycles
- Provide the data for all criterion measurements
- Support search and query by any field

**Lifecycle.** OPEN → COMPLETED → ANALYZED → ARCHIVED.

**Owner.** The system's operational layer, with immutability enforced by the scientific memory.

**Relationships.**
- Belongs to: ResearchProposal (each record is part of a research program)
- Consumed by: CriterionSnapshot (aggregate analysis)
- Consumed by: Knowledge (knowledge is extracted from records)
- Depends on: All other objects (it is the aggregate of everything)

**Evidence required for completion.** A DecisionRecord is complete when: outcome has been observed AND reflection has been recorded AND knowledge has been extracted (even if the knowledge is "this cycle produced no generalizable lesson").

**Success condition.** The DecisionRecord contributes to improved criterion, either through confirmed knowledge or through classified failure that reduces future error recurrence.

**Failure condition.** The DecisionRecord is incomplete (missing reflection or knowledge extraction). An incomplete record is a wasted learning opportunity.

---

## PART IV: Object Relationships

### 4.1 Conceptual Graph

```
                        ┌──────────────────┐
                        │ ResearchProposal  │
                        │ (why we are       │
                        │  investigating)   │
                        └────────┬─────────┘
                                 │ generates
                                 ▼
               ┌─────────────────────────────────┐
               │       DecisionRecord × N         │
               │  (the complete scientific record │
               │   of one operational cycle)      │
               │                                  │
               │  ┌──────────────────────────┐    │
               │  │   Hypothesis             │    │
               │  │   (belief being tested)  │    │
               │  └───────────┬──────────────┘    │
               │              │ collects           │
               │  ┌───────────▼──────────────┐    │
               │  │   Evidence (1..N)        │    │
               │  │   (supports /            │    │
               │  │    contradicts)          │    │
               │  └───────────┬──────────────┘    │
               │              │ informs            │
               │  ┌───────────▼──────────────┐    │
               │  │   Decision               │    │
               │  │   (choice made,          │    │
               │  │    with confidence,      │    │
               │  │    conviction,           │    │
               │  │    rationale)            │    │
               │  └───────────┬──────────────┘    │
               │              │ produces           │
               │  ┌───────────▼──────────────┐    │
               │  │   Outcome                │    │
               │  │   (what happened)        │    │
               │  └───────────┬──────────────┘    │
               │              │ triggers           │
               │  ┌───────────▼──────────────┐    │
               │  │   Reflection             │    │
               │  │   (outcome vs.           │    │
               │  │    hypothesis,           │    │
               │  │    error classification) │    │
               │  └───────────┬──────────────┘    │
               │              │ extracts           │
               │  ┌───────────▼──────────────┐    │
               │  │   Knowledge              │    │
               │  │   (lesson learned)       │    │
               │  └───────────┬──────────────┘    │
               └──────────────┼───────────────────┘
                              │ feeds into
                              ▼
               ┌──────────────────────────────────┐
               │        CriterionSnapshot          │
               │  (periodic measurement of         │
               │   all criterion dimensions,       │
               │   aggregated across all           │
               │   DecisionRecords in the period)  │
               └────────────────┬─────────────────┘
                                │ identifies gaps
                                ▼
               ┌──────────────────────────────────┐
               │        ResearchProposal           │
               │  (new proposal addressing         │
               │   identified criterion gap)       │
               └──────────────────────────────────┘
```

### 4.2 Feedback Loops

**Loop 1 — Learning Loop:**
DecisionRecord → Knowledge → Future Hypothesis Formation → DecisionRecord

Knowledge extracted from one cycle informs the hypotheses formed in future cycles. This is the primary learning mechanism. Over many cycles, knowledge accumulates and hypothesis quality improves.

**Loop 2 — Calibration Loop:**
DecisionRecord → CriterionSnapshot → Confidence Adjustment → DecisionRecord

CriterionSnapshot detects calibration drift (confidence diverging from accuracy). Confidence adjustment corrects the drift. Future decisions are better calibrated.

**Loop 3 — Error Reduction Loop:**
DecisionRecord → ErrorType → ErrorType Frequency → Hypothesis Formation → DecisionRecord

Repeated errors of the same type trigger investigation. The system forms hypotheses about why this error type persists. Lessons from these investigations reduce future error recurrence.

**Loop 4 — Research Direction Loop:**
CriterionSnapshot → ResearchProposal → DecisionRecords → CriterionSnapshot

CriterionSnapshot identifies gaps or weaknesses. ResearchProposals are generated to address these gaps. Experiments produce evidence. Future snapshots measure whether the gap was closed.

### 4.3 Object Creation Map

| Creator | Creates |
|---------|---------|
| ResearchProposal | DecisionRecord (by defining what to test) |
| DecisionRecord | Knowledge (extracted during reflection) |
| DecisionRecord | Evidence (collected during the cycle) |
| DecisionRecord | ErrorType assignment (during reflection) |
| CriterionSnapshot | ResearchProposal (by identifying gaps) |
| Knowledge | Hypothesis (by informing new hypothesis formation) |
| Evidence collection | CriterionSnapshot input (evidence quality is measured) |

### 4.4 Object Consumption Map

| Consumer | Consumes |
|----------|----------|
| DecisionRecord | ResearchProposal (belongs to it) |
| DecisionRecord | Evidence (collects it) |
| DecisionRecord | Hypothesis (tests it) |
| DecisionRecord | Outcome (records it) |
| CriterionSnapshot | DecisionRecord (aggregates it) |
| ResearchProposal | CriterionSnapshot (gaps inform proposals) |
| Hypothesis (future) | Knowledge, Evidence (informed by them) |

---

## PART V: The Minimal Scientific Core

### 5.1 Aggressive Reduction Challenge

The initial audit identified 35 candidate concepts. After evaluation, 9 objects remain (8 independent + 1 aggregate).

This is a 74% reduction.

However, the task requires challenging the model further and attempting at least 25% reduction from the proposed set. From 9 objects, 25% reduction means removing 2–3 more.

**Challenge 1: Can DecisionRecord be eliminated?**

DecisionRecord is an aggregate. In a storage system, DecisionRecord could be a query that joins Hypothesis, Evidence, Decision, Outcome, Reflection, and Knowledge records by a shared cycle ID. However, this would require each sub-object to exist independently, increasing the total object count from 9 to 13+ (Hypothesis, Evidence, Decision, Outcome, Knowledge, ErrorType would already exist; Reflection and the linking mechanism would need their own structures).

**Verdict: DecisionRecord survives.** It is the aggregate that reduces object count. Without it, the system would need more objects, not fewer.

**Challenge 2: Can ResearchProposal be eliminated?**

A ResearchProposal could be a DecisionRecord with a special type — "this is a proposal about what to investigate." Proposals would not have outcomes (they are not tested) and would not produce knowledge directly (they produce experiments that produce knowledge).

**Verdict: ResearchProposal survives but could be simplified.** It is type-distinct from DecisionRecord because it precedes experiments and has a different lifecycle. However, it could be represented as a lightweight configuration rather than a full object. Mark as "candidate for simplification in implementation."

**Challenge 3: Can ErrorType be eliminated?**

ErrorType could be an attribute of Outcome (or Reflection within DecisionRecord) rather than an independent object. It does not have its own lifecycle or relationships — it is a taxonomy referenced by DecisionRecords.

**Verdict: ErrorType demoted to attribute.** ErrorType is a value type (enumeration), not an independent object with identity and lifecycle. It should be an attribute within DecisionRecord.

**Challenge 4: Can CriterionSnapshot be eliminated?**

CriterionSnapshot could be a computed report generated on demand from DecisionRecords, rather than a stored object. It does not need its own lifecycle — it is always derivable from the underlying data.

**Verdict: CriterionSnapshot demoted to computed view.** It is a query result, not a stored object. The measurement logic is important, but the measurement output is derived, not stored as a first-class entity.

**Challenge 5: Can Evidence be eliminated?**

Evidence is always relative to a hypothesis. Could it be an attribute of the Hypothesis — a collection of supporting and contradicting observations?

**Verdict: Evidence survives.** Evidence has its own lifecycle (collection, weighting, decay, expiration). It is created, tracked, and retired independently of the hypothesis it supports. Making it an attribute of Hypothesis would prevent independent evidence management.

### 5.2 Final Minimal Core (After Second Reduction)

**INDEPENDENT OBJECTS (6):**

| # | Object | Status | Rationale |
|---|--------|--------|-----------|
| 1 | **Hypothesis** | Core | Central unit of learning. Independent lifecycle. |
| 2 | **Evidence** | Core | Independent lifecycle. Cannot be attribute of Hypothesis (evidence expires independently). |
| 3 | **Decision** | Core | Independent object with choice, rationale, alternatives. |
| 4 | **Outcome** | Core | Objective record of what happened. Independent of interpretation. |
| 5 | **Knowledge** | Core | Generalizable lesson. Has lifecycle (extracted → validated → revised → invalidated). |
| 6 | **ResearchProposal** | Core | Groups experiments under research question. Has lifecycle. |

**AGGREGATE OBJECT (1):**

| # | Object | Contains |
|---|--------|----------|
| 7 | **DecisionRecord** | Hypothesis + Evidence + Decision + Outcome + Reflection + ErrorType + Knowledge produced |

**REMOVED (from 9-object model):**

| Object | New Disposition | Rationale |
|--------|----------------|-----------|
| ErrorType | Attribute of DecisionRecord | Taxonomy, not independent entity. No lifecycle, no identity. |
| CriterionSnapshot | Computed view | Derivable from DecisionRecords. Not independently stored. |

**Total: 7 objects (6 independent + 1 aggregate)**

This is a 25% reduction from the 9-object model and a 80% reduction from the original 35 candidate concepts.

### 5.3 Objects Explicitly Not Included

The following concepts were evaluated and excluded from the core. Each is documented here to prevent future re-addition without justification:

- **Scenario** — Method on Hypothesis. Generates expected observations.
- **Conviction** — Numeric attribute of Decision. Position size, resource allocation.
- **Pattern** — Knowledge with lower confidence. Same structure, different name.
- **Memory** — Infrastructure. The three memories (scientific, operational, semantic) are storage mechanisms, not domain objects.
- **Trust** — Undefined. Not operationalized in any document.
- **Autonomy** — Policy configuration. Not a runtime object.
- **Opportunity** — Hypothesis with high confidence. Threshold, not object.
- **Correlation, Cluster, Consequence, Event** — Inputs or derived observations. Not learning objects.
- **Wisdom** — Cross-domain Criterion. Criterion is sufficient.
- **Signal, Noise, Information** — Properties of data relative to hypotheses. Not stored objects.
- **Action** — Stage within Decision lifecycle. Not independent.
- **Calibration, Confidence** — Attributes of DecisionRecord (confidence at decision time) and CriterionSnapshot (calibration as metric).

---

## PART VI: Object Lifecycles

### 6.1 Hypothesis Lifecycle

```
                      ┌──────────────┐
                      │  CANDIDATE   │  An idea that may become a hypothesis
                      └──────┬───────┘
                             │ structured and evidence-grounded
                      ┌──────▼───────┐
                      │  FORMULATED  │  Complete with prediction, conditions,
                      └──────┬───────┘  time horizon, invalidation conditions
                             │ committed to tracking
                      ┌──────▼───────┐
                      │    ACTIVE    │  Being tracked. Evidence accumulating.
                      └──────┬───────┘  May be acted upon.
                             │ outcome observed
                      ┌──────▼───────┐
                      │  EVALUATED   │  Outcome compared to prediction.
                      └──────┬───────┘  Error classified.
                             │
               ┌─────────────┼─────────────┐
               │             │             │
         ┌─────▼─────┐ ┌────▼────┐ ┌──────▼──────┐
         │ CONFIRMED │ │REJECTED │ │INCONCLUSIVE │
         └─────┬─────┘ └────┬────┘ └──────┬──────┘
               │            │             │
               └────────────┼─────────────┘
                            │
                      ┌─────▼──────┐
                      │  ARCHIVED  │  Preserved for meta-analysis
                      └────────────┘
```

**Transitions:**
- CANDIDATE → FORMULATED: An idea is structured into a testable hypothesis with all required attributes.
- FORMULATED → ACTIVE: The system commits to tracking the hypothesis and collecting evidence.
- ACTIVE → EVALUATED: An outcome is observed that confirms, rejects, or leaves inconclusive the hypothesis.
- EVALUATED → CONFIRMED/REJECTED/INCONCLUSIVE: The verdict is assigned.
- All terminal states → ARCHIVED: The hypothesis lifecycle is complete. The record is preserved.

**How it contributes to Criterion:** Each completed hypothesis lifecycle produces knowledge. Accumulated knowledge over many hypotheses improves the system's judgment.

### 6.2 Evidence Lifecycle

```
                     ┌─────────────┐
                     │  COLLECTED  │  Evidence identified and linked to a hypothesis
                     └──────┬──────┘
                            │ added to hypothesis
                     ┌──────▼──────┐
                     │   ACTIVE    │  Actively contributing to hypothesis evaluation
                     └──────┬──────┘
                            │
               ┌────────────┼────────────┐
               │            │            │
          ┌────▼────┐ ┌─────▼─────┐ ┌────▼─────┐
          │ EXPIRED │ │SUPERSEDED │ │ ARCHIVED │
          └─────────┘ └───────────┘ └──────────┘
```

**Transitions:**
- COLLECTED → ACTIVE: Evidence is added to a hypothesis's evidence inventory.
- ACTIVE → EXPIRED: Evidence passes its useful lifetime (domain-dependent decay).
- ACTIVE → SUPERSEDED: Better evidence replaces this piece.
- Any state → ARCHIVED: Preserved for audit but no longer active.

**How it contributes to Criterion:** Evidence quality improves as the system learns which sources are reliable, which evidence types are predictive, and how evidence decays.

### 6.3 Decision Lifecycle

```
                     ┌─────────────┐
                     │   FORMED    │  Decision is initiated based on hypothesis and evidence
                     └──────┬──────┘
                            │ committed
                     ┌──────▼──────┐
                     │    MADE     │  Choice recorded with rationale, confidence, conviction
                     └──────┬──────┘
                            │ executed
                     ┌──────▼──────┐
                     │  EXECUTED   │  Action carried out (or explicit non-action recorded)
                     └──────┬──────┘
                            │ outcome observed
                     ┌──────▼──────┐
                     │  EVALUATED  │  Decision quality evaluated independent of outcome
                     └─────────────┘
```

**How it contributes to Criterion:** Decision quality evaluation (independent of outcome) trains the system to make better choices given available evidence.

### 6.4 Knowledge Lifecycle

```
                     ┌──────────────┐
                     │  EXTRACTED   │  Lesson extracted from a DecisionRecord
                     └──────┬───────┘
                            │ published
                     ┌──────▼───────┐
                     │ PROVISIONAL  │  Available for use but not yet validated across multiple cases
                     └──────┬───────┘
                            │
               ┌────────────┼────────────┐
               │            │            │
          ┌────▼────┐ ┌─────▼─────┐ ┌────▼──────┐
          │VALIDATED│ │  REVISED  │ │INVALIDATED│
          └────┬────┘ └─────┬─────┘ └────┬──────┘
               │            │            │
               └────────────┼────────────┘
                            │
                     ┌──────▼──────┐
                     │  ARCHIVED   │  Preserved for historical analysis
                     └─────────────┘
```

**How it contributes to Criterion:** Knowledge is the direct input to criterion. Validated knowledge becomes part of the system's accumulated judgment.

### 6.5 ResearchProposal Lifecycle

```
                     ┌──────────────┐
                     │    DRAFT     │  Proposal being formulated
                     └──────┬───────┘
                            │ approved
                     ┌──────▼───────┐
                     │    ACTIVE    │  Experiments being conducted
                     └──────┬───────┘
                            │ sufficient evidence accumulated
                     ┌──────▼───────┐
                     │  EVALUATING  │  Results being analyzed
                     └──────┬───────┘
                            │
               ┌────────────┼────────────┐
               │            │            │
          ┌────▼────┐ ┌─────▼─────┐ ┌────▼──────┐
          │CONFIRMED│ │ REJECTED  │ │INCONCLUSIVE│
          └────┬────┘ └─────┬─────┘ └────┬──────┘
               │            │            │
               └────────────┼────────────┘
                            │
                     ┌──────▼──────┐
                     │  ARCHIVED   │
                     └─────────────┘
```

**How it contributes to Criterion:** ResearchProposals ensure that experiments are purposeful. They prevent the system from testing hypotheses without a clear research question.

### 6.6 DecisionRecord Lifecycle

```
                     ┌──────────────┐
                     │    OPEN      │  Operational cycle in progress
                     └──────┬───────┘
                            │ cycle complete
                     ┌──────▼───────┐
                     │  COMPLETED   │  Outcome observed, reflection pending
                     └──────┬───────┘
                            │ reflection recorded
                     ┌──────▼───────┐
                     │  ANALYZED    │  Error classified, knowledge extracted
                     └──────┬───────┘
                            │ preserved
                     ┌──────▼───────┐
                     │  ARCHIVED    │  Immutable record in scientific memory
                     └──────────────┘
```

**How it contributes to Criterion:** DecisionRecords are the data from which CriterionSnapshot metrics are computed. The quality and completeness of DecisionRecords directly determines the reliability of criterion measurement.

---

## PART VII: Implementation Readiness

### 7.1 Layer Allocation

The objects naturally separate into four layers:

**Scientific Layer (WHAT we are learning about):**
- ResearchProposal — defines the research agenda
- Hypothesis — the unit of learning
- Evidence — what supports or contradicts beliefs
- ErrorType — how we classify failure
- Knowledge — what we have learned

**Operational Layer (WHAT the system does):**
- Decision — choices made
- Outcome — results observed
- DecisionRecord — the complete record of one cycle

**Learning Layer (HOW we improve):**
- Knowledge lifecycle management
- CriterionSnapshot computation (derived, not stored)
- Cross-cycle pattern detection
- Calibration tracking

**Research Layer (WHY we investigate):**
- ResearchProposal generation
- Experiment design
- Result analysis
- New question formation

### 7.2 Why This Separation Improves Maintainability

**Independent evolution.** The scientific layer (Hypothesis, Evidence, Knowledge) changes only when the project's understanding of learning changes. The operational layer (Decision, Outcome, DecisionRecord) changes when the execution environment changes. The research layer changes when the research agenda changes. These evolve at different rates and for different reasons.

**Replaceable infrastructure.** The underlying storage (memories) can be replaced without changing the object model. Whether the system uses SQL, document stores, or event logs, the objects remain the same.

**Testable in isolation.** Each object can be tested independently. Hypothesis lifecycle can be unit-tested without a trading environment. Decision quality evaluation can be tested with synthetic data. Knowledge extraction logic can be tested with known hypothesis-outcome pairs.

**Clear boundaries for implementation.** Each object has defined responsibilities, inputs, outputs, and relationships. Implementation teams (or automated code generation) can work on different objects independently.

### 7.3 What Must Exist Before Implementation

1. **Object specifications.** Each object's attributes, valid states, and state transitions must be specified precisely enough for schema design. The definitions in Part III provide the foundation; implementation will require field-level specifications.

2. **Relationship rules.** Cardinality (one-to-many, many-to-many), ownership (who creates what), and referential integrity rules must be specified.

3. **Lifecycle implementations.** Each state machine must be implemented with guards (what conditions allow a transition), actions (what happens during a transition), and events (what triggers a transition).

4. **Integration with existing MVP.** The existing event-to-action pipeline must be mapped onto the object model. Events become evidence. Agent opinions become hypotheses (or contributions to hypotheses). Trades become DecisionRecords.

5. **Memory architecture.** The three memories (scientific, operational, semantic) must be designed as storage layers. The object model defines what is stored; the memory architecture defines how.

### 7.4 How the Object Model Prepares Implementation

The object model transforms philosophical questions into engineering questions:

- Instead of "how do we track hypotheses?" → "implement the Hypothesis lifecycle state machine"
- Instead of "how do we learn from outcomes?" → "implement Knowledge extraction from DecisionRecord"
- Instead of "how do we measure criterion?" → "implement CriterionSnapshot computation from DecisionRecords"
- Instead of "how do we ensure scientific rigor?" → "implement ResearchProposal as a required parent for DecisionRecords"
- Instead of "how do we prevent confirmation bias?" → "implement competing hypothesis support within ResearchProposal and DecisionRecord"

Every implementation task traces to a specific object with a defined responsibility. This prevents the common failure mode of building infrastructure without knowing what concepts it serves.

---

## PART VIII: Self-Review

### S-01: Objects That May Be Unnecessary

**Decision (Object 3) vs. DecisionRecord (Object 7):** Decision is embedded within DecisionRecord. Could the system operate with only DecisionRecord, extracting the decision attributes from within?

- Answer: For minimal implementation, yes. Decision exists as a conceptual object but may not need independent storage. The Decision attributes (choice, rationale, confidence, conviction) can be fields within DecisionRecord. However, if the system needs to query decisions independently (e.g., "show all decisions where confidence > 0.8 and execution price deviated from expected"), Decision may deserve its own index.

**Verdict:** Decision is a candidate for merging into DecisionRecord at the storage level while remaining conceptually distinct.

### S-02: Objects That Overlap

**Hypothesis and ResearchProposal overlap.** A ResearchProposal proposes a hypothesis to test. The hypothesis within a DecisionRecord is the specific instance being tested. There is a relationship: ResearchProposal.Hypothesis → DecisionRecord.Hypothesis (the hypothesis in the record is derived from the proposal).

- This is not overlap — it is a class-instance relationship. The proposal defines what to test; the DecisionRecord records the test of that hypothesis in specific conditions.

### S-03: Objects That Are Too Abstract

**Evidence** is the most abstract object. In implementation, evidence may take many forms: price movements, news headlines, macroeconomic indicators, social signals, agent opinions. The object model defines evidence at the conceptual level; implementation will need an evidence type hierarchy or a flexible evidence schema.

- This abstraction is appropriate for the conceptual model. Implementation should support polymorphic evidence types without changing the core object relationships.

### S-04: Implementation Details Disguised as Concepts

**ResearchProposal** borders on being an implementation detail. In a mature system, research proposals may be generated automatically from criterion gaps. In the early system, they may be human-written documents. The object model should not dictate the generation mechanism.

- Keep ResearchProposal as a conceptual object. The generation mechanism is an implementation detail.

### S-05: Missing Objects

**What about Criterion itself?** Criterion is the central concept but is not an object in this model. It is an emergent property — the accumulated state of the system's judgment as measured by CriterionSnapshot. This is correct: criterion is not an object that can be built or stored. It is a measurement derived from the system's behavior.

**What about the Null Hypothesis?** The concept of a null hypothesis (17 Part V) is important but does not require an independent object. The null hypothesis is the baseline that an experimental hypothesis must beat. It can be represented as a configuration parameter within ResearchProposal or Experiment design.

**What about Reflection?** Reflection is a stage in the DecisionRecord lifecycle, not an independent object. It is the analysis that produces ErrorType assignment and Knowledge extraction. This is correctly modeled as a stage within DecisionRecord.

**What about SourceReliability?** SourceReliability is an attribute of Evidence. In a mature system, source reliability may deserve its own tracking object (a source registry with reliability scores that are updated over time). For the minimal core, it is an attribute. Implementation may promote it to an object if reliability tracking proves essential.

### S-06: Future Risks

**Object proliferation.** The 7-object minimal core is aggressively reduced. As the system matures, there will be pressure to add objects: Experiment, SourceReliability, ContextProfile, CriterionLevel, AutonomyLevel, Opportunity. Each addition must be justified against the minimal core. The default answer should be no.

**Knowledge granularity.** Knowledge is defined as a generalizable lesson. In practice, lessons may range from trivial ("this specific event happened") to profound ("this class of hypotheses fails in this regime"). The object model does not constrain knowledge granularity. Implementation will need quality controls.

**ResearchProposal lifecycle coupling.** If every DecisionRecord must belong to a ResearchProposal, the system cannot make operational decisions without a research context. Early implementation should allow a "General Research" proposal for exploratory cycles that do not belong to a specific investigation.

**Evidence decay.** Evidence lifecycle includes expiration, but the object model does not specify how decay is computed. This must be defined before implementation. Decay may vary by: evidence type, domain velocity, source reliability, and subsequent contradictory evidence.

---

## Final Declaration

The implementation of O.M.A.-C.O.R.E. should never begin with code.

It should begin with a precise understanding of what truly exists inside its universe.

Thirty-five concepts were considered. Seven objects survived.

A hypothesis is a testable belief. Evidence supports or contradicts it. A decision commits to action. An outcome records what happened. Knowledge extracts the lesson. A research proposal frames the inquiry. A decision record binds them all into one immutable cycle.

Everything else is attribute, derivative, or infrastructure.

The object model is not the implementation. It is the contract between philosophy and engineering. It ensures that what the philosophy describes is what the implementation builds.

Every object must earn its existence. Every attribute must prove its value. Every relationship must justify its complexity.

The implementation that follows this model will be leaner, more coherent, and more maintainable than one built from concepts alone.

Evidence has the final word.

---

*End of 02_SCIENTIFIC_OBJECT_MODEL.md — Version 1.0 — June 2026*
