"""Long-running runtime for already-activated prospective Funding H1 state.

Responsibilities:
- validate existing runner state
- hold one process-level lock
- enforce monotonic runtime clock samples
- maintain non-evidentiary heartbeat metadata
- repeatedly invoke funding_h1_live_adapter.run_once
- poll no slower than the frozen five-second maximum

This module does NOT:
- initialize activation state
- perform backfill
- write observations_v2
- write ledger records
- write Outcome/Learning/Criterion
- install or manage a scheduler task
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

from . import funding_h1_live_adapter as live_adapter
from . import funding_h1_runner as runner


RUNTIME_SCHEMA = "funding-h1-runtime-v1"
HEARTBEAT_SCHEMA = "funding-h1-runtime-heartbeat-v1"

MAX_WAIT_POLL_SECONDS = 5.0

RUNTIME_DIRECTORY = "runtime"
LOCK_FILE = "runner.lock"
HEARTBEAT_FILE = "heartbeat.json"


def _utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    if not isinstance(value, datetime):
        raise TypeError(
            "datetime required"
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            "timezone-aware datetime required"
        )

    return value.astimezone(
        timezone.utc
    )


def _now():
    return datetime.now(
        timezone.utc
    )


def _json_bytes(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_json(path, value):
    path = Path(path)

    temporary = (
        path.parent
        / (
            "."
            + path.name
            + ".tmp"
        )
    )

    with temporary.open(
        "wb"
    ) as handle:
        handle.write(
            _json_bytes(value)
        )
        handle.flush()
        os.fsync(
            handle.fileno()
        )

    os.replace(
        temporary,
        path,
    )


def _lock_handle(handle):
    handle.seek(
        0,
        os.SEEK_END,
    )

    if handle.tell() == 0:
        handle.write(
            b"\0"
        )
        handle.flush()
        os.fsync(
            handle.fileno()
        )

    handle.seek(0)

    if os.name == "nt":
        import msvcrt

        msvcrt.locking(
            handle.fileno(),
            msvcrt.LK_NBLCK,
            1,
        )

        return "nt"

    import fcntl

    fcntl.flock(
        handle.fileno(),
        fcntl.LOCK_EX
        | fcntl.LOCK_NB,
    )

    return "posix"


def _unlock_handle(
    handle,
    platform,
):
    handle.seek(0)

    if platform == "nt":
        import msvcrt

        msvcrt.locking(
            handle.fileno(),
            msvcrt.LK_UNLCK,
            1,
        )

        return

    import fcntl

    fcntl.flock(
        handle.fileno(),
        fcntl.LOCK_UN,
    )


@contextmanager
def _process_lock(path):
    path = Path(path)

    handle = path.open(
        "a+b"
    )

    locked = False
    platform = None

    try:
        try:
            platform = _lock_handle(
                handle
            )

        except OSError as exc:
            raise RuntimeError(
                "funding runtime already locked"
            ) from exc

        locked = True

        yield path

    finally:
        if locked:
            _unlock_handle(
                handle,
                platform,
            )

        handle.close()


def _validate_poll_seconds(
    value,
):
    if isinstance(
        value,
        bool,
    ):
        raise TypeError(
            "poll seconds must be numeric"
        )

    try:
        value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise TypeError(
            "poll seconds must be numeric"
        ) from exc

    if not (
        0.0
        < value
        <= MAX_WAIT_POLL_SECONDS
    ):
        raise ValueError(
            "poll seconds must be > 0 and <= 5"
        )

    return value


def _heartbeat_body(
    *,
    status,
    started_at,
    updated_at,
    iterations,
    adapter_result,
):
    body = {
        "schema":
            HEARTBEAT_SCHEMA,

        "runtime_schema":
            RUNTIME_SCHEMA,

        "status":
            status,

        "started_at":
            started_at.isoformat(),

        "updated_at":
            updated_at.isoformat(),

        "iterations":
            int(iterations),

        "heartbeat_is_evidence":
            False,

        "pid":
            os.getpid(),

        "last_adapter_status":
            None,

        "last_slot":
            None,
    }

    if adapter_result is not None:
        body[
            "last_adapter_status"
        ] = adapter_result.get(
            "status"
        )

        body[
            "last_slot"
        ] = adapter_result.get(
            "slot"
        )

    return body


def _previous_heartbeat_clock_anchor(path):
    """Return the last valid operational clock anchor, if available.

    Heartbeat remains explicitly non-evidentiary.  A valid previous
    heartbeat may only constrain runtime clock monotonicity across process
    restarts.  Malformed metadata is replaceable and contributes no anchor.
    """

    path = Path(path)

    if not path.is_file():
        return None

    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return None

    if not isinstance(
        value,
        dict,
    ):
        return None

    expected_keys = {
        "schema",
        "runtime_schema",
        "status",
        "started_at",
        "updated_at",
        "iterations",
        "heartbeat_is_evidence",
        "pid",
        "last_adapter_status",
        "last_slot",
    }

    if set(value) != expected_keys:
        return None

    if (
        value["schema"]
        != HEARTBEAT_SCHEMA
        or value[
            "runtime_schema"
        ]
        != RUNTIME_SCHEMA
        or value[
            "heartbeat_is_evidence"
        ]
        is not False
    ):
        return None

    status = value[
        "status"
    ]

    if status not in (
        "STARTED",
        "RUNNING",
        "STOPPED",
    ):
        return None

    iterations = value[
        "iterations"
    ]

    if (
        isinstance(
            iterations,
            bool,
        )
        or not isinstance(
            iterations,
            int,
        )
        or iterations < 0
    ):
        return None

    pid = value[
        "pid"
    ]

    if (
        isinstance(
            pid,
            bool,
        )
        or not isinstance(
            pid,
            int,
        )
        or pid <= 0
    ):
        return None

    last_adapter_status = value[
        "last_adapter_status"
    ]

    if (
        last_adapter_status
        is not None
        and (
            not isinstance(
                last_adapter_status,
                str,
            )
            or not last_adapter_status
        )
    ):
        return None

    last_slot = value[
        "last_slot"
    ]

    if (
        last_slot is not None
        and (
            not isinstance(
                last_slot,
                str,
            )
            or not last_slot
        )
    ):
        return None

    if iterations == 0:
        if (
            last_adapter_status
            is not None
            or last_slot
            is not None
        ):
            return None

    else:
        if last_adapter_status is None:
            return None

    if (
        status == "STARTED"
        and iterations != 0
    ):
        return None

    try:
        started_at = _utc(
            value[
                "started_at"
            ]
        )

        updated_at = _utc(
            value[
                "updated_at"
            ]
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if updated_at < started_at:
        return None

    if (
        status == "STARTED"
        and updated_at != started_at
    ):
        return None

    return updated_at



def run_forever(
    state,
    *,
    clock=_now,
    sleeper=time.sleep,
    run_once_callable=live_adapter.run_once,
    stop_requested=None,
    poll_seconds=MAX_WAIT_POLL_SECONDS,
    max_iterations=None,
):
    """Run one long-lived process over an already-activated Funding state."""

    root = Path(state)

    # Critical authority boundary:
    # runtime validates an existing activation but never initializes one.
    runner.load_config(
        root
    )

    poll_seconds = (
        _validate_poll_seconds(
            poll_seconds
        )
    )

    if not callable(clock):
        raise TypeError(
            "clock callable required"
        )

    if not callable(sleeper):
        raise TypeError(
            "sleeper callable required"
        )

    if not callable(
        run_once_callable
    ):
        raise TypeError(
            "run_once callable required"
        )

    if stop_requested is None:
        stop_requested = (
            lambda: False
        )

    if not callable(
        stop_requested
    ):
        raise TypeError(
            "stop_requested callable required"
        )

    if max_iterations is not None:
        if (
            isinstance(
                max_iterations,
                bool,
            )
            or not isinstance(
                max_iterations,
                int,
            )
            or max_iterations < 1
        ):
            raise ValueError(
                "max_iterations must be positive integer or None"
            )

    runtime = (
        root
        / RUNTIME_DIRECTORY
    )

    runtime.mkdir(
        exist_ok=True
    )

    if not runtime.is_dir():
        raise ValueError(
            "runtime metadata path is not directory"
        )

    lock_path = (
        runtime
        / LOCK_FILE
    )

    heartbeat_path = (
        runtime
        / HEARTBEAT_FILE
    )

    previous = {
        "value": None,
    }

    def guarded_clock():
        current = _utc(
            clock()
        )

        prior = previous[
            "value"
        ]

        if (
            prior is not None
            and current < prior
        ):
            raise ValueError(
                "funding runtime clock moved backwards"
            )

        previous[
            "value"
        ] = current

        return current

    with _process_lock(
        lock_path
    ):
        previous_anchor = (
            _previous_heartbeat_clock_anchor(
                heartbeat_path
            )
        )

        started_at = (
            guarded_clock()
        )

        if (
            previous_anchor is not None
            and started_at
            < previous_anchor
        ):
            raise ValueError(
                "funding runtime clock moved backwards across restart"
            )

        iterations = 0
        last_result = None

        _atomic_json(
            heartbeat_path,
            _heartbeat_body(
                status="STARTED",
                started_at=started_at,
                updated_at=started_at,
                iterations=iterations,
                adapter_result=None,
            ),
        )

        while True:
            if stop_requested():
                break

            observed_at = (
                guarded_clock()
            )

            _atomic_json(
                heartbeat_path,
                _heartbeat_body(
                    status="RUNNING",
                    started_at=started_at,
                    updated_at=observed_at,
                    iterations=iterations,
                    adapter_result=last_result,
                ),
            )

            result = run_once_callable(
                root,
                clock=guarded_clock,
            )

            if not isinstance(
                result,
                dict,
            ):
                raise TypeError(
                    "adapter result must be object"
                )

            status = result.get(
                "status"
            )

            if (
                not isinstance(
                    status,
                    str,
                )
                or not status
            ):
                raise ValueError(
                    "adapter result status missing"
                )

            iterations += 1
            last_result = result

            updated_at = (
                previous["value"]
                if previous["value"] is not None
                else observed_at
            )

            _atomic_json(
                heartbeat_path,
                _heartbeat_body(
                    status="RUNNING",
                    started_at=started_at,
                    updated_at=updated_at,
                    iterations=iterations,
                    adapter_result=last_result,
                ),
            )

            if (
                max_iterations is not None
                and iterations
                >= max_iterations
            ):
                break

            if stop_requested():
                break

            sleeper(
                poll_seconds
            )

        stopped_at = (
            guarded_clock()
        )

        _atomic_json(
            heartbeat_path,
            _heartbeat_body(
                status="STOPPED",
                started_at=started_at,
                updated_at=stopped_at,
                iterations=iterations,
                adapter_result=last_result,
            ),
        )

        return {
            "schema":
                RUNTIME_SCHEMA,

            "status":
                "STOPPED",

            "started_at":
                started_at.isoformat(),

            "stopped_at":
                stopped_at.isoformat(),

            "iterations":
                iterations,

            "last_adapter_status":
                (
                    None
                    if last_result is None
                    else last_result.get(
                        "status"
                    )
                ),

            "last_slot":
                (
                    None
                    if last_result is None
                    else last_result.get(
                        "slot"
                    )
                ),
        }