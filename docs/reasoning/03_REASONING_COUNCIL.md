# Reasoning Council

*Version 1.0 — June 2026*
*Learning Core — Layer 5*
*Canonical Reference: docs/learning_core/01_REASONING_ENGINE.md*

---

## 1. Purpose

The Reasoning Council evaluates, combines, and prioritizes scenario candidates from multiple reasoning modes. It is the gate between raw reasoning output and testable hypotheses.

It answers:
- Which scenarios are worth testing as hypotheses?
- Which scenarios should be discarded?
- When do competing scenarios represent genuinely different hypotheses worth preserving?
- When should similar scenarios be merged?
- What priority should each hypothesis receive?

---

## 2. Reasoning Council vs Agent Council

| Aspect | Agent Council | Reasoning Council |
|--------|---------------|-------------------|
| **Input** | AgentOpinions (recommendation, confidence, evidence list) | Scenario candidates from reasoning modes |
| **Output** | CouncilDecision (action: buy/sell/hold, confidence, conviction) | Prioritized hypothesis candidates |
| **Goal** | Make the operational decision | Design the scientific experiment |
| **Disagreement handling** | Weighted vote → consensus decision | Preserve competing hypotheses |
| **Evaluation criteria** | Agent track record | Falsifiability, novelty, evidence strength |
| **Timing** | Real-time (before execution) | Post-event (can be async) |
| **Relationship to action** | Directly precedes action | Precedes learning |

The Agent Council answers: "What should we do right now?"

The Reasoning Council answers: "What should we believe, and how should we test it?"

---

## 3. Inputs

| Input | Source | Format | Description |
|-------|--------|--------|-------------|
| Scenario candidates | Reasoning modes (12 modes) | List of structured scenarios | Each mode produces 0-N scenarios per event |
| Mode metadata | Reasoning mode registry | Mode ID, confidence, performance stats | Which mode produced this scenario and how reliable it is |
| Event context | EventBus | EventData | The original event that triggered reasoning |
| Active hypotheses | Scientific Store | Hypothesis[] | Existing hypotheses to check for duplication |
| Knowledge context | Knowledge Store (future) | Knowledge[] | Relevant existing knowledge that may support or contradict scenarios |

---

## 4. Outputs

| Output | Destination | Format | Description |
|--------|-------------|--------|-------------|
| Prioritized hypothesis candidates | Hypothesis filter → Scientific Store | List of HypothesisCandidate | Scenarios that passed evaluation, formatted as hypothesis candidates |
| Discarded scenarios | Reasoning log | List of ScenarioRejection | Scenarios that failed evaluation with reasons |
| Disagreement record | Reasoning log | Structured JSON | Record of which modes agreed/disagreed and why |
| Reasoning performance data | Mode tracker | Metrics | How each mode performed in this cycle |

---

## 5. Evaluation Criteria

Each scenario candidate is scored on six dimensions:

| Criterion | Weight (V1) | Description | Scoring |
|-----------|-------------|-------------|---------|
| **Falsifiability** | 0.25 | Can this scenario be proven wrong? | 0 = no invalidation condition, 0.5 = vague condition, 1.0 = specific, measurable condition |
| **Evidence strength** | 0.20 | How much evidence supports this scenario? | 0 = no evidence, 0.5 = some evidence, 1.0 = strong converging evidence |
| **Novelty** | 0.15 | Is this substantially different from existing hypotheses? | 0 = duplicate, 0.5 = overlapping, 1.0 = novel |
| **Specificity** | 0.15 | How precise is the predicted consequence? | 0 = vague ("price will move"), 0.5 = directional ("price will rise"), 1.0 = specific ("price will rise 2-5% within 3 days") |
| **Resource feasibility** | 0.10 | Can we test this hypothesis with available resources? | 0 = cannot test, 0.5 = testable with effort, 1.0 = easily testable |
| **Mode confidence** | 0.15 | How confident is the source reasoning mode? | Based on mode's historical performance for this scenario type |

### Composite Score

```
score = Σ(weight_i * score_i) for all 6 criteria

threshold_v1 = 0.4  (configurable)
threshold_v2 = will be calibrated empirically
```

Scenarios with score < threshold are discarded. Scenarios with score ≥ threshold proceed to hypothesis formulation.

---

## 6. Conflict Handling

### When Reasoning Modes Disagree

Disagreement between reasoning modes is valuable, not problematic. It means multiple perspectives exist, and the system has a choice to make.

| Disagreement Type | Example | Action |
|-------------------|---------|--------|
| **Directional disagreement** | Causal: "BTC will rise." Risk: "BTC will fall." | Create competing hypotheses. Both can be tested. |
| **Magnitude disagreement** | Statistical: "BTC will rise 2%." Economic: "BTC will rise 8%." | Create a range hypothesis. Or create both as competing hypotheses. |
| **Timing disagreement** | Temporal: "within 24h." Economic: "within 5 days." | Adjust time horizon in hypothesis. Or create competing timing hypotheses. |
| **Conditional disagreement** | Causal: "If Fed cuts, gold rises." Contrarian: "If Fed cuts, gold drops because cuts are already priced." | Create both conditional hypotheses. The condition (Fed cut) is the same; the predicted consequence differs. |

### When to Create Competing Hypotheses

Create competing hypotheses when:
1. Two or more modes make genuinely different predictions about the same event
2. Both predictions are falsifiable
3. Both predictions have non-trivial evidence support
4. The system has resources to test both

Do NOT create competing hypotheses when:
1. One scenario clearly dominates on all evaluation criteria
2. The disagreement is semantic (same prediction, different wording)
3. Resources are insufficient to test multiple hypotheses

### When to Merge Hypotheses

Merge scenarios when:
1. They predict the same consequence with similar confidence
2. They differ only in reasoning mode (the same scenario from different perspectives)
3. Merging creates a stronger hypothesis (multiple reasoning modes supporting the same conclusion)

### When to Discard Reasoning Output

Discard when:
1. Score below threshold
2. Not falsifiable (no invalidation condition, no time horizon)
3. Duplicate of an active hypothesis (>80% similarity)
4. Cannot be tested with available resources
5. Violates an architecture invariant

---

## 7. Recording Dissent

Every disagreement between reasoning modes is recorded:

```
{
  "event_id": "EVT-042",
  "scenarios": {
    "SCN-causal-001": {"mode": "causal", "verdict": "bullish", "confidence": 0.7},
    "SCN-risk-003": {"mode": "risk", "verdict": "bearish", "confidence": 0.6}
  },
  "disagreement_type": "DIRECTIONAL",
  "resolution": "COMPETING_HYPOTHESES",
  "created_hypotheses": ["H-201", "H-202"],
  "resolved_at": "ISO8601"
}
```

Dissent records enable post-hoc analysis:
- Which modes disagree most often?
- When modes disagree, which mode is usually right?
- Does disagreement frequency correlate with specific event types?

---

## 8. Evaluating Reasoning Mode Performance

Each reasoning mode's performance is tracked across multiple dimensions:

| Metric | Definition | Update Frequency |
|--------|------------|-----------------|
| **Hypothesis confirmation rate** | % of hypotheses generated by this mode that are eventually CONFIRMED | After each outcome comparison |
| **False hypothesis rate** | % of hypotheses generated by this mode that are REJECTED | After each outcome comparison |
| **Discard rate** | % of scenarios from this mode that are discarded by the Council | Per event |
| **Average score** | Average Council evaluation score for scenarios from this mode | Per event |
| **Average confidence** | Average self-reported confidence from this mode | Per event |
| **Calibration** | Does mode confidence match actual confirmation rate? | Weekly |

Mode performance feeds into:
- Mode weighting in the Reasoning Council
- Mode prioritization (Meta-Reasoning, future)
- Mode retirement decisions (see 05_REASONING_VALIDATION.md)

---

## 9. Relationship to Knowledge Object

The Reasoning Council does not directly produce Knowledge. It produces hypotheses. Knowledge is extracted later by the Outcome Bridge and Knowledge lifecycle.

However, the Reasoning Council's records are valuable for knowledge extraction:
- Which reasoning modes produced the most valuable hypotheses?
- When modes disagree, which mode was right?
- What reasoning patterns correlate with confirmed hypotheses?

These meta-knowledge items belong in the Knowledge store.

---

## 10. Relationship to Criterion Evolution

The Reasoning Council directly contributes to several Criterion dimensions:

| Criterion Dimension | Contribution |
|---------------------|--------------|
| Hypothesis Quality | Council evaluation scores track hypothesis quality before testing |
| Decision Quality | Reasoning mode performance data helps evaluate which thinking patterns produce good decisions |
| Calibration | Mode confidence vs actual confirmation rate |
| Learning Velocity | How quickly does the Council learn to prioritize the right modes? |

---

## 11. Implementation Boundaries

| Boundary | Rule |
|----------|------|
| **No operational decision override** | The Reasoning Council never modifies or overrides the Agent Council's decision |
| **No execution** | The Reasoning Council never triggers or modifies execution |
| **No mandatory output** | If no scenario passes the threshold, no hypothesis is created. This is valid. |
| **Asynchronous** | The Reasoning Council operates after the operational decision, not before |
| **Mode-independent** | If a reasoning mode fails, the Council continues with available modes |

---
