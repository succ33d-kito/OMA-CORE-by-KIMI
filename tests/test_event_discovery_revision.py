"""Contract revision V2 and append-only authority supersession.

Synthetic fixtures only: every journal lives in a temporary directory and the
shared production prospective state is never touched. Historical identity
(activation authority, baseline, discovery, first_seen, document failures)
must survive a revision unchanged.
"""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import sqlite3
import pytest
from core.scientific import event_discovery as d, real_event_receipt as r
from core.scientific.event_direction_operator import activate
from core.scientific.nuisance_pilot_contracts import DatasetRole

T=datetime(2020,1,1,10,tzinfo=timezone.utc)
BASE='https://www.sec.gov/newsroom/press-releases/'
V1_HASH='831c49f02d82112986bdbda352c5f2599e4383a2cafd370fd9ef78e2560772aa'
BEHAVIOUR_KEYS=('schema','scope','role','endpoint','hosts','document_prefix','parser',
                'polling','interval_seconds','baseline','revisions','redirects')


def feed(*ids):
    return ('<rss version="2.0"><channel><title>Press Releases</title>'+''.join(
        '<item><guid>'+i+'</guid><title>SEC '+i+'</title><link>'+BASE+i+'</link>'
        '<pubDate>Mon, 01 Jan 1990 00:00:00 GMT</pubDate></item>' for i in ids)+'</channel></rss>').encode()


@pytest.fixture
def setup(tmp_path,monkeypatch):
    state=dict(now=T,feed=feed('old'),body=b'Bitcoin announcement. Full document.',
               calls=[],agents=[],doc_fetched_at=None,error=None,doc_error=False)
    monkeypatch.setattr(r,'_now',lambda:state['now'])
    activate(tmp_path/'operator',tmp_path/'source.sqlite',role=DatasetRole.PILOT)
    state['now']+=timedelta(seconds=1)
    authority=d.SourceDiscoveryAuthorityV1.activate(tmp_path/'discovery',tmp_path/'operator',role=DatasetRole.PILOT)
    def fetch(url,*,feed,user_agent=None,**kwargs):
        state['calls'].append(url); state['agents'].append(user_agent)
        state['now']+=timedelta(milliseconds=1)
        if state['error'] and (feed or state['doc_error']): raise state['error']
        if not feed and state['doc_error']: raise OSError('document failed')
        if not feed: state['doc_fetched_at']=state['now']
        return (state['feed'] if feed else state['body']),state['now'],('application/rss+xml' if feed else 'text/plain')
    monkeypatch.setattr(d,'_fetch',fetch)
    return authority,state


def poll(a,s,*ids):
    s['now']+=timedelta(minutes=5)
    if ids: s['feed']=feed(*ids)
    return a.poll()


def rows_of(a,kind):
    return [x for x in a.journal._rows() if x['kind']==kind]


def first_receipt(a):
    return r.RealEventStore(a.source_path).receipt(d.inbox(a.root)[0]['receipt_id'])


# 1 --------------------------------------------------------------------------
def test_old_contract_hash_remains_unchanged():
    assert d.digest(d.CONTRACT)==V1_HASH
    assert d.CONTRACT_HASH==V1_HASH
    assert d.CONTRACT_CHAIN[V1_HASH]==d.CONTRACT


# 2 --------------------------------------------------------------------------
def test_new_contract_hash_differs():
    assert d.CONTRACT_V2_HASH!=V1_HASH
    assert d.CONTRACT_V2_HASH==d.digest(d.CONTRACT_V2)
    assert d.CONTRACT_CHAIN[d.CONTRACT_V2_HASH]==d.CONTRACT_V2


# 3 --------------------------------------------------------------------------
def test_user_agent_is_the_only_behavioral_contract_difference():
    v1,v2=d.CONTRACT,d.CONTRACT_V2
    assert set(v1)==set(v2)
    assert [k for k in v1 if v1[k]!=v2[k]]==['user_agent']
    for key in BEHAVIOUR_KEYS:
        assert v1[key]==v2[key]
    assert v1['redirects']=='reject-all' and v2['redirects']=='reject-all'


def test_pending_contact_is_explicitly_non_activatable():
    assert d.CONTACT_PENDING in d.CONTRACT_V2['user_agent']
    assert d.CONTRACT_V2['user_agent']!=d.CONTRACT['user_agent']


# 4 --------------------------------------------------------------------------
def test_supersession_does_not_create_a_new_baseline(setup):
    a,s=setup;poll(a,s,'old')
    assert len(rows_of(a,'baseline'))==1
    b=d.SourceDiscoveryAuthorityV1.supersede(a.root)
    assert len(rows_of(a,'baseline'))==1
    assert b.status()['baseline_count']==1
    assert b.status()['baseline_hash']==a.status()['baseline_hash']


def test_supersession_never_replays_baseline_items_as_prospective(setup):
    a,s=setup;poll(a,s,'old')
    baseline_items={i['item_id'] for i in rows_of(a,'baseline')[0]['data']['items']}
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    poll(a,s,'old')
    assert {x['data']['item']['item_id'] for x in rows_of(a,'discovery')} & baseline_items==set()
    assert rows_of(a,'discovery')==[]


# 5 --------------------------------------------------------------------------
def test_existing_discovery_id_remains_identical(setup):
    a,s=setup
    poll(a,s,'old');poll(a,s,'old','new')
    before=rows_of(a,'discovery')
    assert len(before)==1
    ident=d.digest(before[0])
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    after=rows_of(a,'discovery')
    assert len(after)==1 and d.digest(after[0])==ident


def test_supersession_does_not_duplicate_the_discovery(setup):
    a,s=setup
    poll(a,s,'old');poll(a,s,'old','new')
    n=len(rows_of(a,'discovery'))
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    assert len(rows_of(a,'discovery'))==n==1
    poll(a,s,'old','new')
    assert len(rows_of(a,'discovery'))==1


# 6 --------------------------------------------------------------------------
def test_existing_first_seen_remains_identical(setup):
    a,s=setup
    poll(a,s,'old');poll(a,s,'old','new')
    before=rows_of(a,'discovery')[0]['data']['first_seen_at']
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    assert rows_of(a,'discovery')[0]['data']['first_seen_at']==before


# 7 --------------------------------------------------------------------------
def test_historical_document_failures_remain_untouched(setup):
    a,s=setup
    poll(a,s,'old')
    s['doc_error']=True
    poll(a,s,'old','new')
    failures=rows_of(a,'document_failure')
    assert len(failures)==1
    fingerprints=[d.digest(x) for x in failures]
    s['doc_error']=False
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    assert [d.digest(x) for x in rows_of(a,'document_failure')]==fingerprints


def test_historical_failures_are_not_deleted_or_rewritten(setup):
    a,s=setup
    poll(a,s,'old')
    s['doc_error']=True
    for _ in range(2): poll(a,s,'old','new')
    before=[d.digest(x) for x in rows_of(a,'document_failure')]
    assert len(before)==2
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    after=[d.digest(x) for x in rows_of(a,'document_failure')]
    assert after==before


# 8 / 9 / 10 -----------------------------------------------------------------
def test_later_success_uses_actual_later_receive_time(setup):
    a,s=setup
    poll(a,s,'old')
    s['doc_error']=True
    poll(a,s,'old','new')
    s['doc_error']=False
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    poll(a,s,'old','new')
    receipt=first_receipt(a)
    assert receipt.received_at==s['doc_fetched_at']
    first_seen=datetime.fromisoformat(rows_of(a,'discovery')[0]['data']['first_seen_at'])
    assert receipt.received_at>first_seen


def test_later_success_uses_actual_later_availability_time(setup):
    a,s=setup
    poll(a,s,'old')
    s['doc_error']=True
    poll(a,s,'old','new')
    s['doc_error']=False
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    poll(a,s,'old','new')
    receipt=first_receipt(a)
    assert receipt.available_at is not None
    assert receipt.received_at<=receipt.available_at
    first_seen=datetime.fromisoformat(rows_of(a,'discovery')[0]['data']['first_seen_at'])
    assert receipt.available_at>first_seen


def test_no_backdating_after_revision(setup):
    a,s=setup
    poll(a,s,'old')
    s['doc_error']=True
    poll(a,s,'old','new')
    s['doc_error']=False
    superseded=d.SourceDiscoveryAuthorityV1.supersede(a.root)
    revision_at=datetime.fromisoformat(superseded.supersessions[-1]['at'])
    poll(a,s,'old','new')
    receipt=first_receipt(a)
    discovery=rows_of(a,'discovery')[0]
    assert receipt.received_at>revision_at
    assert receipt.received_at>=datetime.fromisoformat(discovery['data']['first_seen_at'])
    assert receipt.received_at.year==2020          # blog pubDate is 1990 and is never used
    assert receipt.available_at>=receipt.received_at


# 11 -------------------------------------------------------------------------
def test_baseline_items_remain_non_prospective(setup):
    a,s=setup;poll(a,s,'old')
    baseline=rows_of(a,'baseline')[0]
    assert [i['guid'] for i in baseline['data']['items']]==['old']
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    poll(a,s,'old','new')
    assert rows_of(a,'discovery')[0]['data']['item']['guid']=='new'


# 12 ------------------------------------------------------------------------
def test_redirects_remain_rejected_after_revision(setup):
    a,s=setup
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    with pytest.raises(ValueError,match='redirect rejected'):
        d._NoRedirect().redirect_request(None,None,302,'',{},BASE+'moved')
    assert d.CONTRACT_V2['redirects']=='reject-all'


# 13 ------------------------------------------------------------------------
@pytest.mark.parametrize('url',['https://evil.test/a','https://www.sec.gov/other/a',BASE+'../a',
                                BASE+'a?b=1',BASE+'%2e%2e/a',BASE+'a#b',
                                'http://www.sec.gov/newsroom/press-releases/a'])
def test_off_scope_documents_remain_rejected(setup,url):
    a,s=setup
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    with pytest.raises(ValueError,match='INVALID_SCOPE'): d._url(url)


# 14 ------------------------------------------------------------------------
def test_parser_semantics_unchanged(setup):
    a,s=setup
    before=d._parse(feed('a','b'))
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    after=d._parse(feed('a','b'))
    assert [i['item_id'] for i in after]==[i['item_id'] for i in before]
    assert [i['link'] for i in after]==[i['link'] for i in before]
    assert after==before
    with pytest.raises(ValueError,match='INVALID_FEED'):
        d._parse(b'<rss version="2.0"><channel><title>Press Releases</title></channel></rss>')


# 15 ------------------------------------------------------------------------
def test_event_direction_is_not_automatically_created(setup):
    a,s=setup
    poll(a,s,'old');poll(a,s,'old','new')
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    poll(a,s,'old','new')
    row=d.inbox(a.root)[0]
    assert row['attestation_status']=='MISSING'
    assert not [x for x in a.journal._rows() if 'direction' in x['kind']]
    assert not [x for x in r.RealEventStore(a.source_path)._rows() if 'direction' in x['kind']]


# 16 ------------------------------------------------------------------------
def test_p0_is_not_automatically_created(setup):
    a,s=setup
    poll(a,s,'old');poll(a,s,'old','new')
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    poll(a,s,'old','new')
    status=a.status()
    assert status['admitted_candidates']==0
    assert not [x for x in a.journal._rows() if 'p0' in x['kind'].lower()]
    assert d.inbox(a.root)[0]['admission_status']=='AWAITING_MANUAL_ADMISSION'


# supersession safety --------------------------------------------------------
def test_supersession_does_not_mutate_the_old_authority(setup):
    a,s=setup;poll(a,s,'old')
    activation_digest=d.digest(a.journal._rows()[0])
    activation_at=a.activation['at']
    old_authority_id=a.authority_id
    b=d.SourceDiscoveryAuthorityV1.supersede(a.root)
    assert d.digest(b.journal._rows()[0])==activation_digest
    assert b.activation['at']==activation_at
    assert b.authority_id==old_authority_id==a.authority_id
    assert b.authority_ids[0]==old_authority_id
    assert b.activation['data']['contract']==d.CONTRACT
    assert b.activation['data']['contract_hash']==V1_HASH


def test_supersession_rejects_a_second_identical_revision(setup):
    a,s=setup
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    with pytest.raises(ValueError,match='already active'):
        d.SourceDiscoveryAuthorityV1.supersede(a.root)
    assert len(rows_of(a,d.SUPERSESSION_KIND))==1


def test_supersession_rejects_unknown_or_malformed_records(setup):
    a,s=setup
    with pytest.raises(ValueError,match='unknown contract revision'):
        d.supersession_record(previous_authority_id='0'*64,previous_contract_hash=V1_HASH,
                              contract=dict(d.CONTRACT,schema='other'))
    with pytest.raises(ValueError,match='hex digest'):
        d.supersession_record(previous_authority_id='nope',previous_contract_hash=V1_HASH)
    with pytest.raises(ValueError,match='reason'):
        d.supersession_record(previous_authority_id='0'*64,previous_contract_hash=V1_HASH,reason=' ')


def test_broken_supersession_chain_fails_closed(setup):
    a,s=setup;poll(a,s,'old')
    bad=d.supersession_record(previous_authority_id='0'*64,previous_contract_hash=V1_HASH)
    a._write(d.SUPERSESSION_KIND,bad)
    with pytest.raises(ValueError,match='supersession chain mismatch'):
        d.SourceDiscoveryAuthorityV1(a.root)


def test_activation_authority_and_binding_unchanged_after_revision(setup):
    a,s=setup;poll(a,s,'old')
    source_rows=r.RealEventStore(a.source_path,read_only=True)._rows()
    binding=b''.join(str(x).encode() for x in source_rows)
    b=d.SourceDiscoveryAuthorityV1.supersede(a.root)
    assert b.source_path==a.source_path
    assert b''.join(str(x).encode() for x in r.RealEventStore(a.source_path,read_only=True)._rows())==binding


# live behaviour of the revision --------------------------------------------
def test_poll_uses_the_active_contract_user_agent(setup):
    a,s=setup
    poll(a,s,'old')
    assert set(s['agents'])=={d.USER_AGENT}
    s['agents'].clear()
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    poll(a,s,'old')
    assert set(s['agents'])=={d.CONTRACT_V2['user_agent']}
    assert d.CONTRACT_V2['user_agent'] not in ('',None)


def test_status_exposes_history_and_active_revision(setup):
    a,s=setup;poll(a,s,'old')
    assert a.status()['active_contract_hash']==V1_HASH
    assert a.status()['active_authority_id']==a.authority_id
    assert a.status()['contract_revisions']==0
    b=d.SourceDiscoveryAuthorityV1.supersede(a.root)
    st=b.status()
    assert st['contract_hash']==V1_HASH
    assert st['authority_id']==a.authority_id
    assert st['active_contract_hash']==d.CONTRACT_V2_HASH
    assert st['active_authority_id']!=a.authority_id
    assert st['supersedes_authority_id']==a.authority_id
    assert st['contract_revisions']==1


def test_receipt_proofs_still_verify_after_revision(setup):
    a,s=setup
    poll(a,s,'old');poll(a,s,'old','new')
    d.SourceDiscoveryAuthorityV1.supersede(a.root)
    poll(a,s,'old','new')
    store=r.RealEventStore(a.source_path)
    source_rows=store._rows()
    receipt_row=next(x for x in source_rows if x['kind']=='receipt')
    d.verify_receipt_proof(a.source_path,receipt_row,source_rows)


def test_revision_requires_pilot_scope_and_separate_paths(setup,tmp_path):
    a,s=setup
    with pytest.raises(ValueError): d.SourceDiscoveryAuthorityV1.activate(a.root,a.activation['data']['operator_root'],role=DatasetRole.PILOT)
    assert not (tmp_path/'other').exists()
