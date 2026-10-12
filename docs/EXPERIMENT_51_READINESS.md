# Experiment 51 readiness control plane

Run `python -B scripts/check_experiment51_readiness.py --price-state PATH
--metrics-state PATH --funding-state PATH` from DEV. JSON stdout only. The CLI
uses actual aware UTC; no network, initialization or state writes. Collectors,
task definitions, runtime checkout and legacy evidence remain unchanged.

Closed source slots S are inspected only after S+5m. That is the preregistered
source availability deadline, NOT the opportunity decision D=S+1H. Existing
source-specific verification remains stricter where required. The CLI reads raw
payloads only through existing integrity/semantic gates; emits metadata only.

Profiles: authenticated Price coverage and certificate-backed Regime input
support; atomic Metrics capture support; published Funding capture support;
exact same-slot Price/Metrics, Price/Funding and all-three intersections. Missing,
late, invalid and wrong-role inputs remain excluded. Total differs from suffix;
a gap or failed latest closed slot resets current support. Funding is not payment.

Regime readiness requires reconstruction of an exact 81H role certificate.
Mechanics capture support is Price plus the six-member Metrics bundle; it is NOT
admission. Separate capture states do not establish a unified admitted causal
snapshot. No writes/ingestion are attempted. The current implementation keeps
mechanics_input_ready and experiment_51_ready false with explicit unimplemented
qualification blockers. No caller boolean can bypass these gates. Future support
for passing them requires actual authenticated bindings, not changing a flag.

Readiness does not read Event journals, real policy outputs, outcome tables or
holdouts; consequently it does not claim to measure eligible CS4 opportunities.
The existing CommonSupportRegistry remains the authority for that later step.

Readings are not a transactional snapshot across three active collectors. Only
closed slots are included; integrity failures exclude evidence. Snapshot time and
source records are explicit. Heartbeat is never evidence. This metadata report
cannot certify predictive value or provide cryptographic protection against an
attacker rewriting all local artifacts. Operational failures are reported, not repaired.

## Qualification checkpoint (2026-10-13 local / 2026-10-12 UTC)

Baseline ff91dd629997ffc9ad386dfbf65b4c5fad6ede5e. Canonical preregistration hash:
`7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8`.

Windows new/related tests: 129 passed (includes 26 new tests). Existing Windows
partition: 179 passed, 2 environmental skips (pythonw interpreter selection and
symlink privilege; alternative reparse regression passes). Compile and frozen
surface comparison PASS. Linux full-suite qualification is required via the
branch-scoped CI before declaring publication qualified.

Read-only live check at 2026-10-12T23:15:25.174633Z: Price 5 valid total / 5 suffix,
one failed slot; Metrics PILOT 37 / 10, nine failures; Funding PILOT authority
from verified ExecutionReceipt and funding_continuity.ROLE, 68 / 62, two failures
and one missed slot. All last valid slots 2026-10-12T23:00Z. Price ledger PASS,
Funding structural integrity PASS. Price had seven network attempts including
one numbered retry; status command made no network request.

Price/Metrics, Price/Funding and three-way capture intersections each contain
five slots, 2026-10-12T19:00Z through 23:00Z, contiguous with no internal gap.
Earlier exclusions remain in the full CLI output; they are not repaired or
relabelled. Regime plus Metrics input support is zero (no 81H certificate).
Regime input readiness false; Mechanics admitted-input readiness false;
Experiment 51 readiness false. Current runtime liveness remains UNVERIFIED;
heartbeat is not scientific evidence. Counts are a dated snapshot, not a promise
that ongoing collector state stays unchanged.

Adversarial review found a readiness-only issue: a rehashed SUCCESS file with
wrong status/schema or inconsistent completion chronology must not count.
The additive reader now checks these fields; regression passes. No operational
source was altered. SQLite errors also fail closed as explicit verification
failure. No real predictive result or policy output was read.
