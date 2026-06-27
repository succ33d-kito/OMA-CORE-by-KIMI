# Research Lab — Open Questions

*Version 1.0 — June 2026*
*Lane: ORANGE — Unresolved questions requiring experiments before design*

---

## Purpose

The Research Lab contains questions that the project does not yet have enough evidence to answer. These are not feature requests — they are unresolved scientific and architectural questions that must be investigated before certain design decisions can be made.

Each question is a research hypothesis. The goal is not to produce an answer immediately, but to design experiments that will produce evidence over time.

---

## Research Questions

---

### RQ-01: Can Criterion be measured directly, or only inferred from better decisions?

**Why it matters:** The central claim of the project is that Criterion develops over time. Without a valid measurement approach, this claim cannot be tested.

**Current assumption:** Criterion is best measured indirectly — through converging evidence across reasoning quality, decision quality, and outcome quality over time (per CRITERION_VALIDATION_FRAMEWORK.md). Direct measurement may be impossible because Criterion is an emergent property.

**Possible experiment:** Once CriterionSnapshot exists, compare direct Criterion scores with the outcome-based inference. If they consistently agree, either may be valid. If they diverge, investigate which is more predictive of future decision quality.

**Required data:** 12+ months of operational data with complete decision records, outcome comparisons, and CriterionSnapshot measurements.

**Status:** OPEN

---

### RQ-02: Can Criterion decay?

**Why it matters:** If Criterion decays without reinforcement, the system must actively maintain it. If it compounds permanently, the system only needs to add to it.

**Current assumption:** Criterion can decay when the operating environment changes. Knowledge that was valid in one market regime may mislead in another. However, the ability to detect regime changes and adapt should not decay — that is meta-Criterion.

**Possible experiment:** Compare decision quality during stable market regimes vs regime transitions. If decision quality drops during transitions and recovers slowly, Criterion decays during regime changes.

**Required data:** 12+ months of operational data spanning at least two distinct market regimes.

**Status:** OPEN

---

### RQ-03: Can false evidence create false Criterion?

**Why it matters:** If the system learns from evidence that turns out to be incorrect, it may develop confidence in wrong beliefs. The question is whether the system can detect and recover from false evidence.

**Current assumption:** False evidence can create locally incorrect beliefs, but the Criterion framework (hypothesis → outcome → comparison → correction) eventually corrects for it. The risk is proportional to the validation cycle time — longer cycles mean more decisions based on false evidence.

**Possible experiment:** Inject known-false evidence into hypotheses and track whether the system detects and corrects the error over successive outcome cycles.

**Required data:** Simulated experiments within the scientific layer. No operational impact.

**Status:** OPEN

---

### RQ-04: How much memory is enough?

**Why it matters:** The system currently has short-term memory (1-hour TTL), long-term memory (tagged, persistent), and the scientific store (hypotheses and evidence). There is no principled basis for retention periods.

**Current assumption:** Scientific records (hypotheses, evidence, decisions) should be retained indefinitely. Operational data (raw events, telemetry) can be aged out after it is no longer useful for analysis. The boundary between scientific and operational is defined in ARCHITECTURE_V2.md.

**Possible experiment:** Once the system has 12+ months of data, test whether pruning old operational data changes the quality of Criterion analysis.

**Required data:** 12+ months of telemetry and operational records.

**Status:** OPEN

---

### RQ-05: When should knowledge expire?

**Why it matters:** Knowledge that was valid in one regime may become invalid in another. Without expiration, the system may confidently apply invalid knowledge.

**Current assumption:** Knowledge should have a decay function tied to the stability of the conditions under which it was validated. Knowledge validated in stable conditions decays slower. Knowledge from volatile conditions decays faster.

**Possible experiment:** Assign decay rates based on market volatility at validation time. Compare: does fast-decay knowledge produce fewer errors than no-decay knowledge?

**Required data:** 6+ months of knowledge records with outcome data.

**Status:** OPEN

---

### RQ-06: Can the system detect when it does not know enough?

**Why it matters:** A system that knows its own ignorance makes better decisions about when to act vs wait. This is the foundation of the Unknown Detector (Strategic Backlog item 8).

**Current assumption:** The system can estimate its ignorance based on evidence sparsity, hypothesis coverage, confidence variance, and prediction error variance. But this is untested.

**Possible experiment:** Compare the system's ignorance estimates with actual outcome variance. If high-ignorance decisions produce more variable outcomes, the estimate is valid.

**Required data:** 100+ decisions with confidence records and known outcomes.

**Status:** OPEN

---

### RQ-07: Can decision quality improve even when short-term PnL is negative?

**Why it matters:** If yes, the project's thesis is supported — PnL is not the only metric. If no, the thesis is weakened and PnL becomes a necessary (not just correlated) measure.

**Current assumption:** Yes. Decision quality and PnL are not perfectly correlated over short periods due to market noise, timing variance, and luck. Over longer periods they should converge. This is stated in the Theory and Discoveries documents but has never been tested with the system's own data.

**Possible experiment:** Identify periods where decision quality improved but PnL was flat or negative. Analyze whether this was due to bad luck (correct decisions, adverse market) or flawed quality metrics.

**Required data:** 6+ months of decision quality scores and PnL data.

**Status:** OPEN

---

### RQ-08: Can trading Criterion transfer to creator/business domains?

**Why it matters:** The project's long-term vision extends beyond trading. If Criterion does not transfer, the system's applicability is limited to financial markets.

**Current assumption:** Yes, with limits. Pattern recognition and probabilistic reasoning skills transfer. Domain-specific knowledge does not. The structure of hypothesis formation and evidence evaluation should transfer, but the content (market-specific patterns) will not.

**Possible experiment:** Design a non-trading hypothesis test (e.g., content publishing decisions, business opportunity evaluation). Compare Criterion development between trading and non-trading domains.

**Required data:** Non-trading domain data. This requires manual collection or a second operational domain.

**Status:** OPEN

---

### RQ-09: How should opportunity cost be estimated for missed trades?

**Why it matters:** Opportunity cost is essential for evaluating decision quality, but missed trades do not produce outcomes that can be measured directly.

**Current assumption:** Opportunity cost for missed trades can be estimated by: (a) simulating the outcome of the rejected opportunity using the same execution logic, or (b) using a baseline like "average outcome of taken trades" adjusted for similarity. Both approaches have significant error.

**Possible experiment:** Compare estimated opportunity cost with actual outcomes of trades that were similar to missed ones. Measure estimation error and refine the model.

**Required data:** Missed Opportunity Ledger data, 6+ months of trade outcomes.

**Status:** OPEN

---

### RQ-10: How can the system compare a taken decision with an untaken alternative?

**Why it matters:** This is the core of counterfactual reasoning. Without it, the system cannot know if it made the best choice among alternatives.

**Current assumption:** Counterfactual comparison requires either: a simulator that can run alternative histories, or a statistical baseline (e.g., "decisions of this type produce X average outcome"). Both are high-risk: simulators can be misleading, baselines can be biased.

**Possible experiment:** Start with simple baselines (average outcome of same-decision-type). Compare against more sophisticated methods as data accumulates. Measure whether more complex methods produce materially different conclusions.

**Required data:** DecisionRecord (Iteration 5), 12+ months of data.

**Status:** OPEN

---

### RQ-11: What is the minimum evidence threshold for autonomous execution?

**Why it matters:** Level 2 autonomy (auto-execute with approval) requires knowing when a decision is safe to automate. There is currently no theory for what threshold is sufficient.

**Current assumption:** The threshold should be calibrated empirically — start high (require strong evidence, high confidence, low risk) and lower as the system demonstrates reliable execution. The Auto-Approval Readiness Score (P2-3) is the mechanism.

**Possible experiment:** Simulate thresholds on historical decisions. Find the threshold that would have approved only decisions that produced positive outcomes, within a confidence interval.

**Required data:** 100+ approval-ready decisions with known outcomes.

**Status:** OPEN

---

### RQ-12: Can scarce resources be modeled as capital classes?

**Why it matters:** If scarce resources can be modeled with the same mathematical framework as capital (returns, risk, allocation, compounding), then portfolio theory can be applied to resource allocation.

**Current assumption:** Partially. Capital, time, and attention may be modelable as capital classes (fungible, quantifiable, measurable). Relationships, health, and freedom are less fungible and may require different models.

**Possible experiment:** Model capital, time, and attention as capital classes. Track their returns over 6 months. Verify whether the model produces useful allocation insights.

**Required data:** Time and attention tracking data. Baseline capital PnL data.

**Status:** OPEN

---

### RQ-13: How does the system avoid overfitting to recent market regimes?

**Why it matters:** A system that learns only from recent data will overfit to the current regime and fail when the regime changes.

**Current assumption:** The system avoids overfitting through: (a) maintaining hypotheses that test different regime assumptions, (b) tracking knowledge validity across regimes, (c) using evidence decay. But none of these have been tested.

**Possible experiment:** Compare system performance during and after regime changes. Measure how quickly the system adapts vs how much it overfits.

**Required data:** 12+ months of data spanning at least two distinct market regimes.

**Status:** OPEN

---

### RQ-14: What makes a hypothesis worth creating?

**Why it matters:** Not all hypotheses are valuable. A hypothesis that is too vague, too specific, untestable, or irrelevant wastes resources.

**Current assumption:** A hypothesis is worth creating if it is testable, falsifiable, has a clear consequence prediction, and addresses a gap in the system's understanding. But this is a qualitative guideline, not a quantitative filter.

**Possible experiment:** Track which hypothesis attributes correlate with eventual validation (confirmed or rejected with clear learning). Build a predictive model of hypothesis value.

**Required data:** 100+ hypotheses with known outcomes.

**Status:** OPEN

---

### RQ-15: What makes a hypothesis worth killing?

**Why it matters:** Hypotheses that are never killed accumulate and dilute the system's focus. There must be criteria for archiving or abandoning hypotheses before they reach a natural end.

**Current assumption:** A hypothesis should be killed if: (a) its invalidation conditions are met, (b) it has not produced new evidence in N evaluation cycles, (c) a better hypothesis replaces it. These criteria have not been tested.

**Possible experiment:** Set an auto-archive time limit for hypotheses that have not been updated or evaluated. Measure whether archived hypotheses would have become relevant later (false positives) or were correctly retired.

**Required data:** 100+ hypotheses with lifecycle data.

**Status:** OPEN

---

### RQ-16: How can the Innovation Engine improve its own innovation process?

**Why it matters:** The Innovation Engine must not be exempt from the principles it enforces. It must also be subject to evidence-based improvement.

**Current assumption:** The Innovation Engine's effectiveness can be measured by: (a) what percentage of implemented ideas produced their expected impact, (b) what percentage of rejected ideas would have been useful (false negatives), (c) cycle time from idea to validation.

**Possible experiment:** Track Innovation Engine metrics. Review quarterly. Adjust the process based on evidence.

**Required data:** Innovation Engine usage data over 12 months.

**Status:** OPEN

---

## Summary

| # | Question | Key Uncertainty | Estimated Resolution |
|---|----------|-----------------|---------------------|
| RQ-01 | Can Criterion be measured directly? | Measurement validity | 12+ months |
| RQ-02 | Can Criterion decay? | Environmental stability | 12+ months |
| RQ-03 | Can false evidence create false Criterion? | Error recovery | 6–12 months (simulated) |
| RQ-04 | How much memory is enough? | Retention policy | 12+ months |
| RQ-05 | When should knowledge expire? | Decay function | 12+ months |
| RQ-06 | Can the system detect ignorance? | Uncertainty estimation | 6–12 months |
| RQ-07 | Can decision quality improve during negative PnL? | Thesis validation | 6+ months |
| RQ-08 | Can trading Criterion transfer? | Domain generality | 24+ months |
| RQ-09 | How to estimate opportunity cost for missed trades? | Counterfactual estimation | 12+ months |
| RQ-10 | Compare taken vs untaken alternatives? | Counterfactual methodology | 12+ months |
| RQ-11 | Minimum evidence threshold for autonomy? | Safety boundary | 12+ months |
| RQ-12 | Scarce resources as capital classes? | Modeling framework | 12+ months |
| RQ-13 | Avoid overfitting to regimes? | Regime adaptation | 12+ months |
| RQ-14 | What makes a hypothesis worth creating? | Value prediction | 12+ months |
| RQ-15 | What makes a hypothesis worth killing? | Lifecycle optimization | 12+ months |
| RQ-16 | Improve the Innovation Engine? | Meta-innovation | 12+ months |

---
