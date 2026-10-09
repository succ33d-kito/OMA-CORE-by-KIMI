"""Thin one-shot live binding for prospective Funding H1 capture.

This module does not initialize activation state and does not schedule itself.
The state root must already contain the immutable funding-h1-runner config.

Network access is possible only when a due slot reaches runner.attempt_slot()
and no capture override was injected.
"""

from datetime import datetime, timezone

from . import funding_continuity as fc
from . import funding_h1_runner as runner
from .premium_index_capture import capture_premium


ADAPTER_SCHEMA = "funding-h1-live-adapter-v1"


def _now():
    return datetime.now(timezone.utc)


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


def _guarded_clock(
    clock,
    lower_bound,
):
    """Reject regression and expose the runner's first authoritative sample."""

    state = {
        "previous": _utc(
            lower_bound
        ),
        "attempt_started_at": None,
    }

    def sample():
        current = _utc(
            clock()
        )

        if current < state[
            "previous"
        ]:
            raise ValueError(
                "clock moved backwards after adapter observation"
            )

        state["previous"] = current

        if state[
            "attempt_started_at"
        ] is None:
            state[
                "attempt_started_at"
            ] = current

        return current

    return (
        sample,
        state,
    )


def _default_live_capture(
    slot,
    observed_at,
    attempt_state,
):
    target = fc.target_at(
        slot
    )

    deadline = fc.deadline_at(
        slot
    )

    def admission_check(
        request_started,
    ):
        request_started = _utc(
            request_started
        )

        if request_started < observed_at:
            raise ValueError(
                "premium request precedes adapter observation"
            )

        attempt_started_at = attempt_state[
            "attempt_started_at"
        ]

        if attempt_started_at is None:
            raise ValueError(
                "authoritative attempt start unavailable"
            )

        if request_started < attempt_started_at:
            raise ValueError(
                "premium request precedes authoritative attempt start"
            )

        if not (
            target
            <= request_started
            < deadline
        ):
            raise ValueError(
                "premium request outside frozen slot window"
            )

    def capture(path):
        return capture_premium(
            path,
            admission_check=admission_check,
        )

    return capture


def run_once(
    state,
    *,
    clock=_now,
    capture=None,
):
    """Run at most one already-activated prospective H1 opportunity.

    No state initialization occurs here.

    NOT_DUE is an ephemeral adapter result and is never written into the
    continuity state. Past missing slots therefore remain physically absent
    and are derived as MISSED_SLOT by funding_continuity.
    """

    runner.load_config(state)

    observed_at = _utc(
        clock()
    )

    (
        attempt_clock,
        attempt_state,
    ) = _guarded_clock(
        clock,
        observed_at,
    )

    slot = runner.select_slot(
        state,
        observed_at,
    )

    target = fc.target_at(slot)
    deadline = fc.deadline_at(slot)

    if not (
        target
        <= observed_at
        < deadline
    ):
        return {
            "schema": ADAPTER_SCHEMA,
            "status": "NOT_DUE",
            "slot": slot.isoformat(),
            "observed_at":
                observed_at.isoformat(),
            "target_at":
                target.isoformat(),
            "deadline_at":
                deadline.isoformat(),
            "attempt_path": None,
        }

    capture_callable = (
        _default_live_capture(
            slot,
            observed_at,
            attempt_state,
        )
        if capture is None
        else capture
    )

    if not callable(
        capture_callable
    ):
        raise TypeError(
            "capture callable required"
        )

    return runner.attempt_slot(
        state,
        slot,
        capture_callable,
        clock=attempt_clock,
    )
