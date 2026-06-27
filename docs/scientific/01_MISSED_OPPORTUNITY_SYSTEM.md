# Missed Opportunity Intelligence System v1

## The First Learning Component of the Scientific Learning Layer

*Version 1.0 — June 2026*
*IN-001 (Innovation Engine) — GREEN lane*
*Canonical Reference: docs/ARCHITECTURE_V2.md*
*Innovation Reference: docs/innovation/01_IMPLEMENT_NOW.md*

---

## 1. Executive Summary

### Why Missed Opportunities Are One of the Richest Learning Sources

Every decision system has an asymmetry: it sees the outcomes of what it did, but not the outcomes of what it did not do. This is selection bias — the most persistent and dangerous bias in learning systems. A system that learns only from its actions will systematically reinforce the actions it took, never learning whether inaction would have been better.

O.M.A.-C.O.R.E. currently records this:

```
Signal generated → Signal evaluated → Signal blocked → Lost
```

The information loss at "Lost" is catastrophic. The signal carried a hypothesis — a belief about a consequence. The signal carried evidence — observations that supported or contradicted that belief. The signal carried a decision — a choice to act or not act. All of this is discarded the moment the signal is blocked.

The Missed Opportunity Intelligence System transforms this loss into learning. It captures not just the fact of blocking, but the reasoning, the context, the expected outcome, and — crucially — the eventual outcome that would have been compared had the action been taken. It then feeds this learning back into the system's Criterion.

### Doing Nothing Is Also a Decision

The system's architecture defines Decision as "commitment to a course of action based on hypothesis evaluation" (ARCHITECTURE_V2.md §3). Not choosing is still a choice. Ignoring an opportunity is still a decision outcome. The only difference is that the outcome of "doing nothing" is never directly observed — it must be estimated and later validated.

The Missed Opportunity System makes "doing nothing" a first-class scientific object, subject to the same lifecycle, evaluation, and learning as any executed decision.

---

## 2. Problem Statement

### Current Limitation

Today, the system's signal path works as follows:

```
Market Data → Event → AgentOpinions → CouncilDecision → Guard Evaluation → 
    ├── Approved → PaperTradingEngine → Trade → Outcome
    └── Blocked → [DISCARDED]
```

When a signal is blocked — whether by CapitalGuard (capacity full), CrashDetector (crash mode), DirectionController (direction disabled), KnifeDetector (falling knife), or any other guard — the system loses:

1. **The hypothesis** that generated the signal. What did the agents believe would happen?
2. **The evidence** that supported it. What data led to this conclusion?
3. **The reasoning** that produced the recommendation. Why this opportunity and not another?
4. **The expected outcome.** What did the system predict would happen if it acted?
5. **The risk assessment.** What risk did the system identify?
6. **The approval context.** Which guard blocked it and why?
7. **The market conditions.** What was happening at the time?
8. **The scarce resource state.** Was capital available? Was attention available?

All of this information exists in memory for approximately one second during signal processing, then it is discarded. The system retains only that a signal was generated and blocked. It cannot answer:

- "Was blocking this signal correct?"
- "What happened to the opportunity after we ignored it?"
- "Did the market prove our hypothesis right or wrong?"
- "Did we lose money by not acting?"
- "Did we avoid a loss by not acting?"
- "What should we learn from this?"

This is not just an observability gap. It is a learning gap. Every blocked signal is a hypothesis that the system never tested. A hypothesis that is never tested produces no learning. The system is discarding its most abundant data source.

---

## 3. Scientific Thesis

> Every missed opportunity is an experiment that already happened. The only missing part is measuring its outcome.

When the Council produces a decision and a guard blocks it, an experiment was designed:
- A hypothesis was formed (explicitly by the agents, implicitly by the Council)
- Evidence was assembled
- A consequence was predicted
- A decision was made
- The decision was not executed

The experiment was stopped before the outcome phase, but the hypothesis, evidence, and predicted consequence exist. They are a complete scientific record missing only the final outcome.

The Missed Opportunity System completes this record by:
1. Capturing the pre-decision state (hypothesis, evidence, reasoning, context)
2. Tracking the opportunity forward in time (what actually happened in the market)
3. Comparing the predicted outcome with the actual outcome
4. Assigning a verdict (would the action have succeeded or failed?)
5. Extracting knowledge (what does this teach us about our criteria?)
6. Updating Criterion (what should change in how we evaluate future opportunities?)

This transforms every block from a dead end into a learning cycle.

---

## 4. Object Definition

### MissedOpportunity

| Aspect | Definition |
|--------|------------|
| **Purpose** | Capture, track, evaluate, and learn from every opportunity the system evaluated but did not execute. Transform blocked signals into validated learning. |
| **Identity** | Each MissedOpportunity has a unique ID, immutable from creation. It is a first-class scientific object with its own lifecycle, persistence, and relationships. |
| **Lifecycle** | 10 phases from Detected through Archived (see §6). The object moves through these phases over time, potentially spanning days or weeks. |
| **Inputs** | CouncilDecision (the decision that was blocked), Guard evaluation results, Market context at decision time, Scarce resource state |
| **Outputs** | Verified knowledge (did blocking the opportunity prove correct?), Criterion delta (what should change in evaluation criteria), Opportunity cost estimate |
| **Relationships** | Links to: originating Event(s), Hypothesis (if available), Evidence used in reasoning, Decision that was blocked, Guard(s) that blocked it, future Outcome of the same asset/opportunity |
| **Future Persistence** | Dedicated SQLite table in `scientific.db`, isolated from operational `oma_core.db`. Append-only — once written, MissedOpportunity records are immutable except for outcome and knowledge fields. |

### Position in the Scientific Object Model

```
Event ──→ Reasoning ──→ Hypothesis ──→ Evidence ──→ Decision ──→ Approval
                                                                      │
                                                    ┌─────────────────┤
                                                    │                 │
                                                    ▼                 ▼
                                              EXECUTION        MISSED OPPORTUNITY
                                                    │                 │
                                                    ▼                 ▼
                                              Outcome         Observed Outcome
                                                    │                 │
                                                    └──────┬──────────┘
                                                           ▼
                                                  Validated Knowledge
                                                           │
                                                           ▼
                                                      Criterion
```

MissedOpportunity is a parallel branch to Execution. It does not replace or modify the execution path. It observes the decision from the side and tracks what happens to the opportunity that was not taken.

---

## 5. Object Attributes

| # | Field | Type | Description | Populated At |
|---|-------|------|-------------|--------------|
| 1 | `unique_id` | UUID | Permanent immutable identifier. | Detection |
| 2 | `timestamp` | ISO8601 | When the opportunity was evaluated and blocked. | Detection |
| 3 | `signal_id` | String | Reference to the originating signal or CouncilDecision ID. | Detection |
| 4 | `hypothesis_id` | String (nullable) | Link to the Hypothesis that generated this signal. Null if no hypothesis link exists yet (pre-Iteration 3). | Detection |
| 5 | `evidence_snapshot` | JSON | Snapshot of evidence available at decision time: event data, agent opinions, confidence levels, conviction. Not a link — a copy, because evidence may change. | Detection |
| 6 | `reasoning_snapshot` | JSON | The reasoning trace: which agents recommended what, why, what alternatives were considered, what the Council concluded. | Detection |
| 7 | `confidence` | Float [0–1] | Council's confidence in the decision at decision time. | Detection |
| 8 | `risk` | Float [0–1] | Risk assessment at decision time. Higher = more risk identified. | Detection |
| 9 | `expected_return` | Float (nullable) | The expected return or impact if the decision had been executed. May be estimated or explicit. | Detection |
| 10 | `required_capital` | Float (nullable) | Capital that would have been required to execute. Null if not applicable (non-trading domains). | Detection |
| 11 | `block_reason` | String (enum) | Primary reason the opportunity was blocked (see §7 classification). | Detection |
| 12 | `block_reason_detail` | String | Human-readable detail: which guard, which threshold, what value exceeded what limit. | Detection |
| 13 | `block_reasons_additional` | JSON Array | Secondary block reasons. An opportunity may be blocked by multiple guards simultaneously. | Detection |
| 14 | `decision_context` | JSON | Full decision context: portfolio state, position count, available capital, active positions, current drawdown, regime detection. | Detection |
| 15 | `market_context` | JSON | Market conditions at decision time: volatility, trend, volume, relevant macro events, regime classification. | Detection |
| 16 | `scarce_resources_at_time` | JSON | Snapshot of scarce resource availability: capital free, attention budget remaining, time pressure, health/energy level (future). | Detection |
| 17 | `approval_status` | String | Was approval attempted? `NOT_ATTEMPTED` / `ATTEMPTED_BLOCKED` / `AWAITING_APPROVAL` (future). | Detection |
| 18 | `execution_status` | String | `NOT_EXECUTED` / `PARTIALLY_EXECUTED` (if partially filled then blocked) / `CANCELLED`. | Detection |
| 19 | `future_outcome` | JSON (nullable) | What actually happened to the opportunity after it was blocked. Populated during Observation phase. Contains: observed_price_movement, observed_volume, event_occurred, outcome_window_start, outcome_window_end, peak_favorable, trough_adverse. | Observation |
| 20 | `opportunity_cost` | Float (nullable) | Estimated cost of missing this opportunity. Positive = lost profit. Negative = loss avoided. Computed during Comparison phase. | Comparison |
| 21 | `opportunity_cost_detail` | JSON | Breakdown of opportunity cost: financial, time, attention components. Future: knowledge, relationship components. | Comparison |
| 22 | `validated` | Boolean | Whether this missed opportunity has been validated against actual outcomes. | Comparison |
| 23 | `verdict` | String (enum, nullable) | `CORRECT_BLOCK` (opportunity would have lost money or caused harm) / `INCORRECT_BLOCK` (opportunity would have succeeded) / `INCONCLUSIVE` (outcome ambiguous) / `UNKNOWN` (outcome not observable). | Comparison |
| 24 | `knowledge_generated` | JSON (nullable) | Structured knowledge extracted from this missed opportunity. Contains: statement, confidence, conditions, applicability (see §11). | Knowledge Generation |
| 25 | `knowledge_id` | String (nullable) | Link to Knowledge object when Knowledge lifecycle exists (Iteration 6). Future. | Knowledge Generation |
| 26 | `criterion_delta` | JSON (nullable) | Recommended change to Criterion based on this missed opportunity. Contains: dimension, direction, magnitude, evidence_weight. | Criterion Update |
| 27 | `lesson_abstract` | String | One-sentence summary of what was learned. "Blocking this BTC long during crash mode was correct — price dropped 12% within 4 hours." | Knowledge Generation |
| 28 | `archive_status` | String | `ACTIVE` / `OBSERVING` / `EVALUATED` / `KNOWLEDGE_EXTRACTED` / `CRITERION_UPDATED` / `ARCHIVED`. | Lifecycle |
| 29 | `created_at` | ISO8601 | When the record was created. | Detection |
| 30 | `updated_at` | ISO8601 | When the record was last updated. | Any phase |
| 31 | `observed_at` | ISO8601 (nullable) | When the outcome observation window closed. | Observation |
| 32 | `evaluated_at` | ISO8601 (nullable) | When the verdict was assigned. | Comparison |

---

## 6. Lifecycle

### Phases

```
DETECTED
    │
    ▼
CANDIDATE
    │
    ▼
BLOCKED
    │
    ▼
RECORDED
    │
    ▼
OBSERVING ─────────────────────────────────────────────┐
    │ (periodic checks, waiting for outcome window)      │
    │                                                    │
    ▼                                                    │
OUTCOME_AVAILABLE                                        │
    │                                                    │
    ▼                                                    │
COMPARED                                                 │
    │                                                    │
    ▼                                                    │
KNOWLEDGE_GENERATED                                      │
    │                                                    │
    ▼                                                    │
CRITERION_UPDATED                                        │
    │                                                    │
    ▼                                                    │
ARCHIVED ◄───────────────────────────────────────────────┘
```

### Transition Definitions

| From | To | Condition | Description |
|------|----|-----------|-------------|
| **DETECTED** | **CANDIDATE** | A signal was generated and entered the evaluation pipeline. Minimum: signal exists with any evaluation. | The system has noticed an opportunity exists. Not yet blocked — still being evaluated. |
| **CANDIDATE** | **BLOCKED** | A guard rejected the signal, OR Council decided not to act, OR capacity was full. | The opportunity was explicitly rejected. The decision not to act is recorded. |
| **CANDIDATE** | **RECORDED** | (Alternative path) The opportunity was not actively blocked but expired before evaluation. | Some opportunities expire naturally (time decay, price moved beyond entry range). These are still missed opportunities. |
| **BLOCKED** | **RECORDED** | The MissedOpportunity object is fully populated and persisted. | All pre-decision data is captured. The record becomes immutable for pre-outcome fields. |
| **RECORDED** | **OBSERVING** | The outcome observation window opens. Defined by the hypothesis's time horizon or a default observation period. | The system begins monitoring what happens to the market/asset/context that the opportunity was about. |
| **OBSERVING** | **OUTCOME_AVAILABLE** | The observation window closes OR a significant event occurs that determines the outcome. | Enough time has passed to evaluate whether the opportunity would have succeeded or failed. The outcome data is ready. |
| **OUTCOME_AVAILABLE** | **COMPARED** | Outcome data is compared with the predicted consequence. Verdict is assigned. | The system determines: was the block correct? Would the action have succeeded? |
| **COMPARED** | **KNOWLEDGE_GENERATED** | Verdict exists. Knowledge is extracted from the comparison. | A generalizable lesson is formulated. "Blocking low-confidence signals during high volatility preserves capital." |
| **KNOWLEDGE_GENERATED** | **CRITERION_UPDATED** | Knowledge is evaluated for Criterion impact. | The system determines whether Criterion should change based on this learning. Not every knowledge item changes Criterion — only significant or repeated findings. |
| **CRITERION_UPDATED** | **ARCHIVED** | All learning is extracted. The opportunity is no longer needed for active reference. | The record is preserved immutably for historical analysis but no longer actively monitored. |

### Transition Rules

- **No skipped transitions.** An opportunity cannot go from DETECTED to COMPARED without passing through the intermediate states. Each phase has a purpose.
- **Observation has a timeout.** If the observation window expires without a clear outcome, the record moves to COMPARED with verdict = INCONCLUSIVE. It is not left in OBSERVING indefinitely.
- **Knowledge generation is required before archival.** An opportunity cannot be archived without at least attempting knowledge extraction. Even "no learning available" is a valid knowledge statement.
- **Backward transitions are allowed but require reason.** An observed outcome may be invalidated by subsequent events (e.g., a flash crash that reversed). The record may return to OBSERVING with a documented reason.

### Timing

| Phase | Typical Duration | Notes |
|-------|-----------------|-------|
| DETECTED → BLOCKED | Milliseconds to seconds | Happens during signal processing |
| BLOCKED → RECORDED | Milliseconds | Persistence write |
| RECORDED → OBSERVING | Immediate | Observation begins right away |
| OBSERVING → OUTCOME_AVAILABLE | Hours to weeks | Depends on hypothesis time horizon |
| OUTCOME_AVAILABLE → COMPARED | Minutes to hours | Automated comparison |
| COMPARED → KNOWLEDGE_GENERATED | Minutes to days | May involve batch processing |
| KNOWLEDGE_GENERATED → CRITERION_UPDATED | Minutes to days | May require accumulation |
| CRITERION_UPDATED → ARCHIVED | Immediate | |

---

## 7. Classification

### Block Reason Categories

Every missed opportunity must be classified by why it was missed. Multiple causes are allowed — a signal may be blocked by CapitalGuard AND CrashDetector simultaneously.

| # | Category | Description | Source | Example |
|---|----------|-------------|--------|---------|
| 1 | **EXECUTION_CAPACITY** | Position limit reached. Cannot open more positions. | CapitalGuard, PaperTradingEngine | "Max 5 concurrent positions. Currently at 5." |
| 2 | **CAPITAL_CONSTRAINT** | Insufficient free capital. | CapitalGuard | "Free capital below minimum threshold." |
| 3 | **RISK_GUARD** | Active risk guard rejected the signal. | CrashDetector, KnifeDetector, DirectionController, GapRisk | "Crash mode active. Direction disabled." |
| 4 | **MISSING_EVIDENCE** | Evidence was insufficient to justify action. | Council (confidence below threshold), guard | "Agent consensus below 0.6 threshold." |
| 5 | **LOW_CONFIDENCE** | Council confidence was too low to proceed. | Council | "Confidence 0.35, minimum 0.5 required." |
| 6 | **DUPLICATE** | Similar opportunity already active or recently evaluated. | Pipeline deduplication | "Same signal already processed within cooldown window." |
| 7 | **COOLDOWN** | Asset or market in cooldown after recent action. | DirectionController, strategy rules | "BTC in 24h cooldown after stop loss." |
| 8 | **DATA_QUALITY** | Poor data quality prevented reliable evaluation. | Collector validation, data quality engine | "Bid-ask spread exceeds 5%. Stale data." |
| 9 | **TIMEOUT** | Opportunity expired before processing completed. | Pipeline timing | "Event was older than max processing age." |
| 10 | **STRATEGY_FILTER** | Did not match active strategy criteria. | Strategy rules, Council | "Asset not in current strategy universe." |
| 11 | **USER_OVERRIDE** | Explicitly rejected by the user. | CLI, cockpit, Telegram | "User dismissed notification." |
| 12 | **CAPACITY_ATTENTION** | No attention budget available to evaluate this opportunity. | Future: Attention budget tracker | "Attention budget exhausted for this period." |
| 13 | **UNKNOWN** | Reason not captured or not classifiable. | Fallback | "Block reason not recorded by guard." |

### Block Reason Detail

Each block reason should carry structured detail, for example:

```
block_reason: "RISK_GUARD"
block_reason_detail: "CrashDetector.crash_mode() returned PANIC at 2026-06-26T14:30:00Z.
                      Window: 5min. Drop: 3.2%. Threshold: 2.5%."
```

This enables precise analysis of which guards are blocking which signals, and whether those blocks are correct.

---

## 8. Metrics

### Primary Metrics

| # | Metric | Definition | Why It Matters |
|---|--------|------------|----------------|
| 1 | **Average Opportunity Cost** | Mean opportunity cost across all evaluated missed opportunities within a time window. | Indicates whether the system is missing valuable opportunities on average. Rising trend = problem. Falling trend = guards are improving. |
| 2 | **Highest Missed Return** | Maximum positive opportunity cost (profit that would have been earned if executed). | Identifies the most expensive single miss. Each high-value miss is a candidate for guard re-evaluation. |
| 3 | **Highest Missed Loss Avoided** | Maximum negative opportunity cost (loss that was avoided by not executing). | Identifies the best block decisions. Validates that guards are working correctly. |
| 4 | **Top Block Reasons** | Frequency distribution of block_reason across all missed opportunities. | Reveals which guards block the most signals. A guard that blocks 90% of signals may need threshold adjustment. |
| 5 | **Most Frequent Asset** | Asset with the highest number of missed opportunities. | Indicates whether certain assets are systematically under-traded. May indicate data quality issues or strategy gaps. |
| 6 | **Most Valuable Missed Hypothesis** | The hypothesis with the highest opportunity cost if it was incorrectly blocked. | Identifies which hypothesis classes need better evaluation criteria. |
| 7 | **Knowledge Generated** | Count of knowledge items extracted from missed opportunities per period. | Measures the learning yield of the Missed Opportunity System itself. |
| 8 | **Criterion Delta** | Aggregate magnitude of Criterion changes driven by missed opportunity learning. | Measures whether missed opportunity learning is actually changing the system's judgment. |
| 9 | **Opportunity Lifetime** | Average time from detection to observation window close. | Measures how long it takes to validate a block decision. Shorter = faster learning cycles. |
| 10 | **Block Frequency** | Opportunities blocked per unit time. | Baseline volume. Sudden changes may indicate regime shifts or configuration drift. |
| 11 | **Learning Efficiency** | Knowledge items generated per 100 missed opportunities. | Measures the system's ability to extract signal from noise. Low efficiency may indicate most blocks are random. |
| 12 | **Confidence Calibration (Missed)** | For missed opportunities with confidence records: does confidence correlate with correctness of the block? | If high-confidence blocks are frequently incorrect, the Council's confidence is poorly calibrated for the blocking context. |

### Derived Reports

| Report | Composition | Audience |
|--------|-------------|----------|
| **Weekly Missed Opportunity Summary** | Top 5 misses by opportunity cost, top block reasons, learning generated | Daily/weekly review (09_REVIEW_CADENCE.md) |
| **Guard Effectiveness Report** | Per-guard breakdown: opportunities blocked, correctness rate, average opportunity cost | Monthly review — may prompt guard threshold adjustments |
| **Hypothesis-Class Miss Analysis** | Which hypothesis classes are most frequently blocked and whether blocking was correct | Strategic backlog review — may indicate need for better hypothesis formation |
| **Learning Yield Report** | Knowledge generated per period, Criterion delta, most common lessons extracted | Quarterly review — measures the Missed Opportunity System's own effectiveness |

---

## 9. Scientific Integration

### Where MissedOpportunity Enters the Scientific Learning Flow

The canonical Scientific Learning Flow (ARCHITECTURE_V2.md §3):

```
Reality → Observation → Event → Reasoning → Hypothesis → Evidence → 
Decision → Approval → Execution/Action → Outcome → Validated Knowledge → 
Criterion → Scarce Resources → Reinvestment → Stronger Criterion
```

MissedOpportunity enters at the **Approval → Execution** boundary:

```
                          Decision
                             │
                             ▼
                         Approval
                        ┌───────┴───────┐
                        │               │
                        ▼               ▼
                    Execution    MissedOpportunity.DETECTED
                        │               │
                        ▼               ▼
                    Outcome     MissedOpportunity.OBSERVING
                        │               │
                        └───────┬───────┘
                                │
                                ▼
                    MissedOpportunity.OUTCOME_AVAILABLE
                                │
                                ▼
                    MissedOpportunity.COMPARED
                                │
                                ▼
                    MissedOpportunity.KNOWLEDGE_GENERATED
                                │
                                ▼
                    MissedOpportunity.CRITERION_UPDATED
                                │
                                ▼
                          Validated Knowledge
                                │
                                ▼
                           Criterion
```

### Integration Points

| Layer | Integration | Direction |
|-------|-------------|-----------|
| **Reasoning** | Receives the reasoning trace from the decision pipeline. | Pipeline → MissedOpportunity |
| **Hypothesis** | If hypothesis_id exists (post-Iteration 3), links to the hypothesis being tested. | Pipeline → MissedOpportunity |
| **Evidence** | Receives evidence snapshot at decision time. Immutable copy. | Pipeline → MissedOpportunity |
| **Decision** | Receives the decision that was made (not to act). This is the trigger. | Pipeline → MissedOpportunity |
| **Approval** | Receives the approval/guard results showing why the decision was blocked. | Pipeline → MissedOpportunity |
| **Execution** | Not touched. MissedOpportunity does not execute anything. | None |
| **Outcome** | MissedOpportunity does not create outcomes. It observes what happened in the market and compares it to the predicted consequence. The actual trade outcome (if one existed) is from the Execution branch. | Market → MissedOpportunity |
| **Validated Knowledge** | Knowledge generated by MissedOpportunity feeds into the same Knowledge layer as knowledge from executed outcomes. | MissedOpportunity → Knowledge |
| **Criterion** | Criterion delta from MissedOpportunity feeds into the same Criterion layer as all other learning. | MissedOpportunity → Criterion |

### Critical Design Rule

MissedOpportunity is **read-only from the pipeline and write-only from its own lifecycle**. It reads from the decision pipeline at the moment of blocking, then operates independently. It does not modify any pipeline component. It does not inject data back into the Council, agents, or guards. Its output goes only to Knowledge and Criterion — the learning layers.

This isolation ensures the Missed Opportunity System cannot destabilize the operational pipeline.

---

## 10. Future Outcome Bridge

### Interface Design (No Implementation)

The Outcome Bridge is the mechanism that answer the question: *"What happened to the opportunity we ignored?"*

It is the most critical design element of the system. Without it, MissedOpportunity remains historical data. With it, MissedOpportunity becomes learning.

### Input

```
Market data over time window:
  - Price series (OHLCV) for the target asset
  - Volume profile
  - Related asset performance
  - Relevant event occurrences
  
From MissedOpportunity record:
  - unique_id (to match the outcome to the opportunity)
  - hypothesis_id (to know what was predicted)
  - expected_return (the prediction)
  - confidence (how confident the prediction was)
  - observation_window_start
  - observation_window_end (or event-driven trigger)
```

### Processing

```
1. Observation window opens (RECORDED → OBSERVING).
2. Market data is collected for the target asset over the window.
3. The predicted consequence is compared with actual price/volume movement.
4. Verdict is assigned based on the comparison.
5. Opportunity cost is computed.
```

### Output

```
{
  "missed_opportunity_id": "uuid",
  "verdict": "CORRECT_BLOCK" | "INCORRECT_BLOCK" | "INCONCLUSIVE",
  "opportunity_cost": float,
  "opportunity_cost_breakdown": {
    "financial": float,
    "time_saved_or_lost": float,
    "attention_saved_or_spent": float
  },
  "outcome_details": {
    "price_at_entry": float,
    "price_at_exit": float,
    "peak_during_window": float,
    "trough_during_window": float,
    "volume_during_window": float,
    "events_during_window": []
  },
  "comparison_notes": "string"
}
```

### Outcome Window Determination

The observation window is determined by the hypothesis's time horizon:

| Hypothesis Time Horizon | Default Observation Window | Notes |
|------------------------|---------------------------|-------|
| Not specified | 24 hours | Conservative default |
| Scalp (minutes) | 1 hour | Fast feedback |
| Intraday | 1 trading day | Close-to-close |
| Swing (days) | 5 trading days | Captures expected move |
| Position (weeks) | 20 trading days | ~1 calendar month |
| Macro (months) | 60 trading days | ~3 calendar months |

The window must be adjustable per hypothesis class and per asset. Future versions should support dynamic windows based on volatility (longer windows for high-volatility assets to reduce noise).

### Limitations of the Bridge

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Counterfactual uncertainty** | We can never know for certain whether executing would have produced the exact simulated outcome. Slippage, timing, partial fills differ. | Always qualify opportunity cost as estimated, not exact. Use ranges (best/worst/most likely). |
| **Path dependency** | The outcome of an action depends on when and how it is executed. A missed entry at 10:00 may have succeeded while execution at 10:01 would have failed. | Use the entry conditions specified in the original signal. Document any assumptions. |
| **Market impact** | Our own execution, had it happened, would have affected the market (especially for large positions). | For paper trading capital levels, impact is negligible. Flag large-position opportunities. |
| **Regime changes** | The market context may change between block and observation, making comparison meaningless. | If a regime change is detected during the observation window, mark the comparison as INCONCLUSIVE with a regime change note. |

---

## 11. Knowledge Generation

### From Missed Opportunity to Validated Knowledge

A missed opportunity becomes validated knowledge through a structured extraction process. The goal is not to remember every block — it is to extract generalizable lessons that improve future evaluations.

### Knowledge Extraction Rules

| Condition | Knowledge Generated | Example |
|-----------|--------------------|---------|
| **Correct block, repeated** | "Signals of this type blocked by this guard are consistently correct." | "CrashDetector blocks on 5min 2.5% drops during low volume are correct 90% of the time." |
| **Incorrect block, repeated** | "Signals of this type blocked by this guard are consistently incorrect." | "CapitalGuard blocks on crypto assets during high volatility are too conservative. 70% of blocked crypto signals would have been profitable." |
| **Correct block, specific condition** | "This guard is correct under specific market conditions." | "CrashDetector is correct during panic events but incorrect during normal volatility spikes above 2.5%." |
| **Incorrect block, specific condition** | "This guard causes misses under specific conditions." | "DirectionController incorrectly blocks long signals during bear market rallies. The directional bias should be re-evaluated after 3 consecutive incorrect blocks." |
| **High-value miss** | "This class of opportunity should have higher priority." | "Macro-driven gold signals have the highest opportunity cost when blocked. Consider increasing their approval priority." |
| **Pattern discovered** | "A correlation exists between block reasons and outcomes." | "Opportunities blocked by CAPITAL_CONSTRAINT between 14:00-16:00 UTC on Fridays are wrong 60% of the time — liquidity patterns cause false capacity signals." |

### Knowledge Format

Each knowledge item extracted from a MissedOpportunity follows this structure:

```
{
  "id": "uuid",
  "source_type": "MISSED_OPPORTUNITY",
  "source_ids": ["mo_uuid_1", "mo_uuid_2", ...],
  "statement": "string — the generalizable lesson",
  "confidence": float [0-1],
  "conditions": "string — when does this knowledge apply?",
  "evidence_count": int,
  "first_observed": "ISO8601",
  "last_observed": "ISO8601",
  "verdict": "PROVISIONAL" | "VALIDATED" | "REVISED" | "INVALIDATED",
  "impact": "CRITERION" | "GUARD_THRESHOLD" | "HYPOTHESIS_PRIORITY" | "CAPACITY"
}
```

### Aggregation

Knowledge is rarely generated from a single MissedOpportunity. Most knowledge requires aggregation — the same pattern appearing across multiple missed opportunities before it reaches statistical significance.

Minimum evidence thresholds:

| Knowledge Type | Minimum Evidences | Description |
|----------------|-------------------|-------------|
| **Guard correctness** | 5 | Before concluding a guard is correctly/incorrectly blocking |
| **Pattern discovery** | 10 | Before concluding a pattern exists |
| **Criterion change** | 20 | Before Criterion delta is applied (see §12) |
| **Strategy change** | 30 | Before suggesting a strategy adjustment |

These thresholds prevent the system from over-learning from single events. They are intentionally conservative.

---

## 12. Criterion Impact

### How Repeated Missed Opportunities Modify Criterion

Criterion is the accumulated ability to judge what matters. It is not a component — it emerges from learning. The Missed Opportunity System feeds Criterion through repeated, aggregated findings that shift how the system evaluates future opportunities.

### Criterion Dimensions Affected

| Criterion Dimension | How MissedOpportunity Affects It |
|---------------------|----------------------------------|
| **Hypothesis Quality** | Repeated incorrect blocks of a hypothesis class suggest the class is undervalued. Criterion adjusts: "Hypotheses of this type deserve higher/lower priority." |
| **Evidence Quality** | When high-confidence blocked opportunities are frequently correct, the evidence threshold may be too high. Criterion adjusts: "Lower the evidence threshold for this signal type." |
| **Decision Utility** | When a specific guard consistently blocks valuable opportunities, the guard's weight in the decision process is questioned. Criterion adjusts: "Re-evaluate guard X threshold." |
| **Calibration** | When confidence of blocked signals correlates with incorrect blocks, the confidence model is poorly calibrated for the blocking context. Criterion adjusts: "Confidence for blocked decisions needs recalibration." |
| **Learning Velocity** | When the MissedOpportunity system generates high-value knowledge, the system's learning velocity increases. When it generates noise, the system learns to filter. |

### Criterion Delta Application

A Criterion delta is not applied immediately. It follows this process:

```
1. Knowledge extraction produces a finding (e.g., "CapitalGuard blocks are 70% correct")
2. The finding is accumulated with similar findings
3. When evidence thresholds are met (§11), a Criterion delta is proposed
4. The delta is reviewed (automated for low-impact, human-reviewed for high-impact)
5. If approved, the delta is applied to the relevant evaluation criteria
6. The delta is recorded with source evidence for traceability
```

### Example

```
Finding: "DirectionController incorrectly blocked long BTC signals 
          6 out of 8 times during the past 30 days during bear market rallies."
          
Evidence: 8 MissedOpportunity records, all with verdict = INCORRECT_BLOCK,
          all blocked by DirectionController, all long signals during 
          confirmed bear market.

Criterion Delta Proposed: "Temporarily reduce DirectionController's 
           long-blocking threshold during bear market rallies from 
           'immediate block if direction = opposite' to 
           'block only if conviction > 0.8'."

Review: Automated threshold within allowed guard range. Applied.

Monitoring: Watch the next 20 similar opportunities. If incorrect block rate 
           drops below 30%, make the change permanent. If it increases, revert.
```

### Safety

Criterion deltas from MissedOpportunity are always:
- **Reversible** — if the delta produces worse outcomes, it is rolled back
- **Measurable** — the impact of the delta is tracked
- **Attributable** — the source evidence for the delta is always recorded
- **Conservative** — the evidence thresholds ensure the system does not oscillate

---

## 13. Scarce Resources

### How MissedOpportunity Protects Scarce Resources

The primary scarce resource protected by the Missed Opportunity System is **Knowledge** — every missed opportunity that is analyzed produces learning that would otherwise be lost. But it protects other resources as well:

### Resource Impact Matrix

| Scarce Resource | How MissedOpportunity Protects It | How MissedOpportunity Could Consume It (Risk) |
|-----------------|-----------------------------------|-----------------------------------------------|
| **Capital** | Identifying when blocks are incorrect prevents future missed profits. Identifying when blocks are correct prevents future losses from overtrading. | None — no capital is allocated by this system. |
| **Time** | Learning from blocks reduces the time spent evaluating similar opportunities incorrectly in the future. | Time spent maintaining and reviewing the system must be justified by learning yield. A MissedOpportunity system that produces no learning is consuming time. |
| **Attention** | By learning which blocks are consistently incorrect, the system reduces the attention needed to manually review those decisions. | If every MissedOpportunity generates a notification, attention is consumed. The Notification Quality Gate (IN-006) must manage this. |
| **Knowledge** | This is the primary benefit. Every missed opportunity that produces a lesson adds to accumulated knowledge. | Incorrectly analyzed opportunities can create false knowledge, which is worse than no knowledge. Verdict validation is critical. |
| **Relationships** | Indirect — better decision quality in trading and business domains preserves relationships that would be damaged by poor decisions. | None directly. |
| **Mobility** | Indirect — better resource allocation preserves the freedom to move between opportunities and domains. | None directly. |
| **Health** | Indirect — by reducing the stress of "did we miss something important?" through systematic tracking. | If the system generates anxiety about missed opportunities, it harms health. The system must present misses as learning, not loss. |
| **Freedom of Decision** | By learning from missed opportunities, the system reduces the need for manual oversight of every decision, increasing autonomy. | If the system becomes too conservative due to over-learning from past misses, it reduces freedom. |

### Opportunity Cost Is Not Only Financial

The MissedOpportunity object captures opportunity cost as a multi-dimensional value, not just financial PnL:

```
opportunity_cost_detail = {
  "financial": { "estimated": 250.0, "confidence": 0.6, "range": [100.0, 400.0] },
  "time":     { "estimated_hours_saved": 0.5, "confidence": 0.8 },
  "attention": { "estimated_units": 1, "quality": "low_priority" },
  "knowledge": { "learning_value": "medium", "novelty": "low" }
}
```

A missed opportunity that would have consumed 3 hours of attention and produced minimal financial return may have a positive opportunity cost (good that we missed it) even if the financial opportunity cost is negative (we lost potential profit). The system must track both dimensions.

---

## 14. Decision Approval Integration

### Future Interaction with the Decision Approval Engine

The Decision Approval Engine (ARCHITECTURE_V2.md §3 — MISSING, PLANNED for future) will evaluate whether a decision is safe to auto-execute. The Missed Opportunity System provides critical evidence for this evaluation.

### Feedback Loop

```
                         Decision Approval Engine
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            APPROVED                           BLOCKED
                    │                               │
                    ▼                               ▼
              Execution                    MissedOpportunity System
                    │                               │
                    ▼                               ▼
              Outcome                      Knowledge Generated
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                          Approval Criteria Update
                                    │
                                    ▼
                     Decision Approval Engine (next cycle)
```

### How MissedOpportunity Data Feeds Approval

| MissedOpportunity Finding | Impact on Approval Engine |
|---------------------------|---------------------------|
| "This signal type is blocked frequently but most blocks are INCORRECT." | Raise approval priority for this signal type. The engine should be more willing to approve it. |
| "This signal type is blocked frequently and most blocks are CORRECT." | Lower approval priority for this signal type. The engine should be less willing to approve it. |
| "This guard blocks signal type X, and the blocks are 90% correct." | The guard's threshold should be preserved or tightened. |
| "This guard blocks signal type X, and the blocks are 60% incorrect." | The guard's threshold should be reviewed. The Approval Engine may override this guard for this signal type. |
| "Under market conditions Y, blocks of any type are X% more likely to be incorrect." | Adjust baseline approval thresholds for condition Y. |

### Design Principle

The Missed Opportunity System does not directly modify approval criteria. It produces evidence. The Decision Approval Engine (future) reads that evidence and decides whether to adjust its thresholds. This separation preserves the one-person maintainability constraint — each component does one thing and produces data that other components consume.

---

## 15. Cockpit Integration

### Future Widgets (Design Only, No Implementation)

| Widget Name | Data Source | Update Frequency | Purpose |
|-------------|-------------|------------------|---------|
| **Top Missed Opportunity** | MissedOpportunity records sorted by `opportunity_cost` (absolute), filtered to those in OBSERVING or OUTCOME_AVAILABLE state. | Real-time | Shows the most impactful ongoing miss. Answers: "What is the most expensive thing we are currently ignoring?" |
| **Largest Opportunity Cost** | MissedOpportunity records sorted by `opportunity_cost` (absolute), filtered to COMPARED state. | Real-time | Shows the most expensive historical miss. Answers: "What was our worst missed opportunity?" |
| **Most Frequent Block Reason** | Aggregation of `block_reason` across all MissedOpportunity records. | Daily | Shows which guard or reason blocks the most opportunities. Answers: "What is stopping the system from acting?" |
| **Learning Generated Today** | Knowledge items generated from MissedOpportunity records today. | Real-time | Shows what was learned from recent blocks. Answers: "Did we learn anything useful today?" |
| **Criterion Change** | Criterion delta records aggregated over time. | Weekly | Shows how Criterion is evolving based on missed opportunity learning. Answers: "Is the system's judgment improving?" |
| **Guard Effectiveness** | Per-guard breakdown: opportunities blocked, correctness rate, average opportunity cost. | Weekly | Shows which guards are performing well and which need re-evaluation. Answers: "Is this guard doing its job?" |
| **Learning Efficiency** | Knowledge items per 100 missed opportunities over rolling 30-day window. | Weekly | Shows whether the system is extracting signal from noise. Answers: "Are we learning or just collecting data?" |
| **Missed Opportunity Heatmap** | 2D grid: block_reason (rows) × asset_class (columns), colored by aggregate opportunity cost. | Weekly | Shows patterns in who blocks what. Answers: "Are certain guards over-blocking certain assets?" |

### Integration with Terminal Cockpit (IN-007)

The Terminal Cockpit Evolution (IN-007, Implement Now) should include at minimum:

- A `missed` command listing recent missed opportunities with opportunity cost
- A `missed --top` command showing the highest-value current misses
- A `missed --learned` command showing knowledge generated from misses

---

## 16. Validation

### How Will We Know This System Works?

| Success Metric | Definition | Threshold | Time to Measure |
|----------------|------------|-----------|-----------------|
| **Missed Opportunity Capture Rate** | Percentage of blocked signals that are captured as MissedOpportunity records. | >95% within first week | 1 week |
| **Verdict Assignment Rate** | Percentage of captured MissedOpportunities that receive a verdict (not left as UNKNOWN). | >80% within observation window | Per window |
| **Verdict Accuracy** | For opportunities where both a block verdict and a hindsight evaluation exist, the verdict matches the hindsight evaluation. | >70% (baseline — will improve with refinements) | 3 months |
| **Knowledge Yield** | Percentage of MissedOpportunities that produce at least one knowledge item. | >10% (most misses are noise) | 1 month |
| **Criterion Delta Applicability** | Percentage of proposed Criterion deltas that result in measurable improvement. | >50% | 6 months |
| **Time to First Verdict** | Average time from block to verdict assignment. | <24 hours for intraday opportunities | 1 month |
| **False Learning Rate** | Percentage of knowledge items later invalidated by new evidence. | <10% | 6 months |
| **One-Person Maintainability** | Time required to maintain and operate the system per week. | <2 hours | 3 months |

### Validation Methods

| Method | Description | Phase |
|--------|-------------|-------|
| **Unit tests on lifecycle logic** | Verify state machine transitions are correct, immutable fields cannot be modified, verdict assignment follows rules. | During implementation |
| **Integration test: detect → archive** | Create a complete MissedOpportunity and verify it traverses the full lifecycle. | During implementation |
| **Historical replay** | Replay past blocked signals through the system to validate that the capture mechanism works. | During implementation (with historical data) |
| **Outcome simulation** | For a sample of missed opportunities, manually determine the correct verdict and compare with automated verdict. | First month of operation |
| **Periodic calibration** | Review a random sample of knowledge items and verify they are correct and useful. | Monthly |
| **Before/after comparison** | Compare decision quality metrics before and after Criterion deltas from missed opportunity learning are applied. | Quarterly |

---

## 17. Failure Conditions

### How This Design Can Fail

| # | Failure Mode | Description | Risk | Mitigation |
|---|-------------|-------------|------|------------|
| 1 | **Too expensive to maintain** | The MissedOpportunity system adds significant storage, processing, and cognitive overhead. | Medium | Enforce one-person maintainability from day 1. Cap storage. Auto-archive older than 6 months. If maintenance exceeds 2 hours/week, simplify. |
| 2 | **Cannot validate verdicts** | The Outcome Bridge produces unreliable verdicts because counterfactual estimation is too uncertain. | High | Always qualify verdicts as estimated. Use ranges. Mark INCONCLUSIVE when evidence is insufficient. Accept that some misses cannot be validated. |
| 3 | **Creates false learning** | The system generates knowledge from patterns that are random noise. | High | Enforce minimum evidence thresholds (§11). Require replication before knowledge is promoted. |
| 4 | **Duplicates telemetry** | The system stores data that already exists in telemetry or operational logs, creating redundancy without value. | Medium | Define clear boundaries. MissedOpportunity stores pre-decision snapshots (which telemetry does not), not operational metrics. |
| 5 | **Encourages hindsight bias** | Knowing the outcome of a missed opportunity, the system retrospectively adjusts criteria as if the outcome was predictable. | High | The verdict and Criterion delta processes must use only data available before the outcome window. Post-hoc rationalization is explicitly documented as such. |
| 6 | **Learning to be conservative** | The system learns that "doing nothing" is safest and becomes progressively more conservative, reducing all future action. | Medium | Track the ratio of executed vs blocked opportunities over time. If the ratio trends toward zero, investigate. The MissedOpportunity system should not drive the system to inaction — it should make blocks smarter, not more frequent. |
| 7 | **No learning yield** | The system captures thousands of missed opportunities but generates no useful knowledge. | Low-Medium | Monitor Learning Efficiency metric (§8). If <5% after 3 months, the system needs redesign — either the capture criteria are too broad or the knowledge extraction is not finding patterns. |
| 8 | **Attention overload** | Every missed opportunity generates review work, consuming the user's attention. | Medium | The Notification Quality Gate (IN-006) must manage this. MissedOpportunity should generate notifications only for significant findings (high opportunity cost, novel patterns), not for every block. |

---

## 18. Anti-Patterns

### What This Component Must NEVER Become

| # | Anti-Pattern | Why It Must Be Avoided | Guard |
|---|-------------|------------------------|-------|
| 1 | **Logger** | A logger records events and forgets them. The MissedOpportunity System must learn, transform, and feed back into Criterion. If it is only recording blocks without generating knowledge, it is a logger. | Every MissedOpportunity must produce at least one output beyond itself (verdict, knowledge, or criterion delta). If it produces none, it should not be created. |
| 2 | **Dashboard** | A dashboard displays data but does not learn from it. The MissedOpportunity System is not a visualization of missed opportunities — it is a learning engine. Dashboards are outputs (see §15), not the system itself. | The system is measured by learning yield, not by how many opportunities it displays. |
| 3 | **Spreadsheet** | A spreadsheet is a passive container. The MissedOpportunity System must have an active lifecycle, automated outcome observation, and knowledge extraction. If it requires manual data entry for every field, it is a spreadsheet. | All pre-decision fields must be populated automatically from the pipeline. Manual entry is allowed only for post-hoc analysis, never for initial capture. |
| 4 | **Profit calculator** | If the system only computes "how much money did we lose by not trading?" it becomes a regret machine, not a learning system. The opportunity cost is input to learning, not the output. | The system's primary output is knowledge and Criterion delta, not financial PnL. The first value listed in every report should be learning generated, not profit lost. |
| 5 | **Signal archive** | A signal archive stores every signal ever generated. The MissedOpportunity System must be selective — it captures only signals that reached the blocking stage, not every raw signal. | Define the entry threshold clearly: only signals that reached a decision (Council output) and were then blocked qualify. Raw signals that never reached a decision are not MissedOpportunities. |
| 6 | **Blame assignment tool** | The system should not be used to determine which guard or component is "at fault" for misses. The purpose is learning, not attribution of error. | Knowledge and Criterion delta are always constructive. "Guard X needs re-evaluation" is acceptable. "Guard X is bad" is not. |
| 7 | **Notification spammer** | Every missed opportunity must NOT generate a notification. The system learns in the background. Only significant findings rise to the user's attention. | The Notification Quality Gate (IN-006) must be integrated before any user-facing notifications are generated. |

---

## 19. Future Evolution

### Version 2 — Aggregation and Pattern Detection

| Feature | Description |
|---------|-------------|
| **Batch knowledge extraction** | Instead of extracting knowledge per-opportunity, aggregate across similar opportunities and extract patterns. |
| **Guard calibration recommendations** | Automatically suggest guard threshold adjustments based on accumulated evidence. Human-in-the-loop approval. |
| **Hypothesis class profiling** | Build profiles per hypothesis class showing: miss rate, opportunity cost, correctness rate. |
| **Outcome window optimization** | Learn optimal observation windows per asset and hypothesis class based on historical verification accuracy. |
| **Opportunity uniqueness integration** | Incorporate Opportunity Uniqueness Score (IN-002) into opportunity cost estimation. A rare missed opportunity costs more than a common one. |

### Version 3 — Predictive Miss Analysis

| Feature | Description |
|---------|-------------|
| **Block prediction** | Predict which opportunities are likely to be blocked before they enter the guard layer. Enables pre-emptive adjustments. |
| **Opportunity cost prediction** | Estimate opportunity cost at block time (before observation). Compare with actual cost to improve the estimator. |
| **Counterfactual ranking** | Rank missed opportunities by "would have been most valuable." Learn which block reasons cause the most valuable misses. |
| **Criterion delta automation** | Automatically apply low-impact Criterion deltas without human review. High-impact deltas still require approval. |
| **Multi-domain expansion** | Apply the same MissedOpportunity pattern to non-trading domains (content decisions, business opportunities, relationship investments). |

### Version 5 — Autonomous Learning Integration

| Feature | Description |
|---------|-------------|
| **Criterion self-correction** | The system automatically adjusts its own evaluation criteria based on accumulated missed opportunity evidence, without human intervention, within defined safety bounds. |
| **Decision Approval Engine integration** | MissedOpportunity data feeds directly into the Approval Engine's thresholds. Repeated incorrect blocks of signal type X cause the Approval Engine to automatically raise approval priority for type X. |
| **Cross-domain learning** | Lessons from missed trading opportunities inform evaluations in non-trading domains, and vice versa. The MissedOpportunity knowledge base becomes domain-independent. |
| **Opportunity generation feedback** | Knowledge from missed opportunities feeds back into how the system generates new opportunities — not just how it evaluates them. The system learns what kinds of opportunities to look for. |

### Version ∞ — Ten Year Vision

The Missed Opportunity Intelligence System evolves from a component that analyzes blocked signals into the system's primary mechanism for learning from inaction. It becomes as important as the Outcome Comparison pipeline (the system's primary mechanism for learning from action). Together they form the complete learning loop: learn from what you did AND learn from what you did not do. A system that masters both has achieved something rare in decision intelligence: it can evaluate the quality of its choices independently of whether those choices led to action or inaction.

---

## 20. Final Recommendation

### Maturity Assessment

| Aspect | Verdict | Rationale |
|--------|---------|-----------|
| Specification completeness | **MATURE** | All 19 preceding sections define the object, lifecycle, integration, validation, and evolution clearly. No major unknowns at the architectural level. |
| Implementation readiness | **READY** | The design is precise enough that implementation can begin. The lifecycle is unambiguous. The integration points are documented. The anti-patterns are defined. |
| One-person feasibility | **FEASIBLE** | The implementation scope is moderate (single new module, ~500-800 lines of Python, ~200 lines of tests). The system is independent of the operational pipeline. |
| Risk | **LOW** | Additive to the system. Does not modify any existing component. Does not touch execution, capital, or operational databases. Full isolation via separate lifecycle. |

### What Remains Unknown

| Unknown | Impact | Resolution Path |
|---------|--------|-----------------|
| Observation window calibration | High — wrong window sizes produce incorrect verdicts | Start with conservative defaults (24h). Calibrate empirically after 100+ observations. |
| Outcome Bridge accuracy | High — cannot validate counterfactuals | Accept inherent uncertainty. Always qualify as "estimated." Verify manually for a 10% sample. |
| Knowledge extraction effectiveness | Medium — may need tuning | Start with rule-based extraction. Add pattern detection in V2. |
| Storage growth rate | Low — each record is ~2KB. At 1000 opportunities/day = ~2MB/day. | Monitor. Archival policy after 6 months. |

### Recommendation

**This specification is mature enough for implementation.**

The implementation should follow this order:

| Step | Description | Estimated Effort |
|------|-------------|------------------|
| 1 | MissedOpportunity data structure and lifecycle state machine | 1 day |
| 2 | Persistence layer (SQLite table in scientific.db) | 0.5 day |
| 3 | Capture integration with pipeline (read-only, at block point) | 1 day |
| 4 | Outcome Bridge — market data observation and comparison | 2 days |
| 5 | Knowledge extraction (rule-based, V1) | 1 day |
| 6 | Criterion delta tracking (record-keeping only, V1) | 0.5 day |
| 7 | CLI commands for review and querying | 1 day |
| 8 | Tests (unit + integration + historical replay) | 1 day |
| **Total V1** | | **~8 days** |

### Reusability

**This component is highly reusable for future learning systems.**

The design pattern — capture pre-decision state, observe outcome, compare, extract knowledge, update Criterion — applies to any situation where the system evaluates a possibility but does not act. Future learning systems that can reuse this pattern:

- **Signal-to-Decision Audit (IN-005)** — trace every signal through the decision pipeline, using the same pre-decision snapshot mechanism
- **Decision Replay (SB-006)** — replay past decisions using the same comparison mechanism
- **Black Swan Archive (SB-013)** — capture unexpected events using the same observation mechanism
- **Missed Evidence Detection** — future system that detects when evidence was available but not incorporated into a decision

The core loop (Capture → Observe → Compare → Learn → Update Criterion) is the fundamental pattern of the entire Scientific Learning Layer. The Missed Opportunity System is the first implementation of this pattern.

---
