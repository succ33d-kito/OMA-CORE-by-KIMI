"""OMA-PNEP-1.0 synthetic-only sampler. No I/O or operational integration.

Evidence flags attest synthetic fixtures, not real receipt authenticity. Replay
must preserve the append order of receipts; there is no retroactive sorting.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .nuisance_pilot_contracts import (
    DatasetRole, EligibleDecisionOpportunity, InputAvailabilityRecord, InputStatus,
    InputType, closed, digest, identifiers, utc,
)
from .nuisance_pilot_store import ConflictError, OpportunityStore

PROTOCOL = "OMA-PNEP-1.0"
VERSION = "sampling-v1.0-synthetic"
INSTRUMENT = "BTCUSDT"
VENUE = "Binance USDⓈ-M"
PRODUCT = "linear perpetual"


class Relation(Enum):
    DUPLICATE = "DUPLICATE"
    UPDATE = "UPDATE"
    CORRECTION = "CORRECTION"
    SAME_CLUSTER_NEW_REPORT = "SAME_CLUSTER_NEW_REPORT"
    NEW_EVENT = "NEW_EVENT"


class ShockEvidence(Enum):
    OFFICIAL_ANNOUNCEMENT = "OFFICIAL_ANNOUNCEMENT"
    PRIMARY_DOCUMENT = "PRIMARY_DOCUMENT"
    EXPLICIT_RELATION = "EXPLICIT_RELATION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class SourceConfig:
    source: str
    version: str
    authorized_at: datetime

    def __post_init__(self):
        identifiers((self.source, self.version))
        utc(self.authorized_at)


@dataclass(frozen=True, slots=True)
class SyntheticEventEnvelope:
    source: str
    source_version: str
    document_id: str
    revision_id: str
    content_hash: str
    receipt_id: str | None
    received_at: datetime | None
    processed_at: datetime | None
    available_at: datetime | None
    assets: tuple[str, ...] = ()
    binding_unambiguous: bool = False
    announcement_count: int = 0
    shock_evidence: ShockEvidence = ShockEvidence.UNKNOWN
    shock_namespace: str | None = None
    shock_key: str | None = None
    evidence_hash: str | None = None
    prior_event_id: str | None = None
    relation: Relation = Relation.NEW_EVENT
    receipt_verified: bool = False
    integrity_verified: bool = False
    provenance_hash: str | None = None
    normalization_version: str = VERSION
    event_time: datetime | None = None
    published_at: datetime | None = None

    def __post_init__(self):
        identifiers((self.source, self.source_version, self.document_id, self.revision_id,
                     self.content_hash, self.normalization_version))
        identifiers(self.assets)
        for value in (self.receipt_id, self.shock_namespace, self.shock_key, self.evidence_hash,
                      self.prior_event_id, self.provenance_hash):
            if value is not None:
                identifiers((value,))
        for value in (self.received_at, self.processed_at, self.available_at, self.event_time, self.published_at):
            if value is not None:
                utc(value)
        for value in (self.binding_unambiguous, self.receipt_verified, self.integrity_verified):
            if type(value) is not bool:
                raise TypeError("boolean attestation required")
        if type(self.announcement_count) is not int or self.announcement_count < 0:
            raise ValueError("explicit announcement count required")
        closed(self.relation, Relation)
        closed(self.shock_evidence, ShockEvidence)
        if self.available_at is not None and any(
                t is not None and t > self.available_at for t in (self.received_at, self.processed_at)):
            raise ValueError("availability precedes receipt/processing")
        if self.processed_at is not None and self.received_at is not None and self.processed_at < self.received_at:
            raise ValueError("processing precedes receipt")

    @property
    def event_id(self):
        # Content is checked separately: a changed payload under the same declared
        # revision must conflict rather than evade dedup with a fresh identity.
        return digest(("pnep-event-v1", self.source, self.document_id, self.revision_id))


def decision_slot(received_at):
    utc(received_at)
    boundary = received_at.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return boundary, "H1:" + boundary.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class Candidate:
    envelope: SyntheticEventEnvelope
    role: DatasetRole
    relation: Relation
    cluster_id: str | None
    reservation_id: str | None
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Reservation:
    reservation_id: str
    event_id: str
    cluster_id: str
    role: DatasetRole
    decision_at: datetime
    decision_slot_id: str


@dataclass(frozen=True, slots=True)
class Admission:
    reservation_id: str
    admitted: bool
    reasons: tuple[str, ...]
    opportunity: EligibleDecisionOpportunity | None


@dataclass(frozen=True, slots=True)
class SamplingCounts:
    N_raw_events: int
    N_unique_events: int
    N_sampling_eligible_events: int
    N_event_clusters: int
    N_opportunities: int


class SyntheticSampler:
    """Single-threaded in-memory registry, shared across roles for isolation.

    Register receipt records first, then close each decision boundary. A closed
    boundary cannot accept backdated new receipts. Role ownership includes failed
    reservations: a rejected shock cannot be rescued under a different role.
    """
    def __init__(self, sources, *, run_id="synthetic-run"):
        if type(sources) is not tuple or any(type(s) is not SourceConfig for s in sources):
            raise TypeError("immutable synthetic source configuration required")
        if len({s.source for s in sources}) != len(sources):
            raise ConflictError("one frozen configuration per source")
        identifiers((run_id,))
        self.__sources = tuple(sorted(sources, key=lambda s: s.source))
        self.__run_id = run_id
        self.__candidates = []
        self.__receipts = {}
        self.__events = {}
        self.__reservations = {}
        self.__owners = {}
        self.__results = {}
        self.__population = OpportunityStore()
        self.__last_received = None
        self.__closed_at = None

    def candidates(self):
        return tuple(self.__candidates)

    def reservations(self):
        return tuple(self.__reservations.values())

    def population(self):
        return self.__population.population()

    def counts(self):
        admitted = sum(r.admitted for r in self.__results.values())
        return SamplingCounts(len(self.__candidates), len(self.__events), admitted,
                              admitted, len(self.population()))

    def register(self, envelope, *, role=DatasetRole.PILOT):
        if type(envelope) is not SyntheticEventEnvelope:
            raise TypeError("synthetic envelope required")
        closed(role, DatasetRole)
        e = envelope
        if any(c.role is not role and c.envelope.content_hash == e.content_hash for c in self.__candidates):
            raise ConflictError("cross-role content reuse")
        if e.receipt_id is not None and e.receipt_id in self.__receipts:
            old = self.__receipts[e.receipt_id]
            if old.envelope != e or old.role is not role:
                raise ConflictError("receipt identity conflict")
            return old
        if e.received_at is not None:
            if ((self.__last_received is not None and e.received_at < self.__last_received) or
                    (self.__closed_at is not None and e.received_at < self.__closed_at)):
                raise ConflictError("backdated receipt cannot rewrite registry")
        old = self.__events.get(e.event_id)
        if old is not None:
            if old.role is not role:
                raise ConflictError("cross-role event reuse")
            if (old.envelope.content_hash, old.envelope.source_version, old.envelope.normalization_version) != (
                    e.content_hash, e.source_version, e.normalization_version):
                raise ConflictError("declared revision/configuration conflict")
            if old.reservation_id is None and any(reason in old.reasons for reason in (
                    "SOURCE_UNAUTHORIZED", "RECEIPT_UNKNOWN_OR_INVALID")):
                # An unaccredited observation never wins a receipt race. Keep it
                # in the audit log; the first accredited receipt may reserve.
                candidate = self.__new_candidate(e, role)
            else:
                candidate = Candidate(e, role, Relation.DUPLICATE, old.cluster_id, old.reservation_id, ("DUPLICATE",))
        else:
            candidate = self.__new_candidate(e, role)
        # All validation precedes mutation.
        if candidate.reservation_id is not None and candidate.reservation_id not in self.__reservations:
            at, slot = decision_slot(e.received_at)
            self.__reservations[candidate.reservation_id] = Reservation(
                candidate.reservation_id, e.event_id, candidate.cluster_id, role, at, slot)
        if candidate.reservation_id is not None:
            self.__owners.setdefault(candidate.cluster_id, role)
        self.__candidates.append(candidate)
        if old is None or (old.reservation_id is None and candidate.reservation_id is not None):
            self.__events[e.event_id] = candidate
        if e.receipt_id is not None:
            self.__receipts[e.receipt_id] = candidate
        if e.received_at is not None:
            self.__last_received = e.received_at
        return candidate

    def __new_candidate(self, e, role):
        reasons = []
        source = next((s for s in self.__sources if s.source == e.source), None)
        if source is None or source.version != e.source_version or e.received_at is None or not source.authorized_at < e.received_at:
            reasons.append("SOURCE_UNAUTHORIZED")
        if not (e.receipt_verified and e.integrity_verified and e.receipt_id and e.received_at and e.provenance_hash):
            reasons.append("RECEIPT_UNKNOWN_OR_INVALID")
        if e.normalization_version != VERSION:
            reasons.append("NORMALIZATION_VERSION_UNKNOWN")
        cluster = None
        relation = e.relation
        prior = self.__events.get(e.prior_event_id)
        if e.shock_evidence is ShockEvidence.EXPLICIT_RELATION:
            if prior is not None and prior.cluster_id is not None and e.evidence_hash and relation in (
                    Relation.UPDATE, Relation.CORRECTION, Relation.SAME_CLUSTER_NEW_REPORT):
                if relation in (Relation.UPDATE, Relation.CORRECTION) and (
                        e.source != prior.envelope.source or e.document_id != prior.envelope.document_id):
                    raise ConflictError("revision relation belongs to another document")
                cluster = prior.cluster_id
        elif e.shock_evidence in (ShockEvidence.OFFICIAL_ANNOUNCEMENT, ShockEvidence.PRIMARY_DOCUMENT):
            if e.shock_namespace and e.shock_key and e.evidence_hash and relation is Relation.NEW_EVENT and e.prior_event_id is None:
                cluster = digest(("pnep-shock-v1", e.shock_evidence.value, e.shock_namespace, e.shock_key))
        if cluster is None:
            reasons.append("CLUSTER_UNKNOWN")
        if cluster in self.__owners and self.__owners[cluster] is not role:
            raise ConflictError("cross-role shock reuse")
        reservation_id = None
        if cluster is not None:
            key = digest((PROTOCOL, cluster, INSTRUMENT, VENUE, PRODUCT))
            if key in self.__reservations:
                reservation_id = key
                if relation is Relation.NEW_EVENT:
                    relation = Relation.SAME_CLUSTER_NEW_REPORT
                reasons.append("SHOCK_ALREADY_RESERVED")
            elif not reasons and relation is Relation.NEW_EVENT:
                reservation_id = key
            else:
                reasons.append("NO_NEW_EVENT_RESERVATION")
        return Candidate(e, role, relation, cluster, reservation_id, tuple(reasons))

    def __admission_reasons(self, reservation):
        candidate = self.__events[reservation.event_id]
        e = candidate.envelope
        reasons = list(candidate.reasons)
        if e.processed_at is None or e.available_at is None:
            reasons.append("ADMISSION_AVAILABILITY_UNKNOWN")
        elif e.available_at > reservation.decision_at:
            reasons.append("ADMISSION_LATE_NO_ROLLOVER")
        if not e.binding_unambiguous or "BTC" not in e.assets:
            reasons.append("BTC_BINDING_UNKNOWN")
        if e.announcement_count != 1:
            reasons.append("SEMANTIC_UNIT_UNKNOWN")
        # Only corrections already available at this cut can invalidate admission.
        if any(c.cluster_id == reservation.cluster_id and c.relation is Relation.CORRECTION and
               c.envelope.processed_at is not None and c.envelope.normalization_version == VERSION and
               c.envelope.integrity_verified and c.envelope.available_at is not None and
               c.envelope.available_at <= reservation.decision_at and
               "RECEIPT_UNKNOWN_OR_INVALID" not in c.reasons and "SOURCE_UNAUTHORIZED" not in c.reasons
               for c in self.__candidates):
            reasons.append("CORRECTION_AT_CUTOFF")
        return tuple(reasons)

    def sampling_eligible(self, reservation_id, cutoff):
        utc(cutoff)
        r = self.__reservations[reservation_id]
        if cutoff != r.decision_at:
            raise ValueError("only the reserved decision cutoff is permitted")
        if reservation_id in self.__results:
            return self.__results[reservation_id].admitted
        return not self.__admission_reasons(r)

    def close(self, cutoff):
        """Close an H1 cut in synthetic replay, not claim live execution."""
        utc(cutoff)
        if cutoff.minute or cutoff.second or cutoff.microsecond:
            raise ValueError("H1 boundary required")
        if self.__closed_at is not None and cutoff < self.__closed_at:
            raise ConflictError("decision cuts must be monotone")
        for key, r in self.__reservations.items():
            if r.decision_at > cutoff or key in self.__results:
                continue
            reasons = self.__admission_reasons(r)
            opportunity = None if reasons else self.__materialize(r)
            if opportunity is not None:
                self.__population.append(opportunity)
            self.__results[key] = Admission(key, not reasons, reasons, opportunity)
        self.__closed_at = cutoff
        return tuple(self.__results.values())

    def __materialize(self, r):
        e = self.__events[r.event_id].envelope
        identity = EligibleDecisionOpportunity.identity(PROTOCOL, r.event_id, INSTRUMENT, VENUE, PRODUCT, r.decision_slot_id)
        inputs = []
        for kind in InputType:
            is_event = kind is InputType.EVENT
            inputs.append(InputAvailabilityRecord(
                opportunity_id=identity, input_type=kind, input_key=kind.value,
                source=e.source if is_event else "synthetic-unobserved",
                instrument=INSTRUMENT, venue=VENUE, product=PRODUCT,
                decision_at=r.decision_at, assessed_at=r.decision_at,
                status=InputStatus.VALID if is_event else InputStatus.MISSING,
                source_event_time=e.event_time if is_event else None,
                received_at=e.received_at if is_event else None,
                available_at=e.available_at if is_event else None,
                receipt_ids=(e.receipt_id,) if is_event else (),
                value_hash=e.content_hash if is_event else None,
                provenance_hash=e.provenance_hash if is_event else None,
                validator_version=VERSION if is_event else None,
                reason_codes=() if is_event else ("NOT_OBSERVED_IN_SYNTHETIC_SLICE",)))
        return EligibleDecisionOpportunity(
            protocol_id=PROTOCOL, protocol_hash=digest((PROTOCOL, VERSION)), run_id=self.__run_id,
            dataset_role=r.role, population_rule_hash=digest((VERSION, INSTRUMENT, VENUE, PRODUCT,
                tuple((s.source, s.version, s.authorized_at.isoformat()) for s in self.__sources))),
            event_id=r.event_id, event_cluster_id=r.cluster_id, cluster_rule_version=VERSION,
            cluster_evidence_hash=e.evidence_hash, instrument=INSTRUMENT, venue=VENUE, product=PRODUCT,
            decision_slot_id=r.decision_slot_id, decision_at=r.decision_at, inputs=tuple(inputs))
