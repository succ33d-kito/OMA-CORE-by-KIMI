"""CP-7J: simulated PAPER exit intention only; no execution or inventory change."""
from dataclasses import dataclass, field
from datetime import datetime

from . import execution_position_plane as plane
from .paper_position_lifecycle import PaperPositionLifecycle, PaperLifecycleState


@dataclass(frozen=True, slots=True)
class PaperExitIntent:
    """Only frozen explicit thesis expiry supports an exit intention.

    Missing observation never authorizes exit. Availability is assessment time,
    not submission, acknowledgement or fill time. Future simulated exit fills
    require a separate post-intent evidence contract.
    """
    lifecycle: PaperPositionLifecycle
    position_ref: str = field(init=False)
    lifecycle_assessment_ref: str = field(init=False)
    side: plane.Side = field(init=False)
    reason: str = field(init=False)
    mode: plane.Mode = field(init=False, default=plane.Mode.PAPER)
    kind: str = field(init=False, default='SIMULATED_PAPER_EXIT_INTENT')
    actionable: bool = field(init=False, default=False)
    available_at: datetime = field(init=False)
    exit_intent_id: str = field(init=False)

    def __post_init__(self):
        plane.verify(self.lifecycle, PaperPositionLifecycle)
        if (self.lifecycle.state is not PaperLifecycleState.TIMEOUT
                or self.lifecycle.reason != 'EXPLICIT_THESIS_EXPIRY'):
            raise ValueError('only explicit thesis expiry TIMEOUT supports PAPER exit intent')
        entry_side = self.lifecycle.position.side
        if entry_side is plane.Side.BUY:
            side = plane.Side.SELL
        elif entry_side is plane.Side.SELL:
            side = plane.Side.BUY
        else:
            raise ValueError('unsupported PAPER entry side')
        for name, value in (
            ('position_ref', self.lifecycle.position.position_id),
            ('lifecycle_assessment_ref', self.lifecycle.assessment_id),
            ('side', side), ('reason', self.lifecycle.reason),
            ('available_at', self.lifecycle.assessed_at),
        ):
            object.__setattr__(self, name, value)
        plane.upstream._seal(self, 'exit_intent_id')
