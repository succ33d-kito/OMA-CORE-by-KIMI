# Outcome Bridge

*Version 1.0 — June 2026*
*Learning Core Component — ARCHITECTURE V2 Layer 10*

---

## 1. Executive Summary

The Outcome Bridge is the mechanism that connects actions and inactions to learning. It answers the single most important question in the entire architecture: *"Did the outcome confirm or contradict the hypothesis?"*

Without this bridge, the system has:
- Hypotheses that are never tested → no learning
- Decisions that are never compared to outcomes → no feedback
- Outcomes that are never linked to beliefs → no knowledge

The Outcome Bridge serves both the Execution branch (decisions that were acted on) and the Missed Opportunity branch (decisions that were blocked). It produces verdicts, error classifications, and the raw material for Knowledge extraction and Criterion evolution.

---

## 2. Why Outcomes Are Required for Learning

A hypothesis that is never tested produces no learning. A decision that is never evaluated produces no improvement. The Outcome Bridge closes the learning loop:

```
Hypothesis → Decision → Action/Inaction → Outcome → Comparison → Learning
                                                     ↑
                                              Outcome Bridge
```

Without outcome comparison, the system is a signal generator with memory but no feedback. It may execute thousands of decisions and never know whether it is improving. The Outcome Bridge is the mechanism that transforms experience into evidence.

---

## 3. Executed Decision Outcome

For decisions that were executed (trades opened, positions managed, closed):

### Input

| Data | Source | Description |
|------|--------|-------------|
| Hypothesis ID | Scientific Store | The hypothesis the decision was based on |
| Predicted consequence | Hypothesis.predicted_consequence | What was expected to happen |
| Invalidation conditions | Hypothesis.invalidation_conditions | What would prove the hypothesis wrong |
| Entry conditions | Trade record | When, where, and how the action was taken |
| Exit conditions | Trade record | When, where, and why the action was closed |
| Actual outcome | Trade record | PnL, duration, exit reason |
| Market context at exit | Market data | Conditions at the time of outcome |
| Scarce resources consumed | Future: Resource tracker | Capital, time, attention used |

### Output

| Data | Description |
|------|-------------|
| Verdict | CONFIRMED / REJECTED / INCONCLUSIVE |
| Error type | Classification of deviation (if hypothesis was rejected) |
| Outcome comparison detail | Quantitative comparison of predicted vs actual |
| Confidence in comparison | How reliable the comparison is |
| Knowledge trigger | Whether this outcome should trigger knowledge extraction |

### Comparison Method

```
1. Extract predicted_consequence from Hypothesis
2. Extract outcome from Trade (PnL, price movement, duration)
3. Compare predicted vs actual within tolerance:
   - If actual outcome matches predicted within tolerance → CONFIRMED
   - If actual outcome contradicts predicted beyond tolerance → REJECTED
   - If outcome is ambiguous or data is insufficient → INCONCLUSIVE
4. If REJECTED, classify error type
5. Record comparison with confidence score
```

### Tolerance Windows

| Prediction Type | Default Tolerance | Description |
|-----------------|-------------------|-------------|
| Directional (price up/down) | Direction matches | Binary — prediction was directionally correct or not |
| Magnitude (X% move) | ±30% of predicted | "Expected 5%, observed 3-6.5%" = confirmed |
| Timeframe (within N days) | ±50% of predicted | "Expected in 5 days, happened in 3-7" = confirmed. Beyond that = timing error |
| Conditional (if X then Y) | Condition must have occurred | If condition did not occur, verdict = INCONCLUSIVE |

---

## 4. Missed Opportunity Outcome

For decisions that were blocked (Missed Opportunity System — `docs/scientific/01_MISSED_OPPORTUNITY_SYSTEM.md`):

### Input

| Data | Source | Description |
|------|--------|-------------|
| MissedOpportunity ID | Missed Opportunity System | The record of the blocked opportunity |
| Predicted consequence | From the signal / decision | What was expected to happen |
| Observation window | MissedOpportunity lifecycle | Time range for observing the outcome |
| Market data during window | Market data feed | What actually happened |
| Opportunity cost estimate | Outcome Bridge computation | Estimated cost/benefit of missing |

### Output

| Data | Description |
|------|-------------|
| Verdict | CORRECT_BLOCK / INCORRECT_BLOCK / INCONCLUSIVE |
| Opportunity cost | Estimated financial and resource impact |
| Outcome detail | Actual price movement during the observation window |
| Confidence | How reliable the verdict is given counterfactual uncertainty |

### Comparison Method

The Missed Opportunity Outcome Bridge follows the same logic as the executed decision bridge, with one critical difference: the "execution" is simulated. The system estimates:

- What would the entry price have been? (based on the signal)
- What would the exit condition have been? (based on the strategy)
- What would the outcome have been? (based on actual market data)
- What would the capital requirement have been? (based on position sizing at the time)

These estimates are always qualified as counterfactual and carry lower confidence than executed decision outcomes.

---

## 5. Counterfactual Uncertainty

Counterfactual comparisons (for missed opportunities) carry inherent uncertainty:

| Source of Uncertainty | Impact | Mitigation |
|-----------------------|--------|------------|
| **Entry timing variance** | A few seconds can change entry price significantly | Use the signal timestamp price ± spread. |
| **Exit timing variance** | The automated exit may not match manual exit simulation | Use the strategy's standard exit rules (SL/TP/time). |
| **Slippage** | Actual execution may have worse fills | Apply the same slippage model as PaperTradingEngine. |
| **Path dependency** | How the position was managed affects the outcome | Simulate management per strategy rules. |
| **Market impact** | Our trade would have affected the market | Ignore for paper-trading level capital. Flag large positions. |

### Confidence Scoring

| Condition | Confidence |
|-----------|------------|
| Executed decision, clear outcome | 0.9+ |
| Executed decision, ambiguous outcome | 0.6–0.9 |
| Missed opportunity, liquid asset, short window | 0.5–0.7 |
| Missed opportunity, illiquid asset, long window | 0.3–0.5 |
| Missed opportunity, insufficient market data | <0.3 |

---

## 6. Verdict Taxonomy

| Verdict | Definition | Applies To | Example |
|---------|------------|------------|---------|
| **CONFIRMED** | Outcome matched predicted consequence within tolerance | Executed decisions | "Predicted BTC would rally 2-5%. Actual: +3.2%. Confirmed." |
| **REJECTED** | Outcome contradicted predicted consequence beyond tolerance | Executed decisions | "Predicted BTC would rally 2-5%. Actual: -1.8%. Rejected." |
| **INCORRECT_BLOCK** | The blocked opportunity would have succeeded | Missed opportunities | "Blocked BTC long. Price rose 4.2% within window. Block was incorrect." |
| **CORRECT_BLOCK** | The blocked opportunity would have failed | Missed opportunities | "Blocked BTC long. Price dropped 3.1% within window. Block was correct." |
| **INCONCLUSIVE** | Outcome is ambiguous, mixed, or insufficient | Both | "Predicted +2-5%. Actual: +5.8%. Directionally correct but exceeded range. Inconclusive — may indicate under-prediction bias." |
| **UNKNOWN** | Outcome cannot be determined | Both | "Data feed lost during observation window. Unknown." |

---

## 7. Error Taxonomy

When a hypothesis is REJECTED, the error must be classified:

| Error Type | Definition | Example | Frequency Target |
|------------|------------|---------|-----------------|
| **WRONG_HYPOTHESIS** | The causal belief was incorrect. The predicted consequence did not occur because the reasoning was wrong. | "Hypothesized that Fed pause would rally gold. Gold dropped despite pause. Relationship does not hold in current conditions." | Should decrease over time (learning) |
| **WRONG_TIMING** | The predicted consequence was directionally correct but occurred outside the expected timeframe. | "Predicted BTC rally within 5 days. Rally started on day 8. Timing was off." | Should decrease over time |
| **POOR_EXECUTION** | The hypothesis was correct but the execution failed — bad entry, bad exit, poor position management. | "Predicted gold rally correctly but stopped out by volatility spike that reversed immediately after." | Should decrease as execution improves |
| **INSUFFICIENT_EVIDENCE** | The decision was made with inadequate evidence. The hypothesis may have been correct or not — we cannot tell because the evidence was too weak. | "Confidence was 0.35, minimum should have been 0.5. Decision should not have been made." | Should decrease as evidence standards improve |
| **EXTERNAL_SHOCK** | An unpredictable event caused the outcome to deviate. The hypothesis may have been correct under normal conditions. | "Hypothesis about gold during inflation was correct, but unexpected regulatory intervention in commodities market caused temporary distortion." | Should remain stable (unpredictable by definition) |
| **CORRECT_DECISION_BAD_OUTCOME** | The decision was justified by available evidence but produced a negative outcome due to factors that could not have been anticipated. | "All evidence supported the decision. Outcome was negative due to bad luck (e.g., flash crash)." | Should be recognized, not classified as error |
| **BAD_DECISION_GOOD_OUTCOME** | The decision was not justified by available evidence but produced a positive outcome due to luck. | "Insufficient evidence, low confidence, but trade won. This is a lucky outcome, not a good decision." | Should be recognized, not classified as success |

---

## 8. Outcome Comparison Method

### Quantitative Comparison

For hypotheses with numeric predictions:

```
consequence_match = measured(predicted_consequence) 

if direction(consequence_match) == direction(predicted):
    magnitude_error = abs(consequence_match - predicted) / max(|predicted|, epsilon)
    if magnitude_error <= TOLERANCE_MAGNITUDE:
        verdict = CONFIRMED
    else:
        verdict = INCONCLUSIVE  # Directionally correct, magnitude off
else:
    verdict = REJECTED

timing_error = abs(actual_timing - predicted_timing) / predicted_timing
if timing_error > TOLERANCE_TIMING:
    error_type_addition = WRONG_TIMING
```

### Qualitative Comparison

For hypotheses that cannot be expressed numerically (e.g., business decisions, event outcomes):

```
Define outcome categories before decision:
  - "SUCCESS" = measurable consequence X occurred
  - "FAILURE" = measurable consequence Y occurred
  - "MIXED" = both or neither

After outcome:
  - Map observed outcome to predefined category
  - Assign verdict based on match
```

### Comparison Record

Every comparison produces a structured record:

```
{
  "hypothesis_id": "H-042",
  "decision_id": "D-013",
  "outcome_id": "O-007",
  "verdict": "CONFIRMED",
  "error_type": null,
  "predicted_consequence": "BTC increase 2-5% within 24 hours",
  "actual_outcome": "BTC increased 3.2% within 14 hours",
  "tolerance_applied": {"magnitude": 0.3, "timing": 0.5},
  "comparison_confidence": 0.92,
  "error_detail": null,
  "knowledge_triggered": true,
  "compared_at": "ISO8601"
}
```

---

## 9. Outcome Confidence

Each outcome comparison carries a confidence score reflecting how reliable the comparison is:

| Factor | Weight | Description |
|--------|--------|-------------|
| Data quality | 0.4 | Was the outcome data complete and timely? |
| Prediction specificity | 0.3 | Was the hypothesis specific enough for clear comparison? |
| Counterfactual confidence | 0.2 | Only applies to missed opportunities |
| Tolerance appropriateness | 0.1 | Were the tolerance windows appropriate for this context? |

Outcome confidence feeds into knowledge extraction — low-confidence outcomes contribute less to knowledge formation.

---

## 10. Relationship to Hypothesis

The Outcome Bridge consumes hypotheses (specifically their `predicted_consequence` and `invalidation_conditions`) and updates them with verdicts.

After the Outcome Bridge processes a hypothesis:

```
Hypothesis.status = EVALUATED
Hypothesis.status_history includes the outcome comparison
The verdict is recorded for Knowledge extraction
```

A hypothesis that has been compared to an outcome is no longer active. It enters EVALUATED status (per `core/schemas/hypothesis_schema.py` lifecycle: FORMULATED → ACTIVE → EVALUATED → ARCHIVED).

---

## 11. Relationship to Knowledge

The Outcome Bridge is the primary trigger for Knowledge extraction. When a comparison produces a verdict, the system checks whether the outcome should generate Knowledge:

| Condition | Knowledge Action |
|-----------|-----------------|
| First outcome of its type | Flag for potential extraction |
| Recurring pattern across 3+ outcomes of same type | Extract Knowledge (PROVISIONAL) |
| Outcome contradicts existing Knowledge | Flag for review, potentially invalidate Knowledge |
| Outcome confirms existing Knowledge | Strengthen Knowledge confidence and replication count |

The Knowledge extraction itself is handled by the Knowledge Object lifecycle (`02_KNOWLEDGE_OBJECT.md`). The Outcome Bridge provides the raw material.

---

## 12. Relationship to Criterion

Outcome comparisons feed directly into Criterion dimensions:

| Criterion Dimension | Data from Outcome Bridge |
|---------------------|--------------------------|
| Hypothesis Quality | Confirmation/rejection rate per hypothesis class |
| Decision Quality | How well did evidence at decision time predict the outcome? |
| Calibration | Confidence vs actual outcome |
| Error Recurrence | Error type frequency over time |
| Knowledge Yield | Number of outcomes that triggered knowledge extraction |

The Outcome Bridge does not compute Criterion. It produces the data that the Criterion Evolution layer (`03_CRITERION_EVOLUTION.md`) uses to compute Criterion dimensions.

---

## 13. Integration with PaperTrading

The Outcome Bridge reads from PaperTrading (trade records) but does not write to it. Integration points:

| PaperTrading Event | Outcome Bridge Action |
|--------------------|----------------------|
| Trade opened | Register trade ID for future outcome comparison. Link to hypothesis if available. |
| Trade closed (SL) | Compare outcome to predicted. Assign verdict. |
| Trade closed (TP) | Compare outcome to predicted. Assign verdict. |
| Trade closed (time) | Compare outcome to predicted. Assign verdict with timing consideration. |
| Trade closed (manual) | Compare outcome to predicted. Flag for manual error type classification. |

The Outcome Bridge does NOT modify PaperTrading, Trade records, or any execution component. It reads their outputs and produces separate comparison records.

---

## 14. Integration with Missed Opportunity System

The Outcome Bridge extends to the Missed Opportunity System:

| MissedOpportunity Phase | Outcome Bridge Action |
|------------------------|----------------------|
| OUTCOME_AVAILABLE | Receive market data for observation window. Compare predicted consequence to actual movement. |
| COMPARED | Assign verdict (CORRECT_BLOCK / INCORRECT_BLOCK). Compute opportunity cost. |
| KNOWLEDGE_GENERATED | Trigger knowledge extraction if patterns are detected. |

---

## 15. Safety Boundaries

| Boundary | Rule | Enforcement |
|----------|------|-------------|
| **No write to operational pipeline** | The Outcome Bridge never writes to agents, Council, execution, or guards. | Read-only from operational modules. Write-only to scientific store. |
| **No retroactive modification** | Once a comparison record is written, it is immutable. If the outcome is revised, a new comparison is created. | Append-only comparison records. |
| **No outcome without hypothesis** | The bridge does not compare outcomes that have no linked hypothesis. If a trade exists without a hypothesis link, it is recorded as operational data only. | Hypothesis ID required for scientific comparison. |
| **No confidence inflation** | Comparison confidence must reflect actual certainty. Never inflate confidence to make a Knowledge claim stronger. | Confidence scoring rules enforced at record creation. |

---

## 16. Failure Modes

| # | Failure Mode | Description | Mitigation |
|---|-------------|-------------|------------|
| 1 | **False confirmation** | Outcome matches prediction by coincidence, not causality. | Require replication across different conditions. |
| 2 | **False rejection** | Outcome contradicts prediction due to external shock, not wrong hypothesis. | Error type EXTERNAL_SHOCK captures this. Do not count as hypothesis failure. |
| 3 | **Timing errors misclassified** | A timing error is classified as a wrong hypothesis, or vice versa. | Clear definitions and examples for each error type. Manual review of ambiguous cases. |
| 4 | **Missed opportunity validation unreliable** | Counterfactual estimation is too noisy to produce useful verdicts. | Keep confidence low. Only use for trend analysis, not individual decisions. |
| 5 | **Outcome data unavailable** | Market data feed is down during the observation window. | Verdict = UNKNOWN. Do not fabricate or extrapolate. |

---

## 17. Implementation Stages

| Stage | Scope | Effort | Dependencies |
|-------|-------|--------|--------------|
| **V1 — Hypothesis-outcome comparison** | Compare a hypothesis's predicted_consequence with a manually provided outcome. Produce verdict. | 2 days | Hypothesis schema (exists) |
| **V2 — PaperTrading integration** | Read trade records automatically when a trade closes. Link to hypothesis (if hypothesis_id exists on trade). Produce outcome comparison. | 3 days | V1, Trade schema (exists), hypothesis_id on Trade (future) |
| **V3 — Missed Opportunity integration** | Extend comparison to the Outcome/Observation phase of the Missed Opportunity System. Handle counterfactual uncertainty. | 3 days | V1, Missed Opportunity System (exists as spec) |
| **V4 — Error classification** | Automatically classify error types based on comparison characteristics. | 2 days | V2, error taxonomy |
| **V5 — Knowledge trigger** | Connect Outcome Bridge to Knowledge extraction pipeline. | 1 day | V4, Knowledge Object (spec exists) |

---
