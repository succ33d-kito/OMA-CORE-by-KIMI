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
