# Criterion Readiness Audit

## A Scientific Assessment of O.M.A.-C.O.R.E.'s Current Capability to Develop Demonstrable Criterion

*Version 1.0 — June 2026*

---

## 1. Executive Summary

O.M.A.-C.O.R.E. has a sound philosophical foundation. The first-principles documents (Manifesto, Theory, Laws, Constitution, Glossary, Criterion, Discoveries, Assumptions) are internally consistent, evidence-aware, and falsifiable. They correctly identify criterion as an emergent capability, not a component to be built.

The MVP implementation is architecturally honest — it does not claim learning it does not have. The pipeline (WorldMonitorV2 → Agents → Council → Guards → PaperTrading → PerformanceMemory) correctly implements the event-to-action chain.

However, the implementation has not yet crossed the threshold from **signal processing** to **learning intelligence**.

### Current Verdict: PARTIALLY

The system can:
- ✅ Detect events from multiple sources
- ✅ Generate trading signals through agent council voting
- ✅ Execute trades safely through guard layers
- ✅ Record outcomes with agent-level attribution
- ✅ Maintain primitive feedback loops (Council weights, DirectionController)
- ✅ Run continuously with zero runtime errors across hundreds of cycles

The system cannot:
- ❌ Form explicit, testable hypotheses
- ❌ Track evidence for or against any belief
- ❌ Link outcomes back to the hypotheses that produced them
- ❌ Classify errors by decision type (only by runtime exception)
- ❌ Extract generalizable knowledge from outcomes
- ❌ Measure its own criterion development
- ❌ Improve its perceptual or judgmental components through feedback

This document provides the detailed assessment that justifies this verdict and identifies the specific gaps that must be closed.

---

## 2. Current Maturity

### 2.1 Criterion Level Assessment

Using the framework from the Criterion document:

| Level | Description | Current Status | Evidence |
|-------|-------------|---------------|----------|
| **Level 0 — Reactive** | Responds to events as they arrive. No memory. No learning. | ✅ Surpassed | System has memory and basic feedback |
| **Level 1 — Pattern Recognition** | Detects recurring patterns but cannot form hypotheses about them. | ✅ Achieved | Agents detect patterns (RSI, EMA crossovers, keyword matches) |
| **Level 2 — Contextual** | Adjusts behavior based on regime. | 🟡 Partial | DirectionController adapts to direction win rates. CapitalGuard adapts to drawdown regime. No explicit market context model. |
| **Level 3 — Hypothesis-Driven** | Forms explicit hypotheses, tracks evidence, updates as information arrives. | ❌ **Not achieved** | No hypothesis object, no evidence tracking, no hypothesis-to-outcome linking |
| **Level 4 — Self-Correcting** | Detects weakening hypotheses before outcome confirms error. | ❌ Not achieved | Requires Level 3 as prerequisite |
| **Level 5 — Operational Criterion** | Consistent calibrated judgment across conditions. | ❌ Not achieved | Requires Levels 3 and 4 as prerequisites |
| **Level 6 — Strategic Criterion** | Self-directed improvement. Decides what to learn next. | ❌ Not achieved | Requires all lower levels as prerequisites |

**Maturity Assessment:** The system is between Level 1 and Level 2. It has moved beyond pure reactivity but has not yet reached hypothesis-driven intelligence.

### 2.2 Component Maturity Matrix

| Component | Signal Processing | Outcome Recording | Adaptive Feedback | Hypothesis Lifecycle |
|-----------|-----------------|-------------------|-------------------|---------------------|
| MarketAgent | ✅ Full | ❌ None | ❌ None | ❌ None |
| RiskAgent | ✅ Full | ❌ None | ❌ None | ❌ None |
| TrendAgent | ✅ Full | ❌ None | ❌ None | ❌ None |
| MacroAgent | ✅ Full | ❌ None | ❌ None | ❌ None |
| NewsAgent | ✅ Full | ❌ None | ❌ None | ❌ None |
| Council | ✅ Full | ✅ Full | 🟡 Partial (weights) | ❌ None |
| MetaCouncil | ✅ Full | ❌ None | ❌ None | ❌ None |
| ShortTermMemory | 🟡 Storage | ❌ None | ❌ None | ❌ None |
| LongTermMemory | 🟡 Storage | ❌ None | ❌ None | ❌ None |
| PerformanceMemory | ❌ None | ✅ Full | ✅ Full (metrics) | ❌ None (metrics are not hypotheses) |
| PaperTrading | ✅ Full | ✅ Full | ❌ None | ❌ None |
| DirectionController | 🟡 Partial | ✅ Full | ✅ Full (direction) | ❌ None |
| CapitalGuard | 🟡 Partial | ✅ Full | 🟡 Partial (mode) | ❌ None |
| CrashDetector | ✅ Full | 🟡 Partial | ❌ None | ❌ None |
| KnifeDetector | ✅ Full | ❌ None | ❌ None | ❌ None |
| ScoreOpportunity | ✅ Full | ❌ None | ❌ None | ❌ None |
| DataQualityEngine | 🟡 Partial | 🟡 Partial | 🟡 Partial (source) | ❌ None |
| FailureClassifier | ✅ Full | ✅ Full | ❌ None | ❌ None |
| Telemetry | ❌ None | ✅ Full | ❌ None | ❌ None |
| BacktestEngineV2 | ❌ None | ✅ Full | ❌ None | ❌ None |

**Key insight:** Every component has either signal processing capability OR outcome recording. No component has both. The components that process signals (agents) do not learn from outcomes. The components that record outcomes (PerformanceMemory, Telemetry) do not feed back into signal processing. The bridge between outcomes and improved perception does not exist.

### 2.3 Learning Loop Completeness

The Theory (Hypothesis 8) defines the learning loop as:

1. **Decision** — the system commits to an action
2. **Outcome** — the world produces a result
3. **Comparison** — the system compares outcome to hypothesis
4. **Update** — the system adjusts its judgment

Current state:

| Step | Status | Gap |
|------|--------|-----|
| Decision | ✅ Implemented | CouncilDecision → TradeSignal |
| Outcome | ✅ Implemented | Trade PnL recorded in PerformanceMemory |
| Comparison | ❌ **Missing** | Binary win/loss is not comparison to hypothesis. There is no hypothesis to compare against. |
| Update | 🟡 **Partial** | Council weights update. No hypothesis-level update. No evidence-level update. No agent-level update. |

The loop is broken at step 3. Without comparison to a hypothesis, the "update" step cannot know what to update or why.

---

## 3. Criterion Readiness Score

### 3.1 Scoring Methodology

Each dimension is scored from 0.0 (no capability) to 1.0 (full operational capability). Scores are based on documented system behavior, not on potential.

### 3.2 Dimension Scores

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Hypothesis Formation** | 0.00 | No mechanism to form a testable, falsifiable hypothesis exists anywhere in the codebase |
| **Hypothesis Tracking** | 0.00 | No hypothesis object, no hypothesis lifecycle, no hypothesis storage |
| **Evidence Management** | 0.05 | Agent opinions contain evidence lists, but no evidence tracking per hypothesis, no weight, no decay, no source reliability |
| **Confidence Calibration** | 0.15 | PerformanceMemory computes confidence bias (difference between confidence and accuracy). This is not fed back to agents or used for calibration adjustment. |
| **Outcome Decomposition** | 0.10 | ExitReason enum (stop_loss, take_profit, time_expiry). No error classification by decision type. No decomposition into perception vs. judgment vs. execution vs. timing. |
| **Knowledge Extraction** | 0.00 | No mechanism to extract generalizable lessons from outcomes. PerformanceMemory reports statistics but does not generate knowledge statements. |
| **Criterion Measurement** | 0.00 | No criterion index, no criterion level assessment, no mechanism to measure calibration improvement over time |
| **Perceptual Learning** | 0.00 | No agent adjusts its thresholds, rules, or models based on past performance. Every agent is frozen at its initial configuration. |
| **Feedback Loop Integration** | 0.10 | Council weights update based on track records. DirectionController adjusts direction availability. These are narrow feedback loops that do not reach the perceptual or judgment layers. |
| **Self-Evaluation** | 0.00 | The system has no mechanism to evaluate whether a decision was good given the evidence available at the time, independent of the outcome. |

### 3.3 Overall Readiness Score

**Composite Score: 0.04 / 1.0**

**Important caveat:** This composite score is a simple average of ten unequally weighted dimensions. It implies a precision that does not exist. Hypothesis formation (score 0.00) is more foundational than feedback loop integration (score 0.10). A simple average obscures this. The individual dimension scores are more informative than the composite.

The score is not a criticism of the MVP. It is a baseline measurement. The MVP was designed to validate the event-to-action pipeline, which it does successfully. The hypothesis-to-learning pipeline was never claimed to exist.

The score exists to provide a reference point for measuring future improvement. A score of 0.3 would indicate the system has crossed into Level 3 (Hypothesis-Driven). A score of 0.7 would indicate Level 5 (Operational Criterion).

---

## 4. Strengths

### 4.1 Philosophical Foundation

The first-principles documents are the project's strongest asset. They are:
- Internally consistent across 15 documents
- Evidence-aware (assumptions are documented with confidence levels and falsification methods)
- Self-critical (the Self-Review document identifies weak assumptions)
- Falsifiable (the Theory states "no theoretical claim is final")
- Domain-independent (trading is a validation domain, not the identity)

Most projects attempt to build intelligence without defining what intelligence means. O.M.A.-C.O.R.E. has defined criterion, identified its prerequisites, and acknowledged its open questions. This philosophical rigor is rare and valuable.

### 4.2 Outcome Recording Infrastructure

PerformanceMemory is the most advanced learning-related component in the system. It:
- Records every trade with full attribution to agent opinions
- Tracks agent-level accuracy, confidence bias, and per-asset/direction performance
- Computes rolling metrics that could feed a learning system
- Persists data for offline analysis

The infrastructure for outcome recording is largely complete. The missing piece is the hypothesis layer that turns outcomes into knowledge.

### 4.3 Primitive Feedback Loops

Council track records and DirectionController demonstrate that the architects understand the need for adaptive feedback. These are genuine (if narrow) examples of outcome-based behavior modification. They show that the architecture can support learning loops when they are designed in.

### 4.4 Backtesting Capability

BacktestEngineV2 provides the ability to test hypotheses against historical data. This is a critical capability that will be essential for hypothesis validation. It exists and works, even if it is not yet integrated with a hypothesis lifecycle.

### 4.5 Honest Architecture

The system does not claim capabilities it does not have. There is no "AI" label on components that are simple rules. There is no pretense of machine learning where there is only threshold logic. This honesty is a strength because it means the system's actual capabilities are measurable and improvable without having to strip away hype first.

---

## 5. Weaknesses

### 5.1 Complete Absence of Hypotheses

The single most significant weakness. There is no representation of a hypothesis anywhere in the system. This is not a gap — it is a missing architectural layer.

**Consequence:** The system cannot ask "what belief is being tested by this trade?" It cannot ask "what evidence supports this belief?" It cannot ask "was this belief confirmed or rejected by the outcome?" It cannot learn from outcomes because it has no structure to learn into.

**Severity:** Critical. Without hypotheses, there is no unit of learning.

### 5.2 All Agents Are Frozen

Every agent (market, risk, trend, macro, news) uses static rules. None adjusts its behavior based on outcomes. A market agent that has been wrong 80% of the time on SELL signals continues to generate SELL signals with the same confidence.

**Consequence:** The system's perception layer cannot improve. Only the aggregation layer (Council) can adjust weights. The system cannot learn to perceive better — it can only learn to trust or distrust its perceptions.

**Severity:** High. The system is blind to its own perceptual errors.

### 5.3 No Error Classification by Decision Type

FailureClassifier classifies runtime exceptions (API failures, data failures). It does not classify decision errors (wrong hypothesis, wrong timing, poor execution).

**Consequence:** When a trade loses, the system records "stop loss hit" but not "the hypothesis was correct but the timing was wrong." Without error type classification, the system cannot identify which types of errors it makes most often, and cannot target improvements.

**Severity:** High. Error type classification is essential for targeted learning.

### 5.4 No Knowledge Extraction

PerformanceMemory produces statistics but not knowledge. A confirmed hypothesis should produce a lesson: "this pattern works in these conditions." A rejected hypothesis should produce a lesson: "this pattern fails in these conditions." The system produces neither.

**Consequence:** Every outcome is a data point. None becomes a lesson. The system's memory grows but its understanding does not.

**Severity:** Critical. Knowledge is the bridge between outcomes and criterion.

### 5.5 No Criterion Measurement

The Criterion document defines seven levels of criterion development. The system has no mechanism to determine which level it is at, how it is progressing, or whether criterion is improving at all.

**Consequence:** The system's primary success metric (criterion) cannot be measured. The system defaults to measuring what it can measure (PnL, win rate) and optimizes for those instead.

**Severity:** Critical. What cannot be measured cannot be improved.

### 5.6 No Decision Quality Metric

The system evaluates outcomes (win/loss) but not decisions (was this a good decision given the evidence at the time?). A profitable trade from a bad decision reinforces bad behavior. An unprofitable trade from a good decision punishes good behavior.

**Consequence:** The system cannot distinguish between luck and skill. It learns superstitions rather than principles.

**Severity:** High. Decision quality is what the system should optimize, not outcome quality.

### 5.7 Capital Allocation Is Binary

PaperTradingEngine has a hard limit of 3 simultaneous positions. When capacity is reached, all new signals are rejected regardless of quality. There is no comparison, no replacement, no partial allocation.

**Consequence:** The system cannot learn to prioritize. All signals at capacity are treated equally (rejected). The system cannot develop criterion about which opportunities deserve capital.

**Severity:** Medium. This is a known limitation documented in the Execution and Capital Allocation thesis.

---

## 6. Missing Concepts

The following concepts are defined in the philosophy but have no corresponding architectural object in the implementation:

| Concept | Defined In | Current Status | Missing As |
|---------|-----------|---------------|------------|
| Hypothesis | Glossary, Theory, Criterion, Discoveries | Not implemented | First-class object with lifecycle |
| Evidence | Glossary, Theory, Criterion, Discoveries | Implicit (agent opinion evidence lists) | Tracked object with direction, weight, reliability, decay |
| Knowledge | Glossary, Theory, Discoveries | Not implemented | Extracted lesson from hypothesis outcome |
| Error Type | Discoveries (Failure Intelligence) | Not implemented (only runtime exception types exist) | Decision error taxonomy with tracking |
| Criterion Level | Criterion Document | Not measured | Periodic assessment |
| Decision Quality | Discoveries (Decision Quality) | Not implemented | Score per decision independent of outcome |
| Context / Regime | Criterion Document | Implicit (CrashDetector mode, VIX) | Explicit object attached to hypotheses and trades |
| Confidence Calibration | Glossary, Criterion | Partial metric (PerformanceMemory bias) | Feedback mechanism that adjusts confidence based on calibration |
| Opportunity Capture Rate | Discoveries | Not implemented | Metric comparing captured vs. missed opportunities |

---

## 7. Missing Objects

The following architectural objects would need to exist for the system to support the hypothesis lifecycle:

| Object | Purpose | Depends On |
|--------|---------|------------|
| **Hypothesis** | First-class representation of a testable belief | None (foundational) |
| **HypothesisLifecycle** | State machine managing hypothesis state transitions | Hypothesis |
| **Evidence** | Tracked piece of information supporting or contradicting a hypothesis | Hypothesis |
| **SourceReliability** | Tracked reliability per information source | Evidence |
| **HypothesisRun** | Record of a single test of a hypothesis (links hypothesis → decision → action → outcome) | Hypothesis, Decision, Action, Outcome |
| **ErrorClassification** | Decomposed error type with severity | HypothesisRun, Outcome |
| **KnowledgeEntry** | Generalizable lesson extracted from hypothesis outcome | HypothesisRun, ErrorClassification |
| **CriterionSnapshot** | Periodic measurement of system-wide criterion metrics | KnowledgeEntry, Hypothesis (aggregate) |
| **DecisionQuality** | Score evaluating a decision given evidence available at the time | Hypothesis, Evidence (at decision time), Outcome |
| **ContextProfile** | Description of market regime, volatility regime, etc. at a point in time | Event data, derived metrics |

---

## 8. Missing Feedback Loops

The following feedback loops are absent. Each is a cycle that, if closed, would move the system toward criterion development.

| Loop | Description | Current State | If Closed, Would Enable |
|------|-------------|---------------|------------------------|
| **Hypothesis → Outcome → Hypothesis** | Hypothesis predicts outcome, outcome confirms/rejects hypothesis | Not present | Scientific hypothesis testing |
| **Agent Prediction → Outcome → Agent Threshold** | Agent makes prediction, outcome adjusts agent's thresholds | Not present | Perceptual learning |
| **Evidence → Confidence → Decision → Outcome → Evidence Weight** | Evidence weight affects confidence, confidence affects decision, outcome adjusts evidence weight | Not present | Calibrated evidence evaluation |
| **Confidence → Accuracy → Calibration → Confidence** | Confidence compared to accuracy, calibration adjusts future confidence | Partial (metric exists, no feedback) | Self-calibrating system |
| **Error Type → Error Frequency → Error Prevention** | Error classified, type frequency tracked, system adjusts to prevent recurrence | Not present | Learning from failure |
| **Decision → Outcome → Decision Quality → Decision Rules** | Decision evaluated independently of outcome, quality metric adjusts decision rules | Not present | Decision quality optimization |
| **Criterion Measurement → Criterion Improvement → Criterion Measurement** | Criterion measured, improvements identified, changes made, re-measured | Not present | Self-directed improvement |

---

## 9. Architectural Risks

| Risk | Description | Severity | Mitigation |
|------|-------------|----------|------------|
| **Hypothesis lifecycle cannot be retrofitted** | The current architecture may not cleanly support the hypothesis lifecycle without significant restructuring | Medium | The schemas already have linking fields (event_id, opinion_id). The lifecycle can be added as a parallel layer without breaking the existing pipeline. |
| **Agents are too tightly coupled to their static rules** | Adding learning to agents may require replacing rule-based logic with learnable parameters | High | Start with one learnable agent as a proof of concept. Keep static agents as baselines. |
| **PerformanceMemory is optimized for reporting, not learning** | Its data model may not support the hypothesis lifecycle queries needed for learning | Medium | PerformanceMemory can be extended or supplemented with a dedicated hypothesis store. |
| **Current position capacity (3) limits hypothesis diversity** | With only 3 positions, the system cannot test many hypotheses simultaneously | Low | Capacity is configurable. The optimal number is a research question (R-009). |
| **No experiment framework** | The system runs one strategy at a time. There is no A/B testing, no control group, no hypothesis competition. | High | Parallel hypothesis testing requires architectural changes to support multiple simultaneous strategies. |
| **Evidence decay is not modeled** | Evidence from 6 months ago is treated as equally relevant as evidence from yesterday | Medium | Can be added to the evidence management system once it exists. |

---

## 10. Scientific Risks

| Risk | Description | Severity | Falsification |
|------|-------------|----------|---------------|
| **Consequences cannot be detected above noise** (A-001) | The fundamental assumption of the entire project. If consequences cannot be detected with useful accuracy, the framework collapses. | Critical | Measure consequence detection accuracy. If it does not exceed chance after sufficient training, the assumption is falsified. |
| **Criterion does not compound** (A-002) | Criterion may plateau or decay. The system may stop improving after an initial learning phase. | High | Track criterion-relevant metrics over years. If improvement plateaus below useful levels, the compounding assumption is weakened. |
| **Explicit hypotheses do not outperform implicit learning** (A-007) | The hypothesis lifecycle may add complexity without improving learning speed or quality compared to a purely statistical approach. | Medium | Compare hypothesis-driven learning against pattern-recognition-only learning on the same tasks. |
| **Learning does not transfer between domains** (A-006) | Trading criterion may not transfer to creation or entrepreneurship. Each profile may need independent development. | High | Measure criterion in trading, then test in another domain. If performance is at chance levels, transfer has not occurred. |
| **Memory structure does not improve learning** (A-003) | The structured hypothesis lifecycle may not improve learning over simpler storage approaches. | Medium | Compare structured hypothesis memory against flat outcome storage on learning velocity. |

---

## 11. Implementation Risks

| Risk | Description | Severity |
|------|-------------|----------|
| **Overengineering the hypothesis lifecycle** | Building too much infrastructure before validating that hypothesis tracking actually improves learning | High |
| **Underengineering the hypothesis lifecycle** | Building too little structure, resulting in a system that cannot extract real knowledge | High |
| **Premature integration** | Connecting the hypothesis lifecycle to the live trading pipeline before it is validated in simulation | Medium |
| **Metric fixation** | Optimizing hypothesis quality metrics before validating that they correlate with actual criterion development | Medium |
| **Architectural lock-in** | The hypothesis lifecycle design committing to assumptions that are later falsified | Medium |

---

## 12. Tensions and Contradictions

### 12.1 Simplicity vs. Hypothesis Lifecycle (Constitution Article 4)

The Constitution states: *"Complexity is debt. Every component, every layer, every abstraction is a liability until proven otherwise."*

The hypothesis lifecycle adds significant complexity. This creates a tension that must be acknowledged rather than ignored.

**Defense:** The complexity is justified because:
1. The hypothesis lifecycle is not optional — it is the mechanism by which criterion develops. Without it, the system is a signal engine regardless of how sophisticated its other components become.
2. The complexity is concentrated in the lifecycle layer, not distributed across the system. The existing pipeline (events → agents → council → trading) does not need to change.
3. The alternative — relying on implicit learning through statistical pattern matching — has been considered and is documented in Section 12.3.

**Risk:** The complexity may still exceed the benefit. This can only be resolved by testing (Priority 1). If the hypothesis lifecycle does not produce measurable improvement in criterion-relevant metrics, the Constitution demands its removal.

### 12.2 Generic Agent Framework Risk (Anti-Goal 5)

Anti-Goal 5 states that O.M.A.-C.O.R.E. should not become a "generic agent framework." The hypothesis lifecycle could be seen as moving in this direction — a general-purpose scientific method that could apply to any domain.

**Defense:** The lifecycle is not generic. It is specific to consequence detection and criterion development. It is the implementation of the project's specific theory of intelligence, not a platform for building any kind of agent. Every stage of the lifecycle serves the specific purpose of turning outcomes into improved judgment about consequences.

**Boundary:** If the lifecycle can be used for arbitrary purposes unrelated to criterion development, it has crossed the anti-goal boundary. The lifecycle must remain focused on consequence-driven learning.

### 12.3 Alternative Approaches to Learning

This audit assumes that explicit hypothesis tracking is the correct approach to developing criterion. This assumption should be challenged.

**Implicit learning approach:** An alternative would bypass explicit hypotheses entirely. A neural network or reinforcement learning system could learn directly from the PerformanceMemory data — mapping events and outcomes to improved decisions without forming explicit, testable beliefs.

**Why explicit hypotheses are preferred in this project:**
- **Explainability:** An explicit hypothesis can be examined, challenged, and refined. An implicit model cannot.
- **Error decomposition:** When an explicit hypothesis is wrong, the system can identify which part of the hypothesis failed. An implicit model provides only a scalar error signal.
- **Knowledge transfer:** Explicit knowledge ("this pattern works in bull markets") can be applied across domains. Implicit knowledge is architecture-specific.
- **Falsifiability:** An explicit hypothesis can be tested and rejected. An implicit model can only be retrained.

**Risk:** The explicit approach may prove slower, more brittle, or less effective than implicit learning. This is documented as Assumption A-007 (Explicit Hypotheses Outperform Implicit Intuition), currently untested. The hypothesis lifecycle itself should eventually be tested against an implicit baseline.

### 12.4 Falsification Criteria for the Hypothesis Lifecycle

The hypothesis lifecycle is itself a hypothesis. The following evidence would falsify it:

| Claim | Falsifying Evidence |
|-------|-------------------|
| Explicit hypothesis tracking improves learning | After 12 months of operation, criterion-relevant metrics show no improvement compared to the pre-lifecycle baseline |
| Evidence tracking improves confidence calibration | After 1000+ evaluated hypotheses, calibration is not significantly better than chance |
| Error classification reduces error recurrence | Error type frequencies do not decline over 24 months of operation |
| Knowledge extraction produces generalizable lessons | Extracted lessons cannot be applied to predict outcomes in novel market conditions |
| The lifecycle justifies its complexity | The system's decision quality does not improve despite the added infrastructure |

If any of these conditions are met, the hypothesis lifecycle should be reconsidered or abandoned in favor of a simpler approach.

---

### Priority 1 — Hypothesis Data Model (Critical)

Define and implement the Hypothesis, Evidence, and HypothesisRun data objects. This is the foundational layer. Without it, nothing else is possible.

**Success criteria:** A hypothesis can be created with all required attributes, evidence can be added, and the hypothesis lifecycle state can be tracked.

### Priority 2 — Hypothesis Lifecycle State Machine (Critical)

Implement the state machine that manages hypothesis transitions: CANDIDATE → FORMULATED → ACTIVE → TESTING → EVALUATED → CONFIRMED/REJECTED/INCONCLUSIVE → ARCHIVED → RETIRED.

**Success criteria:** A hypothesis automatically transitions through its lifecycle as events, decisions, actions, and outcomes occur. State transitions are recorded with timestamps.

### Priority 3 — Linking Trades to Hypotheses (Critical)

Every trade must carry a hypothesis_id. Every outcome must update the linked hypothesis. Every PerformanceMemory report must include hypothesis-level statistics alongside agent-level statistics.

**Success criteria:** Every trade in PerformanceMemory can be traced back to the hypothesis that generated it. Every hypothesis shows its complete outcome history.

### Priority 4 — Error Classification by Decision Type (High)

Define and implement the decision error taxonomy: wrong event interpretation, wrong correlation, wrong consequence, correct consequence wrong timing, correct hypothesis poor execution, external shock. Add error type recording to the hypothesis outcome evaluation stage.

**Success criteria:** Every evaluated hypothesis carries an error classification. Error type frequencies can be reported and trended.

### Priority 5 — Knowledge Extraction (High)

Define the KnowledgeEntry object. Implement extraction of generalizable lessons from hypothesis outcomes. Each confirmed or rejected hypothesis should produce at least one lesson.

**Success criteria:** Knowledge entries exist, linked to their source hypotheses. Knowledge can be queried by domain, context, and lesson type.

### Priority 6 — Criterion Snapshot (High)

Define the CriterionSnapshot — a periodic measurement of all criterion-relevant metrics: calibration, precision, recall, error type frequencies, hypothesis quality trends, knowledge yield. Create a mechanism to compare snapshots over time.

**Success criteria:** A criterion snapshot can be generated at any time. Trends can be visualized. Improvement or degradation is detectable.

---

## 13. Quick Wins

These items can be implemented with minimal architectural change and provide immediate learning value:

| Item | Effort | Impact | Description |
|------|--------|--------|-------------|
| **Hypothesis metadata on TradeSignal** | Low | Medium | Add an optional `hypothesis_id` and `hypothesis_description` field to the TradeSignal schema. This does not require the full lifecycle but enables tracking. |
| **Error classification on Trade close** | Low | Medium | Add an `error_type` field to the trade close record. Classify closed trades as "hypothesis correct," "wrong timing," "wrong hypothesis," "external shock," or "unknown." |
| **Agent confidence calibration report** | Low | Low | PerformanceMemory already computes confidence bias. Publish it in a format that agents could theoretically read. |
| **Hypothesis creation hook** | Low | Low | Add a callback or event that fires when a new hypothesis concept is identified, without implementing the full lifecycle. |
| **Criterion level self-assessment** | Low | Low | Create a document that maps current system behavior to Criterion Levels 0–6. Re-assess quarterly. |

---

## 14. Long-Term Roadmap

### Phase 1 — Hypothesis Infrastructure (Current Gap)

**Objective:** Make hypothesis a first-class architectural object with a defined lifecycle.

**Duration:** Unknown — this is conceptual design and implementation.

**Deliverables:**
- Hypothesis data model
- Hypothesis lifecycle state machine
- Evidence tracking
- Hypothesis-to-trade linking
- PerformanceMemory hypothesis-level reporting

**Criteria for completion:** A complete hypothesis lifecycle can be traced from creation through outcome to knowledge extraction for every trade.

### Phase 2 — Perceptual Learning

**Objective:** Make agents capable of learning from their own performance.

**Duration:** After Phase 1.

**Deliverables:**
- At least one agent reads its own hypothesis accuracy history
- Agent thresholds adjust based on observed performance
- Agent confidence calibration improves

**Criteria for completion:** The market agent's SELL signal accuracy improves over time across a statistically significant number of trades.

### Phase 3 — Error-Driven Improvement

**Objective:** Error type frequencies decline over time as the system learns from its failures.

**Duration:** After Phase 1 and Phase 2.

**Deliverables:**
- Error type frequency tracking
- Automated error type pattern detection
- Behavior modification based on dominant error types

**Criteria for completion:** At least one error type shows a statistically significant decreasing trend over 6 months of operation.

### Phase 4 — Knowledge Compounding

**Objective:** Knowledge extraction produces lessons that improve future hypothesis quality.

**Duration:** After Phase 1.

**Deliverables:**
- KnowledgeEntry lifecycle
- Cross-hypothesis pattern detection
- Knowledge-fed prior confidence adjustment

**Criteria for completion:** Hypothesis quality metrics show measurable improvement over time, with improvement attributable to knowledge extracted from previous hypotheses.

### Phase 5 — Criterion Measurement

**Objective:** Criterion can be measured, trended, and used as a primary system health metric.

**Duration:** Requires all previous phases for meaningful measurement.

**Deliverables:**
- CriterionSnapshot framework
- Automated criterion level assessment
- Criterion trend reporting

**Criteria for completion:** Criterion snapshot shows improvement across at least 4 of 9 dimensions over a 12-month period.

### Phase 6 — Self-Correction (Level 4)

**Objective:** The system detects weakening hypotheses before outcomes confirm the error.

**Duration:** After all previous phases.

**Deliverables:**
- Real-time evidence weakening detection
- Pre-outcome hypothesis re-evaluation triggers
- Position reduction or exit based on weakening evidence

**Criteria for completion:** The system reduces or closes positions based on weakening evidence at least 24 hours before the outcome would have invalidated the hypothesis.

### Phase 7 — Operational Criterion (Level 5)

**Objective:** The system consistently demonstrates calibrated judgment across multiple market conditions.

**Duration:** Continuous improvement after all previous phases.

**Deliverables:**
- Stable calibration across regimes
- Consistent hypothesis quality improvement
- Knowledge persistence across regime changes

**Criteria for completion:** All criterion metrics are stable or improving for 24 consecutive months of operation.

### Phase 8 — Strategic Criterion (Level 6)

**Objective:** The system decides what to learn next.

**Duration:** Long-term aspirational.

**Deliverables:**
- Meta-hypothesis formation (hypotheses about which hypotheses to pursue)
- Resource allocation for learning
- Domain expansion decisions

**Criteria for completion:** The system autonomously identifies a new domain or question to investigate and demonstrates learning in that domain.

---

## 15. Critical Gap Analysis

### 15.1 The Fundamental Gap

The Criterion document states:

> *"Criterion emerges from the interaction of Memory, Learning, Hypotheses, Evidence, Outcomes, Knowledge, Context, and Time."*

Of these eight elements, the current system has:

| Element | Status | Why It Matters |
|---------|--------|----------------|
| Memory | ✅ Partial | Stores events and outcomes but not hypotheses or evidence |
| Learning | 🟡 Primitive | Council weight updates are learning, but they are too narrow to produce criterion |
| Hypotheses | ❌ **Absent** | No unit of learning exists |
| Evidence | ❌ **Absent** | No evidence tracking per belief |
| Outcomes | ✅ Present | Recorded with attribution |
| Knowledge | ❌ **Absent** | No extraction, no storage, no application |
| Context | 🟡 Implicit | CrashDetector mode, CapitalGuard mode — not a structured context object |
| Time | ✅ Present | System runs continuously and accumulates experience |

**The gap is not a missing feature. It is a missing scientific layer.**

The proposed solution to this gap is defined in the companion document: **14_HYPOTHESIS_LIFECYCLE_MANAGER.md**. That document defines the complete scientific lifecycle of a hypothesis — from candidate formation through evidence collection, testing, outcome evaluation, error classification, knowledge extraction, and criterion update.

The system has the execution infrastructure to act on beliefs. It has the memory infrastructure to record outcomes. What it lacks is the scientific infrastructure to turn outcomes into improved beliefs.

### 15.2 Why This Gap Exists

The MVP was designed to validate the event-to-action pipeline. This was the correct priority. Before you can learn from outcomes, you need to be able to produce outcomes reliably. The MVP has demonstrated this.

The gap exists because the hypothesis lifecycle was intentionally deferred. The CRITERION_AND_CONSEQUENCE_THESIS document states:

> *"For MVP purposes, the Consequence Engine is not authorized for implementation. For MVP purposes, cluster intelligence is not authorized for implementation. For MVP purposes, explicit hypothesis tracking is not authorized for implementation."*

This was a correct architectural decision. The MVP validates the foundation. The next phase must build the scientific layer on top of it.

### 15.3 The Chain That Must Be Completed

The chain from the Criterion and Consequence thesis:

```
Events → Correlations → Clusters → Consequences → Hypotheses → Opportunities → Actions → Outcomes → Memory → Knowledge → Criterion
```

The current system covers:

```
Events → [Correlations → Clusters → Consequences → Hypotheses] → Opportunities → Actions → Outcomes → Memory → [Knowledge → Criterion]
```

The bracketed sections are missing. The system jumps from Events directly to Opportunities (via agent signals) without the intermediate scientific steps. It records Outcomes in Memory but does not extract Knowledge or update Criterion.

### 15.4 The Self-Review Warning

The Self-Review document (09_SELF_REVIEW.md) warned about this gap:

> *"The value of hypothesis tracking. The theory states that explicit hypothesis tracking improves learning. This should be tested: does a system with hypothesis tracking learn faster than a system without it?"*

This question cannot be answered because the system has no hypothesis tracking. The warning has become a confirmed gap.

---

## 16. What Must Exist Before O.M.A.-C.O.R.E. Can Honestly Claim to Develop Criterion?

This is the central question. The answer is not a single component or feature. It is a set of capabilities that must be demonstrated.

### 16.1 Necessary Capabilities

**1. Hypothesis as an operational object in the system.**

A hypothesis must exist as a first-class entity that can be created, tracked, updated, confirmed, rejected, archived, and retired. It must have a defined lifecycle with explicit states and transitions. It must carry evidence, confidence, invalidation conditions, and outcome history.

*Without this, there is no unit of learning.*

**2. Every trade traceable to a hypothesis.**

It must be possible to answer: "What hypothesis did this trade test? What was the prediction? What was the expected consequence? What were the invalidation conditions? Did the outcome confirm or reject the hypothesis?"

*Without this, outcomes are data points, not evidence.*

**3. Evidence tracked per hypothesis with direction, weight, and source reliability.**

Evidence must be accumulated, not averaged. Supporting and contradicting evidence must be tracked as independent dimensions. Source reliability must be measured and updated over time. Evidence must decay.

*Without this, confidence is intuition, not calculation.*

**4. Error classification by decision type, not just runtime exception type.**

Every evaluated hypothesis must carry an error classification that decomposes what went wrong: perception, judgment, timing, execution, or external factors. Error type frequencies must be tracked and trended over time.

*Without this, the system cannot learn from failure.*

**5. Knowledge extracted from hypothesis outcomes.**

Every confirmed or rejected hypothesis must produce at least one generalizable lesson. Knowledge must be stored, queryable, and applicable to future hypotheses. Knowledge must be provisional and subject to revision.

*Without this, the system accumulates data, not understanding.*

**6. Criterion measured and trended.**

Criterion must be operationally defined with measurable dimensions: calibration, precision, recall, error type frequency, knowledge yield, hypothesis quality. These dimensions must be measured periodically and trended over time.

*Without this, criterion is a philosophical concept, not an operational one.*

**7. Demonstrated improvement in at least one criterion dimension over a statistically significant period.**

The system must show that its hypothesis quality, calibration, or error recurrence rate is improving over time. The improvement must be statistically significant and attributable to the hypothesis lifecycle.

*Without this, the system is doing science but not showing results.*

### 16.2 Sufficiency Condition

O.M.A.-C.O.R.E. can honestly claim to develop criterion when:

1. **Capabilities 1–6 are operational** — the infrastructure for criterion development exists
2. **Capability 7 is demonstrated** — the infrastructure produces measurable improvement
3. **The improvement is attributable to the hypothesis lifecycle** — not to external factors, increased data volume, or human intervention
4. **The results are replicable** — the same improvement pattern is observed across multiple time periods, market conditions, or domains

### 16.3 Interim Honesty

Until these conditions are met, the honest claim is:

> *"O.M.A.-C.O.R.E. has the philosophical foundation, execution infrastructure, and outcome recording necessary to support criterion development. The hypothesis lifecycle — the scientific layer that turns outcomes into knowledge — is being designed and validated. The system is currently between Criterion Level 1 (Pattern Recognition) and Level 2 (Contextual). It has not yet reached Level 3 (Hypothesis-Driven)."*

This is not a failure. It is an accurate statement of current maturity. The project's philosophy requires honesty about where it is and what remains to be done.

---

## 17. Self-Assessment of This Document

The claims in this document are themselves provisional. They should be evaluated against the project's own principles:

| Claim | Can It Be Falsified? | How? |
|-------|---------------------|------|
| The system has no hypothesis object | ✅ Yes | Demonstrate a hypothesis object with lifecycle in the codebase |
| Error classification does not exist | ✅ Yes | Demonstrate error type classification on a trade outcome |
| Agents are frozen | ✅ Yes | Demonstrate an agent that adjusts thresholds based on outcomes |
| Knowledge extraction does not exist | ✅ Yes | Demonstrate a KnowledgeEntry linked to a hypothesis outcome |
| Criterion is not measured | ✅ Yes | Demonstrate a CriterionSnapshot that shows measurable dimensions |

Every claim in this audit is falsifiable. If the system changes, the audit should be updated.

---

## 18. Final Assessment

### Current State

The MVP is a working signal engine with:
- Robust event detection
- Safe execution
- Reliable outcome recording
- Primitive feedback loops

It is not a learning intelligence system. No hypothesis is formed, tested, or learned from. No knowledge is extracted from outcomes. No criterion is measured or trended.

### The Gap

The gap between the current system and a criterion-developing system is the hypothesis lifecycle:

- Hypothesis as an object → currently absent
- Evidence tracking per hypothesis → currently absent
- Hypothesis-to-outcome linking → currently absent
- Error classification by decision type → currently absent
- Knowledge extraction → currently absent
- Criterion measurement → currently absent
- Perceptual learning → currently absent

### The Verdict

**PARTIALLY.**

The system is PARTIALLY capable of developing criterion because:

1. **The prerequisites exist.** The event pipeline, execution engine, guard layers, and outcome recording infrastructure are in place. Without these, no learning would be possible.

2. **The philosophy is sound.** The first-principles documents correctly identify what criterion is, what produces it, and what it requires. The project knows what it is trying to build.

3. **The scientific layer does not exist.** The hypothesis lifecycle has not been implemented. The system cannot form, test, or learn from hypotheses. It has no unit of learning.

4. **The path is clear.** The gap is well-defined, the missing concepts are identified, and the priority order is known.

The MVP has built the **execution** layer of an intelligence system. It has not yet built the **learning** layer. Both are necessary for criterion to emerge. The execution layer works. The learning layer must be built next.

---

## 19. Final Principle

A signal engine produces outputs.

A learning intelligence system produces improved judgment over time.

The difference is not in the outputs. It is in what the system does with the feedback from those outputs.

The current MVP produces outputs. When it learns from those outputs through a complete hypothesis lifecycle, it will become a learning intelligence system — and criterion will begin to emerge.

---

*This document is a snapshot of current capability. It should be updated as the system evolves. Every claim should be re-evaluated against the system's actual behavior, not its intended design.*

---

*End of 15_CRITERION_READINESS_AUDIT.md — Version 1.0 — June 2026*
