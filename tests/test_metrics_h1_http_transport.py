"""Real Requests preparation, fake HTTPAdapter.send; external sockets blocked."""
from datetime import datetime, timedelta, timezone
import json
import socket
from urllib.parse import urlsplit

import pytest
import requests
from core.scientific import metrics_h1_http_transport as transport
from core.scientific import metrics_h1_live_adapter as live
from core.scientific import metrics_h1_activation as activation

PARAMS={'symbol':'BTCUSDT','period':'5m','limit':5}
URL='https://fapi.binance.com/futures/data/openInterestHist'


@pytest.fixture
def http(monkeypatch):
    state={'calls':[], 'closed':0, 'status':200, 'body':b' [ { "raw": 1 } ]\n', 'error':None}
    def forbidden(*args,**kwargs): raise AssertionError('real network forbidden')
    monkeypatch.setattr(socket.socket,'connect',forbidden)
    monkeypatch.setattr(socket,'create_connection',forbidden)
    def send(adapter,request,**kwargs):
        state['calls'].append((request,kwargs,adapter.max_retries.total))
        if state['error']: raise state['error']
        response=requests.Response(); response.status_code=state['status']
        response.url=request.url; response._content=state['body']; response._content_consumed=True
        response.request=request
        if response.status_code==302: response.headers['Location']='https://evil.example/'
        return response
    monkeypatch.setattr(requests.adapters.HTTPAdapter,'send',send)
    close=requests.Session.close
    def closing(session):
        state['closed']+=1
        assert session.trust_env is False
        close(session)
    monkeypatch.setattr(requests.Session,'close',closing)
    return state


@pytest.mark.parametrize('endpoint',list(transport.METRIC_ENDPOINTS.values()))
def test_allowed_endpoints_exact_bytes_and_prepared_url(http,endpoint):
    url=transport.BASE+endpoint
    result=transport.public_http_transport(url,params=PARAMS,timeout=0.75)
    assert result==(200,url+'?symbol=BTCUSDT&period=5m&limit=5',http['body'])
    req,kw,retries=http['calls'][0]
    assert req.method=='GET' and req.body is None
    assert kw['timeout']==0.75 and kw['proxies']=={} and retries==0
    assert not {'Authorization','Cookie','X-MBX-APIKEY'} & set(req.headers)
    assert len(http['calls'])==http['closed']==1


@pytest.mark.parametrize('url',['http://fapi.binance.com/futures/data/openInterestHist','https://api.binance.com/futures/data/openInterestHist','https://evil.example/futures/data/openInterestHist','https://127.0.0.1/futures/data/openInterestHist','https://user:pass@fapi.binance.com/futures/data/openInterestHist',URL.replace('.com','.com:444'),URL+'#fragment',URL+'?symbol=BTCUSDT','https://fapi.binance.com/fapi/v1/order','https://fapi.binance.com/fapi/v1/account','https://fapi.binance.com/fapi/v1/listenKey'])
def test_url_rejected_before_session(http,url):
    with pytest.raises(ValueError): transport.public_http_transport(url,params=PARAMS,timeout=1)
    assert http['calls']==[] and http['closed']==0


@pytest.mark.parametrize('params',[{},dict(PARAMS,symbol='ETHUSDT'),dict(PARAMS,period='1h'),dict(PARAMS,limit=1),dict(PARAMS,limit=True),dict(PARAMS,limit=5.0),dict(PARAMS,extra='x'),[('symbol','BTCUSDT')]])
def test_params_rejected(http,params):
    with pytest.raises(ValueError): transport.public_http_transport(URL,params=params,timeout=1)
    assert http['calls']==[]


@pytest.mark.parametrize('timeout',[True,False,0,-1,float('nan'),float('inf'),'1',None,8.1])
def test_timeout_rejected(http,timeout):
    with pytest.raises(ValueError): transport.public_http_transport(URL,params=PARAMS,timeout=timeout)
    assert http['calls']==[]


@pytest.mark.parametrize('allow',[True,0,None])
def test_redirect_flag_exact_false(http,allow):
    with pytest.raises(ValueError): transport.public_http_transport(URL,params=PARAMS,timeout=1,allow_redirects=allow)
    assert http['calls']==[]


@pytest.mark.parametrize('status',[302,429,451,500])
def test_status_preserved_no_retry_redirect(http,status):
    http['status']=status
    assert transport.public_http_transport(URL,params=PARAMS,timeout=1)[0]==status
    assert len(http['calls'])==http['closed']==1


@pytest.mark.parametrize('exception',[requests.Timeout,requests.ConnectionError,requests.exceptions.SSLError])
def test_transport_exception_propagates_and_closes(http,exception):
    http['error']=exception('fake failure')
    with pytest.raises(exception): transport.public_http_transport(URL,params=PARAMS,timeout=1)
    assert len(http['calls'])==http['closed']==1


def test_environment_not_inherited(http,monkeypatch):
    for key in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY'):
        monkeypatch.setenv(key,'http://127.0.0.1:9')
    monkeypatch.setenv('BINANCE_API_KEY','must-not-read')
    transport.public_http_transport(URL,params=PARAMS,timeout=1)
    req,kwargs,_=http['calls'][0]
    assert kwargs['proxies']=={} and 'X-MBX-APIKEY' not in req.headers


def test_fake_e2e_real_requests_five_calls(tmp_path,http,monkeypatch):
    s=datetime(2026,10,11,13,tzinfo=timezone.utc)
    repo=tmp_path/'repo'; repo.mkdir(); state=tmp_path/'metrics-h1-v1'
    activation.activate(state,repo_root=repo,now=s-timedelta(minutes=20),dataset_role='PILOT')
    original=requests.adapters.HTTPAdapter.send
    bodies={}
    def send(adapter,request,**kwargs):
        key=next(k for k,p in transport.METRIC_ENDPOINTS.items() if p==urlsplit(request.url).path)
        row={'symbol':'BTCUSDT','timestamp':int(s.timestamp()*1000)-(300000 if key=='taker' else 0)}
        row.update({'sumOpenInterest':'100','sumOpenInterestValue':'10000'} if key=='oi' else {'buySellRatio':'1.4'} if key=='taker' else {'longShortRatio':'1.2'})
        bodies[key]=json.dumps([row],indent=2).encode()
        http['body']=bodies[key]
        return original(adapter,request,**kwargs)
    monkeypatch.setattr(requests.adapters.HTTPAdapter,'send',send)
    result=live.run_once(state,repo_root=repo,transport=transport.public_http_transport,clock=lambda:s+timedelta(seconds=180))
    assert result['status']=='SUCCESS' and len(http['calls'])==http['closed']==5
    capture=state/'attempts'/'20261011T130000Z'/'capture'
    assert (capture/'receipt.json').is_file() and (capture/'available.json').is_file()
    for key,raw in bodies.items(): assert (capture/'raw'/(key+'.json')).read_bytes()==raw


@pytest.mark.parametrize('suffix',['','?symbol=ETHUSDT&period=5m&limit=5','?symbol=BTCUSDT&period=1h&limit=5','?symbol=BTCUSDT&period=5m&limit=5&extra=1','?symbol=BTCUSDT&period=5m&limit=5#x'])
def test_adapter_rejects_unauthenticated_final_query(tmp_path,http,suffix):
    s=datetime(2026,10,11,13,tzinfo=timezone.utc)
    def fake(url,**kwargs): return 200,url+suffix,b'[]'
    with pytest.raises(ValueError,match='HTTP status/source'):
        live.capture_bundle(capture_directory=tmp_path/'capture',slot=s,expected_source_period_end=s,
            target_at=s+timedelta(seconds=180),deadline_at=s+timedelta(seconds=300),attempt_started_at=s+timedelta(seconds=180),
            clock=lambda:s+timedelta(seconds=180),transport=fake,dataset_role='PILOT',activation_id='a'*64)
