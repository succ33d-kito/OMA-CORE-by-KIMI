"""Outcome-blind SHADOW/PAPER contracts; never broker or execution evidence."""
from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal, localcontext
from enum import Enum

from . import trading_decision_plane as upstream
from .nuisance_pilot_contracts import utc


class Mode(Enum):
    SHADOW = 'SHADOW'
    PAPER = 'PAPER'


class PlanState(Enum):
    READY = 'READY'
    NO_ORDER = 'NO_ORDER'


def verify(value, cls):
    if type(value) is not cls:
        raise TypeError('exact contract type required')
    if replace(value) != value:
        raise ValueError('altered contract identity')


def number(value, *, positive=False):
    if type(value) is not Decimal or not value.is_finite():
        raise TypeError('finite Decimal required')
    if value < 0 or (positive and value == 0):
        raise ValueError('invalid magnitude')


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    decision: upstream.ShadowCapitalDecision
    candidate_id: str
    mode: Mode
    state: PlanState = field(init=False)
    reason: str = field(init=False)
    notional_usd: Decimal | None = field(init=False)
    plan_id: str = field(init=False)

    def __post_init__(self):
        verify(self.decision, upstream.ShadowCapitalDecision)
        if type(self.mode) is not Mode:
            raise TypeError('SHADOW/PAPER only')
        rows = [r for r in self.decision.allocation.rows if r.candidate_id == self.candidate_id]
        if len(rows) != 1:
            raise ValueError('candidate outside finalized allocation')
        row = rows[0]
        amount = None
        if row.amount.value is None or row.amount.value <= 0:
            reason = row.reason
        elif row.effective_authorization is None:
            raise ValueError('missing risk authorization')
        elif len(row.effective_authorization.request.legs) != 1:
            reason = 'UNSUPPORTED_MULTILEG_EXPRESSION'
        elif row.amount.unit is not upstream.CapitalUnit.USD_NOTIONAL:
            reason = 'MISSING_FACTUAL_RISK_TO_NOTIONAL_CONVERSION'
        else:
            amount = row.amount.value
            reason = 'AUTHORIZED_NOTIONAL_ONLY_NOT_VENUE_QUANTITY'
        object.__setattr__(self, 'notional_usd', amount)
        object.__setattr__(self, 'state', PlanState.READY if amount is not None else PlanState.NO_ORDER)
        object.__setattr__(self, 'reason', reason)
        upstream._seal(self, 'plan_id')

    @property
    def available_at(self):
        return self.decision.available_at

    @property
    def role(self):
        return self.decision.role


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """Notional intention only. No venue quantity/conversion adapter is installed."""
    plan: ExecutionPlan
    instrument: str = field(init=False)
    direction: upstream.Direction = field(init=False)
    venue: str = field(init=False)
    product: str = field(init=False)
    quantity: Decimal = field(init=False)
    quantity_unit: str = field(init=False, default='USD_NOTIONAL')
    actionable: bool = field(init=False, default=False)
    reason: str = field(init=False, default='MISSING_VENUE_QUANTITY_AND_ORDER_PARAMETERS')
    intent_id: str = field(init=False)

    def __post_init__(self):
        verify(self.plan, ExecutionPlan)
        if self.plan.state is not PlanState.READY:
            raise ValueError('NO_ORDER plan cannot form order intent')
        row = next(r for r in self.plan.decision.allocation.rows if r.candidate_id == self.plan.candidate_id)
        leg = row.effective_authorization.request.legs[0]
        for name, value in (('instrument', leg.symbol), ('direction', leg.direction),
                            ('venue', leg.venue), ('product', leg.product),
                            ('quantity', self.plan.notional_usd)):
            object.__setattr__(self, name, value)
        upstream._seal(self, 'intent_id')

    @property
    def mode(self):
        return self.plan.mode

    @property
    def role(self):
        return self.plan.role


class QualityState(Enum):
    PASS = 'PASS'
    DEFER = 'DEFER'
    REJECT = 'REJECT'


@dataclass(frozen=True, slots=True)
class QualityPolicy:
    registered_at: datetime
    max_book_age_seconds: Decimal | None
    max_relative_spread: Decimal | None
    policy_id: str = field(init=False)

    def __post_init__(self):
        utc(self.registered_at)
        for value in (self.max_book_age_seconds, self.max_relative_spread):
            if value is not None: number(value)
        upstream._seal(self, 'policy_id')


@dataclass(frozen=True, slots=True)
class ExecutionQualityGate:
    decision: upstream.ShadowCapitalDecision
    candidate_id: str
    policy: QualityPolicy
    state: QualityState = field(init=False)
    reason: str = field(init=False)
    evidence_refs: tuple[str, ...] = field(init=False)
    gate_id: str = field(init=False)

    def __post_init__(self):
        verify(self.decision, upstream.ShadowCapitalDecision)
        verify(self.policy, QualityPolicy)
        if self.policy.registered_at > self.decision.world.as_of:
            raise ValueError('quality policy must precede input world')
        candidates = [c for c in self.decision.radar.candidates if c.candidate_id == self.candidate_id]
        if len(candidates) != 1: raise ValueError('candidate not in decision')
        markets = [m for m in self.decision.world.markets if m.symbol in candidates[0].markets]
        refs = tuple(m.book.observation_id for m in markets if m.book is not None)
        state, reason = QualityState.PASS, 'CAUSAL_BOOK_WITHIN_EXPLICIT_LIMITS'
        if any(m.book is None for m in markets):
            state, reason = QualityState.DEFER, 'MISSING_BOOK'
        elif self.policy.max_book_age_seconds is None or self.policy.max_relative_spread is None:
            state, reason = QualityState.DEFER, 'UNKNOWN_REQUIRED_QUALITY_LIMIT'
        else:
            with localcontext() as ctx:
                ctx.prec = 100
                for m in markets:
                    if m.book.available_at > self.decision.available_at:
                        raise ValueError('future quote')
                    if m.book.exchange_at is None:
                        state, reason = QualityState.DEFER, 'UNKNOWN_EXCHANGE_TIME'
                        break
                    age = Decimal(str((self.decision.available_at - m.book.exchange_at).total_seconds()))
                    if age < 0: raise ValueError('future exchange evidence')
                    if age > self.policy.max_book_age_seconds or m.spread / m.mid > self.policy.max_relative_spread:
                        state, reason = QualityState.REJECT, 'BOOK_OUTSIDE_EXPLICIT_LIMITS'
                        break
        object.__setattr__(self, 'state', state)
        object.__setattr__(self, 'reason', reason)
        object.__setattr__(self, 'evidence_refs', refs)
        upstream._seal(self, 'gate_id')


@dataclass(frozen=True, slots=True)
class ExecutionEstimate:
    """Quote-based estimate, not a venue fill or an ExecutionObservation."""
    gate: ExecutionQualityGate
    reference_quote_usdt_per_base: Decimal | None = field(init=False)
    spread_usdt_per_base: Decimal | None = field(init=False)
    slippage_usdt_per_base: Decimal | None = field(init=False, default=None)
    fee_usdt: Decimal | None = field(init=False, default=None)
    funding_cashflow_usdt: Decimal | None = field(init=False, default=None)
    latency_seconds: Decimal | None = field(init=False, default=None)
    depth_base: Decimal | None = field(init=False, default=None)
    estimate_id: str = field(init=False)

    def __post_init__(self):
        verify(self.gate, ExecutionQualityGate)
        candidate = next(c for c in self.gate.decision.radar.candidates if c.candidate_id == self.gate.candidate_id)
        market = next((m for m in self.gate.decision.world.markets if candidate.markets == (m.symbol,)), None)
        usable = self.gate.state is QualityState.PASS and market is not None and market.book is not None
        object.__setattr__(self, 'reference_quote_usdt_per_base', market.mid if usable else None)
        object.__setattr__(self, 'spread_usdt_per_base', market.spread if usable else None)
        upstream._seal(self, 'estimate_id')


class PositionPhase(Enum):
    PENDING_EXECUTION = 'PENDING_EXECUTION'


@dataclass(frozen=True, slots=True)
class PositionState:
    """Pending position only; no accredited execution-result adapter exists yet.

    Intended USD notional is not a filled base quantity. In particular this
    contract cannot establish factual PAPER inventory from an order intention.
    """
    intent: OrderIntent
    created_at: datetime
    available_at: datetime
    thesis_id: str = field(init=False)
    phase: PositionPhase = field(init=False, default=PositionPhase.PENDING_EXECUTION)
    filled_quantity_base: Decimal | None = field(init=False, default=None)
    entry_price_usdt_per_base: Decimal | None = field(init=False, default=None)
    entry_execution_ref: str | None = field(init=False, default=None)
    position_id: str = field(init=False)

    def __post_init__(self):
        verify(self.intent, OrderIntent)
        utc(self.created_at); utc(self.available_at)
        if not self.intent.plan.available_at <= self.created_at <= self.available_at:
            raise ValueError('noncausal position record')
        thesis = next(t for t in self.intent.plan.decision.theses if t.candidate_id == self.intent.plan.candidate_id)
        object.__setattr__(self, 'thesis_id', thesis.thesis_id)
        upstream._seal(self, 'position_id')

    @property
    def mode(self): return self.intent.mode

    @property
    def role(self): return self.intent.role

    @property
    def instrument(self): return self.intent.instrument

    @property
    def direction(self): return self.intent.direction
