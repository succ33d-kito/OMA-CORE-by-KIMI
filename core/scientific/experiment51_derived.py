"""Read-only authenticated derived policy projection; no outcome or capture API."""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from decimal import Decimal
from .experiment51_p0 import prepare, P0_HASH, _agreement
from .event_direction_v1 import Direction
from .decision_rule import IntentAction
from .nuisance_pilot_contracts import InputType, InputStatus, digest
from .policy_kernel import PolicyKernel
from .common_support import CommonSupportRegistry
from .prospective_receipts import observation_snapshot
from .causal_regime import validate_causal_regime
from .causal_mechanics import validate_causal_mechanics
from .metrics_snapshot_gate import metrics_snapshot_available
from .metrics_observation_admission import EXPECTED_FEATURES
from .experiment51_preparation import commitment, load_protocol

PREREG = '7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8'
RULES = (P0_HASH, digest(('PR-v1',P0_HASH,'structure trend/range pass;transition/unknown veto')),
         digest(('PM-v1',P0_HASH,'authenticated atomic taker >1 long;<1 short;=1 unknown')),
         digest(('PRM-v1',P0_HASH,'Regime veto AND Taker confirms;never create or reverse')))
FAMILY = digest(('experiment51-derived-v1', PREREG, RULES, 'CS4 for all three comparisons'))


def protocol():
    value = load_protocol()
    if commitment(value) != PREREG:
        raise ValueError('PREREGISTRATION_MISMATCH')
    return value


def actions(p0, structure, taker):
    """Pure frozen semantics, NOT a public evidence-authentication boundary."""
    if structure not in (None, 'trend', 'range', 'transition', 'unknown'):
        raise ValueError('UNSUPPORTED_REGIME')
    regime_pass = structure in ('trend','range')
    if taker is not None:
        taker = Decimal(str(taker))
        if not taker.is_finite() or taker < 0:
            raise ValueError('INVALID_TAKER')
    confirms = ((p0 is IntentAction.LONG and taker is not None and taker > 1)
                or (p0 is IntentAction.SHORT and taker is not None and taker < 1))
    if p0 is IntentAction.ABSTAIN:
        return ((p0,'P0_ABSTAIN'),)*4
    regime_reason = 'REGIME_MISSING' if structure is None else 'REGIME_'+structure.upper()
    mechanics_reason = 'MECHANICS_MISSING' if taker is None else 'MECHANICS_UNKNOWN' if taker == 1 else 'MECHANICS_CONFLICT'
    return ((p0,'P0_AGREEMENT'),
            (p0,'REGIME_PASS') if regime_pass else (IntentAction.ABSTAIN,regime_reason),
            (p0,'MECHANICS_CONFIRM') if confirms else (IntentAction.ABSTAIN,mechanics_reason),
            (p0,'BOTH_PASS') if regime_pass and confirms else (IntentAction.ABSTAIN,regime_reason if not regime_pass else mechanics_reason))


@dataclass(frozen=True, slots=True)
class DerivedView:
    regime_id: str | None
    mechanics_id: str | None
    structure: str | None
    taker: str | None
    dependencies: tuple[str, ...]
    commitment: str


def derived(ledger, *, role, decision_at, regime_id=None, mechanics_id=None):
    """Caller selects IDs, never values; all supplied IDs must authenticate."""
    protocol()
    from .regime_observation import _utc
    D = _utc(decision_at); S = D-timedelta(hours=1); raw_cut = S+timedelta(minutes=5)
    known,_ = observation_snapshot(ledger, read_only=True)
    structure = taker = None; dependencies = []
    if regime_id is not None:
        if regime_id not in known: raise ValueError('MISSING_REGIME_ID')
        row = validate_causal_regime(known,known[regime_id],dataset_role=role,cutoff=D)
        cert = row['provenance']['certificate']
        if _utc(cert['last_event_time']) != S or _utc(cert['cutoff']) > D:
            raise ValueError('REGIME_SLOT_MISMATCH')
        for identity in cert['receipt_ids']:
            raw = known[identity]
            if _utc(raw['available_at']) > raw_cut:
                raise ValueError('PRICE_RAW_CUTOFF_FAILURE')
        structure = row['payload']['regime']['structure']
        if structure not in ('trend','range','transition','unknown'):
            raise ValueError('UNSUPPORTED_REGIME')
        dependencies.extend(row['dependencies'])
    if mechanics_id is not None:
        if mechanics_id not in known: raise ValueError('MISSING_MECHANICS_ID')
        row = validate_causal_mechanics(ledger,known[mechanics_id],dataset_role=role,cutoff=D)
        raw_values = row['payload']['raw_values']
        if row['payload']['regime'] is not None or 'FundingRate/Published' in raw_values:
            raise ValueError('MECHANICS_INFORMATION_SET_CONTAMINATION')
        metrics = {key:value for key,value in raw_values.items() if key.startswith('MarketMetrics/')}
        if set(metrics) != EXPECTED_FEATURES:
            raise ValueError('INVALID_BUNDLE')
        bundle_ids = set()
        for item in metrics.values():
            raw = known[item['source_id']]
            if (raw['provenance']['dataset_role'] != role or _utc(raw['event_time']) != S
                    or _utc(raw['available_at']) > raw_cut
                    or not metrics_snapshot_available(known,raw['id'],raw_cut)):
                raise ValueError('INVALID_BUNDLE_ROLE_SLOT_OR_CAUSALITY')
            bundle_ids.add(raw['provenance']['bundle_id']);dependencies.append(raw['id'])
        if len(bundle_ids) != 1: raise ValueError('CONFLICTING_BUNDLE')
        taker = str(metrics['MarketMetrics/TakerBuySellRatio']['value'])
        # Full descriptive state may contain extra dimensions; none enter policy semantics.
    body = (role,D.isoformat(),regime_id,mechanics_id,structure,taker,tuple(sorted(set(dependencies))))
    return DerivedView(regime_id,mechanics_id,structure,taker,body[-1],digest(body))


def reconstruct(authority,store,receipt_id,controls,*,ledger,regime_id=None,mechanics_id=None):
    protocol()
    if controls.policy_contract_hash != P0_HASH or controls.outcome_horizon_seconds != 14400:
        raise ValueError('CONTROL_MISMATCH')
    op,event,price = prepare(authority,store,receipt_id,price_ledger=ledger)
    view = derived(ledger,role=op.dataset_role.value,decision_at=op.decision_at,
                   regime_id=regime_id,mechanics_id=mechanics_id)
    known,_ = observation_snapshot(ledger,read_only=True)
    inputs = []
    for old in op.inputs:
        identity = regime_id if old.input_type is InputType.REGIME else mechanics_id if old.input_type is InputType.MECHANICS else None
        if identity is not None:
            row = known[identity]
            # Policy assessment references an authenticated persisted projection receipt.
            # Full derived dependency verification happens above, before kernel formation.
            old = replace(old,status=InputStatus.VALID,source=row['source'],
                source_event_time=datetime.fromisoformat(row['event_time']),
                received_at=datetime.fromisoformat(row['received_at']),available_at=datetime.fromisoformat(row['available_at']),
                receipt_ids=(identity,),value_hash=digest((identity,row['payload_hash'])),
                provenance_hash=digest(row['provenance']),validator_version=FAMILY,reason_codes=())
        inputs.append(old)
    op = replace(op,inputs=tuple(inputs),population_rule_hash=digest((op.population_rule_hash,FAMILY)))
    decisions = PolicyKernel().form(op,controls)
    support = CommonSupportRegistry().register(op,controls,decisions)
    base = _agreement(event.direction,price) if decisions[0].information_set.causal_eligible else IntentAction.ABSTAIN
    chosen = actions(base,view.structure,view.taker)
    bodies = []
    for index,decision in enumerate(decisions):
        action,reason = chosen[index]
        if not decision.information_set.causal_eligible:
            action = IntentAction.ABSTAIN
            reason = 'INPUT_INELIGIBLE'
        body = dict(schema='experiment51-policy-v1', policy=decision.information_set.policy.value,
            comparison_family=FAMILY,opportunity_id=op.opportunity_id,role=op.dataset_role.value,
            decision_at=op.decision_at.isoformat(),p0_record_id=digest((event.record_id,decisions[0].decision_id,base.value)),
            regime_id=regime_id if index in (1,3) else None,mechanics_id=mechanics_id if index in (2,3) else None,
            action=action.value,reason=reason,rule_hash=RULES[index],kernel_id=decision.decision_id)
        bodies.append(body)
    return op, decisions, support, tuple(bodies), view
