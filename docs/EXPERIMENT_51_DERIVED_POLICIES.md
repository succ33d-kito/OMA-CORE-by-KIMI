# Experiment 51: derived policies, CS4 and sealed DISCOVERY runner

Baseline: 41ad18ddac1ef3cfc57136b6fdb1b1889afd46cf.
Branch: manual/51-derived-policies-bindings-20261013.
Preregistration canonical SHA-256 remains
7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8.

## Reuse and exact semantics

The adapter reuses EventDirectionAuthority, P0.prepare, role_price_window,
validate_causal_regime, validate_causal_mechanics, metrics_snapshot_available,
PolicyKernel, CommonSupportRegistry, ExperimentalManifest and OfficialBinding.
There is no new Regime or Mechanics engine.

Regime source is Regime/Role/v2, committed by its observations_v2 identity,
payload hash, certificate ID, 81 raw IDs and 81 role-attestation IDs. Validation
reconstructs the certificate and existing er20-vol20-vs-prior60-v1 algorithm.
The actual vocabulary is structure=trend/range/transition. trend and range pass;
transition and unknown veto. The separate descriptive direction/volatility axes
never create or reverse a policy direction. Unknown unmodeled axes are not
mistaken for an unknown structure. This does not validate predictive Regime value.

Mechanics source is Mechanics/Descriptive/v1. Exact replay and the six-member
atomic Metrics gate must succeed; all six features must originate from the same
bundle, required slot S=D-1H and role. Only TakerBuySellRatio enters direction:
>1 confirms LONG, <1 SHORT, 1 means unknown. Missing is not zero. Invalid values
or incomplete/forged bundles fail closed. Descriptive Mechanics with Regime or
Funding dependencies is rejected to protect PM's information set; callers must
use the existing independent Mechanics path without those extra inputs.
No OI, positioning or funding directional inference is added.

Raw inputs must be available by S+5m; derived observations must already have been
persisted and available by D. Regime's certificate must end at S and contain exactly
81 contiguous authenticated observations. No new derived receipt is backdated;
this adapter is read-only. Validators reconstruct from evidence, never repair it.

PR preserves P0 only when Regime passes. PM preserves P0 only when Taker confirms.
PRM requires both. P0 abstention always propagates. Supplied corrupt/wrong-role/
future IDs raise; absent information remains ineligible, while valid-but-vetoing
states abstain. Records commit per-policy rules and input IDs, common opportunity,
role, kernel ID and P0 commitment. The append-only decision row supplies a common
internally recorded timestamp and digest identity for the four-record bundle.

## CS4, phase and official binding

The frozen preregistration explicitly requires CS4 and identical eligible IDs in
all four arms. Therefore PR-P0, PM-P0 and PRM-P0 use the SAME CS4 set, not larger
pair-specific supports. Abstention does not remove membership. Missing causal
inputs exclude from CS4 but remain in the manifest and official population hash.
All members must have prospective policy records: no silent omission/reconstruction
of missing records after the fact.

activate_phase is an explicit owner-authorized DISCOVERY operation, never called
by readiness. It requires a separately active DISCOVERY Event authority and binds
its operator/source identity, ledger path, controls, rules and preregistration.
Internal clock selects the next future H1 boundary; phase length is exactly 2160H.
PILOT cannot activate it. No real DISCOVERY activation occurred in this cut.
An owner-reference string is an authorization assertion, not cryptographic proof.

record_opportunity reconstructs evidence and commits the four policies prospectively
at D <= recorded_at < D+4H, using inputs causally bounded by D. Identical replay is
idempotent; changed input is a conflict. Phase purge is deterministic: entry D+1H,
max label ending D+9H must be <= phase end. No outcome influences this membership.
After source Event closure through phase end, bind_experiment reconstructs every
member and persists the create-once official manifest/binding plus exact CS4 IDs,
full prereg hash (horizons, MES, costs, bootstrap, multiplicity) and phase identity.
No binding rewrites or automatic interrupted-publication repair.

## Outcome firewall and statistics

run verifies protocol/rules/phase, original Event population, authenticated inputs,
policy reconstruction, CS4 and actual official files. It requires fixed phase end
and maturation, >=200 paired opportunities, >=200 active opportunities in EACH arm,
and >=12 occupied calendar blocks. Then it exclusively records authorized_run.
Only after that commit can an internal permit open the outcome adapter. Retrying
an already attempted run is rejected, including after a loader failure.

The default adapter reads DISCOVERY-role-authenticated Price bars only after that
boundary. It uses the first full H1 open strictly after D and the 1H/4H/8H closes,
requires all eight bars, rejects missing/conflicting/unverifiable labels and never
selectively deletes an arm. A supplied spy/test loader is explicitly marked
INJECTED_NOT_REAL; it cannot produce a real-evidence classification.

Statistics reuse _paired and _basic_intervals from the frozen preparation harness:
10 bps per active action, abstention zero; 2 bps MES; paired non-circular 168H moving
calendar blocks; 2000 resamples; seed 51; Bonferroni three-comparison intervals.
Degenerate intervals are INCONCLUSIVE. Secondary results cannot rescue primary
failure or identify a winner. A DISCOVERY PASS still requires unchanged independent
confirmation and is not validated Edge. This cut implements DISCOVERY execution;
future confirmation/survivor authorization remains a separate scientific boundary.

Trust limits: Python private members are not hostile-code security. Local custody,
truthful curator/source assertions and exclusive control of the designated paths
remain required. Read-only validation may scan an advancing ledger; a concurrent
change causes reconstruction mismatch/failure, not automatic reconciliation.

## Operational use (no real phase activation in this checkpoint)

Use experiment51_sealed.activate_phase only after explicit owner authorization
and a separate DISCOVERY authority/evidence scope exist. Use record_opportunity
before its formation deadline, bind_experiment after the fixed phase closes,
and readiness before run. SharedControls remain the existing frozen P0 contract;
no new risk/execution defaults are fabricated. Exact file paths are committed.

scripts/check_experiment51_readiness_v2.py exposes read-only current PILOT coverage
separately from DISCOVERY phase gates. Capture counts do not assert derived admission.
Engineering qualification flags identify this qualified code version, not market
truth. Current Event/PILOT authority is neither modified nor relabelled.

## Qualification and current evidence

Implementation checkpoint: 49e46613bdf42b9c60b8c715bef25d1b08a86850.
Branch: manual/51-derived-policies-bindings-20261013.
Baseline: 41ad18ddac1ef3cfc57136b6fdb1b1889afd46cf.

Qualification completed:
- New focal tests: 94 passed (52.18s).
- Directly related tests: 338 passed (135.14s).
- Windows contract partition: 179 passed, 2 environment skips (63.35s):
  interpreter name includes pythonw; symlink privilege unavailable.
- Linux network-isolated CI: 2439 passed, 197 skipped, 3 warnings (192.85s).
  https://github.com/succ33d-kito/OMA-CORE-by-KIMI/actions/runs/38471466765
  Skips comprise 181 Windows partition nodes, four Windows-only activation
  fixtures (including three new tests passed locally), and 12 unavailable
  network/OHLCV tests. These counts are overlapping suites, not additive coverage.
- Compilation of seven new Python files and git diff --check: PASS.

Engineering qualification: Regime/Taker causal adapters; PR/PM/PRM rules;
identical CS4 support for all three comparisons; official binding; outcome
firewall; DISCOVERY sealed runner. All qualified by tests, not by real
predictive outcomes. Confirmation execution remains a separate future boundary.

Read-only operational observation: 2026-10-13T22:14:59.903457+00:00.
Event authority ACTIVE, PILOT; source journal absent; zero post-activation
receipts, attestations, bound events and P0-eligible opportunities.
Price: 28 valid H1, current/longest streak 28, last slot 22:00 UTC,
ledger integrity PASS. Metrics: 54 valid H1, current streak 6, longest 12,
last slot 22:00 UTC. Metrics capture coverage does not prove causal admission.
No runtime liveness assertion is made. LIVE and Price runtime Git trees clean.

PRICE_81H_CAUSAL_READY=NO. REGIME_REAL_READY=NO. METRICS_REAL_READY=NO.
MECHANICS_REAL_READY=NO. DERIVED_SNAPSHOTS_BOUND=NO.
EVENT_POPULATION_BOUND=NO. DISCOVERY_ACTIVATION_READY=NO.
DISCOVERY_ACTIVATED=NO. EXPERIMENT_51_READY=FALSE.

Remaining blockers: real post-activation event evidence; authenticated 81H
Price window; admitted atomic Metrics and derived-state population; explicit
future DISCOVERY authorization and separate role-scoped authority/controls;
fixed future phase, official population binding and frozen sample-size gates.
No PILOT evidence is relabelled DISCOVERY. No real experiment was run.
The nested legacy coverage report retains its older static rule blocker;
this checkpoint and v2 engineering flags establish current code qualification.

Preregistration canonical hash unchanged:
7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8.
No collectors, protected runtime code, holdouts or prospective evidence were
modified by this cut. No outcome results were inspected. The next minimal
operational cut is acquiring and authenticating a first legitimate Event
receipt under the existing PILOT authority, without manufacturing direction.

EXPERIMENT_51_EXECUTED=NO. REGIME_VALIDATED=NO. MECHANICS_VALIDATED=NO.
POLICY_WINNER=NONE. EDGE=NOT_DEMONSTRATED. REAL_CAPITAL_AUTHORIZED=NO.
