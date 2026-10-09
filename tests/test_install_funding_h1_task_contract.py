from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SCRIPT = (
    ROOT
    / "scripts"
    / "install_funding_h1_task.ps1"
)


def source():
    return SCRIPT.read_text(
        encoding="utf-8"
    )


def test_explicit_state_and_plan_only():
    value = source()

    assert "[string]$State" in value
    assert "[switch]$PlanOnly" in value

    assert (
        "Explicit absolute state path required"
        in value
    )


def test_never_initializes_state():
    value = source()

    forbidden = (
        "funding_h1_activation",
        "activation.activate",
        "runner.initialize",
        "New-Item",
        "CreateDirectory",
        "mkdir",
    )

    for token in forbidden:
        assert token not in value


def test_never_expands_frozen_template():
    value = source()

    assert "%USERPROFILE%" not in value

    assert (
        "state_root_policy.template"
        not in value
    )


def test_never_forces_or_starts_task():
    value = source()

    assert (
        "Start-ScheduledTask"
        not in value
    )

    assert " -Force" not in value

    assert (
        "installer_starts_task = $false"
        in value
    )


def test_exact_funding_identity():
    value = source()

    assert (
        "OMA-CORE-Prospective-Funding-H1"
        in value
    )

    assert (
        "run_funding_h1.py"
        in value
    )

    assert (
        '"`"$wrapper`" run --state `"$resolvedState`""'
        in value
    )


def test_state_validated_before_registration():
    value = source()

    check = value.index(
        "$checkOutput = & $Python"
    )

    register = value.index(
        "Register-ScheduledTask"
    )

    assert check < register


def test_existing_task_rejected_without_force():
    value = source()

    existing = value.index(
        "$existing = Get-ScheduledTask"
    )

    register = value.index(
        "Register-ScheduledTask"
    )

    assert existing < register

    assert (
        "Funding task already exists"
        in value
    )


def test_frozen_scheduler_settings():
    value = source()

    required = (
        "-AtLogOn",
        "-MultipleInstances IgnoreNew",
        "-StartWhenAvailable",
        "-AllowStartIfOnBatteries",
        "-DontStopIfGoingOnBatteries",
        "-ExecutionTimeLimit ([TimeSpan]::Zero)",
        "-RestartCount 999",
        "-RestartInterval (New-TimeSpan -Seconds 60)",
        "-LogonType Interactive",
        "-RunLevel Limited",
    )

    for token in required:
        assert token in value


def test_plan_only_precedes_registration():
    value = source()

    plan = value.index(
        "if ($PlanOnly)"
    )

    register = value.index(
        "Register-ScheduledTask"
    )

    assert plan < register

    assert (
        "funding-h1-task-plan-v1"
        in value
    )


def test_bound_to_runtime_design():
    value = source()

    required = (
        "funding-h1-runtime-design-v2",
        "EXPLICIT_OPERATOR_TRANSACTION",
        "task_installer_may_initialize",
        "LONG_RUNNING_AT_LOGON",
        "IGNORE_NEW",
    )

    for token in required:
        assert token in value