"""One-shot PILOT bookTicker capture. No price/event ledger or trading integration."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from time import monotonic
from urllib.request import build_opener, HTTPRedirectHandler

from .capture_clock import continuous
from .execution_observation import ExecutionReceipt, ExecutionObservation, EvidenceKind, Measure
from .nuisance_pilot_contracts import DatasetRole, digest, utc

ENDPOINT = EvidenceKind.BOOK.value
URL = ENDPOINT + "?symbol=BTCUSDT"
SCHEMA = "binance-usdm-book-capture-v1"


def _now():
    return datetime.now(timezone.utc)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("redirect forbidden; no fallback capture")


def _open():
    return build_opener(_NoRedirect()).open(URL, timeout=15)


def _json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _commit(meta):
    return hashlib.sha256(_json(meta)).hexdigest()


def _write(path, content):
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _read_json(path):
    raw = path.read_bytes()
    data = json.loads(raw)
    if _json(data) != raw:
        raise ValueError("noncanonical capture artifact")
    return data


def _project(meta, raw, available_at, provenance):
    receipt = ExecutionReceipt(EvidenceKind.BOOK, ENDPOINT, _commit(meta), provenance,
        raw.decode("utf-8", errors="strict"), DatasetRole.PILOT,
        datetime.fromisoformat(meta["request_started_at"]), datetime.fromisoformat(meta["received_at"]),
        available_at, None)
    payload = receipt.payload()
    if payload.get("bidPrice") is None or payload.get("askPrice") is None:
        raise ValueError("book response lacks both observed quotes")
    return receipt


def capture_book(directory):
    """One HTTP request, internally sampled timestamps; directory must not exist.

    Persist raw before validating projection. No retries or replacement after a
    response. A failed/incomplete capture has no availability marker.
    """
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False)
    started = _now()
    tick = monotonic()
    with _open() as response:
        raw = response.read(262145)
        received = _now()
        elapsed = monotonic() - tick
        meta = dict(schema=SCHEMA, source=ENDPOINT, request_url=URL, response_url=response.geturl(),
            instrument="BTCUSDT", venue="Binance USDⓈ-M", product="linear perpetual", role="PILOT",
            request_started_at=started.isoformat(), received_at=received.isoformat(),
            response_status=response.status, content_type=response.headers.get_content_type(),
            content_length=response.headers.get("Content-Length"), raw_sha256=hashlib.sha256(raw).hexdigest(),
            request_elapsed_seconds=elapsed)
    _write(root / "response.raw", raw)
    _write(root / "receipt.json", _json(meta))
    _validate(meta, raw)
    _project(meta, raw, None, _commit(meta))  # Validate without inventing availability.
    # Raw and metadata writes have returned after fsync, and validation passed.
    # Never finalize a pre-existing directory or reconstruct its availability.
    available = _now()
    utc(available)
    if available < received:
        raise ValueError("clock reversed before availability")
    ready = dict(receipt_id=_commit(meta), available_at=available.isoformat())
    ready["provenance_sha256"] = digest((_commit(meta), ready["available_at"]))
    _write(root / "available.json", _json(ready))
    return load_book(root)


def _validate(meta, raw):
    expected = {"schema", "source", "request_url", "response_url", "instrument", "venue", "product", "role",
                "request_started_at", "received_at", "response_status", "content_type", "content_length",
                "raw_sha256", "request_elapsed_seconds"}
    if set(meta) != expected or (meta["schema"], meta["source"], meta["request_url"], meta["response_url"],
            meta["instrument"], meta["venue"], meta["product"], meta["role"], meta["response_status"]) != (
            SCHEMA, ENDPOINT, URL, URL, "BTCUSDT", "Binance USDⓈ-M", "linear perpetual", "PILOT", 200):
        raise ValueError("capture source/scope mismatch")
    if meta["content_type"] != "application/json" or not raw or len(raw) > 262144:
        raise ValueError("unsupported or oversized response")
    if meta["content_length"] is not None and int(meta["content_length"]) != len(raw):
        raise ValueError("incomplete response body")
    if hashlib.sha256(raw).hexdigest() != meta["raw_sha256"]:
        raise ValueError("raw content hash mismatch")
    started, received = (datetime.fromisoformat(meta[k]) for k in ("request_started_at", "received_at"))
    utc(started)
    utc(received)
    if started > received:
        raise ValueError("request follows receipt")
    continuous(started, received, meta["request_elapsed_seconds"])


def load_book(directory, *, decision_at=None):
    """Project only verified persisted bytes, never a caller-provided price/dict.

    Default decision cut is availability itself, not a claimed trading decision.
    Local custody is required; this detects changes, not malicious full rehashing.
    """
    root = Path(directory)
    meta = _read_json(root / "receipt.json")
    raw = (root / "response.raw").read_bytes()
    ready = _read_json(root / "available.json")
    _validate(meta, raw)
    if set(ready) != {"receipt_id", "available_at", "provenance_sha256"} or ready["receipt_id"] != _commit(meta):
        raise ValueError("receipt commitment mismatch")
    if ready["provenance_sha256"] != digest((_commit(meta), ready["available_at"])):
        raise ValueError("availability/provenance mismatch")
    available = datetime.fromisoformat(ready["available_at"])
    receipt = _project(meta, raw, available, ready["provenance_sha256"])
    return ExecutionObservation("BTCUSDT", "Binance USDⓈ-M", "linear perpetual", DatasetRole.PILOT,
                                available if decision_at is None else decision_at, (receipt,))
