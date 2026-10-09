"""Deterministic prospective Funding H1 continuity.

No HTTP.
No scheduler.
No observations_v2 writes.
No backfill.
No outcome or trading semantics.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from .premium_index_capture import load_premium


CONTRACT = "funding-h1-capture-v1"
ATTEMPT_SCHEMA = "funding-h1-attempt-v1"
RESULT_SCHEMA = "funding-h1-result-v1"
STATUS_SCHEMA = "funding-h1-continuity-v1"
CERTIFICATE_SCHEMA = "funding-81h-certificate-v1"

INSTRUMENT = "BTCUSDT"
VENUE = "Binance USDⓈ-M"
PRODUCT = "linear perpetual"
ROLE = "PILOT"

HOUR = timedelta(hours=1)
TARGET_OFFSET = timedelta(seconds=15)
SLOT_DEADLINE = timedelta(seconds=120)
READINESS_WINDOW_SLOTS = 81


def _utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    if not isinstance(value, datetime):
        raise TypeError("datetime required")

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            "timezone-aware datetime required"
        )

    return value.astimezone(timezone.utc)


def hour(value):
    value = _utc(value)

    return value.replace(
        minute=0,
        second=0,
        microsecond=0,
    )


def _require_slot(value):
    value = _utc(value)

    if value != hour(value):
        raise ValueError(
            "H1 slot boundary required"
        )

    return value


def target_at(slot):
    return (
        _require_slot(slot)
        + TARGET_OFFSET
    )


def deadline_at(slot):
    return (
        _require_slot(slot)
        + SLOT_DEADLINE
    )


def slot_id(slot):
    return _require_slot(slot).strftime(
        "%Y%m%dT%H0000Z"
    )


def _slot_from_id(value):
    try:
        result = datetime.strptime(
            value,
            "%Y%m%dT%H0000Z",
        )
    except ValueError as exc:
        raise ValueError(
            "invalid funding slot identity"
        ) from exc

    return result.replace(
        tzinfo=timezone.utc
    )


def _json_hash(value):
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(
        raw
    ).hexdigest()


def _read_json(path):
    value = json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(value, dict):
        raise ValueError(
            "object JSON required"
        )

    return value


def due_slots(
    activation_slot,
    reference,
):
    activation = _require_slot(
        activation_slot
    )

    reference = _utc(reference)

    candidate = hour(reference)

    if reference < deadline_at(candidate):
        candidate -= HOUR

    if candidate < activation:
        return ()

    count = (
        int(
            (
                candidate
                - activation
            )
            / HOUR
        )
        + 1
    )

    return tuple(
        activation
        + i * HOUR
        for i in range(count)
    )


def _record(
    slot,
    state,
    *,
    receipt_id=None,
    reason=None,
):
    return {
        "slot": slot.isoformat(),
        "slot_id": slot_id(slot),
        "status": state,
        "capture_receipt_id":
            receipt_id,
        "reason": reason,
    }


def _attempt_path(
    state,
    slot,
):
    return (
        Path(state)
        / "attempts"
        / slot_id(slot)
    )


def _validate_attempt(
    attempt,
    slot,
):
    expected = {
        "schema",
        "contract",
        "slot",
        "target_at",
        "deadline_at",
        "started_at",
        "status",
    }

    if set(attempt) != expected:
        raise ValueError(
            "unknown attempt schema"
        )

    if (
        attempt["schema"]
        != ATTEMPT_SCHEMA
        or attempt["contract"]
        != CONTRACT
        or attempt["slot"]
        != slot.isoformat()
        or attempt["target_at"]
        != target_at(slot).isoformat()
        or attempt["deadline_at"]
        != deadline_at(slot).isoformat()
        or attempt["status"]
        != "STARTED"
    ):
        raise ValueError(
            "attempt identity mismatch"
        )

    started = _utc(
        attempt["started_at"]
    )

    if not (
        target_at(slot)
        <= started
        < deadline_at(slot)
    ):
        raise ValueError(
            "attempt outside live slot window"
        )

    return started


def _validate_result(
    result,
    slot,
):
    expected = {
        "schema",
        "contract",
        "slot",
        "status",
        "completed_at",
        "capture_receipt_id",
        "error",
    }

    if set(result) != expected:
        raise ValueError(
            "unknown result schema"
        )

    if (
        result["schema"]
        != RESULT_SCHEMA
        or result["contract"]
        != CONTRACT
        or result["slot"]
        != slot.isoformat()
    ):
        raise ValueError(
            "result identity mismatch"
        )

    if result["status"] not in (
        "SUCCESS",
        "FAILED",
    ):
        raise ValueError(
            "unsupported final result status"
        )

    completed = _utc(
        result["completed_at"]
    )

    return completed


def _scope_role(observation):
    value = getattr(
        observation,
        "dataset_role",
        None,
    )

    return getattr(
        value,
        "value",
        value,
    )


def _classify_slot(
    state,
    slot,
):
    path = _attempt_path(
        state,
        slot,
    )

    if not path.exists():
        return _record(
            slot,
            "MISSED_SLOT",
            reason="NO_ATTEMPT",
        )

    if not path.is_dir():
        return _record(
            slot,
            "INVALID",
            reason="ATTEMPT_NOT_DIRECTORY",
        )

    allowed = {
        "attempt.json",
        "result.json",
        "capture",
    }

    entries = {
        item.name
        for item in path.iterdir()
    }

    if entries - allowed:
        return _record(
            slot,
            "INVALID",
            reason="UNEXPECTED_ATTEMPT_ARTIFACT",
        )

    attempt_path = (
        path / "attempt.json"
    )

    if not attempt_path.is_file():
        return _record(
            slot,
            "INVALID",
            reason="MISSING_ATTEMPT_IDENTITY",
        )

    try:
        attempt = _read_json(
            attempt_path
        )

        started = _validate_attempt(
            attempt,
            slot,
        )

    except Exception as exc:
        return _record(
            slot,
            "INVALID",
            reason=str(exc),
        )

    result_path = (
        path / "result.json"
    )

    if not result_path.exists():
        return _record(
            slot,
            "INCOMPLETE",
            reason="STARTED_WITHOUT_FINAL_RESULT",
        )

    if not result_path.is_file():
        return _record(
            slot,
            "INVALID",
            reason="RESULT_NOT_FILE",
        )

    try:
        result = _read_json(
            result_path
        )

        completed = _validate_result(
            result,
            slot,
        )

    except Exception as exc:
        return _record(
            slot,
            "INVALID",
            reason=str(exc),
        )

    if completed < started:
        return _record(
            slot,
            "INVALID",
            reason="RESULT_PRECEDES_ATTEMPT",
        )

    if result["status"] == "FAILED":

        if (
            result[
                "capture_receipt_id"
            ]
            is not None
        ):
            return _record(
                slot,
                "INVALID",
                reason=(
                    "FAILED_RESULT_HAS_"
                    "RECEIPT"
                ),
            )

        if (
            not isinstance(
                result["error"],
                str,
            )
            or not result["error"]
        ):
            return _record(
                slot,
                "INVALID",
                reason=(
                    "FAILED_RESULT_REQUIRES_"
                    "ERROR"
                ),
            )

        return _record(
            slot,
            "FAILED",
            reason=result["error"],
        )

    if result["error"] is not None:
        return _record(
            slot,
            "INVALID",
            reason="SUCCESS_RESULT_HAS_ERROR",
        )

    receipt_id = result[
        "capture_receipt_id"
    ]

    if (
        not isinstance(
            receipt_id,
            str,
        )
        or not receipt_id
    ):
        return _record(
            slot,
            "INVALID",
            reason="SUCCESS_RECEIPT_ID_REQUIRED",
        )

    capture_path = (
        path / "capture"
    )

    if not capture_path.is_dir():
        return _record(
            slot,
            "INVALID",
            reason="SUCCESS_CAPTURE_MISSING",
        )

    try:
        observation = load_premium(
            capture_path
        )

        if (
            observation.instrument
            != INSTRUMENT
            or observation.venue
            != VENUE
            or observation.product
            != PRODUCT
            or _scope_role(observation)
            != ROLE
            or len(
                observation.receipts
            )
            != 1
        ):
            raise ValueError(
                "capture scope mismatch"
            )

        receipt = (
            observation.receipts[0]
        )

        if (
            receipt.receipt_id
            != receipt_id
        ):
            raise ValueError(
                "capture receipt identity mismatch"
            )

        required_times = (
            receipt.request_started_at,
            receipt.received_at,
            receipt.available_at,
        )

        if any(
            value is None
            for value in required_times
        ):
            raise ValueError(
                "incomplete capture chronology"
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
            <= completed
        ):
            raise ValueError(
                "noncausal attempt/capture/result chronology"
            )

        if not (
            target_at(slot)
            <= request_started
            < deadline_at(slot)
        ):
            raise ValueError(
                "capture outside frozen slot window"
            )

        if (
            getattr(
                observation,
                "decision_at",
                None,
            )
            != receipt.available_at
        ):
            raise ValueError(
                "capture availability projection mismatch"
            )

    except Exception as exc:
        return _record(
            slot,
            "INVALID",
            reason=str(exc),
        )

    return _record(
        slot,
        "SUCCESS",
        receipt_id=receipt_id,
    )


def _structural_scan(
    state,
    activation,
    expected,
):
    attempts = (
        Path(state)
        / "attempts"
    )

    invalid = []
    pre_activation = 0
    not_due = 0

    if not attempts.exists():
        return (
            invalid,
            pre_activation,
            not_due,
        )

    if not attempts.is_dir():
        invalid.append({
            "path":
                str(attempts),
            "reason":
                "ATTEMPTS_NOT_DIRECTORY",
        })

        return (
            invalid,
            pre_activation,
            not_due,
        )

    expected_set = set(
        expected
    )

    for entry in sorted(
        attempts.iterdir(),
        key=lambda item:
            item.name,
    ):
        if not entry.is_dir():
            invalid.append({
                "path":
                    str(entry),
                "reason":
                    "UNEXPECTED_NON_DIRECTORY",
            })

            continue

        try:
            parsed = _slot_from_id(
                entry.name
            )

        except ValueError as exc:
            invalid.append({
                "path":
                    str(entry),
                "reason":
                    str(exc),
            })

            continue

        if parsed < activation:
            pre_activation += 1

        elif parsed not in expected_set:
            not_due += 1

    return (
        invalid,
        pre_activation,
        not_due,
    )


def _gaps(records):
    result = []
    index = 0

    while index < len(records):

        if (
            records[index]["status"]
            == "SUCCESS"
        ):
            index += 1
            continue

        start = index
        statuses = []

        while (
            index < len(records)
            and records[index]["status"]
            != "SUCCESS"
        ):
            statuses.append(
                records[index]["status"]
            )

            index += 1

        block = records[
            start:index
        ]

        result.append({
            "first_slot":
                block[0]["slot"],
            "last_slot":
                block[-1]["slot"],
            "slots":
                len(block),
            "statuses":
                statuses,
        })

    return result


def status(
    state,
    activation_slot,
    reference,
):
    activation = _require_slot(
        activation_slot
    )

    reference = _utc(
        reference
    )

    expected = due_slots(
        activation,
        reference,
    )

    (
        structural_invalid,
        pre_activation,
        not_due,
    ) = _structural_scan(
        state,
        activation,
        expected,
    )

    records = [
        _classify_slot(
            state,
            slot,
        )
        for slot in expected
    ]

    counts = {
        name:
            sum(
                record["status"]
                == name
                for record in records
            )
        for name in (
            "SUCCESS",
            "FAILED",
            "MISSED_SLOT",
            "INCOMPLETE",
            "INVALID",
        )
    }

    current_streak = 0
    longest_streak = 0

    for record in records:

        if (
            record["status"]
            == "SUCCESS"
        ):
            current_streak += 1

            longest_streak = max(
                longest_streak,
                current_streak,
            )

        else:
            current_streak = 0

    successful = [
        record
        for record in records
        if record["status"]
        == "SUCCESS"
    ]

    invalid_count = (
        counts["INVALID"]
        + len(
            structural_invalid
        )
    )

    ready = (
        current_streak
        >= READINESS_WINDOW_SLOTS
        and not structural_invalid
    )

    certificate = None

    if ready:
        selected = records[
            -READINESS_WINDOW_SLOTS:
        ]

        if any(
            record["status"]
            != "SUCCESS"
            for record in selected
        ):
            raise AssertionError(
                "readiness/streak inconsistency"
            )

        members = [
            {
                "slot":
                    record["slot"],
                "slot_id":
                    record["slot_id"],
                "capture_receipt_id":
                    record[
                        "capture_receipt_id"
                    ],
            }
            for record in selected
        ]

        certificate = {
            "schema":
                CERTIFICATE_SCHEMA,
            "contract":
                CONTRACT,
            "instrument":
                INSTRUMENT,
            "number_of_slots":
                READINESS_WINDOW_SLOTS,
            "first_slot":
                selected[0]["slot"],
            "last_slot":
                selected[-1]["slot"],
            "slot_ids": [
                record["slot_id"]
                for record in selected
            ],
            "capture_receipt_ids": [
                record[
                    "capture_receipt_id"
                ]
                for record in selected
            ],
            "certified_set_hash":
                _json_hash(
                    members
                ),
            "certified_at":
                reference.isoformat(),
            "historical_backfill":
                False,
            "gaps":
                0,
        }

    return {
        "schema":
            STATUS_SCHEMA,
        "contract":
            CONTRACT,
        "activation_slot":
            activation.isoformat(),
        "reference_at":
            reference.isoformat(),
        "total_expected_slots":
            len(expected),
        "successful_slots":
            counts["SUCCESS"],
        "failed_slots":
            counts["FAILED"],
        "missed_slots":
            counts["MISSED_SLOT"],
        "incomplete_slots":
            counts["INCOMPLETE"],
        "invalid_slots":
            invalid_count,
        "duplicate_slots":
            0,
        "current_streak":
            current_streak,
        "longest_streak":
            longest_streak,
        "slots_to_81":
            max(
                0,
                READINESS_WINDOW_SLOTS
                - current_streak,
            ),
        "first_valid_slot":
            (
                successful[0]["slot"]
                if successful
                else None
            ),
        "last_valid_slot":
            (
                successful[-1]["slot"]
                if successful
                else None
            ),
        "funding_81h_ready":
            ready,
        "gaps":
            _gaps(records),
        "records":
            records,
        "structural_invalid":
            structural_invalid,
        "pre_activation_attempts":
            pre_activation,
        "not_due_attempts":
            not_due,
        "integrity":
            (
                "PASS"
                if not structural_invalid
                else "FAIL"
            ),
        "certificate":
            certificate,
    }
