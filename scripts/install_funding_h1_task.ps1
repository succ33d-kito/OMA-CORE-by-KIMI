param(
    [Parameter(Mandatory=$true)]
    [string]$Python,

    [Parameter(Mandatory=$true)]
    [string]$State,

    [switch]$PlanOnly
)

$ErrorActionPreference = 'Stop'

$taskName = 'OMA-CORE-Prospective-Funding-H1'
$requiredLeaf = 'funding-h1-v1'

$repoRoot = Split-Path $PSScriptRoot -Parent
$wrapper = Join-Path $PSScriptRoot 'run_funding_h1.py'
$designPath = Join-Path $repoRoot 'docs\FUNDING_H1_RUNTIME_DESIGN.json'

if (!(Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw 'Python executable missing'
}

if (!(Test-Path -LiteralPath $wrapper -PathType Leaf)) {
    throw 'Funding execution wrapper missing'
}

if (!(Test-Path -LiteralPath $designPath -PathType Leaf)) {
    throw 'Funding runtime design missing'
}

if (![System.IO.Path]::IsPathRooted($State)) {
    throw 'Explicit absolute state path required'
}

if ((Split-Path $State -Leaf) -ne $requiredLeaf) {
    throw 'funding-h1-v1 state leaf required'
}

if (!(Test-Path -LiteralPath $State -PathType Container)) {
    throw 'Pre-activated Funding state directory required'
}

$resolvedState = (
    Resolve-Path -LiteralPath $State
).Path

$resolvedRepo = (
    Resolve-Path -LiteralPath $repoRoot
).Path

$repoPrefix = $resolvedRepo.TrimEnd('\') + '\'

if (
    $resolvedState.StartsWith(
        $repoPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )
) {
    throw 'Funding state must be outside repository'
}

$design = Get-Content `
    -LiteralPath $designPath `
    -Raw |
    ConvertFrom-Json

if ($design.schema -ne 'funding-h1-runtime-design-v2') {
    throw 'Unexpected Funding runtime design schema'
}

if ($design.task_name -ne $taskName) {
    throw 'Unexpected Funding task name'
}

if ($design.activation.authority -ne 'EXPLICIT_OPERATOR_TRANSACTION') {
    throw 'Unexpected activation authority'
}

if ($design.activation.task_installer_may_initialize -ne $false) {
    throw 'Installer initialization authority forbidden'
}

if ($design.runtime.topology -ne 'LONG_RUNNING_AT_LOGON') {
    throw 'Unexpected Funding runtime topology'
}

if ($design.scheduler.trigger -ne 'AT_LOGON') {
    throw 'Unexpected Funding scheduler trigger'
}

if ($design.scheduler.multiple_instances -ne 'IGNORE_NEW') {
    throw 'Unexpected Funding multiple-instance policy'
}

if ($design.scheduler.start_when_available -ne $true) {
    throw 'Unexpected Funding StartWhenAvailable policy'
}

if ($design.scheduler.allow_start_on_batteries -ne $true) {
    throw 'Unexpected Funding battery-start policy'
}

if ($design.scheduler.stop_on_battery -ne $false) {
    throw 'Unexpected Funding battery-stop policy'
}

if ([int]$design.scheduler.execution_time_limit_seconds -ne 0) {
    throw 'Unexpected Funding execution time limit'
}

if ([int]$design.scheduler.restart_count -ne 999) {
    throw 'Unexpected Funding restart count'
}

if ([int]$design.scheduler.restart_interval_seconds -ne 60) {
    throw 'Unexpected Funding restart interval'
}

$checkOutput = & $Python `
    $wrapper `
    check `
    --state `
    $resolvedState

if ($LASTEXITCODE -ne 0) {
    throw 'Funding state validation failed'
}

if (-not $checkOutput) {
    throw 'Funding state validation returned no result'
}

$checkText = (
    $checkOutput |
    Out-String
)

$check = (
    $checkText |
    ConvertFrom-Json
)

if ($check.schema -ne 'funding-h1-execution-wrapper-v1') {
    throw 'Funding state validation schema mismatch'
}

if ($check.status -ne 'READY') {
    throw 'Funding state validation status mismatch'
}

$windowlessPython = Join-Path `
    (Split-Path $Python -Parent) `
    'pythonw.exe'

if (!(Test-Path -LiteralPath $windowlessPython -PathType Leaf)) {
    $windowlessPython = $Python
}

$user = (
    [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
)

$arguments = (
    "`"$wrapper`" run --state `"$resolvedState`""
)

$plan = [ordered]@{
    schema = 'funding-h1-task-plan-v1'
    task_name = $taskName
    execute = $windowlessPython
    arguments = $arguments
    working_directory = $repoRoot
    user = $user
    state = $resolvedState
    trigger = 'AT_LOGON'
    multiple_instances = 'IGNORE_NEW'
    start_when_available = $true
    allow_start_on_batteries = $true
    stop_on_battery = $false
    execution_time_limit_seconds = 0
    restart_count = 999
    restart_interval_seconds = 60
    installer_initializes_state = $false
    installer_starts_task = $false
}

if ($PlanOnly) {
    $plan |
        ConvertTo-Json -Compress

    return
}

$existing = Get-ScheduledTask `
    -TaskName $taskName `
    -ErrorAction SilentlyContinue

if ($existing) {
    throw 'Funding task already exists'
}

$action = New-ScheduledTaskAction `
    -Execute $windowlessPython `
    -Argument $arguments `
    -WorkingDirectory $repoRoot

$trigger = New-ScheduledTaskTrigger `
    -AtLogOn `
    -User $user

$principal = New-ScheduledTaskPrincipal `
    -UserId $user `
    -LogonType Interactive `
    -RunLevel Limited

$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Seconds 60)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description 'Prospective Funding H1 runtime over explicitly activated state; no backfill, no same-slot retry, no Outcome or Learning writes.' |
    Out-Null

$registered = Get-ScheduledTask `
    -TaskName $taskName `
    -ErrorAction Stop

$registered |
    Select-Object TaskName, State