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
