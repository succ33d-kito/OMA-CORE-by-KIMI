"""Authenticated P0 agreement, no outcome loader and no execution authority."""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from decimal import Decimal
from .event_direction_v1 import EventDirectionAuthority, Direction, RULE_HASH
from .decision_rule import IntentAction
from .nuisance_pilot_contracts import InputType, InputStatus, digest
from .policy_kernel import PolicyKernel
from .common_support import CommonSupportRegistry
from .prospective_receipts import observation_snapshot, snapshot_causally_available
from .price_role_attestation import verified_price_role_attestation
from .experimental_manifest import PopulationScope, PopulationManifestBuilder
from .official_manifest_binding import OfficialManifestStore

P0_HASH=digest(('experiment51-p0-agreement-v1',RULE_HASH,'equal LONG/SHORT only;otherwise ABSTAIN',
                'source-slot S=D-1H;raw available<=S+5m;attestation<=D;horizon4H'))


def _agreement(event,price):
    return IntentAction.LONG if event is Direction.LONG and price is Direction.LONG else (
        IntentAction.SHORT if event is Direction.SHORT and price is Direction.SHORT else IntentAction.ABSTAIN)


def prepare(authority,store,receipt_id,*,price_ledger=None):
    if type(authority) is not EventDirectionAuthority:
        raise TypeError('authenticated direction authority required')
    record=authority.verify(store,receipt_id)
    matches=[o for o in store.population() if o.event_id==record.event_id]
    if len(matches)!=1:
        raise ValueError('closed official sampling opportunity required')
    op=matches[0]; D=op.decision_at
    if op.dataset_role is not record.dataset_role or D!=record.decision_eligible_at or op.instrument!='BTCUSDT':
        raise ValueError('event opportunity scope mismatch')
    source_slot=D-timedelta(hours=1)
    price=None; att=None
    if price_ledger is not None:
        known,_=observation_snapshot(price_ledger,read_only=True)
        candidates=[r for r in known.values() if r['feature']=='Price/OHLCV' and r['instrument']=='BTCUSDT'
                    and datetime.fromisoformat(r['event_time'])==source_slot]
        if len(candidates)>1:
            raise ValueError('conflicting Price input')
        if candidates:
            price=candidates[0]
            att=verified_price_role_attestation(known,price,op.dataset_role.value,D)
            if (att is None or not snapshot_causally_available(known,price['id'],D)
                    or datetime.fromisoformat(price['available_at'])>source_slot+timedelta(minutes=5)):
                raise ValueError('Price role/availability invalid')
    price_direction=Direction.UNKNOWN
    if price is not None:
        opened,closed=Decimal(str(price['payload']['open'])),Decimal(str(price['payload']['close']))
        price_direction=Direction.LONG if closed>opened else Direction.SHORT if closed<opened else Direction.UNKNOWN
    inputs=[]
    for old in op.inputs:
        if old.input_type is InputType.EVENT:
            old=replace(old,receipt_ids=(record.receipt_id,record.record_id),value_hash=record.record_id,
                        provenance_hash=digest((record.provenance_hash,record.authority_id)),
                        available_at=record.available_at,validator_version=RULE_HASH)
        elif old.input_type is InputType.PRICE and price is not None:
            old=replace(old,status=InputStatus.VALID,source=price['source'],
                        source_event_time=datetime.fromisoformat(price['event_time']),
                        received_at=datetime.fromisoformat(price['received_at']),
                        available_at=max(datetime.fromisoformat(price['available_at']),datetime.fromisoformat(att['available_at'])),
                        receipt_ids=(price['id'],att['id']),value_hash=digest((price['payload_hash'],att['id'])),
                        provenance_hash=digest((price['provenance'],att['provenance'])),validator_version=P0_HASH,reason_codes=())
        inputs.append(old)
    bound=replace(op,inputs=tuple(inputs),population_rule_hash=digest((op.population_rule_hash,RULE_HASH,P0_HASH,authority.authority_id)))
    return bound,record,price_direction


@dataclass(frozen=True,slots=True)
class P0DirectionReceipt:
    opportunity_id: str
    event_record_id: str
    policy_decision_id: str
    comparison_id: str
    dataset_role: str
    decision_at: str
    action: IntentAction
    reason: str
    recorded_at: str
    rule_hash: str = P0_HASH

    @property
    def record_id(self):
        return digest(tuple(getattr(self,k).value if k=='action' else getattr(self,k) for k in self.__dataclass_fields__))


def decide_p0(authority,store,receipt_id,controls,*,price_ledger=None):
    op,event,price_direction=prepare(authority,store,receipt_id,price_ledger=price_ledger)
    if controls.outcome_horizon_seconds!=14400 or controls.policy_contract_hash!=P0_HASH:
        raise ValueError('explicit frozen P0 contract and 4H controls required')
    decision=PolicyKernel().form(op,controls)[0]
    action=_agreement(event.direction,price_direction) if decision.information_set.causal_eligible else IntentAction.ABSTAIN
    reason='AGREEMENT' if action is not IntentAction.ABSTAIN else (
        'MISSING_PRICE' if not decision.information_set.causal_eligible else 'UNKNOWN_OR_CONFLICT')
    body=dict(opportunity_id=op.opportunity_id,event_record_id=event.record_id,policy_decision_id=decision.decision_id,
              comparison_id=decision.comparison_id,dataset_role=op.dataset_role.value,decision_at=op.decision_at.isoformat(),
              action=action.value,reason=reason,rule_hash=P0_HASH)
    journal=authority._journal
    existing=[r for r in journal._rows() if r['kind']=='p0' and r['data']['opportunity_id']==op.opportunity_id]
    if existing:
        if len(existing)!=1 or existing[0]['data']!=body:
            raise ValueError('immutable P0 conflict')
        saved=existing[0]
    else:
        def validate(rows,at):
            if not op.decision_at<=at<op.decision_at+timedelta(hours=4):
                raise ValueError('P0 must be formed prospectively before horizon completion')
            if any(r['kind']=='p0' and r['data']['opportunity_id']==op.opportunity_id for r in rows):
                raise ValueError('concurrent P0 conflict')
        journal._append('p0',body,validate)
        saved=[r for r in journal._rows() if r['kind']=='p0' and r['data']['opportunity_id']==op.opportunity_id][0]
    return P0DirectionReceipt(**{**saved['data'],'action':IntentAction(saved['data']['action']),'recorded_at':saved['at']})


def bind_population(authority,store,controls,*,price_ledger=None,directory):
    """Freeze all closed direction-qualified opportunities, INCLUDING UNKNOWN.

    Separate deployment operation; this task exercises only synthetic journals.
    Existing manifest/common-support custody mechanisms remain authoritative.
    """
    if controls.outcome_horizon_seconds!=14400 or controls.policy_contract_hash!=P0_HASH:
        raise ValueError('frozen P0 controls required')
    all_ops=store.population()
    if not all_ops:
        raise ValueError('no closed Event population')
    records=authority._journal._rows()
    by_event={r['data']['event_id']:r['data']['receipt_id'] for r in records if r['kind']=='direction'}
    prepared=[]
    for op in all_ops:
        if op.event_id not in by_event:
            raise ValueError('unattested event: population not silently filtered')
        prepared.append(prepare(authority,store,by_event[op.event_id],price_ledger=price_ledger)[0])
    first=prepared[0]
    cutoff=max(o.decision_at for o in prepared)
    scope=PopulationScope(first.protocol_id,first.protocol_hash,first.run_id,first.dataset_role,first.population_rule_hash,cutoff)
    builder=PopulationManifestBuilder(scope)
    for op in prepared:
        decisions=PolicyKernel().form(op,controls)
        support=CommonSupportRegistry().register(op,controls,decisions)
        builder.add(op,controls,decisions,support)
    # Same internal operational clock as existing journal; never caller backdating.
    from .real_event_receipt import _now
    now=_now()
    if not cutoff<=now<min(o.decision_at for o in prepared)+timedelta(hours=4):
        raise ValueError('population must freeze before earliest primary horizon completes')
    manifest=builder.freeze(now)
    return manifest,OfficialManifestStore(directory).bind(scope,manifest,now)
