"""Frozen ex-ante REAL policy value adapter + policy-blind decision rule commitments.

OUTCOME-BLIND BY CONSTRUCTION. This module performs no I/O, opens no journal,
reads no label/return/PnL and imports no outcome loader. It does not invent
semantics: it makes explicit, hashable and verifiable the commitments that are
already implemented by ``experiment51_p0`` (P0 agreement) and
``experiment51_derived`` (PR/PM/PRM derived projection), and it binds them to the
canonical preregistration commitment.

Purpose: allow the Experiment 51 blocker ``REAL_POLICY_VALUE_RULE_NOT_QUALIFIED``
to be audited objectively, without modifying the historical prereg artifact.

What this module is NOT:
* it is not a probability model (no probability/confidence semantics exist in the
  frozen prereg) and must not be read as one;
* it is not the synthetic ``ReferenceRule`` path, which remains isolated and
  non-executable for Experiment 51;
* it does not select or tune thresholds from data.
"""
from decimal import Decimal

from .decision_rule import IntentAction
from .event_direction_v1 import RULE_HASH as EVENT_DIRECTION_RULE_HASH
from .experiment51_derived import FAMILY, PREREG, RULES, actions, protocol
from .experiment51_p0 import P0_HASH
from .experiment51_preparation import commitment
from .nuisance_pilot_contracts import PolicyID, digest
from .policy_kernel import families


SCHEMA = 'experiment51-policy-value-commitment-v1'
VALUE_ADAPTER_ID = 'experiment51-real-policy-value-adapter-v1'
DECISION_RULE_ID = 'experiment51-policy-blind-decision-rule-v1'
THRESHOLD_ID = 'experiment51-action-thresholds-v1'

# Every value below is the literal semantic already committed by P0_HASH / RULES and
# implemented by ``experiment51_p0._agreement`` and ``experiment51_derived.actions``.
# Nothing here is chosen, estimated or tuned in this module.
THRESHOLD_SPEC = dict(
    p0_agreement='equal LONG/SHORT only; otherwise ABSTAIN',
    regime_pass_structures=('range', 'trend'),
    regime_veto_structures=('transition', 'unknown'),
    regime_missing='ABSTAIN; missing is not neutral',
    taker_confirm_long='strictly greater than 1',
    taker_confirm_short='strictly less than 1',
    taker_unknown='equality to 1 abstains; UNKNOWN is not zero',
    derived_action_scope='never create or reverse a P0 action; otherwise ABSTAIN',
    abstain_semantics='abstain utility zero and cost zero',
    action_domain=('LONG', 'SHORT', 'ABSTAIN'),
)
THRESHOLD_COMMITMENT_HASH = digest((THRESHOLD_ID, THRESHOLD_SPEC))

ADAPTER_INPUT_DOMAINS = {policy.value: tuple(f.value for f in families(policy)) for policy in PolicyID}
VALUE_ADAPTER_HASH = digest((VALUE_ADAPTER_ID, P0_HASH, EVENT_DIRECTION_RULE_HASH,
                             tuple(ADAPTER_INPUT_DOMAINS[p.value] for p in PolicyID)))
DECISION_RULE_HASH = digest((DECISION_RULE_ID, tuple(RULES), FAMILY, THRESHOLD_COMMITMENT_HASH,
                             tuple(a.value for a in IntentAction)))

STRUCTURES = (None, 'trend', 'range', 'transition', 'unknown')
TAKERS = (None, '0.5', '1', '1.5')


def expected_actions(p0, structure, taker):
    """Independent declarative restatement of the frozen thresholds.

    Deliberately NOT implemented in terms of ``experiment51_derived.actions`` so
    that ``verify()`` can detect any divergence between the committed semantic and
    the executable implementation.
    """
    if p0 not in (IntentAction.LONG, IntentAction.SHORT, IntentAction.ABSTAIN):
        raise ValueError('UNSUPPORTED_ACTION')
    if structure not in STRUCTURES:
        raise ValueError('UNSUPPORTED_REGIME')
    value = None if taker is None else Decimal(str(taker))
    if value is not None and (not value.is_finite() or value < 0):
        raise ValueError('INVALID_TAKER')
    if p0 is IntentAction.ABSTAIN:
        return ((p0, 'P0_ABSTAIN'),) * 4
    regime_pass = structure in ('trend', 'range')
    confirms = ((p0 is IntentAction.LONG and value is not None and value > 1)
                or (p0 is IntentAction.SHORT and value is not None and value < 1))
    regime_reason = 'REGIME_MISSING' if structure is None else 'REGIME_' + structure.upper()
    mechanics_reason = ('MECHANICS_MISSING' if value is None
                        else 'MECHANICS_UNKNOWN' if value == 1 else 'MECHANICS_CONFLICT')
    return ((p0, 'P0_AGREEMENT'),
            (p0, 'REGIME_PASS') if regime_pass else (IntentAction.ABSTAIN, regime_reason),
            (p0, 'MECHANICS_CONFIRM') if confirms else (IntentAction.ABSTAIN, mechanics_reason),
            (p0, 'BOTH_PASS') if (regime_pass and confirms) else (
                IntentAction.ABSTAIN, regime_reason if not regime_pass else mechanics_reason))


def verify():
    """Fail-closed verification of the frozen commitment against live artifacts.

    Raises ValueError on any divergence. Returns the commitment bundle on success.
    Never inspects outcomes.
    """
    document = protocol()                       # raises on prereg mismatch
    if commitment(document) != PREREG:
        raise ValueError('PREREGISTRATION_MISMATCH')
    if len(RULES) != len(PolicyID):
        raise ValueError('RULE_FAMILY_SIZE_MISMATCH')
    if RULES[0] != P0_HASH:
        raise ValueError('P0_RULE_COMMITMENT_MISMATCH')
    if FAMILY != digest(('experiment51-derived-v1', PREREG, RULES, 'CS4 for all three comparisons')):
        raise ValueError('FAMILY_COMMITMENT_MISMATCH')
    declared = document['information_sets']
    for policy in PolicyID:
        if tuple(declared[policy.value]) != ADAPTER_INPUT_DOMAINS[policy.value]:
            raise ValueError('ADAPTER_INFORMATION_SET_MISMATCH:' + policy.value)
    for action in IntentAction:
        if action.value not in THRESHOLD_SPEC['action_domain']:
            raise ValueError('ACTION_DOMAIN_MISMATCH')
    for p0 in (IntentAction.LONG, IntentAction.SHORT, IntentAction.ABSTAIN):
        for structure in STRUCTURES:
            for taker in TAKERS:
                committed = expected_actions(p0, structure, taker)
                implemented = actions(p0, structure, taker)
                if tuple((a.value, r) for a, r in committed) != tuple((a.value, r) for a, r in implemented):
                    raise ValueError('THRESHOLD_IMPLEMENTATION_DIVERGENCE')
    return commitment_bundle()


def commitment_bundle():
    """Deterministic, serializable commitment for prereg binding and audit."""
    return dict(
        schema=SCHEMA,
        prereg=PREREG,
        adapter_id=VALUE_ADAPTER_ID,
        adapter_hash=VALUE_ADAPTER_HASH,
        adapter_input_domains=ADAPTER_INPUT_DOMAINS,
        rule_id=DECISION_RULE_ID,
        rule_hash=DECISION_RULE_HASH,
        rule_family=FAMILY,
        rules=tuple(RULES),
        p0_hash=P0_HASH,
        event_direction_rule_hash=EVENT_DIRECTION_RULE_HASH,
        threshold_id=THRESHOLD_ID,
        threshold_commitment_hash=THRESHOLD_COMMITMENT_HASH,
        abstain_action=IntentAction.ABSTAIN.value,
        policy_blind=True,
        probability_semantics=False,
        outcome_dependency=False,
    )


def bundle_commitment():
    """Digest of the whole bundle: one reproducible identifier for the binding."""
    return digest(commitment_bundle())
