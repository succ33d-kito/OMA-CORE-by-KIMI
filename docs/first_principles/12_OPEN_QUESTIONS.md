# Open Questions

*The biggest unanswered scientific questions that O.M.A.-C.O.R.E. must eventually address.*

---

## Reality Questions

### Q-001: Can Every Consequence Be Detected?

**Question:** Are there fundamental limits to consequence detection? Are some consequences inherently undetectable regardless of the quality of perception and analysis?

**Importance:** Critical — if some consequences are undetectable, the project must know which ones.

**Difficulty:** Very high — this is a question about the nature of complex systems, not a solvable engineering problem.

**Current evidence:** Chaos theory suggests that some systems are fundamentally unpredictable beyond certain time horizons. Noise and signal are not always distinguishable. The efficient market hypothesis suggests that some consequences are immediately priced in and therefore undetectable as opportunities.

**Blocking dependencies:** None — this is a theoretical question, not an implementation dependency.

**Possible experiments:** Systematic analysis of consequence detection accuracy across different time horizons, market conditions, and event types. Identify where detection accuracy drops to chance levels.

---

### Q-002: Can Criterion Decay?

**Question:** If criterion is not continuously exercised, does it degrade? Can the system lose its accumulated judgment through inactivity, regime changes, or memory degradation?

**Importance:** High — if criterion decays, the system requires continuous operation to maintain its capability.

**Difficulty:** Medium — testable over time with controlled experiments.

**Current evidence:** Human expertise decays without practice. Machine learning models experience catastrophic forgetting. Memory systems degrade if not maintained.

**Contradicting evidence:** Some forms of knowledge are persistent once learned (riding a bicycle, language). Structured memory may be more persistent than neural weights.

**Possible experiments:** Measure criterion-relevant metrics before and after periods of inactivity. Test whether criterion developed in one market regime remains valid in a different regime.

---

### Q-003: Can False Memories Create False Criterion?

**Question:** If the system incorrectly stores or misremembers an outcome, can it develop criterion based on false information? How vulnerable is criterion development to memory corruption?

**Importance:** High — if false memories produce false criterion, memory integrity is critical.

**Difficulty:** Medium — testable with controlled memory corruption experiments.

**Current evidence:** Human memory is highly fallible and subject to reconstruction. False memories in humans produce confident but incorrect beliefs. The same may apply to artificial memory systems.

**Possible experiments:** Introduce controlled errors into the system's memory and measure whether criterion degrades or self-corrects.

---

## Learning Questions

### Q-004: How Much Memory Is Enough?

**Question:** How many hypotheses, outcomes, and learning cycles are needed before criterion reaches a practically useful level? Is there a minimum threshold below which criterion is indistinguishable from random?

**Importance:** Medium — informs expectations about development timelines.

**Difficulty:** Medium — can be measured empirically as the system operates.

**Current evidence:** Human expertise typically requires thousands of hours of deliberate practice. The OSIRIS system has processed hundreds of cycles and ~10 trades. This is almost certainly insufficient.

**Possible experiments:** Measure criterion-relevant metrics as functions of cumulative experience. Identify the inflection point where improvement becomes detectable.

---

### Q-005: Should Knowledge Expire?

**Question:** Does evidence have a shelf life? Should old outcomes be discounted or eventually deleted? Does knowledge from five years ago still inform today's decisions, or has the world changed enough to make it misleading?

**Importance:** Medium-High — affects memory architecture and evidence weighting.

**Difficulty:** Medium — testable with time-weighted evidence comparisons.

**Current evidence:** Most financial strategies decay over time as markets evolve. Patterns that worked in the 1990s may not work today. Some knowledge (risk management principles, behavioral biases) appears more persistent.

**Possible experiments:** Compare systems with different evidence decay rates. Measure whether old evidence improves or degrades decision quality.

---

### Q-006: Can Confidence Be Calibrated Automatically?

**Question:** Can the system learn to calibrate its confidence estimates so that 70% confidence means 70% accuracy, without explicit calibration mechanisms?

**Importance:** Medium-High — calibrated confidence is essential for criterion.

**Difficulty:** Medium — calibration is a well-studied problem in forecasting and decision science.

**Current evidence:** Human confidence calibration is poor without training. Statistical calibration methods exist (Platt scaling, isotonic regression) but require sufficient data.

**Possible experiments:** Track the relationship between confidence and accuracy over time. Measure whether calibration improves naturally or requires explicit intervention.

---

### Q-007: Can the System Detect Its Own Ignorance?

**Question:** Can the system distinguish between "I know this is a good opportunity" and "I have no idea whether this is a good opportunity"? Can it recognize the limits of its own knowledge?

**Importance:** High — a system that does not know what it does not know is dangerous.

**Difficulty:** High — this is related to the problem of metacognition in AI, which is an open research area.

**Current evidence:** Most AI systems have no mechanism for detecting their own ignorance. They produce confident outputs regardless of whether their training data supports the conclusion. Some progress has been made in uncertainty estimation for neural networks.

**Possible experiments:** Design scenarios where the system lacks relevant experience and measure whether it correctly identifies its lack of knowledge.

---

## Architecture Questions

### Q-008: Should Hypotheses Become First-Class Objects?

**Question:** Should the system have an explicit Hypothesis object that is created, tracked, updated, and retired as a core data structure? Or is implicit hypothesis management sufficient?

**Importance:** Medium — affects the next major architectural decision.

**Difficulty:** Low-Medium — implementationally straightforward, but the decision affects the entire learning architecture.

**Current evidence:** The OSIRIS system does not have explicit hypothesis objects. Hypotheses are embedded in trade metadata and agent opinions. This works but limits the ability to track hypothesis evolution over time.

**Possible experiments:** Build a prototype with explicit hypothesis objects and compare learning efficiency against the implicit system.

---

### Q-009: Should Memory Ever Be Deleted?

**Question:** Is there ever a reason to delete memory entries? Or should memory be append-only and uneditable?

**Importance:** Medium — affects memory architecture.

**Difficulty:** Low-Medium — implementationally straightforward but philosophically significant.

**Current evidence:** Append-only systems have strong integrity properties (blockchain, audit logs). Editable systems are more flexible but can lose information. The trade-off is between integrity and flexibility.

**Possible experiments:** Compare append-only vs editable memory architectures on measures of criterion development and error correction.

---

### Q-010: Can Criterion Be Measured?

**Question:** Can criterion be measured directly, or can it only be inferred from behavior? If it can be measured, what are the measurement dimensions?

**Importance:** Critical — if criterion cannot be measured, it cannot be validated.

**Difficulty:** High — this is a psychometrics-level problem for artificial systems.

**Current evidence:** Some dimensions (calibration, error classification) can be measured. Others (judgment quality, wisdom) are harder to define operationally. The Criterion document proposes seven conceptual levels but does not specify measurement methods.

**Possible experiments:** Develop a criterion measurement battery analogous to IQ tests or expertise assessment. Validate it against long-term decision quality.

---

## Trading-Specific Questions

### Q-011: How Early Is "Early"?

**Question:** In the context of trading, what constitutes "early" consequence detection? How far before the consensus does a consequence need to be detected to have value? Is there an optimal detection window?

**Importance:** Medium — affects signal filtering and opportunity prioritization.

**Difficulty:** Medium — can be measured empirically.

**Current evidence:** In trading, being too early is indistinguishable from being wrong. The market can remain irrational longer than the trader can remain solvent. There is a tension between early detection and timing accuracy.

**Possible experiments:** Measure the relationship between detection time (how early) and outcome (PnL) across many trades. Identify the optimal detection window for different asset classes.

---

### Q-012: What Defines a Truly Valuable Opportunity?

**Question:** Beyond PnL, what makes an opportunity valuable? Is value purely monetary, or are there dimensions like learning potential, hypothesis quality, or strategic significance?

**Importance:** Medium — affects how opportunities are ranked and prioritized.

**Difficulty:** Medium — requires defining a multi-dimensional value function.

**Current evidence:** The current OSIRIS system ranks opportunities by conviction and risk score. This is a reasonable starting point but may miss important dimensions.

**Possible experiments:** Compare single-dimensional (PnL) vs multi-dimensional (PnL + learning + hypothesis quality) opportunity valuation on long-term system performance.

---

### Q-013: How Should Opportunity Quality Be Measured?

**Question:** What metrics, besides win rate and PnL, capture opportunity quality? How do these metrics relate to each other?

**Importance:** Medium — affects how the system evaluates its own performance.

**Difficulty:** Medium — requires defining and validating quality metrics.

**Current evidence:** Standard metrics include win rate, average win/loss, Sharpe ratio, and maximum drawdown. None of these capture opportunity quality independently of execution quality.

**Possible experiments:** Develop opportunity quality metrics that are independent of execution. Compare their predictive power for long-term system health.

---

## Long-Term Questions

### Q-014: Can Criterion Transfer from Trading to Business?

**Question:** Can the criterion developed through trading experience improve business decisions? Is the judgment of "this consequence is forming" equally valuable in trading, entrepreneurship, and creation?

**Importance:** Critical — this determines whether O.M.A.-C.O.R.E. can fulfill its multi-profile vision.

**Difficulty:** Very high — requires operating across domains for extended periods.

**Current evidence:** No evidence exists. This is a question the project exists to answer.

**Possible experiments:** After developing criterion in trading, apply the same framework to business or creation decisions. Measure whether criterion quality transfers.

---

### Q-015: Can the Same Intelligence Power Every Profile?

**Question:** Does the intelligence that powers a Trader profile also power Creator and Entrepreneur profiles? Or does each profile require its own intelligence core?

**Importance:** High — affects the fundamental architecture.

**Difficulty:** High — requires multi-domain validation.

**Current evidence:** The MetaCouncil architecture assumes a shared intelligence core with profile-specific multipliers. This is a hypothesis, not a proven design.

**Possible experiments:** Develop a second profile and measure whether it benefits from the first profile's experience.

---

### Q-016: Can Consequence Intelligence Become Domain-Independent?

**Question:** Can the system's ability to detect consequences become independent of the domain in which it was trained? Or is consequence detection always domain-specific?

**Importance:** High — determines whether the system can eventually generalize.

**Difficulty:** Very high — this is a long-term research question.

**Current evidence:** Human intelligence can transfer abstract reasoning across domains, but concrete expertise is domain-specific. The question is whether consequence detection is abstract or concrete.

**Possible experiments:** Train consequence detection in financial markets, then test in geopolitical, social, or technological domains.
