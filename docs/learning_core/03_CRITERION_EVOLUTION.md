# Criterion Evolution

*Version 1.0 — June 2026*
*Learning Core Component — ARCHITECTURE V2 Layer 12*

---

## 1. Executive Summary

Criterion is the project's central concept. It is the accumulated ability to judge what matters — and it is explicitly defined as emergent (ARCHITECTURE V2 Invariant 1: "Criterion is never a component, engine, or module. It is not built.").

Because Criterion is emergent, it cannot be designed as a table, class, model, or agent. It cannot be implemented directly. It can only be measured, tracked, and influenced.

This document defines:

- **What can be measured** — the observable dimensions of Criterion
- **How Criterion changes** — the mechanism of Criterion deltas
- **When Criterion should NOT change** — protection against oscillation and noise
- **How to validate** that Criterion is improving over time
- **How Criterion evolution feeds into the Decision Approval Engine**

The goal is not to build Criterion. The goal is to build instruments that observe Criterion's development, detect direction changes, and provide evidence of learning.

---

## 2. Why Criterion Is Emergent

Criterion cannot be built because it is not a thing. It is a property — like health, wisdom, or fitness. You cannot build health. You can eat well, exercise, sleep, and measure biomarkers. The health emerges from the interaction of these practices.

Similarly, Criterion emerges from:
- Forming better hypotheses
- Collecting stronger evidence
- Making more informed decisions
- Comparing outcomes rigorously
- Extracting knowledge consistently
- Applying knowledge to future decisions

Criterion is the trend across these dimensions. No single component produces it. No schema stores it. No algorithm computes it.

What CAN be built:

| Can Be Built | Cannot Be Built |
|-------------|-----------------|
| Hypothesis quality metrics | Criterion itself |
| Evidence quality scores | A Criterion "engine" |
| Decision quality measures | A Criterion database |
| Calibration curves | A Criterion class |
| Knowledge yield tracking | A Criterion agent |
| Learning velocity trends | A Criterion AI model |

This distinction is not philosophical. It is architectural. Building the wrong thing wastes months and creates a component that claims to be Criterion but is not.

---

## 3. What Can Be Measured

Criterion is inferred from converging evidence across multiple independent dimensions. Each dimension is measurable. The convergence of trends across dimensions is the closest observable approximation to Criterion.

This is the same approach used in the CRITERION_VALIDATION_FRAMEWORK.md — converging evidence across five layers. No single metric is sufficient.

---

## 4. Criterion Dimensions

| # | Dimension | What It Measures | How It Improves | Leading/Lagging |
|---|-----------|-----------------|-----------------|-----------------|
| 1 | **Hypothesis Quality** | Are hypotheses becoming more specific, falsifiable, and predictive over time? | Better hypothesis formation → better tests → better learning | Leading |
| 2 | **Evidence Quality** | Is evidence more relevant, reliable, and independent over time? | Better evidence → better evaluations → better decisions | Leading |
| 3 | **Decision Quality** | Are decisions more justified by available evidence? | Better decisions → better outcomes → better learning | Lagging |
| 4 | **Calibration** | Is confidence converging with accuracy? | Better calibration → better risk assessment → better resource allocation | Lagging |
| 5 | **Error Recurrence** | Are the same errors repeating? | Reduced error recurrence → less waste → faster learning | Lagging |
| 6 | **Knowledge Yield** | Is more knowledge being extracted per decision/opportunity? | Higher knowledge yield → more learning per unit of experience | Leading |
| 7 | **Learning Velocity** | How fast does the system improve on repeated tasks? | Faster learning → faster adaptation → better performance | Leading |
| 8 | **Scarce Resource Conversion** | Is the system converting decisions into scarce resources more efficiently? | Better conversion → more resources for reinvestment → stronger Criterion | Lagging |

---

## 5. Hypothesis Quality

### What It Measures

Whether hypotheses are becoming more specific, falsifiable, and predictive over time. A hypothesis that is vague, unfalsifiable, or consistently wrong does not contribute to Criterion.

### Metrics

| Metric | Definition | Baseline | Target |
|--------|------------|----------|--------|
| **Hypothesis specificty score** | Average number of measurable fields populated per hypothesis | Current: all fields required | Maintain 100% |
| **Invalidation condition completeness** | % of hypotheses with valid invalidation conditions | Current: 100% (required by schema) | Maintain 100% |
| **Hypothesis confirmation rate** | % of evaluated hypotheses that were CONFIRMED | Unknown (no Outcome Bridge yet) | 40-60% (too high = too conservative, too low = too speculative) |
| **Hypothesis survival rate** | % of hypotheses that survive to EVALUATED without premature archival | Unknown | >70% |
| **Hypothesis time-to-evaluation** | Average time from FORMULATED to EVALUATED | Unknown | Match stated time horizon |

### Improvement Signal

Hypothesis quality improves when hypotheses become more specific, are confirmed at a reasonable rate, survive to evaluation, and produce learning regardless of confirmation.

---

## 6. Evidence Quality

### What It Measures

Whether evidence attached to hypotheses is relevant, reliable, independent, and weight-calibrated.

### Metrics

| Metric | Definition | Baseline | Target |
|--------|------------|----------|--------|
| **Evidence per hypothesis** | Average count of evidence items per hypothesis | Current: 0 (manual only) | >3 |
| **Evidence direction balance** | Ratio of supporting to contradicting evidence per hypothesis | Unknown | Neither direction should dominate without justification |
| **Source reliability spread** | Variance in source reliability scores across evidence | Unknown | Sources should differentiate (not all 1.0) |
| **Evidence relevance** | % of evidence items that correlate with eventual outcome | Unknown | >60% |
| **Evidence independence** | Average independence score across evidence per hypothesis | Unknown | >0.3 |

### Improvement Signal

Evidence quality improves when hypotheses carry multiple pieces of evidence from differentiated sources, with calibrated reliability and independence.

---

## 7. Decision Quality

### What It Measures

Whether decisions are justified by available evidence, consider alternatives, and record reasoning before the outcome is known.

### Metrics

| Metric | Definition | Baseline | Target |
|--------|------------|----------|--------|
| **Decision-hypothesis linkage** | % of decisions linked to a hypothesis | Current: 0% | >90% |
| **Alternative consideration** | % of decisions that record competing alternatives considered | Current: 0% | >50% |
| **Pre-decision reasoning record** | % of decisions with reasoning recorded before outcome known | Current: partial (agent opinions) | >95% |
| **Decision justification score** | Assessment of whether the evidence at decision time supported the decision | Unknown | Manual review on sample |

### Improvement Signal

Decision quality improves when more decisions are linked to hypotheses, record reasoning before outcomes, and consider alternatives.

---

## 8. Calibration

### What It Measures

Whether the system's confidence (in hypotheses, evidence, decisions) matches actual accuracy. A well-calibrated system knows what it knows and what it does not know.

### Metrics

| Metric | Definition | Baseline | Target |
|--------|------------|----------|--------|
| **Brier score** | Mean squared error between confidence and outcome | Unknown | <0.2 (perfect = 0) |
| **Calibration curve slope** | Linear regression of accuracy on confidence | Unknown | 1.0 (perfect calibration) |
| **Overconfidence rate** | % of decisions where confidence >70% but outcome was negative | Unknown | <15% |
| **Underconfidence rate** | % of decisions where confidence <30% but outcome was positive | Unknown | <15% |
| **Calibration by confidence bucket** | Brier score within each decile of confidence | Unknown | All deciles <0.3 |

### Improvement Signal

Calibration improves when the gap between confidence and accuracy narrows across all confidence levels.

---

## 9. Error Recurrence

### What It Measures

Whether the same types of errors repeat over time. Recurring errors indicate that the system is not learning from its mistakes.

### Error Types (from Outcome Bridge — `04_OUTCOME_BRIDGE.md`)

- WRONG_HYPOTHESIS — the belief was incorrect
- WRONG_TIMING — the belief was correct but the timing was wrong
- POOR_EXECUTION — the belief was correct but execution failed
- INSUFFICIENT_EVIDENCE — the decision was made with inadequate evidence
- EXTERNAL_SHOCK — an unpredictable event caused the outcome

### Metrics

| Metric | Definition | Baseline | Target |
|--------|------------|----------|--------|
| **Error type distribution** | % of each error type over time | Unknown | Even distribution (no single type dominates) |
| **Error recurrence rate** | % of same-type errors in consecutive periods | Unknown | Declining trend |
| **Time to error reduction** | How long before a dominant error type decreases | Unknown | Decreasing over time |
| **Error severity trend** | Average opportunity cost per error type over time | Unknown | Declining trend |

### Improvement Signal

Error recurrence improves when the same error types happen less frequently, and when no single error type dominates.

---

## 10. Knowledge Yield

### What It Measures

How much knowledge the system extracts per unit of experience (decisions, outcomes, missed opportunities).

### Metrics

| Metric | Definition | Baseline | Target |
|--------|------------|----------|--------|
| **Knowledge per outcome** | Average knowledge items extracted per evaluated outcome | Current: 0 (no Knowledge object) | >0.5 |
| **Knowledge per missed opportunity** | Average knowledge items extracted per evaluated missed opportunity | Current: 0 (no MO system) | >0.2 |
| **Knowledge validation rate** | % of EXTRACTED knowledge that reaches VALIDATED status | Current: N/A | >30% |
| **Knowledge application rate** | % of VALIDATED knowledge that informed a subsequent decision | Current: N/A | >20% |

### Improvement Signal

Knowledge yield improves when more knowledge is extracted per experience, and when a higher percentage of extracted knowledge proves valid and useful.

---

## 11. Learning Velocity

### What It Measures

How fast the system improves on repeated tasks. If the system encounters the same type of decision multiple times, does it make better decisions each time?

### Metrics

| Metric | Definition | Baseline | Target |
|--------|------------|----------|--------|
| **Within-class improvement** | Decision quality trend for repeated decision classes | Unknown | Positive slope |
| **Error reduction rate** | Rate at which error recurrence decreases | Unknown | Accelerating |
| **Time to competence** | Number of exposures before a decision class reaches 60% correctness | Unknown | Decreasing over time |
| **Cross-class transfer** | Does improvement in one decision class reduce time-to-competence in related classes? | Unknown | Positive correlation |

### Improvement Signal

Learning velocity improves when the system requires fewer repetitions to reach competence in new decision classes, and when learning transfers across related classes.

---

## 12. Scarce Resource Conversion

### What It Measures

How efficiently the system converts decisions into scarce resources (capital, time, attention, knowledge, etc.). This is the strategic output of Criterion (ARCHITECTURE V2 Invariant 8).

### Metrics

| Metric | Definition | Baseline | Target |
|--------|------------|----------|--------|
| **Capital conversion** | Net PnL per unit of risk taken | Current: Extended Demo data | Improving |
| **Time conversion** | Value generated per hour of system operation | Unknown | Improving |
| **Attention conversion** | Signal-to-noise ratio in notifications | Current: unknown | Improving |
| **Knowledge conversion** | VALIDATED knowledge items per week of operation | Current: N/A | >2 per week after Knowledge object exists |
| **Composite efficiency** | Weighted combination of all resource conversion metrics | Unknown | Improving |

### Improvement Signal

Scarce resource conversion improves when all tracked resources show positive trends. Improvement in one resource at the expense of another is NOT improvement — it is trade-off. True Criterion improvement benefits multiple resources simultaneously.

---

## 13. Criterion Delta Rules

A Criterion delta is a proposed change to evaluation criteria based on accumulated evidence. Deltas should be:

### When to Apply a Delta

| Condition | Delta Type | Approval |
|-----------|------------|----------|
| 5+ consecutive outcomes show the same error pattern | Reduce tolerance for that error type | Automated (low impact) |
| 10+ outcomes show a guard is systematically incorrect | Adjust guard threshold | Human review (medium impact) |
| 20+ outcomes show a hypothesis class is consistently mis-calibrated | Adjust confidence baseline for that class | Human review |
| 30+ outcomes show a new pattern that contradicts current knowledge | Create new knowledge, deprecate old | Automated recommendation, human approval |
| Regime change detected | Suspend all non-regime-specific deltas | Automated |

### When NOT to Apply a Delta

| Situation | Why Not | Alternative |
|-----------|---------|-------------|
| Single outlier outcome | Noise, not signal | Flag for monitoring |
| Regime transition (first 5 observations) | May be adapting to noise | Wait for 10+ observations in new regime |
| User override contradicts system finding | User may have information system lacks | Document override, track over time |
| Knowledge confidence < 0.5 | Insufficient evidence | Continue monitoring, re-evaluate when confidence >0.5 |
| Opposite delta applied within last 30 days | Oscillation risk | Investigate root cause of oscillation before applying new delta |

### Delta Record

Every Criterion delta, whether applied or rejected, is recorded:

```
{
  "id": "CD-2026-07-01",
  "proposed_by": "Criterion Evolution System",
  "source_evidence": {
    "knowledge_ids": ["K-042", "K-043", "K-044"],
    "hypothesis_ids": ["H-201", "H-202", "H-203", "H-204", "H-205"],
    "outcome_ids": ["O-101", "O-102", "O-103", "O-104", "O-105"]
  },
  "dimension": "error_recurrence",
  "change": "Lower tolerance for WRONG_TIMING errors from 30% to 20% repetition threshold",
  "confidence": 0.72,
  "status": "APPLIED" | "REJECTED" | "PENDING_REVIEW",
  "applied_at": "ISO8601",
  "outcome_tracking": { ... }  // Was this delta beneficial?
}
```

---

## 14. When Criterion Should NOT Change

Criterion stability is as important as Criterion improvement. A system that constantly changes its evaluation criteria cannot be evaluated itself.

### Stabilization Rules

1. **No delta within 30 days of a previous delta in the same dimension.** Prevents oscillation.
2. **No delta during a regime transition without 10+ observations in the new regime.** Prevents over-adaptation to noise.
3. **No delta based on single-outcome evidence.** Minimum evidence thresholds apply.
4. **No delta that contradicts an invariant.** Architecture Invariants (ARCHITECTURE_V2.md §13) are untouchable.
5. **No delta that would change the system's identity.** Trading is a validation domain, not the identity. A delta that optimizes for short-term profit at the expense of learning is rejected automatically.

---

## 15. Risks of False Criterion

| Risk | Description | Impact | Mitigation |
|------|-------------|--------|------------|
| **Measuring the wrong dimensions** | The system optimizes metrics that do not correspond to genuine Criterion. | Wasted effort, false confidence | Regularly re-evaluate dimension definitions. Cross-check with outcomes. |
| **Confusing activity with improvement** | More hypotheses, more evidence, more decisions are mistaken for better Criterion. | System becomes busy without improving | Require that dimension improvements correlate with outcome improvements. |
| **Goodhart's Law** | When a metric becomes a target, it ceases to be a good metric. | Metrics become gamed | Use converging evidence, not single metrics. Regularly rotate secondary metrics. |
| **Survivorship bias in knowledge** | Only successful outcomes produce knowledge; failures are forgotten. | Overconfidence in knowledge | Force extraction from failures. Track confirmation/contradiction ratio. |
| **Premature Criterion claims** | Claiming Criterion improvement before statistical significance is reached. | Loss of credibility | Enforce minimum evidence thresholds for all Criterion claims. |

---

## 16. Validation Over Time

Criterion development can only be validated over long time horizons. The CRITERION_VALIDATION_FRAMEWORK.md requires converging evidence across five layers. This document adds the time dimension:

| Time Horizon | What Can Be Validated | Confidence |
|-------------|-----------------------|------------|
| 1 month | Data collection works. Metrics can be computed. | Low — operational validation only |
| 3 months | Trends may be detectable in some dimensions. | Low-Medium — early signals |
| 6 months | Trends in 3+ dimensions should be visible. | Medium — some evidence |
| 12 months | Converging trends across 5+ dimensions should confirm or refute Criterion development. | Medium-High — substantial evidence |
| 24 months | Criterion development should be clearly demonstrable or clearly absent. | High — conclusive |
| 60 months | The system's decision quality should be materially better than at year 1. | Very High — project thesis validated or refuted |

The project does not claim Criterion development until at least 12 months of converging evidence exist.

---

## 17. Minimum Evidence Thresholds

| Claim | Minimum Evidence Required |
|-------|-------------------------|
| "Hypothesis quality is improving" | 50+ hypotheses across 3+ months, with consistent scoring |
| "Decision quality is improving" | 100+ decisions across 3+ months, with outcome comparison |
| "Calibration is improving" | 100+ decisions with confidence and outcome records |
| "Error recurrence is decreasing" | 50+ errors classified, 3+ months of trends |
| "Knowledge yield is improving" | 50+ knowledge items, 3+ months of trends |
| "Learning velocity is increasing" | 5+ repeated decision classes, each with 10+ exposures |
| "Scarce resource conversion is improving" | 6+ months of resource tracking data |
| **"Criterion is developing"** | **Converging positive trends across 5+ dimensions for 12+ months** |

---

## 18. Relationship to Decision Approval Engine

The Decision Approval Engine (ARCHITECTURE V2 Layer 8, MISSING) will determine which decisions are safe to auto-execute. Criterion Evolution provides the evidence basis for this determination.

### How Criterion Informs Approval

| Criterion Finding | Implication for Approval |
|-------------------|--------------------------|
| Calibration is improving across all confidence levels | Increase auto-approval threshold — the system's confidence is more trustworthy |
| Error recurrence is decreasing | Increase auto-approval scope — the system is learning from mistakes |
| Knowledge yield is low | Maintain or decrease auto-approval — the system may not be learning enough to justify autonomy |
| Scarce resource conversion is negative | Decrease auto-approval — the system is consuming resources without producing them |
| Hypothesis quality is declining | Decrease auto-approval — the system's foundational beliefs are getting worse |

### Approval Readiness Condition

The Decision Approval Engine should not approve any decision class for auto-execution until that decision class has:

1. At least 50 evaluated hypotheses in the class
2. At least 30 outcomes with completed comparisons
3. Confirmation rate between 30% and 70% (not too random, not too conservative)
4. Calibration Brier score < 0.3 for the class
5. Knowledge yield > 0.3 knowledge items per outcome
6. No single error type exceeding 40% of total errors in the class

These thresholds ensure that auto-approval only happens for decision classes where the system has demonstrated reliable judgment.

---
