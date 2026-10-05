from dataclasses import replace,FrozenInstanceError
from datetime import timedelta
import pytest
from core.scientific import coverage_ledger as l
from core.scientific.opportunity_radar import scan
from tests.test_opportunity_radar import config
from tests.test_world_state import world


def test_immutable_coverage_replay_and_tamper(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch); r=scan(w,config(),generated_at=w.as_of)
    monkeypatch.setattr(l.c,'_now',lambda:w.as_of+timedelta(seconds=1))
    eid=l.append_coverage(tmp_path/'ledger',r); path=tmp_path/'ledger'/(eid+'.json'); before=path.read_bytes()
    assert l.append_coverage(tmp_path/'ledger',r)==eid and path.read_bytes()==before
    p=l.load_entry(path)['payload']
    assert p['universe_size']==5 and p['observed_count']==5 and p['candidate_count']==2
    assert len(p['non_candidates'])==3 and p['visibility']=='OMA-FULL'
    path.write_bytes(before.replace(b'OMA-FULL',b'RETAIL-X'))
    with pytest.raises(ValueError): l.append_coverage(tmp_path/'ledger',r)


def test_visibility_masks_are_ex_ante_fixed_not_performance_selected(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch)
    monkeypatch.setattr(l.c,'_now',lambda:w.as_of)
    masks=l.freeze_masks(tmp_path/'masks',tmp_path/'universe')
    assert l.load_masks(tmp_path/'masks',tmp_path/'universe')==masks
    assert tuple(m.name for m in masks)==('Retail-1','Retail-5','Retail-20','OMA-FULL')
    assert tuple(len(m.symbols) for m in masks)==(1,5,5,5)
    assert masks[2].requested_size==20 and masks[0].symbols==(w.markets[0].symbol,)
    with pytest.raises(FrozenInstanceError): masks[0].symbols=()
    with pytest.raises(FileExistsError): l.freeze_masks(tmp_path/'masks',tmp_path/'universe')


def test_invalid_accounting_and_future_radar(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch); r=scan(w,config(),generated_at=w.as_of)
    with pytest.raises(ValueError): l.append_coverage(tmp_path/'bad',replace(r,non_candidates=()))
    monkeypatch.setattr(l.c,'_now',lambda:w.as_of-timedelta(seconds=1))
    with pytest.raises(ValueError): l.append_coverage(tmp_path/'early',r)
