"""Create-only dataset-role activation for future Price/OHLCV evidence.

This module performs no market capture, no observation admission and no replay.
It binds a dataset role prospectively to the frozen Price capture surface.
Historical Price observations can never acquire role through this contract.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import uuid


_REPO = Path(__file__).resolve().parents[2]

FROZEN_PRICE_SURFACE = {
    "core/market_mechanics/binance_live_adapter.py":
        "3d7c5ed0ee83b8e0354a6a1264b766df1a6ed467b6318c0553ed9bbee1108e5a",
    "core/scientific/prospective_receipts.py":
        "5b3a573bc9c90b848fe7a746cd2431f7704a130320ad609a2af442dfb2ae1a96",
    "core/scientific/price_continuity.py":
        "7758d84da7d09b411fa4425262fc38bc3921793de1576e20833bb47e34491f42",
    "scripts/capture_price_h1.py":
        "b551eddb2d3265992ab7108b4062b3bc6fbc971219342076d7609104abc0d62a",
}

SCHEMA = "price-role-activation-v1"
PRICE_CONTRACT = "binance-usdm-h1-rest-v1"
INSTRUMENT = "BTCUSDT"
FEATURE = "Price/OHLCV"
ROLES = {"PILOT", "DISCOVERY", "CONFIRMATION"}


def _now():
    return datetime.now(timezone.utc)


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _utc(value):
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError("timezone-aware datetime required")

    return value.astimezone(timezone.utc)


def verify_frozen_price_surface(repo_root=None):
    repo = Path(repo_root) if repo_root is not None else _REPO

    if not repo.is_absolute():
        raise ValueError("absolute repository root required")

    for relative, expected in FROZEN_PRICE_SURFACE.items():
        raw = (repo / relative).read_bytes().replace(b"\r\n", b"\n")

        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(
                "frozen Price source hash mismatch: " + relative
            )

    return True


def build_activation(*, state_root, repo_root, observed_at, dataset_role):
    if dataset_role not in ROLES:
        raise ValueError("explicit supported dataset role required")

    observed = _utc(observed_at)

    root = Path(state_root)
    repo = Path(repo_root)

    if not root.is_absolute() or not repo.is_absolute():
        raise ValueError("absolute paths required")

    if root.exists():
        raise FileExistsError("activation state already exists")

    if not root.parent.is_dir():
        raise ValueError("activation parent must already exist")

    repo = repo.resolve(strict=True)
    root = root.resolve(strict=False)

    if root == repo or repo in root.parents:
        raise ValueError("activation state must remain outside repository")

    verify_frozen_price_surface(repo)

    body = {
        "schema": SCHEMA,
        "price_contract": PRICE_CONTRACT,
        "instrument": INSTRUMENT,
        "feature": FEATURE,
        "dataset_role": dataset_role,
        "observed_at": observed.isoformat(),
        "not_before": observed.isoformat(),
        "state_root": str(root),
        "frozen_price_surface": dict(FROZEN_PRICE_SURFACE),
    }

    return {
        **body,
        "activation_id":
            hashlib.sha256(_canonical(body)).hexdigest(),
    }


def activate(*, state_root, repo_root, dataset_role):
    # Operational activation time is sampled here. The caller may choose a
    # dataset role but may not claim an earlier activation timestamp.
    observed_at = _utc(_now())

    config = build_activation(
        state_root=state_root,
        repo_root=repo_root,
        observed_at=observed_at,
        dataset_role=dataset_role,
    )

    root = Path(config["state_root"])
    staging = root.parent / (
        "." + root.name + ".activating-" + uuid.uuid4().hex
    )

    staging.mkdir()

    published = False

    try:
        target = staging / "config.json"

        with target.open("xb") as stream:
            stream.write(_canonical(config))
            stream.flush()
            os.fsync(stream.fileno())

        raw = target.read_bytes()
        loaded = json.loads(raw)

        if raw != _canonical(config) or loaded != config:
            raise ValueError("activation write verification failed")

        if root.exists():
            raise FileExistsError("activation state already exists")

        os.rename(staging, root)
        published = True

    finally:
        if not published and staging.exists():
            config_path = staging / "config.json"

            if config_path.exists():
                config_path.unlink()

            staging.rmdir()

    return config


def load_activation(state_root, *, repo_root):
    root = Path(state_root)

    raw = (root / "config.json").read_bytes()
    config = json.loads(raw)

    if raw != _canonical(config):
        raise ValueError("noncanonical Price role activation")

    required = {
        "schema",
        "price_contract",
        "instrument",
        "feature",
        "dataset_role",
        "observed_at",
        "not_before",
        "state_root",
        "frozen_price_surface",
        "activation_id",
    }

    if set(config) != required:
        raise ValueError("unexpected Price activation fields")

    if (
        config["schema"] != SCHEMA
        or config["price_contract"] != PRICE_CONTRACT
        or config["instrument"] != INSTRUMENT
        or config["feature"] != FEATURE
        or config["dataset_role"] not in ROLES
        or config["state_root"] != str(root.resolve(strict=True))
        or config["frozen_price_surface"]
        != FROZEN_PRICE_SURFACE
    ):
        raise ValueError("Price activation contract mismatch")

    observed = _utc(datetime.fromisoformat(config["observed_at"]))
    not_before = _utc(datetime.fromisoformat(config["not_before"]))

    if observed != not_before:
        raise ValueError("Price activation chronology mismatch")

    body = {
        key: config[key]
        for key in config
        if key != "activation_id"
    }

    expected = hashlib.sha256(_canonical(body)).hexdigest()

    if config["activation_id"] != expected:
        raise ValueError("Price activation identity mismatch")

    verify_frozen_price_surface(repo_root)

    return config
