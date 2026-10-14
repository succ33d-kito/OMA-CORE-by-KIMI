param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$QualifiedCommit
)
$ErrorActionPreference = 'Stop'
$TaskName = 'OMA-CORE-Experiment51-Metrics-Admission'
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    throw 'Admission task already exists; no overwrite or duplicate creation'
}
$RuntimePath = Join-Path $env:USERPROFILE 'Documents\OMA-CORE-RUNTIME-METRICS51'
$StateRoot = Join-Path $env:USERPROFILE 'Documents\O-C data\prospective\metrics-admission-v1'
$Python = Join-Path $env:USERPROFILE 'Documents\OMA-CORE\.venv\Scripts\python.exe'
$Script = Join-Path $RuntimePath 'scripts\metrics_admission.py'
$head = & git -C $RuntimePath rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $head -ne $QualifiedCommit) { throw 'Runtime SHA differs from qualified commit' }
& git -C $RuntimePath symbolic-ref -q HEAD | Out-Null
if ($LASTEXITCODE -ne 1) { throw 'Detached runtime required' }
$version = & $Python --version
if ($LASTEXITCODE -ne 0 -or $version -notmatch '^Python 3\.11\.') { throw 'Qualified Python 3.11 required' }
& $Python -B $Script --root $StateRoot status | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Authority status verification failed' }
# :04, :09, ...; source capture remains :03 with its existing :05 deadline.
$now = Get-Date
$next = $now.AddSeconds(-$now.Second).AddMilliseconds(-$now.Millisecond).AddMinutes(1)
while (($next.Minute % 5) -ne 4) { $next = $next.AddMinutes(1) }
$action = New-ScheduledTaskAction -Execute $Python -Argument "-B `"$Script`" --root `"$StateRoot`" once" -WorkingDirectory $RuntimePath
$trigger = New-ScheduledTaskTrigger -Once -At $next -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 4) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName,State
