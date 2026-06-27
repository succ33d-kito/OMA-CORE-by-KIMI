# Strategic Backlog — Aligned but Premature Ideas

*Version 1.0 — June 2026*
*Lane: YELLOW — Valuable but premature*

---

## Why These Ideas Are Here

The following ideas are aligned with Architecture V2. They would improve Criterion, decision quality, or scarce resource management. But they are premature — the system does not yet have enough evidence, enough operational data, or enough foundational infrastructure to implement them safely.

Implementing them too early would increase complexity before the system is ready to benefit from them. This is not a rejection — it is a timing decision.

---

## Backlog Ideas

---

### 1. Decision DNA

**What it is:** A fingerprint for each decision type — a compressed representation of decision patterns, evidence weighting, and confidence calibration for a specific hypothesis class.

**Why it matters:** Would enable the system to recognize when it is making a decision it has made before, and apply lessons from past outcomes.

**Why not now:** Requires hundreds of decisions with complete scientific records before patterns can be extracted. The system has zero hypothesis-linked decisions today.

**Dependencies:** Iterations 3–5 of the implementation bridge (hypothesis-linked decisions, outcome comparison, DecisionRecord)

**Future validation method:** Compare decisions of the same "DNA" type and verify that outcomes improve over time.

**Scarce resources improved:** Knowledge, Time

**Verdict:** STRATEGIC BACKLOG

---

### 2. Criterion Timeline

**What it is:** A longitudinal visualization of Criterion metrics over time — hypothesis quality, evidence quality, decision quality, calibration, knowledge yield.

**Why it matters:** The project's central claim is that Criterion improves over time. Without a timeline, this claim cannot be evaluated.

**Why not now:** Requires CriterionSnapshot computation (Iteration 7) which requires DecisionRecords (Iteration 5) which requires outcome comparison (Iteration 4). The data pipeline does not exist yet.

**Dependencies:** Iterations 4–7 of the implementation bridge

**Future validation method:** Trend analysis on Criterion metrics over 3, 6, 12-month windows.

**Scarce resources improved:** Knowledge, Attention

**Verdict:** STRATEGIC BACKLOG

---

### 3. Confidence Calibration

**What it is:** Systematic tracking of confidence vs accuracy across decision types. Calibration curves, overconfidence detection, underconfidence detection, calibration improvement over time.

**Why it matters:** Calibration is a core dimension of Criterion (CRITERION_VALIDATION_FRAMEWORK.md). A system that is well-calibrated knows what it knows and what it does not know.

**Why not now:** Requires a statistically significant sample of decisions with both confidence and outcome records. Currently no hypothesis-linked decisions exist.

**Dependencies:** Iterations 3–5 (decision-hypothesis link, outcome comparison), minimum 100 decisions with outcome data

**Future validation method:** Calibration curves per decision type. Brier score tracking. Improvement over time.

**Scarce resources improved:** Knowledge, Capital

**Verdict:** STRATEGIC BACKLOG

---

### 4. Resource Allocation Engine

**What it is:** A formal allocation system that distributes scarce resources (capital, attention, time) across competing opportunities based on hypothesis quality, evidence strength, uniqueness score, and risk.

**Why it matters:** Architecture V2 defines scarce resources as the strategic output. An allocation engine is the mechanism that converts Criterion into resource-efficient decisions.

**Why not now:** Requires the Scarce Resources model to be defined first. Requires Opportunity Uniqueness Score, Missed Opportunity Ledger, and Auto-Approval Readiness Score to exist. Requires outcome data to validate allocation decisions.

**Dependencies:** Green-lane items (P2-1 through P2-5), Scarce Resources model (research), minimum 6+ months of allocation data for validation

**Future validation method:** Compare resource efficiency before and after allocation engine. Verify that allocated resources produce better outcomes than unallocated.

**Scarce resources improved:** All eight

**Verdict:** STRATEGIC BACKLOG

---

### 5. Counterfactual Simulator

**What it is:** A simulation engine that answers: "What would have happened if we chose the alternative?" Uses historical data to simulate alternative decisions and estimate their outcomes.

**Why it matters:** Without counterfactuals, the system cannot estimate opportunity cost or evaluate decision quality independently of outcomes.

**Why not now:** Requires significant data infrastructure, outcome records, and a reliable simulation model. High risk of generating misleading counterfactuals that reinforce incorrect beliefs.

**Dependencies:** Missed Opportunity Ledger, Opportunity Cost Report, minimum 6 months of outcome data

**Future validation method:** Retrospective tests — simulate alternatives and compare to actual outcomes. Requires careful guard against overfitting.

**Scarce resources improved:** Knowledge, Capital

**Verdict:** STRATEGIC BACKLOG

---

### 6. Decision Replay

**What it is:** A tool that replays past decision situations with current knowledge. Enables the user to see: "Given what we know now, would we make the same decision?"

**Why it matters:** Reveals whether the system's criteria are improving or whether it is just seeing the past differently.

**Why not now:** Requires complete DecisionRecords (Iteration 5) which do not exist yet.

**Dependencies:** DecisionRecord (Iteration 5)

**Future validation method:** Compare original decision quality scores with replay scores. Improvement over time indicates Criterion growth.

**Scarce resources improved:** Knowledge

**Verdict:** STRATEGIC BACKLOG

---

### 7. Cognitive Bias Detector

**What it is:** A module that flags potential cognitive biases in hypotheses and decisions — confirmation bias, anchoring, availability bias, survivorship bias, hindsight bias.

**Why it matters:** The project's philosophy explicitly rejects bias as a source of error. A detector helps the system catch its own reasoning errors.

**Why not now:** Requires a sufficient volume of hypotheses and decisions to establish bias baselines. Risk of false positives (flagging correct reasoning as bias).

**Dependencies:** Scientific Store with 100+ hypotheses, decision records with reasoning traces

**Future validation method:** Compare flagged decisions with actual outcomes. Verify that bias flags correlate with decision errors.

**Scarce resources improved:** Knowledge, Capital

**Verdict:** STRATEGIC BACKLOG

---

### 8. Unknown Detector

**What it is:** A module that estimates how much the system does not know about a given situation — based on evidence sparsity, hypothesis coverage, and past prediction error in similar contexts.

**Why it matters:** A system that knows its own ignorance makes better decisions about when to act vs wait.

**Why not now:** Requires significant calibration data and a formal uncertainty model. Currently no mechanism exists to quantify unknown-unknowns.

**Dependencies:** Confidence Calibration, minimum 6 months of decision data

**Future validation method:** Verify that high-uncertainty decisions have more variable outcomes. Verify that uncertainty estimates improve over time.

**Scarce resources improved:** Capital, Attention (prevents action when the system should wait)

**Verdict:** STRATEGIC BACKLOG

---

### 9. Research Agent

**What it is:** An agent that reads research, documentation, and external sources to generate new hypotheses and identify evidence relevant to existing ones.

**Why it matters:** Would automate the literature review and evidence gathering that currently requires manual effort.

**Why not now:** Requires the full scientific layer to be operational with linked decisions and outcomes. Automated evidence integration is complex and error-prone.

**Dependencies:** Iterations 1–6 (full scientific pipeline), external source integration

**Future validation method:** Compare hypotheses generated by Research Agent with human-generated hypotheses. Measure hit rate.

**Scarce resources improved:** Time, Knowledge

**Verdict:** STRATEGIC BACKLOG

---

### 10. Knowledge Decay

**What it is:** A mechanism that automatically expires or reduces the weight of knowledge that has not been confirmed or applied recently. Knowledge gets weaker over time unless reinforced.

**Why it matters:** Markets and conditions change. Knowledge that was valid in one regime may become invalid in another. Decay prevents the system from relying on stale lessons.

**Why not now:** Requires Knowledge schema and lifecycle (Iteration 6) which do not exist yet.

**Dependencies:** Knowledge extraction (Iteration 6), minimum 1 year of knowledge data to calibrate decay rates

**Future validation method:** Verify that decayed knowledge is less predictive than fresh knowledge. Adjust decay rates based on evidence.

**Scarce resources improved:** Knowledge, Capital

**Verdict:** STRATEGIC BACKLOG

---

### 11. Decision Market

**What it is:** An internal prediction market where agents or hypotheses compete for credibility. Hypotheses that prove correct gain influence. Hypotheses that fail lose it.

**Why it matters:** Would create an emergent mechanism for hypothesis selection without centralized weighting.

**Why not now:** Requires a large number of hypotheses with known outcomes. Prediction markets require significant volume to produce reliable signals.

**Dependencies:** 100+ completed hypothesis lifecycles (evaluated hypotheses), outcome comparison

**Future validation method:** Compare market-selected hypotheses against council-selected ones. Verify that market mechanism converges faster.

**Scarce resources improved:** Knowledge, Capital

**Verdict:** STRATEGIC BACKLOG

---

### 12. World Memory

**What it is:** A structured representation of the system's understanding of how the world works — causal relationships, regime changes, correlation patterns — built from accumulated knowledge.

**Why it matters:** Explicit world models enable the system to reason about novel situations using general principles rather than pattern matching.

**Why not now:** Requires significant accumulated knowledge (Iteration 6+). World model construction is an active research area — premature implementation would likely be incorrect.

**Dependencies:** Iterations 6–7 (knowledge, CriterionSnapshot), research findings

**Future validation method:** Compare world model predictions with actual outcomes. Measure prediction accuracy improvement over time.

**Scarce resources improved:** Knowledge, All others indirectly

**Verdict:** STRATEGIC BACKLOG

---

### 13. Black Swan Archive

**What it is:** A structured collection of extreme, unexpected events that the system did not predict. Each black swan is analyzed for: what happened, why it was not anticipated, what hypotheses failed, what can be learned.

**Why it matters:** The most important learning often comes from failures. A black swan archive ensures the system learns from its most significant blind spots.

**Why not now:** Requires outcome comparison (Iteration 4) and error classification to identify which outcomes were genuinely unpredictable vs predictably missed.

**Dependencies:** Iterations 4–5 (outcome comparison, error classification)

**Future validation method:** Track black swan frequency over time. Verify that fewer events become black swans as the system learns.

**Scarce resources improved:** Knowledge, Capital

**Verdict:** STRATEGIC BACKLOG

---

### 14. Human Override Learning

**What it is:** A mechanism that records when the human overrides the system's recommendation, and learns from the override outcome. Did the human's override improve or worsen the outcome?

**Why it matters:** The human is the most important sensor in the system. Every override contains information about where the system's judgment diverges from the user's.

**Why not now:** Requires Level 1–2 autonomy to be operational first. Without automatic decisions, there are no overrides to learn from.

**Dependencies:** Decision Approval Engine, Level 2 autonomy implementation

**Future validation method:** Track override frequency and override outcome. Verify that the system learns to reduce override frequency over time (except when human judgment is superior).

**Scarce resources improved:** Knowledge, All others through better alignment with user intent

**Verdict:** STRATEGIC BACKLOG

---

### 15. Scarce Resources Dashboard

**What it is:** A dashboard showing the status of all eight scarce resources — capital growth, time saved, attention preserved, knowledge accumulated, relationships developed, mobility maintained, health indicators, freedom of decision.

**Why it matters:** Without visibility into all scarce resources, the system will optimize the visible ones (capital) at the expense of invisible ones (attention, health, freedom).

**Why not now:** Requires the Scarce Resources model to be formally defined. Most resources lack measurement mechanisms today.

**Dependencies:** Scarce Resources model (research), operational data for each resource type

**Future validation method:** Verify dashboard trends correlate with user-reported well-being across all resource dimensions.

**Scarce resources improved:** All eight (awareness is the first step to optimization)

**Verdict:** STRATEGIC BACKLOG

---

## Summary

| # | Idea | Complexity | Key Dependency | Estimated Horizon |
|---|------|------------|----------------|-------------------|
| 1 | Decision DNA | High | 100+ hypothesis-linked decisions | 12+ months |
| 2 | Criterion Timeline | Medium | CriterionSnapshot (Iteration 7) | 12+ months |
| 3 | Confidence Calibration | Medium | 100+ decision records | 6–12 months |
| 4 | Resource Allocation Engine | High | Green-lane items + Scarce Resources model | 12+ months |
| 5 | Counterfactual Simulator | Very High | Ledger + 6 months outcome data | 18+ months |
| 6 | Decision Replay | Medium | DecisionRecord (Iteration 5) | 6–12 months |
| 7 | Cognitive Bias Detector | Medium | 100+ hypotheses | 12+ months |
| 8 | Unknown Detector | High | Confidence Calibration + 6 months data | 12+ months |
| 9 | Research Agent | Very High | Full scientific pipeline | 18+ months |
| 10 | Knowledge Decay | Medium | Knowledge lifecycle (Iteration 6) | 12+ months |
| 11 | Decision Market | High | 100+ completed hypotheses | 18+ months |
| 12 | World Memory | Very High | Significant knowledge accumulation | 24+ months |
| 13 | Black Swan Archive | Medium | Outcome comparison (Iteration 4) | 6–12 months |
| 14 | Human Override Learning | Medium | Level 2 autonomy | 18+ months |
| 15 | Scarce Resources Dashboard | Medium | Scarce Resources model | 12+ months |

---
