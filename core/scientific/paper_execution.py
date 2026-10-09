"""CP-7G: sparse post-intent PAPER simulation, never venue execution evidence.

Callers supply MarketCycles from load_cycle's verified receipt path. In-memory
types/commitments are not independent authentication of HTTP capture. Selection
is earliest within the supplied cycles; it does not certify stream completeness.
The requested USD-notional / USDT-price rule assumes nominal USD=USDT solely for
this simulation. No factual FX conversion, depth, fee or latency is inferred.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, Context, ROUND_HALF_EVEN, localcontext

from . import execution_position_plane as plane
from . import multi_market_capture as capture


POST_INTENT_NEXT_OBSERVED_QUOTE_V0 = 'POST_INTENT_NEXT_OBSERVED_QUOTE_V0'


@dataclass(frozen=True, slots=True)
class PaperExecutionRequest:
    pending_position: plane.PositionState
    quality_gate: plane.ExecutionQualityGate
    submitted_at: datetime
    request_id: str = field(init=False)

    def __post_init__(self):
        plane.verify(self.pending_position, plane.PositionState)
        plane.verify(self.quality_gate, plane.ExecutionQualityGate)
        p = self.pending_position
        if p.mode is not plane.Mode.PAPER or p.phase is not plane.PositionPhase.PENDING_EXECUTION:
            raise ValueError('PAPER pending position required')
        if any(v is not None for v in (p.filled_quantity_base, p.entry_price_usdt_per_base, p.entry_execution_ref)):
            raise ValueError('pending position must have no execution evidence')
        if self.quality_gate.state is not plane.QualityState.PASS:
            raise ValueError('PASS quality gate required')
        plan = p.intent.plan
        if self.quality_gate.decision != plan.decision or self.quality_gate.candidate_id != plan.candidate_id:
            raise ValueError('quality gate decision/candidate mismatch')
        if type(self.submitted_at) is not datetime or self.submitted_at.utcoffset() is None:
            raise ValueError('aware submitted_at required')
        object.__setattr__(self, 'submitted_at', self.submitted_at.astimezone(timezone.utc))
        if self.submitted_at < p.available_at:
            raise ValueError('request predates pending position availability')
        if p.intent.quantity_unit != 'USD_NOTIONAL':
            raise ValueError('authorized USD_NOTIONAL required')
        plane.number(p.intent.quantity, positive=True)
        plane.upstream._seal(self, 'request_id')


def _eligible(request, quote):
    if type(quote) is not capture.MarketObservation:
        raise TypeError('exact MarketObservation required')
    if quote.symbol != request.pending_position.instrument or quote.role != 'PILOT':
        return False
    # Check integrity even when an otherwise matching quote is too early.
    plane.number(quote.bid, positive=True)
    plane.number(quote.ask, positive=True)
    plane.check_book(quote, quote.available_at)
    if quote.exchange_at is None:
        return False
    plane.utc(quote.exchange_at)
    return all(at > request.submitted_at for at in
               (quote.exchange_at, quote.received_at, quote.available_at))


@dataclass(frozen=True, slots=True)
class SimulatedPaperFill:
    request: PaperExecutionRequest
    quote: capture.MarketObservation
    model: str = field(init=False, default=POST_INTENT_NEXT_OBSERVED_QUOTE_V0)
    kind: str = field(init=False, default='SIMULATED_PAPER_FILL')
    quantity_convention: str = field(init=False, default='NOMINAL_USD_EQUALS_USDT_SIMULATION_ONLY')
    side: plane.Side = field(init=False)
    simulated_fill_price_usdt_per_base: Decimal = field(init=False)
    filled_quantity_base: Decimal = field(init=False)
    evidence_ref: str = field(init=False)
    raw_commitment_ref: str = field(init=False)
    exchange_at: datetime = field(init=False)
    received_at: datetime = field(init=False)
    available_at: datetime = field(init=False)
    fill_id: str = field(init=False)

    def __post_init__(self):
        plane.verify(self.request, PaperExecutionRequest)
        if not _eligible(self.request, self.quote):
            raise ValueError('no eligible post-intent quote')
        intent = self.request.pending_position.intent
        price = self.quote.ask if intent.side is plane.Side.BUY else self.quote.bid
        # Isolated precision/rounding, independent of caller Decimal context.
        with localcontext(Context(prec=100, rounding=ROUND_HALF_EVEN)):
            quantity = intent.quantity / price
        for name, value in (
            ('side', intent.side), ('simulated_fill_price_usdt_per_base', price),
            ('filled_quantity_base', quantity), ('evidence_ref', self.quote.observation_id),
            ('raw_commitment_ref', self.quote.raw_commitment), ('exchange_at', self.quote.exchange_at),
            ('received_at', self.quote.received_at), ('available_at', self.quote.available_at),
        ):
            object.__setattr__(self, name, value)
        plane.upstream._seal(self, 'fill_id')


def select_paper_fill(request, cycles):
    """Earliest eligible quote from verified cycles, or None. Never fallback.

    Identical cycle replays are harmless; conflicting cycle/observation identities
    fail closed. This function does not capture, persist, or alter any position.
    """
    plane.verify(request, PaperExecutionRequest)
    if type(cycles) is not tuple:
        raise TypeError('immutable tuple of verified MarketCycles required')
    universe = request.pending_position.intent.plan.decision.world.universe_id
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
            if _eligible(request, quote): eligible.append(quote)
    if not eligible: return None
    chosen = min(eligible, key=lambda q:(q.available_at, q.received_at, q.exchange_at, q.observation_id))
    return SimulatedPaperFill(request, chosen)
