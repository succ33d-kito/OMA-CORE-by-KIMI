import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.scientific import funding_h1_activation as activation


UTC = timezone.utc

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_funding_h1.py"


def load_wrapper():
    spec = importlib.util.spec_from_file_location(
        "oma_test_funding_h1_wrapper",
        SCRIPT,
    )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def activated_state(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    parent = tmp_path / "prospective"
    parent.mkdir()

    state = parent / "funding-h1-v1"

    activation.activate(
        state,
        now=datetime(
            2026,
            10,
            10,
            11,
            55,
            tzinfo=UTC,
        ),
        repo_root=repo,
    )

    return state


def test_check_accepts_only_existing_activation(
    tmp_path,
):
    module = load_wrapper()

    state = activated_state(
        tmp_path
    )

    body = module.check_state(
        state
    )

    assert (
        body["schema"]
        == "funding-h1-execution-wrapper-v1"
    )

    assert body["status"] == "READY"

    assert (
        body["activation_slot"]
        == "2026-10-10T13:00:00+00:00"
    )

    assert body["state_initialized"] is False
    assert body["network_executed"] is False


def test_check_command_prints_json(
    tmp_path,
    capsys,
):
    module = load_wrapper()

    state = activated_state(
        tmp_path
    )

    result = module.main([
        "check",
        "--state",
        str(state),
    ])

    assert result == 0

    body = json.loads(
        capsys.readouterr().out
    )

    assert body["status"] == "READY"

    assert (
        body["state"]
        == str(
            state.resolve(
                strict=True
            )
        )
    )


def test_relative_state_rejected():
    module = load_wrapper()

    with pytest.raises(
        ValueError,
        match="absolute state path required",
    ):
        module.validate_state(
            "funding-h1-v1"
        )


def test_missing_state_rejected_without_creation(
    tmp_path,
):
    module = load_wrapper()

    state = (
        tmp_path
        / "funding-h1-v1"
    )

    assert not state.exists()

    with pytest.raises(
        FileNotFoundError,
        match="does not exist",
    ):
        module.validate_state(
            state
        )

    assert not state.exists()


def test_wrong_state_leaf_rejected(
    tmp_path,
):
    module = load_wrapper()

    state = tmp_path / "wrong-leaf"
    state.mkdir()

    with pytest.raises(
        ValueError,
        match="funding-h1-v1",
    ):
        module.validate_state(
            state
        )


def test_state_file_rejected(
    tmp_path,
):
    module = load_wrapper()

    state = (
        tmp_path
        / "funding-h1-v1"
    )

    state.write_text(
        "not directory",
        encoding="utf-8",
    )

    with pytest.raises(
        NotADirectoryError,
        match="must be directory",
    ):
        module.validate_state(
            state
        )


def test_state_inside_repository_rejected(
    tmp_path,
    monkeypatch,
):
    module = load_wrapper()

    repo = tmp_path / "repo"
    repo.mkdir()

    state = (
        repo
        / "funding-h1-v1"
    )
    state.mkdir()

    monkeypatch.setattr(
        module,
        "REPO_ROOT",
        repo,
    )

    with pytest.raises(
        ValueError,
        match="outside repository",
    ):
        module.validate_state(
            state
        )


def test_run_delegates_once(
    tmp_path,
):
    module = load_wrapper()

    state = activated_state(
        tmp_path
    )

    calls = []

    def fake_runtime(root):
        calls.append(
            Path(root)
        )

    result = module.main(
        [
            "run",
            "--state",
            str(state),
        ],
        run_runtime=fake_runtime,
    )

    assert result == 0

    assert calls == [
        state.resolve(
            strict=True
        )
    ]


def test_invalid_run_never_calls_runtime(
    tmp_path,
):
    module = load_wrapper()

    missing = (
        tmp_path
        / "funding-h1-v1"
    )

    calls = []

    def forbidden(root):
        calls.append(root)

    with pytest.raises(
        FileNotFoundError,
    ):
        module.main(
            [
                "run",
                "--state",
                str(missing),
            ],
            run_runtime=forbidden,
        )

    assert calls == []
    assert not missing.exists()