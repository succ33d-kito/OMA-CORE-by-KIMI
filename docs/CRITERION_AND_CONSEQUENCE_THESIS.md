# Criterion & Consequence Thesis

## O.M.A.-C.O.R.E. Strategic Direction

*Version 1.0 — June 2026*

---

## 1. Executive Summary

O.M.A.-C.O.R.E. is not mainly a trading bot, not a dashboard, not a chatbot, and not merely a multi-agent framework. Its deeper purpose is to develop operational criterion over time.

> *"El propósito de O.M.A.-C.O.R.E. no es predecir el futuro. Es desarrollar criterio suficiente para reconocer las consecuencias más probables antes que la mayoría, aprendiendo continuamente de cada hipótesis, cada decisión y cada resultado."*

The system should evolve across three horizons:

| From | Toward |
|------|--------|
| Event detection | Consequence detection |
| Opportunity generation | Hypothesis tracking |
| Trading signals | Outcome-based learning |
| Reactive triggers | Criterion development |

The current OSIRIS pipeline — WorldMonitorV2 through PaperTradingEngine — is the **first concrete instantiation** of this vision. Trading provides the fastest, most measurable feedback loop for criterion development. But the architecture should be judged by one question: *Does this component help the system detect, explain, validate, or learn from consequences?*

---

## 2. Core Thesis

```
World information produces events.
Events produce correlations.
Correlations form clusters.
Clusters suggest consequences.
Consequences become hypotheses.
Hypotheses translate into opportunities.
Opportunities lead to actions.
Actions produce outcomes.
Outcomes become memory.
Memory becomes knowledge.
Knowledge accumulated over time becomes criterion.
```

This is the full chain from raw information to operational wisdom. Every component of O.M.A.-C.O.R.E. should eventually map to one or more links in this chain — either generating, refining, or learning from it.

The current system covers: events → actions → outcomes → memory. The gap is the middle: clusters, consequences, hypotheses, and explicit criterion accumulation.

---

## 3. Definitions

### Event
A discrete piece of world information: a price movement, a news headline, a macroeconomic release, a social signal. The atomic input.

### Correlation
A statistical or structural relationship between two or more events. Rate cuts correlate with gold prices. Weak dollar correlates with exports.

### Cluster
A group of related events and correlations pointing toward the same possible consequence. Not just many events — events that together reinforce, contradict, or modify a consequence hypothesis.

### Consequence
A possible future state of the world that may emerge from the events and correlations observed. The system's best guess at "what comes next."

### Hypothesis
A structured, recorded belief about a consequence. Contains triggering events, supporting correlations, confidence, evidence, invalidation conditions, and a time horizon. The unit of learning.

### Opportunity Candidate
A consequence that could be acted upon — traded, invested in, or otherwise monetized — but has not yet passed the threshold for action.

### Actionable Opportunity
An opportunity candidate that has met the system's criterion threshold for action. Becomes a TradeSignal (in the trading context) or similar action primitive.

### Action
The execution of an opportunity. In trading: opening a position. In Creator context: publishing content. In Entrepreneur context: a business decision.

### Outcome
The measurable result of an action. Profit or loss. Engagement or silence. Advantage gained or missed.

### Memory
Stored outcomes, decisions, hypotheses, and events. Raw material for learning.

### Knowledge
Processed memory: patterns extracted, correlations validated, heuristics formed, biases identified.

### Criterion
The system's accumulated ability to judge what matters. Not a model — an ongoing, self-correcting calibration of how the system evaluates evidence, forms hypotheses, takes action, and learns from results.

> **Data** is what happened.
> **Knowledge** is what it means.
> **Consequence** is what may follow.
> **Opportunity** is how the consequence can be monetized or used.
> **Outcome** is what actually happened.
> **Criterion** is the system's accumulated ability to judge what matters.

---

## 4. Why Criterion Matters

Prediction asks: *"What will happen?"*

Criterion asks: *"What consequences are forming, how reliable is this hypothesis, what evidence supports it, what could invalidate it, and what action is justified?"*

The difference is structural, not semantic.

A prediction is a single output. It is right or wrong. When it is wrong, the system learns little — the model may adjust weights, but the reason for failure is opaque.

Criterion is a judgment framework. When criterion is wrong, the system can trace the failure to a specific node: was the event misinterpreted? Was the correlation spurious? Was the consequence correct but the timing wrong? Was the hypothesis valid but execution poor?

**Long-term advantage does not come from better models alone.** Models improve marginally each cycle. Criterion compounds: every hypothesis tested, every outcome recorded, every error classified becomes part of the system's accumulated judgment.

After one year, a prediction model and a criterion system may perform similarly. After five years, the criterion system has five years of structured decision memory. The prediction model has five years of retrained weights. These are not the same thing.

---

## 5. Trading-First Focus

Trading remains the correct initial validation domain for three reasons:

1. **Fast feedback loops** — A trade hypothesis is validated or invalidated in hours or days, not months or years.
2. **Measurable outcomes** — Profit and loss are unambiguous. There is no subjective interpretation of "was this action correct?"
3. **Clear consequence chain** — Event → correlation → cluster → consequence → hypothesis → opportunity → action → outcome is straightforward in financial markets.

Creator and Entrepreneur profiles are future translations of the **same consequence intelligence**, not separate brains. A Creator profile needs to detect a cultural consequence before it becomes mainstream. An Entrepreneur profile needs to detect an operational or market consequence before competitors do. The underlying mechanism — detecting early, tracking evidence, forming hypotheses, taking measured action, learning from outcomes — is identical.

**During validation, O.M.A.-C.O.R.E. should focus primarily on trading** before expanding to other profiles. Trading is where criterion is forged.

---

## 6. Consequence Engine Concept

The Consequence Engine is a future component that answers:

- What consequences may emerge from this event?
- Which markets, prices, companies, sectors, or assets may be affected?
- Which consequences are already obvious (priced in)?
- Which consequences are still early (not yet priced)?
- Which consequences are potentially profitable?
- Which consequences are invalidated by new evidence?

The Consequence Engine does not replace the current agent swarm. It sits **above** it — observing the same events but asking a different question. The current agents ask: *"What signal does this generate?"* The Consequence Engine asks: *"What future state does this point toward?"*

The system should not merely detect more information. It should detect **more important consequences** — consequences that are early relative to the consensus, supported by converging evidence, and actionable within the system's capabilities.

For MVP purposes, the Consequence Engine is **not authorized** for implementation. It is documented here as a north star for architectural decisions.

---

## 7. Cluster Intelligence

A cluster is a group of related events reinforcing, contradicting, or modifying a consequence hypothesis.

**Example of cluster formation:**

```
Rate cuts
  + Weak dollar
  + Gold ETF inflows
  + Mining sector strength
  + Inflation expectations rising
  ─────────────────────────────
  Cluster → Bullish gold / precious metals consequence
```

A single event rarely justifies action. A single correlation is often spurious. But when multiple independent signals converge on the same consequence, hypothesis confidence increases.

Clusters also handle contradiction. If rising rate cuts suggest gold bullishness but a sudden dollar rally contradicts it, the cluster updates — evidence for and evidence against are tracked together.

Current OSIRIS agents already detect some of these signals individually (MacroAgent detects rate cuts, MarketAgent detects gold price action). Cluster intelligence would connect them explicitly.

For MVP purposes, cluster intelligence is **not authorized** for implementation. The concept informs how the existing agent outputs could eventually be combined into consequence-level reasoning.

---

## 8. Hypothesis Tracking

O.M.A.-C.O.R.E. should eventually track hypotheses explicitly. Each hypothesis is a structured record containing:

| Field | Description |
|-------|-------------|
| Triggering events | What events initiated this hypothesis |
| Supporting correlations | What relationships support it |
| Related cluster | Which cluster (if any) it belongs to |
| Expected consequence | The predicted future state |
| Confidence | Numerical assessment (0.0–1.0) |
| Evidence | Supporting data points |
| Invalidation conditions | What would disprove this hypothesis |
| Time horizon | Expected validation window |
| Linked opportunities | What actions were taken based on this |
| Linked actions | Specific trade/action records |
| Final outcome | What actually happened |
| Lessons learned | What the system should carry forward |

The system should learn less from *"trade won or lost"* and more from *"which part of the hypothesis was correct or wrong."*

Example:

- Trade lost → shallow learning ("bad signal")
- Trade lost because consequence was correct but timing was wrong → deeper learning ("improve time horizon calibration")
- Trade lost because consequence was wrong and invalidation conditions were not met → structural learning ("tighten invalidation logic")

**Hypothesis tracking is the bridge between raw outcomes and accumulated criterion.** Without it, every outcome is an isolated data point. With it, every outcome becomes a structured lesson.

For MVP purposes, explicit hypothesis tracking is **not authorized** for implementation. The concept should influence how PerformanceMemory evolves.

---

## 9. Failure Intelligence

Not all failures are equal. The system should classify failures by type to learn from each category differently:

| Failure Type | Description | What It Teaches |
|-------------|-------------|-----------------|
| Wrong event interpretation | The event was not what it seemed | Improve event classification |
| Wrong correlation | Two unrelated events were linked | Improve correlation quality filters |
| Wrong consequence | The consequence did not materialize | Improve consequence generation |
| Correct consequence, wrong timing | Right idea, too early or too late | Improve time horizon estimation |
| Correct consequence, poor execution | Right bet, wrong size or entry | Improve execution calibration |
| Correct hypothesis, external shock | Unpredictable black swan intervened | Accept — not a learning failure |
| Good opportunity, ignored | The system missed a valid opportunity | Improve opportunity capture rate |
| Bad opportunity, correctly rejected | The system avoided a bad bet | Reinforce — validate rejection logic |

For MVP purposes, Failure Intelligence is **not authorized** for implementation but should influence how FailureClassifier evolves.

---

## 10. Criterion Index Concept

The Criterion Index is a hypothetical multi-dimensional measure of the system's reasoning quality. It goes beyond win rate and Sharpe ratio.

**Possible dimensions:**

| Dimension | What It Measures |
|-----------|-----------------|
| Hypothesis calibration | How well confidence correlates with accuracy |
| Evidence quality | Whether the system acts on strong vs weak evidence |
| Context awareness | Whether the system considers the broader environment |
| Failure explanation quality | How well the system explains its own errors |
| Self-correction speed | How quickly the system adjusts after error |
| Knowledge stability | Whether lessons persist or are forgotten |
| Prediction consistency | Whether similar situations produce similar judgments |
| Long-term reliability | Whether performance degrades or improves over time |
| Opportunity capture rate | What fraction of valid opportunities are detected |
| False positive reduction | Whether spurious signals are filtered over time |
| False negative reduction | Whether genuine signals are missed over time |

The Criterion Index is **not for MVP implementation.** It is documented to influence how validation metrics evolve beyond raw PnL.

---

## 11. Opportunity Capture Rate

**Opportunity Capture Rate** = profitable/relevant opportunities detected by O.M.A.-C.O.R.E. ÷ profitable/relevant opportunities that existed in the observed market window.

**Fishing net metaphor:**

The information stream is the river. Most small fish (noise) should pass through the net. Medium and large fish (valid opportunities) are the target.

The goal is not fewer opportunities. The goal is **more valuable opportunities captured with less noise.**

A system with high precision but low capture rate is safe but useless. A system with high capture rate but low precision is noisy and expensive. The Criterion Index should balance both.

This metric is **not implementable in the current system** (it requires knowing what opportunities existed beyond those detected). It is documented as a strategic north star.

---

## 12. Product Implications

The same consequence intelligence powers all profiles:

| Profile | Consequence → Action |
|---------|---------------------|
| **Trader** | Consequence → trade setup → position → P&L |
| **Creator** | Consequence → early content idea → published piece → engagement |
| **Entrepreneur** | Consequence → operational/business insight → decision → market advantage |

In each case, the core mechanism is identical:
1. Detect early consequence before consensus
2. Form hypothesis with evidence and invalidation conditions
3. Take calibrated action
4. Measure outcome
5. Learn and accumulate criterion

The differences are in action primitives and feedback loops, not in the intelligence core. MetaCouncil already prototypes this three-profile evaluation.

---

## 13. What This Changes

O.M.A.-C.O.R.E.'s future architecture should be evaluated by one question:

> **Does this component help the system detect, explain, validate, or learn from consequences?**

If not, it may be unnecessary.

This does not mean the current system is wrong. The current system (WorldMonitorV2 → Agent Council → PaperTrading) is a correct and necessary first instantiation. It validates the event-to-action pipeline. It generates outcomes. It builds memory.

What this thesis changes is **how future components are prioritized and evaluated:**

- Not: "Does this improve signal quality?" → But: "Does this improve consequence detection?"
- Not: "Does this increase win rate?" → But: "Does this improve hypothesis calibration?"
- Not: "Does this add a feature?" → But: "Does this help the system learn from outcomes?"

---

## 14. Near-Term Guidance

**This document does NOT authorize immediate implementation** of:

- Consequence Engine
- Cluster Intelligence
- Hypothesis Engine
- Criterion Index
- Failure Intelligence module
- Opportunity Capture Rate tracking

Near-term priority remains:

1. **Continue validation** — Complete the 7-day smoke run and 30-day validation run
2. **Collect outcomes** — Every trade, every cycle, every guard block is learning material
3. **Prove learning** — Let PerformanceMemory accumulate track records and calibration data
4. **Preserve OMA-CORE-by-KIMI as laboratory** — This repository is the research platform where strategic discoveries like this thesis are developed and documented
5. **Avoid premature architecture changes** — The thesis influences evaluation, not implementation. Do not build new components until the current pipeline is fully validated and understood.

---

## 15. Final Principle

O.M.A.-C.O.R.E. should not become a system that merely reacts to information.

It should become a system that develops criterion by remembering what it believed, why it believed it, what it did, what happened, and what it learned.

The output of O.M.A.-C.O.R.E. is not a trade signal, a dashboard metric, or a chatbot response.

The output of O.M.A.-C.O.R.E. is **better criterion tomorrow than today.**

---

*This document is a strategic thesis. It does not override the current validation sprint. It does not authorize new components. It exists to guide architectural thinking and preserve the project's long-term direction.*
