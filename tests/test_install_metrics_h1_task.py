from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest
from core.scientific import metrics_h1_activation as activation

REPO=Path(__file__).resolve().parents[1]
INSTALLER=REPO/'scripts/install_metrics_h1_task.ps1'


def quote(value): return "'"+str(value).replace("'","''")+"'"


@pytest.fixture
def state(tmp_path):
    root=tmp_path/'metrics-h1-v1'
    activation.activate(root,repo_root=REPO,now=datetime(2026,10,10,tzinfo=timezone.utc),dataset_role='PILOT')
    return root


def invoke(state, prefix='', plan=True, windowless_fixture=True):
    shim = r'''function Test-Path { param($LiteralPath,$PathType)
 if ([IO.Path]::GetFileName($LiteralPath) -eq 'pythonw.exe') { return $true }
 return Microsoft.PowerShell.Management\Test-Path -LiteralPath $LiteralPath -PathType $PathType
}
''' if windowless_fixture else ''
    command=shim+prefix+'\n& '+quote(INSTALLER)+' -Python '+quote(sys.executable)+' -State '+quote(state)
    if plan: command+=' -PlanOnly'
    return subprocess.run(['powershell','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-Command',command],
                          capture_output=True,text=True,timeout=30)


def test_plan_executes_real_readonly_check_without_scheduler(state):
    before=(state/'config.json').read_bytes()
    result=invoke(state,"function Get-ScheduledTask { throw 'scheduler must not be inspected' }")
    assert result.returncode==0,result.stderr
    plan=json.loads(result.stdout)
    assert plan['task_name']=='OMA-CORE-Prospective-Metrics-H1'
    assert plan['installer_starts_task'] is False
    assert plan['installer_initializes_state'] is False
    assert plan['restart_count']==999 and plan['multiple_instances']=='IGNORE_NEW'
    assert '--allow-public-http' in plan['arguments']
    assert Path(plan['execute']).name=='pythonw.exe'
    assert list(state.iterdir())==[state/'config.json']
    assert (state/'config.json').read_bytes()==before


def test_existing_task_not_replaced(state):
    result=invoke(state,"function Get-ScheduledTask { return @{TaskName='existing'} }; function Register-ScheduledTask { throw 'MUST_NOT_REGISTER' }",False)
    assert result.returncode!=0
    assert 'already exists' in result.stderr
    assert 'MUST_NOT_REGISTER' not in result.stderr


def test_missing_state_no_initialization(tmp_path):
    root=tmp_path/'metrics-h1-v1'
    result=invoke(root)
    assert result.returncode!=0 and not root.exists()


def test_missing_windowless_interpreter_rejected(state):
    if Path(sys.executable).with_name('pythonw.exe').exists():
        pytest.skip('test interpreter includes pythonw')
    result=invoke(state,windowless_fixture=False)
    assert result.returncode!=0
    assert 'Windowless Python executable required' in result.stderr


def test_registration_uses_frozen_settings_without_start(state):
    # All scheduler commands are replaced inside this isolated PowerShell process.
    mocks=r'''
function Get-ScheduledTask { if ($script:registered) { return @{TaskName='fixture';State='Ready'} } }
function New-ScheduledTaskAction { param($Execute,$Argument,$WorkingDirectory) return @{Execute=$Execute;Argument=$Argument} }
function New-ScheduledTaskTrigger { param([switch]$AtLogOn,$User) if (!$AtLogOn) { throw 'bad trigger' }; return @{} }
function New-ScheduledTaskPrincipal { param($UserId,$LogonType,$RunLevel) if ($RunLevel -ne 'Limited' -or $LogonType -ne 'Interactive') { throw 'bad principal' }; return @{} }
function New-ScheduledTaskSettingsSet {
 param($MultipleInstances,[switch]$StartWhenAvailable,[switch]$AllowStartIfOnBatteries,[switch]$DontStopIfGoingOnBatteries,$ExecutionTimeLimit,$RestartCount,$RestartInterval)
 if ($MultipleInstances -ne 'IgnoreNew' -or !$StartWhenAvailable -or !$AllowStartIfOnBatteries -or !$DontStopIfGoingOnBatteries -or $ExecutionTimeLimit.TotalSeconds -ne 0 -or $RestartCount -ne 999 -or $RestartInterval.TotalSeconds -ne 60) { throw 'bad settings' }
 return @{}
}
function Register-ScheduledTask { param($TaskName,$Action,$Trigger,$Principal,$Settings,$Description)
 if ($TaskName -ne 'OMA-CORE-Prospective-Metrics-H1' -or $Action.Argument -notmatch '--allow-public-http') { throw 'bad registration' }
 $script:registered=$true; Write-Host 'MOCK_REGISTERED'
}
function Start-ScheduledTask { throw 'must never start' }
'''
    result=invoke(state,mocks,False)
    assert result.returncode==0,result.stderr
    assert 'MOCK_REGISTERED' in result.stdout
