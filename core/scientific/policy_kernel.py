"""Outcome-blind PNEP policy formation contracts; no action selection or I/O.

Views contain causal value commitments, not executable payloads or resolvers.
Attested family/provenance semantics remain an upstream trust boundary.
"""
from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .nuisance_pilot_contracts import (
    DatasetRole, EligibleDecisionOpportunity, InputAvailabilityRecord, InputStatus,
    InputType, PolicyID, PolicyDisposition, closed, digest, identifiers,
)


def canonical(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is Decimal:
        sign, digits, exponent = value.as_tuple()
        digits = list(digits)
        while len(digits) > 1 and digits[-1] == 0:
            digits.pop()
            exponent += 1
        return (sign, tuple(digits), exponent)
    if type(value) is tuple:
        return tuple(canonical(v) for v in value)
    if type(value) in (InputAvailabilityRecord, SharedControls, InputEvidence, PolicyInformationSet):
        return tuple((f.name, tuple(sorted((canonical(d) for d in value.dependencies), key=digest))
                      if type(value) is InputAvailabilityRecord and f.name == "dependencies"
                      else canonical(getattr(value, f.name))) for f in fields(value))
    if value is None or type(value) in (str, int, bool):
        return value
    raise TypeError("unsupported policy contract value")


def families(policy):
    closed(policy, PolicyID)
    return {
        PolicyID.P0: (InputType.EVENT, InputType.PRICE),
        PolicyID.PR: (InputType.EVENT, InputType.PRICE, InputType.REGIME),
        PolicyID.PM: (InputType.EVENT, InputType.PRICE, InputType.MECHANICS),
        PolicyID.PRM: tuple(InputType),
    }[policy]


@dataclass(frozen=True, slots=True)
class SharedControls:
    """Explicit predeclared specifications; no defaults, sizing or cost engine.

    Specs are content commitments supplied by the experiment owner. Their actual
    implementation and authenticity are not verified by this representation.
    """
    policy_contract_hash: str
    timeframe: str
    risk_budget_quote: Decimal
    quote_currency: str
    risk_spec_hash: str
    sizing_spec_hash: str
    execution_spec_hash: str
    accounting_spec_hash: str
    transaction_cost_spec_hash: str
    outcome_horizon_seconds: int

    def __post_init__(self):
        if self.timeframe != "H1":
            raise ValueError("PNEP H1 controls required")
        identifiers((self.quote_currency,))
        for f in fields(self):
            if f.name.endswith("_hash"):
                value = getattr(self, f.name)
                if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                    raise ValueError("SHA-256 specification commitment required")
        if type(self.risk_budget_quote) is not Decimal or not self.risk_budget_quote.is_finite() or self.risk_budget_quote <= 0:
            raise ValueError("explicit finite positive risk budget required")
        if type(self.outcome_horizon_seconds) is not int or self.outcome_horizon_seconds <= 0:
            raise ValueError("explicit positive horizon required")

    @property
    def identity(self):
        return digest(canonical(self))


@dataclass(frozen=True, slots=True)
class InputEvidence:
    family: InputType
    status: InputStatus
    assessment_hash: str
    value_hash: str | None
    usable: bool
    reason: str

    def __post_init__(self):
        closed(self.family, InputType)
        closed(self.status, InputStatus)
        if type(self.assessment_hash) is not str or len(self.assessment_hash) != 64 or any(c not in "0123456789abcdef" for c in self.assessment_hash):
            raise ValueError("assessment commitment required")
        if type(self.usable) is not bool:
            raise TypeError("explicit usability required")
        if self.usable:
            if self.status is not InputStatus.VALID or self.reason != "CAUSALLY_ADMISSIBLE":
                raise ValueError("non-valid evidence cannot be usable")
            identifiers((self.value_hash,))
        elif self.value_hash is not None or self.reason != "INPUT_OR_DEPENDENCY_INELIGIBLE":
            raise ValueError("ineligible evidence cannot expose a value")


@dataclass(frozen=True, slots=True)
class PolicyInformationSet:
    policy: PolicyID
    evidence: tuple[InputEvidence, ...]

    def __post_init__(self):
        expected = families(self.policy)
        if type(self.evidence) is not tuple or any(type(x) is not InputEvidence for x in self.evidence):
            raise TypeError("typed immutable policy evidence required")
        if tuple(x.family for x in self.evidence) != expected:
            raise ValueError("information mask violation")

    def get(self, family):
        closed(family, InputType)
        if family not in families(self.policy):
            raise PermissionError("family outside policy information mask")
        return next(x for x in self.evidence if x.family is family)

    @property
    def causal_eligible(self):
        return all(x.usable for x in self.evidence)

    @property
    def identity(self):
        return digest(canonical(self))


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Formation record only. None disposition means unexecuted, not abstain."""
    opportunity_id: str
    event_id: str
    event_cluster_id: str
    dataset_role: DatasetRole
    instrument: str
    venue: str
    product: str
    decision_at: datetime
    controls: SharedControls
    opportunity_commitment: str
    information_set: PolicyInformationSet
    disposition: PolicyDisposition | None

    @property
    def comparison_id(self):
        return digest((self.opportunity_commitment, self.controls.identity, self.opportunity_id,
                       self.event_id, self.event_cluster_id, self.dataset_role.value,
                       self.instrument, self.venue, self.product, self.decision_at.isoformat()))

    @property
    def decision_id(self):
        return digest(("pnep-policy-formation-v1", self.comparison_id, self.information_set.identity,
                       self.disposition.value if self.disposition is not None else None))


def _usable(record, allowed, opportunity):
    # Check transitive dependencies too; exposing a raw assessment object would
    # otherwise give P0 a route to REGIME through PRICE.dependencies.
    if record.input_type not in allowed:
        return False
    if (record.opportunity_id != opportunity.opportunity_id or record.decision_at != opportunity.decision_at or
            (record.instrument, record.venue, record.product) != (opportunity.instrument, opportunity.venue, opportunity.product)):
        return False
    if record.status is not InputStatus.VALID or record.available_at is None or record.available_at > opportunity.decision_at:
        return False
    return all(_usable(d, allowed, opportunity) for d in record.dependencies)


class PolicyKernel:
    """One isolated experiment context; no outcome input or arbitrary callbacks.

    Immutable opportunity snapshots and cluster roles are bound on first use.
    Share this context across compared policies; separate contexts need the
    existing PNEP dataset manifest isolation before data can be combined.
    """
    def __init__(self):
        self.__opportunities = {}
        self.__roles = {}
        self.__controls = {}

    def form(self, opportunity, controls):
        if type(opportunity) is not EligibleDecisionOpportunity or type(controls) is not SharedControls:
            raise TypeError("exact PNEP opportunity and controls required")
        closed(opportunity.dataset_role, DatasetRole)
        if opportunity.protocol_id != "OMA-PNEP-1.0":
            raise ValueError("unsupported protocol")
        # Canonicalize family order, retaining the FULL evidence content rather
        # than record_id (which does not commit status/value/provenance).
        snapshot = tuple((f.name, canonical(tuple(sorted(opportunity.inputs, key=lambda x: x.input_type.value)))
                          if f.name == "inputs" else canonical(getattr(opportunity, f.name)))
                         for f in fields(opportunity))
        commitment = digest(snapshot)
        prior = self.__opportunities.get(opportunity.opportunity_id)
        if prior is not None and prior != commitment:
            raise ValueError("opportunity snapshot conflict; no retrospective repair")
        for key in (("event", opportunity.event_id), ("cluster", opportunity.event_cluster_id)):
            if key in self.__roles and self.__roles[key] is not opportunity.dataset_role:
                raise ValueError("cross-role event/cluster reuse")
        previous_controls = self.__controls.get(opportunity.opportunity_id)
        if previous_controls is not None and previous_controls != controls.identity:
            raise ValueError("shared controls conflict")
        decisions = []
        for policy in PolicyID:
            allowed = families(policy)
            evidence = []
            for family in allowed:
                record = next(x for x in opportunity.inputs if x.input_type is family)
                usable = _usable(record, allowed, opportunity)
                evidence.append(InputEvidence(family, record.status, digest(canonical(record)),
                    record.value_hash if usable else None, usable,
                    "CAUSALLY_ADMISSIBLE" if usable else "INPUT_OR_DEPENDENCY_INELIGIBLE"))
            view = PolicyInformationSet(policy, tuple(evidence))
            # Preserve original fail-closed operational gates. Causal support is
            # separate: this slice grants no Regime/Mechanics execution authority.
            disposition = opportunity.input_disposition(policy) if view.causal_eligible else PolicyDisposition.INPUT_INELIGIBLE
            decisions.append(PolicyDecision(opportunity.opportunity_id, opportunity.event_id, opportunity.event_cluster_id,
                opportunity.dataset_role, opportunity.instrument, opportunity.venue, opportunity.product,
                opportunity.decision_at, controls, commitment, view, disposition))
        self.__opportunities[opportunity.opportunity_id] = commitment
        self.__controls[opportunity.opportunity_id] = controls.identity
        for key in (("event", opportunity.event_id), ("cluster", opportunity.event_cluster_id)):
            self.__roles[key] = opportunity.dataset_role
        return tuple(decisions)


def require_comparable(decisions):
    """Validate shared formation context, not economic results/common support."""
    if type(decisions) is not tuple or not decisions or any(type(d) is not PolicyDecision for d in decisions):
        raise TypeError("immutable formation records required")
    first = decisions[0]
    shared = lambda d: (d.opportunity_id, d.event_id, d.event_cluster_id, d.dataset_role, d.instrument,
                        d.venue, d.product, d.decision_at, d.controls, d.opportunity_commitment)
    if any(shared(d) != shared(first) for d in decisions):
        raise ValueError("incompatible experimental controls or opportunity evidence")
    if len({d.information_set.policy for d in decisions}) != len(decisions):
        raise ValueError("duplicate policy in comparison")
    # Shared permitted families must mean the same evidence, not just same names.
    seen = {}
    for decision in decisions:
        for item in decision.information_set.evidence:
            previous = seen.get(item.family)
            if previous is not None and (previous.assessment_hash != item.assessment_hash or
                    previous.status is not item.status or
                    (previous.usable and item.usable and previous.value_hash != item.value_hash)):
                raise ValueError("shared information differs")
            if previous is None or item.usable:
                seen[item.family] = item
    return first.comparison_id
