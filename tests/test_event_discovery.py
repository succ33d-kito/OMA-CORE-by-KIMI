"""Synthetic HTTP fixtures are restricted to temporary journals, never live state."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.error import HTTPError,URLError
import hashlib
import inspect
import json
import sqlite3
import pytest
from core.scientific import event_discovery as d, real_event_receipt as r
from core.scientific.event_direction_operator import activate
from core.scientific.nuisance_pilot_contracts import DatasetRole,digest
from core.scientific.nuisance_pilot_sampling import Relation,ShockEvidence

T=datetime(2020,1,1,10,tzinfo=timezone.utc)
BASE='https://www.sec.gov/newsroom/press-releases/'


def feed(*ids):
    return ('<rss version="2.0"><channel><title>Press Releases</title>'+''.join(
        '<item><guid>'+i+'</guid><title>SEC '+i+'</title><link>'+BASE+i+'</link><pubDate>Mon, 01 Jan 1990 00:00:00 GMT</pubDate></item>' for i in ids)+'</channel></rss>').encode()


@pytest.fixture
def setup(tmp_path,monkeypatch):
    state=dict(now=T,feed=feed('old'),body=b'Bitcoin announcement. Full document.',calls=[],error=None)
    monkeypatch.setattr(r,'_now',lambda:state['now'])
    activate(tmp_path/'operator',tmp_path/'source.sqlite',role=DatasetRole.PILOT)
    state['now']+=timedelta(seconds=1)
    authority=d.SourceDiscoveryAuthorityV1.activate(tmp_path/'discovery',tmp_path/'operator',role=DatasetRole.PILOT)
    def fetch(url,*,feed):
        state['calls'].append(url)
        state['now']+=timedelta(milliseconds=1)
        if state['error'] and (feed or state.get('doc_error')): raise state['error']
        if not feed and state.get('doc_error'): raise URLError('document failed')
        return (state['feed'] if feed else state['body']),state['now'],('application/rss+xml' if feed else 'text/plain')
    monkeypatch.setattr(d,'_fetch',fetch)
    return authority,state


def poll(a,s,*ids):
    s['now']+=timedelta(minutes=5)
    if ids: s['feed']=feed(*ids)
    return a.poll()


def captured(a,s):
    poll(a,s,'old');poll(a,s,'old','new')
    return r.RealEventStore(a.source_path).receipt(d.inbox(a.root)[0]['receipt_id'])


def test_authority_scope_and_no_caller_clock(setup):
    a,s=setup
    assert a.status()['role']=='PILOT' and a.status()['contract_hash']==d.digest(d.CONTRACT)
    assert 'at' not in inspect.signature(d.SourceDiscoveryAuthorityV1.activate).parameters
    assert a.activation['at']==(T+timedelta(seconds=1)).isoformat()
    with pytest.raises((FileExistsError,ValueError)):
        d.SourceDiscoveryAuthorityV1.activate(a.root,a.activation['data']['operator_root'],role=DatasetRole.PILOT)


@pytest.mark.parametrize('role',[DatasetRole.DISCOVERY,DatasetRole.CONFIRMATION,'PILOT'])
def test_wrong_role(setup,role):
    a,_=setup
    with pytest.raises(ValueError): d.SourceDiscoveryAuthorityV1.activate(a.root,a.root,role=role)


def test_corrupt_authority_rejected(setup):
    a,_=setup
    with sqlite3.connect(a.path) as c: c.execute("UPDATE event_journal SET body=replace(body,'300','301') WHERE seq=1")
    with pytest.raises(ValueError): d.SourceDiscoveryAuthorityV1(a.root)


def test_initial_watermark_excludes_all_forever(setup):
    a,s=setup
    result=poll(a,s,'old','old2')
    assert result['baseline_count']==2 and result['receipts']==0 and result['new_documents']==0
    assert s['calls']==[d.ENDPOINT]
    poll(a,s,'old2','old');assert d.inbox(a.root)==[]
    poll(a,s,'new');poll(a,s,'old')
    assert a.status()['receipts']==1


def test_duplicate_and_multiple_documents(setup):
    a,s=setup;poll(a,s,'old')
    result=poll(a,s,'old','a','b')
    assert result['new_documents']==2 and result['receipts']==2
    before=d.inbox(a.root)
    poll(a,s,'b','a','old')
    assert d.inbox(a.root)==before


@pytest.mark.parametrize('url',['https://evil.test/a','https://www.sec.gov/other/a',BASE+'../a',BASE+'a?b=1',BASE+'%2e%2e/a',BASE+'a#b','http://www.sec.gov/newsroom/press-releases/a','https://www.sec.gov:443/newsroom/press-releases/a'])
def test_url_scope(url):
    with pytest.raises(ValueError,match='INVALID_SCOPE'): d._url(url)


def test_arbitrary_same_host_not_discovered(setup):
    a,s=setup;poll(a,s,'old')
    with pytest.raises(ValueError): d._capture(a,dict(kind='discovery',data={'item':{'link':BASE+'arbitrary'}}),{})
    with pytest.raises(ValueError): r.RealEventStore(a.source_path).capture('arbitrary','v1',DatasetRole.PILOT)


def test_redirect_rejected_without_second_request():
    with pytest.raises(ValueError): d._NoRedirect().redirect_request(None,None,302,'',{},'https://evil.test/')


def test_timestamp_publication_metadata_only(setup):
    a,s=setup;receipt=captured(a,s)
    assert receipt.received_at.year==2020 and receipt.received_at<=receipt.available_at
    assert 'received_at' not in inspect.signature(a.poll).parameters
    discovery=next(x for x in a.journal._rows() if x['kind']=='discovery')
    assert datetime.fromisoformat(discovery['data']['first_seen_at'])<receipt.received_at


def test_failure_then_success_no_backdating(setup):
    a,s=setup;s['error']=URLError('offline')
    assert poll(a,s)['last_status']=='NETWORK_FAILURE'
    s['error']=None
    result=poll(a,s,'old')
    assert result['baseline_count']==1 and result['receipts']==0
    results=[x for x in a.journal._rows() if x['kind']=='result']
    assert len(results)==2 and results[0]['data']['status']=='NETWORK_FAILURE'


def test_document_revision_preserves_original(setup):
    a,s=setup;first=captured(a,s);s['body']=b'Bitcoin revised announcement.'
    poll(a,s,'old','new');rows=d.inbox(a.root)
    assert len(rows)==2 and rows[0]['content']==first.content
    store=r.RealEventStore(a.source_path);last=store.receipt(rows[-1]['receipt_id'])
    assert last.revision_id!=first.revision_id and last.document_id==first.document_id
    assert hashlib.sha256(last.content.encode()).hexdigest()==last.content_hash
    s['body']=first.content.encode();poll(a,s,'old','new')
    assert len(d.inbox(a.root))==3


def test_fetch_failure_no_fake_receipt(setup):
    a,s=setup;poll(a,s,'old');s['doc_error']=True
    result=poll(a,s,'old','new')
    assert result['new_documents']==1 and result['receipts']==0 and result['last_status']=='DOCUMENT_FETCH_FAILURE'
    s['doc_error']=False;poll(a,s,'old','new')
    assert a.status()['new_documents']==1 and a.status()['receipts']==1


def test_no_legacy_bypass(setup):
    a,s=setup;receipt=captured(a,s);store=r.RealEventStore(a.source_path)
    with pytest.raises(ValueError,match='scoped discovery'): store.capture(receipt.source,'arbitrary',DatasetRole.PILOT)
    with pytest.raises(ValueError,match='frozen'): store.authorize_source('extra','v1',BASE+'extra',r.ContentKind.FULL_DOCUMENT)


def test_existing_manual_admission_and_reservation(setup):
    a,s=setup;receipt=captured(a,s);store=r.RealEventStore(a.source_path)
    e=r.AdmissionEvidence('Bitcoin announcement',1,ShockEvidence.OFFICIAL_ANNOUNCEMENT,'SEC','one',Relation.NEW_EVENT,None)
    candidate=store.admit(receipt.receipt_id,e)
    assert candidate.reservation_id and not candidate.reasons
    row=d.inbox(a.root)[0]
    assert row['admission_status']=='ADMITTED' and row['attestation_status']=='MISSING'
    assert row['event_id']==candidate.envelope.event_id
    assert store._replay(store._rows()).reservations()[0].decision_at.isoformat()==row['decision_at']


def test_no_automatic_btc_or_direction(setup):
    a,s=setup;captured(a,s)
    assert d.inbox(a.root)[0]['admission_status']=='AWAITING_MANUAL_ADMISSION'
    assert d.inbox(a.root)[0]['attestation_status']=='MISSING'


def test_generic_release_not_filtered(setup):
    a,s=setup;s['body']=b'SEC administrative publication.';captured(a,s)
    assert a.status()['receipts']==1 and a.status()['admitted_candidates']==0


def test_inbox_read_only_closed_fields(setup):
    a,s=setup;captured(a,s)
    paths=[a.path,a.source_path,Path(a.activation['data']['operator_root'])/'authority.sqlite']
    before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    rows=d.inbox(a.root);a.status()
    assert set(rows[0])=={'receipt_id','event_id','source','document_id','title','content','received_at','available_at','decision_at','admission_status','attestation_status'}
    assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]


def test_tests_cannot_touch_production(tmp_path):
    with pytest.raises(ValueError,match='test process'): d.SourceDiscoveryAuthorityV1.activate(tmp_path/'prospective'/'event',tmp_path,role=DatasetRole.PILOT)
    assert not (tmp_path/'prospective').exists()


def test_no_rapid_retry(setup):
    a,s=setup;poll(a,s)
    calls=len(s['calls'])
    with pytest.raises(ValueError,match='5-minute'): a.poll()
    assert len(s['calls'])==calls


def test_lock_rejects_concurrent_poll(setup):
    a,s=setup
    with d._lock(a.root):
        with pytest.raises(OSError): a.poll()
    assert s['calls']==[]


@pytest.mark.parametrize('raw',[b'bad',b'<rss version="2.0"><channel><title>Press Releases</title></channel></rss>',feed('a','a'),b'<!DOCTYPE rss><rss/>'])
def test_invalid_feed_never_baselines(setup,raw):
    a,s=setup;s['feed']=raw
    result=poll(a,s)
    assert not result['baseline_established'] and result['last_status']=='INVALID_FEED'


def test_guid_link_conflict_fail_closed(setup):
    a,s=setup;captured(a,s)
    s['feed']=feed('new').replace((BASE+'new').encode(),(BASE+'different').encode())
    assert poll(a,s)['last_status']=='INVALID_SCOPE'
    assert a.status()['receipts']==1


def test_discovery_provenance_corruption(setup):
    a,s=setup;receipt=captured(a,s)
    with sqlite3.connect(a.path) as c: c.execute("UPDATE event_journal SET hash='corrupt' WHERE seq=(SELECT max(seq) FROM event_journal)")
    with pytest.raises(ValueError): r.RealEventStore(a.source_path).receipt(receipt.receipt_id)

def test_canonical_hash_independent_of_dict_order():
    assert d.digest({'a':1,'b':{'c':2,'d':3}})==d.digest({'b':{'d':3,'c':2},'a':1})


def test_interrupted_watermark_never_rebaselines(setup,monkeypatch):
    a,s=setup;original=a._write
    def interrupted(kind,data):
        if kind=='baseline': raise RuntimeError('crash')
        original(kind,data)
    monkeypatch.setattr(a,'_write',interrupted)
    with pytest.raises(RuntimeError): poll(a,s,'old')
    monkeypatch.setattr(a,'_write',original)
    with pytest.raises(ValueError,match='watermark'): poll(a,s,'new')
    assert a.status()['receipts']==0


def test_discover_all_before_document_denial(setup,monkeypatch):
    a,s=setup;poll(a,s,'old');original=d._fetch
    def denied(url,*,feed):
        if not feed: raise HTTPError(url,429,'rate',{},None)
        return original(url,feed=feed)
    monkeypatch.setattr(d,'_fetch',denied)
    result=poll(a,s,'old','a','b')
    assert result['new_documents']==2 and result['receipts']==0
    assert sum(x['kind']=='document_failure' for x in a.journal._rows())==1


def test_interrupted_document_ready_stays_unknown(setup,monkeypatch):
    a,s=setup;poll(a,s,'old');original=r.RealEventStore._append
    def interrupted(self,kind,*args):
        if kind=='ready': raise OSError('crash')
        return original(self,kind,*args)
    monkeypatch.setattr(r.RealEventStore,'_append',interrupted)
    poll(a,s,'old','new');monkeypatch.setattr(r.RealEventStore,'_append',original)
    poll(a,s,'old','new')
    assert d.inbox(a.root)[0]['available_at'] is None


def test_transport_one_request_and_exact_bytes(monkeypatch):
    from email.message import Message
    calls=[]
    class Response:
        status=200
        headers=Message()
        headers['Content-Type']='application/rss+xml'
        raw=feed('old')
        headers['Content-Length']=str(len(raw))
        def geturl(self): return d.ENDPOINT
        def read(self,n): return self.raw[:n]
        def __enter__(self): return self
        def __exit__(self,*args): pass
    class Opener:
        def open(self,request,timeout):
            calls.append((request.full_url,request.get_header('User-agent'),timeout))
            return Response()
    monkeypatch.setattr(d,'build_opener',lambda *args:Opener())
    raw,received,kind=d._fetch(d.ENDPOINT,feed=True)
    assert raw==feed('old') and received.tzinfo is not None
    assert calls==[(d.ENDPOINT,d.USER_AGENT,20)]


def test_receipt_corruption_rejected(setup):
    a,s=setup;receipt=captured(a,s)
    with sqlite3.connect(a.source_path) as c:
        c.execute("UPDATE event_journal SET body=replace(body,'Bitcoin','Changed') WHERE body LIKE '%content_hash%'")
    with pytest.raises(ValueError): r.RealEventStore(a.source_path,read_only=True)


def test_late_manual_admission_no_rollover(setup):
    a,s=setup;receipt=captured(a,s);s['now']=T+timedelta(hours=2)
    store=r.RealEventStore(a.source_path)
    store.admit(receipt.receipt_id,r.AdmissionEvidence('Bitcoin announcement',1,ShockEvidence.OFFICIAL_ANNOUNCEMENT,'SEC','one',Relation.NEW_EVENT,None))
    assert d.inbox(a.root)[0]['admission_status']=='REJECTED'
    assert store.close(s['now'])==()

def test_source_binding_removed_fails_closed(setup):
    a,s=setup
    import gc
    gc.collect()  # Existing SQLite context managers may retain handles until collection.
    a.source_path.unlink()
    with pytest.raises(sqlite3.OperationalError): d.SourceDiscoveryAuthorityV1(a.root)
    assert not a.source_path.exists()


def test_changed_scope_with_rehashed_journal_rejected(setup):
    a,s=setup
    rows=a.journal._rows();rows[0]['data']['contract']['interval_seconds']=1
    body=r._json(rows[0]);commitment=digest(('0'*64,body))
    with sqlite3.connect(a.path) as c: c.execute('UPDATE event_journal SET body=?,hash=? WHERE seq=1',(body,commitment))
    with pytest.raises(ValueError,match='contract mismatch'): d.SourceDiscoveryAuthorityV1(a.root)


def test_cli_poll_is_one_shot(setup):
    from scripts.sec_event_discovery import main
    a,s=setup;s['now']+=timedelta(minutes=5)
    result=main(['--root',str(a.root),'poll'])
    assert result['baseline_established'] and s['calls']==[d.ENDPOINT]


def test_installer_requires_baseline_and_no_overwrite():
    source=(Path(__file__).parents[1]/'scripts/install_sec_event_discovery_task.ps1').read_text(encoding='utf-8-sig')
    assert 'baseline_established' in source and 'Task already exists' in source
    assert '-RepetitionInterval (New-TimeSpan -Minutes 5)' in source
    assert '-MultipleInstances IgnoreNew' in source and ' -Force' not in source

def test_empty_scoped_journal_cannot_authorize_arbitrary_source(setup):
    a,s=setup
    with pytest.raises(ValueError,match='scope frozen'):
        r.RealEventStore(a.source_path).authorize_source('rogue','v1',BASE+'rogue',r.ContentKind.FULL_DOCUMENT)
    assert not a.status()['baseline_established']
