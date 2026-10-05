"""Read-only causal view of verified cycles; no signals or relative ranking."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from .multi_market_capture import load_universe, load_cycle, commitment, MarketObservation
from .nuisance_pilot_contracts import utc


@dataclass(frozen=True, slots=True)
class SnapshotMember:
    symbol: str
    status: str
    evidence: MarketObservation | None


@dataclass(frozen=True, slots=True)
class UniverseSnapshot:
    snapshot_id: str
    universe_id: str
    cycle_id: str | None
    cycle_kind: str | None
    as_of: datetime
    members: tuple[SnapshotMember,...]
    role: str = 'PILOT'


def load_snapshot(cycle_directory,universe_directory,*,as_of):
    """Never expose late cycle identity, missingness, fields or member evidence."""
    utc(as_of)
    universe=load_universe(Path(universe_directory))
    if universe.frozen_at>as_of: raise ValueError('universe not available at cutoff')
    cycle=load_cycle(Path(cycle_directory),Path(universe_directory))
    visible=cycle.completed_at<=as_of
    evidence={m.symbol:m for m in cycle.members} if visible else {}
    members=tuple(SnapshotMember(s,'AVAILABLE' if s in evidence else ('MISSING' if visible else 'UNAVAILABLE'),
                                 evidence.get(s)) for s in universe.symbols)
    cid=cycle.cycle_id if visible else None
    kind=cycle.kind if visible else None
    identity=commitment((universe.universe_id,cid,kind,as_of.isoformat(),
                         [(m.symbol,m.status,m.evidence.observation_id if m.evidence else None) for m in members]))
    return UniverseSnapshot(identity,universe.universe_id,cid,kind,as_of,members)
