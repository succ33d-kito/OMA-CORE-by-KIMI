import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.scientific import funding_h1_activation as activation
from core.scientific import funding_h1_runtime as runtime


UTC = timezone.utc


def dt(
    hour,
    minute=0,
    second=0,
):
    return datetime(
        2026,
        10,
        10,
        hour,
        minute,
        second,
        tzinfo=UTC,
    )


def activated_state(tmp_path):
    repo = (
        tmp_path
        / "repo"
    )
    repo.mkdir()

    parent = (
        tmp_path
        / "prospective"
    )
    parent.mkdir()

    state = (
        parent
        / "funding-h1-v1"
    )

    activation.activate(
        state,
        now=dt(11, 55),
        repo_root=repo,
    )

    return (
        repo,
        state,
    )


class TickClock:
    def __init__(
        self,
        start,
        *,
        seconds=1,
    ):
        self.value = start
        self.step = timedelta(
            seconds=seconds
        )

    def __call__(self):
        value = self.value

        self.value = (
            self.value
            + self.step
        )

        return value


def test_runtime_requires_preexisting_activation(
    tmp_path,
):
    state = (
        tmp_path
        / "funding-h1-v1"
    )

    with pytest.raises(
        FileNotFoundError,
    ):
        runtime.run_forever(
            state,
            clock=TickClock(
                dt(12)
            ),
            sleeper=lambda value: None,
            run_once_callable=(
                lambda state, *, clock:
                    {}
            ),
            max_iterations=1,
        )

    assert not state.exists()


def test_runtime_never_initializes_missing_state(
    tmp_path,
):
    state = (
        tmp_path
        / "funding-h1-v1"
    )

    assert not state.exists()

    with pytest.raises(
        FileNotFoundError,
    ):
        runtime.run_forever(
            state,
            clock=TickClock(
                dt(12)
            ),
            sleeper=lambda value: None,
            run_once_callable=(
                lambda state, *, clock:
                    {
                        "status":
                            "NOT_DUE",
                    }
            ),
            max_iterations=1,
        )

    assert not state.exists()


def test_two_iterations_write_non_evidentiary_heartbeat(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    calls = []
    sleeps = []

    def fake_run_once(
        root,
        *,
        clock,
    ):
        calls.append(
            Path(root)
        )

        return {
            "status":
                "NOT_DUE",
            "slot":
                dt(13).isoformat(),
        }

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12)
        ),
        sleeper=sleeps.append,
        run_once_callable=fake_run_once,
        poll_seconds=5,
        max_iterations=2,
    )

    assert result[
        "status"
    ] == "STOPPED"

    assert result[
        "iterations"
    ] == 2

    assert len(calls) == 2

    assert sleeps == [
        5.0,
    ]

    heartbeat = json.loads(
        (
            state
            / "runtime"
            / "heartbeat.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        heartbeat["schema"]
        == "funding-h1-runtime-heartbeat-v1"
    )

    assert (
        heartbeat[
            "heartbeat_is_evidence"
        ]
        is False
    )

    assert (
        heartbeat["status"]
        == "STOPPED"
    )

    assert (
        heartbeat["iterations"]
        == 2
    )

    assert (
        heartbeat[
            "last_adapter_status"
        ]
        == "NOT_DUE"
    )

    assert (
        heartbeat["last_slot"]
        == dt(13).isoformat()
    )


def test_runtime_metadata_does_not_create_attempt(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    runtime.run_forever(
        state,
        clock=TickClock(
            dt(12)
        ),
        sleeper=lambda value: None,
        run_once_callable=(
            lambda root, *, clock:
                {
                    "status":
                        "NOT_DUE",
                    "slot":
                        dt(13).isoformat(),
                }
        ),
        max_iterations=1,
    )

    attempts = (
        state
        / "attempts"
    )

    assert list(
        attempts.iterdir()
    ) == []

    assert (
        state
        / "runtime"
        / "heartbeat.json"
    ).is_file()

    assert (
        state
        / "runtime"
        / "runner.lock"
    ).is_file()


def test_process_lock_rejects_second_runtime(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    runtime_dir = (
        state
        / "runtime"
    )
    runtime_dir.mkdir()

    lock_path = (
        runtime_dir
        / "runner.lock"
    )

    with runtime._process_lock(
        lock_path
    ):
        with pytest.raises(
            RuntimeError,
            match="already locked",
        ):
            runtime.run_forever(
                state,
                clock=TickClock(
                    dt(12)
                ),
                sleeper=lambda value: None,
                run_once_callable=(
                    lambda root, *, clock:
                        {
                            "status":
                                "NOT_DUE",
                        }
                ),
                max_iterations=1,
            )


def test_sequential_restart_can_reacquire_lock(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    def fake(
        root,
        *,
        clock,
    ):
        return {
            "status":
                "NOT_DUE",
            "slot":
                dt(13).isoformat(),
        }

    first = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12)
        ),
        sleeper=lambda value: None,
        run_once_callable=fake,
        max_iterations=1,
    )

    second = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 1)
        ),
        sleeper=lambda value: None,
        run_once_callable=fake,
        max_iterations=1,
    )

    assert (
        first["iterations"]
        == 1
    )

    assert (
        second["iterations"]
        == 1
    )


def test_clock_regression_fails_closed(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    samples = iter(
        [
            dt(12, 0, 1),
            dt(12, 0, 2),
            dt(12, 0, 1),
        ]
    )

    def clock():
        return next(samples)

    def fake_run_once(
        root,
        *,
        clock,
    ):
        clock()

        return {
            "status":
                "NOT_DUE",
        }

    with pytest.raises(
        ValueError,
        match="clock moved backwards",
    ):
        runtime.run_forever(
            state,
            clock=clock,
            sleeper=lambda value: None,
            run_once_callable=fake_run_once,
            max_iterations=1,
        )

    attempts = (
        state
        / "attempts"
    )

    assert list(
        attempts.iterdir()
    ) == []


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
        5.0001,
        6,
    ],
)
def test_poll_interval_outside_frozen_bound_rejected(
    tmp_path,
    value,
):
    _, state = activated_state(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="<= 5",
    ):
        runtime.run_forever(
            state,
            clock=TickClock(
                dt(12)
            ),
            sleeper=lambda seconds: None,
            run_once_callable=(
                lambda root, *, clock:
                    {
                        "status":
                            "NOT_DUE",
                    }
            ),
            poll_seconds=value,
            max_iterations=1,
        )


def test_adapter_result_requires_status(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="status missing",
    ):
        runtime.run_forever(
            state,
            clock=TickClock(
                dt(12)
            ),
            sleeper=lambda seconds: None,
            run_once_callable=(
                lambda root, *, clock:
                    {
                        "slot":
                            dt(13).isoformat(),
                    }
            ),
            max_iterations=1,
        )


def test_pre_requested_stop_performs_no_adapter_call(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    calls = []

    def fake(
        root,
        *,
        clock,
    ):
        calls.append(root)

        return {
            "status":
                "NOT_DUE",
        }

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12)
        ),
        sleeper=lambda seconds: None,
        run_once_callable=fake,
        stop_requested=lambda: True,
    )

    assert calls == []

    assert (
        result["iterations"]
        == 0
    )

    heartbeat = json.loads(
        (
            state
            / "runtime"
            / "heartbeat.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        heartbeat["status"]
        == "STOPPED"
    )


def test_runtime_uses_injected_adapter_without_network(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    seen = []

    def fake(
        root,
        *,
        clock,
    ):
        seen.append(
            (
                Path(root),
                clock(),
            )
        )

        return {
            "status":
                "EXISTING_NOOP",
            "slot":
                dt(13).isoformat(),
        }

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12)
        ),
        sleeper=lambda seconds: None,
        run_once_callable=fake,
        max_iterations=1,
    )

    assert len(seen) == 1

    assert (
        result[
            "last_adapter_status"
        ]
        == "EXISTING_NOOP"
    )

class RestartManualClock:
    def __init__(
        self,
        value,
    ):
        self.value = value

    def __call__(self):
        return self.value

    def advance(
        self,
        seconds,
    ):
        self.value += timedelta(
            seconds=seconds
        )


def test_restart_clock_regression_fails_closed_and_preserves_anchor(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    first = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 0, 30)
        ),
        sleeper=lambda value: None,
        run_once_callable=(
            lambda root, *, clock:
                {
                    "status":
                        "NOT_DUE",
                    "slot":
                        dt(13).isoformat(),
                }
        ),
        max_iterations=1,
    )

    heartbeat_path = (
        state
        / "runtime"
        / "heartbeat.json"
    )

    before = (
        heartbeat_path.read_bytes()
    )

    anchor = datetime.fromisoformat(
        first["stopped_at"]
    )

    regressed = (
        anchor
        - timedelta(seconds=20)
    )

    with pytest.raises(
        ValueError,
        match=(
            "clock moved backwards "
            "across restart"
        ),
    ):
        runtime.run_forever(
            state,
            clock=TickClock(
                regressed
            ),
            sleeper=lambda value: None,
            run_once_callable=(
                lambda root, *, clock:
                    {
                        "status":
                            "NOT_DUE",
                    }
            ),
            max_iterations=1,
        )

    after = (
        heartbeat_path.read_bytes()
    )

    assert after == before

    assert list(
        (
            state
            / "attempts"
        ).iterdir()
    ) == []


def test_stopped_timestamp_samples_clock_after_final_wait(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    clock = RestartManualClock(
        dt(12, 0, 30)
    )

    stop_calls = {
        "value": 0,
    }

    def stop_requested():
        stop_calls[
            "value"
        ] += 1

        return (
            stop_calls["value"]
            >= 3
        )

    def sleeper(seconds):
        clock.advance(
            seconds
        )

    result = runtime.run_forever(
        state,
        clock=clock,
        sleeper=sleeper,
        run_once_callable=(
            lambda root, *, clock:
                {
                    "status":
                        "NOT_DUE",
                    "slot":
                        dt(13).isoformat(),
                }
        ),
        poll_seconds=5,
        stop_requested=
            stop_requested,
    )

    stopped_at = datetime.fromisoformat(
        result["stopped_at"]
    )

    assert stopped_at == clock.value

    heartbeat = json.loads(
        (
            state
            / "runtime"
            / "heartbeat.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        datetime.fromisoformat(
            heartbeat["updated_at"]
        )
        == clock.value
    )

    assert (
        heartbeat["status"]
        == "STOPPED"
    )

    assert (
        heartbeat[
            "heartbeat_is_evidence"
        ]
        is False
    )

def _write_anchor_test_heartbeat(
    state,
    *,
    started_at,
    updated_at,
    status="STOPPED",
):
    runtime_dir = (
        state
        / "runtime"
    )

    runtime_dir.mkdir(
        exist_ok=True
    )

    value = {
        "schema":
            runtime.HEARTBEAT_SCHEMA,

        "runtime_schema":
            runtime.RUNTIME_SCHEMA,

        "status":
            status,

        "started_at":
            started_at.isoformat(),

        "updated_at":
            updated_at.isoformat(),

        "iterations":
            1,

        "heartbeat_is_evidence":
            False,

        "pid":
            123,

        "last_adapter_status":
            "NOT_DUE",

        "last_slot":
            dt(13).isoformat(),
    }

    (
        runtime_dir
        / "heartbeat.json"
    ).write_text(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def test_invalid_heartbeat_status_does_not_become_clock_anchor(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    _write_anchor_test_heartbeat(
        state,
        started_at=dt(22),
        updated_at=dt(23),
        status="GARBAGE",
    )

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 0, 30)
        ),
        sleeper=lambda value: None,
        run_once_callable=(
            lambda root, *, clock:
                {
                    "status":
                        "NOT_DUE",
                    "slot":
                        dt(13).isoformat(),
                }
        ),
        max_iterations=1,
    )

    assert result[
        "iterations"
    ] == 1

    heartbeat = json.loads(
        (
            state
            / "runtime"
            / "heartbeat.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        heartbeat["status"]
        == "STOPPED"
    )


def test_impossible_heartbeat_chronology_does_not_become_clock_anchor(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    _write_anchor_test_heartbeat(
        state,
        started_at=dt(23),
        updated_at=dt(22),
        status="STOPPED",
    )

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 0, 30)
        ),
        sleeper=lambda value: None,
        run_once_callable=(
            lambda root, *, clock:
                {
                    "status":
                        "NOT_DUE",
                    "slot":
                        dt(13).isoformat(),
                }
        ),
        max_iterations=1,
    )

    assert result[
        "iterations"
    ] == 1


def test_missing_heartbeat_status_does_not_become_clock_anchor(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    _write_anchor_test_heartbeat(
        state,
        started_at=dt(22),
        updated_at=dt(23),
        status="STOPPED",
    )

    path = (
        state
        / "runtime"
        / "heartbeat.json"
    )

    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    del value[
        "status"
    ]

    path.write_text(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 0, 30)
        ),
        sleeper=lambda value: None,
        run_once_callable=(
            lambda root, *, clock:
                {
                    "status":
                        "NOT_DUE",
                    "slot":
                        dt(13).isoformat(),
                }
        ),
        max_iterations=1,
    )

    assert result[
        "iterations"
    ] == 1

def _write_writer_state_heartbeat(
    state,
    *,
    status,
    started_at,
    updated_at,
    iterations,
    last_adapter_status,
    last_slot,
):
    runtime_dir = (
        state
        / "runtime"
    )

    runtime_dir.mkdir(
        exist_ok=True
    )

    value = {
        "schema":
            runtime.HEARTBEAT_SCHEMA,

        "runtime_schema":
            runtime.RUNTIME_SCHEMA,

        "status":
            status,

        "started_at":
            started_at.isoformat(),

        "updated_at":
            updated_at.isoformat(),

        "iterations":
            iterations,

        "heartbeat_is_evidence":
            False,

        "pid":
            123,

        "last_adapter_status":
            last_adapter_status,

        "last_slot":
            last_slot,
    }

    (
        runtime_dir
        / "heartbeat.json"
    ).write_text(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def _harmless_runtime_adapter(
    root,
    *,
    clock,
):
    return {
        "status":
            "NOT_DUE",

        "slot":
            dt(13).isoformat(),
    }


def test_valid_started_heartbeat_is_restart_clock_anchor(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    anchor = dt(
        12,
        0,
        30,
    )

    _write_writer_state_heartbeat(
        state,
        status="STARTED",
        started_at=anchor,
        updated_at=anchor,
        iterations=0,
        last_adapter_status=None,
        last_slot=None,
    )

    before = (
        state
        / "runtime"
        / "heartbeat.json"
    ).read_bytes()

    with pytest.raises(
        ValueError,
        match=(
            "clock moved backwards "
            "across restart"
        ),
    ):
        runtime.run_forever(
            state,
            clock=TickClock(
                anchor
                - timedelta(
                    seconds=1
                )
            ),
            sleeper=lambda value: None,
            run_once_callable=
                _harmless_runtime_adapter,
            max_iterations=1,
        )

    after = (
        state
        / "runtime"
        / "heartbeat.json"
    ).read_bytes()

    assert after == before


def test_started_heartbeat_requires_exact_start_update_timestamp(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    _write_writer_state_heartbeat(
        state,
        status="STARTED",
        started_at=dt(22),
        updated_at=dt(23),
        iterations=0,
        last_adapter_status=None,
        last_slot=None,
    )

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 0, 30)
        ),
        sleeper=lambda value: None,
        run_once_callable=
            _harmless_runtime_adapter,
        max_iterations=1,
    )

    assert result[
        "iterations"
    ] == 1


def test_running_zero_iterations_cannot_have_previous_result(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    _write_writer_state_heartbeat(
        state,
        status="RUNNING",
        started_at=dt(22),
        updated_at=dt(23),
        iterations=0,
        last_adapter_status="NOT_DUE",
        last_slot=dt(13).isoformat(),
    )

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 0, 30)
        ),
        sleeper=lambda value: None,
        run_once_callable=
            _harmless_runtime_adapter,
        max_iterations=1,
    )

    assert result[
        "iterations"
    ] == 1


def test_running_positive_iterations_require_adapter_status(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    _write_writer_state_heartbeat(
        state,
        status="RUNNING",
        started_at=dt(22),
        updated_at=dt(23),
        iterations=2,
        last_adapter_status=None,
        last_slot=None,
    )

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 0, 30)
        ),
        sleeper=lambda value: None,
        run_once_callable=
            _harmless_runtime_adapter,
        max_iterations=1,
    )

    assert result[
        "iterations"
    ] == 1


def test_stopped_zero_iterations_cannot_have_previous_result(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    _write_writer_state_heartbeat(
        state,
        status="STOPPED",
        started_at=dt(22),
        updated_at=dt(23),
        iterations=0,
        last_adapter_status="NOT_DUE",
        last_slot=dt(13).isoformat(),
    )

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 0, 30)
        ),
        sleeper=lambda value: None,
        run_once_callable=
            _harmless_runtime_adapter,
        max_iterations=1,
    )

    assert result[
        "iterations"
    ] == 1


def test_stopped_positive_iterations_require_adapter_status(
    tmp_path,
):
    _, state = activated_state(
        tmp_path
    )

    _write_writer_state_heartbeat(
        state,
        status="STOPPED",
        started_at=dt(22),
        updated_at=dt(23),
        iterations=2,
        last_adapter_status=None,
        last_slot=None,
    )

    result = runtime.run_forever(
        state,
        clock=TickClock(
            dt(12, 0, 30)
        ),
        sleeper=lambda value: None,
        run_once_callable=
            _harmless_runtime_adapter,
        max_iterations=1,
    )

    assert result[
        "iterations"
    ] == 1