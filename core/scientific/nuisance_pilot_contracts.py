"""OMA-PNEP-1.0 Slice 1: immutable, non-operational contracts only.

No market data, policy kernel, outcome calculation or statistical release lives
here. Proof references are supplied by a trusted validator; this schema cannot
authenticate evidence. UNKNOWN is deliberately different from admissible.
"""
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import hashlib
import json
import re


class DatasetRole(Enum):
    PILOT = "PILOT"
    DISCOVERY = "DISCOVERY"
    CONFIRMATION = "CONFIRMATION"


class InputStatus(Enum):
    VALID = "VALID"
    MISSING = "MISSING"
    LATE = "LATE"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"


class PolicyID(Enum):
    P0 = "P0"
    PR = "PR"
    PM = "PM"
    PRM = "PRM"


class PolicyDisposition(Enum):
    INPUT_INELIGIBLE = "INPUT_INELIGIBLE"
    POLICY_ABSTAIN = "POLICY_ABSTAIN"
    POLICY_ENTER = "POLICY_ENTER"


class InputType(Enum):
    EVENT = "EVENT"
    PRICE = "PRICE"
    REGIME = "REGIME"
    MECHANICS = "MECHANICS"


class PilotState(Enum):
    NOT_STARTED = "NOT_STARTED"
    COLLECTING = "COLLECTING"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    PARAMETER_READY = "PARAMETER_READY"
    INVALID = "INVALID"


class OutcomeIntegrity(Enum):
    PENDING = "PENDING"
    VALID = "VALID"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"
    INVALID = "INVALID"


class EvidenceType(Enum):
    OBSERVED_QUOTE = "OBSERVED_QUOTE"
    EXPECTED_FILL = "EXPECTED_FILL"
    REAL_FILL = "REAL_FILL"
    FEE_SCHEDULE = "FEE_SCHEDULE"
    REALIZED_FEE = "REALIZED_FEE"
    PUBLISHED_FUNDING = "PUBLISHED_FUNDING"
    REALIZED_FUNDING = "REALIZED_FUNDING"
    LATENCY_MEASUREMENT = "LATENCY_MEASUREMENT"


class AccessClass(Enum):
    RESTRICTED = "RESTRICTED"
    SAFE_AGGREGATE = "SAFE_AGGREGATE"


class ExecutionScenario(Enum):
    BASE = "BASE"
    STRESS = "STRESS"
    LEGACY_EXECUTION_SCENARIO = "LEGACY_EXECUTION_SCENARIO"


class ValuationMode(Enum):
    REFERENCE_EXPECTED = "REFERENCE_EXPECTED"
    REALIZED = "REALIZED"


class CostComponent(Enum):
    FEE = "FEE"
    SPREAD = "SPREAD"
    SLIPPAGE = "SLIPPAGE"
    FUNDING = "FUNDING"
    OTHER = "OTHER"


class CostBasis(Enum):
    MID_COMPONENTS = "MID_COMPONENTS"
    FILL_EMBEDDED = "FILL_EMBEDDED"


class Direction(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class LatencyKind(Enum):
    HTTP_ROUND_TRIP = "HTTP_ROUND_TRIP"
    SOURCE_TO_RECEIPT = "SOURCE_TO_RECEIPT"
    RECEIPT_TO_AVAILABLE = "RECEIPT_TO_AVAILABLE"
    DECISION_TO_REQUEST = "DECISION_TO_REQUEST"
    REQUEST_TO_FILL = "REQUEST_TO_FILL"


def utc(value):
    if not isinstance(value, datetime) or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("UTC-aware datetime required")


def closed(value, kind):
    if type(value) is not kind:
        raise TypeError("closed enum required")


def identifiers(value):
    if type(value) is not tuple or any(type(x) is not str or not x.strip() for x in value):
        raise TypeError("immutable nonempty string identifiers required")


def digest(parts):
    return hashlib.sha256(json.dumps(parts, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()


STATUS_PRECEDENCE = (InputStatus.CONFLICT, InputStatus.MISSING, InputStatus.UNKNOWN,
                     InputStatus.LATE, InputStatus.VALID)


def worst_status(statuses):
    values = tuple(statuses)
    for value in values:
        closed(value, InputStatus)
    return next((s for s in STATUS_PRECEDENCE if s in values), InputStatus.UNKNOWN)


@dataclass(frozen=True, slots=True)
class InputAvailabilityRecord:
    """An assessment frozen at decision_at, never repaired by later receipts.

    Missing candidate => MISSING; candidate without verifiable availability =>
    UNKNOWN. Derived availability includes computation AND all dependencies.
    References attest provenance, not independent verification of its truth.
    """
    opportunity_id: str
    input_type: InputType
    input_key: str
    source: str
    instrument: str
    venue: str
    product: str
    decision_at: datetime
    assessed_at: datetime
    status: InputStatus
    source_event_time: datetime | None = None
    received_at: datetime | None = None
    available_at: datetime | None = None
    computed_at: datetime | None = None
    receipt_ids: tuple[str, ...] = ()
    dependencies: tuple["InputAvailabilityRecord", ...] = ()
    value_hash: str | None = None
    provenance_hash: str | None = None
    validator_version: str | None = None
    conflict: bool = False
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self):
        closed(self.input_type, InputType)
        closed(self.status, InputStatus)
        identifiers((self.opportunity_id, self.input_key, self.source, self.instrument, self.venue, self.product))
        identifiers(self.receipt_ids)
        identifiers(self.reason_codes)
        for value in (self.value_hash, self.provenance_hash, self.validator_version):
            if value is not None:
                identifiers((value,))
        if type(self.dependencies) is not tuple or any(type(d) is not InputAvailabilityRecord for d in self.dependencies):
            raise TypeError("immutable dependency records required")
        if type(self.conflict) is not bool:
            raise TypeError("conflict must be boolean")
        for t in (self.decision_at, self.assessed_at):
            utc(t)
        for t in (self.source_event_time, self.received_at, self.available_at, self.computed_at):
            if t is not None:
                utc(t)
        if self.assessed_at != self.decision_at:
            raise ValueError("assessment must use original decision cut")
        if any(d.decision_at != self.decision_at or d.opportunity_id != self.opportunity_id for d in self.dependencies):
            raise ValueError("dependency belongs to another decision")
        expected = self.expected_status()
        if self.status is not expected:
            raise ValueError("input status inconsistent with availability/provenance")
        if self.status is not InputStatus.VALID and not self.reason_codes:
            raise ValueError("non-admissible input needs explicit reason")

    @property
    def dependency_ids(self):
        return tuple(d.record_id for d in self.dependencies)

    @property
    def record_id(self):
        return digest((self.opportunity_id, self.input_type.value, self.input_key))

    def expected_status(self):
        if self.conflict:
            return InputStatus.CONFLICT
        local = InputStatus.VALID
        if not self.value_hash:
            local = InputStatus.MISSING
        elif not (self.provenance_hash and self.validator_version and self.available_at is not None):
            local = InputStatus.UNKNOWN
        elif self.dependencies:
            if self.received_at is not None and self.available_at < self.received_at:
                raise ValueError("availability precedes receipt")
            if self.computed_at is None or any(d.available_at is None for d in self.dependencies):
                local = InputStatus.UNKNOWN
            elif self.available_at != max(self.computed_at, *(d.available_at for d in self.dependencies)):
                raise ValueError("derived availability must equal maximum computation/dependencies")
        elif self.computed_at is not None or not self.receipt_ids or self.received_at is None:
            local = InputStatus.UNKNOWN
        elif self.available_at < self.received_at:
            raise ValueError("availability precedes receipt")
        if local is InputStatus.VALID and self.available_at > self.decision_at:
            local = InputStatus.LATE
        return worst_status((local, *(d.status for d in self.dependencies)))


@dataclass(frozen=True, slots=True)
class EligibleDecisionOpportunity:
    """Population membership, NOT a policy decision or operational trade.

    Slice 1 stores supplied cluster identity and input assessments only. A None
    disposition means no kernel has run, never abstention. External gate proof is
    deliberately absent: REGIME/MECHANICS policies remain fail-closed here.
    """
    protocol_id: str
    protocol_hash: str
    run_id: str
    dataset_role: DatasetRole
    population_rule_hash: str
    event_id: str
    event_cluster_id: str
    cluster_rule_version: str
    cluster_evidence_hash: str
    instrument: str
    venue: str
    product: str
    decision_slot_id: str
    decision_at: datetime
    inputs: tuple[InputAvailabilityRecord, ...]

    def __post_init__(self):
        closed(self.dataset_role, DatasetRole)
        utc(self.decision_at)
        identifiers(tuple(getattr(self, f.name) for f in fields(self) if f.name not in {"dataset_role", "decision_at", "inputs"}))
        if type(self.inputs) is not tuple or len(self.inputs) != len(InputType):
            raise ValueError("one assessment per input type required, including missing")
        if any(type(i) is not InputAvailabilityRecord for i in self.inputs):
            raise TypeError("input records required")
        if {i.input_type for i in self.inputs} != set(InputType):
            raise ValueError("duplicate or missing input type")
        if any(i.opportunity_id != self.opportunity_id or i.decision_at != self.decision_at or
               (i.instrument, i.venue, i.product) != (self.instrument, self.venue, self.product) for i in self.inputs):
            raise ValueError("input assessment belongs to another opportunity")

    @staticmethod
    def identity(protocol_id, event_id, instrument, venue, product, decision_slot_id):
        parts = (protocol_id, event_id, instrument, venue, product, decision_slot_id)
        identifiers(parts)
        return digest(parts)

    @property
    def opportunity_id(self):
        return self.identity(self.protocol_id, self.event_id, self.instrument, self.venue, self.product, self.decision_slot_id)

    def input_disposition(self, policy):
        closed(policy, PolicyID)
        required = {InputType.EVENT, InputType.PRICE}
        if policy in (PolicyID.PR, PolicyID.PRM):
            required.add(InputType.REGIME)
        if policy in (PolicyID.PM, PolicyID.PRM):
            required.add(InputType.MECHANICS)
        if any(i.status is not InputStatus.VALID for i in self.inputs if i.input_type in required):
            return PolicyDisposition.INPUT_INELIGIBLE
        # Gate verification is outside this slice; do not manufacture gate proof.
        if policy is not PolicyID.P0:
            return PolicyDisposition.INPUT_INELIGIBLE
        return None


@dataclass(frozen=True, slots=True, repr=False)
class RestrictedOutcome:
    """Schema only. Never mapping-compatible, safe-serializable or operational.

    repr deliberately hides every value. Reflection/asdict/pickle in a hostile
    Python process are NOT a security boundary; deployment isolation is future.
    """
    outcome_id: str
    opportunity_id: str
    policy_id: PolicyID
    horizon_id: str
    protocol_hash: str
    policy_kernel_hash: str
    information_set_hash: str
    disposition: PolicyDisposition
    direction: Direction
    valuation_mode: ValuationMode
    execution_scenario: ExecutionScenario
    decision_at: datetime
    outcome_window_start: datetime
    outcome_window_end: datetime
    computed_at: datetime
    integrity_status: OutcomeIntegrity = OutcomeIntegrity.PENDING
    reference_notional_quote: Decimal | None = None
    quantity_base: Decimal | None = None
    gross_quote: Decimal | None = None
    fees_quote: Decimal | None = None
    spread_quote: Decimal | None = None
    slippage_quote: Decimal | None = None
    funding_quote: Decimal | None = None
    other_costs_quote: Decimal | None = None
    net_quote: Decimal | None = None
    net_return: Decimal | None = None
    cost_basis: CostBasis = CostBasis.MID_COMPONENTS
    cost_evidence_ids: tuple[str, ...] = ()
    outcome_receipt_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    record_hash: str | None = None
    dataset_role: DatasetRole = DatasetRole.PILOT
    access_class: AccessClass = AccessClass.RESTRICTED

    def __repr__(self):
        return "<RestrictedOutcome REDACTED>"

    def __post_init__(self):
        for name, kind in (("policy_id", PolicyID), ("disposition", PolicyDisposition),
                           ("direction", Direction), ("valuation_mode", ValuationMode),
                           ("execution_scenario", ExecutionScenario), ("integrity_status", OutcomeIntegrity),
                           ("cost_basis", CostBasis), ("dataset_role", DatasetRole), ("access_class", AccessClass)):
            closed(getattr(self, name), kind)
        if self.dataset_role is not DatasetRole.PILOT or self.access_class is not AccessClass.RESTRICTED:
            raise ValueError("restricted pilot outcome required")
        identifiers((self.outcome_id, self.opportunity_id, self.horizon_id, self.protocol_hash,
                     self.policy_kernel_hash, self.information_set_hash))
        for name in ("cost_evidence_ids", "outcome_receipt_ids", "reason_codes"):
            identifiers(getattr(self, name))
        if self.record_hash is not None:
            identifiers((self.record_hash,))
        for t in (self.decision_at, self.outcome_window_start, self.outcome_window_end, self.computed_at):
            utc(t)
        if not self.decision_at <= self.outcome_window_start < self.outcome_window_end:
            raise ValueError("invalid outcome window")
        amounts = tuple(getattr(self, name) for name in (
            "reference_notional_quote", "quantity_base", "gross_quote", "fees_quote", "spread_quote",
            "slippage_quote", "funding_quote", "other_costs_quote", "net_quote", "net_return"))
        if any(v is not None and (type(v) is not Decimal or not v.is_finite()) for v in amounts):
            raise TypeError("finite Decimal or explicit unknown required")
        if self.disposition is PolicyDisposition.INPUT_INELIGIBLE and any(v is not None for v in amounts):
            raise ValueError("ineligible outcome has no economic values")
        if self.disposition is PolicyDisposition.POLICY_ABSTAIN:
            if self.direction is not Direction.FLAT or any(v is not None and v != 0 for v in amounts[1:]):
                raise ValueError("abstention requires flat direction and explicit zero or unknown economics")
        if self.disposition is PolicyDisposition.POLICY_ENTER and self.direction is Direction.FLAT:
            raise ValueError("entry needs a direction")
        if self.integrity_status is OutcomeIntegrity.VALID:
            if self.computed_at < self.outcome_window_end or not self.record_hash or not self.outcome_receipt_ids:
                raise ValueError("valid outcome requires completed window and evidence")
            if self.disposition is PolicyDisposition.POLICY_ENTER and any(v is None for v in amounts):
                raise ValueError("unknown economics cannot be VALID")
            if self.disposition is PolicyDisposition.POLICY_ABSTAIN and any(v is None for v in amounts[1:]):
                raise ValueError("valid abstention requires explicit zeros, never imputation")


@dataclass(frozen=True, slots=True)
class SafeOutput:
    """Closed Slice 1 control release. No statistics or extensible metadata.

    Identity/hash fields must be bound by a future trusted release controller;
    arbitrary permitted identifiers are not a defense against covert channels.
    """
    protocol_hash: str
    release_id: str
    generated_at: datetime
    processor_code_hash: str
    sealed_input_commitment: str
    release_rule_hash: str
    pilot_state: PilotState = PilotState.NOT_STARTED
    protocol_id: str = "OMA-PNEP-1.0"
    protocol_version: str = "1.0"
    parameter_schema_version: str = "SLICE_1"
    reason_codes: tuple[str, ...] = ("SLICE_1_ONLY",)

    def __post_init__(self):
        closed(self.pilot_state, PilotState)
        utc(self.generated_at)
        if self.pilot_state is PilotState.PARAMETER_READY:
            raise ValueError("parameter readiness unavailable in Slice 1")
        if (self.protocol_id, self.protocol_version, self.parameter_schema_version) != ("OMA-PNEP-1.0", "1.0", "SLICE_1"):
            raise ValueError("unsupported protocol")
        for value in (self.protocol_hash, self.release_id, self.processor_code_hash,
                      self.sealed_input_commitment, self.release_rule_hash):
            if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
                raise ValueError("SHA-256 control identifier required")
        if self.reason_codes != ("SLICE_1_ONLY",):
            raise ValueError("closed Slice 1 reason vocabulary")

    @classmethod
    def from_mapping(cls, data):
        if type(data) is not dict or set(data) - {f.name for f in fields(cls)}:
            raise TypeError("closed SafeOutput schema required")
        return cls(**data)

    def public_record(self):
        return {f.name: (getattr(self, f.name).value if isinstance(getattr(self, f.name), Enum)
                         else getattr(self, f.name).isoformat() if isinstance(getattr(self, f.name), datetime)
                         else getattr(self, f.name)) for f in fields(self)}


class PilotRun:
    """Control transitions only; INVALID terminal, no readiness transition."""
    __slots__ = ("__state",)

    def __init__(self):
        self.__state = PilotState.NOT_STARTED

    @property
    def state(self):
        return self.__state

    def transition(self, target):
        closed(target, PilotState)
        permitted = {
            PilotState.NOT_STARTED: {PilotState.COLLECTING, PilotState.INVALID},
            PilotState.COLLECTING: {PilotState.INSUFFICIENT_INFORMATION, PilotState.INVALID},
            PilotState.INSUFFICIENT_INFORMATION: {PilotState.COLLECTING, PilotState.INVALID},
            PilotState.INVALID: set(),
        }
        if target not in permitted[self.__state]:
            raise ValueError("forbidden pilot transition")
        self.__state = target
