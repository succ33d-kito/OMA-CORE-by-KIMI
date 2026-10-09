"""CP-7I: causal assessment of simulated inventory; no hold or exit authority."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from . import execution_position_plane as plane
from .paper_position import PaperOpenPosition


class PaperLifecycleState(Enum):
    TRACKED = 'TRACKED'
    OBSERVATION_RISK = 'OBSERVATION_RISK'
    TIMEOUT = 'TIMEOUT'


@dataclass(frozen=True, slots=True)
class PaperPositionLifecycle:
    """Observation only: TRACKED is not a recommendation; TIMEOUT is not exit.

    Callers supply worlds from verified loaders. Contract integrity and book
    wire checks do not independently authenticate capture or factual holdings.
    """
    position: PaperOpenPosition
    world: plane.upstream.WorldState
    assessed_at: datetime
    state: PaperLifecycleState = field(init=False)
    reason: str = field(init=False)
    assessment_id: str = field(init=False)

    def __post_init__(self):
        plane.verify(self.position, PaperOpenPosition)
        plane.verify(self.world, plane.upstream.WorldState)
        if type(self.assessed_at) is not datetime or self.assessed_at.utcoffset() is None:
            raise ValueError('aware assessed_at required')
        object.__setattr__(self, 'assessed_at', self.assessed_at.astimezone(timezone.utc))
        decision = self.position.intent.plan.decision
        if self.world.role != self.position.role or self.world.universe_id != decision.world.universe_id:
            raise ValueError('paper lifecycle role/universe mismatch')
        if not self.position.available_at <= self.world.as_of <= self.assessed_at:
            raise ValueError('paper lifecycle requires causal world at or after open availability')
        theses = [t for t in decision.theses if t.thesis_id == self.position.thesis_id]
        markets = [m for m in self.world.markets if m.symbol == self.position.instrument]
        if len(theses) != 1:
            raise ValueError('paper lifecycle requires unique original thesis')
        if len(markets) != 1:
            raise ValueError('paper lifecycle requires unique instrument market')
        thesis, market = theses[0], markets[0]
        if market.book is not None:
            plane.check_book(market.book, self.world.as_of)
        if thesis.expiry is not None and self.assessed_at >= thesis.expiry:
            state, reason = PaperLifecycleState.TIMEOUT, 'EXPLICIT_THESIS_EXPIRY'
        elif market.book is None:
            state, reason = PaperLifecycleState.OBSERVATION_RISK, 'MISSING_CAUSAL_BOOK'
        else:
            state, reason = PaperLifecycleState.TRACKED, 'TRACKED_NO_SUPPORTED_INVALIDATION_EVALUATOR'
        object.__setattr__(self, 'state', state)
        object.__setattr__(self, 'reason', reason)
        plane.upstream._seal(self, 'assessment_id')
