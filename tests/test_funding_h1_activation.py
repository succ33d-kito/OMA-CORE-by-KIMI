from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.scientific import funding_h1_activation as activation
from core.scientific import funding_h1_runner as runner


UTC = timezone.utc


def dt(hour, minute=0, second=0):
    return datetime(
        2026,
        10,
        10,
        hour,
        minute,
        second,
        tzinfo=UTC,
    )


def roots(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    state_parent = (
        tmp_path
        / "prospective"
    )
    state_parent.mkdir()

    state = (
        state_parent
        / "funding-h1-v1"
    )

    return repo, state


def test_selects_boundary_exactly_at_frozen_lead():
    assert (
        activation.select_activation_slot(
            dt(11, 50)
        )
        == dt(12)
    )


def test_selects_next_boundary_when_threshold_passes_hour():
    assert (
        activation.select_activation_slot(
            dt(11, 55)
        )
        == dt(13)
    )


def test_selection_is_never_less_than_600_seconds():
    now = dt(11, 52, 13)

    selected = (
        activation.select_activation_slot(
            now
        )
    )

    assert (
        selected - now
        >= timedelta(seconds=600)
    )

    assert selected.minute == 0
    assert selected.second == 0
    assert selected.microsecond == 0


def test_naive_activation_clock_rejected():
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        activation.select_activation_slot(
            datetime(
                2026,
                10,
                10,
                12,
                0,
            )
        )


def test_relative_state_root_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    with pytest.raises(
        ValueError,
        match="absolute state root",
    ):
        activation.validate_state_root(
            Path("funding-h1-v1"),
            repo_root=repo,
        )


def test_wrong_state_leaf_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    parent = tmp_path / "prospective"
    parent.mkdir()

    with pytest.raises(
        ValueError,
        match="leaf mismatch",
    ):
        activation.validate_state_root(
            parent / "wrong-name",
            repo_root=repo,
        )


def test_state_inside_repository_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    inside_parent = (
        repo
        / "prospective"
    )
    inside_parent.mkdir()

    with pytest.raises(
        ValueError,
        match="outside repository",
    ):
        activation.validate_state_root(
            inside_parent
            / "funding-h1-v1",
            repo_root=repo,
        )


def test_missing_state_parent_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    state = (
        tmp_path
        / "missing"
        / "funding-h1-v1"
    )

    with pytest.raises(
        ValueError,
        match="parent must already exist",
    ):
        activation.validate_state_root(
            state,
            repo_root=repo,
        )


def test_activation_creates_exact_frozen_runner_state(
    tmp_path,
):
    repo, state = roots(
        tmp_path
    )

    result = activation.activate(
        state,
        now=dt(11, 55),
        repo_root=repo,
    )

    assert result == {
        "schema":
            "funding-h1-activation-v1",
        "status":
            "ACTIVATED",
        "observed_at":
            dt(11, 55).isoformat(),
        "activation_slot":
            dt(13).isoformat(),
        "minimum_lead_seconds":
            600,
        "state_root":
            str(state.resolve()),
    }

    config = runner.load_config(
        state
    )

    assert (
        config["activation_slot"]
        == dt(13).isoformat()
    )

    assert (
        config["retry_policy"]
        == "NONE"
    )

    assert (
        config["target_offset_seconds"]
        == 15
    )

    assert (
        config["slot_deadline_seconds"]
        == 120
    )

    assert (
        state
        / "attempts"
    ).is_dir()

    assert list(
        (
            state
            / "attempts"
        ).iterdir()
    ) == []


def test_activation_has_no_staging_residue(
    tmp_path,
):
    repo, state = roots(
        tmp_path
    )

    activation.activate(
        state,
        now=dt(11, 55),
        repo_root=repo,
    )

    leftovers = list(
        state.parent.glob(
            ".funding-h1-v1.activating-*"
        )
    )

    assert leftovers == []


def test_existing_empty_root_is_rejected(
    tmp_path,
):
    repo, state = roots(
        tmp_path
    )

    state.mkdir()

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        activation.activate(
            state,
            now=dt(11, 55),
            repo_root=repo,
        )

    assert list(
        state.iterdir()
    ) == []


def test_existing_configured_state_is_never_reactivated(
    tmp_path,
):
    repo, state = roots(
        tmp_path
    )

    runner.initialize(
        state,
        dt(13),
    )

    before = (
        state
        / "config.json"
    ).read_bytes()

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        activation.activate(
            state,
            now=dt(12),
            repo_root=repo,
        )

    after = (
        state
        / "config.json"
    ).read_bytes()

    assert after == before

    assert (
        runner.activation_slot(
            state
        )
        == dt(13)
    )


def test_initialize_failure_leaves_no_final_root(
    tmp_path,
    monkeypatch,
):
    repo, state = roots(
        tmp_path
    )

    def broken_initialize(path, slot):
        path.mkdir()

        (
            path
            / "partial.txt"
        ).write_text(
            "partial",
            encoding="utf-8",
        )

        raise RuntimeError(
            "simulated initialization crash"
        )

    monkeypatch.setattr(
        activation.runner,
        "initialize",
        broken_initialize,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated initialization crash",
    ):
        activation.activate(
            state,
            now=dt(11, 55),
            repo_root=repo,
        )

    assert not state.exists()

    assert list(
        state.parent.glob(
            ".funding-h1-v1.activating-*"
        )
    ) == []


def test_publication_failure_cleans_staging(
    tmp_path,
    monkeypatch,
):
    repo, state = roots(
        tmp_path
    )

    def broken_replace(source, destination):
        raise OSError(
            "simulated atomic publication failure"
        )

    monkeypatch.setattr(
        activation.os,
        "replace",
        broken_replace,
    )

    with pytest.raises(
        OSError,
        match="publication failure",
    ):
        activation.activate(
            state,
            now=dt(11, 55),
            repo_root=repo,
        )

    assert not state.exists()

    assert list(
        state.parent.glob(
            ".funding-h1-v1.activating-*"
        )
    ) == []


def test_activation_does_not_create_capture_artifacts(
    tmp_path,
):
    repo, state = roots(
        tmp_path
    )

    activation.activate(
        state,
        now=dt(11, 55),
        repo_root=repo,
    )

    assert not list(
        state.rglob("capture")
    )

    assert not list(
        state.rglob("result.json")
    )

    assert not list(
        state.rglob("attempt.json")
    )

def test_missing_repository_root_rejected(
    tmp_path,
):
    parent = tmp_path / "prospective"
    parent.mkdir()

    state = (
        parent
        / "funding-h1-v1"
    )

    missing_repo = (
        tmp_path
        / "repo-missing"
    )

    with pytest.raises(
        ValueError,
        match="repository root must exist",
    ):
        activation.validate_state_root(
            state,
            repo_root=missing_repo,
        )


def test_repository_root_file_rejected(
    tmp_path,
):
    repo = tmp_path / "repo-file"

    repo.write_text(
        "not a directory",
        encoding="utf-8",
    )

    parent = tmp_path / "prospective"
    parent.mkdir()

    state = (
        parent
        / "funding-h1-v1"
    )

    with pytest.raises(
        ValueError,
        match="repository root must be directory",
    ):
        activation.validate_state_root(
            state,
            repo_root=repo,
        )


def test_no_fallible_verification_after_atomic_publication(
    tmp_path,
    monkeypatch,
):
    repo, state = roots(
        tmp_path
    )

    original = (
        activation.runner.load_config
    )

    calls = {
        "value": 0,
    }

    def fail_second_read(path):
        calls["value"] += 1

        if calls["value"] == 2:
            raise RuntimeError(
                "post-publication read must not occur"
            )

        return original(path)

    monkeypatch.setattr(
        activation.runner,
        "load_config",
        fail_second_read,
    )

    result = activation.activate(
        state,
        now=dt(11, 55),
        repo_root=repo,
    )

    assert (
        result["status"]
        == "ACTIVATED"
    )

    assert calls["value"] == 1
    assert state.is_dir()

    config = original(
        state
    )

    assert (
        config["activation_slot"]
        == dt(13).isoformat()
    )


def test_stale_activation_residue_blocks_new_activation(
    tmp_path,
):
    repo, state = roots(
        tmp_path
    )

    stale = (
        state.parent
        / ".funding-h1-v1.activating-stale"
    )

    stale.mkdir()

    (
        stale
        / "partial.txt"
    ).write_text(
        "preserved interrupted activation",
        encoding="utf-8",
    )

    with pytest.raises(
        FileExistsError,
        match="stale funding activation staging residue",
    ):
        activation.activate(
            state,
            now=dt(11, 55),
            repo_root=repo,
        )

    assert not state.exists()

    assert (
        stale
        / "partial.txt"
    ).read_text(
        encoding="utf-8"
    ) == "preserved interrupted activation"


def test_cleanup_failure_is_not_hidden(
    tmp_path,
    monkeypatch,
):
    repo, state = roots(
        tmp_path
    )

    def broken_initialize(
        path,
        slot,
    ):
        path.mkdir()

        (
            path
            / "partial.txt"
        ).write_text(
            "partial",
            encoding="utf-8",
        )

        raise RuntimeError(
            "simulated initialization failure"
        )

    def broken_cleanup(path):
        raise OSError(
            "simulated cleanup failure"
        )

    monkeypatch.setattr(
        activation.runner,
        "initialize",
        broken_initialize,
    )

    monkeypatch.setattr(
        activation.shutil,
        "rmtree",
        broken_cleanup,
    )

    with pytest.raises(
        OSError,
        match="simulated cleanup failure",
    ):
        activation.activate(
            state,
            now=dt(11, 55),
            repo_root=repo,
        )

    assert not state.exists()

    leftovers = list(
        state.parent.glob(
            ".funding-h1-v1.activating-*"
        )
    )

    assert len(leftovers) == 1