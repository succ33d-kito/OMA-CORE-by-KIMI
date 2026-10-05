from dataclasses import FrozenInstanceError
from datetime import timedelta
from decimal import Decimal,localcontext
import pytest
from core.scientific.world_state import load_world
from tests.test_multi_market_capture import freeze,cycle,T
from tests.test_multi_market_premium import premium


def world(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); cycle(tmp_path,monkeypatch); premium(tmp_path,monkeypatch)
    return load_world(tmp_path/'universe',as_of=T+timedelta(hours=2),book_directory=tmp_path/'cycle',premium_directory=tmp_path/'premium')


def test_combined_verified_facts_deterministic(tmp_path,monkeypatch):
    w=world(tmp_path,monkeypatch)
    again=load_world(tmp_path/'universe',as_of=w.as_of,book_directory=tmp_path/'cycle',premium_directory=tmp_path/'premium')
    assert again==w and again.world_state_id==w.world_state_id
    assert w.book_cycle_kind=='DIAGNOSTIC' and w.role=='PILOT'
    for m in w.markets:
        assert m.mid==Decimal('100.5') and m.spread==1
        assert m.premium.mark==101 and m.premium.index==100
        assert m.premium.funding_rate==Decimal('0.0001')
        assert m.book_age_seconds==7200 and m.premium_age_seconds==3600
    with pytest.raises(FrozenInstanceError): w.markets=()
    with localcontext() as ctx:
        ctx.prec=2
        assert w.markets[0].mid==Decimal('100.5')


def test_future_sources_not_exposed(tmp_path,monkeypatch):
    world(tmp_path,monkeypatch)
    w=load_world(tmp_path/'universe',as_of=T+timedelta(minutes=30),book_directory=tmp_path/'cycle',premium_directory=tmp_path/'premium')
    assert w.book_cycle_id is None and w.premium_cycle_id is None
    assert all(m.book is None and m.premium is None and m.mid is None for m in w.markets)
    assert w.book_quality.capture_span_seconds is None


def test_absent_source_no_fill(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch)
    w=load_world(tmp_path/'universe',as_of=T+timedelta(hours=1))
    assert all(m.mid is None and m.premium is None for m in w.markets)
    assert len(w.book_quality.missing_members)==5
