"""Causal comparability only; no execution, outcome inputs or population filter.

Kernel causal eligibility is distinct from operational gate authorization.
Missing policies remain explicitly absent; no reference decision is substituted.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .nuisance_pilot_contracts import DatasetRole, InputStatus, PolicyID, closed, digest
from .policy_kernel import PolicyDecision, PolicyInformationSet, PolicyKernel, require_comparable


class ExclusionReason(Enum):
    MISSING_DECISION = "MISSING_DECISION"
    MISSING_REQUIRED_INFORMATION = "MISSING_REQUIRED_INFORMATION"
    LATE_INFORMATION = "LATE_INFORMATION"
    UNKNOWN_AVAILABILITY = "UNKNOWN_AVAILABILITY"
    CONFLICT = "CONFLICT"
    DEPENDENCY_INELIGIBLE = "DEPENDENCY_INELIGIBLE"


@dataclass(frozen=True, slots=True)
class PolicyExclusion:
    policy: PolicyID
    reasons: tuple[ExclusionReason, ...]


@dataclass(frozen=True, slots=True)
class CommonSupportRecord:
    opportunity_id: str
    dataset_role: DatasetRole
    decision_at: datetime
    comparison_id: str
    controls_commitment: str
    opportunity_commitment: str
    eligible_policies: tuple[PolicyID, ...]
    exclusions: tuple[PolicyExclusion, ...]
    decision_commitments: tuple[tuple[PolicyID, str], ...]

    @property
    def cs4(self):
        return self.eligible_policies == tuple(PolicyID)

    def supports(self, policies):
        if type(policies) is not tuple or not policies:
            raise ValueError("explicit nonempty policy set required")
        for policy in policies:
            closed(policy, PolicyID)
        if len(set(policies)) != len(policies):
            raise ValueError("duplicate policy requested")
        return all(p in self.eligible_policies for p in policies)

    @property
    def support_id(self):
        return digest(("pnep-common-support-v1", self.opportunity_id, self.dataset_role.value,
            self.decision_at.isoformat(), self.comparison_id, self.controls_commitment,
            self.opportunity_commitment, tuple(p.value for p in self.eligible_policies),
            tuple((x.policy.value, tuple(r.value for r in x.reasons)) for x in self.exclusions),
            tuple((p.value, identity) for p, identity in self.decision_commitments)))


class CommonSupportRegistry:
    """First snapshot is final, including empty/partial support. In-memory only.

    All opportunities must be submitted before outcome access by the experiment
    controller. This API cannot detect opportunities deliberately never submitted
    or authenticate a caller's claim that registration happened before outcomes.
    """
    def __init__(self):
        self.__kernel = PolicyKernel()
        self.__records = {}

    def records(self):
        return tuple(self.__records.values())

    def register(self, opportunity, controls, decisions):
        if type(decisions) is not tuple or any(type(d) is not PolicyDecision for d in decisions):
            raise TypeError("immutable PolicyDecision tuple required")
        if any(type(d.information_set) is not PolicyInformationSet for d in decisions):
            raise TypeError("exact policy information sets required")
        # Reuse kernel formation as validation of supplied evidence, not as a
        # replacement for missing decisions. Temporary validation has no effects
        # on this registry if any supplied decision is incompatible or forged.
        expected = PolicyKernel().form(opportunity, controls)
        by_policy = {d.information_set.policy: d for d in expected}
        supplied = {}
        for decision in decisions:
            policy = decision.information_set.policy
            closed(policy, PolicyID)
            if policy in supplied:
                raise ValueError("DUPLICATE_POLICY_DECISION")
            if decision.opportunity_id != opportunity.opportunity_id:
                raise ValueError("OPPORTUNITY_MISMATCH")
            if decision.dataset_role is not opportunity.dataset_role:
                raise ValueError("ROLE_MISMATCH")
            reference = by_policy[policy]
            if (decision.controls != controls or decision.instrument != opportunity.instrument or
                    decision.venue != opportunity.venue or decision.product != opportunity.product or
                    decision.decision_at != opportunity.decision_at):
                raise ValueError("CONTROL_MISMATCH")
            if decision != reference:
                raise ValueError("PROVENANCE_OR_IDENTITY_CONFLICT")
            supplied[policy] = decision
        if decisions:
            require_comparable(decisions)
        eligible, exclusions, commitments = [], [], []
        reasons_by_status = {
            InputStatus.MISSING: ExclusionReason.MISSING_REQUIRED_INFORMATION,
            InputStatus.LATE: ExclusionReason.LATE_INFORMATION,
            InputStatus.UNKNOWN: ExclusionReason.UNKNOWN_AVAILABILITY,
            InputStatus.CONFLICT: ExclusionReason.CONFLICT,
            InputStatus.VALID: ExclusionReason.DEPENDENCY_INELIGIBLE,
        }
        for policy in PolicyID:
            decision = supplied.get(policy)
            if decision is None:
                exclusions.append(PolicyExclusion(policy, (ExclusionReason.MISSING_DECISION,)))
                continue
            commitments.append((policy, decision.decision_id))
            if decision.information_set.causal_eligible:
                eligible.append(policy)
            else:
                reasons = {reasons_by_status[e.status] for e in decision.information_set.evidence if not e.usable}
                exclusions.append(PolicyExclusion(policy, tuple(r for r in ExclusionReason if r in reasons)))
        record = CommonSupportRecord(opportunity.opportunity_id, opportunity.dataset_role, opportunity.decision_at,
            expected[0].comparison_id, controls.identity, expected[0].opportunity_commitment,
            tuple(eligible), tuple(exclusions), tuple(commitments))
        previous = self.__records.get(record.opportunity_id)
        if previous is not None:
            if previous != record:
                raise ValueError("SUPPORT_SNAPSHOT_CONFLICT: no retrospective replacement")
            return previous
        # Reuse kernel's immutable identity/control and cross-role shock guards.
        # Commit only after validation succeeds; no partial registry update.
        self.__kernel.form(opportunity, controls)
        self.__records[record.opportunity_id] = record
        return record
