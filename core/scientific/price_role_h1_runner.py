"""PILOT Price orchestration with explicit in-process, same-window retries."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import time

from core.market_mechanics.binance_live_adapter import capture_price_receipt
from . import price_role_attestation as roles
from .capture_clock import ClockHealthError
from .price_role_activation import load_activation
from .metrics_h1_activation import _reject_aliases
from .funding_h1_runtime import _process_lock
from .prospective_receipts import observation_snapshot, observation_hash, snapshot_causally_available

SCHEMA = "price-role-h1-runner-v1"
LEAF = "price-role-h1-v1"
STATUSES = {"STARTED", "AUTHORIZED", "CAPTURE_STARTED", "CAPTURED", "ATTESTED", "SUCCESS",
            "CAPTURE_FAILED", "ATTESTATION_FAILED", "CONFLICT", "MISSED_SLOT"}
NETWORK_SCHEMA = "price-role-h1-network-v1"
TERMINAL = ("CONFLICT", "MISSED_SLOT", "CAPTURE_FAILED")


def now():
    return datetime.now(timezone.utc)


def utc(value):
    return roles._utc(value)


def bounds(slot):
    slot = utc(slot)
    if slot != slot.replace(minute=0, second=0, microsecond=0):
        raise ValueError("exact UTC H1 slot required")
    return slot + timedelta(seconds=5), slot + timedelta(seconds=125)


def validate_state(state, *, repo_root):
    root, repo = Path(state), Path(repo_root)
    if not root.is_absolute() or not repo.is_absolute() or ".." in root.parts or root.name != LEAF:
        raise ValueError("absolute external price-role-h1-v1 state required")
    _reject_aliases(root)
    _reject_aliases(repo)
    root, repo = root.resolve(strict=True), repo.resolve(strict=True)
    if root == repo or repo in root.parents or any((parent / ".git").exists() for parent in (root, *root.parents)):
        raise ValueError("state must be outside repository")
    # Inspect all runtime-owned paths before any API follows aliases.
    for relative in ("config.json", "authorizations", "attempts", "runtime", "observations.db",
                     "observations.db-wal", "observations.db-shm", "observations.db-journal"):
        _reject_aliases(root / relative)
    config = load_activation(root, repo_root=repo)
    if config["dataset_role"] != "PILOT":
        raise ValueError("this runner requires authenticated PILOT activation")
    return root, config


def _rows(root):
    path = root / "observations.db"
    _reject_aliases(path)
    return observation_snapshot(path, read_only=True)[0] if path.exists() else {}


def _directory(root, slot):
    path = root / "attempts" / slot.strftime("%Y%m%dT%H0000Z")
    _reject_aliases(path)
    return path


def _read(path):
    _reject_aliases(path)
    raw = path.read_bytes()
    body = json.loads(raw)
    if raw != roles._canonical(body) or body.get("record_id") != observation_hash({k:v for k,v in body.items() if k != "record_id"}):
        raise ValueError("corrupt attempt record")
    return body


def _record(root, config, slot, status, at, **details):
    if status not in STATUSES:
        raise ValueError("unknown attempt state")
    path = _directory(root, slot) / (status + ".json")
    _reject_aliases(path)
    body = dict(schema=SCHEMA, activation_id=config["activation_id"], dataset_role="PILOT",
                slot=slot.isoformat(), status=status, at=utc(at).isoformat(), **details)
    if path.exists():
        old = _read(path)
        if {k:v for k,v in old.items() if k not in ("at","record_id")} != {k:v for k,v in body.items() if k != "at"}:
            raise ValueError("immutable attempt conflicts")
        return old
    body["record_id"] = observation_hash(body)
    roles._exclusive_json(path, body)
    return body


def _network_record(root, config, slot, index, status, started_at, at, **details):
    path = _directory(root, slot) / "network" / f"{index:04d}-{status}.json"
    _reject_aliases(path)
    body = dict(schema=NETWORK_SCHEMA, activation_id=config["activation_id"],
                dataset_role="PILOT", slot=slot.isoformat(), attempt_index=index,
                status=status, started_at=utc(started_at).isoformat(), at=utc(at).isoformat(), **details)
    body["record_id"] = observation_hash(body)
    # No overwriting or resuming a network attempt, even with identical content.
    roles._exclusive_json(path, body)
    return body


def _network_records(root, config, slot):
    directory = _directory(root, slot) / "network"
    _reject_aliases(directory)
    records = []
    for path in sorted(directory.glob("*.json")):
        body = _read(path)
        index = body.get("attempt_index")
        status = body.get("status")
        if (body.get("schema") != NETWORK_SCHEMA or type(index) is not int or index < 1
                or status not in ("STARTED", "FAILED", "SUCCESS", "CONFLICT")
                or path.name != f"{index:04d}-{status}.json"
                or body.get("activation_id") != config["activation_id"]
                or body.get("dataset_role") != "PILOT" or body.get("slot") != slot.isoformat()
                or utc(body["at"]) < utc(body["started_at"])):
            raise ValueError("network attempt identity or timing mismatch")
        records.append(body)
    return records


def _prices(known, slot):
    return [r for r in known.values() if r["feature"] == "Price/OHLCV" and utc(r["event_time"]) == slot]


def _auth(root, config, slot, repo_root):
    identity = roles._slot_id(config["activation_id"], slot)
    path = root / "authorizations" / (identity + ".json")
    _reject_aliases(path)
    if not path.exists():
        return None
    record = roles.load_authorization(root, identity, repo_root=repo_root)
    if record["slot_id"] != identity or utc(record["expected_event_time"]) != slot:
        raise ValueError("authorization file does not bind this exact slot")
    return record


def _verify_pair(known, price, auth, config, at):
    att = roles.verified_price_role_attestation(known, price, "PILOT", at)
    if att is None or att["payload"]["authorization_id"] != auth["authorization_id"] or att["payload"]["activation_id"] != config["activation_id"]:
        raise ValueError("exact authorized Price/attestation pair unavailable")
    return att


def attempt_slot(state, slot, *, repo_root, session=None, clock=now, capture=capture_price_receipt, sleeper=time.sleep):
    """Explicit same-process retries; existing raw only recovers its preauthorized attestation.

    Injection points are for deterministic tests. Production CLI supplies the frozen
    callable and actual clock, never a timestamp argument or synthetic envelope.
    """
    root, config = validate_state(state, repo_root=repo_root)
    slot = utc(slot)
    target, deadline = bounds(slot)
    runtime = root / "runtime"
    runtime.mkdir(exist_ok=True)
    lock = runtime / "slot.lock"
    _reject_aliases(lock)
    with _process_lock(lock):
        return _attempt(root, config, slot, target, deadline, repo_root, session, clock, capture, sleeper)


def _attempt(root, config, slot, target, deadline, repo_root, session, clock, capture, sleeper):
    previous = utc(config["not_before"])
    def sample():
        nonlocal previous
        current = utc(clock())
        if current < previous:
            raise ValueError("Price role clock moved backwards")
        previous = current
        return current
    at = sample()
    directory = _directory(root, slot)
    for path in sorted(directory.glob("*.json")):
        old = _read(path)
        if old.get("schema") != SCHEMA or old.get("activation_id") != config["activation_id"] or old.get("slot") != slot.isoformat() or old.get("status") != path.stem or old.get("status") not in STATUSES or old.get("dataset_role") != "PILOT":
            raise ValueError("attempt identity mismatch")
        if utc(old["at"]) > at:
            raise ValueError("Price role clock moved backwards across attempt")
    network_records = _network_records(root, config, slot)
    if any(utc(r["at"]) > at for r in network_records):
        raise ValueError("clock precedes network evidence")
    def record(status, **details):
        return _record(root, config, slot, status, sample(), **details)
    for status in TERMINAL:
        if (directory / (status + ".json")).exists():
            return _read(directory / (status + ".json"))
    known = _rows(root)
    if any(utc(r["recorded_at"]) > at for r in known.values()):
        raise ValueError("clock precedes ledger evidence")
    prices = _prices(known, slot)
    try:
        auth = _auth(root, config, slot, repo_root)
    except (ValueError, KeyError, TypeError):
        return record("CONFLICT", reason="AUTHORIZATION_INVALID")
    if len(prices) > 1:
        return record("CONFLICT", reason="MULTIPLE_RAW_PRICES")
    if prices and auth is None:
        return record("CONFLICT", reason="RAW_WITHOUT_PRECAPTURE_AUTHORIZATION")
    if not prices:
        if (directory / "SUCCESS.json").exists() or (directory / "CAPTURED.json").exists():
            return record("CONFLICT", reason="PERSISTED_RAW_MISSING")
        if (directory / "CAPTURE_STARTED.json").exists() or network_records:
            return record("CAPTURE_FAILED", reason="INTERRUPTED_CAPTURE_NO_RETRY")
        if at > deadline or slot < utc(config["not_before"]).replace(minute=0, second=0, microsecond=0):
            return record("MISSED_SLOT", reason="NO_CAPTURE_BEFORE_DEADLINE")
        if at < target:
            return {"status":"WAITING", "slot":slot.isoformat(), "target":target.isoformat()}
        record("STARTED")
        if auth is None:
            auth = roles.authorize_capture(root, repo_root=repo_root, expected_event_time=slot)
        if utc(auth["authorized_at"]) > sample():
            raise ValueError("clock precedes authorization")
        record("AUTHORIZED", authorization_id=auth["authorization_id"])
        if sample() > deadline:
            return record("MISSED_SLOT", reason="NO_CAPTURE_BEFORE_DEADLINE")
        record("CAPTURE_STARTED", authorization_id=auth["authorization_id"])
        index = 0
        while True:
            started = sample()
            if started > deadline or (index and started >= deadline):
                return record("CAPTURE_FAILED", reason="RETRY_WINDOW_EXHAUSTED")
            index += 1
            _network_record(root, config, slot, index, "STARTED", started, started,
                            authorization_id=auth["authorization_id"])
            try:
                returned = capture(session, root / "observations.db", expected_event_time=slot,
                                   capture_deadline=deadline, clock=sample)
            except Exception as exc:
                # Inspect persistence before deciding whether any retry is permissible.
                try:
                    known = _rows(root)
                    prices = _prices(known, slot)
                except Exception as ledger_exc:
                    completed = sample()
                    _network_record(root, config, slot, index, "FAILED", started, completed,
                        completed_at=completed.isoformat(), exception_type=type(exc).__name__,
                        exception_message=str(exc), failure_kind="LEDGER_UNVERIFIABLE",
                        raw_present_after_failure=None,
                        remaining_window_seconds=max(0.0, (deadline-completed).total_seconds()),
                        ledger_exception_type=type(ledger_exc).__name__, ledger_exception_message=str(ledger_exc))
                    return record("CONFLICT", reason="LEDGER_UNVERIFIABLE_AFTER_CAPTURE")
                completed = sample()
                _network_record(root, config, slot, index, "FAILED", started, completed,
                    completed_at=completed.isoformat(), exception_type=type(exc).__name__,
                    exception_message=str(exc), failure_kind="CLOCK" if isinstance(exc, ClockHealthError) else "CAPTURE_EXCEPTION",
                    raw_present_after_failure=bool(prices),
                    remaining_window_seconds=max(0.0, (deadline-completed).total_seconds()))
                if len(prices) > 1:
                    return record("CONFLICT", reason="MULTIPLE_RAW_PRICES")
                if prices:
                    break  # Exact raw is validated below; never recapture persisted raw.
                remaining = (deadline-completed).total_seconds()
                if remaining <= 0:
                    return record("CAPTURE_FAILED", reason="RETRY_WINDOW_EXHAUSTED")
                sleeper(min(20.0, remaining))
                resumed = sample()
                if resumed <= completed:
                    raise ValueError("retry wait did not advance clock")
                # Recheck under the slot lock in case an external writer changed evidence.
                known = _rows(root)
                prices = _prices(known, slot)
                if prices:
                    break
            else:
                known = _rows(root)
                prices = _prices(known, slot)
                completed = sample()
                if len(prices) != 1 or returned != prices[0]:
                    _network_record(root, config, slot, index, "CONFLICT", started, completed,
                                    completed_at=completed.isoformat(), reason="CAPTURE_RESULT_NOT_EXACT_PERSISTED_RAW")
                    return record("CONFLICT", reason="CAPTURE_RESULT_NOT_EXACT_PERSISTED_RAW")
                _network_record(root, config, slot, index, "SUCCESS", started, completed,
                                completed_at=completed.isoformat(), raw_id=prices[0]["id"])
                break

    if len(prices) != 1:
        return record("CONFLICT", reason="MULTIPLE_RAW_PRICES")
    price = prices[0]
    at = sample()
    if (not snapshot_causally_available(known, price["id"], at)
            or utc(auth["authorized_at"]) >= utc(price["provenance"]["server_received_at"])
            or not target <= utc(price["received_at"]) <= utc(price["available_at"]) <= deadline):
        return record("CONFLICT", reason="RAW_AUTHORIZATION_OR_TIMING_INVALID")
    record("CAPTURED", raw_id=price["id"])
    existing_attestations = [r for r in known.values() if r["feature"] == roles.ATTESTATION_FEATURE and utc(r["event_time"]) == slot]
    if existing_attestations:
        try:
            att = _verify_pair(known, price, auth, config, at)
            if len(existing_attestations) != 1:
                raise ValueError("conflicting attestations")
        except ValueError:
            return record("CONFLICT", reason="ATTESTATION_INVALID")
    else:
        if (directory / "SUCCESS.json").exists():
            return record("CONFLICT", reason="PERSISTED_ATTESTATION_MISSING")
        try:
            roles.attest_price_observation(root, root / "observations.db", repo_root=repo_root,
                slot_id=auth["slot_id"], observation_id=price["id"])
            at = sample()
            known = _rows(root)
            att = _verify_pair(known, price, auth, config, at)
        except Exception:
            return record("ATTESTATION_FAILED", raw_id=price["id"], reason="EXACT_RAW_PRESERVED_NO_RECAPTURE")
    record("ATTESTED", raw_id=price["id"], attestation_id=att["id"])
    return record("SUCCESS", raw_id=price["id"], attestation_id=att["id"])


def status(state, *, repo_root, clock=now):
    """Read-only pair verification, not a replacement for the 81H certificate."""
    root, config = validate_state(state, repo_root=repo_root)
    cutoff = utc(clock())
    known = _rows(root)
    raw = [r for r in known.values() if r["feature"] == "Price/OHLCV"]
    valid = []
    invalid = []
    for price in raw:
        slot = utc(price["event_time"])
        try:
            if len(_prices(known, slot)) != 1:
                raise ValueError("conflicting raw")
            auth = _auth(root, config, slot, repo_root)
            att = _verify_pair(known, price, auth, config, cutoff)
            valid.append({"slot":slot.isoformat(),"raw_id":price["id"],"attestation_id":att["id"]})
        except (ValueError, KeyError, TypeError):
            invalid.append(price["id"])
    attempts = []
    for path in sorted((root / "attempts").glob("*/*.json")):
        attempts.append(_read(path))
    network = []
    for directory in sorted((root / "attempts").glob("*")):
        if directory.is_dir():
            slot = datetime.strptime(directory.name, "%Y%m%dT%H0000Z").replace(tzinfo=timezone.utc)
            network.extend(_network_records(root, config, slot))
    numbered_slots = {r["slot"] for r in network}
    legacy = [r for r in attempts if r["status"] == "CAPTURE_STARTED" and r["slot"] not in numbered_slots]
    activity = network + [r for r in attempts if r["slot"] not in numbered_slots
                             and r["status"] in ("CAPTURE_STARTED", "CAPTURE_FAILED", "CAPTURED")]
    latest = max(activity, key=lambda r:utc(r["at"])) if activity else None
    heartbeat = root / "runtime" / "heartbeat.json"
    _reject_aliases(heartbeat)
    return {"schema":SCHEMA, "state":str(root), "activation_id":config["activation_id"],
        "dataset_role":config["dataset_role"], "ledger_integrity":"PASS" if (root/"observations.db").exists() else "EMPTY",
        "verified_pairs":sorted(valid,key=lambda r:r["slot"]), "invalid_raw_ids":invalid,
        "attested_hours":len(valid), "attempt_records":attempts, "network_executed":False, "state_initialized":False,
        "status_command_network_executed":False,
        "runtime_network_attempts":sum(r["status"] == "STARTED" for r in network)+len(legacy),
        "legacy_uninstrumented_network_attempts":len(legacy), "network_attempt_records":network,
        "last_network_attempt_status":None if latest is None else latest["status"],
        "runtime_liveness":"UNVERIFIED", "heartbeat_is_evidence":False,
        "heartbeat":json.loads(heartbeat.read_text()) if heartbeat.exists() else None}
