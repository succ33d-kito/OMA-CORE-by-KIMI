# Metrics Admission Authority v1 â€” recovery and qualification

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
- Full isolated CI: PASS. Real activation and scheduled smoke: PASS (below).

Adversarial checks: pre-authority exclusion; no receipt retrofit; immutable
activation/role/bindings; no network; repeated scans; actual late availability;
commit before publication; missing proof rejection; exact duplicate preservation;
conflicting rows fail closed; test/production separation. Qualified chronology
regressions remain passing. No outcomes, holdouts or preregistration edits.


## Qualified operational checkpoint — 2026-10-15 Africa/Lagos

Implementation/runtime SHA: bcc8705aa2c02e65b60b2fa798b6e039c48fc8b3.
Full isolated CI: https://github.com/succ33d-kito/OMA-CORE-by-KIMI/actions/runs/38654925380
Workflow conclusion SUCCESS for that exact SHA: 2488 passed, 252 skipped,
3 warnings in 131.40s. Hybrid skips include independently executed Windows cases;
no failed tests were hidden. Existing pytest fixture and Node deprecations remain.
Compile, PowerShell parser, staged diff-check and frozen preregistration hash PASS.
Preregistration: 7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8.

The automatic review rejected an initial manifest-generation command because it
would infer PASS from collection alone. It did not execute. The accepted update
instead parsed the actual 34-pass JUnit execution and registered only 31 applicable
Windows cases. No security/execution policy was changed.

Authority: e27b978486346d59d3022937ffeee5c75e5e1143dbe20cb8a2160abf9e7292aa.
Activation: 2026-10-14T23:38:51.131998+00:00 (2026-10-15 00:38:51 Africa/Lagos).
Role: PILOT. Environment: PROSPECTIVE.
Capture hash: 0925788583bb25885dc41dd8d1ad136db20a0f249cbe04b78866be1ebebf0c91.
Admission hash: 1dbebecd9dbfcd98fd11fe7ec523f7fb024fc849d7128a9e4b1c6a375a0b8c2a.
Publication hash: 43a60407fd92e0e2aa1566f295ab2d1f136f17981b05cff3eaf25c73d92a9f6c.
Contract hash: d9bde76f1aed374e847ed514ea32ab31cfe100ee3c93b8453614d7f2cc6f6125.

Runtime: C:/Users/KiTO/Documents/OMA-CORE-RUNTIME-METRICS51, detached and clean.
Interpreter: C:/Users/KiTO/Documents/OMA-CORE/.venv/Scripts/python.exe.
Script: runtime/scripts/metrics_admission.py; cwd: runtime.
Source binding: C:/Users/KiTO/Documents/O-C data/prospective/metrics-h1-v1.
Admission root: C:/Users/KiTO/Documents/O-C data/prospective/metrics-admission-v1.
Observations binding: admission root/observations.sqlite (not yet created).
Authority and attempts journal exist; no historical observation/publication written.

Task: OMA-CORE-Experiment51-Metrics-Admission; Enabled; Ready; PT5M;
IgnoreNew; PT4M execution limit. Last run 2026-10-14T23:40:05Z, result 0.
Next scheduled run observed: 2026-10-14T23:44:00Z.
Manual smoke and scheduled invocation both NO_ELIGIBLE_BUNDLES.
Last worker completion: 2026-10-14T23:40:10.466015+00:00.
Frozen Metrics capture task definition compared byte-for-byte with its pre-install
XML export: unchanged. Price and SEC runtime/state were read only.

At 2026-10-14T23:40:43Z: 71 valid Metrics captures, current streak 0, longest 12,
23 FAILED, zero MISSED/INCOMPLETE/INVALID. All 71 valid captures PRE_AUTHORITY.
POST_AUTHORITY_VALID_CAPTURES=0
POST_AUTHORITY_ATOMIC_BUNDLES_ADMITTED=0
LATEST_ADMITTED_METRICS_SLOT=null
LATEST_ADMITTED_BUNDLE_ID=null
TAKER_REAL_INPUTS_AVAILABLE=0
MECHANICS_REAL_PATH_ARMED=YES
MECHANICS_REAL_PATH_OBSERVED=NO
METRICS_REAL_READY=NO
MECHANICS_REAL_READY=NO

Independent read-only status at 2026-10-14T23:35:27Z: Price 48 total valid H1,
current contiguous 0, longest 48, ledger integrity PASS; 81H/Regime readiness NO.
SEC: DOCUMENT_FETCH_FAILURE, latest recorded poll 2026-10-14T23:27:15Z,
new documents 1, Event receipts 0, journal integrity PASS. SEC task Enabled/Ready,
last task result 1. This remains a separate operational issue, not remediated here.

RECOVERED_LOCAL_WORK=YES
LAST_REJECTED_EDIT_WAS_PRESENT=NO
METRICS_CHRONOLOGY_FIX_QUALIFIED=YES
METRICS_ADMISSION_V1_IMPLEMENTED=YES
METRICS_ADMISSION_V1_QUALIFIED=YES
METRICS_ADMISSION_AUTHORITY_ACTIVE=YES
METRICS_ADMISSION_RUNTIME_ACTIVE=YES
DISCOVERY_ACTIVATED=NO
EXPERIMENT_51_READY=FALSE
EXPERIMENT_51_EXECUTED=NO
REGIME_VALIDATED=NO
MECHANICS_VALIDATED=NO
POLICY_WINNER=NONE
EDGE=NOT_DEMONSTRATED
REAL_CAPITAL_AUTHORIZED=NO

Result: qualified pipeline armed, waiting for genuinely future SUCCESS evidence.
No waiting for an artificial PASS, no real receipt manufactured, no retrospective
admission. Pending: future complete capture/publication, timely common support,
81H Price and Event evidence. SEC/Price operational failures remain separate.
