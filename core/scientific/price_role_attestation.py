"""Prospective dataset-role attestation for Price/OHLCV.

A role may be attached to Price only when:
1. a valid PriceRoleActivation already exists,
2. an immutable slot authorization is persisted before capture evidence,
3. the exact Price observation passes its frozen semantic/causal gate, and
4. a derived attestation depends on that exact observation.

No historical observation is rewritten or relabelled.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from .price_role_activation import (
    FEATURE,
    FROZEN_PRICE_SURFACE,
    INSTRUMENT,
    PRICE_CONTRACT,
    ROLES,
    SCHEMA as ACTIVATION_SCHEMA,
    load_activation,
)
from .prospective_receipts import (
    append_observation,
    observation_hash,
    observation_snapshot,
    snapshot_causally_available,
)


AUTH_SCHEMA = "price-role-capture-authorization-v1"
ATTESTATION_CONTRACT = "price-role-attestation-v1"
ATTESTATION_FEATURE = "PriceRoleAttestation/v1"
ATTESTATION_SOURCE = "oma://scientific/price-role-attestation-v1"

_ACTIVATION_FIELDS = {
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

_AUTH_FIELDS = {
    "schema",
    "slot_id",
    "activation_id",
    "dataset_role",
    "instrument",
    "feature",
    "price_contract",
    "expected_event_time",
    "authorized_at",
    "activation_not_before",
    "authorization_id",
}


def _now():
    return datetime.now(timezone.utc)


def _utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError("timezone-aware timestamp required")

    return value.astimezone(timezone.utc)


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _slot_id(activation_id, expected_event_time):
    return observation_hash([
        AUTH_SCHEMA,
        activation_id,
        _utc(expected_event_time).isoformat(),
    ])


def _exclusive_json(path, body):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("xb") as stream:
        stream.write(_canonical(body))
        stream.flush()
        os.fsync(stream.fileno())


def _embedded_activation_valid(config):
    try:
        if set(config) != _ACTIVATION_FIELDS:
            return False

        if (
            config["schema"] != ACTIVATION_SCHEMA
            or config["price_contract"] != PRICE_CONTRACT
            or config["instrument"] != INSTRUMENT
            or config["feature"] != FEATURE
            or config["dataset_role"] not in ROLES
            or config["frozen_price_surface"]
            != FROZEN_PRICE_SURFACE
        ):
            return False

        observed = _utc(config["observed_at"])
        not_before = _utc(config["not_before"])

        if observed != not_before:
            return False

        body = {
            key: config[key]
            for key in config
            if key != "activation_id"
        }

        return (
            config["activation_id"]
            == observation_hash(body)
        )

    except (
        ValueError,
        TypeError,
        KeyError,
        OverflowError,
    ):
        return False


def _validate_authorization_record(record, activation):
    if set(record) != _AUTH_FIELDS:
        raise ValueError("unexpected Price authorization fields")

    if (
        record["schema"] != AUTH_SCHEMA
        or record["activation_id"]
        != activation["activation_id"]
        or record["dataset_role"]
        != activation["dataset_role"]
        or record["instrument"] != INSTRUMENT
        or record["feature"] != FEATURE
        or record["price_contract"] != PRICE_CONTRACT
        or record["activation_not_before"]
        != activation["not_before"]
    ):
        raise ValueError("Price authorization contract mismatch")

    expected = _utc(record["expected_event_time"])

    if (
        expected.minute
        or expected.second
        or expected.microsecond
    ):
        raise ValueError("Price event must be aligned to UTC hour")

    expected_slot = _slot_id(
        activation["activation_id"],
        expected,
    )

    if record["slot_id"] != expected_slot:
        raise ValueError("Price authorization slot mismatch")

    authorized = _utc(record["authorized_at"])
    not_before = _utc(activation["not_before"])

    if authorized < not_before:
        raise ValueError(
            "authorization precedes activation"
        )

    body = {
        key: record[key]
        for key in record
        if key != "authorization_id"
    }

    if (
        record["authorization_id"]
        != observation_hash(body)
    ):
        raise ValueError(
            "Price authorization identity mismatch"
        )

    return record


def authorize_capture(
    activation_state,
    *,
    repo_root,
    expected_event_time,
):
    """Persist one create-only authorization before the frozen Price capture."""

    activation = load_activation(
        activation_state,
        repo_root=repo_root,
    )

    event = _utc(expected_event_time)

    if (
        event.minute
        or event.second
        or event.microsecond
    ):
        raise ValueError(
            "Price event must be aligned to UTC hour"
        )

    authorized = _utc(_now())

    if authorized < _utc(activation["not_before"]):
        raise ValueError("clock precedes Price activation")

    slot = _slot_id(
        activation["activation_id"],
        event,
    )

    body = {
        "schema": AUTH_SCHEMA,
        "slot_id": slot,
        "activation_id": activation["activation_id"],
        "dataset_role": activation["dataset_role"],
        "instrument": activation["instrument"],
        "feature": activation["feature"],
        "price_contract": activation["price_contract"],
        "expected_event_time": event.isoformat(),
        "authorized_at": authorized.isoformat(),
        "activation_not_before":
            activation["not_before"],
    }

    record = {
        **body,
        "authorization_id":
            observation_hash(body),
    }

    _exclusive_json(
        Path(activation_state)
        / "authorizations"
        / f"{slot}.json",
        record,
    )

    return record


def load_authorization(
    activation_state,
    slot_id,
    *,
    repo_root,
):
    activation = load_activation(
        activation_state,
        repo_root=repo_root,
    )

    path = (
        Path(activation_state)
        / "authorizations"
        / f"{slot_id}.json"
    )

    if not path.is_file():
        raise ValueError(
            "Price capture authorization not found"
        )

    raw = path.read_bytes()
    record = json.loads(raw)

    if raw != _canonical(record):
        raise ValueError(
            "noncanonical Price authorization"
        )

    return _validate_authorization_record(
        record,
        activation,
    )


def _price_envelope_valid(item):
    return (
        type(item) is dict
        and item.get("source")
        == "https://fapi.binance.com/fapi/v1/klines"
        and item.get("instrument") == INSTRUMENT
        and item.get("feature") == FEATURE
        and item.get("derived") is False
        and item.get("dependencies") == []
        and type(item.get("provenance")) is dict
        and item["provenance"].get("contract")
        == PRICE_CONTRACT
    )


def _attestation_identity(price):
    return observation_hash([
        ATTESTATION_SOURCE,
        price["instrument"],
        ATTESTATION_FEATURE,
        _utc(price["event_time"]).isoformat(),
        _utc(price["source_metric_at"]).isoformat(),
        [price["id"]],
        True,
    ])


def attest_price_observation(
    activation_state,
    ledger,
    *,
    repo_root,
    slot_id,
    observation_id,
):
    """Bind one pre-authorized slot to one exact verified Price observation."""

    activation = load_activation(
        activation_state,
        repo_root=repo_root,
    )

    authorization = load_authorization(
        activation_state,
        slot_id,
        repo_root=repo_root,
    )

    now = _utc(_now())

    rows, _ = observation_snapshot(
        ledger,
        read_only=True,
    )

    price = rows.get(observation_id)

    if not _price_envelope_valid(price):
        raise ValueError(
            "eligible Price/OHLCV observation required"
        )

    if (
        _utc(price["event_time"])
        != _utc(
            authorization["expected_event_time"]
        )
    ):
        raise ValueError(
            "Price observation does not match authorized slot"
        )

    if not snapshot_causally_available(
        rows,
        observation_id,
        now,
    ):
        raise ValueError(
            "Price observation fails causal semantic gate"
        )

    provenance = price["provenance"]

    try:
        first_capture_evidence = _utc(
            provenance["server_received_at"]
        )
    except (
        ValueError,
        TypeError,
        KeyError,
        OverflowError,
    ) as exc:
        raise ValueError(
            "Price capture timing evidence unavailable"
        ) from exc

    authorized = _utc(
        authorization["authorized_at"]
    )

    if authorized >= first_capture_evidence:
        raise ValueError(
            "Price authorization did not strictly precede earliest persisted capture evidence"
        )

    if (
        _utc(activation["not_before"])
        > authorized
    ):
        raise ValueError(
            "Price activation did not precede authorization"
        )

    payload = {
        "price_observation_id":
            price["id"],
        "price_observation_commitment":
            observation_hash(price),
        "activation_id":
            activation["activation_id"],
        "authorization_id":
            authorization["authorization_id"],
        "slot_id":
            authorization["slot_id"],
        "dataset_role":
            activation["dataset_role"],
    }

    provenance = {
        "contract": ATTESTATION_CONTRACT,
        "activation": activation,
        "authorization": authorization,
    }

    return append_observation(
        ledger,
        source=ATTESTATION_SOURCE,
        instrument=INSTRUMENT,
        feature=ATTESTATION_FEATURE,
        event_time=_utc(price["event_time"]),
        source_metric_at=_utc(
            price["source_metric_at"]
        ),
        received_at=now,
        payload=payload,
        provenance=provenance,
        dependencies=(price["id"],),
        derived=True,
        clock=lambda: now,
    )


def verified_price_role_attestation(
    known,
    price,
    dataset_role,
    cutoff,
):
    """Return the exact attestation row or None; never infer a role."""

    try:
        if dataset_role not in ROLES:
            return None

        if not _price_envelope_valid(price):
            return None

        identity = _attestation_identity(price)
        attestation = known.get(identity)

        if (
            type(attestation) is not dict
            or attestation.get("id") != identity
            or attestation.get("source")
            != ATTESTATION_SOURCE
            or attestation.get("instrument")
            != INSTRUMENT
            or attestation.get("feature")
            != ATTESTATION_FEATURE
            or attestation.get("derived") is not True
            or attestation.get("dependencies")
            != [price["id"]]
        ):
            return None

        if not snapshot_causally_available(
            known,
            identity,
            cutoff,
        ):
            return None

        payload = attestation.get("payload")
        provenance = attestation.get("provenance")

        if (
            type(payload) is not dict
            or set(payload) != {
                "price_observation_id",
                "price_observation_commitment",
                "activation_id",
                "authorization_id",
                "slot_id",
                "dataset_role",
            }
            or type(provenance) is not dict
            or set(provenance) != {
                "contract",
                "activation",
                "authorization",
            }
            or provenance["contract"]
            != ATTESTATION_CONTRACT
        ):
            return None

        activation = provenance["activation"]
        authorization = provenance["authorization"]

        if not _embedded_activation_valid(
            activation
        ):
            return None

        try:
            _validate_authorization_record(
                authorization,
                activation,
            )
        except (
            ValueError,
            TypeError,
            KeyError,
            OverflowError,
        ):
            return None

        if (
            activation["dataset_role"]
            != dataset_role
            or authorization["dataset_role"]
            != dataset_role
            or payload["dataset_role"]
            != dataset_role
        ):
            return None

        if (
            payload["price_observation_id"]
            != price["id"]
            or payload[
                "price_observation_commitment"
            ]
            != observation_hash(price)
            or payload["activation_id"]
            != activation["activation_id"]
            or payload["authorization_id"]
            != authorization["authorization_id"]
            or payload["slot_id"]
            != authorization["slot_id"]
        ):
            return None

        if (
            _utc(
                authorization[
                    "expected_event_time"
                ]
            )
            != _utc(price["event_time"])
        ):
            return None

        if (
            _utc(activation["not_before"])
            > _utc(
                authorization["authorized_at"]
            )
        ):
            return None

        if (
            _utc(
                authorization["authorized_at"]
            )
            >= _utc(
                price["provenance"][
                    "server_received_at"
                ]
            )
        ):
            return None

        return attestation

    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        OverflowError,
    ):
        return None


def price_role_authenticated(
    known,
    price,
    dataset_role,
    cutoff,
):
    return (
        verified_price_role_attestation(
            known,
            price,
            dataset_role,
            cutoff,
        )
        is not None
    )
