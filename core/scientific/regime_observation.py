"""Causal Regime observation derived from a certified prospective price window.

This adapter does not establish predictive performance. It converts an already-certified
81-bar Price/OHLCV window into the existing descriptive RegimeState and persists
that result through the generic derived-observation contract.
"""

from datetime import datetime, timezone

from core.market_mechanics.regime import classify_regime
from core.market_mechanics.state import build_market_state

from .prospective_receipts import (
    append_observation,
    observation_hash,
    observation_snapshot,
    snapshot_causally_available,
)


CERTIFICATE_SCHEMA = "price-81h-certificate-v1"
PRICE_FEATURE = "Price/OHLCV"
PRICE_CONTRACT = "binance-usdm-h1-rest-v1"
REGIME_FEATURE = "Regime"
INSTRUMENT = "BTCUSDT"
REGIME_PROVENANCE_SCHEMA = "regime-derived-observation-v1"


def _utc(value):
    if isinstance(value, datetime):
        result = value
    else:
        result = datetime.fromisoformat(str(value))

    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("UTC-aware datetime required")

    return result.astimezone(timezone.utc)


def append_certified_regime_observation(
    ledger,
    certificate,
    *,
    clock=None,
):
    """Append a descriptive Regime observation from one certified 81H window.

    The certificate is authenticated against the observation ledger before any
    derivation. All 81 price observations must already pass the causal gate.

    This function does not inspect outcomes and does not claim predictive value.
    """

    if type(certificate) is not dict:
        raise TypeError("certificate must be a dict")

    if certificate.get("schema") != CERTIFICATE_SCHEMA:
        raise ValueError("unsupported price certificate schema")

    if certificate.get("instrument") != INSTRUMENT:
        raise ValueError("unsupported certificate instrument")

    if certificate.get("feature") != PRICE_FEATURE:
        raise ValueError("certificate is not Price/OHLCV")

    if certificate.get("contract") != PRICE_CONTRACT:
        raise ValueError("unsupported price certificate contract")

    if certificate.get("number_of_bars") != 81:
        raise ValueError("regime requires exactly 81 certified bars")

    if certificate.get("gaps") != 0:
        raise ValueError("certificate contains gaps")

    if certificate.get("conflicts") != 0:
        raise ValueError("certificate contains conflicts")

    if certificate.get("historical_backfill") is not False:
        raise ValueError("historical backfill is not admissible")

    receipt_ids = tuple(certificate.get("receipt_ids", ()))

    if len(receipt_ids) != 81 or len(set(receipt_ids)) != 81:
        raise ValueError("certificate requires 81 unique receipt ids")

    known, prefixes = observation_snapshot(
        ledger,
        read_only=True,
    )

    ledger_count = certificate.get("ledger_observation_count")

    if (
        type(ledger_count) is not int
        or ledger_count < 81
        or ledger_count > len(prefixes)
    ):
        raise ValueError("invalid certificate ledger observation count")

    if prefixes[ledger_count - 1] != certificate.get("ledger_head"):
        raise ValueError("certificate ledger head mismatch")

    missing = tuple(
        identity
        for identity in receipt_ids
        if identity not in known
    )

    if missing:
        raise ValueError("certificate dependency missing from ledger")

    selected = [
        known[identity]
        for identity in receipt_ids
    ]

    if observation_hash(selected) != certificate.get("certified_set_hash"):
        raise ValueError("certificate set hash mismatch")

    event_times = [
        _utc(item["event_time"])
        for item in selected
    ]

    if event_times != sorted(event_times):
        raise ValueError("certificate observations are not ordered")

    if len(set(event_times)) != 81:
        raise ValueError("certificate event times are not unique")

    for first, second in zip(event_times, event_times[1:]):
        if (second - first).total_seconds() != 3600:
            raise ValueError("certificate observations are not H1 contiguous")

    if event_times[0] != _utc(certificate["first_event_time"]):
        raise ValueError("certificate first event mismatch")

    if event_times[-1] != _utc(certificate["last_event_time"]):
        raise ValueError("certificate last event mismatch")

    if any(
        item.get("feature") != PRICE_FEATURE
        or item.get("instrument") != INSTRUMENT
        for item in selected
    ):
        raise ValueError("certificate dependency universe mismatch")

    if any(
        item.get("provenance", {}).get("contract") != PRICE_CONTRACT
        for item in selected
    ):
        raise ValueError("dependency price contract mismatch")

    dependency_source_metric_at = [
        _utc(item["source_metric_at"])
        for item in selected
    ]

    dependency_received_at = [
        _utc(item["received_at"])
        for item in selected
    ]

    dependency_available = [
        _utc(item["available_at"])
        for item in selected
    ]

    latest_source_metric_at = max(
        dependency_source_metric_at
    )

    latest_received_at = max(
        dependency_received_at
    )

    input_available_at = max(
        dependency_available
    )

    if not all(
        snapshot_causally_available(
            known,
            identity,
            input_available_at,
        )
        for identity in receipt_ids
    ):
        raise ValueError("price dependency fails causal availability")

    bars = []

    for item in selected:
        payload = item["payload"]

        bars.append(
            {
                "time": _utc(payload["time"]),
                "open": payload["open"],
                "high": payload["high"],
                "low": payload["low"],
                "close": payload["close"],
                "volume": payload["volume"],
            }
        )

    source_id = (
        PRICE_CONTRACT
        + ":"
        + str(certificate["certified_set_hash"])
    )

    state = build_market_state(
        INSTRUMENT,
        bars,
        source_id=source_id,
        observed_at=input_available_at,
        as_of=input_available_at,
        timeframe_seconds=3600,
        lookback=20,
    )

    if state.bar_count != 81:
        raise ValueError("MarketState did not retain 81 bars")

    if _utc(state.last_bar_closed_at) != event_times[-1]:
        raise ValueError("MarketState close does not match certificate")

    regime = classify_regime(state)

    provenance = {
        "schema": REGIME_PROVENANCE_SCHEMA,
        "semantic_status": "DESCRIPTIVE_HEURISTIC_NOT_PROBABILITY",
        "price_certificate_schema": certificate["schema"],
        "price_certificate_hash": certificate["certified_set_hash"],
        "price_ledger_head": certificate["ledger_head"],
        "price_receipt_count": len(receipt_ids),
        "price_contract": PRICE_CONTRACT,
        "market_state_id": state.state_id,
        "market_state_input_digest": state.input_digest,
        "market_state_algorithm_version": state.algorithm_version,
        "regime_method": regime.method,
    }

    return append_observation(
        ledger,
        source="oma://market-mechanics/regime/" + regime.method,
        instrument=INSTRUMENT,
        feature=REGIME_FEATURE,
        event_time=event_times[-1],
        source_metric_at=latest_source_metric_at,
        received_at=latest_received_at,
        payload=regime.to_dict(),
        provenance=provenance,
        dependencies=receipt_ids,
        derived=True,
        clock=clock,
    )
