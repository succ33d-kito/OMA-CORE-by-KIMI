# Experiment 51: BTC Event Direction v1 and P0

Owner-authorized prospective taxonomy, 2026-10-13. Baseline:
`bb473955f6c7cad37eda8d1026a56cdd4a991486`.

## Semantic authority

`ClassAssertion` is an explicit curator attestation, not an automated classifier.
The curator supplies the canonical class, identity, an exact full-document quote,
and confirmation/direct-BTC/unambiguous assertions. Access expansion and net buy
map to LONG; access restriction and net sell map to SHORT. Buy/sell additionally
require an actor in the quote and an explicit not-fully-completed commitment.
Missing assertions yield UNKNOWN. Unsupported events must be assigned UNKNOWN.
Generic sentiment, macro news, filings/rumors/delays, forecasts, hacks, upgrades,
mining, positioning, funding, OI and taker metrics are not directional authorities.
No source currently authorizes NEUTRAL; this authority cannot emit it.

The code checks evidence inclusion and custody, not whether a curator told the
truth or correctly understood a document. Tests of unsupported classes demonstrate
no fallback, not free-text classification accuracy. A manually constructed record
is not accepted by P0: it re-verifies the journal and source receipt.

## Prospective custody

Activate `EventDirectionAuthority.activate(new_path, role=DatasetRole.PILOT)` in
a separate new journal BEFORE the first eligible receipt. Then call
`attest(event_store, receipt_id, ClassAssertion(...))` before reserved decision D.
No caller timestamps are accepted. Existing RealEventStore hash-chain, transaction
and sampling mechanisms are reused; original Event/Price journals are not written.

Activation < receipt received <= receipt available <= admission available <=
attestation recorded <= durable-publication marker < D. The record commits receipt,
provenance, class assertion, rule, role, authority and original decision reservation.
The first assertion is immutable. Identical replay returns the first record;
conflicting replay fails. Interrupted publication stays unusable, with no repair.
Historical receipts predating activation cannot be relabelled. This is local
custody, not a security boundary against a hostile process with filesystem access.

## P0 and Price cutoff

`prepare` reuses the closed official sampling opportunity and verifies direction.
The unchanged preregistration chooses source slot S = D - 1H, hence the H1 bar
ending S, raw available <= S + 5 minutes, role attestation available <= D.
A bar ending D and received after D is not substituted. Price is read-only and
verified using existing causal snapshot and role-attestation validators.

Price close > open maps LONG, close < open SHORT, flat UNKNOWN. P0 emits LONG or
SHORT only on equal known directions AND PolicyKernel causal eligibility; otherwise
ABSTAIN. Cross-role/future inputs fail closed. Missing Price is never imputed.
`decide_p0` requires P0_HASH and the frozen 4H horizon in SharedControls. It commits
an immutable receipt in the separate direction journal at D <= now < D+4H;
identical replay remains readable later. No execution or outcome loader is invoked.
Actual recording time remains visible; this does not assert execution at D.

## Population boundary

`bind_population` reuses PolicyKernel, CommonSupportRegistry, PopulationScope,
ExperimentalManifest and OfficialManifestStore. Every closed source member must
have a valid direction attestation, or binding fails without silent filtering.
UNKNOWN remains a population member and implies P0 abstention. Missing optional
Regime/Mechanics remain ineligible. Original opportunity identity is preserved;
adapted input and population commitments explicitly identify this authority/rule.
Freeze must precede the earliest primary-horizon completion. This minimal binding
is for a bounded prospective cohort, not retrospective accumulation over many days.

Only fixture journals were bound during qualification. No real population or
derived snapshots have been bound, no authority deployed and no collectors changed.

## Preserved scientific contract

Preregistration canonical SHA-256:
`7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8`.
Primary 4H; secondary 1H/8H; all uncertainty/cost/MES settings unchanged.
PR remains a Regime veto; PM remains taker-ratio confirmation; PRM combines them.
These additional action rules are not implemented here. No OI/positioning direction.

Experiment 51 is NOT ready or executed. Regime/Mechanics validation: NO.
Policy winner: NONE. Edge: NOT DEMONSTRATED. Real capital: NOT AUTHORIZED.

## Qualification and checkpoint

Implementation SHA: `65e5377ef977ebe0d143f9e6ac819fbc29a739ae`.
Branch: `manual/51-event-direction-v1-20261013`.

- Final focal: 47 passed in 5.14s.
- Related contracts before final explicit eligibility guard: 287 passed in 19.87s.
  The final implementation is covered by the full isolated CI below.
- Existing Windows partition: 179 passed, 2 skipped in 36.30s. Skips: pythonw
  branch and unavailable symlink privilege (reparse regression covered).
- Full isolated Linux suite: 2326 passed, 194 skipped, 3 warnings in 203.63s.
  The 194 skips comprise 181 Windows partition nodes, one Windows-only readiness
  fixture (passed in local related tests), and 12 OHLCV-dependent tests with no
  network/data available. Three existing pytest fixture deprecation warnings.
- Compile and git diff --check: PASS. No security policy changed.
- CI: https://github.com/succ33d-kito/OMA-CORE-by-KIMI/actions/runs/38352713051
  Job 115148512447: success. Suite executed with network namespace disabled.
- LIVE and operational Price checkout status stayed clean. No prospective
  runtime, ledger, collector, holdout or preregistration file was modified.

Adversarial review: explicit kernel eligibility now gates P0 action even if
agreement exists; directional Event + missing Price has its own regression.
Wrong role, future evidence, late first formation, conflicting replay, tampering,
interrupted publication, wrong horizon/rule and silent population filtering are
covered. Public assertions are curator claims, not independently established truth.

EVENT_DIRECTION_V1_IMPLEMENTED=YES
EVENT_DIRECTION_V1_QUALIFIED=YES
EVENT_POPULATION_BOUND=NO
P0_DIRECTION_RULE_FROZEN=YES
P0_DIRECTION_RULE_IMPLEMENTED=YES
P0_DIRECTION_RULE_QUALIFIED=YES
DERIVED_SNAPSHOTS_BOUND=NO
EXPERIMENT_51_READY=FALSE
EXPERIMENT_51_EXECUTED=NO
REGIME_VALIDATED=NO
MECHANICS_VALIDATED=NO
POLICY_WINNER=NONE
EDGE=NOT_DEMONSTRATED
REAL_CAPITAL_AUTHORIZED=NO

Population binding capability is qualified on synthetic fixtures only; no real
EventDirection authority was activated and no historical PILOT records relabelled.
Remaining operational dependency: activate a separate authority before future
receipts, attest before D, and bind a causally valid bounded cohort. Additional
PR/PM/PRM and derived-snapshot integration remains outside this cut. Do not infer
scientific validity, profitability or readiness from engineering tests.
