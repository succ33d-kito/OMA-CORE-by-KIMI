"""Synthetic transport only; no outcomes or strategy inputs."""
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from email.message import Message
import json
import pytest
from core.scientific import multi_market_capture as c

T=datetime(2020,1,1,tzinfo=timezone.utc)


def transport(monkeypatch,body,start):
    raw=json.dumps(body).encode()
    class Response:
        status=200
        headers=Message()
        headers['Content-Type']='application/json'
        headers['Content-Length']=str(len(raw))
        def read(self,n): return raw[:n]
        def geturl(self): return self.url
        def __enter__(self): return self
        def __exit__(self,*args): pass
    def http(url):
        r=Response(); r.url=url; return r
    monkeypatch.setattr(c,'_http',http)
    times=iter(start+timedelta(seconds=i) for i in range(6))
    monkeypatch.setattr(c,'_now',lambda:next(times))
    ticks=iter((10.,11.)); monkeypatch.setattr(c,'monotonic',lambda:next(ticks))


def freeze(tmp_path,monkeypatch):
    body={'symbols':[dict(symbol=s,status='TRADING',contractType='PERPETUAL',quoteAsset='USDT',marginAsset='USDT') for s in c.SYMBOLS]}
    transport(monkeypatch,body,T)
    return c.freeze_universe(tmp_path/'universe')


def rows():
    return [dict(symbol=s,bidPrice='100',askPrice='101',bidQty='2',askQty='3',time=1577836800000,lastUpdateId=i) for i,s in enumerate(c.SYMBOLS)]


def cycle(tmp_path,monkeypatch,body=None,**kwargs):
    transport(monkeypatch,rows() if body is None else body,T+timedelta(hours=1))
    return c.capture_cycle(tmp_path/'cycle',tmp_path/'universe',**kwargs)


def test_frozen_determinism_reopen_and_complete(tmp_path,monkeypatch):
    u=freeze(tmp_path,monkeypatch)
    assert c.load_universe(tmp_path/'universe')==u
    assert u.symbols==c.SYMBOLS and u.role=='PILOT'
    with pytest.raises(FrozenInstanceError): u.symbols=('OTHER',)
    result=cycle(tmp_path,monkeypatch)
    assert c.load_cycle(tmp_path/'cycle',tmp_path/'universe')==result
    assert tuple(m.symbol for m in result.members)==u.symbols
    assert result.completeness=='COMPLETE' and result.missing==()
    assert result.capture_span_seconds==2
    assert result.semantics=='SINGLE_HTTP_NOT_SIMULTANEOUS'
    for m in result.members:
        assert m.role=='PILOT' and m.exchange_at==T
        assert m.received_at==result.received_at and m.available_at==result.completed_at
        assert m.raw_commitment and m.observation_id
        assert json.loads(m.wire_json)['lastUpdateId']==m.source_update_id
        assert not hasattr(m,'outcome') and not hasattr(m,'signal')
    with pytest.raises(FrozenInstanceError): result.members=()


def test_missing_member_no_fill(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch)
    result=cycle(tmp_path,monkeypatch,rows()[1:])
    assert result.completeness=='INCOMPLETE'
    assert result.missing==(c.SYMBOLS[0],) and len(result.members)==4


@pytest.mark.parametrize('mode',['unknown','duplicate','crossed','future','boolean_id'])
def test_wire_fail_closed(tmp_path,monkeypatch,mode):
    freeze(tmp_path,monkeypatch); body=rows()
    if mode=='unknown': body[0]['futurePrice']='999'
    if mode=='duplicate': body.append(body[0])
    if mode=='crossed': body[0]['bidPrice']='102'
    if mode=='future': body[0]['time']=2577836800000
    if mode=='boolean_id': body[0]['lastUpdateId']=True
    with pytest.raises(ValueError): cycle(tmp_path,monkeypatch,body)
    assert not (tmp_path/'cycle'/'cycle.json').exists()


def test_no_backfill_and_naive_slot(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch)
    for slot in (T,T.replace(tzinfo=None)):
        with pytest.raises((ValueError,TypeError)):
            cycle(tmp_path,monkeypatch,kind='H1',slot=slot)
    assert not (tmp_path/'cycle').exists()


def test_duplicate_directory_cannot_overwrite(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); cycle(tmp_path,monkeypatch,kind='H1',slot=T+timedelta(hours=1))
    before={p.name:p.read_bytes() for p in (tmp_path/'cycle').iterdir()}
    with pytest.raises(FileExistsError): cycle(tmp_path,monkeypatch,kind='H1',slot=T+timedelta(hours=1))
    assert before=={p.name:p.read_bytes() for p in (tmp_path/'cycle').iterdir()}


def test_corrupted_raw_and_universe_rejected(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); cycle(tmp_path,monkeypatch)
    raw=tmp_path/'cycle'/'response.raw'; original=raw.read_bytes(); raw.write_bytes(original+b' ')
    with pytest.raises(ValueError): c.load_cycle(tmp_path/'cycle',tmp_path/'universe')
    raw.write_bytes(original)
    path=tmp_path/'universe'/'universe.json'
    saved=json.loads(path.read_bytes()); saved['manifest']['role']='DISCOVERY'; path.write_bytes(c._json(saved))
    with pytest.raises(ValueError): c.load_cycle(tmp_path/'cycle',tmp_path/'universe')


def test_universe_commitment_independent_of_dict_order():
    assert c.commitment({'a':1,'b':2})==c.commitment({'b':2,'a':1})


def test_no_public_outcome_or_factual_overrides(tmp_path):
    for key in ('outcome','pnl','bid','available_at','received_at'):
        with pytest.raises(TypeError): c.capture_cycle(tmp_path,tmp_path,**{key:1})
