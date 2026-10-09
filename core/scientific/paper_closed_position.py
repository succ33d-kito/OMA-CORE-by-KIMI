"""CP-7L: fully closed simulated PAPER inventory; no economic interpretation."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from . import execution_position_plane as plane
from .paper_exit_fill import SimulatedPaperExitFill


class PaperClosedPositionPhase(Enum):
    PAPER_CLOSED = 'PAPER_CLOSED'


@dataclass(frozen=True, slots=True)
class PaperClosedPosition:
    """Inventory state derived solely from verified simulated close evidence.

    opened_at/closed_at mean evidence availability, not settlement or factual
    account state. Prices and quantity are inherited, never economic results.
    Original open inventory and fill objects are preserved without mutation.
    """
    exit_fill: SimulatedPaperExitFill
    open_position_ref: str = field(init=False)
    entry_fill_ref: str = field(init=False)
    exit_intent_ref: str = field(init=False)
    exit_fill_ref: str = field(init=False)
    thesis_id: str = field(init=False)
    instrument: str = field(init=False)
    entry_side: plane.Side = field(init=False)
    exit_side: plane.Side = field(init=False)
    quantity_base: Decimal = field(init=False)
    entry_price_usdt_per_base: Decimal = field(init=False)
    exit_price_usdt_per_base: Decimal = field(init=False)
    opened_at: datetime = field(init=False)
    closed_at: datetime = field(init=False)
    phase: PaperClosedPositionPhase = field(init=False, default=PaperClosedPositionPhase.PAPER_CLOSED)
    mode: plane.Mode = field(init=False, default=plane.Mode.PAPER)
    kind: str = field(init=False, default='SIMULATED_PAPER_CLOSED_POSITION')
    actionable: bool = field(init=False, default=False)
    closed_position_id: str = field(init=False)

    def __post_init__(self):
        plane.verify(self.exit_fill, SimulatedPaperExitFill)
        fill = self.exit_fill
        intent = fill.exit_intent
        position = intent.lifecycle.position
        if fill.exit_quantity_base != position.filled_quantity_base:
            raise ValueError('full simulated close quantity required')
        if (position.side, fill.side) not in ((plane.Side.BUY, plane.Side.SELL),
                                             (plane.Side.SELL, plane.Side.BUY)):
            raise ValueError('opposite simulated exit side required')
        if not position.available_at < fill.available_at:
            raise ValueError('simulated close evidence must follow open availability')
        if not all(at > intent.available_at for at in (fill.exchange_at, fill.received_at, fill.available_at)):
            raise ValueError('strictly post-exit-intent evidence required')
        for name, value in (
            ('open_position_ref', position.position_id), ('entry_fill_ref', position.entry_execution_ref),
            ('exit_intent_ref', intent.exit_intent_id), ('exit_fill_ref', fill.exit_fill_id),
            ('thesis_id', position.thesis_id), ('instrument', position.instrument),
            ('entry_side', position.side), ('exit_side', fill.side),
            ('quantity_base', position.filled_quantity_base),
            ('entry_price_usdt_per_base', position.entry_price_usdt_per_base),
            ('exit_price_usdt_per_base', fill.simulated_exit_price_usdt_per_base),
            ('opened_at', position.available_at), ('closed_at', fill.available_at),
        ):
            object.__setattr__(self, name, value)
        plane.upstream._seal(self, 'closed_position_id')
