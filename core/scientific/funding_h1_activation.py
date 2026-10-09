"""Atomic explicit activation for prospective Funding H1 state.

This module performs:
- no HTTP
- no scheduling
- no ledger writes
- no capture
- no backfill

Activation is a create-only operator transaction.

The atomic directory publication is the commit point.  No fallible
verification is performed after that commit point.
"""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import shutil
import uuid

from . import funding_continuity as fc
from . import funding_h1_runner as runner


ACTIVATION_SCHEMA = "funding-h1-activation-v1"
MINIMUM_LEAD = timedelta(seconds=600)
REQUIRED_STATE_LEAF = "funding-h1-v1"


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


def select_activation_slot(now):
    """First H1 boundary at or after now + frozen 600 second lead."""

    threshold = (
        _utc(now)
        + MINIMUM_LEAD
    )

    candidate = fc.hour(
        threshold
    )

    if candidate < threshold:
        candidate += fc.HOUR

    return candidate


def validate_state_root(
    state,
    *,
    repo_root,
):
    root_input = Path(state)

    if not root_input.is_absolute():
        raise ValueError(
            "absolute state root required"
        )

    repo_input = Path(repo_root)

    if not repo_input.is_absolute():
        raise ValueError(
            "absolute repository root required"
        )

    if not repo_input.exists():
        raise ValueError(
            "repository root must exist"
        )

    if not repo_input.is_dir():
        raise ValueError(
            "repository root must be directory"
        )

    if root_input.is_symlink():
        raise ValueError(
            "funding state root symlink forbidden"
        )

    repo = repo_input.resolve(
        strict=True
    )

    root = root_input.resolve(
        strict=False
    )

    if root.name != REQUIRED_STATE_LEAF:
        raise ValueError(
            "funding state root leaf mismatch"
        )

    try:
        root.relative_to(repo)

    except ValueError:
        pass

    else:
        raise ValueError(
            "funding state must remain outside repository"
        )

    parent = root.parent

    if not parent.exists():
        raise ValueError(
            "funding state parent must already exist"
        )

    if not parent.is_dir():
        raise ValueError(
            "funding state parent must be directory"
        )

    return root


def _activation_residue(root):
    return tuple(
        sorted(
            root.parent.glob(
                "."
                + REQUIRED_STATE_LEAF
                + ".activating-*"
            ),
            key=lambda item:
                item.name,
        )
    )


def activate(
    state,
    *,
    now,
    repo_root,
):
    """Atomically create one immutable Funding H1 activation state."""

    observed_at = _utc(
        now
    )

    root = validate_state_root(
        state,
        repo_root=repo_root,
    )

    if root.exists():
        raise FileExistsError(
            "funding activation state already exists"
        )

    residue = _activation_residue(
        root
    )

    if residue:
        raise FileExistsError(
            "stale funding activation staging residue exists"
        )

    activation = select_activation_slot(
        observed_at
    )

    if (
        activation
        < observed_at + MINIMUM_LEAD
    ):
        raise ValueError(
            "activation lead invariant violated"
        )

    staging = (
        root.parent
        / (
            "."
            + REQUIRED_STATE_LEAF
            + ".activating-"
            + uuid.uuid4().hex
        )
    )

    if staging.exists():
        raise FileExistsError(
            "activation staging path already exists"
        )

    published = False

    try:
        runner.initialize(
            staging,
            activation,
        )

        config = runner.load_config(
            staging
        )

        if (
            config["activation_slot"]
            != activation.isoformat()
        ):
            raise ValueError(
                "activation configuration mismatch"
            )

        if (
            config["retry_policy"]
            != "NONE"
        ):
            raise ValueError(
                "activation retry policy mismatch"
            )

        if (
            config[
                "target_offset_seconds"
            ]
            != 15
        ):
            raise ValueError(
                "activation target mismatch"
            )

        if (
            config[
                "slot_deadline_seconds"
            ]
            != 120
        ):
            raise ValueError(
                "activation deadline mismatch"
            )

        os.replace(
            staging,
            root,
        )

        published = True

    finally:
        if (
            not published
            and staging.exists()
        ):
            shutil.rmtree(
                staging
            )

    # Atomic publication above is the transaction commit point.
    # Do not perform a fallible state read after publication.
    return {
        "schema":
            ACTIVATION_SCHEMA,

        "status":
            "ACTIVATED",

        "observed_at":
            observed_at.isoformat(),

        "activation_slot":
            activation.isoformat(),

        "minimum_lead_seconds":
            int(
                MINIMUM_LEAD.total_seconds()
            ),

        "state_root":
            str(root),
    }