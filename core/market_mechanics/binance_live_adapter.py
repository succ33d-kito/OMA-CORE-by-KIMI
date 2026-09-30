"""Optional Binance USD-M public-market adapter; never places orders.

Returns complete 5m metrics only when all endpoint periods align. The caller
records actual receipt time after the *last* response, not response timestamps.
"""
import hashlib,json
from datetime import datetime,timezone,timedelta
from math import isfinite

BASE='https://fapi.binance.com'
METRIC_ENDPOINTS={
 'oi':'/futures/data/openInterestHist',
 'top_account':'/futures/data/topLongShortAccountRatio',
 'top_position':'/futures/data/topLongShortPositionRatio',
 'global':'/futures/data/globalLongShortAccountRatio',
 'taker':'/futures/data/takerlongshortRatio',
}

def _period_end(ms,*,start_label=False):
    x=datetime.fromtimestamp(int(ms)/1000,timezone.utc)
    aligned=datetime.fromtimestamp(round(x.timestamp()/300)*300,timezone.utc)
    if abs((aligned-x).total_seconds())>30:raise ValueError('5m source timestamp not aligned within 30 seconds')
    return aligned+timedelta(minutes=5) if start_label else aligned

def normalize_bundle(items):
    """Normalize provider-specific fields and start/end timestamp semantics."""
    if set(items)!=set(METRIC_ENDPOINTS):raise ValueError('incomplete metrics bundle')
    ends={key:_period_end(value['timestamp'],start_label=(key=='taker')) for key,value in items.items()}
    if len(set(ends.values()))!=1:raise ValueError('mixed 5m periods; retry without filling')
    end=next(iter(ends.values()))
    def positive(value):
        x=float(value)
        if not isfinite(x) or x<=0:raise ValueError('invalid provider metric')
        return x
    payload={'timestamp':(end-timedelta(microseconds=1)).isoformat(),
      'sum_open_interest':positive(items['oi']['sumOpenInterest']),
      'sum_open_interest_value':positive(items['oi']['sumOpenInterestValue']),
      'count_toptrader_long_short_ratio':positive(items['top_account']['longShortRatio']),
      'sum_toptrader_long_short_ratio':positive(items['top_position']['longShortRatio']),
      'count_long_short_ratio':positive(items['global']['longShortRatio']),
      'sum_taker_long_short_vol_ratio':positive(items['taker']['buySellRatio'])}
    return payload

def latest_closed_kline(rows,now):
    now=now.astimezone(timezone.utc)
    valid=[]
    for row in rows:
        if len(row)<6:raise ValueError('malformed kline')
        start=datetime.fromtimestamp(int(row[0])/1000,timezone.utc)
        if start+timedelta(hours=1)<=now:valid.append(row)
    if not valid:raise ValueError('no fully closed H1 bar')
    row=max(valid,key=lambda x:int(x[0]));start=datetime.fromtimestamp(int(row[0])/1000,timezone.utc)
    return {'time':start.isoformat(),'open':float(row[1]),'high':float(row[2]),'low':float(row[3]),'close':float(row[4]),'volume':float(row[5])}

def fetch_once(session,*,api_key=None,clock=None,timeout=8):
    """Fetch one recent bar and one complete metrics bundle; no retries/backfill."""
    now=clock() if clock else datetime.now(timezone.utc)
    headers={'X-MBX-APIKEY':api_key} if api_key else {}
    def get(path,params):
        r=session.get(BASE+path,params=params,headers=headers,timeout=timeout)
        if r.status_code==451:raise RuntimeError('Binance HTTP 451: location restricted; no proxy or backfill fallback')
        r.raise_for_status();return r.json()
    bar=latest_closed_kline(get('/fapi/v1/klines',{'symbol':'BTCUSDT','interval':'1h','limit':3}),now)
    raw={}
    for key,path in METRIC_ENDPOINTS.items():
        result=get(path,{'symbol':'BTCUSDT','period':'5m','limit':1})
        if not isinstance(result,list) or not result:raise ValueError('empty metrics endpoint '+key)
        raw[key]=result[-1]
    metric=normalize_bundle(raw)
    material=json.dumps(raw,sort_keys=True,separators=(',',':')).encode()
    return {'bar':bar,'metric':metric,'raw_metrics_sha256':hashlib.sha256(material).hexdigest(),'raw_metrics':raw}


def capture_price_receipt(session, ledger, *, clock=None, timeout=10, expected_event_time=None):
    """Two public requests, price only; no retries, metrics, history or trading."""
    from core.scientific.prospective_receipts import append_observation, _utc
    utc_now = clock or (lambda: datetime.now(timezone.utc))
    def request(path, params=None):
        response = session.get(BASE + path, params=params, timeout=timeout)
        if response.status_code == 451:
            raise RuntimeError('Binance HTTP 451; no proxy or alternate-provider fallback')
        response.raise_for_status()
        raw = response.text  # Consume bytes before assigning received_at.
        received = _utc(utc_now())
        return raw, received
    server_raw, server_received = request('/fapi/v1/time')
    server_ms = int(json.loads(server_raw)['serverTime'])
    if datetime.fromtimestamp(server_ms/1000, timezone.utc) > server_received:
        raise ValueError('server clock ahead of local receipt clock')
    requested = _utc(utc_now())
    if requested < server_received:
        raise ValueError('clock moved backwards')
    raw, received = request('/fapi/v1/klines', {'symbol':'BTCUSDT','interval':'1h','limit':3})
    rows = json.loads(raw)
    if received < requested:
        raise ValueError('clock moved backwards')
    closed = [r for r in rows if len(r) >= 7 and int(r[0]) + 3_600_000 <= server_ms]
    if not closed:
        raise ValueError('no closed bar supported by server-time evidence')
    row = max(closed, key=lambda r:int(r[0]))
    start = datetime.fromtimestamp(int(row[0])/1000, timezone.utc)
    if expected_event_time is not None and start + timedelta(hours=1) != _utc(expected_event_time):
        raise ValueError('scheduled slot mismatch; no historical backfill')
    payload = latest_closed_kline([row], datetime.fromtimestamp(server_ms/1000, timezone.utc))
    payload.update(open_time_ms=int(row[0]), close_time_ms=int(row[6]))
    return append_observation(ledger, source=BASE+'/fapi/v1/klines', instrument='BTCUSDT',
        feature='Price/OHLCV', event_time=start+timedelta(hours=1),
        source_metric_at=datetime.fromtimestamp(int(row[6])/1000, timezone.utc),
        received_at=received, payload=payload, clock=utc_now,
        provenance={'contract':'binance-usdm-h1-rest-v1','bar_closed':True,
                    'raw_server_time':server_raw,'raw_klines':raw,
                    'server_received_at':server_received.isoformat(),
                    'klines_requested_at':requested.isoformat(),
                    'clock':'host UTC wall clock; decision must use the same clock domain'})
