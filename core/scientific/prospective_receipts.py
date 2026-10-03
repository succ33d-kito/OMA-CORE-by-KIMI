"""Provider-neutral, append-only receipt ledger for prospective market observations.

Receipt time is assigned inside the writer; caller-supplied available_at is forbidden.
The hash chain detects mutation on export. No network access or backfill occurs.
"""
import csv, hashlib, json, sqlite3
from datetime import datetime, timezone, timedelta
from math import isfinite
from pathlib import Path

BAR_FIELDS=('time','open','high','low','close','volume')
METRIC_FIELDS=('timestamp','sum_open_interest','sum_open_interest_value','count_toptrader_long_short_ratio','sum_toptrader_long_short_ratio','count_long_short_ratio','sum_taker_long_short_vol_ratio')

def _utc(value):
    x=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    if x.tzinfo is None or x.utcoffset() is None:raise ValueError('timezone-aware timestamp required')
    return x.astimezone(timezone.utc)

def _digest(previous,kind,source,source_at,received_at,payload):
    obj={'previous_sha256':previous,'kind':kind,'source':source,'source_at':source_at,'received_at':received_at,'payload':payload}
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def _validate(kind,payload):
    fields=BAR_FIELDS if kind=='bar' else METRIC_FIELDS if kind=='metric' else None
    if fields is None or set(payload)!=set(fields):raise ValueError('unexpected kind or fields; available_at may not be supplied')
    at=_utc(payload[fields[0]])
    if kind=='bar' and (at.minute or at.second or at.microsecond):raise ValueError('bar must open on UTC hour')
    values={key:float(payload[key]) for key in fields[1:]}
    if not all(isfinite(x) for x in values.values()):raise ValueError('nonfinite data')
    if kind=='bar':
        o,h,l,c,v=(values[x] for x in fields[1:])
        if min(o,h,l,c)<=0 or v<0 or l>min(o,c) or h<max(o,c) or l>h:raise ValueError('invalid bar')
    elif any(x<=0 for x in values.values()):raise ValueError('invalid metric')
    normalized={fields[0]:at.isoformat(),**values}
    return at,normalized

def _connect(path):
    con=sqlite3.connect(path,timeout=30,isolation_level=None)
    con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA synchronous=FULL')
    con.execute('''CREATE TABLE IF NOT EXISTS receipts (
      seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, source TEXT NOT NULL,
      source_at TEXT NOT NULL, received_at TEXT NOT NULL, payload TEXT NOT NULL,
      previous_sha256 TEXT NOT NULL, row_sha256 TEXT NOT NULL,
      UNIQUE(kind,source_at))''')
    return con

def record(path,kind,payload,*,source,clock=None):
    """Record one point in time. Test clocks are injectable; CLI always uses UTC now."""
    if not source or not isinstance(source,str):raise ValueError('nonempty source required')
    at,normal=_validate(kind,payload)
    now=_utc(clock() if clock else datetime.now(timezone.utc))
    if now<at+(timedelta(hours=1) if kind=='bar' else timedelta(0)):
        raise ValueError('receipt precedes source observation or bar close')
    if now-at>timedelta(days=1):raise ValueError('historical backfill cannot masquerade as prospective receipt')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    con=_connect(path)
    try:
        con.execute('BEGIN IMMEDIATE')
        prev=con.execute('SELECT received_at,row_sha256 FROM receipts ORDER BY seq DESC LIMIT 1').fetchone()
        if prev and now<_utc(prev[0]):raise ValueError('receipt clock moved backwards')
        previous=prev[1] if prev else '0'*64
        source_at=at.isoformat();received=now.isoformat();body=json.dumps(normal,sort_keys=True,separators=(',',':'),allow_nan=False)
        digest=_digest(previous,kind,source,source_at,received,body)
        con.execute('INSERT INTO receipts(kind,source,source_at,received_at,payload,previous_sha256,row_sha256) VALUES (?,?,?,?,?,?,?)',(kind,source,source_at,received,body,previous,digest))
        con.commit();return {'kind':kind,'source_at':source_at,'available_at':received,'row_sha256':digest}
    except Exception:
        con.rollback();raise
    finally:con.close()

def export_verified(path,out):
    """Verify all receipts, then emit exact CSV inputs for the prospective gate."""
    con=_connect(path)
    try:rows=con.execute('SELECT kind,source,source_at,received_at,payload,previous_sha256,row_sha256 FROM receipts ORDER BY seq').fetchall()
    finally:con.close()
    previous='0'*64;bars=[];metrics=[]
    for kind,source,at,received,body,link,digest in rows:
        if link!=previous or _digest(link,kind,source,at,received,body)!=digest:raise ValueError('receipt chain integrity failure')
        payload=json.loads(body)
        if payload[BAR_FIELDS[0] if kind=='bar' else METRIC_FIELDS[0]]!=at:raise ValueError('source timestamp mismatch')
        (bars if kind=='bar' else metrics).append({**payload,'available_at':received})
        previous=digest
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    result={}
    for kind,items,fields,filename in [('bar',bars,BAR_FIELDS,'prospective_bars.csv'),('metric',metrics,METRIC_FIELDS,'prospective_metrics.csv')]:
        target=out/filename
        with target.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=(fields[0],'available_at',*fields[1:]),lineterminator='\n')
            writer.writeheader();writer.writerows(sorted(items,key=lambda x:x[fields[0]]))
        result[kind]={'rows':len(items),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    result['ledger_head_sha256']=previous
    (out/'receipt_manifest.json').write_text(json.dumps(result,indent=2))
    return result

# Versioned generic observations share the existing SQLite file. Legacy rows
# retain their original meaning and are never promoted to this stronger contract.
def canonical_observation(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def observation_hash(value):
    return hashlib.sha256(canonical_observation(value).encode()).hexdigest()


def _observation_db(path):
    con = _connect(path)
    con.execute('''CREATE TABLE IF NOT EXISTS observations_v2 (
        seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
        body TEXT NOT NULL, previous_hash TEXT NOT NULL, receipt_hash TEXT NOT NULL)''')
    for action in ('UPDATE', 'DELETE'):
        con.execute(f'''CREATE TRIGGER IF NOT EXISTS observations_v2_no_{action.lower()}
          BEFORE {action} ON observations_v2 BEGIN SELECT RAISE(ABORT, 'append-only'); END''')
    return con


def observation_snapshot(path):
    con = _observation_db(path)
    try:
        rows = con.execute('SELECT id,body,previous_hash,receipt_hash FROM observations_v2 ORDER BY seq').fetchall()
    finally:
        con.close()
    previous, result, prefixes = '0' * 64, {}, []
    for identity, body, link, digest in rows:
        if link != previous or observation_hash([link, body]) != digest:
            raise ValueError('observation chain integrity failure')
        item = json.loads(body)
        if item['id'] != identity or observation_hash(item['payload']) != item['payload_hash']:
            raise ValueError('payload identity/hash mismatch')
        result[identity] = item
        previous = digest
        prefixes.append(digest)
    return result, prefixes


def load_observations(path):
    return observation_snapshot(path)[0]


def append_observation(path, *, source, instrument, feature, event_time,
                       source_metric_at, received_at, payload, provenance,
                       dependencies=(), derived=False, clock=None, admission_check=None):
    """Trusted capture boundary; explicit clock injection is for tests only.

    All live callers obtain received_at immediately after consuming response
    bytes; available_at/computed_at are assigned here, never caller-supplied.
    Unsupported raw features are stored UNKNOWN, not admitted by default.
    """
    if not source or not instrument or not feature or not isinstance(provenance, dict) or not provenance:
        raise ValueError('missing provenance')
    event, metric, received = map(_utc, (event_time, source_metric_at, received_at))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    known = load_observations(path)
    now = _utc(clock() if clock else datetime.now(timezone.utc))
    if max(event, metric) > received or received > now or now - event > timedelta(days=1):
        raise ValueError('future observation or historical backfill')
    deps = list(dependencies)
    if len(set(deps)) != len(deps):
        raise ValueError('duplicate dependency')
    if deps and not derived:
        raise ValueError('raw observation cannot declare unchecked dependencies')
    available = now.isoformat() if feature == 'Price/OHLCV' and not derived else None
    if derived:
        values = [known.get(x, {}).get('available_at') for x in deps]
        available = max([now, *map(_utc, values)]).isoformat() if deps and all(values) else None
    identity = observation_hash([source, instrument, feature, event.isoformat(), metric.isoformat(), deps, derived])
    item = dict(id=identity, source=source, instrument=instrument, feature=feature,
                event_time=event.isoformat(), source_metric_at=metric.isoformat(),
                received_at=received.isoformat(), available_at=available,
                computed_at=now.isoformat() if derived else None,
                payload=payload, payload_hash=observation_hash(payload), provenance=provenance,
                dependencies=deps, derived=derived, recorded_at=now.isoformat())
    con = _observation_db(path)
    try:
        con.execute('BEGIN IMMEDIATE')
        existing = con.execute('SELECT body FROM observations_v2 WHERE id=?', (identity,)).fetchone()
        last = con.execute('SELECT body,receipt_hash FROM observations_v2 ORDER BY seq DESC LIMIT 1').fetchone()
        if admission_check is not None:
            admitted = _utc(admission_check())
            if admitted < now:
                raise ValueError('clock moved backwards during ledger admission')
            item['recorded_at'] = admitted.isoformat()
            if feature == 'Price/OHLCV' and not derived:
                item['available_at'] = admitted.isoformat()
            now = admitted
        if existing:
            old = json.loads(existing[0])
            if old['payload_hash'] != item['payload_hash']:
                raise ValueError('conflicting observation; no silent overwrite')
            con.rollback()
            return old
        if last and _utc(json.loads(last[0])['recorded_at']) > now:
            raise ValueError('clock moved backwards')
        previous = last[1] if last else '0' * 64
        body = canonical_observation(item)
        con.execute('INSERT INTO observations_v2(id,body,previous_hash,receipt_hash) VALUES (?,?,?,?)',
                    (identity, body, previous, observation_hash([previous, body])))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return item


def _price_closed(item):
    """REST closure evidence: server time sampled BEFORE the kline request."""
    p = item['provenance']
    if item['source'] != 'https://fapi.binance.com/fapi/v1/klines' or item['instrument'] != 'BTCUSDT':
        return False
    if p.get('contract') != 'binance-usdm-h1-rest-v1' or p.get('bar_closed') is not True:
        return False
    raw = json.loads(p['raw_klines'])
    server = json.loads(p['raw_server_time'])['serverTime']
    opened = int(item['payload']['open_time_ms'])
    row = next(r for r in raw if int(r[0]) == opened)
    close = opened + 3_600_000
    if opened % 3_600_000 or int(row[6]) != close - 1 or server < close:
        return False
    t = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc)
    if not (t(server) <= _utc(p['server_received_at']) <= _utc(p['klines_requested_at']) <= _utc(item['received_at'])):
        return False
    if _utc(item['event_time']) != t(close) or _utc(item['source_metric_at']) != t(int(row[6])):
        return False
    normalized = dict(time=t(opened).isoformat(), **{k:float(row[i]) for i,k in enumerate(['open','high','low','close','volume'], 1)})
    _validate('bar', normalized)
    return item['payload'] == dict(normalized, open_time_ms=opened, close_time_ms=int(row[6]))


def is_causally_available(path, observation_id, decision_at):
    """Only verified persisted observations qualify. UNKNOWN always fails closed."""
    try:
        return snapshot_causally_available(load_observations(path), observation_id, decision_at)
    except (ValueError, TypeError, KeyError, sqlite3.Error):
        return False


def snapshot_causally_available(known, observation_id, decision_at):
    """Gate for an already chain-verified snapshot; avoids repeated database scans."""
    try:
        decision = _utc(decision_at)
        def check(identity, visiting):
            if identity in visiting or identity not in known:
                return False
            item = known[identity]
            if not item['available_at'] or not item['provenance']:
                return False
            available = _utc(item['available_at'])
            if not (_utc(item['event_time']) <= _utc(item['received_at']) <= available <= decision):
                return False
            if _utc(item['source_metric_at']) > _utc(item['received_at']):
                return False
            if item['derived']:
                deps = item['dependencies']
                if not deps or not item['computed_at'] or not all(check(x, visiting | {identity}) for x in deps):
                    return False
                if any(known[x]['instrument'] != item['instrument'] for x in deps):
                    return False
                return available == max([_utc(item['computed_at']), *[_utc(known[x]['available_at']) for x in deps]])
            return item['feature'] == 'Price/OHLCV' and _price_closed(item)
        return check(observation_id, set())
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, StopIteration, sqlite3.Error, OverflowError):
        return False
