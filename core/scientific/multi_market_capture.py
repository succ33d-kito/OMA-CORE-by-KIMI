"""Frozen PILOT universe, one full HTTP book response; no simultaneous-price claim."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from time import monotonic
from urllib.request import build_opener
from urllib.error import URLError

from .book_ticker_capture import _NoRedirect, _json, _write, _read_json, _now
from .capture_clock import continuous
from .execution_observation import _decimal, _pairs
from .nuisance_pilot_contracts import utc

SYMBOLS = tuple(sorted(('BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'BNBUSDT')))
BOOK_URL = 'https://fapi.binance.com/fapi/v1/ticker/bookTicker'
INFO_URL = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
LIMIT = 8 * 1024 * 1024


class NetworkCaptureError(RuntimeError):
    """Transport failed; no claim of a verified complete response."""


def commitment(value):
    return hashlib.sha256(_json(value)).hexdigest()


def _http(url):
    return build_opener(_NoRedirect()).open(url, timeout=20)


def _receive(root, url):
    started = _now()
    tick = monotonic()
    try:
        with _http(url) as response:
            raw = response.read(LIMIT + 1)
            received = _now()
            elapsed = monotonic() - tick
            meta = dict(source=url, response_url=response.geturl(), status=response.status,
                        content_type=response.headers.get_content_type(), content_length=response.headers.get('Content-Length'),
                        started_at=started.isoformat(), received_at=received.isoformat(), elapsed=elapsed,
                        raw_sha256=hashlib.sha256(raw).hexdigest())
    except (URLError, TimeoutError, ConnectionError) as error:
        raise NetworkCaptureError('HTTP transport failed') from error
    _write(root/'response.raw', raw)
    _write(root/'receipt.json', _json(meta))
    _verify_response(meta, raw, url)
    return meta, raw


def _verify_response(meta, raw, url):
    if set(meta) != {'source','response_url','status','content_type','content_length','started_at','received_at','elapsed','raw_sha256'}:
        raise ValueError('unknown receipt metadata')
    if (meta['source'],meta['response_url'],meta['status'],meta['content_type']) != (url,url,200,'application/json'):
        raise ValueError('source mismatch')
    if not raw or len(raw)>LIMIT or hashlib.sha256(raw).hexdigest()!=meta['raw_sha256']:
        raise ValueError('raw commitment mismatch')
    if meta['content_length'] is not None and int(meta['content_length'])!=len(raw):
        raise ValueError('incomplete body')
    start, end = (datetime.fromisoformat(meta[k]) for k in ('started_at','received_at'))
    utc(start); utc(end)
    if start>end: raise ValueError('reversed reception')
    continuous(start,end,meta['elapsed'])


def _check_markets(raw):
    data=json.loads(raw,object_pairs_hook=_pairs)
    rows=data['symbols']
    selected=[r for r in rows if r['symbol'] in SYMBOLS]
    if len(selected)!=len(SYMBOLS) or {r['symbol'] for r in selected}!=set(SYMBOLS):
        raise ValueError('universe members missing or duplicated')
    if any((r['status'],r['contractType'],r['quoteAsset'],r['marginAsset']) !=
           ('TRADING','PERPETUAL','USDT','USDT') for r in selected):
        raise ValueError('universe not active linear USDT perpetuals')


@dataclass(frozen=True, slots=True)
class Universe:
    universe_id: str
    frozen_at: datetime
    symbols: tuple[str,...] = SYMBOLS
    version: str = 'v0'
    venue: str = 'Binance USDⓈ-M'
    product: str = 'linear perpetual'
    role: str = 'PILOT'


def freeze_universe(directory):
    root=Path(directory); root.mkdir(parents=True,exist_ok=False)
    meta,raw=_receive(root,INFO_URL)
    _check_markets(raw)
    frozen=_now(); utc(frozen)
    if frozen<datetime.fromisoformat(meta['received_at']): raise ValueError('clock reversed')
    manifest=dict(version='v0',symbols=list(SYMBOLS),venue='Binance USDⓈ-M',product='linear perpetual',
                  role='PILOT',frozen_at=frozen.isoformat(),receipt_commitment=commitment(meta))
    _write(root/'universe.json',_json(dict(manifest=manifest,universe_id=commitment(manifest))))
    return load_universe(root)


def load_universe(directory):
    root=Path(directory)
    meta=_read_json(root/'receipt.json'); raw=(root/'response.raw').read_bytes()
    _verify_response(meta,raw,INFO_URL); _check_markets(raw)
    saved=_read_json(root/'universe.json'); m=saved['manifest']
    if set(saved)!={'manifest','universe_id'} or set(m)!={'version','symbols','venue','product','role','frozen_at','receipt_commitment'}:
        raise ValueError('unknown universe metadata')
    if (m['version'],m['symbols'],m['venue'],m['product'],m['role'],m['receipt_commitment']) != (
            'v0',list(SYMBOLS),'Binance USDⓈ-M','linear perpetual','PILOT',commitment(meta)):
        raise ValueError('universe changed')
    if saved['universe_id']!=commitment(m): raise ValueError('universe commitment mismatch')
    frozen=datetime.fromisoformat(m['frozen_at']); utc(frozen)
    if frozen<datetime.fromisoformat(meta['received_at']): raise ValueError('freeze predates verification')
    return Universe(saved['universe_id'],frozen)


def _rows(raw,received):
    rows=json.loads(raw,object_pairs_hook=_pairs)
    if type(rows) is not list: raise ValueError('all-symbol response must be array')
    found={}
    for row in rows:
        if type(row) is not dict or set(row)-{'symbol','bidPrice','askPrice','bidQty','askQty','time','lastUpdateId'}:
            raise ValueError('unknown source field')
        symbol=row.get('symbol')
        if type(symbol) is not str or symbol in found: raise ValueError('invalid/duplicate symbol')
        found[symbol]=row
        if symbol not in SYMBOLS: continue  # Full nonmember wire records remain in raw.
        bid,ask=(_decimal(row[k]) for k in ('bidPrice','askPrice'))
        if not 0<bid<=ask: raise ValueError('invalid quotes')
        for key in ('bidQty','askQty'):
            if key in row and _decimal(row[key])<0: raise ValueError('negative quantity')
        for key in ('time','lastUpdateId'):
            if key in row and (type(row[key]) is not int or row[key]<0): raise ValueError('invalid source metadata')
        if 'time' in row and datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(milliseconds=row['time'])>received:
            raise ValueError('exchange time after receipt')
    return found


@dataclass(frozen=True, slots=True)
class MarketObservation:
    symbol: str
    observation_id: str
    raw_commitment: str
    wire_json: str
    received_at: datetime
    available_at: datetime
    exchange_at: datetime | None
    source_update_id: int | None
    bid: Decimal
    ask: Decimal
    role: str = 'PILOT'


@dataclass(frozen=True, slots=True)
class MarketCycle:
    cycle_id: str
    universe_id: str
    kind: str
    slot: datetime
    started_at: datetime
    completed_at: datetime
    received_at: datetime
    members: tuple[MarketObservation,...]
    missing: tuple[str,...]
    semantics: str = 'SINGLE_HTTP_NOT_SIMULTANEOUS'

    @property
    def completeness(self): return 'INCOMPLETE' if self.missing else 'COMPLETE'

    @property
    def capture_span_seconds(self): return (self.completed_at-self.started_at).total_seconds()


def capture_cycle(directory, universe_directory, *, kind='DIAGNOSTIC', slot=None):
    universe=load_universe(universe_directory)
    now=_now(); utc(now)
    if kind not in ('DIAGNOSTIC','H1'): raise ValueError('invalid cycle kind')
    slot=now if slot is None and kind=='DIAGNOSTIC' else slot
    utc(slot)
    if universe.frozen_at>now: raise ValueError('universe unavailable')
    if kind=='H1' and (slot!=slot.replace(minute=0,second=0,microsecond=0) or not slot<=now<slot+timedelta(minutes=2)):
        raise ValueError('not a live scheduled slot; no backfill')
    if kind=='DIAGNOSTIC' and slot!=now: raise ValueError('diagnostic slot must be internally sampled')
    root=Path(directory); root.mkdir(parents=True,exist_ok=False)
    meta,raw=_receive(root,BOOK_URL)
    start=datetime.fromisoformat(meta['started_at']); received=datetime.fromisoformat(meta['received_at'])
    if start<now or (kind=='H1' and not slot<=start<slot+timedelta(minutes=2)):
        raise ValueError('capture outside admission window')
    _rows(raw,received)
    available=_now(); utc(available)
    if available<received: raise ValueError('clock reversed')
    m=dict(universe_id=universe.universe_id,kind=kind,slot=slot.isoformat(),available_at=available.isoformat(),
           receipt_commitment=commitment(meta))
    _write(root/'cycle.json',_json(dict(manifest=m,commitment=commitment(m))))
    return load_cycle(root,universe_directory)


def load_cycle(directory,universe_directory):
    universe=load_universe(universe_directory); root=Path(directory)
    meta=_read_json(root/'receipt.json'); raw=(root/'response.raw').read_bytes()
    _verify_response(meta,raw,BOOK_URL)
    saved=_read_json(root/'cycle.json'); m=saved['manifest']
    if set(saved)!={'manifest','commitment'} or set(m)!={'universe_id','kind','slot','available_at','receipt_commitment'}:
        raise ValueError('unknown cycle metadata')
    if saved['commitment']!=commitment(m) or m['universe_id']!=universe.universe_id or m['receipt_commitment']!=commitment(meta):
        raise ValueError('cycle commitment mismatch')
    start,received=(datetime.fromisoformat(meta[k]) for k in ('started_at','received_at'))
    available,slot=(datetime.fromisoformat(m[k]) for k in ('available_at','slot'))
    utc(available); utc(slot)
    if not universe.frozen_at<=slot<=start<=received<=available: raise ValueError('noncausal cycle')
    if m['kind'] not in ('H1','DIAGNOSTIC'): raise ValueError('invalid kind')
    if m['kind']=='H1' and (slot!=slot.replace(minute=0,second=0,microsecond=0) or start>=slot+timedelta(minutes=2)):
        raise ValueError('invalid H1 slot')
    rows=_rows(raw,received)
    cid=commitment((universe.universe_id,m['kind'],slot.isoformat()))
    members=[]
    for symbol in universe.symbols:
        if symbol not in rows: continue
        row=rows[symbol]; wire=_json(row).decode()
        identity=commitment((cid,saved['commitment'],meta['raw_sha256'],symbol,wire))
        at=None if 'time' not in row else datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(milliseconds=row['time'])
        members.append(MarketObservation(symbol,identity,meta['raw_sha256'],wire,received,available,at,
                                         row.get('lastUpdateId'),_decimal(row['bidPrice']),_decimal(row['askPrice'])))
    return MarketCycle(cid,universe.universe_id,m['kind'],slot,start,available,received,tuple(members),
                       tuple(s for s in universe.symbols if s not in rows))
