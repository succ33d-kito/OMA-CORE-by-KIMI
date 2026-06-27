# Hypothesis Lifecycle Manager

## The Scientific Lifecycle of a Hypothesis in O.M.A.-C.O.R.E.

*Version 1.0 — June 2026*

---

## 1. Purpose

This document defines what a hypothesis is, why it is the fundamental unit of learning, and how it lives, dies, and contributes to criterion inside O.M.A.-C.O.R.E.

It does not describe an engine, a service, or a piece of infrastructure. It describes a **scientific lifecycle** — a set of stages, transitions, and principles that any hypothesis must pass through for the system to develop demonstrable criterion.

The Hypothesis Lifecycle Manager is the name for this conceptual framework, not a component to be built. It is the missing scientific layer between O.M.A.-C.O.R.E.'s philosophy and its implementation.

---

## 2. What Is a Hypothesis?

### 2.1 Definition

A hypothesis is a **structured, recorded, testable belief about a consequence**.

It is the answer to the question: *"Given what I have observed, what future state of the world may emerge?"*

A hypothesis connects:
- **Events** that have already happened (observations)
- To **consequences** that may happen (predictions about future states)
- Through **evidence** that supports or contradicts the connection (justification)

### 2.2 What a Hypothesis Is Not

| This | Is not a hypothesis because... |
|------|-------------------------------|
| "Price might go up" | Not testable — no specificity, no time horizon, no invalidation condition |
| "BUY Bitcoin" | An action, not a belief about a consequence |
| "RSI < 30 means oversold" | A rule, not a hypothesis — it is not being tested, it is being applied |
| "The market is volatile" | An observation, not a prediction about a future state |
| "I feel bullish" | An emotion, not a structured belief |
| "The model predicts 0.6" | An output, not a hypothesis — it lacks causal structure, invalidation conditions, and evidence inventory |

### 2.3 Distinction from Events

Events happen. Hypotheses explain possible consequences of events.

An event is: *"The Fed cut rates by 25 basis points."*

A hypothesis is: *"The Fed's 25bp rate cut, combined with a weak dollar and rising gold ETF inflows, will produce a gold price increase of 3–7% within 14 trading days — unless the dollar strengthens unexpectedly, in which case this hypothesis is invalidated."*

Events are inputs. Hypotheses are interpretations. The same event can generate many hypotheses. The same hypothesis can be affected by many events.

### 2.4 Distinction from Knowledge

Knowledge is what survives testing. A hypothesis that has been confirmed or rejected through outcome observation becomes knowledge. Until then, it remains a hypothesis — provisional, uncertain, subject to revision.

**Hypothesis:** *a question framed as a testable statement*
**Knowledge:** *the answer, always provisional, extracted from the outcome*

The same structure that makes a hypothesis testable is what makes it capable of becoming knowledge. An untestable hypothesis can never become knowledge — it remains opinion.

### 2.5 Why the Hypothesis Is the Fundamental Unit of Learning

The Theory (Hypothesis 6) states:

> *"Criterion emerges from repeated cycles of: Form a hypothesis, Act on the hypothesis, Observe the outcome, Compare outcome to hypothesis, Classify the error, Update the hypothesis, Accumulate the lesson."*

The hypothesis is the unit of learning because:
- It is the smallest structure that can be **tested**
- It is the smallest structure that can be **wrong in a specific way**
- It is the smallest structure from which a **generalizable lesson** can be extracted
- It is the smallest structure that can be **compared across contexts**

An event is too small — it has no predictive content.
A trade is too large — it bundles hypothesis, execution, timing, and luck.
A strategy is too large — it contains many untestable assumptions.

The hypothesis is the Goldilocks unit: small enough to test cleanly, large enough to produce meaningful knowledge.

---

## 3. The Complete Hypothesis Lifecycle

### 3.1 The Full Chain

```
Event
  │
  ▼
Hypothesis Creation ──────────── From event to possible consequence
  │
  ▼
Evidence Collection ──────────── Supporting and contradicting evidence
  │
  ▼
Confidence Assignment ────────── How likely is this hypothesis?
  │
  ▼
Decision ─────────────────────── Act? Wait? Ignore? Monitor?
  │
  ▼
Action (or Explicit Non-Action) ──── Interface with reality
  │
  ▼
Outcome ──────────────────────── What actually happened
  │
  ▼
Error Analysis ───────────────── Decompose the error by type
  │
  ▼
Hypothesis Update ────────────── Confirm, reject, or revise
  │
  ▼
Knowledge Extraction ─────────── What generalizable lesson exists?
  │
  ▼
Criterion Update ─────────────── How does this change the system's judgment?
```

### 3.2 Stage Descriptions

#### Stage 1: Hypothesis Creation

**Input:** One or more events, a detected pattern, a correlation, a cluster forming, or a human input.

**Process:** The system (or a human) formulates a structured belief about a possible consequence. The hypothesis must be testable and falsifiable. It must specify: what consequence is expected, under what conditions, within what time horizon, and what would disprove it.

**Output:** A FORMULATED hypothesis with initial evidence inventory, invalidation conditions, and time horizon.

**Failure modes:**
- Hypothesis is not falsifiable — cannot be tested, cannot produce knowledge
- Hypothesis is too vague — consequence cannot be measured
- Hypothesis is too narrow — consequence is trivial or already obvious
- Hypothesis is not grounded in evidence — speculation without basis

#### Stage 2: Evidence Collection

**Input:** The FORMULATED hypothesis, plus new events, data, and information.

**Process:** Evidence accumulates. Each piece of evidence is evaluated for:
- Direction (for or against the hypothesis)
- Weight (how strongly it supports or contradicts)
- Source reliability (how trustworthy the source is)
- Independence (is this new information, or correlated with existing evidence?)

Evidence is not averaged. Supporting and contradicting evidence are tracked as separate dimensions. A hypothesis can simultaneously have strong supporting evidence and strong contradicting evidence — this indicates high uncertainty, not moderate confidence.

**Output:** An evolving evidence inventory with supporting and contradicting entries.

**Failure modes:**
- Confirmation bias — only evidence that supports the hypothesis is tracked
- Source overreliance — evidence from a single unreliable source is overweighted
- Evidence blindness — contradictory evidence exists but is not detected
- Correlation trap — correlated evidence is treated as independent, inflating confidence

#### Stage 3: Confidence Assignment

**Input:** The evidence inventory, source reliability history, and the system's calibration history for similar hypotheses.

**Process:** Confidence is computed from:
- Evidence weight (total supporting weight / total relevant evidence)
- Evidence quality (specificity, independence, source reliability)
- Pattern consistency (have similar hypotheses been confirmed or rejected in similar contexts?)
- Calibration adjustment (does the system tend to be overconfident or underconfident in this type of hypothesis?)

Confidence is never purely numerical. It is always accompanied by the evidence that supports it, the evidence that contradicts it, and the uncertainty that remains.

**Output:** A confidence estimate (0.0–1.0) with explicit uncertainty bounds.

**Failure modes:**
- Overconfidence — confidence exceeds accuracy, leading to unwarranted action
- Underconfidence — confidence is below accuracy, leading to missed opportunities
- False precision — confidence is reported as 0.73 when the system's calibration is ±0.15
- Certainty — confidence of 1.0 or 0.0, which violates the principle that everything is provisional

#### Stage 4: Decision

**Input:** The hypothesis with its confidence, evidence inventory, and time horizon. The current portfolio and capital allocation state.

**Process:** The system decides what to do:
- **Act** — commit resources based on this hypothesis (open a trade)
- **Wait** — the hypothesis is not yet strong enough; collect more evidence
- **Monitor** — the hypothesis is worth tracking but not yet actionable
- **Ignore** — the hypothesis does not meet the minimum evidence threshold
- **Reduce** — a related active position should be reduced
- **Replace** — this hypothesis deserves capital more than an existing position

The decision is recorded alongside the hypothesis. Non-actions are as important as actions for learning.

**Output:** A decision record linked to the hypothesis.

**Failure modes:**
- Action without sufficient evidence — gambling, not testing
- Inaction despite sufficient evidence — missed learning opportunity
- Decision not recorded — the hypothesis cannot be evaluated without knowing what was decided
- Decision separated from hypothesis — outcome cannot be traced to the belief that produced it

#### Stage 5: Action (or Explicit Non-Action)

**Input:** The decision.

**Process:** If action was chosen, the action is executed (trade opened, content published, business decision made). If explicit non-action was chosen, the system records the decision not to act, with reasoning.

**Output:** An action record (or explicit non-action record) linked to the hypothesis and decision.

**Failure modes:**
- Action fails to execute — system error, market conditions, slippage
- Action is modified during execution — the hypothesis is no longer being tested as designed
- Non-action is not recorded — a learning opportunity is lost

#### Stage 6: Outcome

**Input:** The action and the hypothesis's time horizon.

**Process:** The system waits until:
- The time horizon expires, or
- The predicted consequence materializes, or
- An invalidation condition is triggered, or
- The position is closed (stop loss, take profit, time expiry, replacement)

When any of these occur, the outcome is recorded: what happened, when, by how much, and under what conditions.

**Output:** An outcome record linked to the action and hypothesis.

**Failure modes:**
- Outcome is ambiguous — not clearly confirming or rejecting
- Outcome is delayed — the time horizon was too short
- External shock intervenes — the outcome was caused by something outside the hypothesis
- Outcome is not recorded — the feedback signal is lost

#### Stage 7: Error Analysis

**Input:** The hypothesis, the outcome, and the system's error classification framework.

**Process:** The system decomposes the error (if any) into types:
- **Wrong event interpretation** — the triggering event was misunderstood
- **Wrong correlation** — the relationship between events was spurious
- **Wrong consequence** — the consequence did not emerge despite correct events
- **Correct consequence, wrong timing** — the consequence happened, but not within the predicted window
- **Correct consequence, correct timing, poor execution** — the hypothesis was right but the action was poorly calibrated
- **External shock** — an unpredictable event intervened
- **Correct hypothesis, action correctly avoided** — the system correctly chose not to act

A single outcome may contain multiple error types. The goal is not to assign a single label but to decompose the outcome into its components.

**Output:** An error classification record linked to the hypothesis and outcome.

**Failure modes:**
- Error classification is too coarse — "wrong" without specifying why
- Error classification is circular — "the hypothesis was wrong because the outcome was different"
- Hindsight bias — the system evaluates the hypothesis based on what it knows now, not what it knew then
- External shocks used as excuse — the system attributes all failures to external factors

#### Stage 8: Hypothesis Update

**Input:** The hypothesis, outcome, and error classification.

**Process:** The hypothesis is updated to its terminal state:
- **CONFIRMED** — the outcome aligns with the predicted consequence
- **REJECTED** — the outcome contradicts the predicted consequence
- **INCONCLUSIVE** — the outcome is ambiguous

In all cases, the hypothesis is updated with the outcome data, error classification, and a summary of what was learned.

**Output:** A terminal hypothesis with outcome and error classification.

**Failure modes:**
- Hypothesis is neither confirmed nor rejected — ambiguity is not resolved
- Hypothesis is updated incorrectly — the wrong verdict is assigned
- Hypothesis is deleted — the system loses the learning opportunity

#### Stage 9: Knowledge Extraction

**Input:** The terminal hypothesis with its complete lifecycle.

**Process:** The system extracts generalizable lessons:
- What specific prediction was tested?
- Was the prediction correct?
- What type of error occurred (if any)?
- Was this error type seen before?
- What condition determines whether this hypothesis works?
- Should the system form a new hypothesis based on this outcome?
- Should the system's confidence calibration be adjusted?
- Should source reliability be updated?

Knowledge is always provisional. It is a pattern extracted from one or more hypotheses, subject to revision when new evidence accumulates.

**Output:** One or more knowledge entries linked to the hypothesis.

**Failure modes:**
- Overgeneralization — extracting a broad lesson from a single outcome
- Undergeneralization — failing to extract any lesson
- Superstitious learning — extracting a lesson from noise

#### Stage 10: Criterion Update

**Input:** The knowledge extracted from this hypothesis, plus knowledge from all other hypotheses.

**Process:** The system updates its accumulated judgment:
- Calibration is adjusted (confidence vs. accuracy)
- Error type frequencies are updated
- Context-based priors are updated (what works in bull vs. bear markets)
- Evidence source reliability is updated
- Hypothesis quality metrics are recomputed

Criterion is not stored in a single place. It is distributed across the system's calibration, its error memory, its context awareness, and its priors.

**Output:** An updated system-wide criterion state.

**Failure modes:**
- Criterion does not change — the system did not learn
- Criterion changes too much — the system overfitted to a single outcome
- Criterion changes in the wrong direction — the system learned the opposite lesson

---

### 3.3 Self-Correction During Testing: A Critical Design Note

The lifecycle described above is a **simplified model**. In practice, one of the most important transitions is not shown in the basic linear flow: the ability to exit TESTING pre-emptively when evidence weakens during the test.

Level 4 of the Criterion framework (Self-Correcting) requires:

> *"The system detects when its own hypotheses are incorrect and adjusts before the outcome confirms the error. It identifies weakening evidence and reduces position size or exits before the loss."*

This means the system must be able to transition from TESTING back to ACTIVE (or directly to EVALUATED with a "pre-emptive exit" outcome) **before the time horizon expires**, based on incoming evidence that weakens the hypothesis.

**Implication:** The state machine must support:
- TESTING → ACTIVE (when evidence weakens but the hypothesis is not yet invalidated; the system exits the position and returns to monitoring)
- TESTING → EVALUATED (when evidence clearly contradicts the hypothesis and the position is closed as a pre-emptive rejection)

This is not a contradiction of the linear model. It is an extension required for Level 4 capability. The linear model is the standard path. Self-correction is the advanced capability.

---

## 4. Hypothesis States

### 4.1 State Definitions

| State | Definition | Can Knowledge Be Extracted? | Can Action Be Taken? |
|-------|-----------|----------------------------|---------------------|
| **CANDIDATE** | An idea has been identified but not yet structured into a testable form | No | No |
| **FORMULATED** | The hypothesis has been structured with testable prediction, invalidation conditions, and time horizon | No | Yes (monitoring) |
| **ACTIVE** | The system has committed to tracking this hypothesis. Evidence is being collected. | No | Yes (accumulating evidence) |
| **TESTING** | An action has been taken to test the hypothesis. An outcome is expected within the time horizon. Evidence continues to be monitored. If evidence weakens significantly, the system may exit pre-emptively (Level 4). | No | No (waiting for outcome or pre-emptive exit) |
| **EVALUATED** | The outcome has been observed. Comparison to prediction is underway. | No | No (analysis in progress) |
| **CONFIRMED** | The outcome aligns with the predicted consequence within tolerance. | Yes | No |
| **REJECTED** | The outcome contradicts the predicted consequence. | Yes | No |
| **INCONCLUSIVE** | The outcome does not clearly confirm or reject. | Partial | No |
| **ARCHIVED** | The hypothesis lifecycle is complete. Preserved for meta-analysis. | No | No |
| **RETIRED** | Lessons have been fully absorbed into criterion. | No | No |

### 4.2 State Transition Diagram

```
                    ┌─────────────┐
                    │  CANDIDATE  │
                    └──────┬──────┘
                           │ structured
                    ┌──────▼──────┐
                    │ FORMULATED  │◄──────────────┐
                    └──────┬──────┘               │
                           │ committed            │
                    ┌──────▼──────┐               │
                    │   ACTIVE    │───────────────┤
                    └──┬────┬─────┘  (irrelevant) │
                       │    │                     │
            action taken│    │evidence weakens    │
                       │    │(Level 4)            │
                    ┌──▼────▼─────┐               │
                    │  TESTING    │               │
                    └──┬────┬─────┘               │
                       │    │                     │
           outcome     │    │pre-emptive exit     │
           observed    │    │(evidence weakened)  │
                    ┌──▼────▼─────┐               │
                    │ EVALUATED   │               │
                    └──┬───┬───┬──┘               │
                       │   │   │                  │
              ┌────────┘   │   └────────┐         │
        ┌─────▼─────┐ ┌───▼────┐ ┌─────▼─────┐   │
        │ CONFIRMED │ │REJECTED│ │INCONCLUSIVE│───┤
        └─────┬─────┘ └───┬────┘ └─────┬─────┘   │
              │           │            │         │
              └─────┬─────┴──────┬─────┘         │
                    │            │                │
            ┌───────▼──┐  ┌─────▼──────┐         │
            │ ARCHIVED │  │  RETIRED   │         │
            └──────────┘  └────────────┘         │
                                                  │
              (INCONCLUSIVE may return to ACTIVE  │
               if new evidence or methodology     │
               allows a clearer test)            │
              (CONFIRMED/REJECTED may return      │
               to FORMULATED only if the original │
               hypothesis is restructured)        │
              (TESTING may return to ACTIVE when  │
               evidence weakens during testing —  │
               this is Level 4 Self-Correction)   │
```

### 4.3 Why These Transitions Exist

**CANDIDATE → FORMULATED:** A raw idea must be structured before it can be tested. Without this transition, the system acts on vague intuitions.

**FORMULATED → ACTIVE:** The system commits to tracking the hypothesis. This prevents the proliferation of untracked hypotheses that consume attention without producing evidence.

**ACTIVE → TESTING:** An action is the commitment to reality. Without action, a hypothesis remains speculation regardless of how much evidence accumulates.

**ACTIVE → ARCHIVED:** Some hypotheses become irrelevant without being tested (consequence already happened, market regime changed). Archiving preserves them for analysis without wasting attention.

**TESTING → EVALUATED:** The outcome is the critical feedback signal. Without evaluation, action teaches nothing.

**TESTING → ACTIVE (Level 4 Self-Correction):** If evidence weakens significantly during testing — the predicted consequence becomes less likely, invalidation conditions approach, or contradicting evidence accumulates — the system may exit the test pre-emptively. The position is closed. The hypothesis returns to monitoring. This transition is the defining capability of Criterion Level 4.

**EVALUATED → CONFIRMED/REJECTED/INCONCLUSIVE:** The verdict is the terminal scientific judgment. It determines what knowledge can be extracted.

**INCONCLUSIVE → ACTIVE:** An inconclusive result may warrant another test with better conditions or methodology.

**CONFIRMED/REJECTED → ARCHIVED:** Preservation allows meta-analysis across many hypotheses.

**ARCHIVED → RETIRED:** Lessons are absorbed into criterion. The hypothesis no longer needs to be individually accessible.

**RETIRED → ACTIVE:** Only if genuinely new evidence reopens a settled question. This should be rare.

---

## 5. Hypothesis Attributes

Every hypothesis is defined by the following attributes. These are scientific attributes, not database columns.

### 5.1 Identity and Origin

| Attribute | Description | Required? |
|-----------|-------------|-----------|
| **ID** | Unique identifier for the hypothesis | Always |
| **Title** | Concise, descriptive name | Always |
| **Description** | Full statement of the belief being tested | Always |
| **Origin Type** | How the hypothesis was created: event, pattern, correlation, human, meta-analysis | Always |
| **Origin Event(s)** | The specific events or observations that triggered this hypothesis | If applicable |
| **Domain** | Trading, creation, entrepreneurship, or other | Always |
| **Created At** | When the hypothesis was first formulated | Always |

### 5.2 Prediction and Scope

| Attribute | Description | Required? |
|-----------|-------------|-----------|
| **Predicted Consequence** | The specific future state the system expects | Always |
| **Prediction Specificity** | How precisely the consequence is defined: qualitative, directional, quantitative range, exact | Always |
| **Expected Magnitude** | The expected size of the consequence (e.g., 3–7% price movement) | If quantitative |
| **Time Horizon (Earliest)** | The minimum time before the consequence could materialize | Always |
| **Time Horizon (Expected)** | The most likely time for the consequence to materialize | Always |
| **Time Horizon (Latest)** | The maximum time before the hypothesis is considered expired | Always |
| **Invalidation Conditions** | Specific, measurable conditions that would disprove the hypothesis | Always |
| **Validation Conditions** | Specific, measurable conditions that would confirm the hypothesis | Always |
| **Context Scope** | The conditions under which this hypothesis is expected to hold (market regime, volatility regime, etc.) | Recommended |

### 5.3 Evidence State

| Attribute | Description | Required? |
|-----------|-------------|-----------|
| **Supporting Evidence** | Evidence that strengthens the hypothesis | Accumulated |
| **Contradicting Evidence** | Evidence that weakens the hypothesis | Accumulated |
| **Evidence Weight (Supporting)** | Cumulative weight of supporting evidence | Computed |
| **Evidence Weight (Contradicting)** | Cumulative weight of contradicting evidence | Computed |
| **Evidence Ratio** | supporting / (supporting + contradicting) | Computed |
| **Total Evidence Events** | Number of distinct evidence items tracked | Computed |

### 5.4 Confidence and Calibration

| Attribute | Description | Required? |
|-----------|-------------|-----------|
| **Confidence** | How likely the hypothesis is correct (0.0–1.0) | Always |
| **Confidence Uncertainty** | The uncertainty around the confidence estimate (± range) | Recommended |
| **Calibration Adjustment** | Historical bias adjustment for this type of hypothesis | Computed |
| **Source Reliability Score** | Weighted reliability of evidence sources | Computed |
| **Evidence Independence Score** | How independent the evidence sources are from each other | Computed |

### 5.5 Decision History

| Attribute | Description | Required? |
|-----------|-------------|-----------|
| **Decision Made** | Act, wait, monitor, ignore, reduce, replace | If applicable |
| **Decision Rationale** | Why this decision was made | Recommended |
| **Decision Confidence** | The confidence at the time of decision | If decision was made |
| **Action ID** | Reference to the action taken (trade, etc.) | If action was taken |
| **Action Type** | Trade, content publish, business decision, explicit non-action | If action was taken |

### 5.6 Outcome and Evaluation

| Attribute | Description | Required? |
|-----------|-------------|-----------|
| **Outcome** | What actually happened | After outcome |
| **Outcome vs Prediction** | Aligns, contradicts, aligns partially, ambiguous, external shock | After outcome |
| **Error Classification** | Decomposed error type(s) | After outcome |
| **Error Severity** | How significant the error was | After outcome |
| **Outcome Timing** | When the outcome occurred relative to time horizon | After outcome |

### 5.7 Knowledge and Criterion

| Attribute | Description | Required? |
|-----------|-------------|-----------|
| **Lessons Extracted** | Generalizable lessons from this hypothesis | After evaluation |
| **Knowledge Produced** | Knowledge entries linked to this hypothesis | After evaluation |
| **Related Hypotheses** | Other hypotheses affected by this outcome | Recommended |
| **Criterion Contribution** | How the system's judgment changed | After evaluation |
| **Calibration Impact** | How this updated the system's calibration | After evaluation |
| **Error Frequency Impact** | How this updated error type frequencies | After evaluation |

### 5.8 Lifecycle

| Attribute | Description | Required? |
|-----------|-------------|-----------|
| **Current Status** | Current state in the lifecycle | Always |
| **Status History** | Every state transition with timestamp and reason | Always |
| **Current Version** | Version number (hypotheses can be revised) | Always |
| **Derived From** | If this is a revision, which previous hypothesis version | If revision |
| **Retired At** | When the hypothesis was fully absorbed | After retirement |

---

## 6. Evidence

### 6.1 What Qualifies as Evidence

Evidence must satisfy all of these criteria:

1. **Relevance** — The information must be directly related to the hypothesis's predicted consequence or causal chain. A random price movement is not evidence unless it can be connected to the hypothesis.

2. **Specificity** — The information must be specific enough to support or contradict a specific claim. "The market is uncertain" is not specific. "VIX increased by 15% in one day" is specific.

3. **Source Attribution** — The source must be identifiable and trackable. Anonymous or unverifiable information is not evidence.

4. **Temporal Ordering** — The information must have a clear timestamp relative to the hypothesis. Evidence that arrives after the outcome is retrospective, not predictive.

5. **Measurability** — The information must be measurable in principle, even if the measurement is noisy.

### 6.2 What Does NOT Qualify

- Opinions without source attribution
- Predictions from untracked sources with no reliability history
- Information that is consistent with every possible outcome (tautology)
- Information that arrived after the outcome (hindsight)
- Noise — information statistically indistinguishable from random
- Gut feelings without supporting structure

### 6.3 Conflicting Evidence

Conflicting evidence is not a problem to be solved. It is information to be preserved.

When evidence conflicts:
- **Do not average.** Supporting and contradicting evidence are independent dimensions.
- **Do not discard.** The conflict itself is information — it tells the system that the hypothesis has high uncertainty.
- **Do track separately.** Maintain separate inventories of supporting and contradicting evidence.
- **Do investigate.** The nature of the conflict may reveal a missing variable or an incorrect assumption.

A hypothesis with 10 supporting items and 10 contradicting items is fundamentally different from a hypothesis with 0 of each. The first has high uncertainty. The second has no evidence at all.

### 6.4 Evidence Expiration

Evidence has a shelf life. The shelf life depends on:

- **Domain velocity** — In fast-moving domains (crypto trading), evidence may expire in days. In slow-moving domains (real estate), evidence may last years.
- **Regime stability** — Evidence from a different market regime may be misleading.
- **Source consistency** — A historically reliable source that suddenly changes methodology invalidates its previous evidence.

The system does not need a single formula for evidence decay. The decay rate should itself be a hypothesis that the system tests: *"Evidence older than X time units has Y% of its original predictive value."*

### 6.5 Evidence Weighting

Evidence should be weighted by:

- **Source reliability** — Weight × source_reliability_score. A source that is correct 90% of the time contributes more than a source that is correct 50% of the time.
- **Recency** — More recent evidence may be weighted higher. The decay function should be domain-specific.
- **Independence** — Three correlated sources should not count as three independent evidence items. Independence reduces the risk of false confirmation.
- **Specificity** — Precise evidence ("gold will move ±2%") is weighted higher than vague evidence ("gold may move").
- **Direction strength** — How strongly the evidence supports or contradicts. A price movement of +5% is stronger evidence for a bullish hypothesis than +0.5%.

### 6.6 Source Reliability

Source reliability is a measured property, not an assigned one. It is updated through the same lifecycle as hypotheses:

- Each source accumulates a track record of predictions vs. outcomes
- Reliability = proportion of correct predictions (calibrated for difficulty)
- Reliability is domain-specific (a source may be reliable for crypto but not for macro)
- Reliability is context-dependent (a source may be reliable in bull markets but not in bear markets)

A source with no track record has unknown reliability. The system should treat unknown reliability as low confidence, not as neutral.

### 6.7 Scientific Considerations for Evidence Management

#### 6.7.1 Bayesian Inference

The natural mathematical framework for evidence accumulation is Bayesian inference. Each piece of evidence updates the probability that a hypothesis is correct:

```
P(H|E) = P(E|H) * P(H) / P(E)
```

Bayesian updating provides a principled way to:
- Combine multiple pieces of evidence
- Weight evidence by its diagnosticity (how much it changes the probability)
- Handle prior beliefs and update them as evidence accumulates
- Quantify uncertainty after each update

The confidence assignment process (Stage 3) should be understood as an approximate Bayesian update, even if the implementation uses simplified heuristics.

**Caveat:** Bayesian inference assumes that the hypothesis space is well-defined and that prior probabilities can be assigned. In practice, both assumptions are approximations. The system should treat Bayesian confidence as a useful model, not as ground truth.

#### 6.7.2 Occam's Razor

Given two hypotheses that explain the same evidence equally well, the simpler one should be preferred. Simplicity is not a guarantee of correctness, but it is a useful prior:

- Simpler hypotheses have fewer free parameters and are harder to overfit
- Simpler hypotheses are easier to test and falsify
- Simpler hypotheses generalize better across contexts

The system should prefer simpler hypotheses when all other evidence is equal. This preference should be explicitly tracked as a prior, not applied as an unstated rule.

#### 6.7.3 Multiple Comparison Problem

When many hypotheses are tested simultaneously, some will be confirmed by chance alone. The system must account for this:

- If 100 hypotheses are tested at a 95% confidence level, approximately 5 will be "confirmed" by random chance
- The system should track the total number of hypotheses tested and adjust its confidence thresholds accordingly
- A hypothesis confirmed in isolation is less meaningful than a hypothesis confirmed when few others were being tested

The standard statistical correction (Bonferroni, Benjamini-Hochberg) should be applied when assessing whether a hypothesis is genuinely confirmed or likely to be a false positive.

#### 6.7.4 Hypothesis Generation

This document defines the lifecycle from CANDIDATE onward but does not fully specify how hypotheses are generated. The generation mechanism is itself an open question:

- **Event-driven:** A significant event triggers hypothesis formation (e.g., "Fed cut → what consequences?")
- **Pattern-driven:** A detected pattern in historical data triggers hypothesis formation (e.g., "RSI < 30 preceded bounces 6 times → is this a valid hypothesis?")
- **Correlation-driven:** A detected correlation between two variables triggers hypothesis formation
- **Human-driven:** A human operator defines a hypothesis manually
- **Meta-driven:** Knowledge extracted from past hypotheses generates new hypotheses

Each mechanism has trade-offs. Event-driven hypotheses are reactive but grounded. Pattern-driven hypotheses are proactive but may overfit. Human-driven hypotheses are high-quality but limited by human attention.

The generation mechanism should itself become a subject of hypothesis testing as the system matures.

---

## 7. Learning

### 7.1 How One Hypothesis Improves Another

Hypotheses do not exist in isolation. They form a web of relationships:

**Evidence sharing:** Evidence that supports or contradicts hypothesis A may also affect hypothesis B if they share a causal chain. The system should propagate evidence across related hypotheses.

**Context sharing:** If hypothesis A was confirmed in context X (bull market, high volatility), this raises the prior confidence for hypothesis B in the same context.

**Error pattern sharing:** If hypotheses A and B were both rejected due to "wrong timing," the system learns that its timing estimation needs improvement across both domains.

**Hierarchical relationship:** A higher-level hypothesis (e.g., "rising interest rates reduce tech stock valuations") generates lower-level hypotheses (e.g., "AAPL will decline 5% after the next rate decision"). When the lower-level hypothesis is confirmed, it strengthens the higher-level one. When it is rejected, it may refine the higher-level one (e.g., "the effect is 2%, not 5%").

**Competitive relationship:** When two hypotheses predict opposite consequences from the same events, they are in competition. The system should track which competitor is accumulating more supporting evidence. Competition accelerates learning.

### 7.2 Preserving Failed Hypotheses

A rejected hypothesis is not a wasted hypothesis. It is a hypothesis that produced evidence.

Failed hypotheses must be preserved because:
- **Error classification requires preservation.** The system cannot track error type frequencies if failures are deleted.
- **Calibration requires preservation.** The system cannot calibrate confidence without knowing when it was wrong.
- **Reversal is possible.** A hypothesis rejected today may be confirmed tomorrow if conditions change. The system needs the original formulation to compare.
- **Meta-learning requires preservation.** The system can only learn "what types of hypotheses fail" if it has access to failed hypothesis records.
- **Integrity requires preservation.** A system that deletes failures cannot be trusted to evaluate itself honestly.

The Law states: *"Errors must be preserved and classified, not hidden or ignored. A system that cannot acknowledge its failures cannot develop criterion."*

### 7.3 Why Failure Is Valuable

Each failure teaches the system one of these lessons:

- **The hypothesis was wrong.** The consequence does not follow from the events as predicted. The system learns that this causal chain is invalid in this context.
- **The evidence was insufficient.** The hypothesis may be correct, but the evidence at decision time did not justify action. The system learns to require stronger evidence.
- **The evidence was misleading.** The sources were wrong, or the correlations were spurious. The system learns to discount certain evidence types.
- **The timing was incorrect.** The consequence may materialize, but outside the predicted window. The system learns to calibrate time horizons.
- **The execution was poor.** The hypothesis and timing were correct, but the action was poorly sized or entered. The system learns to improve execution.
- **The context was wrong.** The hypothesis works in some contexts but not in this one. The system learns the boundary conditions.

### 7.4 How Repeated Failures Generate Better Criterion

A single failure is a data point. Repeated failures of the same type are a pattern.

When the system observes repeated failures of the same type:
- **It reduces confidence** in hypotheses of that type
- **It requires stronger evidence** before acting on similar hypotheses
- **It investigates the root cause** — is the failure in perception, judgment, timing, or execution?
- **It updates its priors** — "in this context, this type of hypothesis is unreliable"
- **It generates new hypotheses** — "why does this type of hypothesis consistently fail?"

The system that fails in the same way 100 times and never learns is not developing criterion. The system that fails in the same way 5 times, identifies the pattern, and stops repeating the error is developing criterion.

Criterion is not about avoiding failure. It is about **learning from failure faster than failure accumulates**.

---

## 8. Hypothesis Quality Metrics

These metrics measure the quality of individual hypotheses and the hypothesis ecosystem as a whole. They are diagnostic tools, not performance targets.

### 8.1 Calibration

**Definition:** The absolute difference between confidence and accuracy.
- **Formula:** |confidence - accuracy| for a set of hypotheses
- **Perfect:** 0.0 (confidence perfectly predicts accuracy)
- **Worst:** 1.0 (confidence and accuracy are opposites)
- **Interpretation:** Calibration below 0.1 is excellent. Calibration above 0.3 indicates systematic bias.

Calibration should be measured across confidence buckets: "When the system is 70% confident, is it right 70% of the time?" If not, the confidence assignment process needs adjustment.

### 8.2 Precision

**Definition:** Of the hypotheses the system confirmed, what proportion were actually correct?
- **Formula:** true_confirmed / (true_confirmed + false_confirmed)
- **Interpretation:** High precision means the system rarely confirms a false hypothesis. Low precision means the system confirms too many wrong hypotheses.

### 8.3 Recall

**Definition:** Of the hypotheses that were correct in reality, what proportion did the system identify?
- **Formula:** true_confirmed / (true_confirmed + false_rejected)
- **Interpretation:** High recall means the system captures most valid hypotheses. Low recall means the system misses many correct hypotheses.

Precision and recall must be balanced. High precision with low recall produces a timid system that misses opportunities. High recall with low precision produces a noisy system that acts on too many false hypotheses.

### 8.4 Survival Rate

**Definition:** The proportion of hypotheses that survive from FORMULATED to CONFIRMED at each confidence threshold.
- **Interpretation:** If 80% of hypotheses with confidence > 0.8 reach CONFIRMED but only 20% of hypotheses with confidence 0.6–0.8 reach CONFIRMED, the system's confidence thresholds are reasonable. If the survival rate is uniform across confidence levels, confidence is not informative.

### 8.5 Evidence Ratio

**Definition:** supporting_evidence_weight / (supporting + contradicting)
- **Range:** 0.0 (all evidence contradicts) to 1.0 (all evidence supports)
- **Interpretation:** A healthy hypothesis ecosystem should show a distribution of evidence ratios. A cluster of hypotheses with evidence ratio > 0.9 may indicate confirmation bias. A cluster with evidence ratio < 0.1 may indicate the system is acting despite strong contradictory evidence.

### 8.6 Prediction Accuracy

**Definition:** The proportion of hypotheses that reach a terminal state (CONFIRMED or REJECTED) that are confirmed.
- **Interpretation:** This is NOT the win rate. It includes hypotheses that were never acted upon. A prediction accuracy of 0.5 is the baseline for a binary hypothesis in a random environment. Above 0.6 indicates genuine predictive ability. Below 0.4 indicates systematic error.

### 8.7 Time-to-Validation

**Definition:** The average time from FORMULATED to EVALUATED across all hypotheses.
- **Interpretation:** Shorter validation times produce faster learning cycles. However, time-to-validation should be balanced against prediction accuracy. Fast but wrong is not learning.

### 8.8 Knowledge Yield

**Definition:** The average number of generalizable lessons extracted per hypothesis.
- **Formula:** total_lessons / total_hypotheses
- **Interpretation:** A knowledge yield of 0 means the system is not learning from its hypotheses. A knowledge yield above 1 indicates that hypotheses are producing compound lessons.

### 8.9 Criterion Contribution

**Definition:** The measurable improvement in system-wide calibration or decision quality that can be attributed to a hypothesis.
- **Measurement:** Compare system performance metrics before and after incorporating the hypothesis's lessons.
- **Interpretation:** This is the most important and most difficult metric. Over time, criterion contribution should compound: each hypothesis should contribute more than the previous one as the system's learning improves.

### 8.10 Error Type Frequency

**Definition:** The distribution of error types across all rejected or partially failed hypotheses.
- **Interpretation:** A system that consistently fails due to "wrong timing" should invest in timing calibration. A system that consistently fails due to "poor execution" should invest in execution. Declining frequency of a specific error type indicates learning.

### 8.11 Error Type Recurrence Rate

**Definition:** The proportion of hypotheses whose error type matches the modal error type of the previous N hypotheses.
- **Interpretation:** A recurrence rate that decreases over time indicates the system is learning from its errors. A recurrence rate that stays constant or increases indicates the system is not extracting the right lessons.

---

## 9. Complete Trading Example

### Hypothesis: "Fed Rate Cut Will Boost Gold"

**Background:** The Fed cut rates by 25bp. The MacroAgent detected the event. The MarketAgent detected a weak dollar the same day. Gold ETF inflows have been rising for 3 days.

**Stage 1 — Creation:**
> **Title:** Fed cut + weak dollar + gold inflows → gold rally
> **Prediction:** Gold (XAU/USD) will increase by 2–5% within 10 trading days
> **Invalidation:** Gold drops below the pre-announcement price within 5 days, or the dollar strengthens above pre-announcement levels
> **Context:** Normal volatility regime, no concurrent crises
> **Status:** FORMULATED

**Stage 2 — Evidence Collection:**
> **Supporting:** Fed cut confirmed (source: FRED, reliability: 0.95). Dollar index -0.4% (source: Yahoo Finance, reliability: 0.90). Gold ETF inflows +2.3% (source: CoinGecko, not applicable, using Bloomberg data, reliability: 0.85).
> **Contradicting:** Gold futures open interest declined 1.2% (source: CME, reliability: 0.95). One hawkish Fed comment noted (source: RSS news, reliability: 0.70).
> **Evidence Ratio:** 0.73

**Stage 3 — Confidence:**
> Confidence: 0.68 (adjusted from raw 0.72 by calibration factor of -0.04 for macro hypotheses)
> Uncertainty: ±0.12

**Stage 4 — Decision:**
> Decision: ACT — buy gold ETF (GLD)
> Rationale: Three independent signals converge. Invalidation conditions are clear. Risk budget available.
> Decision Confidence: 0.68

**Stage 5 — Action:**
> Action: Open long position in GLD, position size based on confidence (65% of maximum), stop loss at 2% below entry, target at +4%
> Linked Trade: trade_id = 1042

**Stage 6 — Outcome:**
> Day 7: Gold +3.1%. Target not yet hit. Time horizon still within range.
> Day 10: Gold +2.8%. Within predicted range.
> Outcome: CONFIRMED (within tolerance)

**Stage 7 — Error Analysis:**
> Error type: No significant error. The consequence was correctly predicted.
> Minor deviation: The +3.1% peak was higher than predicted; the +2.8% closing was within range.
> Learning opportunity: The system under-predicted the upside by approximately 0.5%. This is within noise but worth noting.

**Stage 8 — Knowledge Extraction:**
> Lesson 1: "Fed cuts combined with weak dollar and gold inflows predict a 2.8–3.1% gold increase within 10 days." (Confidence: Medium — single data point)
> Lesson 2: "The predictive accuracy was slightly better when all three signals converged than any single signal." (Confidence: Medium-Low — insufficient data for statistical significance)
> Lesson 3: "Confidence of 0.68 was reasonably calibrated — actual movement was within expected range." (Confidence: Medium — single data point)

**Stage 9 — Criterion Update:**
> Macro hypothesis calibration: Slightly improved (confidence 0.68 vs. actual accuracy, within tolerance)
> Evidence source reliability: FRED maintained at 0.95, Yahoo Finance maintained at 0.90, RSS news adjusted to 0.68 (hawkish comment was misleading)
> Error type frequency: No error to record
> Prior for similar hypotheses: Slightly increased for three-signal convergence patterns

---

## 10. Quality Metrics Summary

| Metric | What It Measures | Target | Current MVP Status |
|--------|-----------------|--------|-------------------|
| Calibration | Confidence vs. accuracy alignment | < 0.10 | Not measurable (no hypotheses) |
| Precision | False confirmation rate | > 0.75 | Not measurable (no hypotheses) |
| Recall | Missed hypothesis rate | > 0.60 | Not measurable (no hypotheses) |
| Survival Rate | Confidence informativeness | Increasing with confidence | Not measurable (no hypotheses) |
| Evidence Ratio | Evidence balance | 0.3–0.7 range | Not measurable (no evidence tracking) |
| Prediction Accuracy | Correct hypothesis proportion | > 0.55 | Not measurable (no hypotheses) |
| Time-to-Validation | Learning velocity | Domain-dependent | Not measurable (no hypotheses) |
| Knowledge Yield | Lessons per hypothesis | > 0.5 | Not measurable (no hypotheses) |
| Criterion Contribution | System improvement per hypothesis | Positive trend | Not measurable (no hypotheses) |
| Error Type Frequency | Dominant failure mode | Declining | Not measurable (no error classification) |
| Error Recurrence Rate | Learning from failure | Declining | Not measurable (no error classification) |

The status column reveals the critical gap: **none of these metrics can currently be measured because the MVP has no hypothesis lifecycle.** Every metric depends on hypotheses existing, being tracked, reaching verdicts, and producing knowledge.

---

## 11. Relationship to Existing Concepts

### 11.1 Connection to Events

Events trigger hypotheses. An event is data until it is interpreted through a hypothesis. The same event may trigger multiple competing hypotheses. Events that do not trigger any hypothesis are noise — they are processed but not learned from.

### 11.2 Connection to Correlations

Correlations suggest possible causal relationships. A correlation is not a hypothesis — it is an observation that may lead to a hypothesis. The hypothesis formalizes the correlation into a testable claim.

### 11.3 Connection to Clusters

A cluster is a group of events pointing toward the same consequence. A cluster strengthens a hypothesis by providing converging evidence. Multiple independent signals in a cluster reduce the probability that the hypothesis is based on spurious correlation.

### 11.4 Connection to Consequences

A consequence is the predicted future state. The hypothesis is the framework that connects current evidence to the predicted consequence. Without a hypothesis, "consequence" is a guess. With a hypothesis, "consequence" is a testable prediction.

### 11.5 Connection to Opportunities

An opportunity is a consequence that can be acted upon. The hypothesis is the bridge from "this consequence may happen" to "I should act on this belief." The hypothesis's confidence and evidence inventory determine whether the opportunity is actionable.

### 11.6 Connection to the Criterion Levels

| Criterion Level | Hypothesis Lifecycle Status |
|-----------------|----------------------------|
| **Level 0 — Reactive** | No hypotheses. Pure event-response. |
| **Level 1 — Pattern Recognition** | Patterns are recognized but not formalized into testable hypotheses. |
| **Level 2 — Contextual** | Patterns are context-dependent but still not formalized into hypotheses. |
| **Level 3 — Hypothesis-Driven** | **Hypotheses are formed, tracked, and tested. The lifecycle is operational.** |
| **Level 4 — Self-Correcting** | Hypotheses can be invalidated before outcomes arrive. Evidence weakening triggers pre-emptive action. |
| **Level 5 — Operational Criterion** | Hypothesis quality metrics are trending positive across all dimensions. Calibration is within tolerance. |
| **Level 6 — Strategic Criterion** | The system forms hypotheses about which hypotheses to pursue. The lifecycle applies to itself. |

The hypothesis lifecycle manager is the architectural requirement for reaching Level 3. Without it, the system cannot progress beyond Level 2.

### 11.7 Connection to the Laws

| Law | Implication for Hypothesis Lifecycle |
|-----|--------------------------------------|
| Law 1 — Every Event Has Consequences | Every event may generate a hypothesis about its consequences |
| Law 2 — Not Every Consequence Creates Opportunity | Hypothesis → opportunity threshold is explicit |
| Law 3 — Every Opportunity Originates from Consequences | Every opportunity must trace back to a hypothesis |
| Law 4 — Knowledge Without Outcomes Is Opinion | Only tested hypotheses produce knowledge |
| Law 5 — Learning Without Memory Is Impossible | Hypothesis memory must be structured and persistent |
| Law 6 — Criterion Cannot Exist Without Evidence | Evidence tracking per hypothesis is mandatory |
| Law 7 — Complexity Must Justify Itself | The hypothesis lifecycle must demonstrate learning improvement |
| Law 8 — Every Decision Leaves Evidence | Non-action decisions are recorded with the hypothesis |
| Law 9 — Everything Is Provisional | All hypotheses are subject to revision |
| Law 10 — No Idea Is Above Evidence | Evidence from hypothesis outcomes overrides all priors |

---

## 12. Open Questions

The following questions are not resolved by this document. They are hypotheses about the hypothesis lifecycle itself.

**Q-HLM-001: What is the optimal number of simultaneous active hypotheses?**
Too many hypotheses dilute evidence. Too few miss opportunities. The optimal number is unknown and likely context-dependent.

**Q-HLM-002: Should hypotheses compete or coexist in a hierarchy?**
Competition accelerates learning but may waste resources. Hierarchy preserves structure but may bias outcomes.

**Q-HLM-003: How should contradictory evidence be aggregated across a hypothesis network?**
Evidence for hypothesis A may affect hypothesis B. The propagation rules are not yet defined.

**Q-HLM-004: What is the minimum evidence threshold for a hypothesis to become ACTIVE?**
Without a threshold, the system may track too many noise hypotheses. With too high a threshold, valid hypotheses may be missed.

**Q-HLM-005: Can the hypothesis lifecycle be applied to itself?**
If the system can form hypotheses about its own hypothesis formation process, it enters Level 6 — Strategic Criterion. The criteria for this meta-level are not yet defined.

**Q-HLM-006: How should hypothesis quality metrics be validated?**
The metrics in Section 8 are theoretical. Each should be validated against long-term system performance before being treated as reliable indicators.

---

## 13. Relationship to Previous Documents

This document does not contradict the Manifesto, Theory, Laws, Constitution, Glossary, Criterion document, Discoveries, or Assumptions.

It is consistent with:
- **Theory Hypothesis 5** — "Every Hypothesis Is Provisional" — the lifecycle enforces provisionality through its state machine
- **Theory Hypothesis 6** — "Criterion Develops Through Validated Experience" — the lifecycle is the implementation of this cycle
- **Theory Hypothesis 7** — "Memory Enables Learning" — the lifecycle structures memory around hypotheses
- **Theory Hypothesis 8** — "Learning Requires Outcome-Based Feedback" — the lifecycle is feedback-driven
- **Glossary — Hypothesis** — the attributes defined here extend the glossary definition
- **Glossary — Evidence** — the evidence section here extends the glossary definition
- **Criterion Doc — What Produces Criterion** — the lifecycle operationalizes the interaction of memory, learning, hypotheses, evidence, outcomes, knowledge, context, and time
- **Discoveries — Discovery 3 (Hypothesis Tracking)** — this document is the full development of that discovery
- **Assumptions — A-007 (Explicit Hypotheses Outperform Implicit Intuition)** — the lifecycle is the implementation of this assumption
- **Constitution — Article 2 (Decision Process)** — the lifecycle enforces hypothesis-first decision-making
- **Criterion Readiness Audit (15_CRITERION_READINESS_AUDIT.md)** — the audit identifies the absence of the hypothesis lifecycle as the single largest gap. This document is the response to that gap.

---

## 14. Self-Review of This Document

This section evaluates the Hypothesis Lifecycle Manager document for internal consistency, weak assumptions, and potential contradictions.

### 14.1 Weak Assumptions

**Assumption 1: Explicit hypothesis tracking improves learning.** This is Assumption A-007 from the Assumptions document, currently untested. The entire lifecycle rests on this assumption. If falsified, the lifecycle adds complexity without benefit.

**Assumption 2: Evidence weight can be meaningfully computed.** Evidence weight depends on source reliability, independence, specificity, and direction strength. Each of these is an approximation. The system may compute weights that are systematically biased.

**Assumption 3: Error types are classifiable.** The error taxonomy proposed (wrong event, wrong correlation, wrong consequence, wrong timing, poor execution, external shock) assumes that outcomes can be decomposed into these categories. In practice, errors may be entangled. The same outcome may be simultaneously "wrong timing" and "poor execution."

**Assumption 4: Knowledge extracted from one context applies to another.** The lifecycle assumes that lessons learned from one hypothesis can be applied to future hypotheses. This requires the world to be sufficiently stable that past patterns inform future outcomes. If the world changes faster than the system learns, extracted knowledge becomes misleading.

### 14.2 Potential Circularities

**Hypothesis ↔ Learning:** The document defines the hypothesis as the unit of learning and then defines learning as the process of extracting patterns from hypothesis outcomes. This is not strictly circular — hypothesis is the container, learning is the process — but it means the system cannot learn without hypotheses and cannot improve hypotheses without learning. The cycle must be bootstrapped with initial hypotheses that may be poor.

**Confidence ↔ Calibration:** Confidence is assigned based on evidence. Calibration measures whether confidence matches accuracy. If calibration is poor, confidence assignment should change. But the document does not specify the feedback mechanism that adjusts confidence based on calibration. This is a gap, not a contradiction.

### 14.3 Conceptual Gaps

1. **Hypothesis generation is underspecified.** The lifecycle starts at CANDIDATE but does not define how candidates arise. Are they manually created? Generated by a pattern detector? Created by a meta-learning process? Each approach has different implications for the system's autonomy and learning velocity.

2. **Hypothesis capacity is undefined.** How many ACTIVE hypotheses can the system track? Is there a maximum? Does tracking degrade with more hypotheses? The document describes the lifecycle of a single hypothesis but not the ecosystem dynamics.

3. **Hypothesis competition is acknowledged but not designed.** When two hypotheses predict opposite consequences, how should the system manage them? Should both be tracked? Does one suppress the other? The document mentions competition (Section 7.1) but does not define a mechanism.

4. **The boundary between knowledge and criterion is not operationalized.** Knowledge is defined as extracted lessons. Criterion is defined as accumulated judgment. The document does not specify how knowledge becomes criterion — how individual lessons combine into general judgment.

### 14.4 Verdict

This document is a conceptual framework, not an implementation specification. It should be treated as a hypothesis about how criterion develops, not as a proven design. The strongest test of this document will be whether a system implemented according to its principles demonstrates measurable improvement in hypothesis quality, calibration, or error recurrence.

### 14.5 Recommended Modifications to Previous Documents

The following modifications to earlier documents are suggested based on insights from this document:

1. **Glossary (04_GLOSSARY.md)** — The definition of Hypothesis could be extended to include the lifecycle states defined in this document. The current glossary defines a hypothesis by its attributes but not by its lifecycle.

2. **Discoveries (03_DISCOVERIES.md) — Discovery 3 (Hypothesis Tracking)** — This discovery correctly identified hypothesis tracking as important. It could be updated to reference the full lifecycle defined here.

3. **Assumptions (10_ASSUMPTIONS.md) — A-007** — The assumption "Explicit Hypotheses Outperform Implicit Intuition" is the foundational bet of this document. It could be updated to reference the lifecycle framework.

4. **Criterion Document (08_CRITERION.md) — Level 3 (Hypothesis-Driven)** — The description of Level 3 could be expanded to reference the complete hypothesis lifecycle as the defining capability.

---

## 15. Final Principle

A hypothesis is not a prediction. It is not a belief. It is not a signal.

A hypothesis is a **testable question about reality, framed as a statement, with explicit conditions under which it would be proven wrong.**

The system that forms hypotheses, tests them, records outcomes, extracts lessons, and updates its judgment is not processing signals.

It is doing science.

The hypothesis lifecycle is the scientific method, expressed as an architectural principle.

*This document is itself a hypothesis. It is subject to revision when evidence accumulates against any of its claims.*

---

*End of 14_HYPOTHESIS_LIFECYCLE_MANAGER.md — Version 1.0 — June 2026*
