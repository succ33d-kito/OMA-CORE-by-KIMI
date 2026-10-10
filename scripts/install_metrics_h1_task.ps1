param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$State,
    [switch]$PlanOnly
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$wrapper = Join-Path $PSScriptRoot 'run_metrics_h1.py'
$taskName = 'OMA-CORE-Prospective-Metrics-H1'
if (![IO.Path]::IsPathRooted($Python) -or !(Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw 'Absolute Python executable required'
}
if (![IO.Path]::IsPathRooted($State)) { throw 'Absolute activated state required' }
foreach ($value in @($Python,$State,$wrapper)) {
    if ($value.Contains('"') -or $value.Contains("`n") -or $value.Contains("`r")) {
        throw 'Unsafe argument path'
    }
}
# The wrapper authenticates frozen design, role, path and complete config.
$output = & $Python $wrapper check --state $State
if ($LASTEXITCODE -ne 0) { throw 'Metrics configuration validation failed' }
$check = ($output | Out-String) | ConvertFrom-Json
if ($check.schema -ne 'metrics-h1-execution-wrapper-v1' -or $check.status -ne 'CONFIG_VERIFIED') {
    throw 'Unexpected validation response'
}
$resolvedState = $check.state
$pythonw = Join-Path (Split-Path $Python -Parent) 'pythonw.exe'
if (!(Test-Path -LiteralPath $pythonw -PathType Leaf)) {
    throw 'Windowless Python executable required'
}
$user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$arguments = "`"$wrapper`" run --state `"$resolvedState`" --allow-public-http"
$plan = [ordered]@{
    schema='metrics-h1-task-plan-v1'; task_name=$taskName; execute=$pythonw
    arguments=$arguments; working_directory=$repoRoot; user=$user; state=$resolvedState
    activation_id=$check.activation_id; trigger='AT_LOGON'; multiple_instances='IGNORE_NEW'
    start_when_available=$true; allow_start_on_batteries=$true; stop_on_battery=$false
    execution_time_limit_seconds=0; restart_count=999; restart_interval_seconds=60
    installer_initializes_state=$false; installer_starts_task=$false
}
if ($PlanOnly) { $plan | ConvertTo-Json -Compress; return }
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw 'Metrics task already exists; no overwrite permitted'
}
$action = New-ScheduledTaskAction -Execute $pythonw -Argument $arguments -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Seconds 60)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal `
    -Settings $settings -Description 'Prospective Metrics H1; pre-activated state; no backfill or same-slot retry.' | Out-Null
Get-ScheduledTask -TaskName $taskName -ErrorAction Stop | Select-Object TaskName,State
