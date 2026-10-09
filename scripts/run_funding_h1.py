"""Explicit execution boundary for an already-activated Funding H1 runtime.

The wrapper accepts one explicit state root. It never derives the frozen
state-root template, never initializes state, never backfills data, and never
installs or manages Windows scheduled tasks.
"""

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


from core.scientific import funding_h1_runner as runner
from core.scientific import funding_h1_runtime as runtime


WRAPPER_SCHEMA = "funding-h1-execution-wrapper-v1"
REQUIRED_STATE_LEAF = "funding-h1-v1"


def _outside_repository(path):
    repository = REPO_ROOT.resolve(
        strict=True
    )

    try:
        path.relative_to(
            repository
        )

    except ValueError:
        return True

    return False


def validate_state(value):
    """Validate one explicit pre-existing activated state root."""

    raw = Path(value)

    if not raw.is_absolute():
        raise ValueError(
            "absolute state path required"
        )

    if raw.name != REQUIRED_STATE_LEAF:
        raise ValueError(
            "funding-h1-v1 state leaf required"
        )

    if not raw.exists():
        raise FileNotFoundError(
            "funding state does not exist"
        )

    if not raw.is_dir():
        raise NotADirectoryError(
            "funding state must be directory"
        )

    if raw.is_symlink():
        raise ValueError(
            "funding state symlink forbidden"
        )

    root = raw.resolve(
        strict=True
    )

    if not _outside_repository(
        root
    ):
        raise ValueError(
            "funding state must be outside repository"
        )

    # Validation only. Never initializes state.
    runner.load_config(
        root
    )

    activation_slot = (
        runner.activation_slot(
            root
        )
    )

    return (
        root,
        activation_slot,
    )


def check_state(value):
    root, activation_slot = (
        validate_state(
            value
        )
    )

    return {
        "schema":
            WRAPPER_SCHEMA,

        "status":
            "READY",

        "state":
            str(root),

        "activation_slot":
            activation_slot.isoformat(),

        "runtime_schema":
            runtime.RUNTIME_SCHEMA,

        "state_initialized":
            False,

        "network_executed":
            False,
    }


def _parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    for name in (
        "check",
        "run",
    ):
        child = subparsers.add_parser(
            name
        )

        child.add_argument(
            "--state",
            required=True,
        )

    return parser


def main(
    argv=None,
    *,
    run_runtime=None,
):
    args = _parser().parse_args(
        argv
    )

    if args.command == "check":
        body = check_state(
            args.state
        )

        print(
            json.dumps(
                body,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )

        return 0

    root, _ = validate_state(
        args.state
    )

    if run_runtime is None:
        run_runtime = (
            runtime.run_forever
        )

    if not callable(
        run_runtime
    ):
        raise TypeError(
            "runtime callable required"
        )

    run_runtime(
        root
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )