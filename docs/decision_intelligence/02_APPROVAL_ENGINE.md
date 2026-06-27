# Approval Engine

## O.M.A.-C.O.R.E. Decision Intelligence — Component 2

*Version 1.0 — June 2026*

---

## 1. Purpose

The Approval Engine receives the multi-dimensional confidence vector from the Decision Confidence Engine and decides what to do:

| Decision | Meaning |
|---|---|
| EXECUTE | Proceed with the action under the recommended resource allocation |
| WAIT | Do not execute now, but retain the hypothesis for re-evaluation |
| REJECT | The hypothesis is not viable under current conditions; discard or archive |
| NEED MORE EVIDENCE | The hypothesis is promising but underdetermined; invest in evidence acquisition first |

The Approval Engine **never predicts markets**. It evaluates readiness to act. It does not generate hypotheses, assess market direction, or produce trading signals. It is a gating function — either the system is ready, or it is not.

---

## 2. Architectural Position

```
Decision Confidence Engine
        ↓ (Confidence Vector C)
Approval Engine
        ↓ (Decision: EXECUTE | WAIT | REJECT | NEED_MORE_EVIDENCE)
   ┌────┴────┐
   ↓         ↓
Execute   Operational Flow
 (via     (collectors, agents,
 Execution  council, paper trading,
 Pipeline)  runtime — untouched by DI)
```

The Approval Engine is the **last decision gate before operational execution** is triggered (or before the decision is surfaced to a human for authorization). It has no runtime access, no direct execution capability, and no authority to modify operational state. It emits a decision record that the Operational Flow interprets at its own discretion.

---

## 3. Core Decision Architecture

### 3.1 Decision Rule

For each incoming confidence vector `C`, the Approval Engine applies a policy-defined decision function:

```
Decision(C) = {
    EXECUTE            if C.readiness ≥ τ_readiness AND
                            C.knowledge ≥ τ_knowledge AND
                            C.maturity ≥ τ_maturity AND
                            C.stability ≥ τ_stability AND
                            C.uncertainty < τ_uncertainty AND
                            no veto conditions active

    NEED_MORE_EVIDENCE if C.readiness ≥ τ_readiness AND
                            C.knowledge < τ_knowledge AND
                            C.maturity ≥ τ_maturity AND
                            evidence_gain_possible(C)

    WAIT               if C.readiness ≥ τ_readiness AND
                            (C.knowledge ≥ τ_knowledge OR C.maturity ≥ τ_maturity) AND
                            not all veto conditions met AND
                            C.uncertainty < τ_uncertainty_critical

    REJECT             if C.readiness < τ_readiness_min OR
                            any hard veto condition active OR
                            C.uncertainty ≥ τ_uncertainty_critical OR
                            resource depletion C.overall < τ_fatal
}
```

All thresholds `τ_*` are policy parameters (see Document 4 — Decision Policy). They are not static — they evolve as criterion matures and as the system's autonomy level changes.

### 3.2 Decision Classes

The Approval Engine maintains separate decision classes because different action types have different risk profiles:

| Class | Examples | Default Threshold |
|---|---|---|
| **Entry** | Open new position, deploy capital | Highest evidence requirement |
| **Exit** | Close position, take profit, stop loss | Lowest evidence requirement (time-sensitive) |
| **Sizing** | Increase, decrease, split position | Moderate evidence requirement |
| **Skip** | Do nothing, maintain current state | Default when uncertainty exceeds entry threshold |
| **Evidence acquisition** | Request more data, run analysis | Low threshold (low resource cost) |
| **Criterion change** | Apply a criterion delta | Maximum threshold (changes the system itself) |
| **Resource reallocation** | Rebalance capital between strategies | Moderate threshold |

---

## 4. Approval Rules

### 4.1 Two-Tier Approval

**Tier 1 — Automatic Approval** (low resource cost, low risk):
- Evidence acquisition requests
- Skip / do-nothing decisions
- Exit decisions (time-bounded)
- Criterion read-only access

**Tier 2 — Gated Approval** (requires minimum confidence):
- Entry decisions
- Sizing changes
- Resource reallocation
- Criterion delta application (only after human review until Stage 8+ autonomy)

### 4.2 Rule Priority

Rules are evaluated in order. The first matching rule determines the decision:

1. Emergency stop / veto conditions → REJECT (immediate, regardless of confidence)
2. Resource depletion below critical → REJECT
3. Black swan / unknown situation detected → WAIT + escalate
4. Criterion delta application requested → require human review (until autonomy maturity)
5. Standard decision rules (above) → EXECUTE | WAIT | NEED_MORE_EVIDENCE | REJECT

---

## 5. Evidence Thresholds

Evidence thresholds map to the knowledge quality dimension `D_KQ` and vary by decision class:

| Class | Minimum Evidence | Minimum Knowledge Status | Minimum Replication |
|---|---|---|---|
| Entry | 3 supporting evidence records | PROVISIONAL | 1 |
| Exit | 1 supporting evidence | EXTRACTED | 0 |
| Sizing increase | 2 supporting evidence | PROVISIONAL | 1 |
| Sizing decrease | 1 supporting evidence | EXTRACTED | 0 |
| Criterion delta | 5 supporting evidence | VALIDATED | 2 |

These are minimums. The Confidence Engine's `D_KQ` sub-score will be higher if evidence significantly exceeds these thresholds.

---

## 6. Escalation

When the engine cannot decide (tie, conflicting signals, or uncertainty within a borderline band), it escalates to the next level:

| Level | Authority | Action |
|---|---|---|
| L0 — Automatic | Approval Engine | Execute within policy bounds |
| L1 — Logged | Approval Engine + audit | Execute but record detailed rationale for later review |
| L2 — Warning | Log + human notification | Flag to operator; auto-execute if no response within timeout |
| L3 — Escalated | Human required | Pause until human reviews and authorizes or rejects |
| L4 — Emergency | Human only | Full stop; no automatic action possible |

Escalation is triggered by:
- Confidence vector in a borderline region (all sub-scores between 0.4 and 0.6)
- Conflicting dimensions (e.g., high readiness but near-zero knowledge)
- First decision of a new decision class
- After any system-level fault or restart
- When uncertainty dimension crosses the "unknown unknowns" threshold

---

## 7. Human Override

A human operator can:

- **Override to EXECUTE**: Force execution even if confidence is below minimum. This is logged and flagged as a confidence calibration event for post-hoc analysis.
- **Override to REJECT**: Block execution even if confidence is above threshold. This is logged and may indicate a criterion gap.
- **Override to WAIT**: Postpone until a specific condition or timestamp.
- **Override to NEED_MORE_EVIDENCE**: Require specific evidence before re-evaluation.

Human override is itself a decision that feeds back into the calibration loop. Systematic patterns of human override (e.g., "human always overrides to REJECT when confidence is borderline") indicate a policy calibration problem that should trigger a criterion delta proposal.

**Critical invariant**: Human override does not bypass the decision policy. It is a **policy exception** that is:
1. Always logged with full context
2. Always time-bounded (expires automatically)
3. Tracked as a calibration data point for future engine improvement

---

## 8. Emergency Stop

An emergency stop overrides all approval rules and immediately rejects all pending decisions. It is triggered by:

- Capital drawdown exceeding the kill-switch threshold
- Crash Detector entering PANIC or EMERGENCY mode
- System health monitor reporting CRITICAL on any component
- Manual emergency signal from human operator
- Loss of data source connectivity exceeding recovery timeout

During emergency stop the Approval Engine:
1. Rejects all pending EXECUTE and NEED_MORE_EVIDENCE decisions
2. Automatically approves EXIT decisions for all open positions (time-critical)
3. Enters a WAIT-only state: only WAIT and REJECT decisions are emitted
4. Logs the emergency context and timestamps the start and end

Emergency stop is released when:
- The triggering condition clears
- A minimum cooldown period has elapsed (policy parameter, suggested minimum 1 full cycle)
- The system passes a health check (all components nominal)

---

## 9. Risk Veto

The Risk dimension `D_R` carries veto authority independent of all other dimensions:

- If `D_R < 0.2` (extreme risk): **Automatic veto** on all EXECUTE decisions for the affected decision class
- If `0.2 ≤ D_R < 0.4` (high risk): EXECUTE decisions require two-tier approval (must pass both Tier 1 and Tier 2 thresholds)
- If `D_R ≥ 0.4`: Standard rules apply

Risk veto does not block EXIT decisions. It does not block evidence acquisition. It blocks resource commitment in high-risk environments.

---

## 10. Missing Data Handling

| Scenario | Approval Engine Behavior |
|---|---|
| One input dimension unavailable | Use last known value with decay penalty; flag as degraded in decision log |
| Majority of dimensions unavailable | Default to REJECT (cannot estimate confidence without inputs) |
| Data source returns unexpected format | Log error; mark all dimensions dependent on that source as unavailable |
| Timestamps indicate stale data | Apply freshness decay to affected dimensions |
| No historical replay data exists | Set D_HC = 0.0 (no calibration); default uncertainty to maximum |
| Knowledge base empty | Set D_KQ = 0.0; require at minimum EXTRACTED knowledge for EXECUTE |

---

## 11. Unknown Situations

An "unknown situation" is detected when:

- The hypothesis domain has no matching knowledge items (zero overlap)
- The current market regime has no historical analog in replay data
- Multiple input dimensions return contradictory values (variance across dimensions > 0.7)
- The system has never made a decision in this decision class

In an unknown situation, the Approval Engine **defaults to WAIT + escalate to L3**. The system may not act in completely unknown territory without human authorization. This is a hard safety constraint.

---

## 12. Black Swan Detection

Black swans are not predictable by definition. The Approval Engine cannot detect them in advance. However, it can detect conditions consistent with a black swan event:

- Multi-standard-deviation moves across uncorrelated assets simultaneously
- Data sources reporting mutually exclusive states
- Execution layer reporting slippage > 10x historical average
- Multiple guard systems triggering simultaneously (Crash Detector + Knife Detector + Gap Risk + Kill Switch)

When black swan conditions are detected, the Approval Engine:
1. Immediately escalates to EMERGENCY mode
2. Rejects all non-EXIT decisions
3. Only permits EXIT and WAIT decisions
4. Logs the event for post-hoc analysis and criterion delta proposal

---

## 13. Criterion State Dependence

### 13.1 Low Criterion State

When criterion maturity `D_CM < 0.3`:

- All thresholds are raised by 30% (the system needs more evidence to compensate for immature criterion)
- Criterion delta proposals are automatically prioritized for human review
- Maximum decision class diversity is limited to 2 classes concurrently
- Automatic approval is restricted to Tier 1 only (evidence acquisition, exit)
- All entry decisions require escalation to L2 at minimum

### 13.2 High Criterion State

When criterion maturity `D_CM ≥ 0.7`:

- Thresholds return to standard levels
- Criterion delta proposals may enter an expedited review queue
- Automatic approval can include Tier 2 decisions
- Sizing decisions may be automated within confidence bounds
- The system may operate at L1 (logged) instead of L2+ for routine decisions

### 13.3 Criterion Degradation

If criterion maturity **decreases** (deltas are rejected, knowledge is invalidated, or calibration worsens), the Approval Engine does not instantly expand authority. Degradation is treated symmetrically with growth — the system must **re-prove** its readiness at each threshold level.

---

## 14. Relationship with Operational Execution

The Approval Engine and Operational Execution are **separate concerns**:

| Concern | Decision Intelligence | Operational Execution |
|---|---|---|
| What to do | EXECUTE / WAIT / REJECT | Specific action (buy 0.1 BTC at market) |
| When to do it | Now / Later / Never | Immediate execution or scheduled |
| Why to do it | Confidence vector + policy | Signal + risk + sizing model |
| Who decides | Approval Engine | PaperTradingEngine / ExecutionEngine |
| Resource allocation | Approval boundary | Actual deployment |

The Approval Engine says "yes, this is worth doing." The Operational Flow says "here is how to do it." They never merge.

---

## 15. Relationship with Paper Trading

Paper trading is the **primary validation mechanism** for the Approval Engine:

1. Paper trading generates hypotheses and outcomes without consuming real capital
2. The Approval Engine evaluates paper trading decisions identically to real decisions
3. Confidence calibration from paper trading is used to set thresholds for real decisions
4. A minimum number of paper trading cycles must complete before the Approval Engine is trusted for any real-capital decision

Paper trading does not bypass the Approval Engine. Paper trading decisions must also pass through approval — but with lower resource-depletion penalties (capital usage is simulated, not real).

---

## 16. Relationship with Future Autonomy

The Approval Engine is designed to support increasing autonomy levels without structural changes:

- **Stage 0 (Human-only)**: All decisions escalate to L3; Approval Engine operates in observation mode only
- **Stage 1 (Advisory)**: Approval Engine recommends but does not decide; human always confirms
- **Stage 2 (Supervised automatic)**: Approval Engine decides; human can override within timeout
- **Stage 3 (Conditional autonomy)**: Approval Engine decides for Tier 1; human for Tier 2
- **Stage 4 (High autonomy)**: Approval Engine decides for Tier 1 and most Tier 2; human for criterion changes
- **Stage 5 (Full autonomy)**: Approval Engine decides all classes; human monitors; emergency stop always available

Each autonomy stage maps to a threshold multiplier set in the Decision Policy. The engine itself does not change — only the policy parameters change.

---

## 17. Open Design Questions

1. Should the Approval Engine maintain a queue of WAIT decisions with re-evaluation triggers (time-based, event-based)? **Current position**: Yes — a re-evaluation scheduler is necessary but out of scope for the engine itself. Design a separate Re-evaluation Scheduler component.

2. Should the engine distinguish between "reject permanently" and "reject for this cycle"? **Current position**: Yes — REJECT_Permanent vs REJECT_Temporary. Permanent requires explicit human un-rejection. Temporary auto-re-evaluates next cycle.

3. Should human override of a single decision trigger a full policy review? **Current position**: Only if the override pattern exceeds 3 standard deviations from the historical override rate. Otherwise, it is a single calibration data point.

4. Who decides whether to implement the Approval Engine's decision — the engine itself, or a downstream component? **Current position**: The Approval Engine produces a decision record. An Execution Gate (separate, simple component) reads the decision record and either passes execution to the operational pipeline or blocks it. The Approval Engine does not execute — it decides.
