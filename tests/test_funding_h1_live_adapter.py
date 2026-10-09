from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import core.scientific.funding_continuity as fc
import core.scientific.funding_h1_live_adapter as adapter
import core.scientific.funding_h1_runner as runner


T = datetime(
    2026,
    10,
    10,
    0,
    0,
    0,
    tzinfo=timezone.utc,
)


class Clock:
    def __init__(self, *values):
        self.values = list(values)

    def __call__(self):
        if not self.values:
            raise AssertionError(
                "clock exhausted"
            )

        return self.values.pop(0)


def observation(
    slot,
    *,
    request_offset=32,
    received_offset=33,
    available_offset=34,
    receipt_id=None,
):
    if receipt_id is None:
        receipt_id = (
            "receipt-"
            + fc.slot_id(slot)
        )

    receipt = SimpleNamespace(
        receipt_id=receipt_id,
        request_started_at=(
            slot
            + timedelta(
                seconds=request_offset
            )
        ),
        received_at=(
            slot
            + timedelta(
                seconds=received_offset
            )
        ),
        available_at=(
            slot
            + timedelta(
                seconds=available_offset
            )
        ),
    )

    return SimpleNamespace(
        instrument=fc.INSTRUMENT,
        venue=fc.VENUE,
        product=fc.PRODUCT,
        dataset_role=SimpleNamespace(
            value=fc.ROLE
        ),
        decision_at=receipt.available_at,
        receipts=(receipt,),
    )


def fake_success(
    slot,
    calls,
):
    obs = observation(slot)

    def capture(
        path,
        *,
        admission_check=None,
    ):
        calls.append(
            Path(path)
        )

        if admission_check is not None:
            admission_check(
                slot
                + timedelta(seconds=32)
            )

        Path(path).mkdir(
            parents=False,
            exist_ok=False,
        )

        return obs

    return capture


def attempt_path(
    root,
    slot=T,
):
    return (
        Path(root)
        / "attempts"
        / fc.slot_id(slot)
    )


def test_uninitialized_state_fails_without_capture(
    tmp_path,
):
    calls = []

    with pytest.raises(
        FileNotFoundError
    ):
        adapter.run_once(
            tmp_path / "missing",
            clock=Clock(
                T + timedelta(seconds=30)
            ),
            capture=lambda path: calls.append(path),
        )

    assert calls == []

    assert not (
        tmp_path / "missing"
    ).exists()


def test_before_target_is_not_due_without_capture(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = []

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=14)
        ),
        capture=lambda path: calls.append(path),
    )

    assert result["status"] == "NOT_DUE"
    assert calls == []

    assert list(
        (
            tmp_path
            / "attempts"
        ).iterdir()
    ) == []


def test_live_window_delegates_once(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = []

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=30),
            T + timedelta(seconds=31),
            T + timedelta(seconds=35),
        ),
        capture=fake_success(
            T,
            calls,
        ),
    )

    assert result["status"] == "SUCCESS"
    assert len(calls) == 1

    assert calls[0] == (
        attempt_path(tmp_path)
        / "capture"
    )


def test_late_wake_is_not_due_and_creates_no_attempt(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = []

    now = (
        T
        + timedelta(minutes=5)
    )

    result = adapter.run_once(
        tmp_path,
        clock=Clock(now),
        capture=lambda path: calls.append(path),
    )

    assert result["status"] == "NOT_DUE"
    assert result["slot"] == (
        T + fc.HOUR
    ).isoformat()

    assert calls == []

    assert list(
        (
            tmp_path
            / "attempts"
        ).iterdir()
    ) == []

    status = fc.status(
        tmp_path,
        T,
        now,
    )

    assert status["missed_slots"] == 1


def test_future_activation_is_not_due_without_capture(
    tmp_path,
):
    activation = T + fc.HOUR

    runner.initialize(
        tmp_path,
        activation,
    )

    calls = []

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(minutes=30)
        ),
        capture=lambda path: calls.append(path),
    )

    assert result["status"] == "NOT_DUE"
    assert result["slot"] == activation.isoformat()
    assert calls == []

    assert list(
        (
            tmp_path
            / "attempts"
        ).iterdir()
    ) == []


def test_existing_attempt_is_noop_without_second_capture(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    first_calls = []

    first = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=30),
            T + timedelta(seconds=31),
            T + timedelta(seconds=35),
        ),
        capture=fake_success(
            T,
            first_calls,
        ),
    )

    assert first["status"] == "SUCCESS"

    second_calls = []

    second = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=40)
        ),
        capture=lambda path: second_calls.append(path),
    )

    assert second["status"] == "EXISTING_NOOP"
    assert second_calls == []


def test_failed_capture_is_persisted_once(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = []

    def fail(path):
        calls.append(
            Path(path)
        )

        raise RuntimeError(
            "transport down"
        )

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=30),
            T + timedelta(seconds=31),
            T + timedelta(seconds=32),
        ),
        capture=fail,
    )

    assert result["status"] == "FAILED"
    assert len(calls) == 1

    persisted = json.loads(
        (
            attempt_path(tmp_path)
            / "result.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert persisted["status"] == "FAILED"


def test_config_tamper_fails_before_capture(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    config_path = (
        tmp_path
        / "config.json"
    )

    config = json.loads(
        config_path.read_text(
            encoding="utf-8"
        )
    )

    config["retry_policy"] = "RETRY"

    config_path.write_text(
        json.dumps(
            config,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    calls = []

    with pytest.raises(
        ValueError,
        match="frozen contract",
    ):
        adapter.run_once(
            tmp_path,
            clock=Clock(
                T + timedelta(seconds=30)
            ),
            capture=lambda path: calls.append(path),
        )

    assert calls == []


def test_default_live_binding_used_only_when_due(
    tmp_path,
    monkeypatch,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = []

    fake = fake_success(
        T,
        calls,
    )

    monkeypatch.setattr(
        adapter,
        "capture_premium",
        fake,
    )

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=30),
            T + timedelta(seconds=31),
            T + timedelta(seconds=35),
        ),
    )

    assert result["status"] == "SUCCESS"
    assert len(calls) == 1


def test_default_live_binding_not_touched_when_not_due(
    tmp_path,
    monkeypatch,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = []

    def forbidden(path):
        calls.append(path)
        raise AssertionError(
            "live capture invoked while not due"
        )

    monkeypatch.setattr(
        adapter,
        "capture_premium",
        forbidden,
    )

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=10)
        ),
    )

    assert result["status"] == "NOT_DUE"
    assert calls == []


def test_deadline_race_becomes_missed_without_capture(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = []

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=119),
            T + timedelta(seconds=120),
        ),
        capture=lambda path: calls.append(path),
    )

    assert result["status"] == "MISSED_SLOT"
    assert calls == []

    assert not attempt_path(
        tmp_path
    ).exists()


def test_noncallable_capture_rejected_only_when_due(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    with pytest.raises(
        TypeError,
        match="capture callable required",
    ):
        adapter.run_once(
            tmp_path,
            clock=Clock(
                T + timedelta(seconds=30)
            ),
            capture=42,
        )

    assert not attempt_path(
        tmp_path
    ).exists()


def test_not_due_result_is_ephemeral_only(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=10)
        ),
        capture=42,
    )

    assert result["status"] == "NOT_DUE"

    assert set(result) == {
        "schema",
        "status",
        "slot",
        "observed_at",
        "target_at",
        "deadline_at",
        "attempt_path",
    }

    assert result["attempt_path"] is None

    assert list(
        (
            tmp_path
            / "attempts"
        ).iterdir()
    ) == []

def test_observed_to_attempt_clock_regression_fails_before_capture(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = []

    with pytest.raises(
        ValueError,
        match="clock moved backwards after adapter observation",
    ):
        adapter.run_once(
            tmp_path,
            clock=Clock(
                T + timedelta(seconds=30),
                T + timedelta(seconds=20),
            ),
            capture=lambda path: calls.append(path),
        )

    assert calls == []

    assert not attempt_path(
        tmp_path
    ).exists()


def test_default_binding_rechecks_internal_request_before_transport(
    tmp_path,
    monkeypatch,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = {
        "binding": 0,
        "transport": 0,
    }

    def guarded_capture(
        path,
        *,
        admission_check=None,
    ):
        calls["binding"] += 1

        assert admission_check is not None

        admission_check(
            T + timedelta(seconds=120)
        )

        calls["transport"] += 1

        raise AssertionError(
            "transport must remain unreachable"
        )

    monkeypatch.setattr(
        adapter,
        "capture_premium",
        guarded_capture,
    )

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=119),
            T + timedelta(seconds=119),
            T + timedelta(seconds=121),
        ),
    )

    assert result["status"] == "FAILED"

    assert calls == {
        "binding": 1,
        "transport": 0,
    }

    persisted = json.loads(
        (
            attempt_path(tmp_path)
            / "result.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert persisted["status"] == "FAILED"

def test_default_binding_rejects_request_before_runner_start_before_transport(
    tmp_path,
    monkeypatch,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = {
        "binding": 0,
        "transport": 0,
    }

    def guarded_capture(
        path,
        *,
        admission_check=None,
    ):
        calls["binding"] += 1

        assert admission_check is not None

        admission_check(
            T + timedelta(seconds=35)
        )

        calls["transport"] += 1

        raise AssertionError(
            "transport must remain unreachable"
        )

    monkeypatch.setattr(
        adapter,
        "capture_premium",
        guarded_capture,
    )

    result = adapter.run_once(
        tmp_path,
        clock=Clock(
            T + timedelta(seconds=30),
            T + timedelta(seconds=40),
            T + timedelta(seconds=41),
        ),
    )

    assert result["status"] == "FAILED"

    assert calls == {
        "binding": 1,
        "transport": 0,
    }

    persisted = json.loads(
        (
            attempt_path(tmp_path)
            / "result.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert persisted["status"] == "FAILED"
