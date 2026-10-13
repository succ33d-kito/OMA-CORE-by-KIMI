"""Prospective owner-authorized BTC taxonomy; explicit curator assertions, not NLP.

Uses existing Event journal machinery in a SEPARATE journal. Local custody and
truth of the curator's semantic assertions remain trust boundaries.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import re
from pathlib import Path
from . import real_event_receipt as events
from .nuisance_pilot_contracts import DatasetRole, closed, digest


class EventClass(Enum):
    BTC_ACCESS_EXPANSION_CONFIRMED = 'BTC_ACCESS_EXPANSION_CONFIRMED'
    BTC_ACCESS_RESTRICTION_CONFIRMED = 'BTC_ACCESS_RESTRICTION_CONFIRMED'
    BTC_NET_BUY_COMMITMENT_CONFIRMED = 'BTC_NET_BUY_COMMITMENT_CONFIRMED'
    BTC_NET_SELL_COMMITMENT_CONFIRMED = 'BTC_NET_SELL_COMMITMENT_CONFIRMED'
    UNKNOWN = 'UNKNOWN'


class Direction(Enum):
    LONG='LONG'
    SHORT='SHORT'
    NEUTRAL='NEUTRAL'
    UNKNOWN='UNKNOWN'


RULE = ('btc-event-direction-v1', tuple(c.value for c in EventClass),
        'EXPANSION/BUY=LONG;RESTRICTION/SELL=SHORT;OTHER=UNKNOWN',
        'official-confirmed-direct-BTC;buy/sell-identifiable-actor-uncompleted',
        'explicit-curator-exact-quote;no-sentiment;no-neutral-authority;prospective-only')
RULE_HASH = digest(RULE)


@dataclass(frozen=True, slots=True)
class ClassAssertion:
    event_class: EventClass
    curator: str
    quote: str
    actor: str
    official_confirmed: bool
    direct_btc_action: bool
    unambiguous: bool
    commitment_not_fully_completed: bool

    def __post_init__(self):
        closed(self.event_class, EventClass)
        if any(type(v) is not str for v in (self.curator,self.quote,self.actor)) or not self.curator.strip():
            raise ValueError('identified curator and literal evidence required')
        if any(type(v) is not bool for v in (self.official_confirmed,self.direct_btc_action,self.unambiguous,self.commitment_not_fully_completed)):
            raise TypeError('explicit semantic assertions required')

    def body(self):
        return {**asdict(self),'event_class':self.event_class.value}


def _classify(receipt, assertion):
    if assertion.event_class is EventClass.UNKNOWN:
        return Direction.UNKNOWN
    if (not assertion.quote or assertion.quote not in receipt.content
            or not re.search(r'\b(?:BTC|Bitcoin)\b',assertion.quote,re.I)):
        raise ValueError('exact explicit BTC quote required')
    if not (assertion.official_confirmed and assertion.direct_btc_action and assertion.unambiguous):
        return Direction.UNKNOWN
    if assertion.event_class in (EventClass.BTC_NET_BUY_COMMITMENT_CONFIRMED,EventClass.BTC_NET_SELL_COMMITMENT_CONFIRMED):
        if not assertion.actor.strip() or assertion.actor not in assertion.quote or not assertion.commitment_not_fully_completed:
            return Direction.UNKNOWN
    return Direction.LONG if assertion.event_class in (EventClass.BTC_ACCESS_EXPANSION_CONFIRMED,EventClass.BTC_NET_BUY_COMMITMENT_CONFIRMED) else Direction.SHORT


@dataclass(frozen=True, slots=True)
class EventDirectionRecordV1:
    event_id: str
    receipt_id: str
    dataset_role: DatasetRole
    event_class: EventClass
    direction: Direction
    direction_basis: str
    provenance_hash: str
    recorded_at: datetime
    available_at: datetime
    decision_eligible_at: datetime
    authority_id: str
    rule_hash: str = RULE_HASH
    instrument: str = 'BTCUSDT'
    schema: str = 'event-direction-record-v1'

    @property
    def record_id(self):
        return digest(tuple((k,v.value if isinstance(v,Enum) else v.isoformat() if isinstance(v,datetime) else v) for k,v in asdict(self).items()))


def _context(store, receipt_id, role):
    if type(store) is not events.RealEventStore:
        raise TypeError('real Event journal required')
    receipt=store.receipt(receipt_id)
    if receipt.role is not role or receipt.kind is not events.ContentKind.FULL_DOCUMENT or receipt.available_at is None:
        raise ValueError('receipt role/full-content/availability invalid')
    replay=store._replay(store._rows())
    candidates=[c for c in replay.candidates() if c.envelope.receipt_id==receipt_id]
    if len(candidates)!=1 or candidates[0].reasons:
        raise ValueError('unique causally admitted event required')
    c=candidates[0]
    reservation=next((x for x in replay.reservations() if x.reservation_id==c.reservation_id),None)
    if reservation is None or reservation.event_id!=c.envelope.event_id or not replay.sampling_eligible(reservation.reservation_id,reservation.decision_at):
        raise ValueError('event is not first eligible shock reservation')
    return receipt,c,reservation


class EventDirectionAuthority:
    """First attestation is final; interrupted publication is never repaired."""
    def __init__(self,path):
        if not Path(path).is_file():
            raise ValueError('explicit prospective activation required')
        self._journal=events.RealEventStore(path)
        rows=self._journal._rows()
        if not rows or rows[0]['kind']!='direction_authority' or rows[0]['data'].get('rule_hash')!=RULE_HASH:
            raise ValueError('invalid direction authority')
        self._config=rows[0]
        DatasetRole(rows[0]['data']['role'])
        self.authority_id=digest(rows[0])

    @property
    def role(self):
        return DatasetRole(self._config['data']['role'])

    @classmethod
    def activate(cls,path,*,role):
        closed(role,DatasetRole)
        # Exclusive creation prevents accidentally using or initializing any existing journal.
        with Path(path).open('xb'):
            pass
        journal=events.RealEventStore(path)
        journal._append('direction_authority',dict(rule_hash=RULE_HASH,role=role.value),lambda rows,at:None)
        return cls(path)

    def attest(self,store,receipt_id,assertion):
        if type(assertion) is not ClassAssertion:
            raise TypeError('closed explicit ClassAssertion required')
        receipt,c,reservation=_context(store,receipt_id,self.role)
        if not datetime.fromisoformat(self._config['at']) < receipt.received_at <= receipt.available_at:
            raise ValueError('historical receipt cannot receive prospective direction')
        _classify(receipt,assertion)
        data=dict(receipt_id=receipt_id,event_id=c.envelope.event_id,assertion=assertion.body(),
                  provenance_hash=receipt.provenance_hash,decision_at=reservation.decision_at.isoformat())
        existing=[r for r in self._journal._rows() if r['kind']=='direction' and r['data']['event_id']==c.envelope.event_id]
        if existing:
            if len(existing)!=1 or existing[0]['data']!=data:
                raise ValueError('immutable direction conflict')
            return self.verify(store,receipt_id)
        def validate(rows,at):
            if any(r['kind']=='direction' and r['data']['event_id']==c.envelope.event_id for r in rows):
                raise ValueError('concurrent attestation conflict')
            if not receipt.available_at <= c.envelope.available_at <= at < reservation.decision_at:
                raise ValueError('attestation must precede reserved decision')
        self._journal._append('direction',data,validate)
        def ready_check(rows,at):
            if at >= reservation.decision_at:
                raise ValueError('direction publication is late')
        self._journal._append('direction_ready',dict(receipt_id=receipt_id),ready_check)
        return self.verify(store,receipt_id)

    def verify(self,store,receipt_id):
        receipt,c,reservation=_context(store,receipt_id,self.role)
        rows=self._journal._rows()
        records=[r for r in rows if r['kind']=='direction' and r['data']['receipt_id']==receipt_id]
        ready=[r for r in rows if r['kind']=='direction_ready' and r['data']['receipt_id']==receipt_id]
        if len(records)!=1 or len(ready)!=1:
            raise ValueError('missing/ambiguous committed direction')
        item=records[0]; data=item['data']; claim=dict(data['assertion'])
        claim['event_class']=EventClass(claim['event_class'])
        assertion=ClassAssertion(**claim)
        recorded,available=map(datetime.fromisoformat,(item['at'],ready[0]['at']))
        if not (datetime.fromisoformat(self._config['at']) < receipt.received_at <= receipt.available_at
                <= c.envelope.available_at <= recorded <= available < reservation.decision_at):
            raise ValueError('noncausal direction')
        if data['event_id']!=c.envelope.event_id or data['provenance_hash']!=receipt.provenance_hash or data['decision_at']!=reservation.decision_at.isoformat():
            raise ValueError('direction provenance mismatch')
        return EventDirectionRecordV1(c.envelope.event_id,receipt_id,self.role,assertion.event_class,
            _classify(receipt,assertion),digest(assertion.body()),receipt.provenance_hash,
            recorded,available,reservation.decision_at,self.authority_id)
