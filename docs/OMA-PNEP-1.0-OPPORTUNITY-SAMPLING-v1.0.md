# OMA-PNEP-1.0 — Opportunity Sampling Contract v1.0

## Scope and authority

Implements the project owner's approved synthetic sampling slice on baseline
`2ed24dedcd3c65632cad3a45d38487f9c324dd52`. Existing PNEP contracts are unchanged.
This is an in-memory synthetic fixture harness, NOT live admission or execution.
No network, collectors, real data, live ledger, market inputs, policy kernel,
trades, outcome calculations, performance, or operational integration.

## Fixed universe and identity

- Asset: BTC; instrument: BTCUSDT; venue: Binance USDⓈ-M.
- Product: linear perpetual; cadence: H1.
- The envelope cannot choose instrument, venue, product or a policy.
- Event ID: SHA-256 of the versioned namespace, source, document ID and revision
  ID. Content is bound by registry checks: incompatible content under the same
  declared revision raises ConflictError, rather than obtaining a fresh ID.
- Processing time, receipt time, role and sampling result are not event identity.
- Opportunity ID uses the existing EligibleDecisionOpportunity identity exactly.
- A new revision must have a new declared revision ID. Repeated receipts remain
  separate audit records; replaying an identical receipt ID is idempotent.

## Synthetic evidence and causal cut

SourceConfig is frozen before use: exact source/version and authorized_at strictly
before receipt. Envelope attestations are fixture inputs, not authentication of
real evidence. Unknown, incomplete or conflicting provenance is never inferred.

event_time and published_at are nullable descriptive fields. They never supply
received_at. UTC-aware times are mandatory. When present, processing cannot
precede receipt and availability cannot precede receipt or processing.

An accredited receipt reserves its sole decision cut:

`decision_at = floor_UTC_hour(received_at) + 1 hour`

Thus 10:23 and 10:59:59 map to 11:00; exactly 11:00 maps to 12:00.
The slot ID is `H1:YYYY-MM-DDTHH:00:00Z`. Processing never changes this cut.
Admission requires processed_at and available_at to be known and
`received_at <= available_at <= decision_at`. Late or unknown admission fails
permanently for that reservation. No rollover or later report rescue.

## Minimal API and ordering

1. Construct SyntheticSampler with an immutable tuple of synthetic SourceConfig.
2. register(envelope, role=PILOT) appends a Candidate and, when appropriate,
   creates the immutable Reservation. Returns the original candidate on identical
   receipt replay. No evidence-dependent reordering is performed.
3. sampling_eligible(reservation_id, cutoff) checks only the reserved cutoff.
4. close(cutoff) freezes due Admission results and materializes admitted
   EligibleDecisionOpportunity objects using the existing store/contracts.
5. candidates(), reservations(), population(), counts() expose immutable snapshots.

Register the synthetic input log in actual receipt order. Equal receipt times use
the log's append sequence, preserved on replay. close() represents a completed
input watermark: no later new receipt may be backdated before it. Identical
receipt replay remains idempotent. Closing later can reconstruct accounting at
the original cut, never claim that a live decision was executed there.

An unaccredited observation remains in the audit log but does not beat the first
accredited receipt. The event lookup may advance to that first accredited record;
the earlier candidate is never overwritten or repaired. Once reserved, no second
receipt changes the reservation, inputs or result.

## Shock evidence, classification and reservation

Only an official announcement key, an explicit canonical primary-document key,
or a relation to a previously registered event supplies cluster identity. Keys
are namespaced. Explicit relation evidence must name an existing parent and its
cluster. Updates/corrections must refer to the same source/document lineage.
No title, category, entity, date or price similarity is accepted by the API.

Taxonomy:

| Class | Identity and action |
|---|---|
| DUPLICATE | Same document/revision; audit receipt only |
| UPDATE | New revision linked explicitly to the original cluster; no new reservation |
| CORRECTION | New revision linked explicitly; no new reservation or historical overwrite |
| SAME_CLUSTER_NEW_REPORT | New report or explicit syndication; existing reservation only |
| NEW_EVENT | New explicitly evidenced shock; may reserve once |

Reservation key: protocol + cluster + fixed instrument + venue + product.
The first accredited NEW_EVENT owns it, including when later admission fails.
Provided cluster references on pending/late envelopes are provisional claims for
dedup/reservation only: they do not establish an admitted cluster or increase N.
Unknown cluster prevents reservation and admission. A later revision cannot
retroactively repair that unknown candidate.

One unambiguous announcement with explicit BTC binding is required. BTC plus
other assets is allowed if it is one announcement. Generic crypto, assumed macro
relevance, altcoin-only and ambiguous/multiple announcements fail closed. No
semantic splitting or implicit BTC relevance is implemented.

A verified correction available by the original cut conservatively rejects that
reservation. A correction available after it cannot change the frozen result.
Updates do not replace the original selected candidate. A genuinely new shock
needs a new explicit announcement identity.

## Population and roles

Missing Price, Regime and Mechanics produce explicit MISSING input assessments;
they never remove an admitted opportunity. EVENT uses the accredited envelope's
receipt, availability and provenance. No policy is executed.

Role is assigned at register(), before admission. A shared registry rejects
cross-role event, content and reserved-shock reuse, including failed reservations.
Independent registries must not be combined without existing manifest isolation;
they intentionally have no global persistent coordination in this slice.
Existing half-open manifest window semantics remain unchanged. No horizon or
outcome window is invented by this sampler.

Counters are population-only:

- N_raw_events: distinct appended receipt records, including duplicate articles
  and rejected candidates. An identical receipt replay is not a new observation.
- N_unique_events: distinct scientific document/revision identities recorded.
- N_sampling_eligible_events: finalized admitted representatives.
- N_event_clusters: distinct clusters represented by finalized admissions.
- N_opportunities: materialized opportunity IDs, irrespective of input eligibility.

The last three are equal in this single-instrument, one-reservation-per-shock
slice. Reservations/candidates expose pending and rejected records separately.
These counters are not a statistical release from RestrictedStore/SafeOutput.

## Limitations and scientific safety

- No real provenance authentication: fabricated synthetic flags cannot authorize
  live use. Receipt, semantic and announcement proof must be implemented/reviewed
  separately before any real admission.
- Explicit evidence keys must be canonical upstream. Different references to the
  same economic shock cannot be reconciled automatically; no fuzzy fallback.
- Binding and announcement count are synthetic attestations, not NLP findings.
- In-memory, single-threaded registry; no persistence, recovery service or scheduler.
- Frozen source configuration; version drift cannot reinterpret old records.
- Operational Event IDs, scores, sentiment, performance and price reaction are
  absent from the API. No imports into operational engines or live capture.

## Verification

Run only the synthetic sampling tests and the reused Slice 1 contract/blinding
tests. Fixtures cover receipt and source gates, exact H1 boundaries, revisions,
immutable reservation/replay, clustering, cross-role reuse, missing inputs,
closed API/counters and existing half-open manifest compatibility.

No Edge claim, no live admission, no commit or push authorized by this slice.
