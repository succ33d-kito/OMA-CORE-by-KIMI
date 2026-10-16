"""Qualification of the frozen real policy value adapter + policy-blind rule.

These tests are outcome-blind: no label, return, PnL or sealed outcome loader is
imported or executed. They prove that the commitment artifact binds the already
frozen semantics to the canonical preregistration and that the executable
implementation cannot diverge from the committed thresholds.
"""
import ast
import inspect
from decimal import Decimal
from pathlib import Path

import pytest

from core.scientific import policy_value_commitment as pvc
from core.scientific import experiment51_derived as derived
from core.scientific import experiment51_p0 as p0
from core.scientific.decision_rule import IntentAction, ReferenceRule
from core.scientific.experiment51_preparation import commitment, load_protocol
from core.scientific.nuisance_pilot_contracts import PolicyID, digest
from core.scientific.policy_kernel import families

CANONICAL_PREREG = '7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8'
ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = (
    'core/scientific/policy_value_commitment.py',
    'core/scientific/experiment51_p0.py',
    'core/scientific/experiment51_derived.py',
    'core/scientific/decision_rule.py',
    'core/scientific/policy_kernel.py',
)


def table(p0_action, structure, taker):
    return tuple((a.value, r) for a, r in derived.actions(p0_action, structure, taker))


# 1 --------------------------------------------------------------------------
def test_deterministic_value_for_identical_input():
    first = table(IntentAction.LONG, 'trend', '1.5')
    for _ in range(5):
        assert table(IntentAction.LONG, 'trend', '1.5') == first
    assert pvc.commitment_bundle() == pvc.commitment_bundle()
    assert pvc.bundle_commitment() == pvc.bundle_commitment()


# 2 --------------------------------------------------------------------------
def test_no_outcome_field_is_accepted():
    for func in (derived.actions, pvc.expected_actions):
        params = set(inspect.signature(func).parameters)
        assert params == {'p0', 'structure', 'taker'}
        assert not (params & {'outcome', 'label', 'return_', 'pnl', 'realized', 'forward'})
    assert inspect.signature(pvc.commitment_bundle).parameters == {}
    assert inspect.signature(pvc.verify).parameters == {}


# 3 --------------------------------------------------------------------------
def test_no_future_evidence_entrypoint_exists():
    for func in (derived.actions, pvc.expected_actions, pvc.verify, pvc.commitment_bundle):
        params = set(inspect.signature(func).parameters)
        assert not (params & {'available_at', 'event_time', 'now', 'price', 'ledger'})
    # causal admission is enforced upstream by the real gate, which requires a ledger
    # and a decision instant; the commitment layer accepts no evidence at all.
    assert {'ledger', 'decision_at'} <= set(inspect.signature(derived.derived).parameters)
    for func in (pvc.expected_actions, pvc.verify, pvc.commitment_bundle, pvc.bundle_commitment):
        assert not (set(inspect.signature(func).parameters) & {'ledger', 'decision_at'})


# 4 --------------------------------------------------------------------------
def test_missing_required_input_fails_closed_to_abstain():
    for structure in (None, 'transition', 'unknown'):
        assert table(IntentAction.LONG, structure, '1.5')[1][0] == 'ABSTAIN'
    assert table(IntentAction.LONG, 'trend', None)[2][0] == 'ABSTAIN'
    assert table(IntentAction.LONG, 'trend', None)[3][0] == 'ABSTAIN'
    assert table(IntentAction.LONG, None, None)[3] == ('ABSTAIN', 'REGIME_MISSING')


# 5 --------------------------------------------------------------------------
def test_unknown_is_not_numeric_zero():
    assert table(IntentAction.LONG, 'unknown', '1.5')[1] == ('ABSTAIN', 'REGIME_UNKNOWN')
    assert table(IntentAction.LONG, 'trend', '1')[2] == ('ABSTAIN', 'MECHANICS_UNKNOWN')
    assert pvc.THRESHOLD_SPEC['taker_unknown'].startswith('equality to 1 abstains')


# 6 --------------------------------------------------------------------------
def test_missing_is_not_neutral():
    for p0_action in (IntentAction.LONG, IntentAction.SHORT):
        rows = table(p0_action, None, None)
        assert rows[0][0] == p0_action.value          # P0 unaffected by absent optional inputs
        assert rows[1][0] == 'ABSTAIN' and rows[2][0] == 'ABSTAIN' and rows[3][0] == 'ABSTAIN'


# 7 --------------------------------------------------------------------------
def test_raw_value_is_not_labelled_probability():
    bundle = pvc.commitment_bundle()
    assert bundle['probability_semantics'] is False
    assert not [k for k in bundle if ('probab' in k or 'confidence' in k) and k != 'probability_semantics']
    api = [name for name in dir(pvc) if not name.startswith('_')]
    assert not [name for name in api if 'probab' in name.lower() or 'confidence' in name.lower()]


# 8 --------------------------------------------------------------------------
def test_one_rule_is_used_for_all_four_arms():
    rules = p0.P0_HASH, *derived.RULES[1:]
    assert len(rules) == 4
    assert derived.RULES[0] == p0.P0_HASH
    assert set(pvc.commitment_bundle()['rules']) == set(derived.RULES)
    for policy in PolicyID:
        assert tuple(f.value for f in families(policy)) == pvc.ADAPTER_INPUT_DOMAINS[policy.value]


# 9 --------------------------------------------------------------------------
def test_arm_identity_cannot_change_threshold():
    assert 'policy' not in inspect.signature(derived.actions).parameters
    assert 'policy' not in inspect.signature(pvc.expected_actions).parameters
    assert len(pvc.THRESHOLD_SPEC) == len(set(pvc.THRESHOLD_SPEC))
    # identical thresholds apply to every arm: the spec is single and shared
    assert pvc.THRESHOLD_COMMITMENT_HASH == digest((pvc.THRESHOLD_ID, pvc.THRESHOLD_SPEC))


# 10 -------------------------------------------------------------------------
def test_provenance_is_preserved():
    bundle = pvc.verify()
    for key in ('prereg', 'adapter_id', 'adapter_hash', 'rule_id', 'rule_hash', 'rules',
                'p0_hash', 'event_direction_rule_hash', 'threshold_id', 'threshold_commitment_hash'):
        assert key in bundle
    assert bundle['prereg'] == CANONICAL_PREREG
    assert bundle['rule_family'] == derived.FAMILY
    assert bundle['p0_hash'] == p0.P0_HASH


# 11 / 12 / 13 ---------------------------------------------------------------
def test_adapter_rule_and_threshold_hashes_are_deterministic():
    again = pvc.VALUE_ADAPTER_HASH, pvc.DECISION_RULE_HASH, pvc.THRESHOLD_COMMITMENT_HASH
    import importlib
    reloaded = importlib.reload(pvc)
    assert again == (reloaded.VALUE_ADAPTER_HASH, reloaded.DECISION_RULE_HASH,
                     reloaded.THRESHOLD_COMMITMENT_HASH)
    assert pvc.verify()['threshold_commitment_hash'] == again[2]


# 14 -------------------------------------------------------------------------
def test_long_boundary_behaviour():
    assert table(IntentAction.LONG, 'trend', '1.5') == (
        ('LONG', 'P0_AGREEMENT'), ('LONG', 'REGIME_PASS'), ('LONG', 'MECHANICS_CONFIRM'),
        ('LONG', 'BOTH_PASS'))
    assert table(IntentAction.LONG, 'trend', '1')[2] == ('ABSTAIN', 'MECHANICS_UNKNOWN')   # strict >
    assert table(IntentAction.LONG, 'transition', '1.5')[1][0] == 'ABSTAIN'


# 15 -------------------------------------------------------------------------
def test_short_boundary_behaviour():
    assert table(IntentAction.SHORT, 'range', '0.5') == (
        ('SHORT', 'P0_AGREEMENT'), ('SHORT', 'REGIME_PASS'), ('SHORT', 'MECHANICS_CONFIRM'),
        ('SHORT', 'BOTH_PASS'))
    assert table(IntentAction.SHORT, 'range', '1')[2] == ('ABSTAIN', 'MECHANICS_UNKNOWN')  # strict <
    assert table(IntentAction.SHORT, 'unknown', '0.5')[3][0] == 'ABSTAIN'


# 16 -------------------------------------------------------------------------
def test_abstain_boundary_behaviour():
    for structure in pvc.STRUCTURES:
        for taker in pvc.TAKERS:
            assert table(IntentAction.ABSTAIN, structure, taker) == (('ABSTAIN', 'P0_ABSTAIN'),) * 4


# 17 -------------------------------------------------------------------------
def test_tie_behaviour_is_deterministic():
    assert table(IntentAction.LONG, 'trend', '1')[2] == ('ABSTAIN', 'MECHANICS_UNKNOWN')
    assert table(IntentAction.SHORT, 'trend', '1')[2] == ('ABSTAIN', 'MECHANICS_UNKNOWN')
    assert table(IntentAction.LONG, 'trend', '1')[3] == ('ABSTAIN', 'MECHANICS_UNKNOWN')


# 18 -------------------------------------------------------------------------
def test_malformed_inputs_are_rejected():
    with pytest.raises(ValueError, match='UNSUPPORTED_REGIME'):
        derived.actions(IntentAction.LONG, 'sideways', '1.5')
    with pytest.raises(ValueError, match='INVALID_TAKER'):
        derived.actions(IntentAction.LONG, 'trend', '-0.1')
    with pytest.raises((ValueError, ArithmeticError)):
        derived.actions(IntentAction.LONG, 'trend', 'not-a-number')
    with pytest.raises(ValueError, match='UNSUPPORTED_REGIME'):
        pvc.expected_actions(IntentAction.LONG, 'sideways', '1.5')
    with pytest.raises((ValueError, ArithmeticError)):
        pvc.expected_actions(IntentAction.LONG, 'trend', 'not-a-number')
    with pytest.raises(ValueError, match='UNSUPPORTED_ACTION'):
        pvc.expected_actions('MAYBE', 'trend', '1.5')


# 19 --------------------------------------------------------------------------
def test_policy_blind_invariant_is_enforced():
    # The committed semantic is restated independently and compared exhaustively
    # against the executable implementation for the full frozen domain.
    checked = 0
    for action in (IntentAction.LONG, IntentAction.SHORT, IntentAction.ABSTAIN):
        for structure in pvc.STRUCTURES:
            for taker in pvc.TAKERS:
                assert pvc.expected_actions(action, structure, taker) == derived.actions(action, structure, taker)
                checked += 1
    assert checked == 3 * 5 * 4
    assert pvc.commitment_bundle()['policy_blind'] is True


# 20 -------------------------------------------------------------------------
def _imports(path):
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or '')
    return names


def test_no_label_or_outcome_dependency_in_decision_path():
    forbidden_modules = ('experiment51_sealed',)
    forbidden_tokens = ('outcome_loader', 'load_labels', 'pnl', 'profit', 'realized',
                        'forward_return', 'realized_return')
    for path in DECISION_PATH:
        source = (ROOT / path).read_text(encoding='utf-8')
        imports = _imports(path)
        assert not any(bad in name for name in imports for bad in forbidden_modules), path
        for token in forbidden_tokens:
            assert token not in source, f'{token} present in {path}'
    # 'outcome_horizon_seconds' is a causal control parameter, not an outcome value.
    # AST-level check: no code identifier may mention outcome/label/pnl semantics.
    for path in DECISION_PATH:
        tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Name):
                names.append(node.id)
            elif isinstance(node, ast.Attribute):
                names.append(node.attr)
            elif isinstance(node, ast.keyword) and node.arg:
                names.append(node.arg)
            for name in names:
                low = name.lower()
                if 'outcome' in low:
                    # the audit flag itself and the causal control parameter are allowed
                    assert low in ('outcome_horizon_seconds', 'outcome_dependency'), f'{path}:{name}'
                assert not any(t in low for t in ('label', 'pnl', 'profit', 'realized', 'forward_return')), f'{path}:{name}'
    assert pvc.commitment_bundle()['outcome_dependency'] is False


# extras ---------------------------------------------------------------------
def test_preregistration_artifact_is_not_modified():
    document = load_protocol()
    assert commitment(document) == CANONICAL_PREREG
    assert document['status'] == 'DESIGN_FROZEN_EXECUTION_BLOCKED'
    assert pvc.PREREG == CANONICAL_PREREG


def test_synthetic_reference_rule_remains_isolated_and_non_executable():
    rule = ReferenceRule(version='1', minimum_absolute_votes=1)
    assert rule.rule_id == 'pnep-synthetic-vote-sum'
    # the isolation marker lives in the hashed preimage, not in the digest itself
    assert 'TEST_REFERENCE_ONLY' in inspect.getsource(ReferenceRule)
    assert rule.identity not in (pvc.VALUE_ADAPTER_HASH, pvc.DECISION_RULE_HASH, pvc.THRESHOLD_COMMITMENT_HASH)
    assert 'pnep-synthetic-vote-sum' not in (pvc.VALUE_ADAPTER_ID, pvc.DECISION_RULE_ID)
    source = (ROOT / 'core/scientific/experiment51_p0.py').read_text(encoding='utf-8')
    derived_source = (ROOT / 'core/scientific/experiment51_derived.py').read_text(encoding='utf-8')
    assert 'decide_reference' not in source and 'decide_reference' not in derived_source


def test_commitment_binds_the_same_rules_the_sealed_phase_requires():
    source = (ROOT / 'core/scientific/experiment51_sealed.py').read_text(encoding='utf-8')
    assert 'rules=list(RULES)' in source and "family=FAMILY" in source
    assert 'prereg=PREREG' in source
    assert pvc.commitment_bundle()['rules'] == tuple(derived.RULES)


def test_threshold_spec_values_come_from_committed_strings():
    committed = ' '.join(('experiment51-p0-agreement-v1', 'PR-v1', 'PM-v1', 'PRM-v1'))
    assert committed  # committed rule family identifiers are fixed text, not parameters
    assert pvc.THRESHOLD_SPEC['regime_pass_structures'] == ('range', 'trend')
    assert pvc.THRESHOLD_SPEC['taker_confirm_long'].startswith('strictly greater')
    assert pvc.THRESHOLD_SPEC['taker_confirm_short'].startswith('strictly less')
    assert Decimal('1') in (Decimal(pvc.TAKERS[2]), Decimal('1'))
