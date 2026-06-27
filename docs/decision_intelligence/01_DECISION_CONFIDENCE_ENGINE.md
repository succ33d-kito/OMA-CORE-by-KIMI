# Decision Confidence Engine

## O.M.A.-C.O.R.E. Decision Intelligence — Component 1

*Version 1.0 — June 2026*

---

## 1. Purpose

The Decision Confidence Engine transforms all scientific outputs of the Learning Core into a structured, multi-dimensional confidence estimate. It does **not** approve, reject, or escalate. It estimates readiness. The Approval Engine (Document 2) consumes these estimates.

The central question the Confidence Engine answers:

> Given everything the system knows, how confident should it be that acting on this hypothesis will produce a net positive scarce-resource outcome?

---

## 2. Architectural Position

```
Learning Core → Scientific Lab → Historical Replay
                                      ↓
                          Decision Confidence Engine
                                      ↓
                             Approval Engine
                                      ↓
                     Execute / Wait / Reject / Need Evidence
```

The Confidence Engine sits between the Scientific Learning Laboratory and the Approval Engine. It is the first component in the Decision Intelligence Layer. It has no connection to collectors, execution, paper trading, agents, council, or runtime.

---

## 3. Confidence Is Not Probability

| Property | Probability | Confidence |
|---|---|---|
| Definition | Measure of likelihood of an event | Measure of readiness to act on a belief |
| Range | 0.0–1.0, sums to 1 across outcomes | Multi-dimensional, does not sum to 1 |
| Calibration | Requires known outcome distribution | Requires self-consistency over time |
| Updates | Bayes' rule (evidence weights) | Policy-governed re-evaluation |
| Interpretation | "How likely is X to happen?" | "How prepared are we to act on X?" |

Probability is about the world. Confidence is about the system's relationship to the world. A system can accurately estimate a 40% probability of success and still be unprepared to act — because it lacks knowledge, resources, or criterion maturity. Probability feeds confidence, but confidence also incorporates readiness, risk tolerance, and resource state.

---

## 4. Confidence Is Not Conviction

| Property | Conviction | Confidence |
|---|---|---|
| Source | Council consensus strength | Multi-dimensional engine score |
| Scope | Single decision opportunity | System-wide readiness state |
| Direction | Market direction belief | Action readiness belief |
| Persistence | Per-cycle | Accumulates across cycles |
| Used by | Trade signal generation | Approval Engine |

Conviction is an operational signal: *"how strongly do agents agree this trade will win?"* Confidence is an intelligence signal: *"how ready is the system to commit resources to this action?"* A high-conviction trade with low system confidence should wait. A low-conviction trade with high system confidence can proceed — but only within tight resource bounds.

---

## 5. Why Confidence Evolves

Confidence is not static because every input dimension changes:

- **Knowledge decays** without replication (see `knowledge_lifecycle.py` decay function)
- **Criteria mature** as deltas are proposed, reviewed, and applied
- **Historical calibration** shifts as new replay sessions complete
- **Resource states** change as capital, attention, and bandwidth are consumed
- **Uncertainty quanta** expand when new evidence contradicts existing knowledge

The Confidence Engine always produces a **current-state snapshot**. It does not cache or assume stability.

---

## 6. Input Dimensions

Each dimension produces a normalized sub-score `[0.0, 1.0]`. The engine does not weight them statically — weighting is a policy parameter (see Decision Policy, Document 4) that itself evolves as criterion matures.

### 6.1 Reasoning Quality (`D_RQ`)

Quality of the reasoning chain that produced the hypothesis under consideration.

| Sub-component | Source | Measure |
|---|---|---|
| Logical coherence | Hypothesis.structure | Completeness of premise→inference→prediction chain |
| Assumption explicitness | Hypothesis.assumptions | Ratio of stated vs. implicit assumptions |
| Fallacy detection | Reasoning Engine | Count of identified reasoning errors |
| Counterfactual coverage | Hypothesis.conditions | Scenarios explicitly ruled in/out |

### 6.2 Hypothesis Quality (`D_HQ`)

Quality of the specific hypothesis being evaluated for action.

| Sub-component | Source | Measure |
|---|---|---|
| Formulation precision | Hypothesis.statement | Falsifiability score (binary: can it be proven wrong?) |
| Temporal specificity | Hypothesis.time_horizon | Existence and precision of time bounds |
| Scope clarity | Hypothesis.conditions | Clear boundary between inside/outside scope |
| Source traceability | Hypothesis.provenance | Distance from raw event to formulated hypothesis |

### 6.3 Evidence Quality (`D_EQ`)

Quality of evidence accumulated for and against the hypothesis.

| Sub-component | Source | Measure |
|---|---|---|
| Volume | Evidence count | Absolute count of evidence records |
| Consistency | Evidence.scores | Variance across supporting evidence |
| Recency | Evidence.timestamp | Time since most recent evidence |
| Independence | Evidence provenance overlap | Evidence from distinct observation channels |
| Contradiction | Evidence against hypothesis count | Ratio of contradictory to supporting evidence |

### 6.4 Knowledge Quality (`D_KQ`)

Quality of knowledge items relevant to the hypothesis domain.

| Sub-component | Source | Measure |
|---|---|---|
| Status progression | Knowledge.status | Position in lifecycle (archived > validated > provisional) |
| Confidence level | Knowledge.confidence | Current decay-adjusted value |
| Replication count | Knowledge.replication_count | Number of independent validations |
| Provenance depth | Knowledge.provenance | Generations from raw observation |
| Domain coverage | Knowledge.tags | Overlap with hypothesis domain descriptors |

### 6.5 Criterion Maturity (`D_CM`)

Maturity of the criterion instruments that govern this decision class.

| Sub-component | Source | Measure |
|---|---|---|
| Delta volume | CriterionDelta count | Total proposed deltas in this dimension |
| Review completion | Applied + rejected / total deltas | Ratio of resolved deltas |
| Stability period | Time since last applied delta | Days without criterion change |
| Dimension coverage | CriterionDelta.dimension | Distinct dimensions with mature deltas |
| Error memory | ErrorType distribution | Known error patterns documented |

### 6.6 Historical Calibration (`D_HC`)

How well the system's past confidence estimates correlated with outcomes.

| Sub-component | Source | Measure |
|---|---|---|
| Calibration error | Historical replay sessions | Brier score of past confidence vs. outcome |
| Overconfidence bias | Replay sessions | Mean(confidence - accuracy) |
| Underconfidence bias | Replay sessions | Mean(accuracy - confidence) |
| Decision resolution | Replay sessions | Ability to distinguish good/bad opportunities |
| Stability | Calibration trend | Variance of calibration error across sessions |

### 6.7 Mode Performance (`D_MP`)

Current operational mode and its historical reliability.

| Sub-component | Source | Measure |
|---|---|---|
| Market regime | Crash Detector / Volatility | Current volatility regime classification |
| Mode history | Operational logs | Performance of past decisions in this regime |
| Regime change velocity | Velocity indicators | Speed of transition between regimes |

### 6.8 Risk (`D_R`)

Explicit risk estimation for this decision.

| Sub-component | Source | Measure |
|---|---|---|
| Position risk | Position size / capital | Fraction of available capital at stake |
| Tail risk | Historical distribution | Probability of >2σ adverse move |
| Liquidity risk | Order book / slippage | Estimated execution impact |
| Correlation risk | Open positions | Overlap with existing exposure |
| Systemic risk | Market-wide indicators | Regime-level risk overlay |

### 6.9 Uncertainty (`D_U`)

Known unknowns about this decision.

| Sub-component | Source | Measure |
|---|---|---|
| Evidence gap | Missing evidence dimensions | Ratio of unobserved to required evidence |
| Temporal uncertainty | Time to outcome | Longer horizons increase uncertainty |
| Model uncertainty | Hypothesis complexity | Number of unvalidated assumptions |
| Outcome dispersion | Expected distribution width | Variance of possible PnL outcomes |

### 6.10 Missing Information (`D_MI`)

Explicit absence of required data.

| Sub-component | Source | Measure |
|---|---|---|
| Schema completeness | Required vs. available fields | Ratio of populated required fields |
| Source freshness | Most recent data timestamp | Age of most recent observation |
| Channel diversity | Number of active data sources | Count of distinct information channels |
| Historical depth | Available history window | Days of continuous data available |

### 6.11 Opportunity Cost (`D_OC`)

What the system foregoes by acting on this hypothesis vs. alternatives.

| Sub-component | Source | Measure |
|---|---|---|
| Capital allocation | Current capital deployment | Fraction of capital committed |
| Attention budget | Concurrent hypotheses count | Open hypotheses vs. maximum |
| Temporal exclusivity | Time-sensitive alternatives | Count of competing time-windowed opportunities |

### 6.12 Resource Availability (`D_RA`)

Current state of system resources required for execution.

| Sub-component | Source | Measure |
|---|---|---|
| Capital available | Free capital / total capital | Ratio of uncommitted capital |
| Execution bandwidth | Current orders / max orders | Remaining order capacity |
| Compute headroom | CPU/Memory utilization | Available processing capacity |
| Human supervision | Current supervision mode | Autonomous / monitored / supervised |

---

## 7. Output Structure

The engine produces a **Confidence Vector**, not a single number:

```
C = {
  "overall":     f(D_RQ, D_HQ, D_EQ, D_KQ, D_CM, D_HC, D_MP, D_R, D_U, D_MI, D_OC, D_RA),
  "readiness":   g(D_RA, D_R, D_MP),              # Can we execute?
  "knowledge":   h(D_KQ, D_EQ, D_HC),             # Do we understand?
  "maturity":    i(D_CM, D_HQ, D_U),              # Is criterion ready?
  "stability":   j(D_HC, D_MP, D_MI),             # Is the environment stable?
  "efficiency":  k(D_OC, D_RA, D_R),              # Is this the best use?
  "uncertainty": l(D_U, D_MI, missing_info_count)  # What don't we know?
}
```

Where `f`, `g`, `h`, `i`, `j`, `k`, `l` are policy-governed aggregation functions (see Decision Policy, Document 4). Each sub-vector is also `[0.0, 1.0]` but carries semantic meaning beyond magnitude.

The critical architectural invariant: **the Confidence Engine never emits a single threshold-passing number**. It emits a vector. The Approval Engine interprets the vector.

---

## 8. Failure Modes

| Failure Mode | Description | Mitigation |
|---|---|---|
| Overconfidence | Engine reports high confidence despite poor calibration | Historical calibration dimension penalizes systematic overconfidence |
| Input hysteresis | Lagging input dimensions delay confidence updates | Freshness checks on every input source |
| Dimension collapse | Implicit weighting reduces 12 dimensions to 1-2 dominant ones | Policy must ensure dimension diversity; monitor entropy of weight distribution |
| Self-reinforcement | High confidence leads to action that biases future confidence | Confidence must not feed back into itself — separate estimation from action |
| Calibration brittleness | Small dataset produces misleading calibration scores | Minimum replay threshold before calibration is trusted |
| Resource blindness | Ignoring resource depletion in confidence estimate | Resource availability is a mandatory (non-optional) input dimension |

---

## 9. Calibration Protocol

Calibration is measured via replay sessions (Document 5, Stage 9 — Historical Learning Replay). For each past decision that has an observed outcome:

1. Run the Confidence Engine as-if at decision time (using only pre-decision data)
2. Record the confidence vector
3. Record the observed outcome
4. Compute Brier score and calibration curve per dimension

Calibration is only considered valid after:
- Minimum 30 replayed decisions per decision class
- Minimum 3 replay sessions at different time windows
- Calibration error < 0.15 (Brier score)

---

## 10. Interaction with Learning Core

The Confidence Engine consumes from the Learning Core but does not write to it:

| Learning Core Output | Confidence Input |
|---|---|
| OutcomeComparison (verdict, error_type) | D_HC (historical calibration) |
| Knowledge (status, confidence, replication_count) | D_KQ (knowledge quality) |
| CriterionDelta (status, dimension) | D_CM (criterion maturity) |
| Hypothesis (statement, conditions, time_horizon) | D_HQ, D_RQ |
| Evidence (score, timestamp) | D_EQ |

The engine is a pure function of Learning Core state. If the Learning Core is empty, the Confidence Engine returns minimum confidence — which is the correct behavior for an untrained system.

---

## 11. Open Design Questions

1. Should each decision class have its own confidence calibration model, or is a global model sufficient? **Current position**: Per-class, because different decision types (entry, exit, sizing, skip) have fundamentally different risk/reward profiles.

2. Should confidence be time-decayed like knowledge? **Current position**: No — confidence is always a current-state estimate. The decay is embedded in the knowledge quality dimension.

3. Should the engine expose intermediate computation for human inspection? **Current position**: Yes — all sub-dimension scores must be logged and accessible via the lab interface. A single opaque number defeats the purpose of multi-dimensional confidence.

4. How should the engine behave when multiple conflicting hypotheses compete for the same resource? **Current position**: Each hypothesis receives an independent confidence vector. Comparison is the Approval Engine's responsibility.
