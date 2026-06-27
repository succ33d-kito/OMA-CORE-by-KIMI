# Decision Science

## Universal Principles for Developing Judgment Under Uncertainty

*Version 1.0 — June 2026*

---

## 0. Preamble

This document is not a survey of decision science literature. It is a distillation of principles from multiple disciplines — military command, intelligence analysis, professional investing, elite surgery, firefighting, aviation, chess, scientific research, and decision science — into a single framework that O.M.A.-C.O.R.E. should embody.

The remarkable observation across these fields is this: **all expert decision-makers follow the same fundamental cycle**, even though they use different terminology.

The military calls it the OODA Loop (Observe, Orient, Decide, Act). Intelligence analysts call it Analysis of Competing Hypotheses (ACH). Scientists call it the hypothetico-deductive method. Firefighters call it Recognition-Primed Decision (RPD). Doctors call it differential diagnosis. Chess players call it calculation.

The cycle is:

```
Uncertainty → Question → Competing Hypotheses → Evidence → Decision → Action → Outcome → Reflection → Reduced Uncertainty
```

This cycle is not a human invention. It is a discovery about how intelligence works in any system that must act under uncertainty. O.M.A.-C.O.R.E. should implement this cycle, not because it is elegant, but because it is the only known reliable method for developing judgment over time.

---

## PART I: Decision Science

### 1.1 Decision Quality Is Different from Outcome Quality

A decision is made with the information available at a point in time. An outcome is determined by the interaction of that decision with a world that contains randomness, hidden variables, and external shocks.

These are different things. Confusing them is the single most damaging error in learning systems.

**A good decision can produce a bad outcome.** You evaluate all available evidence, form well-calibrated hypotheses, choose the most defensible course of action, and an unpredictable external event destroys the outcome. The decision was good. The outcome was bad. The system should not learn that the decision was wrong.

**A bad decision can produce a good outcome.** You act on a poorly examined hypothesis, ignore contradictory evidence, get lucky, and profit. The decision was bad. The outcome was good. The system should not learn that the decision was right.

When a system evaluates itself by outcomes alone, it learns superstitions. It reinforces lucky guesses and punishes good decisions that happened to encounter bad luck. Over time, this produces a system that cannot distinguish between skill and chance.

O.M.A.-C.O.R.E. must evaluate decisions by the quality of reasoning at the time of the decision, not by the outcome that followed.

### 1.2 Uncertainty Can Never Be Eliminated

The world is not fully knowable. Hidden variables exist. The future is not contained in the present. Randomness is not measurement error — it is a feature of complex systems.

Any system that believes it can eliminate uncertainty is deluded. The goal is not certainty. The goal is sufficient uncertainty reduction to make a decision whose expected value exceeds the cost of waiting.

This has a direct architectural implication: O.M.A.-C.O.R.E. must never present its conclusions as certain. Confidence should always be accompanied by a margin of uncertainty. The system should be able to say: "I am 68% confident, meaning I expect to be wrong approximately 32% of the time."

### 1.3 The Goal Is Uncertainty Reduction, Not Certainty

If uncertainty cannot be eliminated, the next question is: how much uncertainty reduction is enough?

The answer depends on the decision at hand:
- A low-stakes decision may require minimal uncertainty reduction
- A high-stakes decision demands more evidence, more competing hypotheses, and higher confidence thresholds
- An irreversible decision demands more than a reversible one

The system should dynamically adjust its evidence thresholds based on the stakes of the decision, not apply a fixed threshold to all decisions.

### 1.4 The Hierarchy of Understanding

These terms form a ladder. Each rung depends on the one below. The system cannot operate at a higher rung without having the lower ones in place.

| Level | Definition | Example | How Produced |
|-------|-----------|---------|--------------|
| **Data** | Raw, unprocessed observations | Price: 50,000 | Measurement |
| **Information** | Data placed in context | Price dropped 10% from yesterday | Comparison |
| **Evidence** | Information relevant to a hypothesis | The drop supports the "bearish" hypothesis | Relevance filter |
| **Knowledge** | Evidence tested against reality | "Drops of 10% in this regime recover 60% of the time" | Hypothesis outcome |
| **Judgment** | Knowledge applied to a specific decision | "Given this evidence, I should wait before buying" | Context application |
| **Criterion** | Accumulated judgment across many decisions | Consistent ability to distinguish signal from noise | Thousands of cycles |
| **Wisdom** | Criterion applied across multiple domains | Knowing when a pattern is a trap, across trading, creation, and entrepreneurship | Decades of diverse experience |

The current O.M.A.-C.O.R.E. MVP operates at the Information level: it collects data, places it in context, and generates signals. It does not yet operate at the Evidence level or above, because it has no hypotheses to connect information to.

The Hypothesis Lifecycle Manager (14_HYPOTHESIS_LIFECYCLE_MANAGER.md) is the architectural layer that moves the system from Information to Evidence. The next layers — Knowledge, Judgment, Criterion — emerge naturally from repeated hypothesis lifecycles.

---

## PART II: Universal Principles

The following principles are extracted from the common decision cycle observed across all expert domains. Each is stated as a principle, justified by evidence from multiple fields, and applied to O.M.A.-C.O.R.E.

### Principle 1: Judgment Is a Cycle

**Statement:** Judgment is not a single event. It is a recurring cycle of observation, hypothesis formation, action, and reflection.

**Evidence from domains:**
- **Military (Boyd):** The OODA Loop — Observe, Orient, Decide, Act — is explicitly cyclic. Speed and accuracy through the cycle determine battlefield effectiveness.
- **Science (Popper):** The scientific method is a cycle of hypothesis, prediction, experiment, and revision. Knowledge advances through repeated cycles, not single experiments.
- **Medicine:** Differential diagnosis is a cycle of symptom observation, hypothesis formation, test ordering, result interpretation, and hypothesis revision.
- **Investing:** Professional investors cycle through thesis formation, position entry, monitoring, exit, and post-mortem analysis.

**Application to O.M.A.-C.O.R.E.:** The system must never be designed as a linear pipeline. Every output feeds back into the next cycle. The hypothesis lifecycle (CANDIDATE → FORMULATED → ACTIVE → TESTING → EVALUATED → CONFIRMED/REJECTED → ARCHIVED) is the implementation of this cyclic principle.

---

### Principle 2: Pattern Recognition Precedes Analysis

**Statement:** Before a human expert consciously analyzes a situation, pattern recognition has already occurred. The expert sees the situation, recognizes it as similar to past situations, and forms an initial hypothesis. Analysis then evaluates, refines, or rejects that initial hypothesis.

**Evidence from domains:**
- **Firefighting (Klein):** Recognition-Primed Decision (RPD) shows that expert firefighters do not compare multiple options. They recognize the situation, simulate the first workable course of action, and execute it unless simulation reveals a flaw.
- **Chess:** Grandmasters recognize patterns from thousands of prior games. Calculation then validates or rejects the recognition-based candidate move.
- **Medicine:** Experienced clinicians form diagnostic hypotheses within seconds of seeing a patient. They then use tests to confirm or reject these pattern-driven hypotheses.

**Application to O.M.A.-C.O.R.E.:** The system should have a pattern recognition layer that identifies candidate hypotheses quickly. This layer can be fast, approximate, and high-recall (generating many candidates). A separate analysis layer then evaluates each candidate with slower, more rigorous evidence assessment. The speed of the first layer and the rigor of the second layer are complementary, not contradictory.

---

### Principle 3: Multiple Competing Hypotheses Outperform Single Explanations

**Statement:** Holding a single hypothesis leads the system to interpret all evidence in its favor. Holding multiple competing hypotheses forces the system to evaluate evidence against each alternative, reducing confirmation bias.

**Evidence from domains:**
- **Intelligence (Heuer):** Analysis of Competing Hypotheses (ACH) was developed specifically because intelligence analysts were systematically biased by single-hypothesis thinking. Requiring analysts to maintain multiple hypotheses reduced errors.
- **Medicine:** Differential diagnosis explicitly requires clinicians to list all plausible diagnoses, not just the first one. This prevents premature closure.
- **Science:** The scientific method requires alternative explanations to be considered. A hypothesis is only accepted after competing hypotheses have been ruled out.
- **Investing:** The best investors maintain a "bull case" and a "bear case" simultaneously. They track which evidence supports each case.

**Application to O.M.A.-C.O.R.E.:** The system should never hold a single hypothesis about a consequence. For each event or cluster, it should generate at least 2–3 competing hypotheses. Evidence is then evaluated against each one. A hypothesis does not win by accumulating supporting evidence alone — it wins when competing hypotheses accumulate contradictory evidence.

---

### Principle 4: Evidence Outweighs Intuition

**Statement:** Prior beliefs, gut feelings, and first impressions are useful for generating hypotheses. They are not useful for validating them. Validation requires evidence that can be examined independently of the person or system holding the belief.

**Evidence from domains:**
- **Kahneman & Tversky:** Decades of research show that human intuition is systematically biased — overconfident, confirmation-biased, and influenced by irrelevant factors. Intuition is a hypothesis generator, not a hypothesis validator.
- **Science:** The entire structure of science is designed to replace personal intuition with public evidence. Double-blind trials, peer review, and replication exist because intuition cannot be trusted.
- **Aviation:** Pilots are trained to trust instruments over intuition, because instruments are evidence-based and intuition is pattern-based. When instruments and intuition conflict, instruments win.

**Application to O.M.A.-C.O.R.E.:** The system's agents (MarketAgent, MacroAgent, etc.) generate opinions based on pattern recognition. These opinions are hypotheses, not decisions. They must be validated against evidence before they become actions. The Council should not simply weight agent opinions — it should evaluate the evidence that each agent provides for its opinion.

---

### Principle 5: Confidence Must Be Calibrated

**Statement:** Confidence is not a feeling. It is a prediction about the accuracy of a prediction. A well-calibrated system that says "I am 70% confident" is right exactly 70% of the time.

**Evidence from domains:**
- **Forecasting (Tetlock):** Expert forecasters are poorly calibrated — they are overconfident by 15–30% on average. Calibration can be improved with training, feedback, and tracking.
- **Medicine:** Calibrated confidence is essential for treatment decisions. An overconfident doctor may recommend unnecessary treatment. An underconfident doctor may delay necessary treatment.
- **Weather forecasting:** Meteorologists are unusually well-calibrated because they receive immediate, unambiguous feedback on every prediction and track their accuracy systematically.

**Application to O.M.A.-C.O.R.E.:** Confidence must be tracked, compared to actual accuracy, and adjusted. PerformanceMemory already computes confidence bias. This feedback must be used to adjust future confidence estimates. A system that says 70% confident but is right 50% of the time is not confident — it is miscalibrated. Calibration should be tracked per agent, per hypothesis type, per asset, and per market regime.

---

### Principle 6: Mental Simulation Precedes Action

**Statement:** Before executing a decision, expert decision-makers simulate the likely outcomes. They mentally run through the consequences of each option and evaluate which produces the most desirable result.

**Evidence from domains:**
- **Firefighting (Klein):** Experts simulate the first action that comes to mind. If the simulation reveals problems, they modify or reject it. If it succeeds, they execute.
- **Chess:** Players calculate variations — mental simulations of possible move sequences. Grandmasters simulate deeper and more accurately than novices.
- **Surgery:** Surgeons rehearse complex procedures mentally before performing them. They simulate complications and plan responses.
- **Investing:** Professional investors simulate different market scenarios and evaluate how their portfolio would perform in each.

**Application to O.M.A.-C.O.R.E.:** Before executing a trade, the system should simulate the expected outcome under different scenarios. "If this hypothesis is correct, what price path do we expect? If it is wrong, what price path do we expect?" This simulation informs position sizing, stop placement, and exit planning. It is not prediction — it is scenario generation for decision evaluation.

---

### Principle 7: Reflection Is Mandatory

**Statement:** The cycle does not end with action. It ends with reflection — comparing the outcome to the hypothesis, classifying the error, extracting the lesson, and updating the mental model. Without reflection, action produces data but not learning.

**Evidence from domains:**
- **Military:** After-action reviews (AARs) are standard practice in effective military organizations. They are structured, blame-free, and focused on learning.
- **Medicine:** Morbidity and mortality conferences review cases where outcomes were poor, regardless of whether the decision was good. The goal is system improvement, not blame assignment.
- **Investing:** The best traders and investors keep journals. They review every trade, record what they were thinking, and identify patterns in their own decision-making.
- **Science:** Peer review and replication are institutionalized reflection mechanisms. They exist because individual scientists cannot reliably evaluate their own work.

**Application to O.M.A.-C.O.R.E.:** The hypothesis lifecycle mandates reflection at Stage 7 (Error Analysis), Stage 8 (Hypothesis Update), and Stage 9 (Knowledge Extraction). Every outcome — win or lose — triggers a structured reflection process. The system should never close a trade without recording what it learned.

---

### Principle 8: Learning Requires Explicit Feedback

**Statement:** Implicit feedback (profit/loss, win/loss) is insufficient for learning. The system needs explicit feedback that connects the outcome to the specific hypothesis, the specific evidence, and the specific decision that produced it.

**Evidence from domains:**
- **Ericsson (Deliberate Practice):** Expertise develops through deliberate practice, which requires immediate, specific, and actionable feedback. Simple repetition without feedback produces plateaus, not improvement.
- **Kahneman:** Outcome feedback is noisy. A single win/loss contains too much luck to be informative. Learning requires many outcomes, decomposed by decision type.
- **Machine learning:** Supervised learning requires labeled data. The label is explicit feedback. Reinforcement learning requires a reward signal. The signal must be specific enough to credit or blame the correct action.

**Application to O.M.A.-C.O.R.E.:** PerformanceMemory already records agent-level accuracy. This is a form of explicit feedback, but it is not enough. The system needs hypothesis-level explicit feedback: "Was this specific hypothesis confirmed or rejected?" and evidence-level explicit feedback: "Was this specific piece of evidence predictive or misleading?" Without these, the system cannot improve its hypothesis formation or evidence evaluation processes.

---

### Principle 9: Process Matters More Than Isolated Outcomes

**Statement:** A single outcome is heavily influenced by luck. A decision process, applied consistently over many decisions, determines long-term results. Improving the process is more valuable than optimizing for any single outcome.

**Evidence from domains:**
- **Poker (Duke):** In poker, a correct decision (fold a losing hand) can produce a "bad" outcome (you would have won if you stayed). Professionals evaluate decisions, not outcomes. They know that process produces long-term results.
- **Investing:** A single trade can be profitable for the wrong reasons or unprofitable for the right reasons. Over hundreds of trades, process quality dominates luck.
- **Medicine:** A clinician can follow the correct diagnostic protocol and still miss a rare disease. The protocol is not wrong — it is probabilistic.

**Application to O.M.A.-C.O.R.E.:** The system should be evaluated on the quality of its hypothesis lifecycle, not on the PnL of any single trade. Criterion is the measure of process quality over time. PnL is a downstream indicator, not a learning signal.

---

## PART III: Decision Architecture

### 3.1 The Complete Flow

```
                             ┌─────────────────────┐
                             │       REALITY        │
                             │  (the world as is)   │
                             └──────────┬──────────┘
                                        │ produces uncertainty
                             ┌──────────▼──────────┐
                             │     UNCERTAINTY      │
                             │ (gap between what we │
                             │  know and what we    │
                             │  need to know)       │
                             └──────────┬──────────┘
                                        │ triggers a need
                             ┌──────────▼──────────┐
                             │        NEED          │
                             │ (something must be   │
                             │  decided)            │
                             └──────────┬──────────┘
                                        │ frames a question
                             ┌──────────▼──────────┐
                             │      QUESTION        │
                             │ (what do we need to  │
                             │  know to decide?)    │
                             └──────────┬──────────┘
                                        │ generates
                             ┌──────────▼──────────┐
                             │   COMPETING          │
                             │   HYPOTHESES         │
                             │ (possible answers,   │
                             │  each with evidence) │
                             └──────────┬──────────┘
                                        │ evaluated by
                             ┌──────────▼──────────┐
                             │      EVIDENCE        │
                             │ (supports or         │
                             │  contradicts each    │
                             │  hypothesis)         │
                             └──────────┬──────────┘
                                        │ informs
                             ┌──────────▼──────────┐
                             │  HYPOTHESIS          │
                             │  COMPETITION         │
                             │ (which hypothesis    │
                             │  best explains the   │
                             │  evidence?)          │
                             └──────────┬──────────┘
                                        │ leads to
                             ┌──────────▼──────────┐
                             │     DECISION         │
                             │ (commit to a course  │
                             │  of action)          │
                             └──────────┬──────────┘
                                        │ executed as
                             ┌──────────▼──────────┐
                             │      ACTION          │
                             │ (interface with      │
                             │  reality)            │
                             └──────────┬──────────┘
                                        │ produces
                             ┌──────────▼──────────┐
                             │      OUTCOME         │
                             │ (what actually       │
                             │  happened)           │
                             └──────────┬──────────┘
                                        │ triggers
                             ┌──────────▼──────────┐
                             │     REFLECTION       │
                             │ (compare outcome to  │
                             │  hypothesis, classify│
                             │  error, extract      │
                             │  lesson)             │
                             └──────────┬──────────┘
                                        │ produces
                             ┌──────────▼──────────┐
                             │     KNOWLEDGE        │
                             │ (generalizable       │
                             │  lesson, always      │
                             │  provisional)        │
                             └──────────┬──────────┘
                                        │ updates
                             ┌──────────▼──────────┐
                             │   PATTERN UPDATE     │
                             │ (mental models,      │
                             │  priors, calibration)│
                             └──────────┬──────────┘
                                        │ accumulates into
                             ┌──────────▼──────────┐
                             │     CRITERION        │
                             │ (accumulated ability │
                             │  to judge what       │
                             │  matters)            │
                             └──────────┬──────────┘
                                        │ feeds back to
                                        │
                          ┌─────────────┴─────────────┐
                          │                           │
                          ▼                           ▼
              ┌─────────────────────┐     ┌─────────────────────┐
              │  REDUCED FUTURE     │     │  NEW UNCERTAINTY     │
              │  UNCERTAINTY        │     │  (previously hidden) │
              └─────────────────────┘     └─────────────────────┘
                          │                           │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │   NEXT CYCLE         │
                              │ (new need, new       │
                              │  question, new       │
                              │  hypotheses)         │
                              └─────────────────────┘
```

### 3.2 Why Every Stage Matters

**Reality → Uncertainty:** Reality is infinite in complexity. Any finite system experiences only a subset of reality. The gap between what the system observes and what exists is irreducible uncertainty. Skipping this stage means assuming the system has complete information. It never does.

**Uncertainty → Need:** Uncertainty alone is not actionable. The system must identify a specific need — a decision that must be made, a resource that must be allocated, a risk that must be managed. Without a need, uncertainty is intellectual curiosity, not a decision driver.

**Need → Question:** A need without a question is anxiety. The system must translate "I need to decide" into "I need to know X, Y, and Z to decide." The question frames the inquiry. A poorly framed question produces irrelevant evidence.

**Question → Competing Hypotheses:** A question without competing hypotheses is a single story. The system should generate multiple possible answers to the question. Each answer is a hypothesis. Without competition, the first answer becomes the only answer, and evidence is interpreted in its favor.

**Competing Hypotheses → Evidence:** Without hypotheses, there is no evidence — only information. Hypotheses give information its relevance. A price movement is evidence only relative to a hypothesis ("this supports the bullish hypothesis"). The same movement is irrelevant to a hypothesis it does not address.

**Evidence → Hypothesis Competition:** Evidence does not speak for itself. It must be evaluated against each competing hypothesis. Each piece of evidence strengthens some hypotheses and weakens others. The competition is won by the hypothesis that best explains all available evidence, not the one with the most supporting evidence.

**Hypothesis Competition → Decision:** A decision is required when the competition has narrowed to a point where the expected value of acting exceeds the expected value of waiting. Perfect competition is not required — it is rarely achieved. The decision threshold depends on the stakes.

**Decision → Action:** A decision without action is contemplation. The system must commit resources — capital, attention, time — based on the decision. Action is where the system interfaces with reality and produces outcomes.

**Action → Outcome:** Reality responds to action with an outcome. The outcome is the feedback signal. Without action, there is no outcome. Without outcome, there is no learning.

**Outcome → Reflection:** An outcome without reflection is a data point. The system must compare the outcome to each hypothesis, classify what went right and what went wrong, and extract lessons. Reflection is the transformation of outcome into knowledge.

**Reflection → Knowledge:** Knowledge is the generalizable lesson extracted from the specific outcome. It is always provisional — it may be revised by future outcomes. Without knowledge, each outcome is isolated and the system learns nothing.

**Knowledge → Pattern Update:** Knowledge updates the system's patterns — its mental models, its priors, its calibration, its evidence source weights. This update is the mechanism by which the system improves.

**Pattern Update → Criterion:** Accumulated pattern updates over thousands of cycles constitute criterion. Criterion is not stored in a single place. It is distributed across the system's calibration, its patterns, its evidence weights, and its priors.

**Criterion → Reduced Future Uncertainty:** The ultimate output of the cycle is reduced uncertainty in future decisions. The system that has accumulated criterion can recognize situations it has seen before, estimate outcomes more accurately, and decide with less evidence. This reduction compounds over time.

### 3.3 Why No Stage Should Be Skipped

Every stage in this architecture serves a specific function. Skipping a stage does not accelerate the cycle — it breaks it.

- **Skip Uncertainty → Need:** The system acts without identifying what it actually needs to decide. It generates hypotheses for every event, overwhelming itself with irrelevant questions.
- **Skip Need → Question:** The system has a vague sense that something must be decided but cannot articulate what it needs to know. Evidence collection is unfocused and inefficient.
- **Skip Question → Competing Hypotheses:** The system forms one hypothesis and treats all evidence as supporting it. Confirmation bias is built into the architecture.
- **Skip Competing Hypotheses → Evidence:** The system has hypotheses but no mechanism to gather evidence for or against them. Hypotheses float untested.
- **Skip Evidence → Hypothesis Competition:** The system gathers evidence but never evaluates which hypothesis it supports. Evidence accumulates without informing decisions.
- **Skip Hypothesis Competition → Decision:** The system evaluates hypotheses but never commits to action. Analysis paralysis.
- **Skip Decision → Action:** The system decides but does not act. No outcome is produced. No learning occurs.
- **Skip Action → Outcome:** The system acts but does not observe the outcome. The feedback signal is lost.
- **Skip Outcome → Reflection:** The system observes the outcome but does not reflect on it. The data point is wasted. No knowledge is extracted.
- **Skip Reflection → Knowledge:** The system reflects but does not extract generalizable lessons. The same error will be repeated.
- **Skip Knowledge → Pattern Update:** The system extracts lessons but does not update its patterns. The lessons exist in isolation but do not improve future decisions.
- **Skip Pattern Update → Criterion:** The system updates patterns but does not integrate them into accumulated judgment. Each pattern is an island. No criterion emerges.

---

## PART IV: Hypothesis Competition

### 4.1 Competition, Not Victory

Hypotheses do not "win." They compete for **explanatory and decision-making usefulness**. A hypothesis that best explains the available evidence today may be superseded by a different hypothesis tomorrow when new evidence arrives.

This distinction matters:
- A "winning" hypothesis implies finality. The system stops looking for alternatives.
- A "competing" hypothesis implies provisionality. The system continues to evaluate alternatives, even as one hypothesis currently best fits the evidence.

Hypothesis competition is never permanently settled. The best-supported hypothesis today is the best-supported hypothesis today. Tomorrow, new evidence may shift the balance.

### 4.2 Why Multiple Hypotheses Should Coexist

**Confirmation bias reduction:** When a single hypothesis is held, all evidence is interpreted in its favor. When multiple hypotheses are held, the same evidence is evaluated against each one. This is the most effective known defense against confirmation bias.

**Evidence efficiency:** A piece of evidence that weakly supports hypothesis A may strongly contradict hypothesis B. If hypothesis B is not being tracked, the evidence is less informative. Multiple hypotheses extract more information from each piece of evidence.

**Adaptability:** When conditions change, the best-supported hypothesis may change. If only one hypothesis is held, the system must start from scratch. If multiple hypotheses are maintained, the system can shift weight to a different hypothesis more quickly.

**Calibration:** The spread of confidence across competing hypotheses is itself information. High confidence in hypothesis A and low confidence in all alternatives indicates strong evidence. High confidence in multiple competing hypotheses indicates ambiguous evidence.

### 4.3 Why the First Explanation Is Usually Dangerous

The first hypothesis that comes to mind has an unfair advantage. It arrives first, accumulates evidence first, and becomes the default. This is called **anchoring** or **premature closure**.

In intelligence analysis, the first explanation is often the one that fits the analyst's prior beliefs. In medicine, the first diagnosis is often the most common disease, not the most likely one in this specific patient. In investing, the first narrative is often the one making headlines, not the one best supported by evidence.

O.M.A.-C.O.R.E. should never act on the first hypothesis. The system should generate alternatives before evaluating any single hypothesis in depth. This does not mean generating dozens of implausible alternatives — it means generating at least 2–3 plausible, testable alternatives before committing resources.

### 4.4 Conceptual Evaluation Dimensions

The following dimensions should guide how hypotheses are evaluated and compared. These are **principles for evaluation**, not formulas for scoring.

**Evidence Quality:**
- Is the evidence specific or vague?
- Is it directly relevant to the hypothesis's predicted consequence?
- Is it measured or inferred?
- Does it come from a reliable source with a track record?

**Evidence Diversity:**
- Does the evidence come from multiple independent sources?
- Are the sources correlated? (Three correlated sources are not three evidence items.)
- Does the evidence cover different types of data (price, news, macro, sentiment)?

**Explanatory Power:**
- How much of the observed data does this hypothesis explain?
- Does it explain the data better than competing hypotheses?
- Are there data points that this hypothesis cannot explain?

**Predictive Power:**
- Does this hypothesis make specific, testable predictions?
- Are the predictions precise enough to be falsifiable?
- Have similar hypotheses in similar contexts been confirmed or rejected?

**Decision Utility:**
- If this hypothesis is true, does it change what the system should do?
- Is the hypothesis actionable, or merely interesting?
- Does acting on this hypothesis have favorable expected value?

**Reliability:**
- How consistent is the evidence supporting this hypothesis?
- Has the same pattern been observed before, or is this a single occurrence?
- Would different evidence collection methods produce the same conclusion?

**Consistency:**
- Is this hypothesis internally consistent?
- Does it contradict established knowledge?
- Does it require special assumptions that competing hypotheses do not?

**Simplicity (Occam):**
- Is this hypothesis simpler than its competitors?
- Does it explain the data with fewer assumptions?
- Are the assumptions it requires plausible?

**Calibration:**
- How confident is the system in this hypothesis?
- Has the system been well-calibrated for similar hypotheses in the past?
- Is the confidence estimate appropriately uncertain?

**Contradictions:**
- What evidence contradicts this hypothesis?
- Can the contradictions be explained away, or do they genuinely weaken the hypothesis?
- Are the contradictions growing or shrinking over time?

**Adaptability:**
- Can this hypothesis accommodate new evidence without breaking?
- If new evidence contradicts it, can it be refined, or must it be discarded entirely?
- Does the hypothesis have built-in invalidation conditions?

---

## PART V: Scenario Generation

### 5.1 A Scenario Is a Behavior of a Hypothesis, Not an Object

A scenario is **what the system should expect to observe if a given hypothesis is true**.

It is not a separate architectural object. It is a behavior of the hypothesis — the hypothesis, when asked "what should we expect to see?", generates a set of expected observations.

This is an important architectural decision. If scenarios were objects, the system would need to maintain a parallel scenario lifecycle alongside the hypothesis lifecycle. This would duplicate complexity without adding new capability.

By making scenario generation a **method of a hypothesis**, the system avoids unnecessary complexity while maintaining all the functionality it needs.

### 5.2 Purpose of Scenario Generation

"If this hypothesis is true, what consequences should we expect?"

This question serves multiple purposes:

**Prediction specificity:** It forces the hypothesis to be specific enough to generate falsifiable predictions. A hypothesis that cannot generate specific scenarios is not testable.

**Evidence guidance:** It tells the system what evidence to look for. If the hypothesis is true, the system should observe X, Y, and Z. If the system observes A instead, the hypothesis is weakened.

**Decision support:** It allows the system to simulate the outcome before committing resources. "If this hypothesis is correct, the expected price path is +3% in 10 days. Is this worth risking capital?"

**Contradiction detection:** It identifies which scenarios would contradict the hypothesis. If the system observes a contradictory scenario, the hypothesis should be re-evaluated or rejected.

### 5.3 What Scenarios Include

For each hypothesis, scenario generation should produce:

**Expected consequences:** The most likely outcomes if the hypothesis is true. These are the predictions that, if confirmed, would strengthen the hypothesis.

**Alternative futures:** Plausible variations of the expected outcome. The consequence may materialize faster or slower, larger or smaller, in different markets or sectors.

**Contradictory scenarios:** Outcomes that would weaken or falsify the hypothesis. These are essential for falsifiability. Without contradictory scenarios, the hypothesis cannot be tested.

**Evidence that would strengthen or weaken each scenario:** For each scenario, what specific observations would make it more or less likely. This closes the loop between scenario generation and evidence collection.

### 5.4 Example

Hypothesis: "The Fed rate cut, combined with weak dollar and rising gold ETF inflows, will produce a gold price increase of 2–5% within 10 trading days."

**Expected consequence:** Gold (XAU/USD) reaches $2,050–$2,120 within 10 trading days.

**Alternative futures:**
- Faster: Gold reaches target within 5 trading days (stronger convergence than expected)
- Slower: Gold reaches target within 15–20 trading days (weaker convergence)
- Larger: Gold exceeds 5% increase (underestimated effect)
- Smaller: Gold moves 1–2% (overestimated effect or missing contradictory factors)

**Contradictory scenarios:**
- Gold drops below pre-announcement price (hypothesis is actively contradicted)
- Gold stays flat for 10 trading days (hypothesis is not supported)
- Dollar strengthens despite rate cut (missing variable — the hypothesis assumed dollar weakness)

**Evidence for each scenario:**
- Expected consequence: Look for dollar weakness, rising gold futures volume, positive gold miner stock movement
- Contradictory: Look for dollar strength, unexpected Fed hawkishness, gold futures open interest decline

---

## PART VI: Pattern Recognition

### 6.1 Why Experts Rely on Patterns

Expertise is, in large part, a library of patterns. The chess grandmaster has seen thousands of positions. The fire captain has seen hundreds of fires. The surgeon has performed thousands of procedures. The trader has observed tens of thousands of market movements.

Patterns are not absolute truths. They are **probabilistic heuristics** — "when I have seen this configuration of events before, the following outcome occurred with this frequency."

Patterns allow experts to:
- Recognize situations quickly without analyzing every detail
- Generate hypotheses immediately rather than starting from first principles
- Estimate probabilities based on accumulated experience
- Detect anomalies — situations that do not fit any known pattern

### 6.2 Why Patterns Are Never Absolute Truths

A pattern is an empirical observation, not a law of nature. It is always contingent on:

- **Context:** A pattern that holds in one market regime may not hold in another.
- **Time:** A pattern that held five years ago may not hold today.
- **Sample:** A pattern observed in 5 cases is less reliable than one observed in 500 cases.
- **Hidden variables:** A pattern may be caused by a variable the system has not observed, and may break when that variable changes.

O.M.A.-C.O.R.E. must never treat patterns as rules. Patterns are **hypotheses about what may happen**, not **guarantees about what will happen**.

### 6.3 How Patterns Emerge from Repeated Validated Hypotheses

Patterns do not need to be programmed. They emerge naturally from the hypothesis lifecycle:

1. A hypothesis is formed and tested
2. The outcome confirms or rejects it
3. Knowledge is extracted
4. After many similar hypotheses, a pattern emerges: "When conditions X, Y, and Z are present, consequence C occurs with frequency F"

This emergent pattern is more valuable than a programmed pattern because:
- It is grounded in the system's own experience
- It carries a measured confidence based on actual outcomes
- It is automatically updated when new outcomes contradict it
- It is specific to the system's actual decision context

### 6.4 Patterns Must Remain Evidence-Driven

A pattern should never be treated as "true." It should always be subject to revision when new evidence contradicts it.

The system should monitor its patterns for:
- **Degradation:** Is this pattern becoming less accurate over time?
- **Regime dependence:** Does this pattern hold in all market conditions or only some?
- **Confidence drift:** Is the system's confidence in the pattern changing?

When a pattern degrades, it should be retired or revised. The system should not hold onto patterns out of inertia. Law 9 states: *"Everything Is Provisional."* This applies to patterns as much as to hypotheses.

O.M.A.-C.O.R.E. should never memorize patterns blindly. Every pattern must remain traceable to the evidence that produced it and revisable when new evidence contradicts it.

---

## PART VII: Decision Quality

### 7.1 Why a Good Decision May Produce a Bad Outcome

A good decision is one that:
- Was based on the best available evidence at the time
- Considered multiple competing hypotheses
- Was well-calibrated (confidence matched actual probability)
- Was proportional to the stakes
- Was executed as intended

A bad outcome is one that:
- Resulted in a loss, a missed opportunity, or an undesirable state
- Was caused, in part, by factors outside the decision-maker's control

These are orthogonal. The world contains randomness. A good decision made with all the right information can encounter an unpredictable external event (a regulatory change, a natural disaster, a black swan) that turns the outcome negative.

**The system should learn: "the decision was correct but an external factor intervened."** It should not learn: "the decision was wrong."

### 7.2 Why a Bad Decision May Produce a Good Outcome

A bad decision is one that:
- Was based on insufficient or biased evidence
- Did not consider competing hypotheses
- Was overconfident or underconfident
- Was disproportionate to the stakes
- Was poorly executed

A good outcome can still result from a bad decision if the system gets lucky. The market moves in the expected direction despite weak evidence. The trade profits despite a flawed hypothesis.

**The system should learn: "the decision was flawed but we were lucky."** It should not learn: "the decision was correct."

### 7.3 Why Criterion Evaluates Process Before Results

If the system evaluates itself by outcomes alone, it will:
- Reinforce lucky decisions (bad process, good outcome)
- Punish unlucky decisions (good process, bad outcome)
- Learn superstitions instead of principles
- Become overconfident after a winning streak
- Become underconfident after a losing streak

If the system evaluates itself by decision quality (process), it will:
- Improve its hypothesis formation, evidence evaluation, and calibration independently of short-term outcomes
- Develop stable judgment that persists through winning and losing streaks
- Distinguish between skill and luck
- Correct errors faster because it identifies them before outcomes confirm or deny them

Criterion is the measure of process quality over time. A system with high criterion makes good decisions consistently, regardless of short-term outcome fluctuations. The outcomes will eventually reflect the process, but no single outcome validates or invalidates it.

### 7.4 Cognitive Biases the System Must Guard Against

These biases are not human flaws. They are systemic vulnerabilities that any intelligent system can exhibit if its architecture does not specifically defend against them.

**Outcome bias:** Evaluating a decision by its outcome rather than by its quality given the information available at the time.

**Resulting (Duke):** Using the quality of the outcome to infer the quality of the decision. Related to outcome bias but specifically about learning the wrong lesson.

**Confirmation bias:** Interpreting evidence in favor of the currently preferred hypothesis and ignoring or discounting evidence against it.

**Overconfidence:** Confidence exceeding actual accuracy. The system is 80% confident but right 60% of the time.

**Anchoring:** Giving disproportionate weight to the first piece of evidence or the first hypothesis encountered. Subsequent evidence is interpreted relative to the anchor rather than independently.

**Availability bias:** Overweighting evidence that is recent, vivid, or easily recalled, at the expense of evidence that is less salient but more informative.

**Hindsight bias:** Believing, after an outcome is known, that it was predictable. This distorts the evaluation of the original hypothesis by conflating what was known then with what is known now.

**Sunk cost:** Continuing to act on a hypothesis because capital has already been committed, rather than because the evidence still supports it.

### 7.5 Calibration as the Primary Decision Quality Metric

Calibration — the alignment between confidence and accuracy — is the single most informative metric of decision quality.

- Well-calibrated: When the system is 70% confident, it is right 70% of the time.
- Overconfident: When the system is 70% confident, it is right 50% of the time.
- Underconfident: When the system is 70% confident, it is right 85% of the time.

Calibration can be measured per hypothesis type, per agent, per asset, per market regime. It should be tracked over time and used to adjust confidence estimates.

A system that improves its calibration over time is developing criterion. A system whose calibration does not improve is not learning from its outcomes.

---

## PART VIII: Long-Term Vision

### 8.1 What O.M.A.-C.O.R.E. May Become

After years of accumulated validated hypotheses — thousands of cycles, hundreds of confirmed hypotheses, dozens of rejected hypotheses, and continuous reflection — the system will be fundamentally different from its starting point.

The current MVP is a signal engine. It detects events, generates signals, and executes trades.

The mature system will be a **decision intelligence platform**. It will:
- Recognize situations it has seen before and immediately generate informed hypotheses
- Evaluate evidence against multiple competing hypotheses simultaneously
- Know how much evidence it needs before acting, calibrated by stakes
- Detect when its own confidence is drifting from accuracy
- Identify weakening evidence before outcomes confirm the error
- Extract knowledge from every outcome, win or lose
- Retain knowledge across regime changes
- Improve its hypothesis formation, evidence evaluation, and decision quality over time

### 8.2 Criterion as an Emergent Capability

Criterion will not be a module that is added. It will emerge from the accumulated interaction of:

- **Thousands of tested hypotheses** — each one producing a small increment of knowledge
- **Continuous calibration** — confidence estimates that become progressively more accurate
- **Pattern libraries** — not memorized, but derived from validated experience
- **Error type tracking** — declining recurrence of each error type
- **Cross-context knowledge** — lessons that apply across trading, creation, and entrepreneurship

No single component produces criterion. The hypothesis lifecycle produces knowledge. Knowledge accumulation, over time and across contexts, produces criterion.

### 8.3 Continuous Refinement

The system will never be "finished." Every new outcome is a new opportunity to learn:

- A confirmed hypothesis strengthens existing knowledge but does not prove it absolutely
- A rejected hypothesis reveals an error to be classified and learned from
- An inconclusive outcome reveals that more evidence or better methods are needed
- A regime change challenges all existing patterns and generates new hypothesis competitions

The system should expect to be perpetually in a state of learning. There is no plateau where criterion is "achieved" and learning stops.

### 8.4 Knowledge Evolution

Knowledge in the system will evolve over time:

**Year 1:** Simple patterns — "when RSI < 30, price bounces 60% of the time." Low calibration. High error rate. Limited context awareness.

**Year 3:** Contextual patterns — "when RSI < 30 in a bull market with above-average volume, price bounces 70% of the time. In bear market, bounce rate drops to 40%." Improved calibration. Declining error rate. Context-sensitive.

**Year 5:** Complex integrated knowledge — "the combination of RSI oversold, volume spike, macro support, and sector strength produces a 75% probability of a 3–7% bounce within 5–10 days, unless VIX is above 30, in which case probability drops to 45%." Well-calibrated. Low error recurrence. Multi-variable.

**Year 10:** Strategic knowledge — the system identifies which types of hypotheses to pursue and which to avoid. It allocates learning resources to the most promising areas. It recognizes when its knowledge is insufficient and seeks new evidence before committing capital.

### 8.5 Decision Superiority

The ultimate aspiration is decision superiority: the consistent ability to make better decisions than would be made without the system.

Decision superiority does not mean winning every trade. It means:
- Better calibration (confidence matches accuracy)
- Faster recognition of emerging consequences
- More reliable distinction between signal and noise
- Less repetition of past errors
- Greater adaptability to changing conditions
- More robust performance across different environments

Decision superiority is not measured by a single metric. It is measured by the trajectory of all criterion-relevant metrics over years of operation.

### 8.6 Why Criterion Is Never "Finished"

Criterion is asymptotic. It approaches a limit of perfect calibration and optimal judgment but never reaches it.

The world changes. Markets evolve. New asset classes emerge. New risks appear. New information sources become available. The system that stops learning because it believes it has achieved criterion will inevitably degrade as the world moves past it.

The final principle of decision science for O.M.A.-C.O.R.E. is:

**The best system tomorrow will be the one that learned the most today.**

---

## Self-Review

### S-01: Weak Assumptions

**Assumption: The decision cycle is universal across domains.**
The document asserts that all expert decision-makers follow the same fundamental cycle. This is supported by the literature (Boyd, Klein, Heuer, Popper, Ericsson) but is still a strong claim. Some decision-making models (naturalistic decision making, recognition-primed decisions) emphasize pattern matching over hypothesis competition. The document resolves this by placing pattern recognition in Part VI as an input to hypothesis generation, not as a replacement for it.

**Assumption: Explicit hypothesis competition is superior to implicit pattern matching.**
This is Assumption A-007 from the Assumptions document, applied here at the architectural level. The decision science literature is divided on this. Klein's RPD model suggests experts often decide without comparing multiple options. The document resolves this by treating pattern recognition as the fast, hypothesis-generation layer and explicit competition as the slow, validation layer.

**Assumption: Process evaluation produces better long-term results than outcome evaluation.**
While supported by poker (Duke), forecasting (Tetlock), and deliberate practice (Ericsson), this assumption is not proven for automated trading systems. It is a hypothesis the system itself should help validate.

### S-02: Potential Circular Reasoning

**Decision quality → Process quality → Criterion → Decision quality:**
The document states that decision quality is measured by process quality, that process quality accumulates into criterion, and that criterion improves future decision quality. This is not circular — it is a positive feedback loop — but it means the system must be bootstrapped with initial decisions of unknown quality before the loop can begin.

**Hypothesis → Evidence → Competition → Decision → Outcome → Hypothesis:**
The lifecycle is a cycle, not a circle. Each iteration produces a different outcome (knowledge, reduced uncertainty). The cycle is not repeating the same process — it is spiraling upward with each iteration.

### S-03: Conceptual Overlap with Existing Documents

This document overlaps substantially with:
- **14_HYPOTHESIS_LIFECYCLE_MANAGER.md** — The decision architecture in Part III extends the hypothesis lifecycle by adding the upstream stages (Reality, Uncertainty, Need, Question) that precede hypothesis formation.
- **08_CRITERION.md** — Part VIII extends the Criterion levels by describing what each level looks like in practice after years of operation.
- **04_GLOSSARY.md** — Part I refines the hierarchy from Data to Wisdom, adding Judgment between Knowledge and Criterion.
- **01_THEORY_OF_OMA_CORE.md** — Hypothesis 6 (Criterion Develops Through Validated Experience) is the central cycle the document formalizes.

The overlap is intentional and consistent. No contradictions are introduced.

### S-04: Ideas Lacking Evidence

**Scenario generation as hypothesis behavior (Part V):** The decision to make scenarios a method rather than an object is an architectural hypothesis. It has not been tested. If scenario complexity proves too high for a single method, scenarios may need their own lifecycle.

**Competing hypotheses reducing confirmation bias (Part IV):** While supported by intelligence analysis literature (Heuer), this has not been tested in an automated trading context. The system may find that maintaining multiple hypotheses is too expensive or that the hypotheses converge too quickly to be useful.

**The complete 15-stage decision architecture (Part III):** This architecture is theoretical. It has not been implemented in any system. Every stage is justified by decision science principles, but the integrated whole may reveal emergent problems that the individual stages do not.

### S-05: Hidden Complexity

**Hypothesis competition (Part IV):** The document defines evaluation dimensions (evidence quality, explanatory power, etc.) but does not specify how they should be combined. Aggregating multiple dimensions into a single assessment is non-trivial. The system may need to keep them separate and accept multi-dimensional output rather than a single score.

**Scenario generation (Part V):** Generating specific, falsifiable scenarios from a hypothesis requires a model of how the world works. If the hypothesis is vague ("the market will go up"), scenario generation produces vague scenarios. The system can only generate good scenarios from well-formed hypotheses.

**Calibration tracking (Part VII):** Calibration requires sufficient data points to be meaningful. A hypothesis tracked once produces no calibration information. The system needs hundreds of hypotheses before calibration becomes actionable.

### S-06: Architectural Risks

**Hypothesis generation bottleneck (Part II, Principle 2):** If the system cannot generate enough competing hypotheses, the competition mechanism adds complexity without benefit. The pattern recognition layer must be fast and high-recall.

**Decision threshold calibration (Part III):** Determining when uncertainty has been reduced enough to act is difficult. Too high a threshold produces analysis paralysis. Too low a threshold produces premature action. The optimal threshold is context-dependent and must be learned.

**Reflection overhead (Part VII):** If every outcome triggers a full reflection cycle, the system may spend more time reflecting than acting. The reflection depth should be proportional to the stakes and novelty of the decision.

### S-07: What Should Be Considered Provisional

1. **The complete 15-stage architecture** — This has never been implemented. Every stage is justified but unproven in combination.

2. **The competition dimensions (Part IV)** — The 11 dimensions are reasonable but may need to be adjusted, added to, or removed based on experience.

3. **Scenario generation as hypothesis behavior (Part V)** — This is an architectural hypothesis that should be tested early.

4. **The calibration-as-primary-metric emphasis (Part VII)** — Calibration is informative but not sufficient. A well-calibrated system can still make bad decisions if it is well-calibrated to the wrong probability distribution.

5. **The long-term vision (Part VIII)** — The 10-year trajectory is aspirational. The system may develop differently than predicted.

---

## Final Principle

O.M.A.-C.O.R.E. does not seek perfect predictions. The world is too complex, too stochastic, too full of hidden variables for prediction to ever be reliable.

O.M.A.-C.O.R.E. does not seek perfect decisions. Decisions are made with incomplete information under time pressure. There is no perfect decision — only the best decision given what is known at the time.

O.M.A.-C.O.R.E. seeks **progressively better decisions through disciplined competition between evidence-backed hypotheses.**

Each cycle sharpens the system's judgment. Each error teaches a lesson. Each confirmed hypothesis adds to accumulated knowledge.

The system that wins is not the one that predicts perfectly.

It is the one that, after ten thousand cycles, makes better decisions than it did after one hundred.

---

*This document is a synthesis of principles from military command, intelligence analysis, medicine, firefighting, aviation, chess, scientific research, and decision science. It is not an implementation specification. It is a framework for designing a machine that learns to judge what matters.*

*Every claim in this document is provisional. Evidence always has the final word.*

---

*End of 16_DECISION_SCIENCE.md — Version 1.0 — June 2026*
