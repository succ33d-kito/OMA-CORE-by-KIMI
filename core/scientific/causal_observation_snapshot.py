"""Read-only causal as-of projection over observations_v2.

STEP 49A.1.

This module does not capture data, admit observations, infer missing values,
construct trading signals, write WorldState, write EvidenceGraph, or perform
network access.

It authenticates the observations_v2 hash chain through observation_snapshot()
and exposes only raw observations causally available at an explicit cutoff.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from .metrics_snapshot_gate import metrics_snapshot_available

from .prospective_receipts import (
    observation_hash,
    observation_snapshot,
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

    def to_dict(self):
        return {
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


@dataclass(frozen=True, slots=True)
class CausalObservationSnapshot:
    instrument: str
    as_of: datetime
    requested_features: tuple[str, ...]
    observations: tuple[CausalObservation, ...]
    missing_features: tuple[str, ...]
    snapshot_id: str = field(init=False)

    def __post_init__(self):
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
            if item.instrument != self.instrument:
                raise ValueError("cross-instrument observation")
            if item.feature not in self.requested_features:
                raise ValueError("unrequested observation")
            if item.available_at > cutoff:
                raise ValueError("future observation in snapshot")

        commitment = {
            "schema":
                "causal-observation-snapshot-v1",
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


def _candidate(item, cutoff):
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
    )


def load_causal_snapshot(
    ledger,
    *,
    instrument,
    as_of,
    features=BTC_CAUSAL_FEATURES,
):
    """Return latest unambiguous raw observation per feature as-of cutoff."""

    cutoff = _utc(as_of)

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

        candidate = _candidate(
            item,
            cutoff,
        )

        if candidate is not None and item['feature'] in ('Price/OHLCV', 'FundingRate/Published'):
            # A persisted timestamp/hash is not provider/semantic evidence.
            # Reuse the existing raw source contract before causal projection.
            if not snapshot_causally_available(rows, item['id'], cutoff):
                continue

        if candidate is not None and item['feature'].startswith('MarketMetrics/'):
            if not metrics_snapshot_available(rows, item['id'], cutoff):
                continue

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
        observations=tuple(selected),
        missing_features=missing,
    )