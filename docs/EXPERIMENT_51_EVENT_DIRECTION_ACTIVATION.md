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
