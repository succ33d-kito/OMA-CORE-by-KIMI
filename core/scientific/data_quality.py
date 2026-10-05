"""Factual quality of evidence at a cutoff, without trading thresholds."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from .multi_market_capture import MarketCycle, SYMBOLS
from .multi_market_premium import PremiumCycle
from .nuisance_pilot_contracts import utc


class SourceError(Enum):
    NETWORK_FAILURE='NETWORK_FAILURE'
    UNSPECIFIED_FAILURE='UNSPECIFIED_FAILURE'
    NOT_OBSERVED='NOT_OBSERVED'


@dataclass(frozen=True,slots=True)
class DataQuality:
    state: str
    capture_span_seconds: float | None
    member_timestamp_skew_seconds: float | None
    oldest_evidence_age_seconds: float | None
    oldest_available_age_seconds: float | None
    missing_members: tuple[str,...]
    unknown_timestamp_members: tuple[str,...]
    source_errors: tuple[SourceError,...]
    clock_state: str
    assessed_at: datetime


def assess_quality(cycle,*,as_of):
    utc(as_of)
    if type(cycle) not in (MarketCycle,PremiumCycle): raise TypeError('supported cycle required')
    if cycle.completed_at>as_of: raise ValueError('quality not available at cutoff')
    symbols=tuple(m.symbol for m in cycle.members)
    if len(set(symbols))!=len(symbols) or set(symbols)&set(cycle.missing) or set(symbols)|set(cycle.missing)!=set(SYMBOLS):
        raise ValueError('invalid population accounting')
    times=[m.exchange_at for m in cycle.members if m.exchange_at is not None]
    unknown=tuple(sorted(m.symbol for m in cycle.members if m.exchange_at is None))
    if any(m.available_at>as_of for m in cycle.members) or any(t>as_of for t in times):
        raise ValueError('future evidence')
    complete_times=bool(times) and not unknown
    return DataQuality(cycle.completeness,cycle.capture_span_seconds,
        (max(times)-min(times)).total_seconds() if complete_times else None,
        (as_of-min(times)).total_seconds() if complete_times else None,
        max((as_of-m.available_at).total_seconds() for m in cycle.members) if cycle.members else None,
        tuple(sorted(cycle.missing)),unknown,(),'LOCAL_CONTINUITY_ONLY',as_of)


def unavailable_quality(*,as_of,source_error=SourceError.NOT_OBSERVED):
    utc(as_of)
    if type(source_error) is not SourceError: raise TypeError('closed source error required')
    return DataQuality('INCOMPLETE',None,None,None,None,SYMBOLS,(),(source_error,),'UNKNOWN',as_of)
