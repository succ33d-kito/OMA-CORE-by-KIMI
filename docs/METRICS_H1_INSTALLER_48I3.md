# 48I.3 — create-only scheduler installer

`scripts/install_metrics_h1_task.ps1 -Python <absolute python.exe> -State
<activated metrics-h1-v1> -PlanOnly` validates config and emits the task plan.
Without PlanOnly it registers only `OMA-CORE-Prospective-Metrics-H1`, refusing an
existing task. It never starts the task or initializes state. Logon will start
the registered runtime. Requires matching pythonw.exe beside the qualified Python.

Frozen settings: interactive limited principal, logon trigger, IgnoreNew,
StartWhenAvailable, battery permitted, unlimited execution, 999 restart attempts
at 60 seconds. No keep-awake, backfill or old-slot retry. The authenticated wrapper
check validates the frozen design before either planning or registration.

Tests invoke real PowerShell and the real read-only Python checker on temporary
synthetic state. Scheduler commands are mocked for registration tests; no actual
task is created. Tests simulate pythonw presence for scheduler qualification and
separately verify rejection when it is absent. Script execution permission is
process-local to the test subprocess; no persistent policy is changed.
Deployment must separately verify interpreter dependencies,
task action, actual process, first complete bundle and persisted continuity.
Requests inactivity timeouts still do not guarantee a hard total duration.

CODE_READY does not imply DEPLOYED, LIVE_CAPTURE_VERIFIED or 81H readiness.
