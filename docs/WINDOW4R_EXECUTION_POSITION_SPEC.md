# Window #4R — Execution and Position contract

Baseline: `029c4d1f6f7473b6895da93ec7159ddd600de491`.
This is a new implementation, not recovery of the lost Window #4 tip or history.
Each stage must pass focal tests, compilation and diff checks, then be committed
and pushed before the next stage starts. Publication failure stops the window.

## Target chain

ShadowCapitalDecision → ExecutionPlan → OrderIntent → ExecutionQualityGate →
ExecutionEstimate → PositionState → ThesisLifecycle → ExitIntent → Reallocation
→ Attribution → opt-in shadow execution intent runner.

The runner evaluates quality before issuing an intent. These are separate
contracts, not proof that an order was submitted or executed.

## Identity, causality and authority

Objects are immutable and use deterministic content commitments. Identity binds
the exact upstream objects, mode, role, timestamps, configuration and evidence.
Reconstruct and validate upstream decisions before accepting their commitments;
a caller-supplied hash alone is insufficient. Preserve PILOT role and explicit
SHADOW/PAPER modes. LIVE is unsupported. Evidence availability must not exceed
the assessment time. Later evidence cannot rewrite an earlier decision.

Reuse finalized ShadowCapitalDecision, risk authorization, allocation, ranking
and WorldState contracts. Risk remains authoritative. Ranking is PILOT priority,
not expected economic utility. Never import legacy paper trading or slippage
engines as factual execution evidence.

## Stage contracts

2. ExecutionPlan binds a validated finalized decision and allocation. It makes
   no broker call. Missing factual conversion from risk units to notional is
   NO_ORDER, not a numerical default. Unsupported multi-leg execution is
   NO_ORDER. A supported single-leg notional still requires explicit executable
   quantity/price semantics before an actionable order intent can exist.
3. OrderIntent binds a valid plan, side, instrument, venue, product, mode and
   explicit quantity units and execution parameters. Missing required parameters
   prevent actionable intent. It is neither acknowledgement nor fill.
4. ExecutionQualityGate returns PASS, DEFER or REJECT using causal evidence and
   explicit policy. Unknown required evidence defers. No future quotes or outcomes.
5. ExecutionEstimate is separate from observation. Reference quote, spread,
   slippage, fees, funding cashflow, latency and depth remain independently
   nullable with explicit units and provenance. Funding rate is not cashflow;
   configured zero cannot replace unknown factual evidence.
6. PositionState binds instrument, direction, quantity, thesis, entry provenance,
   timestamps, lifecycle and mode. Intent alone cannot establish a factual PAPER
   position. Appropriate adapter execution-result evidence is mandatory for that
   transition; absent an adapter, opening remains unsupported. SHADOW state must
   be explicitly hypothetical. No LIVE activation.
7. ThesisLifecycle assesses later causal WorldState. Implement only states with
   supported factual predicates (for example expiry or unavailable execution
   evidence). Do not claim strengthening, regime/mechanics changes or target
   attainment without a defined supported evaluator. PnL is not a thesis input.
8. ExitIntent binds position, lifecycle assessment, evidence, reason and mode.
   It does not close or mutate the position; closure needs execution evidence.
9. Reallocation binds currently authorized portfolio and validated ranking.
   Missing a common comparable basis defers. Any proposed additional exposure
   requires risk reauthorization. Cash and retaining exposure are valid; no
   forced turnover or invented opportunity-cost return.
10. Attribution is a schema only: forecast, selection, regime, mechanics, sizing,
    portfolio, execution, exit, fees, funding, slippage, opportunity cost and
    residual are distinct. Unknown contributions remain unknown. No attribution
    value feeds historical decision formation or establishes learned Edge.
11. The opt-in shadow runner connects decision, quality, plan and intent with
    durable deterministic artifacts and idempotent replay. Preserve abstention,
    defer, rejection and NO_ORDER. No broker, fabricated paper fill or mutation
    of upstream decisions. Position/lifecycle integration remains evidence gated.
12. Adversarial tests cover type/provenance substitution, future inputs, unknown
    values, LIVE promotion, risk bypass, unsupported conversion/multi-leg orders,
    intent-as-fill, estimate-as-observation and legacy evidence substitution.

## Non-claims and validation

Plan ≠ execution. Intent ≠ acknowledgement/fill. Estimate ≠ observation.
Exit intent ≠ close. Paper/shadow ≠ live. Attribution schema ≠ learned Edge.
UNKNOWN ≠ zero. Raw score ≠ probability. Uncalibrated forecast ≠ valid economic
probability. No outcomes/PnL may form or alter historical decisions.

Final validation runs new focal tests and direct upstream regressions for shadow
decisions, risk, allocation, ranking, WorldState, Radar and ExecutionObservation;
compile core and check whitespace. Report every stage commit, publication status,
HEAD, origin/main and worktree. Success requires all stages published and a clean
tree with HEAD equal to origin/main. No real capture or operational deployment is
implied. Edge, Regime validation and Mechanics validation remain NO; no policy
winner is selected.

## Implementation record — Window #4R

New modules: `core/scientific/execution_position_plane.py` and
`core/scientific/shadow_execution_intent_runner.py`. They reuse finalized shadow
decisions and the existing risk/allocation revalidation, without changing those
upstream contracts. No local collectors, captures or operational ledgers changed.

Explicit supported limits:

- ExecutionPlan READY means authorized single-leg **USD notional**, never a venue
  order. There is no factual risk-to-notional conversion adapter.
- OrderIntent has BUY/SELL, instrument, venue, product, mode and USD_NOTIONAL
  units. All intents remain non-actionable: USD notional is not USDT/base quantity,
  and the venue quantity/order-parameter adapter is absent. The runner records
  NO_ORDER even when a descriptive notional intent can be represented.
- PositionState is PENDING_EXECUTION only, in SHADOW or PAPER. Filled quantity,
  entry price and execution reference are unknown. Opening/closing factual
  inventory is deliberately unavailable until an accredited result adapter exists.
- Lifecycle ACTIVE means tracked, not validated. Only missing causal book and
  explicit thesis expiry yield EXECUTION_RISK and TIMEOUT. No strengthening,
  predictive invalidation, Regime/Mechanics change or target evaluator is supplied.
- Reallocation can reauthorize additions to an empty portfolio. Any incumbents
  defer comparison, even if an ID matches ranking. No disposal/turnover is modeled.
- Attribution declarations are SCHEMA_ONLY_UNVERIFIED_NOT_EDGE; evidence references
  and method declarations do not constitute independently validated attribution.

Trust boundary: input worlds must come from the existing verified loaders and
quality policies from the caller's frozen configuration. These object contracts
do not authenticate the internet or accredit a caller-supplied registration time.
Book materialized fields are checked against wire and temporal order; proving
the full raw-response commitment remains the responsibility of the existing
loader. No fixtures or caller-constructed objects constitute real capture proof.

Opt-in API: `run_shadow_intents(decision, quality_policy, directory, enabled=True)`.
Choose a dedicated artifact directory outside the repository and outside all
Price/Event capture ledgers. No runner is installed or scheduled. Artifacts bind
the full plan/gate provenance, original upstream state, per-candidate reasons and
null position/lifecycle hooks. Identical replay reads the existing bytes without
rewriting them. Conflicting or interrupted partial files fail closed; automatic
repair or overwrite is intentionally absent. Changing any committed input creates
a different run identity, not a revision of the original artifact.

Adversarial review added wire/materialized-field and received/available checks,
explicit BUY/SELL semantics, and regression coverage for tampered caps/identities,
future/naive timestamps, intent/estimate substitution, unsupported multi-leg
execution, expiry, unknown costs, absent incumbent comparison, and preserved
HALT/DEFER/REJECT/abstention. Legacy execution and learning imports are excluded.

Validation: 26 Window #4R focal tests and 61 direct upstream regressions passed.
Core compileall and git diff whitespace checks passed. Tests use synthetic
fixtures only, with no claim of prospective execution or trading evidence.

### CP-7H: separate simulated open inventory

`core.scientific.paper_position.PaperOpenPosition(fill)` accepts only an exact,
verified `SimulatedPaperFill`. It derives base quantity, entry price, fill and
pending-position references, thesis and availability from that fill. The fill
retains the complete request, quality gate, intent, quote and simulation provenance.
PaperOpenPosition.entry_execution_ref references only SimulatedPaperFill.fill_id; it is not an ExecutionResult, venue fill, broker acknowledgement, or factual/live execution reference.
The frozen contract has a deterministic position identity and a separate
`PaperPositionPhase.PAPER_OPEN`; mode is PAPER and actionable remains false.
Availability follows the quote's available_at, never an earlier exchange time.

`PositionState` and `PositionPhase` remain PENDING_EXECUTION only. Construction
does not mutate the pending record. None/NO_FILL, intents and estimates cannot
open inventory. ThesisLifecycle, ExitIntent and reallocation are not extended
to accept this contract. No runner, persistence or legacy bridge is introduced.

PAPER_OPEN denotes simulated inventory, not venue/broker execution or factual
holdings. CP-7G's supplied-cycle scope and nominal USD=USDT assumption remain.
Fees, funding, realized PnL, exits, learning and execution accreditation are not
established. EDGE remains NOT_DEMONSTRATED, REGIME_VALIDATED and
MECHANICS_VALIDATED remain NO, and POLICY_WINNER remains NONE.
