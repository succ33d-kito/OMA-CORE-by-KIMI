"""Atomic causal admission of one verified Metrics H1 bundle into observations_v2.

No network access.
No capture.
No scheduler.
No backfill.
No partial Metrics admission.
No Outcome/Learning/Knowledge/Criterion writes.

The only accepted source authority is load_verified_bundle(), which authenticates
the immutable persisted SUCCESS capture before this module opens the ledger.
"""

import json
from datetime import datetime, timezone, timedelta
from math import isfinite
from pathlib import Path

from core.market_mechanics.binance_live_adapter import METRIC_ENDPOINTS

from .metrics_observation_bundle import load_verified_bundle
from .prospective_receipts import (
    _observation_db,
    _utc,
    canonical_observation,
    observation_hash,
    observation_snapshot,
)


ADMISSION_CONTRACT = "metrics-observations-v2-admission-v1"
BUNDLE_SCHEMA = "metrics-h1-verified-bundle-v1"
CAPTURE_CONTRACT = "metrics-h1-capture-v1"
PROVIDER = "https://fapi.binance.com"
INSTRUMENT = "BTCUSDT"
PRODUCT = "USD-M"

EXPECTED_MAPPING = {
    ("oi", "sumOpenInterest"):
        "MarketMetrics/OpenInterest",
    ("oi", "sumOpenInterestValue"):
        "MarketMetrics/OpenInterestValue",
    ("top_account", "longShortRatio"):
        "MarketMetrics/TopTraderAccountPositioning",
    ("top_position", "longShortRatio"):
        "MarketMetrics/TopTraderPositionPositioning",
    ("global", "longShortRatio"):
        "MarketMetrics/GlobalPositioning",
    ("taker", "buySellRatio"):
        "MarketMetrics/TakerBuySellRatio",
}

EXPECTED_FEATURES = frozenset(EXPECTED_MAPPING.values())


def _parse_verified_bundle(bundle):
    try:
        body = json.loads(bundle.canonical_json)
    except Exception as exc:
        raise ValueError("invalid verified bundle JSON") from exc

    if type(body) is not dict:
        raise ValueError("verified bundle must be object")

    canonical = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if canonical != bundle.canonical_json:
        raise ValueError("verified bundle is not canonical")

    if body.get("schema") != BUNDLE_SCHEMA:
        raise ValueError("unsupported verified bundle schema")
    if body.get("contract") != CAPTURE_CONTRACT:
        raise ValueError("unsupported Metrics capture contract")
    if body.get("provider") != PROVIDER:
        raise ValueError("unsupported Metrics provider")
    if body.get("instrument") != INSTRUMENT:
        raise ValueError("unsupported Metrics instrument")
    if body.get("product") != PRODUCT:
        raise ValueError("unsupported Metrics product")

    if body.get("derived") is not False:
        raise ValueError("Metrics admission must remain raw")
    if body.get("dependencies") != []:
        raise ValueError("raw Metrics cannot declare dependencies")
    if body.get("admission_status") != "NOT_ADMITTED":
        raise ValueError("source bundle must be NOT_ADMITTED")
    if body.get("ledger_available_at") is not None:
        raise ValueError("source bundle already claims ledger availability")

    values = body.get("values")
    if type(values) is not list or len(values) != 6:
        raise ValueError("exactly six Metrics values required")

    observed = set()
    for value in values:
        if type(value) is not dict:
            raise ValueError("invalid Metrics value envelope")

        if set(value) != {
            "feature",
            "value",
            "component",
            "raw_field",
        }:
            raise ValueError("unexpected Metrics value fields")

        key = (
            value["component"],
            value["raw_field"],
        )
        if EXPECTED_MAPPING.get(key) != value["feature"]:
            raise ValueError("Metrics feature mapping mismatch")

        if type(value["value"]) not in (int, float):
            raise ValueError("Metrics value must be numeric")

        numeric = float(value["value"])
        if not isfinite(numeric) or numeric <= 0:
            raise ValueError("Metrics value must be finite and positive")

        observed.add(value["feature"])

    if observed != EXPECTED_FEATURES:
        raise ValueError("complete six-feature Metrics set required")

    if type(body.get("components")) is not dict:
        raise ValueError("component provenance required")

    return body


def _build_items(body, bundle_id, admitted_at):
    slot = _utc(body["slot"])
    source_start = _utc(body["source_period_start"])
    source_end = _utc(body["source_period_end"])
    received = _utc(body["received_at"])
    capture_available = _utc(body["capture_available_at"])

    source_metric_at = slot - timedelta(microseconds=1)

    if source_end != slot:
        raise ValueError("source period end must equal slot")
    if source_start != slot - timedelta(minutes=5):
        raise ValueError("source period must be exact five-minute window")

    if not (
        source_start
        < source_metric_at
        < slot
        <= received
        <= capture_available
        <= admitted_at
    ):
        raise ValueError("noncausal Metrics admission chronology")

    # Match observations_v2's existing anti-backfill policy.
    if admitted_at - slot > timedelta(days=1):
        raise ValueError("historical backfill cannot become Metrics admission")

    values = sorted(
        body["values"],
        key=lambda value: value["feature"],
    )

    items = []

    for value in values:
        component = value["component"]
        raw_field = value["raw_field"]
        feature = value["feature"]

        if component not in METRIC_ENDPOINTS:
            raise ValueError("unknown Metrics component")

        metadata = body["components"].get(component)
        if type(metadata) is not dict:
            raise ValueError("missing Metrics component provenance")

        endpoint = METRIC_ENDPOINTS[component]

        if metadata.get("endpoint") != endpoint:
            raise ValueError("component endpoint mismatch")

        if _utc(metadata["source_period_end"]) != slot:
            raise ValueError("component source period mismatch")

        component_received = _utc(metadata["received_at"])
        if component_received > received:
            raise ValueError("component receipt exceeds bundle receipt")

        source = PROVIDER + endpoint

        payload = {
            "value": float(value["value"]),
        }

        provenance = {
            "contract": ADMISSION_CONTRACT,
            "capture_contract": body["contract"],
            "bundle_schema": body["schema"],
            "bundle_id": bundle_id,
            "activation_id": body["activation_id"],
            "dataset_role": body["dataset_role"],
            "provider": body["provider"],
            "product": body["product"],
            "slot": body["slot"],
            "slot_id": body["slot_id"],
            "attempt_id": body["attempt_id"],
            "result_id": body["result_id"],
            "capture_receipt_id": body["capture_receipt_id"],
            "source_period_start": body["source_period_start"],
            "source_period_end": body["source_period_end"],
            "capture_received_at": body["received_at"],
            "capture_available_at": body["capture_available_at"],
            "ledger_available_at": admitted_at.isoformat(),
            "raw_bundle_sha256": body["raw_bundle_sha256"],
            "selected_rows_sha256": body["selected_rows_sha256"],
            "component": component,
            "raw_field": raw_field,
            "component_metadata": metadata,
            "source_metric_timestamp_convention":
                "SLOT_MINUS_ONE_MICROSECOND",
        }

        identity = observation_hash([
            source,
            INSTRUMENT,
            feature,
            slot.isoformat(),
            source_metric_at.isoformat(),
            [],
            False,
        ])

        items.append({
            "id": identity,
            "source": source,
            "instrument": INSTRUMENT,
            "feature": feature,
            "event_time": slot.isoformat(),
            "source_metric_at": source_metric_at.isoformat(),
            "received_at": received.isoformat(),
            "available_at": admitted_at.isoformat(),
            "computed_at": None,
            "payload": payload,
            "payload_hash": observation_hash(payload),
            "provenance": provenance,
            "dependencies": [],
            "derived": False,
            "recorded_at": admitted_at.isoformat(),
        })

    if len({item["id"] for item in items}) != 6:
        raise ValueError("Metrics observation identities must be unique")

    return items


def _same_semantic_observation(left, right):
    return all(
        left.get(key) == right.get(key)
        for key in (
            "instrument",
            "feature",
            "event_time",
            "source_metric_at",
        )
    )


def _verify_chain_rows(rows):
    """Verify the observations_v2 chain inside the active write transaction."""

    previous = "0" * 64
    result = []

    for identity, raw, link, digest in rows:
        if link != previous:
            raise ValueError(
                "observation chain link integrity failure"
            )

        if observation_hash([link, raw]) != digest:
            raise ValueError(
                "observation chain digest integrity failure"
            )

        item = json.loads(raw)

        if item.get("id") != identity:
            raise ValueError(
                "observation identity mismatch"
            )

        if observation_hash(
            item.get("payload")
        ) != item.get("payload_hash"):
            raise ValueError(
                "observation payload integrity failure"
            )

        result.append(item)
        previous = digest

    return result


def admit_verified_metrics_bundle(
    ledger,
    state,
    slot,
    *,
    repo_root,
    now,
    clock=None,
):
    """Atomically admit six verified Metrics observations or admit none."""

    # Reconstruct authority directly from persisted evidence.
    bundle = load_verified_bundle(
        state,
        slot,
        repo_root=repo_root,
        now=now,
    )

    body = _parse_verified_bundle(bundle)

    admitted_at = _utc(
        clock()
        if clock is not None
        else datetime.now(timezone.utc)
    )

    items = _build_items(
        body,
        bundle.bundle_id,
        admitted_at,
    )

    ledger = Path(ledger)
    ledger.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Verify the existing append-only chain before opening a new transaction.
    observation_snapshot(ledger)

    con = _observation_db(ledger)

    try:
        con.execute("BEGIN IMMEDIATE")

        # Re-verify the ledger under the same write transaction that will
        # perform admission. This closes the gap between preflight verification
        # and persistence.
        existing_all = con.execute(
            """
            SELECT id, body, previous_hash, receipt_hash
            FROM observations_v2
            ORDER BY seq
            """
        ).fetchall()

        existing_objects = _verify_chain_rows(
            existing_all
        )

        # Re-authenticate the persisted Metrics evidence immediately before
        # admission. VerifiedMetricsBundle is a projection, not authority by
        # itself.
        reverified = load_verified_bundle(
            state,
            slot,
            repo_root=repo_root,
            now=now,
        )

        if (
            reverified.bundle_id != bundle.bundle_id
            or reverified.canonical_json
            != bundle.canonical_json
        ):
            raise ValueError(
                "verified Metrics evidence changed "
                "before ledger admission"
            )

        # Detect semantic conflicts even if a conflicting row used another
        # source and therefore obtained another observation id.

        candidate_ids = {
            item["id"]
            for item in items
        }

        for old in existing_objects:
            for item in items:
                if (
                    _same_semantic_observation(old, item)
                    and old["id"] != item["id"]
                ):
                    raise ValueError(
                        "conflicting Metrics observation already exists"
                    )

        placeholders = ",".join(
            "?"
            for _ in candidate_ids
        )

        existing_candidates = con.execute(
            f"""
            SELECT id, body
            FROM observations_v2
            WHERE id IN ({placeholders})
            """,
            tuple(candidate_ids),
        ).fetchall()

        if existing_candidates:
            if len(existing_candidates) != 6:
                raise ValueError(
                    "partial prior Metrics admission detected"
                )

            existing_map = {
                identity: json.loads(raw)
                for identity, raw in existing_candidates
            }

            availability = set()

            for item in items:
                old = existing_map[item["id"]]

                if (
                    old.get("payload_hash")
                    != item["payload_hash"]
                    or old.get("provenance", {}).get("bundle_id")
                    != bundle.bundle_id
                ):
                    raise ValueError(
                        "conflicting Metrics observation; "
                        "no silent overwrite"
                    )

                availability.add(
                    old.get("available_at")
                )

            if (
                None in availability
                or len(availability) != 1
            ):
                raise ValueError(
                    "existing Metrics bundle has inconsistent availability"
                )

            con.rollback()

            return {
                "status": "ALREADY_ADMITTED",
                "bundle_id": bundle.bundle_id,
                "row_count": 6,
                "ledger_available_at": next(iter(availability)),
                "observation_ids": sorted(candidate_ids),
            }

        last = con.execute(
            """
            SELECT body, receipt_hash
            FROM observations_v2
            ORDER BY seq DESC
            LIMIT 1
            """
        ).fetchone()

        if (
            last
            and _utc(
                json.loads(last[0])["recorded_at"]
            ) > admitted_at
        ):
            raise ValueError(
                "ledger clock moved backwards"
            )

        previous = (
            last[1]
            if last
            else "0" * 64
        )

        for item in items:
            raw = canonical_observation(item)
            digest = observation_hash(
                [previous, raw]
            )

            con.execute(
                """
                INSERT INTO observations_v2(
                    id,
                    body,
                    previous_hash,
                    receipt_hash
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    item["id"],
                    raw,
                    previous,
                    digest,
                ),
            )

            previous = digest

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()

    return {
        "status": "ADMITTED",
        "bundle_id": bundle.bundle_id,
        "row_count": 6,
        "ledger_available_at": admitted_at.isoformat(),
        "observation_ids": sorted(candidate_ids),
    }