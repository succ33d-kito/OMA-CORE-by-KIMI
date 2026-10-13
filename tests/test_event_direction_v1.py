from dataclasses import replace, FrozenInstanceError
from datetime import timedelta
from pathlib import Path
import json
import pytest
from tests.test_real_event_receipt import setup_store,evidence,T
import tests.test_price_role_attestation as price_fixture
from tests.test_policy_kernel import controls as old_controls
from core.scientific import real_event_receipt as ev
from core.scientific import event_direction_v1 as ed
from core.scientific import experiment51_p0 as p0
from core.scientific.nuisance_pilot_contracts import DatasetRole
from core.scientific.decision_rule import IntentAction


def claim(kind=ed.EventClass.BTC_ACCESS_EXPANSION_CONFIRMED,**changes):
    return ed.ClassAssertion(**dict(dict(event_class=kind,curator='fixture-curator',quote='Actor commits to Bitcoin action',actor='Actor',
        official_confirmed=True,direct_btc_action=True,unambiguous=True,commitment_not_fully_completed=True),**changes))


@pytest.fixture
def ctx(tmp_path,monkeypatch):
    store,state=setup_store(tmp_path,monkeypatch)
    state['now']=T
    authority=ed.EventDirectionAuthority.activate(tmp_path/'directions.db',role=DatasetRole.PILOT)
    state['now']=T+timedelta(minutes=23)
    state['raw']=b'Bitcoin announcement. Actor commits to Bitcoin action.'
    receipt=store.capture('official','v1',DatasetRole.PILOT)
    store.admit(receipt.receipt_id,evidence())
    return authority,store,state,receipt


def close(ctx):
    a,s,t,r=ctx;t['now']=T+timedelta(hours=1);s.close(t['now'])


def controls():
    return replace(old_controls(),policy_contract_hash=p0.P0_HASH,outcome_horizon_seconds=14400)


def price(tmp_path,monkeypatch,close_value=101,role='PILOT',slot=T):
    monkeypatch.setattr(price_fixture,'T',slot)
    root=price_fixture.create_activation(tmp_path,monkeypatch,role=role)
    auth=price_fixture.authorize(root,monkeypatch)
    original=price_fixture.append_observation
    def adapted(*args,**kwargs):
        kwargs['payload']['close']=close_value
        raw=json.loads(kwargs['provenance']['raw_klines']);raw[0][4]=str(close_value)
        kwargs['provenance']['raw_klines']=json.dumps(raw)
        return original(*args,**kwargs)
    monkeypatch.setattr(price_fixture,'append_observation',adapted)
    ledger=tmp_path/'price.db';r=price_fixture.append_price(ledger)
    monkeypatch.setattr(price_fixture.attestation,'_now',lambda:slot+timedelta(seconds=4))
    price_fixture.attestation.attest_price_observation(root,ledger,repo_root=price_fixture.repo_root(),slot_id=auth['slot_id'],observation_id=r['id'])
    return ledger


@pytest.mark.parametrize('kind,direction',[(ed.EventClass.BTC_ACCESS_EXPANSION_CONFIRMED,ed.Direction.LONG),
    (ed.EventClass.BTC_ACCESS_RESTRICTION_CONFIRMED,ed.Direction.SHORT),(ed.EventClass.BTC_NET_BUY_COMMITMENT_CONFIRMED,ed.Direction.LONG),
    (ed.EventClass.BTC_NET_SELL_COMMITMENT_CONFIRMED,ed.Direction.SHORT),(ed.EventClass.UNKNOWN,ed.Direction.UNKNOWN)])
def test_taxonomy_and_idempotence(ctx,kind,direction):
    a,s,t,r=ctx
    result=a.attest(s,r.receipt_id,claim(kind))
    assert result.direction is direction
    assert a.attest(s,r.receipt_id,claim(kind))==result
    assert a.verify(s,r.receipt_id).record_id==result.record_id
    assert s.receipt(r.receipt_id)==r
    with pytest.raises(FrozenInstanceError): result.direction=ed.Direction.SHORT
    assert replace(result,event_class=ed.EventClass.BTC_ACCESS_RESTRICTION_CONFIRMED if kind is ed.EventClass.UNKNOWN else ed.EventClass.UNKNOWN).record_id!=result.record_id
    with pytest.raises(ValueError): a.attest(s,r.receipt_id,claim(kind,curator='changed'))


@pytest.mark.parametrize('text',['positive news','negative news','CPI beat','Fed cuts','ETF filing','ETF rumor','ETF delay','general regulation','sentiment tie','hack','whale inflow'])
def test_unsupported_never_sentiment_fallback(ctx,text):
    a,s,t,r=ctx
    result=a.attest(s,r.receipt_id,claim(ed.EventClass.UNKNOWN,quote=text))
    assert result.direction is ed.Direction.UNKNOWN
    assert result.direction is not ed.Direction.NEUTRAL


@pytest.mark.parametrize('change',[{'official_confirmed':False},{'direct_btc_action':False},{'unambiguous':False},
    {'commitment_not_fully_completed':False},{'actor':''}])
def test_incomplete_buy_assertion_unknown(ctx,change):
    a,s,t,r=ctx
    assert a.attest(s,r.receipt_id,claim(ed.EventClass.BTC_NET_BUY_COMMITMENT_CONFIRMED,**change)).direction is ed.Direction.UNKNOWN


def test_quote_invalid(ctx):
    a,s,t,r=ctx
    with pytest.raises(ValueError): a.attest(s,r.receipt_id,claim(quote='not in document BTC'))


def test_future_and_historical_and_cross_role(ctx,tmp_path):
    a,s,t,r=ctx
    wrong=ed.EventDirectionAuthority.activate(tmp_path/'other.db',role=DatasetRole.CONFIRMATION)
    with pytest.raises(ValueError): wrong.attest(s,r.receipt_id,claim())
    historical=ed.EventDirectionAuthority.activate(tmp_path/'late.db',role=DatasetRole.PILOT)
    with pytest.raises(ValueError): historical.attest(s,r.receipt_id,claim())
    t['now']=T+timedelta(hours=1)
    with pytest.raises(ValueError): a.attest(s,r.receipt_id,claim())


@pytest.mark.parametrize('kind,bar,expected',[(ed.EventClass.BTC_ACCESS_EXPANSION_CONFIRMED,101,'LONG'),
    (ed.EventClass.BTC_ACCESS_RESTRICTION_CONFIRMED,99,'SHORT'),(ed.EventClass.BTC_ACCESS_EXPANSION_CONFIRMED,99,'ABSTAIN'),
    (ed.EventClass.BTC_ACCESS_RESTRICTION_CONFIRMED,101,'ABSTAIN'),(ed.EventClass.UNKNOWN,101,'ABSTAIN'),
    (ed.EventClass.BTC_ACCESS_EXPANSION_CONFIRMED,100,'ABSTAIN'),(ed.EventClass.UNKNOWN,None,'ABSTAIN'),(ed.EventClass.BTC_ACCESS_EXPANSION_CONFIRMED,None,'ABSTAIN')])
def test_p0_authenticated_agreement(ctx,tmp_path,monkeypatch,kind,bar,expected):
    a,s,t,r=ctx;a.attest(s,r.receipt_id,claim(kind));close(ctx)
    ledger=price(tmp_path,monkeypatch,bar) if bar else None
    result=p0.decide_p0(a,s,r.receipt_id,controls(),price_ledger=ledger)
    assert result.action.value==expected
    t['now']=T+timedelta(hours=12)
    assert p0.decide_p0(a,s,r.receipt_id,controls(),price_ledger=ledger)==result
    with pytest.raises(FrozenInstanceError): result.action=IntentAction.LONG


def test_neutral_agreement_abstains_but_authority_cannot_emit_neutral():
    assert p0._agreement(ed.Direction.NEUTRAL,ed.Direction.LONG) is IntentAction.ABSTAIN
    assert 'NEUTRAL' not in {c.value for c in ed.EventClass}


def test_price_wrong_role(ctx,tmp_path,monkeypatch):
    a,s,t,r=ctx;a.attest(s,r.receipt_id,claim());close(ctx)
    ledger=price(tmp_path,monkeypatch,101,role='CONFIRMATION')
    with pytest.raises(ValueError): p0.decide_p0(a,s,r.receipt_id,controls(),price_ledger=ledger)


@pytest.mark.parametrize('field',['outcome','future_return','PnL','was_correct','winner'])
def test_outcome_interface_closed(ctx,field):
    a,s,t,r=ctx
    with pytest.raises(TypeError): a.attest(s,r.receipt_id,claim(),**{field:1})
    with pytest.raises(TypeError): p0.decide_p0(a,s,r.receipt_id,controls(),**{field:1})


def test_unknown_population_retained_and_bound(ctx,tmp_path):
    a,s,t,r=ctx;a.attest(s,r.receipt_id,claim(ed.EventClass.UNKNOWN));close(ctx)
    before=s.population()
    manifest,binding=p0.bind_population(a,s,controls(),directory=tmp_path/'official')
    assert len(manifest.records)==1 and not manifest.records[0].cs4
    assert binding.manifest_id==manifest.manifest_id
    assert s.population()==before


def test_missing_attestation_population_not_silently_filtered(ctx,tmp_path):
    a,s,t,r=ctx;close(ctx)
    with pytest.raises(ValueError): p0.bind_population(a,s,controls(),directory=tmp_path/'official')
    assert not (tmp_path/'official').exists()


def test_late_first_decision_rejected(ctx):
    a,s,t,r=ctx;a.attest(s,r.receipt_id,claim());close(ctx)
    t['now']=T+timedelta(hours=6)
    with pytest.raises(ValueError): p0.decide_p0(a,s,r.receipt_id,controls())


def test_future_price_rejected(ctx,tmp_path,monkeypatch):
    a,s,t,r=ctx;a.attest(s,r.receipt_id,claim());close(ctx)
    ledger=price(tmp_path,monkeypatch)
    known,chain=p0.observation_snapshot(ledger,read_only=True)
    future={k:dict(v,available_at=(T+timedelta(hours=2)).isoformat()) for k,v in known.items()}
    monkeypatch.setattr(p0,'observation_snapshot',lambda *a,**kw:(future,chain))
    with pytest.raises(ValueError): p0.decide_p0(a,s,r.receipt_id,controls(),price_ledger=ledger)


def test_interrupted_direction_stays_unknown_no_repair(ctx,monkeypatch):
    a,s,t,r=ctx
    original=a._journal._append
    def crash(kind,*args):
        if kind=='direction_ready': raise RuntimeError('fixture crash')
        return original(kind,*args)
    monkeypatch.setattr(a._journal,'_append',crash)
    with pytest.raises(RuntimeError): a.attest(s,r.receipt_id,claim())
    monkeypatch.setattr(a._journal,'_append',original)
    with pytest.raises(ValueError): a.attest(s,r.receipt_id,claim())
    with pytest.raises(ValueError): a.verify(s,r.receipt_id)


def test_rule_and_horizon_controls_not_replaceable(ctx):
    a,s,t,r=ctx;a.attest(s,r.receipt_id,claim());close(ctx)
    for bad in (replace(controls(),outcome_horizon_seconds=3600),replace(controls(),policy_contract_hash='0'*64)):
        with pytest.raises(ValueError): p0.decide_p0(a,s,r.receipt_id,bad)


def test_journal_tampering_detected(ctx,tmp_path):
    import sqlite3
    a,s,t,r=ctx;a.attest(s,r.receipt_id,claim())
    with sqlite3.connect(tmp_path/'directions.db') as con:
        con.execute("UPDATE event_journal SET hash='bad' WHERE seq=2")
    with pytest.raises(ValueError): a.verify(s,r.receipt_id)


def test_authority_no_reactivation_or_public_role_change(ctx,tmp_path):
    a,s,t,r=ctx
    with pytest.raises(FileExistsError): ed.EventDirectionAuthority.activate(tmp_path/'directions.db',role=DatasetRole.PILOT)
    with pytest.raises(AttributeError): a.role=DatasetRole.CONFIRMATION


def test_frozen_preregistration_unchanged():
    from core.scientific.experiment51_preparation import load_protocol,commitment
    assert commitment(load_protocol())=='7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8'
