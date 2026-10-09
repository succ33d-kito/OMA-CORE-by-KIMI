"""Deterministic orchestration for prospective Funding H1 capture.

This module performs no network access and has no scheduler integration.
A capture callable is injected by the caller.

MISSED_SLOT is never persisted.  A due slot without an attempt directory is
derived later by funding_continuity.status().
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path

from . import funding_continuity as fc


RUNNER_SCHEMA = "funding-h1-runner-v1"
CADENCE = "H1"
RETRY_POLICY = "NONE"


def _utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    if not isinstance(value, datetime):
        raise TypeError("datetime required")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")

    return value.astimezone(timezone.utc)


def _slot(value):
    value = _utc(value)

    if value != fc.hour(value):
        raise ValueError("H1 slot boundary required")

    return value


def _json(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _exclusive_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("xb") as handle:
        handle.write(_json(value))
        handle.flush()
        os.fsync(handle.fileno())


def _read_json(path):
    value = json.loads(
        Path(path).read_text(encoding="utf-8")
    )

    if not isinstance(value, dict):
        raise ValueError("object JSON required")

    return value


def _expected_config(activation_slot):
    activation = _slot(activation_slot)

    return {
        "schema": RUNNER_SCHEMA,
        "contract": fc.CONTRACT,
        "activation_slot": activation.isoformat(),
        "cadence": CADENCE,
        "target_offset_seconds": int(
            fc.TARGET_OFFSET.total_seconds()
        ),
        "slot_deadline_seconds": int(
            fc.SLOT_DEADLINE.total_seconds()
        ),
        "retry_policy": RETRY_POLICY,
    }


def initialize(state, activation_slot):
    root = Path(state)
    root.mkdir(parents=True, exist_ok=True)

    config_path = root / "config.json"
    expected = _expected_config(activation_slot)

    if config_path.exists():
        if _read_json(config_path) != expected:
            raise ValueError(
                "runner configuration changed"
            )
    else:
        if any(root.iterdir()):
            raise ValueError(
                "unrecognized existing runner state"
            )

        _exclusive_json(
            config_path,
            expected,
        )

    attempts = root / "attempts"

    if attempts.exists() and not attempts.is_dir():
        raise ValueError(
            "attempts state is not a directory"
        )

    attempts.mkdir(exist_ok=True)

    return root


def load_config(state):
    root = Path(state)
    config = _read_json(
        root / "config.json"
    )

    expected_keys = {
        "schema",
        "contract",
        "activation_slot",
        "cadence",
        "target_offset_seconds",
        "slot_deadline_seconds",
        "retry_policy",
    }

    if set(config) != expected_keys:
        raise ValueError(
            "unknown runner configuration schema"
        )

    activation = _slot(
        config["activation_slot"]
    )

    if config != _expected_config(activation):
        raise ValueError(
            "runner configuration violates frozen contract"
        )

    attempts = root / "attempts"

    if not attempts.is_dir():
        raise ValueError(
            "attempts directory missing"
        )

    return config


def activation_slot(state):
    return _slot(
        load_config(state)[
            "activation_slot"
        ]
    )


def select_slot(state, now):
    """Select only the current live window or the next future H1 slot.

    Past slots are never enumerated for capture and are never materialized.
    """

    activation = activation_slot(state)
    now = _utc(now)

    candidate = fc.hour(now)

    if candidate < activation:
        return activation

    if now < fc.target_at(candidate):
        return candidate

    if now < fc.deadline_at(candidate):
        return candidate

    return candidate + fc.HOUR


def _attempt_path(state, slot):
    return (
        Path(state)
        / "attempts"
        / fc.slot_id(slot)
    )


def _role_value(observation):
    role = getattr(
        observation,
        "dataset_role",
        None,
    )

    return getattr(
        role,
        "value",
        role,
    )


def _validate_capture_observation(
    observation,
    slot,
    started,
    capture_path,
):
    """Validate the injected capture before SUCCESS may be persisted."""

    capture_path = Path(
        capture_path
    )

    if not capture_path.is_dir():
        raise ValueError(
            "capture directory missing"
        )

    if (
        getattr(
            observation,
            "instrument",
            None,
        )
        != fc.INSTRUMENT
        or getattr(
            observation,
            "venue",
            None,
        )
        != fc.VENUE
        or getattr(
            observation,
            "product",
            None,
        )
        != fc.PRODUCT
        or _role_value(
            observation
        )
        != fc.ROLE
    ):
        raise ValueError(
            "capture scope mismatch"
        )

    receipts = getattr(
        observation,
        "receipts",
        None,
    )

    if not isinstance(
        receipts,
        tuple,
    ):
        raise ValueError(
            "capture observation receipts must be tuple"
        )

    if len(receipts) != 1:
        raise ValueError(
            "capture observation must contain exactly one receipt"
        )

    receipt = receipts[0]

    receipt_id = getattr(
        receipt,
        "receipt_id",
        None,
    )

    if (
        not isinstance(
            receipt_id,
            str,
        )
        or not receipt_id
    ):
        raise ValueError(
            "capture receipt identity missing"
        )

    required_times = (
        getattr(
            receipt,
            "request_started_at",
            None,
        ),
        getattr(
            receipt,
            "received_at",
            None,
        ),
        getattr(
            receipt,
            "available_at",
            None,
        ),
    )

    if any(
        value is None
        for value in required_times
    ):
        raise ValueError(
            "capture chronology incomplete"
        )

    request_started = _utc(
        receipt.request_started_at
    )

    received = _utc(
        receipt.received_at
    )

    available = _utc(
        receipt.available_at
    )

    if not (
        started
        <= request_started
        <= received
        <= available
    ):
        raise ValueError(
            "noncausal attempt/capture chronology"
        )

    if not (
        fc.target_at(slot)
        <= request_started
        < fc.deadline_at(slot)
    ):
        raise ValueError(
            "capture outside frozen slot window"
        )

    decision_at = getattr(
        observation,
        "decision_at",
        None,
    )

    if decision_at is None:
        raise ValueError(
            "capture decision availability missing"
        )

    if _utc(
        decision_at
    ) != available:
        raise ValueError(
            "capture availability projection mismatch"
        )

    return (
        receipt_id,
        available,
    )


def _attempt_body(slot, started):
    return {
        "schema": fc.ATTEMPT_SCHEMA,
        "contract": fc.CONTRACT,
        "slot": slot.isoformat(),
        "target_at": fc.target_at(
            slot
        ).isoformat(),
        "deadline_at": fc.deadline_at(
            slot
        ).isoformat(),
        "started_at": started.isoformat(),
        "status": "STARTED",
    }


def _result_body(
    slot,
    status,
    completed,
    *,
    receipt_id=None,
    error=None,
):
    return {
        "schema": fc.RESULT_SCHEMA,
        "contract": fc.CONTRACT,
        "slot": slot.isoformat(),
        "status": status,
        "completed_at": completed.isoformat(),
        "capture_receipt_id": receipt_id,
        "error": error,
    }


def attempt_slot(
    state,
    slot,
    capture,
    *,
    clock,
):
    """Perform at most one prospective attempt for one H1 slot.

    Existing attempts are immutable and are never retried.
    A slot already past deadline with no attempt remains physically absent;
    continuity later derives MISSED_SLOT from that absence.
    """

    root = Path(state)
    config = load_config(root)

    slot = _slot(slot)
    activation = _slot(
        config["activation_slot"]
    )

    if slot < activation:
        raise ValueError(
            "slot precedes activation"
        )

    path = _attempt_path(
        root,
        slot,
    )

    if path.exists():
        return {
            "status": "EXISTING_NOOP",
            "slot": slot.isoformat(),
            "attempt_path": str(path),
        }

    started = _utc(clock())

    if started < fc.target_at(slot):
        raise ValueError(
            "attempt before frozen target"
        )

    if started >= fc.deadline_at(slot):
        return {
            "status": "MISSED_SLOT",
            "slot": slot.isoformat(),
            "attempt_path": None,
        }

    path.mkdir(
        parents=False,
        exist_ok=False,
    )

    _exclusive_json(
        path / "attempt.json",
        _attempt_body(
            slot,
            started,
        ),
    )

    try:
        capture_path = (
            path / "capture"
        )

        observation = capture(
            capture_path
        )

        (
            receipt_id,
            capture_available_at,
        ) = _validate_capture_observation(
            observation,
            slot,
            started,
            capture_path,
        )

    except Exception as exc:
        completed = _utc(clock())

        if completed < started:
            raise ValueError(
                "clock moved backwards during failed attempt"
            ) from exc

        error = (
            f"{type(exc).__name__}: {exc}"
        )

        _exclusive_json(
            path / "result.json",
            _result_body(
                slot,
                "FAILED",
                completed,
                receipt_id=None,
                error=error,
            ),
        )

        return {
            "status": "FAILED",
            "slot": slot.isoformat(),
            "attempt_path": str(path),
            "error": error,
        }

    completed = _utc(clock())

    if completed < started:
        raise ValueError(
            "clock moved backwards during successful attempt"
        )

    if completed < capture_available_at:
        raise ValueError(
            "attempt completion precedes capture availability"
        )

    _exclusive_json(
        path / "result.json",
        _result_body(
            slot,
            "SUCCESS",
            completed,
            receipt_id=receipt_id,
            error=None,
        ),
    )

    return {
        "status": "SUCCESS",
        "slot": slot.isoformat(),
        "attempt_path": str(path),
        "capture_receipt_id": receipt_id,
    }
