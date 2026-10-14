# Metrics Admission Authority v1 — recovery and qualification

Baseline: 88ee365b827939800f611a24a17a20c06e932b9f.
Branch: manual/51-metrics-real-admission-20261014.
Recovered four untracked files; no unrelated changes. Last rejected edit absent.
No qualified chronology/capture contract was changed.

## Scientific boundary
Activation is exclusive, internally timestamped, PILOT-only and binds source
configuration/root, dedicated observations ledger, admission/publication code
hashes and detached runtime commit. Every read reauthenticates the authority.
TEST_ONLY cannot bind production paths; pytest is rejected before reading them.

A verified SUCCESS is POST_AUTHORITY only when every component request started
after activation. Economic timestamps are preserved separately. Pre-authority
captures remain forensic evidence and receive no admission/publication receipts.

The interrupted worker had an extra current-hour filter. Recovery removed it:
re-inspection may admit an unprocessed post-authority bundle later, subject to the
qualified admission contract's existing 24-hour limit. No timestamps are backdated.
A later publication is invisible to earlier decisions. Experiment 51's frozen
S+5m raw cutoff is unchanged; late admission cannot manufacture timely Mechanics.
There is no source request, retry, backfill, interpolation or historical repair.

## Atomicity, persistence and replay
The worker reuses qualified six-row atomic admission and post-commit publication.
Missing receipt is unavailable; interrupted claims are terminal, without automatic
publication repair. The separate append-only hash-linked result journal records
START/RESULT/SCAN, authority, slot, bundle/capture, six IDs, publication, start/end
and failure reason. Exact completed admission is reauthenticated idempotently.

Descriptive Mechanics is persisted through the existing adapter only when the
frozen raw cutoff passes. Result includes mechanics_id or the late-publication
reason. Status distinguishes capture, admission, causal Taker and readiness.
OBSERVED requires production authority plus an authenticated admitted bundle;
it does not imply that a late bundle passes the frozen Experiment 51 cutoff.
METRICS_REAL_READY, MECHANICS_REAL_READY and EXPERIMENT_51_READY remain false in
this operator: experiment population/common-support gates are separate.

## Deployment contract (not activated before CI)
Runtime: Documents/OMA-CORE-RUNTIME-METRICS51, detached at qualified SHA.
State: Documents/O-C data/prospective/metrics-admission-v1.
Files: authority.json, attempts.sqlite, observations.sqlite (including the existing
metrics_publications_v1 table). Source: prospective/metrics-h1-v1, read-only.

CLI: scripts/metrics_admission.py --root <absolute-path> activate --capture-root
<absolute-source>; then once/status/inventory. No fixture mode in production CLI.
Installer rejects duplicate OMA-CORE-Experiment51-Metrics-Admission tasks. Python
3.11, explicit immutable runtime/working directory/state, IgnoreNew, 4-minute
limit, interactive limited principal. Every five minutes (:04, :09, ...). An early
scan finding no SUCCESS does not claim the slot; subsequent scans inspect again.
Cadence never changes scientific availability. Frozen source scheduler untouched.
Runtime pinning must precede activation because the authority authenticates its
runtime; both operations occur only after full CI PASS.

## Local qualification
- Focal: 65 passed.
- Related causal/role/replay/Mechanics/PM/PRM/readiness/support/binding: 256 passed.
- Existing Windows partition: 202 passed, 2 known skips (pythonw; symlink privilege).
- Authority/worker execution evidence: 34 passed, zero errors/failures/skips,
  operator-results.xml under O-C data/metrics-admission-recovery-validation.
  Only its 31 Windows-fixture cases were added to the hybrid CI manifest.
- PowerShell test now uses shutil.which('pwsh') or powershell, normal import;
  no security/execution policy was changed.
- Full isolated CI: pending candidate publication. Real activation: pending CI.

Adversarial checks: pre-authority exclusion; no receipt retrofit; immutable
activation/role/bindings; no network; repeated scans; actual late availability;
commit before publication; missing proof rejection; exact duplicate preservation;
conflicting rows fail closed; test/production separation. Qualified chronology
regressions remain passing. No outcomes, holdouts or preregistration edits.
