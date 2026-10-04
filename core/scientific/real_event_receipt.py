"""Bounded prospective document capture and ledger-backed Sampling admission.

No historical timestamp inputs, strategy, feature construction or Price I/O.
"""
from dataclasses import dataclass, replace, asdict
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.request import urlopen
from urllib.parse import urlparse

from .nuisance_pilot_contracts import DatasetRole, InputType, closed, digest, identifiers, utc
from .nuisance_pilot_sampling import (
    SyntheticSampler, SyntheticEventEnvelope, SourceConfig, Relation, ShockEvidence, VERSION,
)

REAL_VERSION = "real-event-receipt-v1"


def _now():
    return datetime.now(timezone.utc)


class ContentKind(Enum):
    FULL_DOCUMENT = "FULL_DOCUMENT"
    HEADLINE_ONLY = "HEADLINE_ONLY"
    SNIPPET_ONLY = "SNIPPET_ONLY"
    METADATA_ONLY = "METADATA_ONLY"


@dataclass(frozen=True, slots=True)
class RealEventReceipt:
    receipt_id: str
    source: str
    source_version: str
    document_id: str
    revision_id: str
    content: str
    content_hash: str
    kind: ContentKind
    role: DatasetRole
    received_at: datetime
    available_at: datetime | None
    provenance_hash: str


@dataclass(frozen=True, slots=True)
class AdmissionEvidence:
    """Explicit upstream semantic attribution, not automatically proven causality."""
    btc_quote: str
    announcement_count: int
    shock_evidence: ShockEvidence
    shock_namespace: str
    shock_key: str
    relation: Relation
    prior_event_id: str | None

    def __post_init__(self):
        identifiers((self.btc_quote, self.shock_namespace, self.shock_key))
        closed(self.shock_evidence, ShockEvidence)
        closed(self.relation, Relation)
        if type(self.announcement_count) is not int or self.announcement_count != 1:
            raise ValueError("one explicit announcement required")
        if self.prior_event_id is not None:
            identifiers((self.prior_event_id,))


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


class RealEventStore:
    """One Event-only SQLite journal. Capture is restricted to authorized exact URLs.

    Source scope and semantic completeness are ex-ante operator assertions. HTTPS
    authenticates the endpoint, not the truth of the article or shock attribution.
    """
    def __init__(self, path):
        self.__path = Path(path)
        self.__path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.__path) as con:
            con.execute("CREATE TABLE IF NOT EXISTS event_journal(seq INTEGER PRIMARY KEY, body TEXT NOT NULL, hash TEXT NOT NULL)")

    def _read(self, con):
        records, previous = [], "0" * 64
        for seq, body, commitment in con.execute("SELECT seq,body,hash FROM event_journal ORDER BY seq"):
            if seq != len(records) + 1 or digest((previous, body)) != commitment:
                raise ValueError("event journal integrity failure")
            item = json.loads(body)
            records.append(item)
            previous = commitment
        return records, previous

    def _append(self, kind, data, validate):
        with sqlite3.connect(self.__path) as con:
            con.execute("BEGIN IMMEDIATE")
            rows, previous = self._read(con)
            at = _now()
            utc(at)
            if rows and at < datetime.fromisoformat(rows[-1]["at"]):
                raise ValueError("clock moved backwards")
            validate(rows, at)
            body = _json(dict(kind=kind, at=at.isoformat(), data=data))
            con.execute("INSERT INTO event_journal(body,hash) VALUES (?,?)", (body, digest((previous, body))))

    def _rows(self):
        with sqlite3.connect(self.__path) as con:
            return self._read(con)[0]

    def authorize_source(self, source, version, url, kind):
        identifiers((source, version, url))
        closed(kind, ContentKind)
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError("credential-free HTTPS document URL required")
        def check(rows, at):
            if any(r["kind"] == "receipt" for r in rows):
                raise ValueError("source set frozen after first capture")
            if any(r["kind"] == "source" and r["data"]["source"] == source for r in rows):
                raise ValueError("source authorization already frozen")
        self._append("source", dict(source=source, version=version, url=url, content_kind=kind.value), check)

    def capture(self, source, revision_id, role):
        """Read complete UTF-8 HTTP entity (max 4 MiB); never accept caller timestamps/content."""
        identifiers((source, revision_id))
        closed(role, DatasetRole)
        rows = self._rows()
        authorized = next((r for r in rows if r["kind"] == "source" and r["data"]["source"] == source), None)
        if authorized is None:
            raise ValueError("source unauthorized")
        config = authorized["data"]
        with urlopen(config["url"], timeout=10) as response:
            if response.status != 200 or response.geturl() != config["url"]:
                raise ValueError("unexpected source response/redirect")
            content_type = response.headers.get_content_type()
            if content_type not in ("text/plain", "text/html"):
                raise ValueError("unsupported full-document representation")
            raw = response.read(4 * 1024 * 1024 + 1)
            received = _now()
            utc(received)
            length = response.headers.get("Content-Length")
            if not raw or len(raw) > 4 * 1024 * 1024 or (length is not None and int(length) != len(raw)):
                raise ValueError("incomplete or oversized document")
        content = raw.decode("utf-8", errors="strict")
        content_hash = hashlib.sha256(raw).hexdigest()
        identity = digest((REAL_VERSION, source, config["version"], config["url"], revision_id))
        payload = dict(receipt_id=identity, source=source, source_version=config["version"],
            document_id=config["url"], revision_id=revision_id, content=content, content_hash=content_hash,
            content_kind=config["content_kind"], role=role.value, received_at=received.isoformat(),
            source_authorization=digest(authorized), response_content_type=content_type)
        old = next((r for r in rows if r["kind"] == "receipt" and r["data"]["receipt_id"] == identity), None)
        if old is not None:
            if old["data"]["content_hash"] != content_hash or old["data"]["role"] != role.value:
                raise ValueError("receipt revision/role conflict")
            return self.receipt(identity)  # Preserve first receipt and availability.
        def check(current, at):
            if not datetime.fromisoformat(authorized["at"]) < received <= at:
                raise ValueError("source must precede receipt; receipt cannot be future")
            for r in current:
                if r["kind"] == "receipt":
                    p = r["data"]
                    if p["receipt_id"] == identity:
                        raise ValueError("concurrent duplicate receipt; retry")
                    if p["role"] != role.value and (p["document_id"] == config["url"] or p["content_hash"] == content_hash):
                        raise ValueError("cross-role document/content reuse")
        self._append("receipt", payload, check)
        # Raw bytes are durable first. Only a subsequent ready marker establishes
        # pipeline availability; interrupted capture stays UNKNOWN, never repaired.
        self._append("ready", dict(receipt_id=identity), lambda rows, at: None)
        return self.receipt(identity)

    def receipt(self, receipt_id):
        rows = self._rows()
        item = next(r for r in rows if r["kind"] == "receipt" and r["data"]["receipt_id"] == receipt_id)
        p = item["data"]
        if hashlib.sha256(p["content"].encode("utf-8")).hexdigest() != p["content_hash"]:
            raise ValueError("content integrity failure")
        ready = next((r for r in rows if r["kind"] == "ready" and r["data"]["receipt_id"] == receipt_id), None)
        return RealEventReceipt(receipt_id, p["source"], p["source_version"], p["document_id"],
            p["revision_id"], p["content"], p["content_hash"], ContentKind(p["content_kind"]), DatasetRole(p["role"]),
            datetime.fromisoformat(p["received_at"]), datetime.fromisoformat(ready["at"]) if ready else None,
            digest((item, ready)))

    def _replay(self, rows):
        sources = tuple(SourceConfig(r["data"]["source"], r["data"]["version"], datetime.fromisoformat(r["at"]))
                        for r in rows if r["kind"] == "source")
        sampler = SyntheticSampler(sources, run_id=REAL_VERSION)
        receipts = {r["data"]["receipt_id"]: r["data"] for r in rows if r["kind"] == "receipt"}
        for row in rows:
            p = row["data"]
            if row["kind"] == "admit":
                receipt = receipts[p["receipt_id"]]
                proof = p["evidence"]
                # Reuse ONLY the existing pure sampling reducer, not its trust
                # boundary. These attestations originate in verified journal rows.
                envelope = SyntheticEventEnvelope(receipt["source"], receipt["source_version"],
                    receipt["document_id"], receipt["revision_id"], receipt["content_hash"], p["receipt_id"],
                    datetime.fromisoformat(receipt["received_at"]), datetime.fromisoformat(row["at"]),
                    datetime.fromisoformat(row["at"]), assets=("BTC",), binding_unambiguous=True,
                    announcement_count=1, shock_evidence=ShockEvidence(proof["shock_evidence"]),
                    shock_namespace=proof["shock_namespace"], shock_key=proof["shock_key"],
                    evidence_hash=digest(proof), prior_event_id=proof["prior_event_id"],
                    relation=Relation(proof["relation"]), receipt_verified=True, integrity_verified=True,
                    provenance_hash=p["provenance_hash"], normalization_version=VERSION)
                sampler.register(envelope, role=DatasetRole(receipt["role"]))
            elif row["kind"] == "close":
                sampler.close(datetime.fromisoformat(p["cutoff"]))
        return sampler

    def admit(self, receipt_id, evidence):
        if type(evidence) is not AdmissionEvidence:
            raise TypeError("explicit immutable semantic evidence required")
        receipt = self.receipt(receipt_id)
        if receipt.kind is not ContentKind.FULL_DOCUMENT or receipt.available_at is None:
            raise ValueError("full-content receipt with known availability required")
        if evidence.btc_quote not in receipt.content or not re.search(r"\b(?:BTC|Bitcoin)\b", evidence.btc_quote, re.I):
            raise ValueError("explicit BTC content binding required")
        proof = {**asdict(evidence), "relation": evidence.relation.value, "shock_evidence": evidence.shock_evidence.value}
        data = dict(receipt_id=receipt_id, evidence=proof, provenance_hash=receipt.provenance_hash)
        def check(rows, at):
            if at < receipt.available_at:
                raise ValueError("admission precedes availability")
            if any(r["kind"] == "admit" and r["data"]["receipt_id"] == receipt_id for r in rows):
                raise ValueError("admission already frozen")
            self._replay(rows + [dict(kind="admit", at=at.isoformat(), data=data)])
        self._append("admit", data, check)
        return self._replay(self._rows()).candidates()[-1]

    def close(self, cutoff):
        utc(cutoff)
        data = dict(cutoff=cutoff.isoformat())
        def check(rows, at):
            if cutoff > at:
                raise ValueError("cannot close future cutoff")
            self._replay(rows + [dict(kind="close", at=at.isoformat(), data=data)])
        self._append("close", data, check)
        return self.population()

    def population(self):
        rows = self._rows()
        population_rule = digest((REAL_VERSION, tuple(r for r in rows if r["kind"] == "source")))
        return tuple(replace(op, protocol_hash=digest((op.protocol_id, REAL_VERSION)),
            population_rule_hash=population_rule, cluster_rule_version=REAL_VERSION,
            inputs=tuple(replace(i, validator_version=REAL_VERSION) if i.input_type is InputType.EVENT else
                         replace(i, source="unobserved", reason_codes=("NOT_OBSERVED_IN_EVENT_RECEIPT_SLICE",))
                         for i in op.inputs)) for op in self._replay(rows).population())
