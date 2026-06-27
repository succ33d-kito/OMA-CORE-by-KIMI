# Decision Policy

## O.M.A.-C.O.R.E. Decision Intelligence — Component 4

*Version 1.0 — June 2026*

---

## 1. Purpose

The Decision Policy is the constitution governing all decisions in the Decision Intelligence Layer. It defines:

- The principles that no decision may violate
- The hard invariants that cannot be overridden
- The forbidden behaviors that the system must never exhibit
- The evidence requirements that must be met before action
- The autonomy ladder that governs human involvement
- The ethics framework for resource trade-offs
- The conditions under which the system must refuse action

This policy is **machine-readable by design**. Every rule maps to a policy parameter that the Confidence Engine, Approval Engine, and Scarce Resources Model consume. The policy is not advisory — it is enforced.

---

## 2. Decision Principles

### 2.1 Evidence Primacy

> No decision shall be executed without a traceable chain from observation to hypothesis to evidence to confidence estimate.

**Implications**:
- Every EXECUTE decision must reference a specific hypothesis
- Every hypothesis must reference evidence (supporting or contradicting)
- Every confidence estimate must be explainable as a function of evidence quality
- Decisions from intuition (evidence-free) are prohibited by architectural constraint

### 2.2 Learning Priority

> When a choice exists between a resource-generating action and a learning-generating action with comparable resource cost, the learning-generating action is preferred.

**Implications**:
- A hypothesis that the system has not tested before is preferred over a repeat of a known outcome, all else equal
- Paper trading a novel hypothesis is preferred over paper trading a confirmed strategy
- Evidence collection is preferred over execution when confidence is borderline
- This principle is subordinate to Safety Priority (Section 2.4) — no learning at catastrophic cost

### 2.3 Resource Preservation

> No single decision may consume more than a policy-defined fraction of any critical resource.

**Implications**:
- Position size limits are hard caps, not soft suggestions
- Attention has a maximum concurrent hypothesis count
- The emergency stop must be triggerable before resource depletion reaches critical
- Resource consumption is checked before every decision, not after

### 2.4 Safety Priority

> No architectural principle overrides safety. Safety means: the system must survive to make future decisions.

**Implications**:
- Capital loss that threatens continued operation is prohibited
- Reputation loss that destroys stakeholder trust is prohibited (as far as controllable)
- Knowledge corruption (validating false knowledge) is prohibited
- The kill switch is the highest-priority component in the system
- All other principles yield to safety when conflict is detected

### 2.5 Criterion Priority

> Decisions that generate criterion are preferred over decisions that only generate resources.

**Implications**:
- A trade that produces both profit and a testable hypothesis is preferred over a trade with equal expected profit but no learning
- A decision that generates a criterion delta proposal is valued above one that does not
- The system should prefer novel market conditions over repeated ones (learning opportunity)
- This principle is subordinate to Safety Priority

### 2.6 Transparency

> Every decision must be explainable in terms the human operator can understand, given reasonable effort.

**Implications**:
- The Confidence Engine must expose sub-dimension scores, not just the overall vector
- The Approval Engine must log the rule chain that produced the decision
- All overrides must be logged with full context
- No opaque "neural network style" black boxes in the decision layer
- Explanation must be computable in under one second for any past decision

### 2.7 One-Person Maintainability

> The Decision Intelligence Layer must remain understandable and modifiable by a single competent engineer working alone.

**Implications**:
- No machine learning models that require ongoing training data management
- No distributed systems that require cluster maintenance
- No dependencies on external ML platforms or APIs for core decision logic
- All policy parameters must be human-readable and human-settable
- The total line count of the implemented Decision Intelligence Layer should not exceed 3000 lines of Python (excluding tests and documentation)

---

## 3. Hard Invariants

These invariants are **enforced at the architectural level**. They cannot be changed by any policy parameter update or criterion delta. Changing an invariant requires an architecture review and explicit human authorization.

| # | Invariant | Rationale |
|---|---|---|
| 1 | No decision may execute without a confidence estimate | Prevents blind action |
| 2 | The emergency stop must always be triggerable, including by human | Self-preservation |
| 3 | No criterion delta may be auto-applied to live operational parameters | Human review gate (until Autonomy Stage 4+) |
| 4 | The Approval Engine must never generate hypotheses, signals, or predictions | Separation of concerns |
| 5 | The Decision Intelligence Layer must not have write access to any operational database | Isolation safety |
| 6 | Risk dimension `D_R` carries independent veto authority | Risk cannot be overruled by other dimensions |
| 7 | Human override must always be possible for any decision class | Ultimate accountability |
| 8 | All decisions must be logged with full input vector and rule trace | Auditability |
| 9 | The system must refuse action in completely unknown situations (no matching knowledge) | Unknown unknowns principle |
| 10 | Resource consumption must be estimated before the decision, not after | Proactive protection |

---

## 4. Forbidden Behaviors

The following behaviors are **never permitted** under any circumstances:

| Behavior | Why Forbidden |
|---|---|
| **Predicting prices** | The system evaluates readiness, not market direction. Price prediction is a different (inferior) paradigm. |
| **Optimizing for short-term profit at the expense of long-term learning** | Violates Learning Priority and Criterion Priority. Destroys the system's raison d'être. |
| **Bypassing the Approval Engine** | All resource-consuming decisions must pass through approval. No side channels. |
| **Modifying policy parameters without logging** | Policy changes without audit trail destroy explainability and trust. |
| **Overriding the risk veto without human authorization** | Risk is independent for a reason. |
| **Operating without a minimum knowledge base** | Starting from zero knowledge may be acceptable only during initialization. The system must not make resource-consuming decisions without at least EXTRACTED knowledge in the relevant domain. |
| **Continuous high-frequency execution** | The system is a decision intelligence system, not a market maker. High-frequency execution consumes execution bandwidth and attention without generating commensurate learning. |
| **Ignoring contradictory evidence** | All evidence must be considered — supporting and contradictory. Cherry-picking evidence violates Evidence Primacy. |
| **Deleting decision logs** | Logs are append-only. No deletion. No modification after creation. (Exception: privacy regulations may require deletion, but this must be logged separately.) |

---

## 5. Required Evidence

### 5.1 Minimum Evidence Pre-Conditions

Before any decision can proceed to the Approval Engine with a non-REJECT outcome, the following evidence conditions must be met:

| Condition | Requirement | Applies To |
|---|---|---|
| Hypothesis exists | A formal hypothesis object must exist in the Learning Core | All decisions |
| Minimum evidence count | ≥1 evidence record for Tier 1, ≥3 for Tier 2 | Entry, Sizing, Criterion |
| Evidence freshness | Most recent evidence within policy-defined freshness window | All decisions |
| Knowledge presence | At least one knowledge item with ≥PROVISIONAL status in the relevant domain | Entry, Criterion |
| No contradictory veto | If contradictory evidence > supporting evidence and no explanation logged | Entry, Sizing increase |

### 5.2 Decision-Specific Requirements

| Decision Class | Evidence Requirement | Knowledge Requirement |
|---|---|---|
| Entry | 3+ records, 2 from independent sources | 1+ PROVISIONAL knowledge item in domain |
| Exit (take profit) | 1+ supporting evidence | Knowledge recommended but not required |
| Exit (stop loss) | 0 — automatic, time-critical | N/A |
| Exit (manual override) | As specified by human | N/A |
| Sizing increase | 2+ supporting evidence, 1 indicating favorable risk/reward | 1+ PROVISIONAL knowledge item |
| Sizing decrease | 1+ supporting evidence indicating elevated risk | Knowledge recommended |
| Skip / do nothing | 0 — default state | N/A |
| Evidence acquisition | 0 — the request itself generates evidence | N/A |
| Criterion delta proposal | N/A — proposals are always allowed | N/A (but reviewed with evidence) |
| Criterion delta apply | 5+ evidence records, 2+ independent replications | 1+ VALIDATED knowledge item |

---

## 6. Human Review Requirements

### 6.1 Decisions Requiring Mandatory Human Review

The following decisions cannot proceed without explicit human authorization, regardless of confidence:

| Decision | Reason |
|---|---|
| First real-capital deployment | No historical calibration for real-capital decisions |
| Entering a new decision class (first time) | No experience in this class |
| Criterion delta application | Changes the system's judgment criteria |
| Policy parameter modification | Changes the decision constitution |
| Emergency stop override | Cannot override the override safeguard |
| Operating in a new asset class | No calibration for this market structure |
| After any critical system failure restart | Post-failure state is untrusted |

### 6.2 Human Review Cadence

| Review Type | Frequency | Scope |
|---|---|---|
| Daily summary | Every cycle | All decisions, overrides, escalations |
| Calibration review | Weekly | Confidence calibration trends, bias detection |
| Policy review | Monthly | Threshold appropriateness, forbidden behavior audit |
| Architecture review | Quarterly | Invariant validity, separation of concerns check |

---

## 7. Autonomy Ladder

The autonomy ladder defines how much authority the Decision Intelligence Layer has, independent of the underlying policy:

| Stage | Name | Entry Decisions | Exit Decisions | Sizing | Criterion Deltas | Evidence Acq. | Escalation Level |
|---|---|---|---|---|---|---|---|
| 0 | Human-only | Human | Auto | Human | Human | Auto | L3 all non-auto |
| 1 | Advisory | Recommend | Auto | Recommend | Human | Auto | L3 entry, L2 sizing |
| 2 | Supervised | Auto with timeout | Auto | Auto with timeout | Human | Auto | L1 most, L2 borderline |
| 3 | Conditional | Auto (τ+30%) | Auto | Auto (τ+20%) | Human review | Auto | L1 routine, L3 criterion |
| 4 | High | Auto (τ standard) | Auto | Auto (τ standard) | Auto with human veto | Auto | L1 all non-criterion |
| 5 | Full | Auto | Auto | Auto | Auto | Auto | L1 all, L2 monitor only |

**τ standard**: The threshold values defined in the current policy.
**τ+X%**: Elevated thresholds (more evidence required) at lower autonomy.

Transition between autonomy stages is governed by the validation gates defined in Document 5 (Roadmap). Autonomy is granted based on demonstrated capability, not time passed.

---

## 8. Decision Ethics

### 8.1 Ethical Framework

The system operates under a **consequentialist framework bounded by deontological constraints**:

- **Consequentialist**: Decisions are evaluated by their expected impact on scarce resource generation across all dimensions
- **Deontological constraints**: Certain actions are forbidden regardless of consequences (see Section 4 — Forbidden Behaviors)

### 8.2 Specific Principles

- **Fairness**: The system must not exploit structural market advantages that harm other participants illegitimately (front-running, manipulation, spoofing)
- **Responsibility**: The human operator bears ultimate responsibility for system behavior. The system must enable, not obstruct, responsible oversight
- **Honesty**: The system must accurately represent its confidence, uncertainty, and capability. No exaggeration, no false precision
- **Learning precedence**: When in doubt between two ethically permissible actions, prefer the one that produces more learning
- **Non-destruction**: Never take an action that, even if successful, destroys a resource with regeneration time exceeding the system's expected lifespan

### 8.3 Resource Trade-off Ethics

When resources must be traded off against each other:

1. **Irrecoverable resources** (Trust, Reputation, Information Advantage) take precedence over recoverable ones (Capital, Compute)
2. **Strategic resources** (Knowledge, Criterion, Autonomy) take precedence over tactical ones (Liquidity, Execution Bandwidth)
3. **Long-term generation** takes precedence over short-term extraction, unless the short-term extraction is necessary to prevent catastrophic loss
4. **Human welfare** takes precedence over system resources — the system must never take actions that harm humans, even indirectly and even if profitable

---

## 9. When to Refuse Action

The system must refuse action in the following situations:

| Situation | Refusal Type | Notes |
|---|---|---|
| Unknown domain (zero knowledge match) | REJECT + escalate L3 | Cannot act in completely unknown territory |
| Resource depletion below critical threshold | REJECT | Self-preservation |
| Risk dimension below 0.2 | REJECT (risk veto) | Independent veto |
| Emergency stop active | REJECT all non-exit | Overrides all other logic |
| Multiple vetoes triggered | REJECT | Any single veto is sufficient |
| Policy parameter outside valid range | REJECT | Configuration integrity failure |
| Data source connectivity lost for critical inputs | WAIT | Cannot evaluate without data |
| Contradictory evidence exceeds supporting (3:1) without explanation | WAIT + escalate | Evidence conflict unresolved |
| Hypothesis has not been re-evaluated after a regime change | WAIT | Stale hypothesis in changed environment |

---

## 10. When Uncertainty Wins

Uncertainty is not always resolvable. The following conditions indicate that uncertainty should "win" — the system should prefer inaction over action:

1. **Uncertainty dimension `D_U > 0.8`**: The system does not know enough to act. Additional evidence is required before any non-reject decision is possible.

2. **Outcome dispersion > 2× expected return**: If the range of possible outcomes exceeds twice the expected value, the uncertainty risk is unacceptable. This is a direct application of the principle that "first, do no harm."

3. **Multiple contradictory signals from independent knowledge domains**: If two validated knowledge items from independent domains predict opposite outcomes, the system has insufficient meta-knowledge to resolve the conflict. Uncertainty wins.

4. **No historical analog**: If the current situation has zero matches in the replay database (even after relaxation of matching criteria), the system is in unknown territory. Inaction is the only safe default.

5. **Calibration error > 0.25**: If the system's past confidence estimates were unreliable by more than 0.25 Brier score, the system cannot trust its own confidence. Inaction until calibration improves.

---

## 11. When Inaction Is Correct

Specific scenarios where doing nothing is the correct decision, even when confidence is sufficient for action:

1. **Opportunity cost exceeds expected gain**: If committing to this decision forecloses a better opportunity within the same resource budget, inaction (on this decision) is correct.

2. **Capital is better deployed elsewhere**: Even a good trade is not worth executing if another available trade has significantly higher expected resource generation.

3. **Attention budget is fully consumed**: Adding a new hypothesis when attention is at maximum degrades all existing hypotheses. Inaction on new entry preserves attention for existing commitments.

4. **System is in learning mode**: During dedicated learning cycles (paper trading, replay analysis), the system may choose inaction on live decisions to maximize learning throughput.

5. **Regime transition detected**: During a detected transition between market regimes, all existing hypotheses are suspect. Inaction until the regime stabilizes is the conservative but correct approach.

6. **After a significant loss**: The system must cool down after a loss exceeding a policy-defined threshold. Inaction allows recalibration and prevents loss-chasing behavior.

---

## 12. Policy Parameter Schema

Every policy parameter has a defined schema:

```python
@dataclass
class PolicyParameter:
    key: str                    # Unique identifier, e.g., "threshold.entry.readiness"
    value: float | int | str   # Current value
    min_value: float | int     # Absolute minimum (enforced)
    max_value: float | int     # Absolute maximum (enforced)
    autonomy_min: int          # Minimum autonomy stage for this parameter
    description: str           # Human-readable explanation
    last_modified: str         # ISO timestamp
    modified_by: str           # "human" or "criterion_delta:<id>"
```

Policy parameters are stored in the Scientific Store alongside criteria. They are versioned and track their modification history.

---

## 13. Open Design Questions

1. Should policy parameters be allowed to evolve through criterion deltas, or should they always require human modification? **Current position**: Criterion deltas can propose policy parameter changes, but the changes must be explicitly approved by human review. The policy is the system's constitution — it should change with deliberation.

2. How should policy conflicts be resolved (e.g., Learning Priority vs. Resource Preservation in a resource-scarce learning opportunity)? **Current position**: Safety Priority > Resource Preservation > Learning Priority > Criterion Priority > Evidence Primacy > Transparency > One-Person Maintainability. This explicit ordering must be maintained.

3. Should the policy be allowed to contradict itself? **Current position**: No. Policy rules must be checked for contradiction at load time and after any modification. Contradictory policy is a configuration error that must prevent operation until resolved.

4. How frequently should policy parameters be reviewed? **Current position**: Weekly automatic review (calibration trends), monthly human review (threshold appropriateness). Policy parameters that have not changed in 6+ months should be evaluated for relevance.
