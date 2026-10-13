from datetime import timedelta
from pathlib import Path
import sqlite3
import pytest
from tests.test_event_direction_v1 import claim, controls
from tests.test_real_event_receipt import setup_store, evidence, T
from core.scientific import event_direction_operator as op
from core.scientific.event_direction_v1 import EventClass
from core.scientific.real_event_receipt import RealEventStore
from core.scientific.nuisance_pilot_contracts import DatasetRole
from scripts.event_direction_operator import main

ROLE = DatasetRole.PILOT


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    store, clock = setup_store(tmp_path, monkeypatch)
    clock['now'] = T
    # Existing test store path is resolved below from its fixture-created journal.
    source = tmp_path / 'events.sqlite'
    root = tmp_path / 'authority'
    initial = op.activate(root, source, role=ROLE)
    clock['now'] = T + timedelta(minutes=23)
    clock['raw'] = b'Bitcoin announcement. Actor commits to Bitcoin action.'
    receipt = store.capture('official', 'v1', ROLE)
    store.admit(receipt.receipt_id, evidence())
    return root, source, store, clock, receipt, initial


def test_internal_activation_no_backdating(tmp_path):
    with pytest.raises(TypeError): op.activate(tmp_path/'a', tmp_path/'e', role=ROLE, activated_at=T)


def test_empty_activation_and_readonly_status(tmp_path):
    root, source = tmp_path/'a', tmp_path/'e'
    first = op.activate(root, source, role=ROLE)
    before = {p.name:p.read_bytes() for p in root.iterdir()}
    assert op.inspect(root, role=ROLE) == first
    assert before == {p.name:p.read_bytes() for p in root.iterdir()}
    assert not source.exists()
    assert first['post_activation_event_receipts'] == first['p0_eligible_opportunities'] == 0
    with pytest.raises(FileExistsError): op.activate(root, source, role=ROLE)
    assert before == {p.name:p.read_bytes() for p in root.iterdir()}


def test_wrong_role(ctx):
    root,*_ = ctx
    with pytest.raises(ValueError): op.inspect(root, role=DatasetRole.CONFIRMATION)


@pytest.mark.parametrize('kind',list(EventClass))
def test_explicit_attest_and_unknown_population(ctx,kind):
    root, source, store, clock, receipt, _ = ctx
    result = op.attest(root, receipt.receipt_id, claim(kind), role=ROLE)
    assert result.direction.value == ('UNKNOWN' if kind is EventClass.UNKNOWN else 'LONG' if 'BUY' in kind.value or 'EXPANSION' in kind.value else 'SHORT')
    assert op.attest(root, receipt.receipt_id, claim(kind), role=ROLE) == result
    clock['now'] = T+timedelta(hours=1);store.close(clock['now'])
    binding = op.bind(root, controls(), role=ROLE)
    before = {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    state = op.inspect(root, role=ROLE, controls=controls())
    assert state['bound_event_population'] == 1
    assert state['p0_eligible_opportunities'] == 0
    assert state['directions'][result.direction.value] == 1
    assert state == op.inspect(root, role=ROLE, controls=controls())
    assert before == {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    with pytest.raises(ValueError): op.bind(root, controls(), role=ROLE)
    assert op.attest(root, receipt.receipt_id, claim(kind), role=ROLE).record_id == result.record_id


@pytest.mark.parametrize('delta',[0,-1])
def test_activation_boundary_rejects(ctx,tmp_path,delta):
    root, source, store, clock, receipt, _ = ctx
    clock['now'] = receipt.received_at - timedelta(seconds=delta)
    late = tmp_path/'late';op.activate(late,source,role=ROLE)
    with pytest.raises(ValueError): op.attest(late,receipt.receipt_id,claim(),role=ROLE)


def test_missing_direction_fails_binding_without_filter(ctx):
    root,source,store,clock,receipt,_ = ctx
    clock['now']=T+timedelta(hours=1);store.close(clock['now'])
    with pytest.raises(ValueError): op.bind(root,controls(),role=ROLE)
    assert not (root/'population').exists()
    assert op.inspect(root,role=ROLE)['ineligible_reasons']


def test_late_and_conflicting_attestation(ctx):
    root,source,store,clock,receipt,_=ctx
    first=op.attest(root,receipt.receipt_id,claim(),role=ROLE)
    with pytest.raises(ValueError): op.attest(root,receipt.receipt_id,claim(curator='other'),role=ROLE)
    assert op.attest(root,receipt.receipt_id,claim(),role=ROLE)==first


def test_late_first_attestation(ctx):
    root,source,store,clock,receipt,_=ctx
    clock['now']=T+timedelta(hours=1)
    with pytest.raises(ValueError): op.attest(root,receipt.receipt_id,claim(),role=ROLE)


def test_corrupt_authority(ctx):
    root,*_=ctx
    with sqlite3.connect(root/'authority.sqlite') as con:
        con.execute("UPDATE event_journal SET hash='bad' WHERE seq=1")
    with pytest.raises(ValueError): op.inspect(root,role=ROLE)


def test_wrong_rule(ctx,monkeypatch):
    root,*_=ctx
    monkeypatch.setattr(op,'RULE_HASH','0'*64)
    with pytest.raises(ValueError): op.inspect(root,role=ROLE)


def test_source_prefix_replacement(ctx):
    root,source,*_=ctx
    with sqlite3.connect(source) as con: con.execute('DELETE FROM event_journal')
    with pytest.raises(ValueError): op.inspect(root,role=ROLE)


def test_readonly_store_no_init_or_write(ctx,tmp_path):
    root,source,store,clock,receipt,_=ctx
    with pytest.raises(sqlite3.OperationalError): RealEventStore(tmp_path/'missing',read_only=True)
    assert not (tmp_path/'missing').exists()
    readonly=RealEventStore(source,read_only=True)
    before=source.read_bytes()
    with pytest.raises(ValueError): readonly.capture('official','v2',ROLE)
    with pytest.raises(ValueError): readonly.close(clock['now'])
    assert source.read_bytes()==before


def test_cli_activation_status_and_closed_inputs(tmp_path,capsys):
    root=tmp_path/'a';source=tmp_path/'e'
    args=['--root',str(root),'--role','PILOT']
    result=main(args+['activate','--event-journal',str(source)])
    assert main(args+['status'])==result
    with pytest.raises(SystemExit): main(args+['activate','--event-journal',str(source),'--activated-at','2020'])
    with pytest.raises(SystemExit): main(args+['status','--outcome','1'])
    assert not any(x in result for x in ('outcome','PnL','return','winner','success_rate'))


def test_incomplete_population_not_claimed(ctx):
    root,*_=ctx
    (root/'population').mkdir()
    assert op.inspect(root,role=ROLE)['population_state']=='INCOMPLETE_PUBLICATION'


def test_population_tampering(ctx):
    root,source,store,clock,receipt,_=ctx
    op.attest(root,receipt.receipt_id,claim(),role=ROLE)
    clock['now']=T+timedelta(hours=1);store.close(clock['now'])
    op.bind(root,controls(),role=ROLE)
    (root/'population'/'manifest.json').write_text('{}')
    with pytest.raises(ValueError): op.inspect(root,role=ROLE)


def test_valid_price_p0_eligibility_and_source_unchanged(ctx,tmp_path,monkeypatch):
    from tests.test_event_direction_v1 import price
    root,source,store,clock,receipt,_=ctx
    op.attest(root,receipt.receipt_id,claim(),role=ROLE)
    clock['now']=T+timedelta(hours=1);store.close(clock['now'])
    ledger=price(tmp_path,monkeypatch)
    before=source.read_bytes()
    state=op.inspect(root,role=ROLE,controls=controls(),price_ledger=ledger)
    assert state['p0_eligible_opportunities']==1
    binding=op.bind(root,controls(),role=ROLE,price_ledger=ledger)
    assert op.inspect(root,role=ROLE,controls=controls(),price_ledger=ledger)['bound_event_population']==1
    assert source.read_bytes()==before


def test_publication_after_decision_not_repaired(ctx,monkeypatch):
    root,source,store,clock,receipt,_=ctx
    original=RealEventStore._append
    def delayed(self,kind,*args):
        if kind=='direction_ready': clock['now']=T+timedelta(hours=1)
        return original(self,kind,*args)
    monkeypatch.setattr(RealEventStore,'_append',delayed)
    with pytest.raises(ValueError): op.attest(root,receipt.receipt_id,claim(),role=ROLE)
    with pytest.raises(ValueError): op.attest(root,receipt.receipt_id,claim(),role=ROLE)
    assert op.inspect(root,role=ROLE)['direction_attestations']==0
