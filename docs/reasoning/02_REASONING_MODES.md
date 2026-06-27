# Reasoning Modes

*Version 1.0 — June 2026*
*Learning Core — Layer 5*

---

## Mode Summary

| # | Mode | Status | Purpose |
|---|------|--------|---------|
| 1 | Causal Reasoning | V1_REQUIRED | What chain of cause and effect does this event initiate? |
| 2 | Probabilistic / Statistical Reasoning | V1_REQUIRED | What do the numbers say? |
| 3 | Temporal Reasoning | V1_REQUIRED | How does timing and sequence affect the outcome? |
| 4 | Economic Reasoning | V1_REQUIRED | What do incentives and economic logic predict? |
| 5 | Risk Reasoning | V1_REQUIRED | What could go wrong? |
| 6 | Analogical Reasoning | V2_OPTIONAL | Have we seen something like this before? |
| 7 | Market Microstructure Reasoning | V2_OPTIONAL | How will market mechanics affect the outcome? |
| 8 | Contrarian Reasoning | V2_OPTIONAL | What if the consensus is wrong? |
| 9 | Counterfactual Reasoning | V2_OPTIONAL | What if conditions were different? |
| 10 | Resource Reasoning | V2_OPTIONAL | What resource constraints affect this situation? |
| 11 | Game Theory / Incentive Reasoning | FUTURE_RESEARCH | What are the strategic interactions? |
| 12 | Meta-Reasoning | FUTURE_RESEARCH | What reasoning mode should we use here? |

---

## Mode Definitions

---

### Mode 1: Causal Reasoning

**Status:** V1_REQUIRED

**Purpose:** Identify cause-and-effect relationships. Events do not happen in isolation — they are links in a causal chain. This mode traces those chains forward (consequences) and backward (root causes).

**What question it asks:** *"If this event happened, what else will happen as a result?"*

**Input:** Event data, market context, historical cause-effect patterns, agent opinions

**Output:** Causal chains: Event → Direct Effect → Second-Order Effect → Nth-Order Effect

**Example in trading:**
```
Event: "Fed raises rates by 25bp"
Causal chain:
  Direct: USD strengthens
  Second-order: USD-denominated commodities become more expensive
  Third-order: Commodity-producing equities decline
  Nth-order: Inflation expectations adjust → consumer spending shifts
```

**Example outside trading:**
```
Event: "Major client delays payment by 60 days"
Causal chain:
  Direct: Cash flow gap increases
  Second-order: Must delay supplier payment or draw on credit line
  Third-order: Supplier relationships strain, credit costs increase
```

**Failure mode:** Over-attribution — finding causal links where only correlation exists. Mitigated by requiring that each causal link has observable evidence.

**Validation method:** Compare predicted causal chains with actual sequences. Chains that consistently predict correctly are kept; chains that fail are revised or retired.

**How it improves Criterion:** Causal reasoning is the foundation of understanding why markets behave as they do. A system that understands causality makes better predictions about non-repeating events.

---

### Mode 2: Probabilistic / Statistical Reasoning

**Status:** V1_REQUIRED

**Purpose:** Apply quantitative analysis to events. What do the statistics say about the likelihood of various outcomes? This mode takes historical data, current conditions, and statistical patterns to produce probability estimates.

**What question it asks:** *"Given the data, what is the probability distribution of possible outcomes?"*

**Input:** Historical price data, volatility metrics, correlation matrices, regime classifications, event probabilities

**Output:** Probability distributions: P(outcome A | conditions), P(outcome B | conditions), confidence intervals

**Example in trading:**
```
Event: "BTC breaks above 20-day MA after 10 days below"
Statistical output:
  P(continuation above MA within 3 days): 0.65
  P(pullback below MA within 3 days): 0.25
  P(uncertain / range-bound): 0.10
  Confidence interval: ±0.08 (based on sample size of 47 similar events)
```

**Example outside trading:**
```
Event: "Content piece A received 2x normal engagement in first hour"
Statistical output:
  P(continued high engagement at 24h): 0.72 (based on 120 similar pieces)
  P(engagement decay): 0.82 average retention at 24h for this content type
```

**Failure mode:** Over-reliance on historical patterns that may not repeat. The future is not always statistically like the past. Mitigated by tracking regime changes and adjusting probability baselines.

**Validation method:** Calibration tracking — do events assigned 70% probability occur approximately 70% of the time? Brier score per mode.

**How it improves Criterion:** Statistical reasoning provides the calibration baseline. Without it, the system cannot know whether its confidence is justified.

---

### Mode 3: Temporal Reasoning

**Status:** V1_REQUIRED

**Purpose:** Analyze the timing, sequence, and duration of events. When something happens is as important as what happens. This mode considers lead/lag relationships, seasonality, event sequencing, time-to-impact estimation.

**What question it asks:** *"How does timing affect the likely outcome?"*

**Input:** Event timestamp, event sequence, historical lead/lag patterns, seasonal patterns, time-to-impact models

**Output:** Time-annotated scenarios: outcome X expected within N days, outcome Y expected within M days. Sequence dependencies: outcome A must happen before outcome B.

**Example in trading:**
```
Event: "FOMC minutes released"
Temporal output:
  Initial volatility: within 15 minutes
  Direction establishment: within 2 hours
  Full price discovery: within 24 hours
  Mean reversion probability: increases after 48 hours
```

**Example outside trading:**
```
Event: "Product launch announced"
Temporal output:
  Initial user spike: within 24 hours
  Retention signal: measurable at 7 days
  Market reaction: 2-4 weeks (analyst reports, competitor responses)
```

**Failure mode:** Timing over-specificity — predicting exact time windows that are too narrow, causing correct directional predictions to be classified as wrong due to timing error. Mitigated by the tolerance windows defined in the Outcome Bridge.

**Validation method:** Compare predicted time windows with actual timing. Track timing error distribution. Adjust window sizes based on empirical timing variance.

**How it improves Criterion:** Understanding timing separates signal from noise. A directionally correct prediction at the wrong time is operationally useless. Temporal reasoning improves the system's ability to act at the right time.

---

### Mode 4: Economic Reasoning

**Status:** V1_REQUIRED

**Purpose:** Apply economic principles — supply and demand, arbitrage, substitution effects, capital flows, opportunity cost. Economic reasoning grounds hypotheses in fundamental logic that should hold across different market conditions.

**What question it asks:** *"What does basic economic logic predict will happen?"*

**Input:** Event data, market structure information, economic indicators, supply/demand estimates, capital flow data

**Output:** Economically-grounded scenarios: prediction with economic rationale, expected adjustment path

**Example in trading:**
```
Event: "Oil production cut announced"
Economic output:
  Supply decreases → price should rise (all else equal)
  Magnitude depends on demand elasticity and spare capacity
  Substitution effect: if oil rises, alternative energy becomes more attractive
  Countervailing force: high prices may reduce demand over time
```

**Example outside trading:**
```
Decision: "Should we raise prices?"
Economic output:
  If demand is elastic: revenue may decrease
  If demand is inelastic: revenue will increase
  Competitive response: if we raise prices, competitors may hold or lower
  Net effect depends on brand strength and switching costs
```

**Failure mode:** Assuming markets are rational and efficient. In the short term, markets can defy economic logic due to sentiment, liquidity, or structural constraints. Mitigated by combining economic reasoning with market microstructure and sentiment analysis.

**Validation method:** Track economic predictions against outcomes. Economic reasoning should perform better over medium-to-long time horizons (days to weeks) than short horizons.

**How it improves Criterion:** Economic reasoning provides the "anchor" — the prediction that would be true in a rational world. Deviations from this anchor reveal market inefficiencies, sentiment effects, or structural changes.

---

### Mode 5: Risk Reasoning

**Status:** V1_REQUIRED

**Purpose:** Explicitly consider what could go wrong. Every hypothesis carries risk — this mode identifies, categorizes, and estimates the probability of adverse outcomes.

**What question it asks:** *"What are the ways this hypothesis could be wrong, and what would that cost?"*

**Input:** Risk guard outputs (CrashDetector, CapitalGuard, KnifeDetector, etc.), volatility metrics, tail risk indicators, correlation matrices, drawdown context

**Output:** Risk-annotated scenarios: probability of adverse outcome, estimated loss magnitude, scenario-specific risks, tail risks

**Example in trading:**
```
Hypothesis: "BTC long based on MA breakout"
Risk output:
  Primary risk: false breakout (30% probability, -2% to -5%)
  Tail risk: black swan event (2% probability, -15% to -30%)
  Execution risk: slippage during volatile conditions
  Regime risk: if this is a ranging market, breakouts fail more often
```

**Example outside trading:**
```
Decision: "Invest 20 hours in new content vertical"
Risk output:
  Primary risk: low engagement (40% probability, 20 hours + opportunity cost)
  Tail risk: reputational damage from poor-quality content
  Opportunity risk: cannot pursue other verticals during this time
```

**Failure mode:** Risk paralysis — identifying so many risks that no hypothesis seems worth testing. Mitigated by separating risks into "acceptable" (within normal bounds) and "unacceptable" (violates invariants or constraints).

**Validation method:** Track risk estimates against actual adverse outcomes. Are events assigned 30% risk occurring at approximately 30% rate? Calibrate risk estimates over time.

**How it improves Criterion:** Risk reasoning is the mechanism that prevents overconfidence. Every hypothesis must survive a risk challenge before it enters the store. This directly protects scarce resources.

---

### Mode 6: Analogical Reasoning

**Status:** V2_OPTIONAL

**Purpose:** Map current situations to similar past situations. Analogical reasoning identifies structural similarities between the current event and past events, then uses the past outcome to inform the current hypothesis.

**What question it asks:** *"Have we seen something like this before, and what happened then?"*

**Input:** Knowledge store, Scientific Store, historical event database, outcome records

**Output:** Analogous scenarios: "Situation A is structurally similar to current situation. Outcome of A was X. Proposed hypothesis accounts for similarities and differences."

**Failure mode:** Surface-level analogies that ignore structural differences. "BTC dropped 10% in June 2024 and bounced" does not mean "BTC dropped 10% now, so it will bounce" unless the structural conditions are similar.

**Validation method:** Track analogical predictions. If analogies consistently produce correct hypotheses, the analogical matching criteria are good. If not, refine the matching criteria.

---

### Mode 7: Market Microstructure Reasoning

**Status:** V2_OPTIONAL

**Purpose:** Analyze how market mechanics — order flow, liquidity, spreads, exchange dynamics — will affect outcomes. This mode is essential for understanding short-term price action but less relevant for longer horizons.

**What question it asks:** *"How will market structure affect the execution and outcome of this hypothesis?"*

**Input:** Order book data (future), liquidity metrics, spread data, exchange-specific dynamics, volume profile

**Output:** Microstructure predictions: expected slippage, liquidity risk, order flow imbalance, exchange-specific risks

**Failure mode:** Over-emphasizing microstructure noise that is irrelevant at the hypothesis time horizon. Mitigated by combining with temporal reasoning.

---

### Mode 8: Contrarian Reasoning

**Status:** V2_OPTIONAL

**Purpose:** Deliberately challenge consensus. If all agents and reasoning modes agree, contrarian reasoning asks: "What if the consensus is wrong?" This ensures the system does not fall into groupthink.

**What question it asks:** *"What would need to be true for the consensus to be wrong?"*

**Input:** Consensus output from other reasoning modes, Agent Council decision, market positioning data (future), sentiment indicators

**Output:** Contrarian counter-hypothesis: "The consensus predicts X. If the consensus is wrong, the outcome would be NOT X, because..."

**Failure mode:** Being contrarian for its own sake. Constant contrarianism is as bad as constant consensus. Mitigated by requiring evidence for the contrarian position, not mere disagreement.

---

### Mode 9: Counterfactual Reasoning

**Status:** V2_OPTIONAL

**Purpose:** Consider what would happen if key conditions were different. This mode supports robustness testing of hypotheses: "Is this hypothesis robust to changes in conditions?"

**What question it asks:** *"If condition X were different, would the hypothesis still hold?"*

**Input:** Current hypothesis from another mode, alternative condition scenarios

**Output:** Conditional robustness assessment: "Hypothesis holds under conditions A, B, C. Fails under condition D."

**Failure mode:** Counterfactual proliferation — too many "what if" scenarios without prioritization. Mitigated by limiting counterfactuals to plausible alternative conditions.

---

### Mode 10: Resource Reasoning

**Status:** V2_OPTIONAL

**Purpose:** Apply scarce resource constraints to hypothesis generation. Not every hypothesis is worth pursuing given limited capital, time, and attention. This mode estimates the resource cost of testing a hypothesis and filters out hypotheses whose expected value does not justify their resource consumption.

**What question it asks:** *"Is this hypothesis worth the resources required to test it?"*

**Input:** Scarce resource state (capital, time, attention budget), hypothesis expected value estimate, resource cost estimate

**Output:** Resource-feasibility assessment: "This hypothesis requires 2% capital and 30 minutes of attention. Expected value justifies cost." OR "This hypothesis requires more resources than it is likely to return."

**Failure mode:** Underestimating resource costs (especially attention and time) leading to resource depletion. Mitigated by tracking actual resource consumption vs estimates.

---

### Mode 11: Game Theory / Incentive Reasoning

**Status:** FUTURE_RESEARCH

**Purpose:** Model strategic interactions between market participants. Markets are games with players who have different incentives, information, and strategies. This mode models those interactions.

**What question it asks:** *"What are the strategic incentives of the participants, and what behavior do they predict?"*

**Input:** Market participant types, incentive structures, information asymmetry estimates, strategic behavior patterns

**Output:** Game-theoretic predictions: "Given incentives, participants are likely to behave in way X, leading to outcome Y."

**Failure mode:** Over-complex models that are not falsifiable. Game theory predictions are often qualitative and difficult to validate. Requires significant development and validation before it can be useful.

---

### Mode 12: Meta-Reasoning

**Status:** FUTURE_RESEARCH

**Purpose:** Decide which reasoning modes to apply to which situations. Meta-reasoning is the system's ability to allocate its cognitive resources — choosing the right thinking tool for the job.

**What question it asks:** *"Given this event type and context, which reasoning modes are likely to produce the most valuable hypotheses?"*

**Input:** Event type classification, current context, reasoning mode performance history, available cognitive budget (time/compute)

**Output:** Reasoning mode selection: "For this event type, prioritize Causal and Temporal reasoning. Defer Analogical and Contrarian."

**Failure mode:** Meta-reasoning overhead exceeds the value of better mode selection. The meta-layer must be lightweight.

---

## V1 Mode Priority

| Priority | Mode | Rationale |
|----------|------|-----------|
| 1 | **Causal Reasoning** | Core cognitive capability. Everything depends on understanding cause and effect. |
| 2 | **Probabilistic / Statistical Reasoning** | Provides the quantitative foundation for all hypothesis confidence. |
| 3 | **Temporal Reasoning** | Essential for time-bounded hypotheses. Without it, timing is ignored. |
| 4 | **Economic Reasoning** | Anchors hypotheses in fundamental logic. Prevents detachment from reality. |
| 5 | **Risk Reasoning** | Protects scarce resources. Every hypothesis must be risk-challenged. |

V1 implements these 5 modes. Modes 6-12 are V2_OPTIONAL or FUTURE_RESEARCH.

---

## Mode Output Format

Every reasoning mode produces outputs in a consistent format:

```json
{
  "mode": "causal",
  "event_id": "EVT-042",
  "scenarios": [
    {
      "id": "SCN-causal-001",
      "description": "Fed rate cut leads to USD weakness, which leads to commodity rally",
      "causal_chain": ["Fed cuts rates", "USD weakens", "USD-denominated commodities rise", "Commodity equities benefit"],
      "confidence": 0.65,
      "time_horizon": "5-20 trading days",
      "conditions": ["No other major central bank cuts simultaneously", "No geopolitical shock"],
      "invalidation": "USD strengthens despite rate cut",
      "evidence": ["Historical correlation: 0.72 between rate cuts and USD weakness in current cycle", "CFTC positioning data shows short USD sentiment"]
    }
  ],
  "mode_confidence": 0.70,
  "processing_time_ms": 145
}
```

This format feeds directly into the Reasoning Council and the Hypothesis formulation pipeline.

---
