from decimal import Decimal,localcontext
from dataclasses import replace
from datetime import timedelta
import pytest
from core.scientific.opportunity_radar import RadarConfig,scan,Primitive
from core.scientific.opportunity_candidate import CandidateStatus
from tests.test_world_state import world
from tests.test_multi_market_capture import T


def config(**changes):
    args=dict(frozen_at=T,mark_index_fraction=Decimal('0.005'),funding_fraction_difference=Decimal('0.0002'),
              relative_spread_difference=Decimal('0.001'),max_candidates=2,horizon_seconds=3600)
    args.update(changes); return RadarConfig(**args)


def test_descriptive_subset_with_complete_accounting(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch); r=scan(w,config(),generated_at=w.as_of)
    assert r==scan(w,config(),generated_at=w.as_of)
    assert len(r.candidates)==2 and len(r.non_candidates)==3 and len(r.observed)==5 and not r.missing
    assert tuple(s for s,_ in r.candidate_subjects)==r.universe[:2]
    assert all(c.status is CandidateStatus.OBSERVED for c in r.candidates)
    assert all(reason=='LEXICOGRAPHIC_CAP' for _,reason in r.non_candidates)
    assert all(f.value==Decimal('0.01') for f in r.findings if f.primitive is Primitive.MARK_INDEX_DISPLACEMENT)
    with localcontext() as ctx:
        ctx.prec=2
        assert scan(w,config(),generated_at=w.as_of)==r


def test_non_candidates_and_missing_coverage(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch)
    quiet=scan(w,config(mark_index_fraction=Decimal('1')),generated_at=w.as_of)
    assert not quiet.candidates and len(quiet.non_candidates)==5
    from core.scientific.world_state import load_world
    empty=load_world(tmp_path/'universe',as_of=w.as_of)
    r=scan(empty,config(),generated_at=empty.as_of)
    assert not r.observed and len(r.missing)==5
    assert all(f.primitive is Primitive.MISSING_EVIDENCE for f in r.findings)


def test_ex_ante_config_and_no_outcomes(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch)
    with pytest.raises(ValueError): scan(w,config(frozen_at=w.as_of+timedelta(seconds=1)),generated_at=w.as_of)
    with pytest.raises(ValueError): config(mark_index_fraction=Decimal('NaN'))
    with pytest.raises(TypeError): scan(w,config(),generated_at=w.as_of,pnl=1)
    with pytest.raises(ValueError): config(role='CONFIRMATION')
