"""Full premiumIndex response projected to the frozen PILOT universe; no payments."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
from . import multi_market_capture as c
from .execution_observation import _pairs, _decimal

URL='https://fapi.binance.com/fapi/v1/premiumIndex'


def _parse(raw,received):
    data=json.loads(raw,object_pairs_hook=_pairs)
    if type(data) is not list: raise ValueError('all-symbol array required')
    found={}
    for row in data:
        if type(row) is not dict or set(row)-{'symbol','markPrice','indexPrice','estimatedSettlePrice','lastFundingRate','interestRate','nextFundingTime','time'}:
            raise ValueError('unknown premium wire fields')
        symbol=row.get('symbol')
        if type(symbol) is not str or symbol in found: raise ValueError('duplicate/invalid symbol')
        found[symbol]=row
        if symbol not in c.SYMBOLS: continue
        for key in ('markPrice','indexPrice','lastFundingRate'):
            if key not in row or row[key] is None: raise ValueError('required observation missing')
        for key,value in row.items():
            if key=='symbol': continue
            if key in ('time','nextFundingTime'):
                if type(value) is not int or value<0: raise ValueError('invalid timestamp')
            else:
                value=_decimal(value)
                if key.endswith('Price') and value<=0: raise ValueError('nonpositive price')
                if key.endswith('Rate') and abs(value)>1: raise ValueError('fraction required')
        if 'time' in row and _at(row['time'])>received: raise ValueError('future source timestamp')
    return found


def _at(ms): return datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(milliseconds=ms)


@dataclass(frozen=True,slots=True)
class PremiumMember:
    symbol: str
    observation_id: str
    raw_commitment: str
    wire_json: str
    mark: Decimal
    index: Decimal
    funding_rate: Decimal
    next_funding_at: datetime | None
    exchange_at: datetime | None
    received_at: datetime
    available_at: datetime
    source: str = URL
    role: str = 'PILOT'


@dataclass(frozen=True,slots=True)
class PremiumCycle:
    cycle_id: str
    universe_id: str
    started_at: datetime
    received_at: datetime
    completed_at: datetime
    members: tuple[PremiumMember,...]
    missing: tuple[str,...]
    role: str = 'PILOT'

    @property
    def completeness(self): return 'INCOMPLETE' if self.missing else 'COMPLETE'

    @property
    def capture_span_seconds(self): return (self.completed_at-self.started_at).total_seconds()


def capture_premium_cycle(directory,universe_directory):
    u=c.load_universe(universe_directory)
    root=Path(directory); root.mkdir(parents=True,exist_ok=False)
    meta,raw=c._receive(root,URL)
    received=datetime.fromisoformat(meta['received_at'])
    if u.frozen_at>datetime.fromisoformat(meta['started_at']): raise ValueError('universe unavailable')
    _parse(raw,received)
    available=c._now(); c.utc(available)
    if available<received: raise ValueError('clock reversed')
    m=dict(universe_id=u.universe_id,receipt_commitment=c.commitment(meta),available_at=available.isoformat(),role='PILOT')
    c._write(root/'premium.json',c._json(dict(manifest=m,commitment=c.commitment(m))))
    return load_premium_cycle(root,universe_directory)


def load_premium_cycle(directory,universe_directory):
    u=c.load_universe(universe_directory); root=Path(directory)
    meta=c._read_json(root/'receipt.json'); raw=(root/'response.raw').read_bytes()
    c._verify_response(meta,raw,URL)
    saved=c._read_json(root/'premium.json'); m=saved['manifest']
    if set(saved)!={'manifest','commitment'} or set(m)!={'universe_id','receipt_commitment','available_at','role'}:
        raise ValueError('unknown premium metadata')
    if saved['commitment']!=c.commitment(m) or (m['universe_id'],m['receipt_commitment'],m['role'])!=(u.universe_id,c.commitment(meta),'PILOT'):
        raise ValueError('premium commitment mismatch')
    start,received=(datetime.fromisoformat(meta[k]) for k in ('started_at','received_at'))
    available=datetime.fromisoformat(m['available_at']); c.utc(available)
    if not u.frozen_at<=start<=received<=available: raise ValueError('noncausal premium')
    rows=_parse(raw,received); cid=saved['commitment']; members=[]
    for s in u.symbols:
        if s not in rows: continue
        row=rows[s]; wire=c._json(row).decode()
        members.append(PremiumMember(s,c.commitment((cid,s,wire)),meta['raw_sha256'],wire,
            *(_decimal(row[k]) for k in ('markPrice','indexPrice','lastFundingRate')),
            _at(row['nextFundingTime']) if 'nextFundingTime' in row else None,
            _at(row['time']) if 'time' in row else None,received,available))
    return PremiumCycle(cid,u.universe_id,start,received,available,tuple(members),tuple(s for s in u.symbols if s not in rows))
