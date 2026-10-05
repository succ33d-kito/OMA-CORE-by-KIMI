from datetime import timedelta
from decimal import Decimal
import pytest
from core.scientific import shadow_runner as s
from core.scientific.radar_runner import freeze_config
from core.scientific.coverage_ledger import freeze_masks
from tests.test_multi_market_capture import freeze,cycle,T
from tests.test_multi_market_premium import premium
from tests.test_trading_decision_plane import risk_policy


def prepare(root,monkeypatch,mask='OMA-FULL'):
    freeze(root,monkeypatch)
    monkeypatch.setattr(s.c,'_now',lambda:T+timedelta(seconds=10))
    freeze_config(root/'radar-config',root/'universe',mark_index_fraction=Decimal('0.005'),funding_fraction_difference=Decimal('0.0002'),
        relative_spread_difference=Decimal('0.001'),max_candidates=2,horizon_seconds=3600)
    s.t.register_ranking_policy(root/'ranking',criteria=(s.t.RankingCriterion.COMPLETENESS,s.t.RankingCriterion.EVIDENCE_BREADTH))
    freeze_masks(root/'masks',root/'universe')
    monkeypatch.setattr(s.c,'_now',lambda:T+timedelta(seconds=20))
    s.freeze_shadow_config(root/'shadow-config',root/'universe',root/'radar-config',root/'ranking',root/'masks',mask_name=mask,
        risk_policy=risk_policy(T+timedelta(seconds=10)),allocation_policy=s.t.AllocationPolicy(T+timedelta(seconds=10),True),
        equity=s.t.CapitalAmount(s.t.CapitalUnit.USD_NOTIONAL,Decimal('10000')),budget=s.t.CapitalAmount(s.t.CapitalUnit.RISK_UNIT,Decimal('3')),
        requested_risk=s.t.CapitalAmount(s.t.CapitalUnit.RISK_UNIT,Decimal('1')),kill_switch=False)
    cycle(root,monkeypatch); premium(root,monkeypatch)
    monkeypatch.setattr(s.c,'_now',lambda:T+timedelta(hours=2))


def run(root):
    return s.run_shadow_once(root/'universe',root/'cycle',root/'radar-config',root/'ranking',root/'masks',root/'shadow-config',root/'decisions',premium_directory=root/'premium')


def test_reference_pipeline_no_fake_alpha_idempotent(tmp_path,monkeypatch):
    prepare(tmp_path,monkeypatch)
    monkeypatch.setattr(s.c,'_http',lambda url:pytest.fail('shadow runner cannot capture'))
    identity=run(tmp_path); path=next((tmp_path/'decisions').glob('*/decision.json')); before=path.read_bytes()
    monkeypatch.setattr(s.c,'_now',lambda:T+timedelta(hours=3))
    assert run(tmp_path)==identity and path.read_bytes()==before
    decision=s.c._read_json(path)['decision']
    assert decision['state']=='DEFERRED'
    assert all(row['amount']['value']=='0' for row in decision['allocation']['rows'])
    assert decision['allocation']['portfolio']['provenance']=='SHADOW_CONFIG'


@pytest.mark.parametrize('mask,count',[('Retail-1',1),('Retail-5',5),('Retail-20',5),('OMA-FULL',5)])
def test_frozen_masks_precede_selection(tmp_path,monkeypatch,mask,count):
    prepare(tmp_path,monkeypatch,mask); run(tmp_path)
    d=s.c._read_json(next((tmp_path/'decisions').glob('*/decision.json')))['decision']
    assert len(d['radar']['visible_symbols'])==count
    assert sum(m['book'] is not None for m in d['world']['markets'])==count
    assert all(set(c['markets'])<=set(d['radar']['visible_symbols']) for c in d['radar']['candidates'])
    assert sum(reason=='NOT_VISIBLE' for _,reason in d['radar']['non_candidates'])==5-count


def test_old_source_and_mutated_decision_rejected(tmp_path,monkeypatch):
    prepare(tmp_path,monkeypatch); run(tmp_path)
    path=next((tmp_path/'decisions').glob('*/decision.json'))
    path.write_bytes(path.read_bytes().replace(b'DEFERRED',b'APPROVED'))
    with pytest.raises(ValueError): run(tmp_path)
