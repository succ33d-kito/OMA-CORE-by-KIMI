param(
    [Parameter(Mandatory=$true)][string]$Python,
    [string]$Ledger = 'C:\Users\KiTO\Documents\O-C data\prospective\receipts.db',
    [string]$State = 'C:\Users\KiTO\Documents\O-C data\prospective\continuous',
    [string]$TaskName = 'OMA-CORE-Prospective-Price-H1'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$runner = Join-Path $PSScriptRoot 'capture_price_h1.py'
if (!(Test-Path -LiteralPath $Python)) { throw 'Python executable missing' }
& $Python -c 'import requests'
if ($LASTEXITCODE -ne 0) { throw 'Selected Python needs requests' }
$windowlessPython = Join-Path (Split-Path $Python -Parent) 'pythonw.exe'
if (!(Test-Path -LiteralPath $windowlessPython)) { $windowlessPython = $Python }
$action = New-ScheduledTaskAction -Execute $windowlessPython -Argument "`"$runner`" run --ledger `"$Ledger`" --state `"$State`"" -WorkingDirectory $repoRoot
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Prospective Binance H1 Price receipts only; no backfill, outcomes or trading.' -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName,State
