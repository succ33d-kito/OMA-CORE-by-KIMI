"""NON-CALIBRATED, NON-EDGE, TEST/REFERENCE ONLY. No execution integration."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .nuisance_pilot_contracts import DatasetRole, InputType, PolicyID, closed, digest, identifiers, utc
from .policy_kernel import PolicyDecision, PolicyInformationSet, SharedControls


class IntentAction(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    ABSTAIN = "ABSTAIN"  # No new exposure; not a command to close a position.


@dataclass(frozen=True, slots=True)
class ReferenceSignal:
    """Synthetic vote, not a market feature. No payload/metadata/dependencies."""
    family: InputType
    vote: int

    def __post_init__(self):
        closed(self.family, InputType)
        if type(self.vote) is not int or self.vote not in (-1, 0, 1):
            raise ValueError("synthetic vote must be -1, 0 or 1")

    @property
    def commitment(self):
        return digest(("pnep-synthetic-vote-v1", self.family.value, self.vote))


@dataclass(frozen=True, slots=True)
class ReferenceRule:
    version: str
    minimum_absolute_votes: int

    def __post_init__(self):
        if self.version != "1":
            raise ValueError("unsupported reference rule version")
        if type(self.minimum_absolute_votes) is not int or self.minimum_absolute_votes <= 0:
            raise ValueError("explicit positive integer vote threshold required")

    @property
    def rule_id(self):
        return "pnep-synthetic-vote-sum"

    @property
    def parameters_commitment(self):
        return digest(("minimum_absolute_votes", self.minimum_absolute_votes))

    @property
    def identity(self):
        return digest((self.rule_id, self.version, self.parameters_commitment,
            tuple(a.value for a in IntentAction), "ABSTAIN_NO_NEW_EXPOSURE", "TEST_REFERENCE_ONLY"))


@dataclass(frozen=True, slots=True)
class ActionIntent:
    opportunity_id: str
    policy: PolicyID
    dataset_role: DatasetRole
    decision_at: datetime
    policy_decision_id: str
    comparison_id: str
    information_commitment: str
    controls_commitment: str
    rule: ReferenceRule
    value_commitments: tuple[tuple[InputType, str], ...]
    action: IntentAction

    def __post_init__(self):
        closed(self.policy, PolicyID)
        closed(self.dataset_role, DatasetRole)
        closed(self.action, IntentAction)
        utc(self.decision_at)
        identifiers((self.opportunity_id, self.policy_decision_id, self.comparison_id,
                     self.information_commitment, self.controls_commitment))
        if type(self.rule) is not ReferenceRule or type(self.value_commitments) is not tuple:
            raise TypeError("immutable rule and value commitments required")
        for item in self.value_commitments:
            if type(item) is not tuple or len(item) != 2:
                raise TypeError("immutable family commitment pair required")
            closed(item[0], InputType)
            identifiers((item[1],))
        order = tuple(f.value for f, _ in self.value_commitments)
        if not order or order != tuple(sorted(set(order))):
            raise ValueError("canonical unique family commitments required")

    @property
    def reference_only(self):
        return True

    @property
    def intent_id(self):
        return digest(("pnep-reference-action-intent-v1", self.opportunity_id, self.policy.value,
            self.dataset_role.value, self.decision_at.isoformat(), self.policy_decision_id,
            self.comparison_id, self.information_commitment, self.controls_commitment,
            self.rule.identity, tuple((f.value, h) for f, h in self.value_commitments), self.action.value))


def _reference_action(votes, minimum_absolute_votes):
    # This function receives no policy name, role, controls or external context.
    total = sum(votes)
    if abs(total) < minimum_absolute_votes:
        return IntentAction.ABSTAIN
    return IntentAction.LONG if total > 0 else IntentAction.SHORT


def decide_reference(decision, rule, signals):
    """Return a non-operational intent, or reject; never downgrade an information set.

    The caller supplies an upstream-validated PolicyDecision. This primitive does
    not authenticate forged decisions, provenance or market feature semantics.
    """
    if type(decision) is not PolicyDecision or type(rule) is not ReferenceRule:
        raise TypeError("exact policy decision and reference rule required")
    if type(decision.information_set) is not PolicyInformationSet or type(decision.controls) is not SharedControls:
        raise TypeError("exact information set and controls required")
    closed(decision.dataset_role, DatasetRole)
    utc(decision.decision_at)
    # None is the existing unexecuted state. No other disposition is silently
    # reinterpreted, particularly INPUT_INELIGIBLE or prior POLICY_ABSTAIN.
    if decision.disposition is not None or not decision.information_set.causal_eligible:
        raise ValueError("decision ineligible or not unexecuted; no fallback")
    if type(signals) is not tuple or any(type(x) is not ReferenceSignal for x in signals):
        raise TypeError("immutable typed synthetic signals required")
    if len({x.family for x in signals}) != len(signals):
        raise ValueError("duplicate signal family")
    view = decision.information_set
    for signal in signals:
        evidence = view.get(signal.family)  # Kernel owns authorization, including masks.
        if signal.commitment != evidence.value_hash:
            raise ValueError("signal does not match committed input")
    if {x.family for x in signals} != {e.family for e in view.evidence}:
        raise ValueError("missing authorized input; no fallback")
    ordered = tuple(sorted(signals, key=lambda x: x.family.value))
    action = _reference_action(tuple(x.vote for x in ordered), rule.minimum_absolute_votes)
    return ActionIntent(decision.opportunity_id, view.policy, decision.dataset_role,
        decision.decision_at, decision.decision_id, decision.comparison_id, view.identity,
        decision.controls.identity, rule, tuple((x.family, x.commitment) for x in ordered), action)


def require_same_rule_experiment(intents):
    """Paired contract check, not an economic comparison or outcome evaluator."""
    if type(intents) is not tuple or not intents or any(type(x) is not ActionIntent for x in intents):
        raise TypeError("nonempty immutable intent tuple required")
    if len({x.policy for x in intents}) != len(intents):
        raise ValueError("duplicate policy intent")
    key = lambda x: (x.opportunity_id, x.dataset_role, x.decision_at, x.comparison_id,
                     x.controls_commitment, x.rule.identity)
    if any(key(x) != key(intents[0]) for x in intents):
        raise ValueError("incompatible rule experiment")
    seen = {}
    for intent in intents:
        for family, commitment in intent.value_commitments:
            if family in seen and seen[family] != commitment:
                raise ValueError("shared input content differs")
            seen[family] = commitment
    return digest((intents[0].comparison_id, intents[0].rule.identity))
