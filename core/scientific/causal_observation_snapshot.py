"""Read-only causal as-of projection over observations_v2.

STEP 49A.1.

This module does not capture data, admit observations, infer missing values,
construct trading signals, write WorldState, write EvidenceGraph, or perform
network access.

It authenticates the observations_v2 hash chain through observation_snapshot()
and exposes only raw observations causally available at an explicit cutoff.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import json
from pathlib import Path

from .metrics_snapshot_gate import metrics_snapshot_available
from .metrics_publication import observation_snapshot, publication_for
from .execution_observation import EvidenceKind, ExecutionReceipt
from .nuisance_pilot_contracts import DatasetRole
from .price_role_attestation import (
    price_role_authenticated,
    verified_price_role_attestation,
)

from .prospective_receipts import (
    observation_hash,
    snapshot_causally_available,
)


BTC_CAUSAL_FEATURES = (
    "Price/OHLCV",
    "FundingRate/Published",
    "MarketMetrics/OpenInterest",
    "MarketMetrics/OpenInterestValue",
    "MarketMetrics/TopTraderAccountPositioning",
    "MarketMetrics/TopTraderPositionPositioning",
    "MarketMetrics/GlobalPositioning",
    "MarketMetrics/TakerBuySellRatio",
)


def _role_bearing_feature(feature):
    return (
        feature.startswith("MarketMetrics/")
        or feature == "FundingRate/Published"
    )


def _funding_role_authenticated(item, dataset_role):
    if dataset_role != "PILOT":
        return False

    try:
        provenance = (
            json.loads(item.provenance_json)
            if hasattr(item, "provenance_json")
            else item["provenance"]
        )

        if (
            provenance.get("dataset_role") != "PILOT"
            or provenance.get("dataset_role_contract")
            != "funding-dataset-role-auth-v1"
        ):
            return False

        source = (
            item.source
            if hasattr(item, "source")
            else item["source"]
        )

        received_at = (
            item.received_at
            if hasattr(item, "received_at")
            else _utc(item["received_at"])
        )

        available_at = (
            item.available_at
            if hasattr(item, "available_at")
            else _utc(item["available_at"])
        )

        receipt = ExecutionReceipt(
            kind=EvidenceKind.MARK_FUNDING,
            source=source,
            receipt_id=provenance["capture_receipt_id"],
            provenance_sha256=
                provenance["capture_provenance_sha256"],
            response_json=provenance["raw_response"],
            dataset_role=DatasetRole.PILOT,
            request_started_at=_utc(
                provenance["capture_request_started_at"]
            ),
            received_at=_utc(
                provenance["capture_received_at"]
            ),
            available_at=_utc(
                provenance["capture_available_at"]
            ),
            fee_account_reference=None,
        )

        return (
            receipt.identity
            == provenance.get("capture_identity")
            and receipt.received_at == received_at
            and receipt.available_at <= available_at
        )

    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        OverflowError,
    ):
        return False


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
    )


@dataclass(frozen=True, slots=True)
class CausalObservation:
    id: str
    source: str
    instrument: str
    feature: str
    event_time: datetime
    source_metric_at: datetime
    received_at: datetime
    available_at: datetime
    payload_json: str
    provenance_json: str
    role_attestation_json: str | None = None

    def to_dict(self):
        result = {
            "id": self.id,
            "source": self.source,
            "instrument": self.instrument,
            "feature": self.feature,
            "event_time": self.event_time.isoformat(),
            "source_metric_at": self.source_metric_at.isoformat(),
            "received_at": self.received_at.isoformat(),
            "available_at": self.available_at.isoformat(),
            "payload": json.loads(self.payload_json),
            "provenance": json.loads(self.provenance_json),
        }

        if self.role_attestation_json is not None:
            result["role_attestation"] = json.loads(
                self.role_attestation_json
            )

        return result


def _price_projection_row(item):
    """Reconstruct the exact raw Price envelope committed by the attestation."""

    payload = json.loads(item.payload_json)
    available = item.available_at.isoformat()

    return {
        "id": item.id,
        "source": item.source,
        "instrument": item.instrument,
        "feature": item.feature,
        "event_time": item.event_time.isoformat(),
        "source_metric_at":
            item.source_metric_at.isoformat(),
        "received_at": item.received_at.isoformat(),
        "available_at": available,
        "computed_at": None,
        "payload": payload,
        "payload_hash": observation_hash(payload),
        "provenance": json.loads(
            item.provenance_json
        ),
        "dependencies": [],
        "derived": False,
        "recorded_at": available,
    }


def _projected_price_role_authenticated(
    item,
    dataset_role,
    cutoff,
):
    if item.role_attestation_json is None:
        return False

    try:
        attestation = json.loads(
            item.role_attestation_json
        )

        price = _price_projection_row(item)

        known = {
            price["id"]: price,
            attestation["id"]: attestation,
        }

        return price_role_authenticated(
            known,
            price,
            dataset_role,
            cutoff,
        )

    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        OverflowError,
    ):
        return False


@dataclass(frozen=True, slots=True)
class CausalObservationSnapshot:
    instrument: str
    as_of: datetime
    requested_features: tuple[str, ...]
    observations: tuple[CausalObservation, ...]
    missing_features: tuple[str, ...]
    dataset_role: str | None = None
    snapshot_id: str = field(init=False)

    def __post_init__(self):
        if self.dataset_role is not None and self.dataset_role not in ("PILOT", "DISCOVERY", "CONFIRMATION"):
            raise ValueError("unsupported dataset role")
        if not self.instrument:
            raise ValueError("instrument required")

        cutoff = _utc(self.as_of)
        object.__setattr__(self, "as_of", cutoff)

        if (
            type(self.requested_features) is not tuple
            or not self.requested_features
            or len(set(self.requested_features))
            != len(self.requested_features)
        ):
            raise ValueError(
                "unique requested feature tuple required"
            )

        if type(self.observations) is not tuple:
            raise TypeError("immutable observation tuple required")

        if type(self.missing_features) is not tuple:
            raise TypeError("immutable missing feature tuple required")

        present = tuple(
            item.feature
            for item in self.observations
        )

        if len(set(present)) != len(present):
            raise ValueError(
                "one selected observation per feature required"
            )

        expected_missing = tuple(
            feature
            for feature in self.requested_features
            if feature not in set(present)
        )

        if self.missing_features != expected_missing:
            raise ValueError(
                "missing-feature contract mismatch"
            )

        for item in self.observations:
            if item.role_attestation_json is not None:
                if (
                    self.dataset_role is None
                    or item.feature != "Price/OHLCV"
                ):
                    raise ValueError(
                        "Price role attestation outside scoped Price observation"
                    )

            if self.dataset_role is not None:
                provenance = json.loads(item.provenance_json)
                role_valid = (
                    (
                        item.feature.startswith("MarketMetrics/")
                        and provenance.get("dataset_role")
                        == self.dataset_role
                    )
                    or (
                        item.feature == "FundingRate/Published"
                        and _funding_role_authenticated(
                            item,
                            self.dataset_role,
                        )
                    )
                    or (
                        item.feature == "Price/OHLCV"
                        and _projected_price_role_authenticated(
                            item,
                            self.dataset_role,
                            cutoff,
                        )
                    )
                )

                if not role_valid:
                    raise ValueError(
                        'observation role unavailable or incompatible'
                    )
            if item.instrument != self.instrument:
                raise ValueError("cross-instrument observation")
            if item.feature not in self.requested_features:
                raise ValueError("unrequested observation")
            if item.available_at > cutoff:
                raise ValueError("future observation in snapshot")

        commitment = {
            "schema":
                "causal-observation-snapshot-v1",
            **({"dataset_role": self.dataset_role} if self.dataset_role is not None else {}),
            "instrument":
                self.instrument,
            "as_of":
                cutoff.isoformat(),
            "requested_features":
                list(self.requested_features),
            "observations":
                [
                    item.to_dict()
                    for item in self.observations
                ],
            "missing_features":
                list(self.missing_features),
        }

        object.__setattr__(
            self,
            "snapshot_id",
            observation_hash(commitment),
        )

    def to_dict(self):
        return {
            "schema":
                "causal-observation-snapshot-v1",
            **({"dataset_role": self.dataset_role} if self.dataset_role is not None else {}),
            "snapshot_id":
                self.snapshot_id,
            "instrument":
                self.instrument,
            "as_of":
                self.as_of.isoformat(),
            "requested_features":
                list(self.requested_features),
            "observations":
                [
                    item.to_dict()
                    for item in self.observations
                ],
            "missing_features":
                list(self.missing_features),
        }


def _candidate(
    item,
    cutoff,
    *,
    role_attestation=None,
):
    if item.get("available_at") is None:
        return None

    if item.get("derived") is not False:
        return None

    if item.get("dependencies") != []:
        raise ValueError(
            "raw observation declares dependencies"
        )

    event = _utc(item["event_time"])
    metric = _utc(item["source_metric_at"])
    received = _utc(item["received_at"])
    available = _utc(item["available_at"])

    if not (
        event <= received
        and metric <= received
        and received <= available
    ):
        raise ValueError(
            "noncausal observation chronology"
        )

    if available > cutoff:
        return None

    if (
        not item.get("source")
        or not item.get("instrument")
        or not item.get("feature")
        or type(item.get("payload")) is not dict
        or type(item.get("provenance")) is not dict
        or not item["provenance"]
    ):
        raise ValueError(
            "incomplete observation envelope"
        )

    return CausalObservation(
        id=item["id"],
        source=item["source"],
        instrument=item["instrument"],
        feature=item["feature"],
        event_time=event,
        source_metric_at=metric,
        received_at=received,
        available_at=available,
        payload_json=_canonical(item["payload"]),
        provenance_json=_canonical(
            item["provenance"]
        ),
        role_attestation_json=(
            _canonical(role_attestation)
            if role_attestation is not None
            else None
        ),
    )


def load_causal_snapshot(
    ledger,
    *,
    instrument,
    as_of,
    features=BTC_CAUSAL_FEATURES,
    dataset_role=None,
):
    """Return latest unambiguous raw observation per feature as-of cutoff."""

    cutoff = _utc(as_of)
    if dataset_role is not None and dataset_role not in ("PILOT", "DISCOVERY", "CONFIRMATION"):
        raise ValueError("unsupported dataset role")

    if not instrument:
        raise ValueError("instrument required")

    features = tuple(features)

    if (
        not features
        or any(
            type(feature) is not str
            or not feature
            for feature in features
        )
        or len(set(features)) != len(features)
    ):
        raise ValueError(
            "unique non-empty features required"
        )

    rows, _ = observation_snapshot(
        Path(ledger),
        read_only=True,
    )

    grouped = {
        feature: []
        for feature in features
    }

    for item in rows.values():
        if (
            item.get("instrument") != instrument
            or item.get("feature") not in grouped
        ):
            continue

        role_attestation = None

        if dataset_role is not None:
            # Role-specific views consume only observations whose role is
            # authenticated by their source-specific boundary. Price remains
            # raw evidence; its separate derived attestation is authority
            # metadata and is never promoted to a market feature.
            if item['feature'].startswith('MarketMetrics/'):
                if (
                    item.get('provenance', {}).get('dataset_role')
                    != dataset_role
                ):
                    continue

            elif item['feature'] == 'FundingRate/Published':
                if not _funding_role_authenticated(
                    item,
                    dataset_role,
                ):
                    continue

            elif item['feature'] == 'Price/OHLCV':
                role_attestation = (
                    verified_price_role_attestation(
                        rows,
                        item,
                        dataset_role,
                        cutoff,
                    )
                )

                if role_attestation is None:
                    continue

            else:
                continue

        candidate = _candidate(
            item,
            cutoff,
            role_attestation=role_attestation,
        )

        if (
            candidate is not None
            and item['feature'] == 'FundingRate/Published'
        ):
            provenance = item.get('provenance', {})

            # Historical Funding evidence predates dataset-role provenance and
            # remains valid in unscoped mode. Once an observation claims any
            # role metadata, however, the complete role attestation becomes
            # mandatory even for an unscoped snapshot.
            if (
                'dataset_role' in provenance
                or 'dataset_role_contract' in provenance
            ) and not _funding_role_authenticated(
                item,
                'PILOT',
            ):
                continue

        if candidate is not None and item['feature'] in ('Price/OHLCV', 'FundingRate/Published'):
            # A persisted timestamp/hash is not provider/semantic evidence.
            # Reuse the existing raw source contract before causal projection.
            if not snapshot_causally_available(rows, item['id'], cutoff):
                continue

        if candidate is not None and item['feature'].startswith('MarketMetrics/'):
            if not metrics_snapshot_available(rows, item['id'], cutoff):
                continue
            publication = publication_for(rows, item['provenance']['bundle_id'])
            candidate = replace(candidate,
                available_at=max(candidate.available_at, _utc(publication['published_at'])),
                provenance_json=_canonical({**json.loads(candidate.provenance_json),
                    'durable_publication': publication}))

        if candidate is not None:
            grouped[candidate.feature].append(
                candidate
            )

    selected = []

    for feature in features:
        candidates = grouped[feature]

        if not candidates:
            continue

        latest_metric = max(
            item.source_metric_at
            for item in candidates
        )

        latest = [
            item
            for item in candidates
            if item.source_metric_at
            == latest_metric
        ]

        if len(latest) != 1:
            raise ValueError(
                "ambiguous latest observation "
                f"for {feature}"
            )

        selected.append(latest[0])

    present = {
        item.feature
        for item in selected
    }

    missing = tuple(
        feature
        for feature in features
        if feature not in present
    )

    return CausalObservationSnapshot(
        instrument=instrument,
        as_of=cutoff,
        requested_features=features,
        dataset_role=dataset_role,
        observations=tuple(selected),
        missing_features=missing,
    )