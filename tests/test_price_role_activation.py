from pathlib import Path
from datetime import datetime, timedelta, timezone
import json

import pytest

import core.scientific.price_role_activation as activation
from core.scientific.price_role_activation import (
    activate,
    build_activation,
    load_activation,
)


T = datetime(
    2026,
    10,
    11,
    18,
    0,
    tzinfo=timezone.utc,
)


def test_price_role_activation_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(activation, "_now", lambda: T)
    repo = Path(__file__).resolve().parents[1]
    state = tmp_path / "price-role-pilot"

    result = activate(
        state_root=state,
        repo_root=repo,
        dataset_role="PILOT",
    )

    loaded = load_activation(
        state,
        repo_root=repo,
    )

    assert loaded == result
    assert loaded["dataset_role"] == "PILOT"
    assert loaded["not_before"] == T.isoformat()


@pytest.mark.parametrize(
    "role",
    ["pilot", "", None, False, 42],
)
def test_invalid_price_role_fails_closed(tmp_path, role):
    repo = Path(__file__).resolve().parents[1]

    with pytest.raises(ValueError):
        build_activation(
            state_root=tmp_path / "activation",
            repo_root=repo,
            observed_at=T,
            dataset_role=role,
        )


def test_activation_is_create_only(tmp_path, monkeypatch):
    monkeypatch.setattr(activation, "_now", lambda: T)
    repo = Path(__file__).resolve().parents[1]
    state = tmp_path / "price-role-pilot"

    activate(
        state_root=state,
        repo_root=repo,
        dataset_role="PILOT",
    )

    with pytest.raises(FileExistsError):
        activate(
            state_root=state,
            repo_root=repo,
            dataset_role="DISCOVERY",
        )


def test_activation_tampering_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(activation, "_now", lambda: T)
    repo = Path(__file__).resolve().parents[1]
    state = tmp_path / "price-role-pilot"

    activate(
        state_root=state,
        repo_root=repo,
        dataset_role="PILOT",
    )

    path = state / "config.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    body["dataset_role"] = "DISCOVERY"

    path.write_text(
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_activation(
            state,
            repo_root=repo,
        )


def test_operational_activation_has_no_caller_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(activation, "_now", lambda: T)

    repo = Path(__file__).resolve().parents[1]
    state = tmp_path / "price-role-pilot"

    with pytest.raises(TypeError):
        activate(
            state_root=state,
            repo_root=repo,
            dataset_role="PILOT",
            observed_at=T - timedelta(days=1),
        )

    assert not state.exists()
