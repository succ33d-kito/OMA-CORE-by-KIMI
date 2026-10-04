# Decision Rule Contract v1

Baseline: `2c686203974428d39563c404222c1d133a2b1c0b`.

## Scope and semantics

PolicyDecision retains authorization/causal eligibility. ActionIntent separately
records the result of a rule. Neither is an order or fill. This slice is explicitly
**TEST/REFERENCE ONLY, SYNTHETIC, NON-CALIBRATED, NON-EDGE**.

The existing Kernel supplies hashes rather than value payloads. ReferenceSignal
therefore supplies a closed synthetic `(family, vote)` with vote -1, 0 or +1 and a
namespaced commitment. No metadata, dependencies, callbacks or market feature
adapter is accepted. Its commitment must match the authorized InputEvidence's
value_hash. There is no inference of direction from arbitrary hash contents.

## One function

`decide_reference(decision, rule, signals)` verifies eligibility and delegates to
one policy-blind function: sum all authorized votes; ABSTAIN when the absolute sum
is below the explicitly provided positive integer minimum_absolute_votes;
otherwise LONG for positive sum and SHORT for negative sum. The algorithm receives
only votes and the threshold, never policy name, controls, role or outside state.

ABSTAIN means no new exposure, not closing an existing position. No confidence,
sizing, quantities, costs, execution or outcomes are computed.

ReferenceRule ID is `pnep-synthetic-vote-sum`, supported version `1`. Parameters,
action space, abstention semantics and reference-only mode are committed. There
are no default parameters or calibration. The threshold 1 in fixtures is a
synthetic demonstration, not an empirical trading threshold. Unsupported rule
versions fail; a future algorithm requires an explicit new version/implementation.

## Eligibility and comparability

Only unexecuted decisions with disposition None and fully causal authorized
information produce reference intents. Ineligible decisions fail without fallback.
Missing signals, unauthorized families, duplicates or mismatched commitments fail.
Kernel masks are reused; no new policy authorization table is introduced.

The current real Kernel still blocks PR/PM/PRM operationally. This code preserves
that restriction. Tests explicitly construct hypothetical eligible decisions to
exercise those interfaces and separately prove real Kernel decisions remain
blocked. No fixture override is implemented in the production module.

`require_same_rule_experiment` checks paired opportunity/context, role, decision
time, controls, rule/version/parameters and common value commitments. Different
actions are allowed; duplicate policies and different shared inputs are not.
The caller must run this check before treating intents as one paired experiment.

## Audit and boundary

Immutable ActionIntent commits policy and opportunity identity, role, decision
time, PolicyDecision identity, comparison context, information set, controls,
rule/parameters, canonical family commitments and action. Ordering does not affect
identity. SharedControls are referenced through their commitment, never modified.

Upstream validation/provenance remains required. A manually forged PolicyDecision
is not authenticated by this pure function; it has no access to raw receipts or
an authority store. Typed synthetic votes are not validated market features, and
their hashes do not establish scientific meaning. Direct dataclass construction
is not evidence that an intent was produced by the rule.

There are no operational imports, clocks, randomness, global mutable rule state,
outcome arguments, executions or learning updates. All returned intents are
reference-only. Applying the reference function is not operational authorization.

## Validation and next step

Synthetic tests cover four masks with one rule, different actions, real upstream
gate rejection, temporal/missing inputs, transitive forbidden dependencies,
commitment mismatches, parameters/controls/role incompatibility, immutable aliases,
input order, process/hash-seed determinism and outcome argument rejection.
Integration uses Policy Kernel tests only.

Next minimal experimental work: specify causal value schemas and their adapters
for Event + Price before considering any non-reference rule. No claim that Regime
or Mechanics inputs are available or validated is implied.

Edge = NO. Regime validation = NO. Mechanics validation = NO. Policy winner = NONE.
