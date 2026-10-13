# Experiment 51: prospective EventDirection operator

Baseline `f5e73193fc74a3287af144d4cfa8ba8dbea39e08`.
Branch `manual/51-event-activation-20261013`.
Taxonomy, P0 rule and preregistration are unchanged.

## Existing capture boundary

RealEventStore.authorize_source freezes an exact HTTPS source before capture.
Capture performs bounded HTTP and internally timestamps complete received content;
a second durable ready marker establishes availability. Explicit AdmissionEvidence
provides BTC/shock attribution; the existing sampling reducer reserves the next H1
decision. RealEventStore.close emits the population at the cutoff. These APIs remain
authoritative; no new capture loop or classifier is installed.

Inspected operational Event directory contains the 2026-10-04 first-receipt journal
and a primary-announcement watch configured for one check. Neither is promoted into
new EventDirection evidence. No assertion about an unrelated process being alive
is inferred from these files. This operator does not need a running collector.

## Operator interface

Use the qualified project Python and `scripts/event_direction_operator.py`:

```
python -B scripts/event_direction_operator.py --root <new-authority-directory> --role PILOT activate --event-journal <future-Event-journal>
python -B scripts/event_direction_operator.py --root <authority-directory> --role PILOT status
python -B scripts/event_direction_operator.py --root <authority-directory> --role PILOT attest --receipt-id <id> --assertion-json <curator-file>
python -B scripts/event_direction_operator.py --root <authority-directory> --role PILOT status --controls-json <frozen-controls> --price-ledger <ledger>
python -B scripts/event_direction_operator.py --root <authority-directory> --role PILOT bind --controls-json <frozen-controls> --price-ledger <ledger>
```

No timestamp, return, outcome or inferred class arguments exist. Assertion JSON
requires all ClassAssertion fields: event_class, curator, quote, actor,
official_confirmed, direct_btc_action, unambiguous, commitment_not_fully_completed.
The four flags are JSON booleans, not strings. UNKNOWN is an explicit valid class;
it never silently becomes NEUTRAL. Source semantics remain a curator trust boundary.
Do not let an automated agent infer the class for future real receipts.

Controls JSON must contain exactly the existing SharedControls constructor fields,
including Decimal-compatible risk_budget_quote, the frozen P0_HASH and 14400-second
horizon. No synthetic default risk or execution specification is manufactured.

## Activation and custody

Activation exclusively creates the authority directory and separate SQLite journal.
It records the existing taxonomy authority, then a versioned operator binding with
role, rule hash, resolved source path and hash/count of any existing source prefix.
The completed operator-binding timestamp is the conservative activation time A;
receipt R must be strictly later than A. Both timestamps are internally generated.
The binding digest is activation_id; the taxonomy header digest is authority_id.
Duplicate/interrupted activation is never overwritten or repaired. Wrong role,
rule, corrupt journal or changed source prefix fails closed. A missing source file
is allowed only when the committed prefix is empty; activation does not create it.

A newly designated source journal is a separate prospective cohort. Its future
source authorization/capture/admission must use the existing RealEventStore API.
The operator never appends to that source, retroactively reassigns role or relabels
old evidence. Explicitly close the cohort through the existing API after D before
binding, then bind before its earliest 4H horizon completes. Missing/malformed
members fail the whole bind rather than disappearing. UNKNOWN remains included;
missing Price remains kernel-ineligible. Binding once fixes the cohort; this is not
a rolling append population. Incomplete publication is observable, never repaired.

## Read-only status

RealEventStore now supports mode=ro reads that do not initialize schema/files;
its capture/write methods reject read-only use. EventDirectionAuthority accepts
that read-only mode. Status reports verified direction counts, post-activation
receipts, reasons, bound count, and P0 eligibility when controls are supplied.
Without controls and with receipts present, P0 count is null/CONTROLS_REQUIRED,
not falsely zero. Status checks persisted manifest/binding against their publication
commitment. No predictive data is loaded. Local journal custody is not a security
boundary against hostile filesystem access. Status is a read-only scan, not an
atomic cross-database transaction during concurrent collection.

## Qualification

New operator plus existing direction tests: 69 passed (22 new, 47 existing).
Related Event/role/kernel/population/readiness suite before two final added tests:
287 passed. Final hybrid CI and real activation are recorded below after completion.
No real receipt or curator assertion is generated by qualification.

Preregistration canonical SHA-256 remains
`7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8`.
Experiment 51 is not executed; no Regime/Mechanics validation, policy winner, Edge
or real-capital authorization is implied by activation.

## Qualified operational checkpoint — 2026-10-13

Implementation SHA: `c9e706d31bcbd15f30a47cdc1f473929537b6c43`.

- Final focal: 69 passed (22 operator, 47 direction/P0).
- Related contracts: 287 passed before the final two added operator regressions.
- Windows hybrid partition: 179 passed, 2 skipped in 38.33s (pythonw branch and
  unavailable symlink privilege; existing reparse regression covered).
- Full isolated Linux CI: 2348 passed, 194 skipped, 3 warnings in 200.96s.
  Skips: 181 Windows partition nodes, one Windows-only readiness fixture covered
  locally, 12 unavailable-network/OHLCV tests. Existing pytest fixture warnings.
- CI: https://github.com/succ33d-kito/OMA-CORE-by-KIMI/actions/runs/38356376387
  Job 115160128844 completed successfully on the implementation commit.
- Changed Python compile checks and git diff --check: PASS.

Real activation initially did NOT execute because automatic approval review hit a
usage limit. On explicit resume, HEAD and clean tree were reverified, both proposed
state paths were absent, and the qualified CLI performed the activation exactly once.
No test suite was needlessly repeated on unchanged implementation.

EVENT_DIRECTION_AUTHORITY_ACTIVATED=YES
EVENT_DIRECTION_AUTHORITY_ID=222ed0b4ab7e1a3eec75d5620f0d18e684e752dc19954e287e7ff37be55053fe
ACTIVATION_ID=9f0fe2a218dae7685409c252b8dfe2590055d0c938336fc3c375a30b992c41da
EVENT_DIRECTION_ACTIVATED_AT=2026-10-13T16:39:33.520949+00:00
EVENT_DIRECTION_DATASET_ROLE=PILOT
RULE_HASH=6a07b7e1d5a1ed2f9a9635de362b50844d5c9092bea52792f3391da3e9045833

State directory:
`C:/Users/KiTO/Documents/O-C data/prospective/event/experiment51-direction-pilot-20261013`
Authority journal: `authority.sqlite` inside that directory.
Designated future source journal (not created):
`C:/Users/KiTO/Documents/O-C data/prospective/event/experiment51-source-pilot-20261013.sqlite`

POST_ACTIVATION_EVENT_RECEIPTS=0
EVENT_DIRECTION_ATTESTATIONS=0
BOUND_EVENT_POPULATION=0
P0_ELIGIBLE_OPPORTUNITIES=0
EVENT_POPULATION_BOUND=NO
P0_REAL_PROSPECTIVE_PATH=NO

The last flag means no real receipt-to-P0 path has yet been observed. Its operator
and binding code is qualified and available; it is not a claim of real evidence.
The source journal is absent. No Event capture or classifier was installed/launched.
No real EventClass was selected and no prior Event was relabelled.

Read-only CLI reread returned identical activation/authority identities and counts;
SHA-256 of authority.sqlite was unchanged before/after status. The two historical
Event journals also retained their pre-activation hashes:
- first-real-receipt-2026-10-04: 57fa5663ce58a0fc65a0bb588a9c860e6131a7b01cb8352c16586199be030763
- primary-announcement-watch-2026-10-04: e9ed9db42e4e2ede19f6c51e67ea2532da9dbdbdc46adcc7b10d947f59142efe
LIVE and Price runtime worktrees remained clean. Runtime SQLite state stays outside
Git; this document records immutable activation facts only.

DERIVED_SNAPSHOTS_BOUND=NO
EXPERIMENT_51_READY=FALSE
EXPERIMENT_51_EXECUTED=NO
REGIME_VALIDATED=NO
MECHANICS_VALIDATED=NO
POLICY_WINNER=NONE
EDGE=NOT_DEMONSTRATED
REAL_CAPITAL_AUTHORIZED=NO

Next dependency: authorize/capture a future source through the existing real Event
API into the designated PILOT journal, obtain explicit authorized curator assertion
before D, and close/bind a causally valid cohort. Missing inputs remain ineligible.
Do not backdate, automatically classify, repair older receipts or inspect outcomes.
