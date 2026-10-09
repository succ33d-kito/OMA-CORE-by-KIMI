"""Bridge one verified premiumIndex capture into observations_v2.

This adapter performs no network access. It does not infer a funding payment,
cashflow, realized cost, PnL, or economic outcome.
"""

import json
from datetime import datetime, timezone

from .execution_observation import EvidenceKind
from .premium_index_capture import (
    ENDPOINT,
    SCHEMA as CAPTURE_SCHEMA,
    load_premium,
)
from .prospective_receipts import (
    _published_funding_rate,
    append_observation,
)


FEATURE = "FundingRate/Published"
CONTRACT = "binance-usdm-published-funding-rate-v1"
INSTRUMENT = "BTCUSDT"
SEMANTIC_STATUS = "PUBLISHED_RATE_NOT_CASHFLOW"


def _epoch_ms(value):
    return datetime.fromtimestamp(
        value / 1000,
        timezone.utc,
    )


def append_verified_funding_rate_observation(
    ledger,
    capture_directory,
    *,
    clock=None,
):
    """Append one verified published funding-rate snapshot.

    capture_directory must already be a persisted premium capture. Verification
    is delegated to load_premium(); this function never performs HTTP.

    The capture availability timestamp remains provenance. observations_v2
    assigns its own availability timestamp at ledger admission.
    """

    observation = load_premium(
        capture_directory
    )

    if (
        observation.instrument != INSTRUMENT
        or observation.venue != "Binance USDⓈ-M"
        or observation.product != "linear perpetual"
        or observation.dataset_role.value != "PILOT"
        or len(observation.receipts) != 1
    ):
        raise ValueError(
            "unsupported premium observation boundary"
        )

    receipt = observation.receipts[0]

    if (
        receipt.kind is not EvidenceKind.MARK_FUNDING
        or receipt.source != ENDPOINT
        or receipt.dataset_role.value != "PILOT"
    ):
        raise ValueError(
            "unsupported premium receipt boundary"
        )

    if (
        receipt.request_started_at is None
        or receipt.received_at is None
        or receipt.available_at is None
        or receipt.exchange_at is None
    ):
        raise ValueError(
            "complete capture chronology required"
        )

    if observation.decision_at != receipt.available_at:
        raise ValueError(
            "capture projection must use verified availability"
        )

    if not (
        receipt.exchange_at
        <= receipt.received_at
        <= receipt.available_at
    ):
        raise ValueError(
            "noncausal premium capture chronology"
        )

    # load_premium() has already authenticated these persisted bytes and
    # ExecutionReceipt has already validated the provider response surface.
    raw = json.loads(
        receipt.response_json
    )

    next_funding_ms = raw.get(
        "nextFundingTime"
    )

    next_funding_at = (
        _epoch_ms(next_funding_ms).isoformat()
        if next_funding_ms is not None
        else None
    )

    payload = {
        "funding_rate":
            raw["lastFundingRate"],
        "mark_price":
            raw["markPrice"],
        "index_price":
            raw["indexPrice"],
        "exchange_at":
            receipt.exchange_at.isoformat(),
        "next_funding_at":
            next_funding_at,
    }

    provenance = {
        "contract":
            CONTRACT,
        "semantic_status":
            SEMANTIC_STATUS,
        "capture_schema":
            CAPTURE_SCHEMA,
        "capture_receipt_id":
            receipt.receipt_id,
        "capture_provenance_sha256":
            receipt.provenance_sha256,
        "capture_identity":
            receipt.identity,
        "capture_request_started_at":
            receipt.request_started_at.isoformat(),
        "capture_received_at":
            receipt.received_at.isoformat(),
        "capture_available_at":
            receipt.available_at.isoformat(),
        "raw_response":
            receipt.response_json,
    }

    # Preflight against the exact causal FundingRate/Published contract before
    # persistence. This prevents an available-but-causally-invalid raw row from
    # entering observations_v2.
    candidate = {
        "source":
            ENDPOINT,
        "instrument":
            INSTRUMENT,
        "feature":
            FEATURE,
        "event_time":
            receipt.exchange_at.isoformat(),
        "source_metric_at":
            receipt.exchange_at.isoformat(),
        "received_at":
            receipt.received_at.isoformat(),
        "payload":
            payload,
        "provenance":
            provenance,
        "dependencies":
            [],
        "derived":
            False,
    }

    if not _published_funding_rate(
        candidate
    ):
        raise ValueError(
            "verified capture does not satisfy "
            "published funding-rate contract"
        )

    def admission_time():
        admitted = (
            clock()
            if clock is not None
            else datetime.now(timezone.utc)
        )

        if (
            not isinstance(admitted, datetime)
            or admitted.tzinfo is None
            or admitted.utcoffset() is None
        ):
            raise ValueError(
                "ledger admission clock must be timezone-aware"
            )

        admitted = admitted.astimezone(
            timezone.utc
        )

        if admitted < receipt.available_at:
            raise ValueError(
                "ledger admission precedes verified "
                "capture availability"
            )

        return admitted

    return append_observation(
        ledger,
        source=ENDPOINT,
        instrument=INSTRUMENT,
        feature=FEATURE,
        event_time=receipt.exchange_at,
        source_metric_at=receipt.exchange_at,
        received_at=receipt.received_at,
        payload=payload,
        provenance=provenance,
        dependencies=(),
        derived=False,
        clock=clock,
        admission_check=admission_time,
    )
