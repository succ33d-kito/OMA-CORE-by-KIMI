# 47W3-2 — Operator activation ceremony

Status: BLOCKED_ENVIRONMENT / UNQUALIFIED / UNPUBLISHED.
Baseline: 426a38ab3721507404663ceb9666628ded66b0b0.
Branch: work/post-cp7l-prep-20261009.

The existing three-file draft was recovered and hardened. All qualified upstream
Funding modules, wrapper, installer and frozen design remain unchanged.

## Implemented boundary (not dynamically qualified)

PLAN samples UTC internally. No public state path or now parameter is accepted.
The canonical root is %USERPROFILE%\Documents\O-C data\prospective\funding-h1-v1.
Existing ancestors and the state root are inspected with lstat for symlinks and
Windows reparse attributes; permission failures propagate. No parent is created.
PLAN reports state/residue existence without changes.

The full plan binds repository root, branch, HEAD, dirty status, activation and
ceremony SHA-256, design identity, sampled UTC, selected slot and capture policy.
ACTIVATE requires the exact confirmation token and a clean, unchanged repository.
It samples UTC internally twice, including after read-only checks, rejects plans
older than 60s, clock regression, changed boundary and loss of 600s lead. Target
+15s, deadline +120s, retry NONE and no backfill remain unchanged. The token is
intentional confirmation, not authentication. No hostile-security or atomic
clock/filesystem/repository guarantee against concurrent changes is claimed.

Design binding verifies the exact Git blob:
23e1f78504448a4fd8a921110e5d7f6a31e88caa
and canonical-JSON SHA-256:
b07a56978b557bbf49bf155834bdb0784b4a382ff0e481dcced3f776e9b0afab
plus explicit activation/capture/state-policy semantics. The supplied SHA is the
canonical JSON digest, not the newline-containing file-byte digest. Checkout bytes
matched the published blob exactly.

ACTIVATE delegates only to the existing create-only primitive. No extra durable
activation receipt was added: atomic inclusion would require changing the
qualified primitive. Preserve the reviewed plan and returned result separately.
No fallible receipt write follows the publication commit point. Do not retry an
ambiguous activation automatically.

Before future real activation independently verify: Funding task absent, Funding
state/residue absent, and Price task XML identity unchanged. Python does not query
or change the scheduler. SCHEDULER_GUARD_LOCAL_VERIFICATION_REQUIRED=YES.

## Qualification and stop

Static compile, AST authority/import checks, exact design digest/blob and file-set
checks passed. No scheduler/network/ledger/learning calls were introduced.

Focal tests stopped at the first fixture setup error, before a test body ran.
One unchanged baseline activation run produced 4 passed, then the same error:
OSError: could not create numbered directory under sandbox AC/Temp/pytest-of-KiTO
after 10 tries. This run did not report WinError 5 directly.
ENVIRONMENT_RESTRICTION_CANDIDATE: shared temporary-filesystem failure.
No retry, alternate test directory, weakened validation or full regression followed.
Wrapper/installer/runtime/Funding/adversarial qualification: NOT RUN.
The adversarial cases added to the test file remain unqualified.

All three draft files remain untracked/uncommitted. No real Funding state, task,
runtime, HTTP capture, ledger write or Price task change occurred.

## Local PowerShell qualification — tests only

Run on the operator host outside the restricted sandbox:

```powershell
Set-Location -LiteralPath 'C:\Users\KiTO\Documents\OMA-CORE'
$py = 'C:\Users\KiTO\AppData\Local\Temp\omacore-audit-2d7b1c9f21d54f708738ee2db11823e3\audit-venv\Scripts\python.exe'
$env:PYTHONDONTWRITEBYTECODE = '1'
& $py -m pytest tests/test_funding_h1_operator_ceremony.py -q -p no:cacheprovider --tb=short
if ($LASTEXITCODE -ne 0) { throw 'STOP: focal qualification failed' }
& $py -m pytest tests/test_funding_h1_activation.py tests/test_funding_h1_operator_ceremony.py tests/test_funding_h1_execution_wrapper.py tests/test_install_funding_h1_task_contract.py tests/test_funding_h1_runtime.py tests/test_funding_h1_live_adapter.py tests/test_funding_h1_runner.py tests/test_funding_continuity.py tests/test_funding_rate_observation.py -q -p no:cacheprovider --tb=short
if ($LASTEXITCODE -ne 0) { throw 'STOP: regression qualification failed' }
& $py -c "from pathlib import Path; [compile(Path(p).read_text(),p,'exec') for p in ('scripts/activate_funding_h1.py','tests/test_funding_h1_operator_ceremony.py')]"
git -c safe.directory=C:/Users/KiTO/Documents/OMA-CORE diff --check
git -c safe.directory=C:/Users/KiTO/Documents/OMA-CORE status --short
```

No commit, push or real activation is authorized by these commands.
EDGE=NOT_DEMONSTRATED; REGIME_VALIDATED=NO; MECHANICS_VALIDATED=NO;
POLICY_WINNER=NONE. Readiness is not Edge.