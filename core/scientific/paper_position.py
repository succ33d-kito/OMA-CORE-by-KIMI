"""CP-7H: immutable simulated inventory, separate from pending PositionState.

This contract neither executes nor persists orders. PAPER_OPEN is simulated
inventory only, never venue/broker evidence, factual holdings or validated edge.
It does not authorize exits, portfolio reallocation, PnL or learning.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from . import execution_position_plane as plane
from .paper_execution import SimulatedPaperFill


class PaperPositionPhase(Enum):
    PAPER_OPEN = 'PAPER_OPEN'


@dataclass(frozen=True, slots=True)
class PaperOpenPosition:
    """All inventory and provenance derive from one verified simulated fill.

    available_at is the fill evidence availability, not its exchange timestamp.
    Replaying the same fill gives the same identity; no pending object is mutated.
    The fill retains CP-7G's supplied-evidence and nominal USD=USDT limitations.
    """
    fill: SimulatedPaperFill
    phase: PaperPositionPhase = field(init=False, default=PaperPositionPhase.PAPER_OPEN)
    mode: plane.Mode = field(init=False, default=plane.Mode.PAPER)
    kind: str = field(init=False, default='SIMULATED_PAPER_POSITION')
    actionable: bool = field(init=False, default=False)
    filled_quantity_base: Decimal = field(init=False)
    entry_price_usdt_per_base: Decimal = field(init=False)
    entry_execution_ref: str = field(init=False)
    pending_position_ref: str = field(init=False)
    thesis_id: str = field(init=False)
    available_at: datetime = field(init=False)
    position_id: str = field(init=False)

    def __post_init__(self):
        plane.verify(self.fill, SimulatedPaperFill)
        pending = self.fill.request.pending_position
        for name, value in (
            ('filled_quantity_base', self.fill.filled_quantity_base),
            ('entry_price_usdt_per_base', self.fill.simulated_fill_price_usdt_per_base),
            ('entry_execution_ref', self.fill.fill_id),
            ('pending_position_ref', pending.position_id),
            ('thesis_id', pending.thesis_id),
            ('available_at', self.fill.available_at),
        ):
            object.__setattr__(self, name, value)
        plane.upstream._seal(self, 'position_id')

    @property
    def intent(self): return self.fill.request.pending_position.intent

    @property
    def instrument(self): return self.intent.instrument

    @property
    def direction(self): return self.intent.direction

    @property
    def side(self): return self.fill.side

    @property
    def role(self): return self.intent.role

    @property
    def model(self): return self.fill.model

    @property
    def quantity_convention(self): return self.fill.quantity_convention

    @property
    def evidence_ref(self): return self.fill.evidence_ref

    @property
    def raw_commitment_ref(self): return self.fill.raw_commitment_ref

    @property
    def exchange_at(self): return self.fill.exchange_at

    @property
    def received_at(self): return self.fill.received_at
