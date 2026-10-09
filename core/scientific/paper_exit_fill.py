"""CP-7K: simulated exit fill only; neither closes inventory nor establishes PnL.

Callers supply cycles from load_cycle's verified receipt path. These in-memory
checks do not authenticate capture or certify complete stream coverage.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from . import execution_position_plane as plane
from . import multi_market_capture as capture
from .paper_exit_intent import PaperExitIntent


POST_EXIT_INTENT_NEXT_OBSERVED_QUOTE_V0 = 'POST_EXIT_INTENT_NEXT_OBSERVED_QUOTE_V0'


def _eligible(exit_intent, quote):
    if type(quote) is not capture.MarketObservation:
        raise TypeError('exact MarketObservation required')
    if quote.symbol != exit_intent.lifecycle.position.instrument or quote.role != 'PILOT':
        return False
    plane.number(quote.bid, positive=True)
    plane.number(quote.ask, positive=True)
    plane.check_book(quote, quote.available_at)
    if quote.exchange_at is None:
        return False
    plane.utc(quote.exchange_at)
    return all(at > exit_intent.available_at for at in
               (quote.exchange_at, quote.received_at, quote.available_at))


@dataclass(frozen=True, slots=True)
class SimulatedPaperExitFill:
    """Full simulated exit quantity only; no mutation or venue execution authority."""
    exit_intent: PaperExitIntent
    quote: capture.MarketObservation
    kind: str = field(init=False, default='SIMULATED_PAPER_EXIT_FILL')
    model: str = field(init=False, default=POST_EXIT_INTENT_NEXT_OBSERVED_QUOTE_V0)
    side: plane.Side = field(init=False)
    simulated_exit_price_usdt_per_base: Decimal = field(init=False)
    exit_quantity_base: Decimal = field(init=False)
    evidence_ref: str = field(init=False)
    raw_commitment_ref: str = field(init=False)
    exchange_at: datetime = field(init=False)
    received_at: datetime = field(init=False)
    available_at: datetime = field(init=False)
    exit_fill_id: str = field(init=False)

    def __post_init__(self):
        plane.verify(self.exit_intent, PaperExitIntent)
        if not _eligible(self.exit_intent, self.quote):
            raise ValueError('no eligible post-exit-intent quote')
        price = self.quote.bid if self.exit_intent.side is plane.Side.SELL else self.quote.ask
        quantity = self.exit_intent.lifecycle.position.filled_quantity_base
        plane.number(quantity, positive=True)
        for name, value in (
            ('side', self.exit_intent.side), ('simulated_exit_price_usdt_per_base', price),
            ('exit_quantity_base', quantity), ('evidence_ref', self.quote.observation_id),
            ('raw_commitment_ref', self.quote.raw_commitment), ('exchange_at', self.quote.exchange_at),
            ('received_at', self.quote.received_at), ('available_at', self.quote.available_at),
        ):
            object.__setattr__(self, name, value)
        plane.upstream._seal(self, 'exit_fill_id')


def select_paper_exit_fill(exit_intent, cycles):
    """Earliest eligible quote among supplied verified cycles, or None; no fallback.

    Identical replays are harmless; conflicting identities fail closed. This
    selector does not capture, persist, close or change any position.
    """
    plane.verify(exit_intent, PaperExitIntent)
    if type(cycles) is not tuple:
        raise TypeError('immutable tuple of verified MarketCycles required')
    universe = exit_intent.lifecycle.position.intent.plan.decision.world.universe_id
    seen_cycles, seen_quotes, eligible = {}, {}, []
    for cycle in cycles:
        if type(cycle) is not capture.MarketCycle or type(cycle.members) is not tuple or type(cycle.missing) is not tuple:
            raise TypeError('exact immutable MarketCycle required')
        if cycle.universe_id != universe or cycle.kind not in ('H1', 'DIAGNOSTIC') or cycle.semantics != 'SINGLE_HTTP_NOT_SIMULTANEOUS':
            raise ValueError('cycle scope mismatch')
        for at in (cycle.slot, cycle.started_at, cycle.received_at, cycle.completed_at): plane.utc(at)
        if not cycle.slot <= cycle.started_at <= cycle.received_at <= cycle.completed_at:
            raise ValueError('noncausal cycle')
        identity = capture.commitment((cycle.universe_id, cycle.kind, cycle.slot.isoformat()))
        if cycle.cycle_id != identity:
            raise ValueError('cycle identity mismatch')
        if cycle.cycle_id in seen_cycles and seen_cycles[cycle.cycle_id] != cycle:
            raise ValueError('conflicting cycle identity')
        seen_cycles[cycle.cycle_id] = cycle
        if any(type(q) is not capture.MarketObservation for q in cycle.members):
            raise TypeError('exact MarketObservation members required')
        symbols = tuple(q.symbol for q in cycle.members)
        if symbols != tuple(sorted(set(symbols))) or set(symbols) - set(capture.SYMBOLS) or cycle.missing != tuple(s for s in capture.SYMBOLS if s not in symbols):
            raise ValueError('cycle population mismatch')
        for quote in cycle.members:
            if quote.available_at != cycle.completed_at or quote.received_at != cycle.received_at:
                raise ValueError('quote/cycle timestamps mismatch')
            if quote.observation_id in seen_quotes and seen_quotes[quote.observation_id] != quote:
                raise ValueError('conflicting observation identity')
            seen_quotes[quote.observation_id] = quote
            if _eligible(exit_intent, quote): eligible.append(quote)
    if not eligible: return None
    chosen = min(eligible, key=lambda q: (q.available_at, q.received_at, q.exchange_at, q.observation_id))
    return SimulatedPaperExitFill(exit_intent, chosen)
