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

## Frozen shadow decision

ShadowCapitalDecision binds the exact world, radar population, theses, forecasts,
ranking evidence IDs, portfolio, risk authorizations and verified allocation.
All availability precedes decision availability. Replacing a thesis after ranking
fails; new configuration changes identity. No order, fill or outcome fields exist.
WOULD_ALLOCATE is a shadow authorization result, never a profitable-trade claim.

## Reference shadow runner

`shadow_runner.freeze_shadow_config` binds radar, ranking, risk, allocation, capital,
mask and fixed REFERENCE_NON_VALIDATED thesis/UNKNOWN_DIRECTION forecast producers.
Parameters are persisted before freeze time. `run_shadow_once` accepts only source
captures starting after registration, generates internal decision timestamps and
persists the complete chain without HTTP or broker calls. Exact replay is idempotent;
incomplete or corrupted runs stop. The reference producer does not invent direction,
so risk defers rather than manufacturing allocation.

All four frozen masks are supported. Hidden market fields are removed from the
WorldState projection; comparative radar statistics use only visible members.
Nonvisible markets are reported NOT_VISIBLE rather than emitted as quality
candidates. Raw receipt commitments remain shared provenance, not a filesystem
access-control boundary. No mask performance comparison is performed.

RUNNER_CODE_READY / LIVE_RUNTIME_UNVERIFIED. No prospective shadow decision has
been created from real data in this window; all integration runs use fixtures.

## Focused adversarial review

Material guards added: ranking order must match its registered policy and vectors;
final shadow construction recomputes vectors from the actual chain; joint allocation
cannot mix risk policies; finalization rechecks positive allocations for freshness
and rejects expired theses; zero shadow equity cannot authorize risk. Regression
tests cover changed ranking/components, mixed policies, stale final decisions and
zero capital. Other tested boundaries retain unknown calibration/correlation/risk,
cost controls defer when required, immutable decisions and pre-capture mask freeze.
