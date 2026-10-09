from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import core.scientific.funding_continuity as fc
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
    receipt_id=None,
    request_offset=16,
    received_offset=17,
    available_offset=18,
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
        instrument="BTCUSDT",
        venue="Binance USDⓈ-M",
        product="linear perpetual",
        dataset_role=SimpleNamespace(
            value="PILOT"
        ),
        decision_at=receipt.available_at,
        receipts=(receipt,),
    )


def capture_success(slot):
    obs = observation(slot)

    def capture(path):
        Path(path).mkdir(
            parents=False,
            exist_ok=False,
        )

        return obs

    return capture, obs


def capture_success_value(
    value,
):
    def capture(path):
        Path(path).mkdir(
            parents=False,
            exist_ok=False,
        )

        return value

    return capture


def test_initialize_freezes_activation(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    config = json.loads(
        (
            tmp_path
            / "config.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        config["activation_slot"]
        == T.isoformat()
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
        config["retry_policy"]
        == "NONE"
    )


def test_initialize_same_config_idempotent(
    tmp_path,
):
    first = runner.initialize(
        tmp_path,
        T,
    )

    second = runner.initialize(
        tmp_path,
        T,
    )

    assert first == second


def test_initialize_changed_activation_rejected(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    with pytest.raises(
        ValueError,
        match="configuration changed",
    ):
        runner.initialize(
            tmp_path,
            T + fc.HOUR,
        )


def test_select_slot_before_target_uses_current(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    selected = runner.select_slot(
        tmp_path,
        T + timedelta(seconds=10),
    )

    assert selected == T


def test_select_slot_inside_window_uses_current(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    selected = runner.select_slot(
        tmp_path,
        T + timedelta(seconds=30),
    )

    assert selected == T


def test_select_slot_after_deadline_moves_next(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    selected = runner.select_slot(
        tmp_path,
        T + timedelta(minutes=3),
    )

    assert selected == T + fc.HOUR


def test_late_slot_is_missed_without_attempt(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    result = runner.attempt_slot(
        tmp_path,
        T,
        lambda path: pytest.fail(
            "capture must not run"
        ),
        clock=Clock(
            T + timedelta(minutes=2)
        ),
    )

    assert (
        result["status"]
        == "MISSED_SLOT"
    )

    assert not (
        tmp_path
        / "attempts"
        / fc.slot_id(T)
    ).exists()

    report = fc.status(
        tmp_path,
        T,
        T + timedelta(minutes=2),
    )

    assert report["missed_slots"] == 1
    assert report["current_streak"] == 0


def test_success_attempt_integrates_with_continuity(
    tmp_path,
    monkeypatch,
):
    runner.initialize(
        tmp_path,
        T,
    )

    capture, obs = capture_success(T)

    result = runner.attempt_slot(
        tmp_path,
        T,
        capture,
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=19),
        ),
    )

    assert result["status"] == "SUCCESS"

    attempt_path = (
        tmp_path
        / "attempts"
        / fc.slot_id(T)
    )

    attempt = json.loads(
        (
            attempt_path
            / "attempt.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    final = json.loads(
        (
            attempt_path
            / "result.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert attempt["status"] == "STARTED"
    assert final["status"] == "SUCCESS"

    monkeypatch.setattr(
        fc,
        "load_premium",
        lambda path: obs,
    )

    report = fc.status(
        tmp_path,
        T,
        T + timedelta(minutes=2),
    )

    assert report["successful_slots"] == 1
    assert report["current_streak"] == 1


def test_failed_attempt_is_persisted_and_not_retried(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    calls = {"failed": 0, "retry": 0}

    def fail(path):
        calls["failed"] += 1
        raise RuntimeError(
            "network down"
        )

    result = runner.attempt_slot(
        tmp_path,
        T,
        fail,
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=16),
        ),
    )

    assert result["status"] == "FAILED"
    assert calls["failed"] == 1

    def forbidden_retry(path):
        calls["retry"] += 1
        raise AssertionError(
            "retry occurred"
        )

    again = runner.attempt_slot(
        tmp_path,
        T,
        forbidden_retry,
        clock=Clock(
            T + timedelta(seconds=30)
        ),
    )

    assert (
        again["status"]
        == "EXISTING_NOOP"
    )

    assert calls["retry"] == 0

    report = fc.status(
        tmp_path,
        T,
        T + timedelta(minutes=2),
    )

    assert report["failed_slots"] == 1


def test_existing_incomplete_attempt_is_never_retried(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    path = (
        tmp_path
        / "attempts"
        / fc.slot_id(T)
    )

    path.mkdir()

    runner._exclusive_json(
        path / "attempt.json",
        runner._attempt_body(
            T,
            T + timedelta(seconds=15),
        ),
    )

    calls = {"count": 0}

    def forbidden(path):
        calls["count"] += 1
        raise AssertionError(
            "incomplete attempt retried"
        )

    result = runner.attempt_slot(
        tmp_path,
        T,
        forbidden,
        clock=Clock(
            T + timedelta(seconds=30)
        ),
    )

    assert (
        result["status"]
        == "EXISTING_NOOP"
    )

    assert calls["count"] == 0

    report = fc.status(
        tmp_path,
        T,
        T + timedelta(minutes=2),
    )

    assert report["incomplete_slots"] == 1


def test_resume_after_multiple_missed_slots_synthesizes_nothing(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    resumed = (
        T
        + 3 * fc.HOUR
        + timedelta(minutes=5)
    )

    selected = runner.select_slot(
        tmp_path,
        resumed,
    )

    assert selected == T + 4 * fc.HOUR

    assert list(
        (
            tmp_path
            / "attempts"
        ).iterdir()
    ) == []

    report = fc.status(
        tmp_path,
        T,
        resumed,
    )

    assert report["missed_slots"] == 4
    assert report["total_expected_slots"] == 4

    assert list(
        (
            tmp_path
            / "attempts"
        ).iterdir()
    ) == []


def test_restart_inside_live_window_can_attempt_current_slot(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    now = T + timedelta(seconds=30)

    selected = runner.select_slot(
        tmp_path,
        now,
    )

    assert selected == T

    obs = observation(
        T,
        request_offset=31,
        received_offset=32,
        available_offset=33,
    )

    def capture(path):
        Path(path).mkdir(
            parents=False,
            exist_ok=False,
        )

        return obs

    result = runner.attempt_slot(
        tmp_path,
        selected,
        capture,
        clock=Clock(
            now,
            T + timedelta(seconds=40),
        ),
    )

    assert result["status"] == "SUCCESS"


def test_clock_regression_after_capture_leaves_incomplete(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    capture, _ = capture_success(T)

    with pytest.raises(
        ValueError,
        match="clock moved backwards",
    ):
        runner.attempt_slot(
            tmp_path,
            T,
            capture,
            clock=Clock(
                T + timedelta(seconds=30),
                T + timedelta(seconds=29),
            ),
        )

    attempt_path = (
        tmp_path
        / "attempts"
        / fc.slot_id(T)
    )

    assert (
        attempt_path
        / "attempt.json"
    ).exists()

    assert not (
        attempt_path
        / "result.json"
    ).exists()

    report = fc.status(
        tmp_path,
        T,
        T + timedelta(minutes=2),
    )

    assert report["incomplete_slots"] == 1


def test_failed_slot_does_not_block_future_slot(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    def fail(path):
        raise RuntimeError(
            "temporary outage"
        )

    first = runner.attempt_slot(
        tmp_path,
        T,
        fail,
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=16),
        ),
    )

    assert first["status"] == "FAILED"

    next_slot = T + fc.HOUR
    capture, _ = capture_success(next_slot)

    second = runner.attempt_slot(
        tmp_path,
        next_slot,
        capture,
        clock=Clock(
            next_slot
            + timedelta(seconds=15),
            next_slot
            + timedelta(seconds=19),
        ),
    )

    assert second["status"] == "SUCCESS"

def test_wrong_instrument_is_failed(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    bad = observation(T)
    bad.instrument = "ETHUSDT"

    result = runner.attempt_slot(
        tmp_path,
        T,
        capture_success_value(bad),
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=20),
        ),
    )

    assert result["status"] == "FAILED"
    assert "capture scope mismatch" in result["error"]


def test_wrong_venue_is_failed(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    bad = observation(T)
    bad.venue = "Other Venue"

    result = runner.attempt_slot(
        tmp_path,
        T,
        capture_success_value(bad),
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=20),
        ),
    )

    assert result["status"] == "FAILED"


def test_wrong_product_is_failed(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    bad = observation(T)
    bad.product = "spot"

    result = runner.attempt_slot(
        tmp_path,
        T,
        capture_success_value(bad),
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=20),
        ),
    )

    assert result["status"] == "FAILED"


def test_wrong_role_is_failed(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    bad = observation(T)
    bad.dataset_role = SimpleNamespace(
        value="CONFIRMATION"
    )

    result = runner.attempt_slot(
        tmp_path,
        T,
        capture_success_value(bad),
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=20),
        ),
    )

    assert result["status"] == "FAILED"


def test_capture_request_before_attempt_is_failed(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    bad = observation(
        T,
        request_offset=14,
        received_offset=17,
        available_offset=18,
    )

    result = runner.attempt_slot(
        tmp_path,
        T,
        capture_success_value(bad),
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=20),
        ),
    )

    assert result["status"] == "FAILED"
    assert (
        "noncausal attempt/capture chronology"
        in result["error"]
    )


def test_capture_request_at_deadline_is_failed(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    bad = observation(
        T,
        request_offset=120,
        received_offset=121,
        available_offset=122,
    )

    result = runner.attempt_slot(
        tmp_path,
        T,
        capture_success_value(bad),
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=123),
        ),
    )

    assert result["status"] == "FAILED"
    assert (
        "capture outside frozen slot window"
        in result["error"]
    )


def test_reversed_capture_chronology_is_failed(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    bad = observation(
        T,
        request_offset=16,
        received_offset=18,
        available_offset=17,
    )

    result = runner.attempt_slot(
        tmp_path,
        T,
        capture_success_value(bad),
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=20),
        ),
    )

    assert result["status"] == "FAILED"
    assert (
        "noncausal attempt/capture chronology"
        in result["error"]
    )


def test_availability_projection_mismatch_is_failed(
    tmp_path,
):
    runner.initialize(
        tmp_path,
        T,
    )

    bad = observation(T)

    bad.decision_at = (
        T + timedelta(seconds=19)
    )

    result = runner.attempt_slot(
        tmp_path,
        T,
        capture_success_value(bad),
        clock=Clock(
            T + timedelta(seconds=15),
            T + timedelta(seconds=20),
        ),
    )

    assert result["status"] == "FAILED"
    assert (
        "capture availability projection mismatch"
        in result["error"]
    )
