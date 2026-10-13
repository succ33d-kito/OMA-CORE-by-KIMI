param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$RuntimeRepo,
    [Parameter(Mandatory=$true)][string]$StateRoot
)
$ErrorActionPreference = 'Stop'
$name = 'OMA-CORE-Experiment51-SEC-Event-Discovery'
$pythonPath = (Resolve-Path -LiteralPath $Python).Path
$repoPath = (Resolve-Path -LiteralPath $RuntimeRepo).Path
$statePath = (Resolve-Path -LiteralPath $StateRoot).Path
$scriptPath = (Resolve-Path -LiteralPath (Join-Path $repoPath 'scripts/sec_event_discovery.py')).Path
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) { throw 'Task already exists; inspect, do not overwrite or duplicate.' }
$statusJson = & $pythonPath -B $scriptPath --root $statePath status
if ($LASTEXITCODE -ne 0) { throw 'Discovery status verification failed.' }
$status = $statusJson | ConvertFrom-Json
if (-not $status.baseline_established -or $status.integrity -ne 'PASS' -or $status.role -ne 'PILOT') { throw 'Successful PILOT watermark required.' }
$arguments = '-B "{0}" --root "{1}" poll' -f $scriptPath, $statePath
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $arguments -WorkingDirectory $repoPath
$trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(5)) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 4) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'SEC scope-frozen PILOT discovery; 5-minute polls; no outcomes, no auto-attestation.' | Out-Null
Get-ScheduledTask -TaskName $name | Select-Object TaskName,State,Actions,Triggers,Settings
Get-ScheduledTaskInfo -TaskName $name | Select-Object LastRunTime,NextRunTime,LastTaskResult
