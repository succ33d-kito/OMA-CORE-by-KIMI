# Knowledge Object

*Version 1.0 — June 2026*
*Learning Core Component — ARCHITECTURE V2 Layers 11–12*

---

## 1. Executive Summary

The system currently stores data (events, trades), information (processed signals), evidence (linked to hypotheses), and hypotheses (structured beliefs). It does not store Knowledge.

Knowledge is what survives testing. It is a generalizable lesson extracted from comparing an outcome to a hypothesis. It is not raw data, not processed information, not an opinion, and not an untested belief. It is the output of the learning cycle — the component that makes future decisions better than past ones.

This document defines Knowledge as a first-class scientific object with its own lifecycle, provenance requirements, confidence model, conditions, expiration, and revision mechanism.

---

## 2. Distinctions

Understanding what Knowledge is requires understanding what it is not:

| Concept | Definition | Example | Persistence | Status in System |
|---------|------------|---------|-------------|------------------|
| **Data** | Raw, unprocessed observations | "BTC closed at 62450 at 2026-06-26 16:00 UTC" | Ephemeral or archived | Implemented |
| **Information** | Processed data with context | "BTC closed 2.3% above 20-day MA" | Ephemeral | Implemented |
| **Evidence** | Information linked to a hypothesis | "BTC closing above 20-day MA supports hypothesis H-042" | Structured in Scientific Store | Implemented |
| **Hypothesis** | A testable belief about a consequence | "If BTC stays above 20-day MA for 3 consecutive days, it will test 65000 within 1 week" | Structured with lifecycle | Implemented |
| **Outcome** | What actually happened | "BTC reached 65100 on day 4. Hypothesis confirmed." | Recorded | Partial — no comparison mechanism yet |
| **Knowledge** | A generalizable lesson extracted from comparing outcome to hypothesis | "BTC 20-day MA crossovers during low-volatility regimes have 70% accuracy for short-term targets within 1 week" | Structured with lifecycle, conditions, confidence | MISSING |
| **Criterion** | The accumulated ability to judge what matters | "The system consistently identifies which 20-day MA signals are noise and which are real" | Emergent — cannot be stored directly | EMERGENT |

Knowledge sits between Outcome and Criterion in the scientific flow:

```
Outcome → Comparison → Knowledge → Accumulation → Criterion
```

---

## 3. Knowledge Object Definition

| Aspect | Definition |
|--------|------------|
| **Purpose** | Capture validated, generalizable lessons from outcome-hypothesis comparisons. Make learning explicit, inspectable, and reusable. |
| **Identity** | Each Knowledge item has a unique ID, immutable once created. Content may be revised (see lifecycle), but the identity is permanent. |
| **Lifecycle** | 4 states: EXTRACTED → PROVISIONAL → VALIDATED/REVISED/INVALIDATED → ARCHIVED |
| **Provenance** | Every Knowledge item must trace back to the specific hypotheses, outcomes, and missed opportunities that produced it. |
| **Confidence** | Knowledge confidence is calibrated separately from hypothesis confidence. It represents how certain we are that this knowledge is correct. |
| **Conditions** | Knowledge only applies under specific conditions. When conditions are not met, the knowledge should not be used. |
| **Expiration** | Knowledge may decay or expire as conditions change. |

---

## 4. Knowledge Lifecycle

```
EXTRACTED
    │
    ▼
PROVISIONAL
    │
    ├──→ VALIDATED (replicated across multiple outcomes)
    ├──→ REVISED (updated with new evidence)
    ├──→ INVALIDATED (contradicted by new evidence)
    └──→ ARCHIVED (no longer relevant, superseded)
```

### Phase Definitions

| Phase | Description | Duration | Promotion Condition |
|-------|-------------|----------|---------------------|
| **EXTRACTED** | Knowledge has been identified from a single outcome-hypothesis comparison. It is a candidate, not yet confirmed. | Immediate → PROVISIONAL | Manual or automated review confirms the extraction is coherent. |
| **PROVISIONAL** | Knowledge is plausible but not yet validated. It may be used for reference but should not drive decisions. | Until validation threshold met | Minimum N replications (see §8) across different conditions. |
| **VALIDATED** | Knowledge has been replicated across sufficient conditions. It is trustworthy enough to inform decisions. | Until invalidated or revised | Meets all validation thresholds. |
| **REVISED** | Knowledge has been updated with new evidence. The revision is tracked, and the original is preserved for audit. | Until re-validated | Revision produces different or refined knowledge. |
| **INVALIDATED** | Knowledge has been contradicted by new evidence. The system no longer uses it but preserves it for audit. | Permanent | Single contradictory replication OR systematic evidence against. |
| **ARCHIVED** | Knowledge is no longer active. It may be VALIDATED knowledge that has passed its useful lifetime, or INVALIDATED knowledge that should not be reused. | Permanent | Expiration or supersession. |

---

## 5. Fields / Attributes

| # | Field | Type | Description | Populated At |
|---|-------|------|-------------|--------------|
| 1 | `id` | UUID | Permanent unique identifier | Creation |
| 2 | `statement` | String | The generalizable lesson. Must be a complete sentence. "If [condition], then [observation] with [confidence] under [scope]." | EXTRACTED |
| 3 | `hypothesis_ids` | UUID[] | Hypotheses that contributed to this knowledge | EXTRACTED |
| 4 | `outcome_ids` | UUID[] | Outcomes that contributed to this knowledge | EXTRACTED |
| 5 | `missed_opportunity_ids` | UUID[] | Missed opportunities that contributed (if applicable) | EXTRACTED |
| 6 | `evidence_summary` | String | Concise summary of the evidence supporting this knowledge | EXTRACTED |
| 7 | `confidence` | Float [0-1] | Calibrated confidence. Separate from hypothesis confidence. | PROVISIONAL |
| 8 | `conditions` | String | When does this knowledge apply? Market regime, volatility range, asset class, etc. | EXTRACTED |
| 9 | `scope` | String | Domain/context where this knowledge is applicable. "crypto" / "equities" / "macro" / "general" | EXTRACTED |
| 10 | `time_horizon` | String | The timeframe over which this knowledge was validated. "intraday" / "swing" / "position" / "secular" | EXTRACTED |
| 11 | `replication_count` | Int | How many times this knowledge has been independently replicated | Updated with each replication |
| 12 | `replication_conditions` | JSON | List of conditions under which replication occurred. Used to assess robustness. | Updated with each replication |
| 13 | `contrary_evidence_count` | Int | How many times this knowledge was contradicted | Updated with each contrary finding |
| 14 | `last_validated_at` | ISO8601 | When this knowledge was last confirmed | Updated |
| 15 | `expires_at` | ISO8601 (nullable) | When this knowledge should be re-evaluated. Null = no expiration (rare). | PROVISIONAL |
| 16 | `status` | String | Current lifecycle phase | Lifecycle |
| 17 | `provenance` | JSON | Full chain: which events, hypotheses, outcomes, and missed opportunities produced this knowledge | EXTRACTED |
| 18 | `revision_history` | JSON | If REVISED, previous versions of the knowledge statement | REVISED |
| 19 | `created_at` | ISO8601 | When the knowledge item was first extracted | EXTRACTED |
| 20 | `updated_at` | ISO8601 | When the knowledge item was last updated | Any phase |

---

## 6. Provenance Requirements

Every Knowledge item must be able to answer:

- **Which hypothesis produced this knowledge?** (hypothesis_ids)
- **Which outcome confirmed or contradicted it?** (outcome_ids)
- **Which missed opportunity contributed?** (missed_opportunity_ids)
- **What was the original statement?** (revision_history, first entry)
- **Under what conditions was it validated?** (conditions, scope, time_horizon)
- **How many times has it been replicated?** (replication_count)
- **How many times has it been contradicted?** (contrary_evidence_count)

Provenance is immutable. Once a source link is established, it cannot be broken. If a source hypothesis is later invalidated, the knowledge remains linked to it — the link documents the provenance, not the correctness.

---

## 7. Confidence and Scope

### Confidence Model

Knowledge confidence follows a separate scale from hypothesis confidence:

| Confidence Range | Label | Meaning |
|-----------------|-------|---------|
| 0.0 – 0.3 | SPECULATIVE | Single extraction, not yet replicated. Do not use for decisions. |
| 0.3 – 0.5 | PROVISIONAL | Some replication but insufficient for confident use. Reference only. |
| 0.5 – 0.7 | VALIDATED | Multiple replications under varied conditions. Safe for informed decisions. |
| 0.7 – 0.9 | STRONG | Extensive replication, consistent across regimes. Reliable for decision support. |
| 0.9 – 1.0 | ROBUST | Near-universal replication. Rare. May indicate a mechanical law rather than a market pattern. |

### Scope

Scope defines where the knowledge applies:

```
Scope: "crypto"
  ├── Assets: ["BTC", "ETH", "major altcoins"]
  ├── Regime: ["low volatility", "trending"]
  ├── Timeframe: "swing (3-10 days)"
  └── Exceptions: "does not apply during black swan events"
```

Knowledge applied outside its scope should be flagged. If repeatedly applied outside scope and found correct, the scope should be expanded.

---

## 8. Conditions Where Knowledge Applies

Knowledge statements should follow this structure:

> Under [conditions], when [trigger], then [outcome] with [confidence], unless [invalidation].

Example:
> Under low-volatility regimes in crypto markets, when BTC closes above 20-day MA for 3 consecutive days, then BTC will test the next resistance level within 1 week with 70% confidence, unless a macro shock occurs.

This structure makes the knowledge testable, falsifiable, and scoped.

### Condition Types

| Condition Type | Example | Impact |
|----------------|---------|--------|
| **Market regime** | Low volatility, trending, ranging, high volatility | Changes the applicability |
| **Asset class** | Crypto, equities, forex, commodities | Narrows or widens scope |
| **Time horizon** | Intraday, swing, position | Changes the expected duration |
| **External factors** | Macro events, regulatory changes, seasonality | May invalidate temporarily |
| **System state** | Position capacity, risk mode, drawdown regime | Changes whether to act |

---

## 9. Expiration / Decay

### Why Knowledge Expires

Markets change. Regimes shift. Knowledge that was valid in 2024 may be invalid in 2026. Without expiration, the system would apply increasingly stale knowledge with unwarranted confidence.

### Expiration Rules

| Condition | Expiration Action |
|-----------|-------------------|
| Knowledge has not been confirmed in 180 days | Confidence decays by 0.1 per 30 days past expiry |
| Knowledge was validated in a regime that has since changed | Status → PROVISIONAL, confidence halved |
| Knowledge is contradicted by new evidence | Status → INVALIDATED |
| Knowledge was based on a single hypothesis | Expires faster (90 days default) |
| Knowledge was extensively replicated (10+ times) | Expires slower (365 days default, renewable) |

### Decay Function (V1)

```
adjusted_confidence = base_confidence * decay_factor(days_since_last_confirmation)

decay_factor = max(0.1, 1.0 - (days_since_last_confirmation / confirmation_window))

confirmation_window = base 180 days, extended by replication_count * 30 days
```

The decay function ensures that knowledge which is never re-confirmed eventually becomes unusable, while knowledge that is regularly confirmed compound.

---

## 10. Revision and Invalidation

### Revision

Knowledge may be revised when new evidence refines rather than contradicts it:

| Condition | Action |
|-----------|--------|
| New outcome confirms knowledge but narrows conditions | Update conditions field. Status → REVISED. |
| New outcome confirms knowledge but broadens conditions | Update conditions field. Status → REVISED. |
| New outcome refines confidence (higher or lower) | Update confidence. Status remains VALIDATED unless confidence drops below threshold. |
| Multiple new outcomes produce a more precise statement | Update statement. Status → REVISED. Update replication count. |

### Invalidation

Knowledge is invalidated when:

| Condition | Action |
|-----------|--------|
| Single clear contradictory outcome | Flag for review. If review confirms, status → INVALIDATED. |
| Multiple contradictory outcomes (3+) | Automatic invalidation. Status → INVALIDATED. |
| Regime shift that invalidates underlying conditions | Status → PROVISIONAL. If not re-confirmed within 90 days → INVALIDATED. |
| Refined understanding supersedes this knowledge | New knowledge created. Old knowledge → ARCHIVED (superseded). |

### Audit Trail

Every revision and invalidation preserves:
- The previous knowledge statement
- The evidence that caused the change
- The timestamp of the change
- The confidence before and after

This prevents the system from revising away uncomfortable findings.

---

## 11. Relationship to Validated Knowledge

Validated Knowledge (ARCHITECTURE V2 Layer 11) is the subset of Knowledge with status = VALIDATED and confidence ≥ 0.5. It is the knowledge the system actively uses to inform decisions.

The Knowledge pipeline:

```
EXTRACTED ──→ PROVISIONAL ──→ VALIDATED ──→ Decision Support
                                       │
                                       └──→ Criterion Update
```

Only VALIDATED knowledge feeds into decision-making and Criterion evaluation. PROVISIONAL knowledge is for reference only.

---

## 12. Relationship to Missed Opportunity System

The Missed Opportunity System (IN-001, `docs/scientific/01_MISSED_OPPORTUNITY_SYSTEM.md`) is a primary source of Knowledge.

Its knowledge extraction process (§11 of that document) feeds directly into the Knowledge lifecycle:

```
MissedOpportunity.COMPARED
    │
    ▼
Knowledge Extraction (rule-based)
    │
    ▼
Knowledge.EXTRACTED → Knowledge.PROVISIONAL → ...
```

Knowledge from missed opportunities follows the same lifecycle and confidence model as knowledge from executed decisions. There is no distinction between "learning from action" and "learning from inaction" at the Knowledge layer — they merge.

---

## 13. Relationship to Criterion

Knowledge is the raw material for Criterion evolution. As described in `03_CRITERION_EVOLUTION.md`:

- Knowledge items are accumulated
- Patterns across knowledge items reveal Criterion trends
- Criterion deltas are derived from aggregated knowledge
- Criterion changes when knowledge consistently points in the same direction

The relationship is:

```
Knowledge items (individual lessons)
    │
    ├── aggregated → Criterion dimension scores
    ├── trended → Criterion direction
    └── applied → Better decisions → Scarce resources
```

Knowledge without Criterion impact is data. Criterion without Knowledge support is speculation.

---

## 14. Validation Method

| Method | Description | Phase |
|--------|-------------|-------|
| **Knowledge extraction tests** | Given a hypothesis-outcome pair, verify the correct knowledge is extracted. | Implementation |
| **Lifecycle tests** | Verify all state transitions: EXTRACTED → PROVISIONAL → VALIDATED, etc. | Implementation |
| **Expiration tests** | Verify decay function produces correct confidence adjustments. | Implementation |
| **Provenance tests** | Verify that source links are immutable and traceable. | Implementation |
| **Historical replay** | Extract knowledge from past outcomes and evaluate whether the knowledge would have been useful. | Implementation |
| **Knowledge quality review** | Periodic human review of a random sample of knowledge items. Assess accuracy, relevance, usefulness. | Ongoing monthly |

---

## 15. Failure Modes

| # | Failure Mode | Description | Mitigation |
|---|-------------|-------------|------------|
| 1 | **Knowledge overload** | Every comparison produces knowledge, overwhelming the store. | Minimum replication threshold for PROVISIONAL status. Extraction is cheap; promotion is expensive. |
| 2 | **Trivial knowledge** | Extracted lessons are obvious ("if price goes up, long positions profit"). | Filter on novelty. Knowledge must provide non-trivial insight. |
| 3 | **Overfitting** | Knowledge is too specific to be generalizable. | Minimum scope requirement. Knowledge that applies to exactly one asset in exactly one regime is suspect. |
| 4 | **Confirmation bias** | The system only extracts knowledge that confirms existing beliefs. | Force extraction from contradictory outcomes. Track confirmation/contradiction ratio. |
| 5 | **Stale knowledge confidence** | Old knowledge retains high confidence despite regime changes. | Expiration and decay function. Automatic re-evaluation triggers. |
| 6 | **Revision without improvement** | Knowledge is revised but not improved — just changed. | Require that revisions produce measurably better predictions. Track revision quality over time. |

---
