# Reasoning to Hypothesis

*Version 1.0 — June 2026*
*Learning Core — Layer 5→6 Bridge*

---

## 1. Purpose

This document defines the exact transformation from a reasoning output to a formal Hypothesis object. A reasoning output is not a hypothesis. It becomes one only after passing strict gates — falsifiability, specificity, timing, resource feasibility, novelty, and duplication.

This gate is the most important quality control in the entire hypothesis pipeline. It prevents vague beliefs, untestable claims, and resource-wasting distractions from entering the Scientific Store.

---

## 2. Data Flow

```
Event
  │
  ▼
Reasoning Mode Output (scenario candidate — unstructured, qualitative)
  │
  ▼
Scenario Candidate (structured, with fields)
  │
  ▼
Reasoning Council Evaluation (scored against 6 criteria)
  │
  ▼
Hypothesis Candidate (passes Council threshold, fields mapped to Hypothesis schema)
  │
  ▼
Falsifiability Gate (hard pass/fail)  ← YOU SHALL NOT PASS
  │
  ▼
Duplicate Detection (merge or discard)
  │
  ▼
Novelty Score (flag if low)
  │
  ▼
Resource Feasibility Check (advisory)
  │
  ▼
Priority Assignment
  │
  ▼
Hypothesis Created in Scientific Store
```

---

## 3. Scenario Candidate Format

Produced by reasoning modes, consumed by the Reasoning Council:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String | Yes | Unique ID within the reasoning mode |
| `mode` | String | Yes | Source reasoning mode (e.g., "causal", "temporal") |
| `event_id` | String | Yes | Originating event ID |
| `description` | String | Yes | Natural language description of the scenario |
| `predicted_consequence` | String | Yes | What outcome is expected to occur |
| `confidence` | Float [0-1] | Yes | Mode's confidence in this scenario |
| `time_horizon` | String | Yes | Expected time window for the consequence |
| `conditions` | String[] | Yes | Conditions under which this scenario applies |
| `invalidation_conditions` | String[] | Yes | What would prove this scenario wrong |
| `evidence_summary` | String | Yes | Brief summary of evidence supporting this scenario |
| `resources_required` | JSON | No | Estimated capital, time, attention needed to test |

---

## 4. Hypothesis Candidate Format

After the Reasoning Council evaluates a scenario and it passes the threshold, it becomes a HypothesisCandidate:

| Field | Source | Mapping to Hypothesis Schema |
|-------|--------|------------------------------|
| `title` | Derived from description | `Hypothesis.title` |
| `description` | `scenario.description` | `Hypothesis.description` |
| `predicted_consequence` | `scenario.predicted_consequence` | `Hypothesis.predicted_consequence` |
| `conditions` | `scenario.conditions` (joined) | `Hypothesis.conditions` |
| `invalidation_conditions` | `scenario.invalidation_conditions` (joined) | `Hypothesis.invalidation_conditions` |
| `confidence` | `scenario.confidence` × `Council score factor` | `Hypothesis.confidence` |
| `source_mode` | `scenario.mode` | Not in schema — added to metadata/tagging |
| `event_id` | `scenario.event_id` | Not in schema — future field |
| `time_horizon` | `scenario.time_horizon` | Not in schema — embedded in predicted_consequence or conditions |
| `priority` | Computed from Council score | Used for creation ordering, not stored in schema |

---

## 5. Falsifiability Gate

This is a hard gate. A hypothesis candidate that fails ANY of these checks is rejected immediately. No exceptions.

| Requirement | Check | Pass Condition | Fail Condition |
|-------------|-------|----------------|----------------|
| **Specific predicted consequence** | Must describe a measurable outcome | "BTC will increase 2-5% within 24 hours" | "BTC will move" or "Something will happen" |
| **Invalidation condition** | Must specify what would prove the hypothesis wrong | "BTC drops more than 1% within 6 hours" | "If something changes" or left blank |
| **Time horizon** | Must specify when the consequence is expected | "Within 5 trading days" | "Eventually" or left blank |
| **Measurement criteria** | Must specify how to measure success/failure | "Price increase of 2-5% from entry" | "Price goes up" or "It feels right" |

### Gate Logic

```
def passes_falsifiability_gate(candidate: HypothesisCandidate) -> bool:
    checks = [
        has_specific_predicted_consequence(candidate),
        has_invalidation_condition(candidate),
        has_time_horizon(candidate),
        has_measurement_criteria(candidate)
    ]
    return all(checks)
```

If `passes_falsifiability_gate()` returns False, the candidate is rejected with a log entry explaining which check(s) failed.

---

## 6. Duplicate Detection

Before a hypothesis is created, it is checked against all active hypotheses in the Scientific Store:

| Similarity Level | Threshold | Action |
|-----------------|-----------|--------|
| **Exact duplicate** | >95% match on title + predicted_consequence + asset | Discard candidate. Log: "Duplicate of H-XXX." |
| **Near duplicate** | >80% match | Flag for potential merge. If candidate has stronger evidence, update existing hypothesis instead of creating new one. |
| **Overlapping** | >50% match on asset/direction but different consequence | Create as separate hypothesis. Overlap is noted in metadata. |
| **Novel** | <50% match | Create as new hypothesis. |

### Comparison Dimensions

| Dimension | Comparison Method |
|-----------|-------------------|
| Asset/symbol | Direct match or alias resolution |
| Direction | Bullish/bearish/neutral match |
| Predicted consequence | Embedding similarity or keyword overlap |
| Conditions | Condition set overlap |
| Time horizon | Duration proximity |
| Evidence sources | Evidence source overlap |

---

## 7. Novelty Score

After passing the duplicate check, each candidate receives a novelty score:

| Score | Meaning | Action |
|-------|---------|--------|
| 0.0 – 0.3 | Low novelty — very similar to existing hypotheses | Flag for review. May still be created if evidence is strong. |
| 0.3 – 0.7 | Moderate novelty — some overlap but distinct | Create as new hypothesis. Note relationship to existing hypotheses. |
| 0.7 – 1.0 | High novelty — no closely related hypothesis exists | Create as new hypothesis. High priority for knowledge extraction. |

---

## 8. Priority Score

Each hypothesis candidate receives a priority score used to determine creation order:

```
priority = (Council_evaluation_score × 0.4) 
         + (novelty_score × 0.2) 
         + (urgency × 0.2) 
         + (user_interest × 0.2)
```

| Component | Definition |
|-----------|------------|
| Council evaluation score | From the 6-criteria evaluation (03_REASONING_COUNCIL.md §5) |
| Novelty score | From §7 above |
| Urgency | Based on event urgency and time horizon — more urgent = higher priority |
| User interest | Based on user's expressed interests — which assets, domains, or hypothesis types the user prioritizes |

---

## 9. Resource Feasibility Check

Advisory (not a hard gate at V1). Checks:

| Resource | Check | Action If Insufficient |
|----------|-------|------------------------|
| **Attention budget** | Does the user have attention to review this hypothesis? | Flag as "low attention priority." Create but suppress notification. |
| **Capital availability** | Can this hypothesis be tested with available capital? | Flag as "capital constrained." Create but note that testing depends on capital availability. |
| **Time to evaluate** | Does the hypothesis time horizon fit within current evaluation capacity? | Flag as "long horizon." Create but schedule evaluation reminder. |

---

## 10. Rejection Reasons

When a hypothesis candidate is rejected at any gate, the rejection is recorded:

| Gate | Rejection Reason | Example |
|------|------------------|---------|
| Council evaluation | Below minimum score threshold | "Score 0.31 < threshold 0.40. Evidence too weak." |
| Falsifiability | Missing invalidation condition | "No invalidation condition specified. Cannot test." |
| Falsifiability | No specific consequence | "Predicted consequence 'price will move' is not measurable." |
| Falsifiability | No time horizon | "No time horizon specified. Cannot evaluate." |
| Duplicate detection | Exact duplicate | "Duplicate of H-042 (99% match). Discarded." |
| Resource feasibility | Attention budget exceeded | "Attention budget exhausted for this period. Candidate archived for next cycle." |

---

## 11. Examples

### Example 1: Event → Reasoning Outputs → Hypothesis

```
Event: "Fed rate cut 25bp"
  │
  ▼
Causal Reasoning: "Rate cut → USD weakens → commodities rise → gold +3-5% in 5-10 days"
  │
  ▼
Scenario Candidate: {
  predicted_consequence: "Gold price increases 3-5% within 5-10 trading days",
  invalidation_conditions: ["USD strengthens despite cut", "Gold drops >1% within 48h"],
  conditions: ["No simultaneous ECB cut", "Market not already pricing 100% probability"]
}
  │
  ▼
Council Score: 0.72 → PASSES
Falsifiability Gate: ALL CHECKS PASS
Duplicate Check: Novel (no active hypothesis on gold + Fed)
Priority: 0.68
  │
  ▼
Hypothesis Created:
  Title: "Gold rally on Fed rate cut"
  Description: "Fed 25bp rate cut will weaken USD and drive gold up 3-5%"
  Predicted consequence: "Gold price increases 3-5% within 5-10 trading days"
  Conditions: "No simultaneous ECB cut. Market not already pricing 100%."
  Invalidation: "USD strengthens despite cut. Gold drops >1% within 48h."
  Confidence: 0.65
  Status: FORMULATED
```

### Example 2: Event → Multiple Competing Hypotheses

```
Event: "BTC breaks below $60,000 support"
  │
  ├── Statistical: "70% probability of continued decline to $55,000" → H-201
  ├── Contrarian: "False breakdown. Will recover to $62,000 within 48h" → H-202
  └── Temporal: "Range-bound between $58,000-$62,000 for 5-7 days" → H-203
```

All three pass the gates. All three are created as competing hypotheses. The Outcome Bridge will later determine which was correct.

### Example 3: Event → No Hypothesis Created

```
Event: "Routine economic data release — no significant deviation from consensus"
  │
  ├── Causal: "No significant causal chain. Output: none."
  ├── Statistical: "Within normal range. No statistically significant prediction. Output: none."
  ├── Temporal: "No timing anomaly. Output: none."
  └── Risk: "No new risk factors identified. Output: none."
  │
  ▼
No scenario candidates. No hypotheses created. This is correct — not every event should produce a hypothesis.
```

---

## 12. Connection to Existing Hypothesis Schema

The existing Hypothesis schema (`core/schemas/hypothesis_schema.py`) defines:

```python
class Hypothesis:
    id: str
    title: str
    description: str
    predicted_consequence: str
    conditions: str
    invalidation_conditions: str
    confidence: float
    status: HypothesisStatus
    created_at: datetime
    updated_at: datetime
    status_history: List[Dict[str, Any]]
```

The Reasoning → Hypothesis pipeline maps to this schema directly. Future schema extensions may add:
- `event_id` — the event that triggered the hypothesis
- `reasoning_mode` — which reasoning mode(s) generated it
- `reasoning_council_score` — the Council evaluation score at creation

These are not required for V1. The mapping above (section 4) shows how current fields are populated.

---
