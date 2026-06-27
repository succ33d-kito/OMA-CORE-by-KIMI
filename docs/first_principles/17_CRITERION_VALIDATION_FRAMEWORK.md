# Criterion Validation Framework

## How O.M.A.-C.O.R.E. Scientifically Demonstrates That Judgment Improves Over Time

*Version 1.0 — June 2026*

---

## 0. Preamble

A system that claims to develop criterion must be able to prove it.

Not with philosophy. Not with intent. Not with architecture diagrams. With **repeatable, falsifiable evidence** that decision quality improves over time, independent of short-term outcome fluctuations.

This document defines how O.M.A.-C.O.R.E. will produce that evidence.

It does not describe how to build a validation system. It describes what must be measured, what counts as evidence, how to separate skill from luck, and what would falsify the claim that criterion is developing.

---

## PART I: Why Validation Matters

### 1.1 Why Better Outcomes Alone Are Insufficient

A system can produce better outcomes without developing criterion. This happens whenever:

- **Market conditions improve.** A system that trades the same way in a bull market will show better PnL than in a bear market. The system did not improve. The market did.
- **Risk increases.** A system that takes larger positions will show higher absolute returns (and higher absolute drawdowns). The system did not improve. Exposure did.
- **Luck intervenes.** A random system will show winning streaks and losing streaks. A winning streak is not evidence of learning.

Outcomes are the result of skill, luck, and environment interacting. Isolating skill from this interaction is the central validation challenge.

### 1.2 Why Profit Alone Is Insufficient

Profit confounds:
- Decision quality (did the system choose well?)
- Market direction (was the wind at its back?)
- Risk taken (was it compensated or uncompensated?)
- Position sizing (did allocation amplify or dampen returns?)
- Luck (did random events help or hurt?)

A profitable system may be a lucky system. An unprofitable system may be an unlucky system that is making good decisions. Profitability alone cannot distinguish between these.

### 1.3 Why Win Rate Alone Is Insufficient

Win rate measures the frequency of profitable outcomes but not:
- The magnitude of wins versus losses (a 40% win rate can be highly profitable if winners are 3x larger than losers)
- The quality of decisions (a system can win on luck and lose on skill)
- The risk taken to achieve wins (a 70% win rate achieved with wide stops and small targets may have negative expectancy)

### 1.4 Why Drawdown Alone Is Insufficient

Drawdown measures capital loss but not:
- Whether the losses were justified by the evidence available at entry
- Whether the system learned from the drawdown
- Whether the drawdown was caused by poor decisions or by reasonable decisions that encountered bad luck
- Whether the system adjusted its behavior after the drawdown

### 1.5 Why Prediction Accuracy Alone Is Insufficient

Prediction accuracy measures whether the system's forecasts matched reality but not:
- Whether the predictions were useful for decisions (a system that predicts "the market will go up or down" is always correct and never useful)
- Whether the predictions were well-calibrated (70% accuracy is meaningless if confidence was 95%)
- Whether the predictions were testable and falsifiable
- Whether the system learned from its prediction errors

### 1.6 The Four Components of Any Validated Decision

Every decision produces four distinct outcomes that must be evaluated independently:

| Component | Definition | Evaluated By | Confused With |
|-----------|-----------|--------------|---------------|
| **Good Decision** | The choice was justified by the evidence available at the time | Reasoning quality, evidence use, hypothesis competition | Outcome |
| **Good Outcome** | The result was favorable | PnL, win/loss, risk-adjusted return | Decision quality |
| **Good Process** | The system followed its own methodology consistently | Methodology adherence, rule compliance, documentation | Outcome |
| **Good Learning** | The system improved from the experience | Future decision quality, calibration change, error reduction | All of the above |

These four components are independent:
- A good decision can produce a bad outcome (correct hypothesis, external shock)
- A bad decision can produce a good outcome (lucky guess)
- A good process can produce a bad decision (correct methodology applied to misleading evidence)
- A good outcome can produce no learning (profit with no reflection)
- A good learning event can be triggered by a bad outcome (profitable loss)

Validation must measure all four. Any system that measures only one will draw incorrect conclusions about its own performance.

---

## PART II: What Is Being Measured

### 2.1 Operational Definition of Criterion

Criterion is defined conceptually in 08_CRITERION.md as *"the accumulated ability to judge what matters."*

For validation purposes, this must be made operational:

**Criterion is the system's demonstrated ability to reduce uncertainty before allocating scarce resources, measured by converging evidence across reasoning quality, decision quality, and outcome quality over time.**

This definition has five components that must all be present for criterion to be claimed:

1. **Demonstrated** — observable in repeatable measurement, not inferred from architecture
2. **Reduce uncertainty** — the system makes decisions with progressively less uncertainty relative to the stakes
3. **Before allocating scarce resources** — the improvement is in the decision process, not in post-hoc rationalization
4. **Converging evidence** — improvement must be shown across multiple independent layers simultaneously
5. **Over time** — single events are never sufficient; trends across many cycles are required

### 2.2 What Criterion Is Not

| Misconception | Correction |
|---------------|------------|
| Criterion is profit | Profit is an outcome. Criterion is the ability that produces (some) profit. They correlate over long time horizons but are not identical. |
| Criterion is accuracy | A system can be accurate by predicting only high-probability events and missing all others. Criterion includes knowing when to act and when to refrain. |
| Criterion is confidence | Confidence is an estimate. Criterion is the accumulated ability that makes estimates well-calibrated. |
| Criterion is memory | Memory is storage. Criterion is the ability to use stored experience to judge new situations. |
| Criterion is knowledge | Knowledge is extracted lessons. Criterion is the integration of all lessons into consistent judgment. |

### 2.3 Scarce Resources That Decisions Allocate

Every decision allocates one or more scarce resources. The quality of allocation is a dimension of criterion.

| Resource | How Criterion Improves Allocation |
|----------|----------------------------------|
| **Capital** | Better capital allocation across opportunities. Higher conviction receives more capital. Lower conviction receives less. |
| **Time** | Less time spent on noise. More time spent on emerging consequences that matter. |
| **Attention** | Attention directed toward the most informative evidence, not the most salient. |
| **Knowledge** | Knowledge applied to the situations where it is relevant, not generalized where it is not. |
| **Trust** | Trust allocated to evidence sources proportionally to their demonstrated reliability. |
| **Relationships** | In non-trading profiles, relationships prioritized by consequence relevance. |
| **Mobility** | Faster recognition of when to change course, enter, or exit. |
| **Health** | In the long-term, recognition of when system operation should be paused or slowed to prevent degradation. |
| **Freedom of Action** | Decisions that preserve optionality when uncertainty is high. Commitment when uncertainty is low. |

The system's ability to allocate these resources more efficiently over time is direct evidence of criterion development.

### 2.4 The Principle of Converging Evidence

Criterion cannot be measured by a single metric. Any single metric can be gamed, confounded, or produced by random chance.

Criterion development is demonstrated when **multiple independent evidence streams converge** on the same conclusion: the system's judgment is improving.

The three layers that must converge are defined in Part III. The principle is:

> *Criterion should only be considered improved when all validation layers improve together.*

- Improved outcomes alone are insufficient (could be luck or market conditions).
- Improved reasoning alone is insufficient (could be irrelevant if it does not translate to decisions).
- Improved decisions alone are insufficient (could be irrelevant if they do not translate to outcomes over time).
- Improved reasoning + improved decisions + improved outcomes over sufficient time = scientific evidence that criterion has evolved.

---

## PART III: The Five Layers of Validation

### 3.1 The Validation Hierarchy

Criterion validation operates across five layers. Each layer answers a different question. No layer can replace another.

```
Layer 1: Reasoning Quality
  │  Was the thinking sound?
  ▼
Layer 2: Decision Quality
  │  Was the choice justified?
  ▼
Layer 3: Execution Quality
  │  Was the action carried out correctly?
  ▼
Layer 4: Outcome Quality
  │  What happened?
  ▼
Layer 5: Learning Quality
  │  Did the system improve afterward?
```

### 3.2 Layer 1 — Reasoning Quality

**Question answered:** Was the internal reasoning coherent, evidence-driven, and well-structured?

**What is evaluated:**

| Dimension | What to Look For |
|-----------|-----------------|
| **Question quality** | Was the right question asked? Was it specific, testable, and decision-relevant? |
| **Hypothesis generation** | Were multiple competing hypotheses generated? Or was only one explanation considered? |
| **Hypothesis diversity** | Were the hypotheses genuinely different, or were they minor variations of the same idea? |
| **Evidence selection** | Was the evidence relevant to the hypotheses? Was it specific or vague? |
| **Evidence weighting** | Was evidence weighted by source reliability, recency, and independence? |
| **Confidence calibration** | Did the system's confidence match the strength of the evidence? |
| **Falsifiability** | Were invalidation conditions specified before the outcome was known? |
| **Scenario generation** | Were expected consequences and contradictory scenarios considered? |
| **Uncertainty acknowledgment** | Did the system identify what it did not know? |
| **Confirmation bias defense** | Was contradictory evidence actively sought, not passively accepted? |

**How it improves over time:**
- Questions become more specific and decision-relevant
- Hypotheses become more precise and testable
- More competing hypotheses are generated per decision
- Evidence selection becomes more discriminating
- Confidence estimates converge toward actual accuracy

**Measurement approach:** Before-action reasoning records are scored against a standardized rubric. The rubric should be designed to resist gaming — it evaluates structure and rigor, not whether the conclusion was correct.

### 3.3 Layer 2 — Decision Quality

**Question answered:** Given only the information available at the time of the decision, was this the best possible choice?

**What is evaluated:**

| Dimension | What to Look For |
|-----------|-----------------|
| **Evidence-decision alignment** | Did the decision follow from the evidence presented? Or was there a gap between evidence and action? |
| **Proportionality** | Was resource allocation proportional to conviction? Did high-conviction decisions receive more capital? |
| **Alternatives considered** | Were alternative courses of action explicitly evaluated and rejected with reasons? |
| **Uncertainty handling** | Was uncertainty acknowledged in the decision? Were mitigation measures in place? |
| **Timing** | Was the decision made at the right time? Not too early (before sufficient evidence) and not too late (after the opportunity passed)? |
| **Reversibility** | Was the decision's reversibility considered? Were irreversible decisions held to a higher standard? |
| **Expert defensibility** | Would a domain expert consider this a defensible decision given the evidence available at the time? |

**Why good decisions sometimes lose:**
The world contains irreducible randomness. A decision can be excellent given the available evidence and still produce a loss because an unpredictable event intervenes. This is not a failure of decision quality. It is a feature of operating under uncertainty.

**Why bad decisions sometimes win:**
A decision can be poor and still produce a profit if the system gets lucky. A hypothesis with weak evidence and no invalidation conditions can be confirmed by random price movement. This is not validation of the decision.

**Measurement approach:** Decisions are evaluated retrospectively using only the information available at decision time. The evaluator (human or automated) must be blinded to the outcome to avoid outcome bias. A panel of independent evaluators or a structured scoring system can be used.

### 3.4 Layer 3 — Execution Quality

**Question answered:** Was the decision executed correctly, or were operational errors introduced?

**What is evaluated:**

| Dimension | What to Look For |
|-----------|-----------------|
| **Fidelity** | Was the action executed as intended? Were there slippage, timing, or sequencing errors? |
| **Calibration** | Were position sizes, stop losses, and targets set as planned? |
| **Timing** | Was execution timely? Did delays affect the outcome? |
| **System integrity** | Did all system components function correctly during execution? |
| **Operational noise** | Were there data errors, API failures, or infrastructure issues that affected execution? |

Execution quality is separated from decision quality because a correct decision can be poorly executed and an incorrect decision can be well-executed. These must be evaluated independently to determine where the system's failures actually occur.

### 3.5 Layer 4 — Outcome Quality

**Question answered:** What happened, and was it consistent with the hypothesis?

**What is evaluated:**

| Dimension | What to Look For |
|-----------|-----------------|
| **PnL** | Was the trade profitable? By how much? |
| **Hypothesis alignment** | Did the outcome match the predicted consequence? |
| **Risk-adjusted return** | Was the return commensurate with the risk taken? |
| **Time efficiency** | Was capital deployed for an appropriate duration? |
| **Opportunity cost** | Did this position prevent capturing a better opportunity? |

**Why outcomes alone never prove criterion:**
A single outcome (or even a sequence) can be produced by luck. A coin flipped 10 times can produce 8 heads. The coin did not improve. The same applies to a trading system. Only when outcomes are evaluated across many decisions, in conjunction with reasoning and decision quality, do they become evidence of criterion.

**Measurement approach:** Standard trading metrics (win rate, profit factor, Sharpe, max drawdown) are necessary but not sufficient. They must be trended over time and compared against expected distributions under the null hypothesis (no skill).

### 3.6 Layer 5 — Learning Quality

**Question answered:** Did the system improve as a result of this experience?

**What is evaluated:**

| Dimension | What to Look For |
|-----------|-----------------|
| **Memory update** | Was the outcome stored with its hypothesis, evidence, and decision trace? |
| **Error classification** | Was the error (if any) classified by type? |
| **Knowledge extraction** | Was at least one generalizable lesson extracted? |
| **Calibration update** | Was the system's confidence calibration adjusted based on this outcome? |
| **Hypothesis improvement** | Did the system's hypotheses become more precise or testable after this experience? |
| **Error type tracking** | Was this error type recorded in the system's error frequency history? |
| **Process adjustment** | Did the system change its behavior based on what it learned? |

Learning quality is the most important layer because it determines whether the system compounds its experience or merely accumulates it. A system that captures every trade outcome but never extracts lessons is not learning — it is storing.

**How it improves over time:**
- Error classification becomes more precise
- Knowledge extraction becomes faster and more reliable
- Error type frequencies decline for previously identified errors
- Calibration improves
- Hypotheses require fewer outcomes to reach statistical significance

---

## PART IV: The Criterion Score

### 4.1 Purpose

The Criterion Score is not a formula. It is a **multi-dimensional profile** that collectively indicates whether criterion is developing. No single number captures criterion. Any attempt to reduce criterion to a scalar would produce a target that the system could optimize at the expense of genuine judgment.

### 4.2 Dimensions

Each dimension is measured independently. Improvement is demonstrated when multiple dimensions trend positively over time.

**Reasoning Quality:**
The coherence, rigor, and completeness of the system's reasoning before action. Includes question quality, hypothesis diversity, evidence selection, and falsifiability.

**Evidence Quality:**
The relevance, specificity, independence, and source reliability of evidence used to support hypotheses. Improving evidence quality means the system uses more informative evidence, not more evidence.

**Hypothesis Quality:**
The precision, testability, and falsifiability of hypotheses. Improving hypothesis quality means hypotheses become more specific, more measurable, and more clearly invalidatable.

**Calibration:**
The alignment between confidence and accuracy. Improving calibration means the system's confidence estimates converge toward actual outcome frequencies. Well-calibrated: 70% confidence → right 70% of the time.

**Decision Utility:**
The extent to which decisions improve the system's position relative to its goals, adjusted for the quality of information available. Not the same as outcome quality — decision utility evaluates the decision given what was known.

**Error Recovery:**
The speed and completeness with which the system recovers from errors. Includes error recognition time, error classification accuracy, and behavior change after the error. Improving error recovery means the system makes fewer repeated errors.

**Learning Velocity:**
The rate at which the system extracts knowledge from outcomes. Measured by knowledge entries per hypothesis, time from outcome to knowledge extraction, and applicability of extracted knowledge to future decisions.

**Pattern Evolution:**
The refinement of patterns over time. Patterns should become more context-specific, more precisely quantified, and more robust across different conditions. Static patterns indicate no learning.

**Resource Efficiency:**
The amount of uncertainty reduction achieved per unit of scarce resource consumed (capital, time, attention). Improving resource efficiency means the system achieves the same or better decisions with fewer resources.

**Adaptability:**
The system's ability to recognize when conditions have changed and adjust its behavior accordingly. Includes regime detection speed, pattern retirement, and hypothesis regeneration after regime change.

**Decision Compression:**
The system's ability to make high-quality decisions with progressively less evidence over time. Compression is evidence that patterns have been internalized into reliable heuristics. It should be measured against a quality-adjusted baseline — compression without quality degradation is improvement.

### 4.3 How the Dimensions Interact

The dimensions are not independent. They interact in predictable ways:

- Improving **hypothesis quality** tends to improve **calibration** because more precise hypotheses produce more measurable outcomes.
- Improving **error recovery** tends to improve **learning velocity** because classified errors produce clearer lessons.
- Improving **calibration** tends to improve **decision utility** because well-calibrated confidence leads to better resource allocation.
- Improving **adaptability** may temporarily reduce **resource efficiency** because recognizing a regime change requires attention.
- Improving **decision compression** should be validated against **reasoning quality** to ensure compression is not skipping necessary rigor.

No single dimension is sufficient. Only when multiple dimensions trend positively together is criterion development scientifically demonstrable.

### 4.4 What Would Count as a Positive Trend

For each dimension, a positive trend is:

- **Statistically significant** — the improvement exceeds what would be expected from random variation
- **Sustained** — the improvement persists across multiple measurement periods (quarters, not days)
- **Robust across conditions** — the improvement holds in different market regimes, not just favorable ones
- **Attributable** — the improvement can be linked to specific changes in the system's process (better hypotheses, better evidence use, better calibration)

---

## PART V: Separating Skill from Luck

### 5.1 The Fundamental Problem

Every outcome is produced by three factors:

```
Outcome = Skill + Luck + Environment
```

- **Skill** — the system's actual decision-making ability
- **Luck** — random factors that influence outcomes
- **Environment** — market conditions, regime, external events

The validation problem is to estimate the skill component independently from luck and environment.

### 5.2 Why Separation Is Required

Without separating skill from luck:

- A profitable streak is interpreted as skill improvement when it may be luck
- A losing streak is interpreted as skill degradation when it may be bad luck
- A bull market makes every system look skilled
- A bear market makes every system look unskilled
- The system cannot accurately evaluate itself

### 5.3 Methods for Separation

**Repeated observation:**
Skill and luck can be distinguished only through repeated observation. A single outcome (or a small sample) cannot separate them. The Law of Large Numbers requires sufficient observations before skill becomes distinguishable from luck.

**Statistical expected distribution:**
If the system has no skill, its outcomes follow a known distribution determined by randomness and market conditions. If the system's outcomes significantly deviate from this distribution in the favorable direction, skill is plausible.

**A/B comparison:**
Run two versions of the system simultaneously: one that makes decisions using the hypothesis lifecycle and one that makes random or baseline decisions. The lifecycle version should outperform the baseline version over sufficient time. This controls for environmental factors.

**Historical replay:**
Replay past decisions against historical data. If the system would have made different (better) decisions with its current knowledge compared to its past self, this is evidence of learning.

**Counterfactual analysis:**
After an outcome, ask: "What would have happened if the system had made a different decision?" This estimates the quality of the decision that was actually made relative to alternatives.

**Blind replay:**
Present historical situations to the system without revealing the actual outcome. Compare the system's decisions to what actually happened. This tests whether the system can recognize situations it has seen before.

**Self-comparison across versions:**
Compare the system's current performance against its own past performance at different points in its development. If the system with 12 months of experience outperforms the system with 1 month of experience, learning has occurred.

### 5.4 Confounding Factors to Control For

**Survivorship bias:** Evaluating only surviving positions or strategies biases the analysis toward positive outcomes. All decisions — including those that were rejected, abandoned, or resulted in losses — must be included.

**Outcome bias:** Evaluating decision quality based on outcome rather than on the information available at decision time. This is controlled by evaluating decisions before outcomes are known, or by blinding evaluators to outcomes.

**Overfitting:** The system's knowledge may be specific to past data and not generalize to future conditions. This is controlled by validating on out-of-sample data.

**Regime dependence:** The system may perform well only in specific market conditions. This is controlled by evaluating across multiple market regimes and reporting performance per regime.

**Data snooping:** The system may have been indirectly exposed to future data during development. This is controlled by strict temporal separation between training/development data and validation data.

### 5.5 The Null Hypothesis

The null hypothesis for criterion validation is:

> *The system's decision quality does not improve over time. Any observed improvement is attributable to random chance, changing market conditions, or increasing data volume rather than genuine learning.*

To reject this null hypothesis, the system must demonstrate that improvements are:
1. Statistically significant (p < 0.05, adjusted for multiple comparisons)
2. Robust across different market conditions
3. Attributable to specific learning mechanisms (better hypotheses, better calibration, better evidence use)
4. Reproducible in out-of-sample testing

---

## PART VI: What Data Must Be Stored

### 6.1 The Complete Scientific Record

For every important decision, the system must preserve a complete reasoning record. This record is the raw material for all criterion validation.

| Field | Why It Matters |
|-------|----------------|
| **Context** | Enables evaluation of whether the system recognized the situation correctly. Without context, decisions cannot be compared across time. |
| **Need** | Documents why a decision was necessary. Without this, the system cannot evaluate whether it is acting on noise or signal. |
| **Question** | Frames the inquiry. Question quality is a criterion dimension. Without the question, the quality of the answer cannot be evaluated. |
| **Hypotheses Generated** | Records what the system considered. Without this, hypothesis diversity and competition cannot be measured. |
| **Hypotheses Rejected** | Documents what the system considered and discarded. This is critical for evaluating whether the system prematurely discarded valid alternatives. |
| **Evidence Used** | Records what evidence informed the decision. Without this, evidence quality cannot be evaluated. |
| **Evidence Ignored** | Documents what the system consciously chose not to use. This is critical for evaluating whether the system dismissed relevant evidence. |
| **Confidence** | Records what the system believed at decision time. Without this, calibration cannot be measured. |
| **Conviction** | Records how strongly the system acted on its belief. Without this, decision utility cannot be evaluated. |
| **Expected Scenario** | Documents what the system predicted would happen. Without this, hypothesis alignment cannot be measured. |
| **Expected Consequences** | Documents the specific outcomes the system expected. Without this, prediction specificity cannot be evaluated. |
| **Decision** | The choice made. |
| **Action** | How the decision was executed. Without this, execution quality cannot be evaluated. |
| **Outcome** | What actually happened. |
| **Unexpected Events** | Documents external factors that affected the outcome. Without this, the system cannot distinguish between decision failure and environmental disruption. |
| **Reasoning Review** | The system's evaluation of its own reasoning. Without this, self-correction cannot be measured. |
| **Error Classification** | Type of error that occurred (if any). Without this, error type frequencies cannot be tracked. |
| **Knowledge Produced** | Lessons extracted. Without this, learning quality cannot be measured. |
| **Criterion Change** | How this decision affected the system's accumulated judgment. |
| **Future Recommendation** | What the system would do differently next time. |

### 6.2 Why Preserving the Reasoning Process Is More Valuable Than Preserving the Outcome Alone

An outcome is a single number: win or loss, profit or loss, correct or incorrect.

A reasoning process contains:
- The structure of the inquiry (question, hypotheses, evidence)
- The state of knowledge at the time (what was known and unknown)
- The decision calculus (how evidence led to decision)
- The learning that occurred (what was extracted from the outcome)

A database of outcomes can tell you whether the system was profitable. A database of reasoning processes can tell you *why* the system was profitable, *whether* it is learning, and *how* it can improve.

### 6.3 Storage Requirements

The reasoning record must be:
- **Immutable** — Once recorded, it cannot be altered. This prevents hindsight bias in evaluation.
- **Temporal** — Every entry carries a timestamp. This enables longitudinal analysis.
- **Queryable** — Records can be searched by context, hypothesis, error type, knowledge produced, and other dimensions.
- **Complete** — Every important decision is recorded. Selective recording would bias validation.

---

## PART VII: Trading as the First Laboratory

### 7.1 Why Trading Is the First Validation Domain

Trading is the initial validation domain because it provides:

- **Fast feedback** — Hours to days, not months to years
- **Unambiguous outcomes** — Profit and loss are measurable
- **Abundant data** — Thousands of cycles can be accumulated in months
- **Clear consequence chain** — Event to hypothesis to action to outcome is observable
- **Objective measurement** — No subjective interpretation of "was this decision correct?"

Trading is a laboratory, not an identity. The purpose is to develop and validate the criterion framework in a favorable environment before expanding to other domains.

### 7.2 Trading Metrics vs. Criterion Metrics

Both sets of metrics are necessary. They answer different questions.

**Trading metrics answer:** "Is the system profitable and well-behaved?"

| Metric | What It Measures |
|--------|-----------------|
| Win Rate | Proportion of profitable trades |
| Profit Factor | Gross profit / gross loss |
| PnL | Net profit or loss |
| Sharpe Ratio | Risk-adjusted return |
| Maximum Drawdown | Largest peak-to-trough decline |
| Exposure Time | Proportion of time capital is deployed |
| Capital Efficiency | Return per unit of capital deployed |
| Opportunity Capture Rate | Profitable opportunities acted upon / total profitable opportunities that existed |

**Criterion metrics answer:** "Is the system developing better judgment?"

| Metric | What It Measures |
|--------|-----------------|
| Hypothesis Quality | Precision, testability, falsifiability of hypotheses over time |
| Reasoning Quality | Coherence, rigor, completeness of reasoning before action |
| Decision Quality | Justifiability of decisions given available evidence |
| Calibration | Alignment between confidence and accuracy |
| Error Reduction | Decline in error type frequencies over time |
| Question Quality | Specificity, relevance, and testability of questions asked |
| Learning Velocity | Rate of knowledge extraction from outcomes |
| Confidence Accuracy | Improvement in confidence calibration across time |

### 7.3 Why Both Are Necessary

Trading metrics without criterion metrics tell you whether the system is making money but not whether it is learning. A system that is profitable today but not learning will eventually be overtaken by changing market conditions.

Criterion metrics without trading metrics tell you whether the system is learning but not whether the learning is operationally valuable. A system that improves its reasoning but does not improve its outcomes is learning something irrelevant.

Both sets of metrics must trend positively for the system to be developing operational criterion.

---

## PART VIII: Proving Improvement

### 8.1 Validation Experiments

The following experiments are designed to produce falsifiable evidence for or against criterion development.

**21-Day Validation:**
Run the system for 21 consecutive trading days. Compare the first 10 decisions against the second 10 decisions across all five validation layers. Improvement in layers 1–3 (reasoning, decision, execution) is expected within this window. Layer 4 (outcome) may not show statistically significant improvement due to small sample size. Layer 5 (learning) should show measurable knowledge extraction.

**Success:** Reasoning quality improves from the first 10 to the second 10 decisions. Knowledge is extracted from at least 50% of outcomes.

**Failure:** No measurable improvement in any layer. No knowledge extracted.

**90-Day Validation:**
Run the system for 90 consecutive trading days. The larger sample size allows statistical evaluation of all five layers. Outcomes should show improvement after controlling for market conditions.

**Success:** Improvement in at least 3 of 5 validation layers, with statistical significance (p < 0.10). Error type frequencies begin to decline.

**Failure:** Improvement in 1 or fewer layers. Error frequencies are flat or increasing.

**Rolling Validation:**
Compute all criterion metrics on a rolling basis (e.g., 30-trade window, sliding by 1 trade). This produces a time series of criterion development that can be analyzed for trends, plateaus, and regime dependence.

**Success:** A statistically significant positive trend in at least 4 of 11 Criterion Score dimensions over the observation period.

**Failure:** No positive trend in any dimension. Negative trend in 2 or more dimensions.

**A/B Reasoning Comparison:**
Run two instances of the system simultaneously. Instance A uses the full hypothesis lifecycle (competing hypotheses, evidence tracking, error classification). Instance B uses a simplified baseline (single hypothesis, no evidence tracking, no error classification). Compare their criterion metrics over the same time period.

**Success:** Instance A outperforms Instance B on at least 4 of 11 Criterion Score dimensions.

**Failure:** Instance A does not outperform Instance B on any dimension. This would falsify the hypothesis that the lifecycle improves criterion (Assumption A-007).

**Historical Replay:**
Take past market situations that the system encountered, and present them to the current system. Compare the current system's decisions to the decisions it made at the time. If the current system makes better decisions, learning has occurred.

**Success:** The current system outperforms its past self on at least 3 of 5 validation layers.

**Failure:** No improvement, or the current system performs worse (indicating degradation or overfitting).

**Blind Replay:**
Present historical market situations without revealing the outcome. Ask the system to form hypotheses and make decisions. Compare these decisions to what actually happened. This tests whether the system has learned to recognize patterns from past experience.

**Success:** Decision accuracy exceeds chance levels, with the gap widening as the system gains more experience.

**Failure:** Decision accuracy is at chance levels regardless of experience.

**Counterfactual Analysis:**
After each outcome, simulate what would have happened under alternative decisions. This estimates the opportunity cost of the chosen action and provides a counterfactual baseline for evaluating decision quality.

**Success:** The system's chosen actions consistently outperform counterfactual alternatives.

**Failure:** Counterfactual alternatives consistently outperform the system's actual decisions.

**Expert Comparison:**
Compare the system's decisions against those of human experts (or a benchmark model) on the same situations. The system should demonstrate comparable or improving decision quality relative to the benchmark.

**Success:** The system's criterion metrics converge toward or exceed the benchmark's over time.

**Failure:** The system's relative performance does not improve.

**Self-Comparison Across Versions:**
As the system evolves, run old versions against new versions on the same historical data. This directly measures whether newer versions have learned from the experience of older versions.

**Success:** Each successive version outperforms previous versions on criterion metrics.

**Failure:** Version performance is flat or degrades.

### 8.2 Failure Conditions

The system fails validation when:

1. **No improvement in any validation layer** after 90 days of operation with a minimum of 30 decisions.

2. **Improvement in outcomes but degradation in reasoning or learning quality.** This indicates the system is getting lucky, not getting better.

3. **Improvement in reasoning but not in outcomes after 180 days.** This indicates the system is learning something that does not translate to operational decisions.

4. **Calibration does not improve.** The system's confidence estimates remain as inaccurate after 100 decisions as after 10.

5. **Error type frequencies are flat or increasing.** The system is repeating its mistakes.

6. **Learning quality metrics are zero.** No knowledge is extracted from any outcome.

7. **Performance degrades when conditions change.** The system cannot adapt to new regimes and repeats errors from previous regimes.

### 8.3 Success Conditions

The system passes validation when:

1. **All five validation layers show positive trends** over a 90-day validation period.

2. **Calibration improves** by a statistically significant margin. Confidence estimates converge toward actual accuracy.

3. **Error type frequencies decline** for the most common error types.

4. **Knowledge is being extracted** from at least 70% of outcomes.

5. **Improvements are robust across market conditions.** The system performs better in a bear market after having learned in a bull market (or vice versa).

6. **Improvements are attributable** to specific changes in reasoning, hypothesis formation, evidence evaluation, or calibration — not to external factors.

---

## PART IX: Autonomy Validation

### 9.1 Autonomy Must Be Earned

O.M.A.-C.O.R.E. must never receive autonomy by assumption. Autonomy is granted progressively as the system demonstrates criterion at each level.

The levels are cumulative. Level N requires that all previous levels have been validated.

### 9.2 Progressive Autonomy Levels

**Level 0 — Observation:**
The system observes the world and records what it sees. It makes no recommendations and takes no actions.

*Evidence required:* None. This is the starting state.

**Level 1 — Recommendation:**
The system may generate recommendations (hypotheses, opportunity candidates) but cannot act on them. Decisions are made by a human or higher-level system.

*Evidence required:* Demonstrated ability to generate testable, falsifiable hypotheses. At least 10 hypotheses with defined invalidation conditions and time horizons.

**Level 2 — Prioritization:**
The system may rank and prioritize recommendations but cannot execute them. It indicates which opportunities it considers most valuable and why.

*Evidence required:* Demonstrated ability to score and rank opportunities. At least 30 decisions worth of hypothesis-outcome data showing that the system's rankings correlate with actual outcomes better than chance (p < 0.10).

**Level 3 — Decision Support:**
The system may present full reasoning traces — hypotheses, evidence, confidence, expected scenarios — to support decision-making. The decision is still made by a human or higher-level system.

*Evidence required:* Demonstrated calibration at Level 2. Confidence estimates must be within ±15 percentage points of actual accuracy. Reasoning quality must be scoreable and improving.

**Level 4 — Semi-Autonomous Execution:**
The system may execute decisions within defined boundaries (position size limits, asset class restrictions, risk budget constraints). All decisions outside boundaries require human approval.

*Evidence required:* Demonstrated decision quality at Level 3. Decisions made by the system must be defensible under blind review (reviewers cannot distinguish system decisions from human expert decisions at better than chance levels).

**Level 5 — Trusted Autonomous Execution:**
The system may execute decisions within broader boundaries. Human review is periodic (daily or weekly), not per-decision.

*Evidence required:* Demonstrated outcome quality at Level 4. The system's risk-adjusted returns must be consistent across at least 180 days of operation and two different market regimes.

**Level 6 — Strategic Autonomy:**
The system may determine which domains to operate in, which questions to investigate, and which hypotheses to pursue. It allocates its own learning resources.

*Evidence required:* Demonstrated learning quality at Level 5. The system must show that its self-directed learning produces better criterion development than externally directed learning over a 12-month period.

### 9.3 Revocation

Autonomy is revocable. If criterion metrics degrade at any level, autonomy should be reduced to the previous level until the degradation is investigated and corrected.

**Trigger conditions for revocation:**
- Any validation layer shows a statistically significant negative trend over 30 decisions
- Calibration degrades by more than 10 percentage points compared to the previous 90-day average
- Error type frequencies increase by more than 20% over the previous 90-day average
- Learning quality drops to zero for 10 consecutive outcomes (no knowledge extracted)

---

## PART X: Long-Term Scientific Program

### 10.1 Ten-Year Validation Strategy

Criterion validation is a long-term scientific program, not a one-time certification. The strategy spans years and evolves as the system accumulates experience.

**Year 1 — Infrastructure and Baseline:**
- Establish the reasoning record for every decision
- Implement the five validation layers
- Collect baseline data with no expectation of criterion improvement
- Produce the first Criterion Snapshot (baseline measurement)
- Validate Layers 1–3 (reasoning, decision, execution) with small samples

*Success criteria:* Complete reasoning records exist for all decisions. Baseline criterion measurements are documented. The system demonstrates basic hypothesis formation and evidence tracking.

**Year 2 — Early Learning Detection:**
- Accumulate sufficient data for statistical analysis
- Begin trend analysis on all criterion dimensions
- Validate Layer 5 (learning quality) — is knowledge being extracted?
- Test calibration improvement

*Success criteria:* At least 100 decisions with complete reasoning records. Calibration is measurable. Knowledge extraction rate exceeds 50%. First detection of positive trends in any criterion dimension.

**Year 3 — Cross-Condition Validation:**
- Evaluate criterion metrics across different market regimes
- Test whether learning transfers between conditions
- Validate out-of-sample (new data not seen during development)
- Begin A/B comparisons (lifecycle vs. baseline)

*Success criteria:* Criterion improvement is observed in at least two different market regimes. Out-of-sample performance does not degrade. A/B comparison favors the hypothesis lifecycle.

**Year 5 — Operational Criterion:**
- Demonstrate calibration within ±10 percentage points
- Demonstrate declining error type frequencies
- Demonstrate knowledge persistence across regime changes
- Progress to Autonomy Level 4 or 5

*Success criteria:* All criterion dimensions show positive trends. Calibration is stable within ±10 points. At least three error types show statistically significant decline. The system operates at Semi-Autonomous or Trusted Autonomous level.

**Year 10 — Strategic Criterion:**
- Demonstrate self-directed learning
- Validate across multiple domains (trading, creation, entrepreneurship)
- Demonstrate decision superiority over baseline in all active domains
- Contribute validated criterion methodology to the scientific community

*Success criteria:* The system operates at Strategic Autonomy. Criterion metrics are stable or improving across all domains. The system's decision quality demonstrably exceeds what a human or baseline system could achieve with the same information.

### 10.2 Why Criterion Is Asymptotic

Criterion approaches a limit but never reaches it. The limit is perfect calibration and optimal decision-making under uncertainty — a theoretical boundary that cannot be achieved because:

- The world changes (new regimes, new assets, new risks)
- Information is always incomplete (hidden variables, unknown unknowns)
- Resources are always finite (time, attention, capital)
- Randomness is irreducible (no system can predict all outcomes)

The asymptotic nature of criterion means:
- The system should always be learning, never "finished"
- Validation should measure the rate of improvement, not the absolute level
- Plateaus are expected and should trigger investigation, not alarm
- The goal is to keep the trajectory positive, not to reach a final state

### 10.3 Why the Project Should Never Declare Itself "Finished"

A declaration of "finished" would violate:

**Law 9 — Everything Is Provisional:**
Every claim is subject to revision when evidence accumulates against it. A finished system cannot admit new evidence.

**Law 10 — No Idea Is Above Evidence:**
The system's ultimate authority is accumulated evidence. A finished system would place its existing knowledge above new evidence.

**Constitution Article 6 — Continuous Refinement:**
*"The project should improve continuously, not in bursts. Small, evidence-based refinements are preferred over large, untested redesigns."*

The project should never declare itself finished because:
- The world will continue to change, requiring adaptation
- The system will continue to accumulate experience, enabling improvement
- New validation methods may reveal previously hidden weaknesses
- Scientific humility requires acknowledging that current understanding is incomplete

### 10.4 The Central Scientific Hypothesis

The central scientific hypothesis of O.M.A.-C.O.R.E. is:

> *A system develops criterion when its future hypotheses become consistently better because its previous hypotheses were explicitly tested, evaluated, and transformed into reusable knowledge.*

**What this means operationally:**
- "Future hypotheses become consistently better" — measurable improvement in hypothesis quality, evidence quality, and calibration over time
- "Because" — the improvement is attributable to the hypothesis lifecycle, not to external factors
- "Explicitly tested" — every hypothesis has a defined test, outcome, and evaluation
- "Evaluated" — every outcome triggers error classification and knowledge extraction
- "Transformed into reusable knowledge" — lessons are extracted, stored, and applied to future hypotheses

**What would falsify this hypothesis:**
- A system that implements the full hypothesis lifecycle shows no improvement in criterion metrics over 24 months of operation
- A simpler system (no explicit hypotheses, no evidence tracking, no error classification) matches or exceeds the lifecycle system's criterion metrics
- Improvement in criterion metrics is observed but cannot be attributed to the lifecycle (attributable to data volume, market conditions, or other confounds)
- Criterion metrics improve initially but plateau below operationally useful levels
- Criterion metrics improve in one domain but do not transfer to any other domain

**Maintaining scientific neutrality:**
The hypothesis is not assumed to be true. It is tested by the validation experiments in Part VIII. If the evidence falsifies it, the project should abandon or revise the hypothesis. The goal is not to defend the hypothesis — it is to discover whether it is true.

---

## Self-Review

### S-01: Weak Assumptions

**Assumption: The five validation layers are independent.**
In practice, improvements in reasoning quality may cause improvements in decision quality, which cause improvements in outcome quality. This does not invalidate the framework — it is expected — but it means the layers are not statistically independent. Longitudinal analysis must account for temporal correlation between layers.

**Assumption: Criterion can be inferred from recorded behavior.**
The framework assumes that evaluating reasoning traces, decisions, and outcomes collectively reveals criterion. This assumes that criterion leaves observable traces. If criterion is truly emergent, it may have no single observable manifestation. The convergence of evidence approach mitigates this by requiring multiple independent indicators.

**Assumption: The Criterion Score dimensions are comprehensive.**
Eleven dimensions are proposed. There is no guarantee that these capture all aspects of criterion. Additional dimensions may be discovered through experience. The framework should be open to new dimensions.

**Assumption: Blinded evaluation is feasible.**
Decision quality evaluation requires blinding the evaluator to outcomes. In practice, maintaining perfect blinding may be difficult, especially if the evaluator can infer outcomes from context clues. This introduces potential bias.

### S-02: Conceptual Gaps

**Gap: No defined frequency for Criterion Snapshot generation.**
The framework refers to periodic measurement but does not define the period. Too frequent (daily) produces noisy data. Too infrequent (annually) delays detection of degradation.

**Gap: Cost of validation is not accounted for.**
The reasoning record requires storage and processing. Validation analysis requires time and computation. The cost of validation should be proportional to the stakes of the decisions being validated.

**Gap: No defined threshold for "statistically significant" in criterion trends.**
The framework refers to statistical significance but does not specify the threshold or the correction for multiple comparisons across 11 dimensions.

**Gap: Expert comparison benchmark is undefined.**
The framework suggests comparing against human experts but does not define who qualifies as an expert, how many experts are needed, or how agreement is measured.

### S-03: Potential Circular Reasoning

**Criterion → Better decisions → Better outcomes → Validation → We have criterion.**
This cycle is not strictly circular because it requires measurement at each step. But it does mean that if the measurement instruments are flawed, the cycle can produce false positives. Independent validation of the measurement instruments is required.

**Learning quality → Knowledge extraction → Better hypotheses → Better outcomes → Validation → Learning quality.**
The feedback loop between learning quality and criterion development is the mechanism the framework is designed to validate. It is not circular — it is the hypothesized causal chain — but it requires independent measurement of each stage.

### S-04: Ideas Lacking Evidence

**The five-layer hierarchy has not been validated.**
The theoretical basis for each layer is sound, but the interaction between layers has not been empirically tested. It is possible that some layers are redundant or that important layers are missing.

**Autonomy levels are theoretical.**
The six autonomy levels are based on logical progression, not empirical evidence. The specific evidence requirements for each level may need adjustment as experience accumulates.

**The 11 Criterion Score dimensions may covary more than expected.**
The framework assumes they provide independent information. If they are highly correlated, the effective number of independent dimensions is much smaller than 11.

### S-05: Metrics That May Be Misleading

**Reasoning quality scoring may be subjective.**
If reasoning quality is scored by a human evaluator, inter-rater reliability must be established. If scored by an automated system, the scoring criteria must be validated against human expert judgment.

**Calibration requires sufficient data per bucket.**
If the system makes 100 decisions at varying confidence levels, there may be only 5–10 decisions in the 70–80% confidence bucket. Calibration estimates from small buckets are unreliable. The framework should require minimum sample sizes per confidence bucket.

**Learning velocity may not capture learning depth.**
Extracting many trivial lessons is not the same as extracting one important lesson. The framework measures quantity (knowledge entries per hypothesis) but not quality (significance of the lesson).

### S-06: Validation Risks

**Risk: The Hawthorne effect.**
Knowing that every decision is recorded and evaluated may change the system's behavior. In an automated system, this is less of a concern than with humans, but if the evaluation criteria are known, the system could optimize for the criteria rather than for genuine criterion.

**Risk: Validation becomes the goal.**
If the Criterion Score dimensions are used as performance targets, the system may optimize for the dimensions at the expense of unmeasured aspects of judgment. The framework should periodically rotate which dimensions are emphasized.

**Risk: Data volume overwhelms analysis.**
If the system makes thousands of decisions per year, the reasoning record will grow very large. Automated analysis tools must be developed in parallel with data collection.

**Risk: The system may appear to improve when it is actually overfitting.**
Improved performance on historical data does not guarantee improved performance on future data. Out-of-sample validation is essential and must be strictly enforced.

### S-07: Architectural Risks

**The reasoning record requires storage that does not yet exist.**
The database schema must be extended to support the complete scientific record. This is an implementation dependency.

**Blind replay requires infrastructure that does not yet exist.**
Presenting historical situations without revealing outcomes requires a simulation environment that isolates the system from temporal data leakage.

**A/B comparison requires running two system instances simultaneously.**
This doubles infrastructure requirements during validation periods.

**Counterfactual analysis requires a model of what would have happened under alternative decisions.**
Building this model is non-trivial and may introduce its own biases.

### S-08: What Should Be Considered Provisional

1. **The five-layer hierarchy.** The layers are logically justified but empirically unvalidated. The hierarchy may need to be restructured after initial data collection.

2. **The 11 Criterion Score dimensions.** These are candidates. Experience may show that some are redundant, some are missing, or some cannot be measured reliably.

3. **The autonomy levels.** The specific evidence thresholds at each level are estimates. They should be adjusted based on experience.

4. **The validation experiments.** The specific designs (21-day, 90-day, A/B, historical replay) are prototypes. They may need to be adapted to the system's actual operating characteristics.

5. **The central scientific hypothesis.** The hypothesis may be falsified. The project must be prepared to abandon or revise it if the evidence does not support it.

---

## Final Principle

O.M.A.-C.O.R.E. should never claim to possess criterion.

It should only claim the amount of criterion that has been demonstrated through repeatable, falsifiable, independently verifiable evidence.

A system that claims criterion without evidence is not developing judgment — it is making a claim it cannot support.

A system that demonstrates criterion through converging evidence across reasoning, decision, and outcome quality — sustained over time, robust across conditions, attributable to its own learning mechanisms — has earned the right to say:

*"Our judgment is improving. Here is the evidence. You can verify it yourself."*

Everything remains falsifiable.

Evidence always has the final word.

---

*End of 17_CRITERION_VALIDATION_FRAMEWORK.md — Version 1.0 — June 2026*
