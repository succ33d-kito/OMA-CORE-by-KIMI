# Real Event Receipt & Causal Admission v1

Baseline: `2d9b4374806999f6f857357c373b0a8318bf6943`.

## Capture boundary

No sufficient real Event receipt existed in the inspected contracts. This module
adds a separate Event-only SQLite journal and bounded HTTPS document capture.
It does not read/change the Price ledger, collectors, Event Intelligence, Kernel
or Decision Rule. No source has been authorized or contacted in deployment by
this implementation session; tests use deterministic HTTP transport fixtures.

Authorize an exact credential-free HTTPS document URL and immutable source
version/content kind before receipt. The source set freezes on the first persisted
capture. Document URLs are the narrow capture unit, not a universal news provider
or discovery crawler. Redirects, non-200 responses, unsupported representations,
empty/oversized bodies and Content-Length mismatches are rejected. Only complete
UTF-8 text/plain or text/html entities up to 4 MiB are supported.

FULL_DOCUMENT means the complete HTTP entity from an endpoint declared ex ante to
serve the full document. HEADLINE_ONLY, SNIPPET_ONLY and METADATA_ONLY are explicit
non-admissible kinds. Complete transport does not prove semantic completeness: the
operator must select an actual full-document endpoint. A login page or misleading
endpoint is not made scientifically valid by its content kind. No paywall bypass,
HTML interpretation, provider signatures or automatic completeness inference exists.

## Times, identity and persistence

`received_at` is sampled internally immediately after reading the response bytes.
There is no public clock/content/timestamp injection into capture. Publication or
editorial dates are not accepted as availability evidence. Historical documents
retrieved today are known today, never at their historical publication dates.

Raw content and its SHA-256 are committed first. A subsequent ready marker assigns
`available_at` after that durable write. An interrupted capture without a ready
marker remains UNKNOWN; replay never repairs or backdates it. Admission also has
its own internally assigned processing/availability time, which is what Sampling
uses for the semantic event. A later normalization cannot masquerade as earlier
semantic knowledge. Clock rollback fails closed; clocks are not authenticated.

Document identity is the authorized URL. Revision identity is the caller's explicit
revision identifier within source/version/document. Receipt identity commits that
tuple. Changed content under the same revision conflicts; a new revision appends.
Same revision/content retries return the first receipt unchanged. Content SHA-256
and journal provenance are separate commitments. Roles cannot reuse a document
or identical content across captures.

The journal uses transactions and a hash chain over canonical rows. Supported
operations only append source, receipt, ready, admission or close records. Reads
verify the chain. No overwrite/delete/repair API is provided. External file edits,
deletion, whole-history replacement, hostile Python and clock compromise require
external custody controls; a local hash chain is not a trusted timestamp authority.

## Admission and Sampling reuse

Admission accepts a persisted receipt ID and a closed immutable semantic evidence
object. It requires full-content/known availability, an exact quote containing
explicit BTC or Bitcoin, one declared announcement and explicit shock attribution.
These are upstream semantic assertions tied to content, not a new classifier or
proof of causal/economic impact. A mere mention does not independently establish
relevance; the upstream curator must supply a defensible quote and shock.

The existing SyntheticSampler is reused strictly as an internal deterministic
reducer. Its envelope flags are constructed only after verified real receipt
checks; the public admission API never accepts synthetic envelopes or verification
flags. The exported opportunity receives real-event validator/protocol/population
commitments. Downstream PRICE/REGIME/MECHANICS stay MISSING. No existing module is
changed and no synthetic fixture is promoted to real receipt evidence.

Slots, relations, cluster derivation, first reservation, cross-role shock guards
and correction handling remain the existing Sampling algorithm. Admission follows
receipt order and never retrospectively sorts records. Out-of-order normalization
is rejected by the reducer. Later revisions/reports of the same shock cannot create
another reservation or replace its winner. Corrections known by the decision cut
can invalidate admission; corrections after a closed cut cannot rewrite it.

10:23 and 10:59:59 reserve 11:00; exactly 11:00 reserves 12:00. Late processing
rejects admission at the reserved cut with no rollover. Repeated admission of a
receipt fails closed; repeated capture is idempotent. Close cannot target a future
cutoff. The journal allows deterministic reconstruction of reservations/population.

## Validation and limits

Tests exercise the real capture/admission APIs with simulated HTTP responses and
private clock monkeypatching: no live PIT Event has yet been collected by this
slice. Source authority is an ex-ante local configuration; HTTPS endpoint identity
does not validate publisher claims, manual revision IDs or supplied shock semantics.
The reducer is intentionally small, reconstructing this journal on reads; scalable
collection, external custody and semantic automation are outside scope.

Next minimal action: choose one full-document source and perform one prospective
capture/admission smoke test with its preserved receipt, without outcomes.

Edge = NO. Regime validation = NO. Mechanics validation = NO. Policy winner = NONE.
