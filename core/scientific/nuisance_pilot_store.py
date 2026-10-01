"""In-memory Slice 1 stores; no persistence, operational adapters or live reads.

RestrictedStore requires distinct caller-held reader/writer capabilities, checked
by object identity on every access. Hand untrusted consumers ONLY PublicSafeAPI,
which contains no reference to the restricted store. This is an application API
boundary, not protection against hostile Python reflection or process memory
access. Capabilities must remain with a future trusted composition root.

Future integration needs explicit dataset-role rejection before operational
ingestion (OperationalLearningIntegrator._process_record and OutcomeBridge's
operational data ingress). No such integration is authorized in this slice.
"""
from dataclasses import dataclass
from datetime import datetime

from .nuisance_pilot_contracts import (
    DatasetRole, EligibleDecisionOpportunity,
    RestrictedOutcome, SafeOutput, closed, identifiers, utc,
)


class ConflictError(ValueError):
    """Same identity, incompatible content; existing record remains untouched."""


def insert_once(records, key, record):
    if key in records:
        if records[key] != record:
            raise ConflictError("immutable identity conflict")
        return False
    records[key] = record
    return True


class OpportunityStore:
    """All opportunities retained regardless of eligibility; frozen assessments."""
    __slots__ = ("__records", "__inputs")

    def __init__(self):
        self.__records = {}
        self.__inputs = {}

    def append(self, record):
        if type(record) is not EligibleDecisionOpportunity:
            raise TypeError("opportunity contract required")
        # Check every conflict before any mutation (atomic even with four inputs).
        if record.opportunity_id in self.__records:
            return insert_once(self.__records, record.opportunity_id, record)
        for item in record.inputs:
            if item.record_id in self.__inputs and self.__inputs[item.record_id] != item:
                raise ConflictError("immutable assessment conflict")
        for item in record.inputs:
            insert_once(self.__inputs, item.record_id, item)
        return insert_once(self.__records, record.opportunity_id, record)

    def population(self):
        return tuple(self.__records.values())


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    """Canonical economic keys supplied by curator, not inferred from filenames.

    outcome_domain is a declared economic dependency universe, including linked
    instruments/venues when applicable. Missing/wrong equivalence declarations
    cannot be detected here. Windows are half-open; no learned embargo imposed.
    """
    opportunity_id: str
    event_id: str
    event_cluster_id: str
    economic_observation_hash: str
    content_hash: str
    outcome_domain: str
    outcome_start: datetime
    outcome_end: datetime
    dynamic_receipt_ids: tuple[str, ...] = ()

    def __post_init__(self):
        identifiers((self.opportunity_id, self.event_id, self.event_cluster_id,
                     self.economic_observation_hash, self.content_hash, self.outcome_domain))
        identifiers(self.dynamic_receipt_ids)
        utc(self.outcome_start)
        utc(self.outcome_end)
        if self.outcome_end <= self.outcome_start:
            raise ValueError("nonempty outcome window required")


@dataclass(frozen=True, slots=True)
class StaticMetadata:
    """Only explicitly attested static metadata may be shared; never observations."""
    content_hash: str
    kind: str
    shareable: bool

    def __post_init__(self):
        identifiers((self.content_hash,))
        if self.kind not in ("PRODUCT_METADATA", "CALENDAR", "FEE_SCHEDULE") or self.shareable is not True:
            raise ValueError("explicit static shareable metadata required")


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    dataset_role: DatasetRole
    entries: tuple[ManifestEntry, ...]
    static_metadata: tuple[StaticMetadata, ...] = ()

    def __post_init__(self):
        closed(self.dataset_role, DatasetRole)
        for items, kind in ((self.entries, ManifestEntry), (self.static_metadata, StaticMetadata)):
            if type(items) is not tuple or any(type(item) is not kind for item in items):
                raise TypeError("immutable typed manifest entries required")
        if len({e.opportunity_id for e in self.entries}) != len(self.entries):
            raise ConflictError("duplicate opportunity in manifest")


def validate_isolation(manifests):
    """Fail closed across ALL different roles; no performance inspected."""
    manifests = tuple(manifests)
    if any(type(m) is not DatasetManifest for m in manifests):
        raise TypeError("dataset manifests required")
    for n, left in enumerate(manifests):
        for right in manifests[n + 1:]:
            if left.dataset_role is right.dataset_role:
                continue
            for a in left.entries:
                for b in right.entries:
                    for key in ("opportunity_id", "event_id", "event_cluster_id",
                                "economic_observation_hash", "content_hash"):
                        if getattr(a, key) == getattr(b, key):
                            raise ConflictError("cross-role isolation: " + key)
                    if set(a.dynamic_receipt_ids) & set(b.dynamic_receipt_ids):
                        raise ConflictError("cross-role dynamic receipt reuse")
                    if a.outcome_domain == b.outcome_domain and max(a.outcome_start, b.outcome_start) < min(a.outcome_end, b.outcome_end):
                        raise ConflictError("cross-role outcome window overlap")
            # Marking an already-declared dynamic observation 'static' is no escape.
            for dynamic, static in ((left, right), (right, left)):
                if {e.content_hash for e in dynamic.entries} & {s.content_hash for s in static.static_metadata}:
                    raise ConflictError("dynamic content cannot be relabeled static")
    return True


class RestrictedStore:
    """No ungated outcome access, enumeration/export or subgroup-query methods."""
    __slots__ = ("__writer", "__reader", "__records")

    def __init__(self, *, writer_capability, reader_capability):
        if type(writer_capability) is not object or type(reader_capability) is not object or writer_capability is reader_capability:
            raise TypeError("two distinct opaque object capabilities required")
        self.__writer = writer_capability
        self.__reader = reader_capability
        self.__records = {}

    def append(self, record, *, capability):
        if capability is not self.__writer:
            raise PermissionError("restricted access denied")
        if type(record) is not RestrictedOutcome:
            raise TypeError("restricted contract required")
        return insert_once(self.__records, record.outcome_id, record)

    def read(self, outcome_id, *, capability):
        if capability is not self.__reader:
            raise PermissionError("restricted access denied")
        identifiers((outcome_id,))
        if outcome_id not in self.__records:
            raise KeyError("restricted record not found")
        return self.__records[outcome_id]


class PublicSafeAPI:
    """Detached immutable control release, with no link to restricted storage."""
    __slots__ = ("__release",)

    def __init__(self, release):
        if type(release) is not SafeOutput:
            raise TypeError("only exact SafeOutput accepted")
        self.__release = release

    def release(self):
        return self.__release.public_record()
