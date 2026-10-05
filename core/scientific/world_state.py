"""Immutable as-of state from verified book/premium receipts; no forecasts."""
from dataclasses import dataclass,asdict,field
from datetime import datetime
from decimal import Decimal,localcontext
from .multi_market_capture import load_universe,load_cycle,MarketObservation,SYMBOLS,commitment
from .multi_market_premium import load_premium_cycle,PremiumMember
from .universe_snapshot import load_snapshot
from .data_quality import DataQuality,assess_quality,unavailable_quality
from .nuisance_pilot_contracts import utc


def _normalize(value):
    if isinstance(value,datetime): return value.isoformat()
    if isinstance(value,Decimal): return str(value)
    if isinstance(value,dict): return {k:_normalize(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [_normalize(v) for v in value]
    from enum import Enum
    if isinstance(value,Enum): return value.value
    return value


@dataclass(frozen=True,slots=True)
class WorldMarket:
    symbol: str
    book: MarketObservation | None
    premium: PremiumMember | None
    book_age_seconds: float | None
    premium_age_seconds: float | None

    @property
    def mid(self):
        if self.book is None: return None
        with localcontext() as ctx:
            ctx.prec=100
            return (self.book.bid+self.book.ask)/2

    @property
    def spread(self):
        if self.book is None: return None
        with localcontext() as ctx:
            ctx.prec=100
            return self.book.ask-self.book.bid


@dataclass(frozen=True,slots=True)
class WorldState:
    universe_id: str
    as_of: datetime
    markets: tuple[WorldMarket,...]
    book_cycle_id: str | None
    book_cycle_kind: str | None
    premium_cycle_id: str | None
    book_quality: DataQuality
    premium_quality: DataQuality
    role: str = 'PILOT'
    world_state_id: str = field(init=False)

    def __post_init__(self):
        utc(self.as_of)
        if self.role!='PILOT' or type(self.markets) is not tuple or tuple(m.symbol for m in self.markets)!=SYMBOLS:
            raise ValueError('immutable frozen PILOT population required')
        for m in self.markets:
            if type(m) is not WorldMarket: raise TypeError('closed world market required')
            for evidence,cls in ((m.book,MarketObservation),(m.premium,PremiumMember)):
                if evidence is not None and (type(evidence) is not cls or evidence.role!=self.role or evidence.symbol!=m.symbol or evidence.available_at>self.as_of):
                    raise ValueError('noncausal/cross-scope evidence')
        if any(type(q) is not DataQuality or q.assessed_at!=self.as_of for q in (self.book_quality,self.premium_quality)):
            raise ValueError('quality cutoff mismatch')
        payload={f:getattr(self,f) for f in ('universe_id','as_of','book_cycle_id','book_cycle_kind','premium_cycle_id','role')}
        payload.update(markets=[asdict(m) for m in self.markets],book_quality=asdict(self.book_quality),premium_quality=asdict(self.premium_quality))
        object.__setattr__(self,'world_state_id',commitment(_normalize(payload)))


def load_world(universe_directory,*,as_of,book_directory=None,premium_directory=None):
    utc(as_of); u=load_universe(universe_directory)
    if u.frozen_at>as_of: raise ValueError('universe unavailable')
    books={}; premiums={}; bid=bkind=pid=None
    bq=unavailable_quality(as_of=as_of); pq=unavailable_quality(as_of=as_of)
    if book_directory is not None:
        snapshot=load_snapshot(book_directory,universe_directory,as_of=as_of)
        if snapshot.cycle_id is not None:
            books={m.symbol:m.evidence for m in snapshot.members if m.evidence is not None}
            bid=snapshot.cycle_id; bkind=snapshot.cycle_kind
            bq=assess_quality(load_cycle(book_directory,universe_directory),as_of=as_of)
    if premium_directory is not None:
        cycle=load_premium_cycle(premium_directory,universe_directory)
        if cycle.completed_at<=as_of:
            premiums={m.symbol:m for m in cycle.members}; pid=cycle.cycle_id
            pq=assess_quality(cycle,as_of=as_of)
    def age(e): return None if e is None or e.exchange_at is None else (as_of-e.exchange_at).total_seconds()
    markets=tuple(WorldMarket(s,books.get(s),premiums.get(s),age(books.get(s)),age(premiums.get(s))) for s in u.symbols)
    return WorldState(u.universe_id,as_of,markets,bid,bkind,pid,bq,pq)
