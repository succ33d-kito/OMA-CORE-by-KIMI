"""Offline exact-byte fixtures; socket access is forbidden."""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import socket
from urllib.parse import urlencode

import pytest
from core.scientific import metrics_h1_activation as activation
from core.scientific import metrics_h1_live_adapter as adapter

S = datetime(2026,10,11,13,tzinfo=timezone.utc)
END = int(S.timestamp()*1000)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError('external network forbidden')
    monkeypatch.setattr(socket.socket,'connect',forbidden)
    monkeypatch.setattr(socket,'create_connection',forbidden)


def rows(key):
    stamp = END - (300000 if key=='taker' else 0)
    fields = {'sumOpenInterest':'100','sumOpenInterestValue':'10000'} if key=='oi' else {'buySellRatio':'1.4'} if key=='taker' else {'longShortRatio':'1.2'}
    # Desired period is deliberately NOT last; adjacent periods must not win.
    return [dict(symbol='BTCUSDT',timestamp=stamp,**fields), dict(symbol='BTCUSDT',timestamp=stamp+300000,**fields)]


class Transport:
    def __init__(self):
        self.raw={k:json.dumps(rows(k),indent=2).encode() for k in adapter.METRIC_ENDPOINTS}
        self.calls=[]; self.status=200; self.final=None; self.error=None
    def __call__(self,url,**kwargs):
        self.calls.append((url,kwargs))
        if self.error: raise self.error
        key=next(k for k,v in adapter.METRIC_ENDPOINTS.items() if url.endswith(v))
        return self.status, self.final or url + '?' + urlencode(kwargs['params']), self.raw[key]


def capture(tmp_path, transport=None, clock=None, **changes):
    args=dict(capture_directory=tmp_path/'capture',slot=S,expected_source_period_end=S,
              target_at=S+timedelta(seconds=180),deadline_at=S+timedelta(seconds=300),
              attempt_started_at=S+timedelta(seconds=180),clock=clock or (lambda:S+timedelta(seconds=180)),
              transport=transport or Transport(),dataset_role='PILOT',activation_id='a'*64)
    args.update(changes)
    return adapter.capture_bundle(**args)


def test_exact_bundle_and_independent_commitments(tmp_path):
    transport=Transport(); result=capture(tmp_path,transport)
    root=tmp_path/'capture'; receipt=json.loads((root/'receipt.json').read_bytes())
    marker=json.loads((root/'available.json').read_bytes())
    material={}
    for key,endpoint in adapter.METRIC_ENDPOINTS.items():
        raw=(root/'raw'/(key+'.json')).read_bytes()
        assert raw==transport.raw[key]
        assert hashlib.sha256(raw).hexdigest()==receipt['components'][key]['raw_sha256']
        material[endpoint]=base64.b64encode(raw).decode('ascii')
        assert receipt['components'][key]['source_period_end']==S.isoformat()
    canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    assert hashlib.sha256(canonical(material)).hexdigest()==result['raw_bundle_sha256']
    identity=receipt.pop('receipt_id')
    assert hashlib.sha256(canonical(receipt)).hexdigest()==identity==marker['receipt_id']==result['capture_receipt_id']
    assert marker['available_at']==result['available_at']
    assert result['slot']==result['source_period_end']==S.isoformat()
    assert receipt['normalized_metrics']=={'timestamp':(S-timedelta(microseconds=1)).isoformat(),'sum_open_interest':100.0,'sum_open_interest_value':10000.0,'count_toptrader_long_short_ratio':1.2,'sum_toptrader_long_short_ratio':1.2,'count_long_short_ratio':1.2,'sum_taker_long_short_vol_ratio':1.4}
    assert receipt['components']['taker']['timestamp_label']=='START'
    assert len(transport.calls)==5
    for url,kw in transport.calls:
        assert kw['params']=={'symbol':'BTCUSDT','period':'5m','limit':5}
        assert kw['allow_redirects'] is False and 0<kw['timeout']<=8


@pytest.mark.parametrize('key',list(adapter.METRIC_ENDPOINTS))
@pytest.mark.parametrize('offset',[-300000,300000])
def test_every_component_requires_exact_period(tmp_path,key,offset):
    t=Transport(); row=rows(key)[0]; row['timestamp']+=offset; t.raw[key]=json.dumps([row]).encode()
    with pytest.raises(ValueError,match='exact source period'): capture(tmp_path,t)
    assert not (tmp_path/'capture'/'receipt.json').exists()
    assert not (tmp_path/'capture'/'available.json').exists()
    assert len(t.calls)<=5


@pytest.mark.parametrize('case',['malformed','empty','missing','nonnumeric','nan','infinite','zero','negative','boolean','wrong_symbol','duplicate','duplicate_key'])
def test_malformed_evidence_fails(tmp_path,case):
    t=Transport(); row=rows('oi')[0]
    if case=='missing': row.pop('sumOpenInterest')
    if case in {'nonnumeric','nan','infinite','zero','negative','boolean'}:
        row['sumOpenInterest']={'nonnumeric':'abc','nan':'NaN','infinite':'Infinity','zero':0,'negative':-1,'boolean':True}[case]
    if case=='wrong_symbol': row['symbol']='ETHUSDT'
    raw=json.dumps([row,row] if case=='duplicate' else [row]).encode()
    if case=='malformed': raw=b'{'
    if case=='empty': raw=b'[]'
    if case=='duplicate_key': raw=b'[{"symbol":"BTCUSDT","symbol":"ETHUSDT"}]'
    t.raw['oi']=raw
    with pytest.raises((ValueError,KeyError)): capture(tmp_path,t)
    assert not (tmp_path/'capture'/'receipt.json').exists()
    assert not (tmp_path/'capture'/'available.json').exists()


@pytest.mark.parametrize('status',[301,451,500])
def test_http_failure_no_retry(tmp_path,status):
    t=Transport(); t.status=status
    with pytest.raises(ValueError,match='HTTP'): capture(tmp_path,t)
    assert len(t.calls)==1
    assert not (tmp_path/'capture'/'available.json').exists()


def test_wrong_source_and_timeout(tmp_path):
    t=Transport(); t.final='https://other.example/metrics'
    with pytest.raises(ValueError,match='source'): capture(tmp_path,t)
    t=Transport(); t.error=TimeoutError('fixture timeout')
    another=tmp_path/'another'; another.mkdir()
    with pytest.raises(TimeoutError): capture(another,t)
    assert len(t.calls)==1


@pytest.mark.parametrize('seconds,valid',[(179,False),(180,True),(299.999,True),(300,False),(301,False)])
def test_start_window(tmp_path,seconds,valid):
    now=S+timedelta(seconds=seconds); t=Transport()
    if valid: assert capture(tmp_path,t,clock=lambda:now,attempt_started_at=now)['status']=='SUCCESS'
    else:
        with pytest.raises(ValueError): capture(tmp_path,t,clock=lambda:now,attempt_started_at=now)
        assert t.calls==[]


def test_late_final_response_preserves_partial_raw_only(tmp_path):
    t=Transport(); count=0
    def clock():
        nonlocal count
        count+=1
        return S+timedelta(seconds=301 if count>=11 else 180)
    with pytest.raises(ValueError,match='deadline'): capture(tmp_path,t,clock=clock)
    assert len(t.calls)==5
    assert (tmp_path/'capture'/'raw'/'oi.json').exists()
    assert not (tmp_path/'capture'/'receipt.json').exists()
    assert not (tmp_path/'capture'/'available.json').exists()


@pytest.mark.parametrize('naive',[False,True])
def test_invalid_clock(tmp_path,naive):
    values=iter([S+timedelta(seconds=180),S.replace(tzinfo=None) if naive else S+timedelta(seconds=179)])
    with pytest.raises(ValueError): capture(tmp_path,clock=lambda:next(values))
    assert not (tmp_path/'capture'/'available.json').exists()


def test_wrong_requested_period_no_transport(tmp_path):
    t=Transport()
    with pytest.raises(ValueError,match='period'): capture(tmp_path,t,expected_source_period_end=S-timedelta(hours=1))
    assert t.calls==[]


def test_raw_tamper_before_receipt_rejected(tmp_path,monkeypatch):
    original=adapter._write
    def write(path,raw):
        original(path,raw)
        if path.name=='taker.json': (path.parent/'oi.json').write_bytes(b'[]')
    monkeypatch.setattr(adapter,'_write',write)
    with pytest.raises(ValueError,match='evidence mismatch'): capture(tmp_path)
    assert not (tmp_path/'capture'/'receipt.json').exists()


def test_marker_waits_for_verified_receipt_and_late_persistence_fails(tmp_path,monkeypatch):
    original=adapter._write
    late=False
    def write(path,raw):
        nonlocal late
        if path.name=='available.pending':
            assert (path.parent/'receipt.json').is_file()
            late=True
        original(path,raw)
    monkeypatch.setattr(adapter,'_write',write)
    with pytest.raises(ValueError,match='deadline'):
        capture(tmp_path,clock=lambda:S+timedelta(seconds=301 if late else 180))
    assert not (tmp_path/'capture'/'available.json').exists()
    assert (tmp_path/'capture'/'available.pending').exists()  # Forensics, not admission.


def test_runner_integration_no_retry_or_ledger(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); state=tmp_path/'metrics-h1-v1'
    activation.activate(state,repo_root=repo,now=S-timedelta(minutes=20),dataset_role='PILOT')
    t=Transport(); now=lambda:S+timedelta(seconds=180)
    assert adapter.run_once(state,repo_root=repo,transport=t,clock=now)['status']=='SUCCESS'
    assert adapter.run_once(state,repo_root=repo,transport=t,clock=now)['status']=='NOT_DUE'
    assert len(t.calls)==5 and not list(state.rglob('*.db'))
    assert not (state/'runtime').exists()


def test_failure_integration_and_future_slot(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); state=tmp_path/'metrics-h1-v1'
    activation.activate(state,repo_root=repo,now=S-timedelta(minutes=20),dataset_role='PILOT')
    t=Transport(); t.error=TimeoutError()
    result=adapter.run_once(state,repo_root=repo,transport=t,clock=lambda:S+timedelta(seconds=180))
    assert result['status']=='FAILED'
    assert not list(state.rglob('receipt.json')) and not list(state.rglob('available.json'))
    assert adapter.run_once(state,repo_root=repo,transport=t,clock=lambda:S+timedelta(seconds=180))['status']=='NOT_DUE'
    assert len(t.calls)==1


def test_frozen_runner_and_activation_unchanged():
    repo=Path(__file__).resolve().parents[1]
    for file,digest in {'core/scientific/metrics_h1_runner.py':'59589264d61532d6129a475b46c15c08c09456eb5e48b48dc480092aef68e735','core/scientific/metrics_h1_activation.py':'d50b2c6ec8fc7e8335df9544746d9ad20c2dd0a20d5c25a1be845315d267069c',**activation._FROZEN}.items():
        assert hashlib.sha256((repo/file).read_bytes()).hexdigest()==digest
