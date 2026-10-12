# 51-R1 â€” prospective PILOT Price H1 runtime

## Boundary
Implementation complete; full qualification BLOCKED by Windows Code Integrity.
Not yet deployment-ready or published. No real activation, scheduler installation, HTTP
capture or LIVE edits are performed by this implementation mission.

PRICE_ROLE_AWARE_RUNTIME_IMPLEMENTED=YES
PRICE_ROLE_AWARE_RUNTIME_DEPLOYED=NO
PRICE_ROLE_AWARE_RUNTIME_RUNNING=NO
REAL_PRICE_ROLE_ACTIVATION_EXISTS=NO
PRICE_REAL_ATTESTED_H1=0
PRICE_81H_ROLE_WINDOW_READY=NO
51_EXPERIMENT_READINESS=FAIL

The role is explicitly authenticated PILOT, not inferred from path/source/caller.
Existing PriceRoleActivation remains the activation authority. `run`, `check`,
`status` and the installer never initialize activation. State must have the leaf
`price-role-h1-v1`, be absolute and outside Git checkouts, and have no symlink or
reparse components (including runtime-owned files). The separate ledger is
`<state>/observations.db`. Legacy receipts.db and all existing tasks are untouched.

## Flow and timing
For UTC H1 slot S: target **S+5s**, deadline **S+125s**. The unchanged frozen
`capture_price_receipt` receives exact expected_event_time and capture_deadline,
retaining its preflight, server-time, clock and completion/admission checks.

1. Authenticate existing PILOT activation.
2. Persist slot authorization BEFORE invoking capture.
3. Persist immutable CAPTURE_STARTED; invoke the frozen capture callable.
4. Resolve the exact raw Price in the verified ledger, not a caller claim.
5. Attest that exact Price using its pre-created authorization.
6. Reverify with verified_price_role_attestation; only then record SUCCESS.

The evidence claim remains: **authorization strictly precedes earliest persisted
Price capture evidence**. Code also orders authorization before the capture call,
without claiming external proof of a stronger network-start timestamp.

Unlike the legacy retry loop, v1 deliberately allows **one network capture attempt
per slot** (two HTTP requests inside the frozen callable). No failed/ambiguous
attempt is retried. This conservative operational restriction does not change
Price's frozen causal/timing semantics.

## Immutable failures and recovery
Create-only, hash-checked records under `attempts/<UTC slot>/` retain schema,
activation, role, slot, actual time and exact identities. Existing records cannot
be silently overwritten. States: STARTED, AUTHORIZED, CAPTURE_STARTED, CAPTURED,
ATTESTED, SUCCESS, CAPTURE_FAILED, ATTESTATION_FAILED, CONFLICT, MISSED_SLOT.

- Authorization but no capture marker/raw: capture may proceed within live window.
- CAPTURE_STARTED without raw: terminal CAPTURE_FAILED; uncertain request is not retried.
- Raw with valid preauthorization, no attestation: recover that exact raw only,
  without another Price capture; preserve original failure records.
- Raw without valid prior authorization: terminal CONFLICT; no later authorization.
- Exact raw + valid attestation: idempotent, reverified SUCCESS.
- Deadline exhausted without raw: terminal MISSED_SLOT; no backfill.
- Conflicting/tampered/missing committed evidence: fail closed, never repair.

Startup recovery visits persisted raw only, never historical hours for capture.
Raw-only recovery remains bounded by the frozen writer's existing one-day
anti-backfill/age constraint. Expired recovery remains failed. Authorization-only
historical slots are never revisited for capture. Sleep/resume preserves a missed
due slot and schedules the current eligible or next future slot; skipped hours
remain missing. Restart does not duplicate completed cycles.

## Runtime / operator surface
Reuse existing OS lock and atomic metadata primitives. `runtime/runner.lock`
rejects a second runtime; `runtime/slot.lock` also serializes direct slot calls.
Regressions against activation, attempt/ledger timestamps, runtime samples and
restart heartbeat fail closed. Expected capture failures leave future slots eligible.
Heartbeat contains schema, activation ID, status, start/update times, PID and last
slot/result, with heartbeat_is_evidence=false. It is replaceable metadata, never
scientific evidence. A clock failure may prevent heartbeat refresh; stale RUNNING
is not proof of life. Task/PID inspection must independently establish liveness.

`check`/`status`: read-only, no HTTP. Status reverifies raw/attestation pairs, exposes
immutable attempt records and labels liveness UNVERIFIED. Its count is NOT an 81H
certificate. Later use the unchanged 50A exact-window certifier; synthetic tests
never count as real coverage. `run --allow-public-http` requires prior activation.

The separate installer validates qualified Python and activation, refuses task
overwrite, and never activates or starts a task. It uses that venv's pythonw,
logon trigger, IgnoreNew and restart settings. It neither prevents suspension nor
replaces the legacy Price task. All implementation tests use temporary state.

## Deployment commands â€” NOT executed in this mission
Only after successful full qualification, publication and separate user approval, in Windows PowerShell. The prospective parent
must already exist. Never delete/recreate existing activation to retry a failure.

```powershell
$dev = 'C:\Users\KiTO\Documents\OMA-CORE-DEV'
$py = 'C:\Users\KiTO\Documents\OMA-CORE\.venv\Scripts\python.exe'
$state = 'C:\Users\KiTO\Documents\O-C data\prospective\price-role-h1-v1'
$task = 'OMA-CORE-Prospective-Price-Role-H1'
Set-Location -LiteralPath $dev
if ((git branch --show-current) -ne 'manual/51-price-role-runtime-20261012') { throw 'Wrong branch' }
if (git status --porcelain) { throw 'Dirty DEV checkout' }
if (Test-Path -LiteralPath $state) { throw 'State exists: inspect, never overwrite' }

# 1. Explicit create-once activation; existing API samples the real time.
@'
import json, sys
from core.scientific.price_role_activation import activate
print(json.dumps(activate(state_root=sys.argv[1], repo_root=sys.argv[2], dataset_role="PILOT"), sort_keys=True))
'@ | & $py - $state $dev
if ($LASTEXITCODE -ne 0) { throw 'Activation failed; stop' }

# 2. Verify activation; no HTTP.
& $py "$dev\scripts\run_price_role_h1.py" check --state $state
if ($LASTEXITCODE -ne 0) { throw 'Activation check failed' }

# 3. Preview then install a SEPARATE task; neither command starts it.
& "$dev\scripts\install_price_role_h1_task.ps1" -Python $py -State $state -PlanOnly
& "$dev\scripts\install_price_role_h1_task.ps1" -Python $py -State $state

# 4. Explicit start enables future public HTTP capture.
Start-ScheduledTask -TaskName $task

# 5. Task/process and non-evidentiary heartbeat.
Get-ScheduledTask -TaskName $task | Select-Object TaskName,State
Get-ScheduledTaskInfo -TaskName $task
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run_price_role_h1.py*' } |
    Select-Object ProcessId,CreationDate,CommandLine
Get-Content -LiteralPath "$state\runtime\heartbeat.json"

# 6. After the next eligible UTC H1 window, verify exact raw/attestation + SUCCESS.
$report = (& $py "$dev\scripts\run_price_role_h1.py" status --state $state | ConvertFrom-Json)
$report | Select-Object dataset_role,activation_id,ledger_integrity,attested_hours,invalid_raw_ids
$report.verified_pairs | Select-Object -Last 1
$report.attempt_records | Where-Object status -eq 'SUCCESS' | Select-Object -Last 1
```

Missing first success is not permission to retry history. Inspect the immutable
failure and await the next future slot. Do not change/move the DEV checkout used
by a running task without a separately reviewed operational procedure.

## Scientific limits
REGIME_VALIDATED=NO; MECHANICS_VALIDATED=NO; POLICY_WINNER=NONE;
EDGE=NOT_DEMONSTRATED; REAL_CAPITAL_AUTHORIZED=NO.
No trading, outcomes, holdout access or experiments. Real 81H accumulation and 51
readiness remain unproven; the mission ends before real activation.


## Qualification checkpoint - 2026-10-12 (publication blocked)
- Base HEAD: `1bd4ca6f76fe5a62ee450547be6a68d44c105d65`.
- Branch: `manual/51-price-role-runtime-20261012`.
- 42 new deterministic tests plus directly related regressions: **88 passed**.
- `py_compile`: all six new Python files PASS (temporary external bytecode only).
- Installer syntax PASS; installer NOT executed.
- git diff --check / staged diff --check: PASS.
- All five frozen files content-identical to baseline; no existing source edited.
- Full pytest: **7 errors during collection, 9.44s**; no full-suite PASS.
- Isolated `import pandas` reproduces failure without importing new modules.
- Installed pandas metadata: 3.0.6. Windows Code Integrity events 3077/3033 identify
  `C:/Users/KiTO/Documents/OMA-CORE/.venv/Lib/site-packages/pandas/_libs/tslibs/timestamps.cp311-win_amd64.pyd`
  as failing Enterprise signing requirements / policy
  `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`.
- No policy bypass, DLL replacement, environment repair or LIVE edit attempted.
- Real target state absent; new scheduler task absent. Existing Price/Metrics/Funding
  tasks observed Running; none changed. LIVE clean at
  `d9e0f72ec0e1eb897a240a6ecd5820403de039e5`.
- No commits or push: eight additive files staged and preserved for continuation.
- Remote ref for this new branch absent at final read-only ls-remote check.

Resume after the authorized Windows administrator/environment owner resolves the
application-control block through the approved process. First verify isolated
pandas import with the qualified interpreter; then rerun full DEV pytest with
`-q -rs -p no:cacheprovider --basetemp <new external temp directory> --tb=short`.
Do not omit pandas tests or substitute an unqualified interpreter to manufacture
PASS. After qualification create bounded commits and publish only this branch.
Real activation and task installation still need separate user authorization.
