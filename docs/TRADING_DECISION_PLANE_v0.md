# PILOT capital decision plane

No broker or real capital is connected. No Edge, Regime or Mechanics validation;
no policy winner. This document records contract readiness, not deployment.

## Thesis

Immutable thesis binds candidate and causal WorldState, explicit support and
contradiction references, premises, assumptions, invalidation and configuration.
Only evidence in that world may support or contradict it. An overlapping support/
contradiction reference is preserved as CONFLICTING. NONE_DECLARED is not proof
that contradictions do not exist. Thesis is a hypothesis, never validated Edge.

## Forecast semantics

Scores, probabilities, expected returns, distributions and directions are distinct
types with explicit units. Missing values stay None. No accredited calibration or
expected-return forecasting adapter exists in v0: CALIBRATED and numeric expected
return are blocked, rather than accepting a caller's unsupported validation claim.
Uncalibrated probability/distribution may be represented but never exposed as
economic_probability. Scenario distributions are hypotheses, not observed outcomes.

## Global priority

Ranking policy is create-once registered before the WorldState cutoff. It declares
lexicographic criteria, UNKNOWN-last behavior and candidate-ID tie-break. Ranking
covers the full radar candidate set with component vectors and explicit exclusions.
Output is PILOT_PRIORITY, not economic utility; no forecast numeric value enters
the ordering. Missing contradictions mean unknown, not proof of no contradiction.

## Shadow portfolio and factual overlap

Equity and positions are SHADOW_CONFIG, never broker observations. Amounts carry
explicit units without conversion; unknown risk stays None. ExposureGraph counts
instrument/underlying/direction, shared legs, venue/product and family overlap.
These are factual overlaps, not correlations. No validated relationship evidence
adapter exists here, so correlation remains UNKNOWN rather than zero.

## Independent risk

RiskPolicy is versioned by content identity and explicitly PILOT_SYNTHETIC_LIMITS.
All core limits are explicit; None causes DEFER. Kill switch TRUE causes HALT,
unknown causes DEFER. Position/aggregate budgets, count concentration, freshness,
direction and book observability are checked independently of ranking. Required
drawdown/daily-loss/event/volatility/cost/correlation controls are represented but
not observed by this data plane: requesting them causes DEFER, never assumed zero.
Authorization can be recomputed and verified; a forged cap is rejected. Risk policy
registration time is contractual until frozen by the runner configuration.

## Joint allocation

PILOT_ALLOCATOR uses frozen priority order, never Kelly or expected returns. It
verifies every authorization and exact candidate population, then reauthorizes
each proposed allocation against positions already selected in that plan. HALT
anywhere halts the plan; DEFER/REJECT allocate zero. Cash is valid. Unknown budget
leaves unallocated budget unknown, not zero. Shared-instrument exclusion is an
explicit policy switch. Every zero allocation retains a reason.
