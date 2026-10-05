from dataclasses import FrozenInstanceError
from datetime import timedelta
import pytest
from core.scientific.universe_snapshot import load_snapshot
from tests.test_multi_market_capture import freeze,cycle,rows,T


def test_causal_snapshot_and_identity(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); observed=cycle(tmp_path,monkeypatch)
    args=(tmp_path/'cycle',tmp_path/'universe')
    snapshot=load_snapshot(*args,as_of=observed.completed_at)
    assert snapshot==load_snapshot(*args,as_of=observed.completed_at)
    assert snapshot.cycle_id==observed.cycle_id and snapshot.cycle_kind=='DIAGNOSTIC'
    assert tuple(m.evidence for m in snapshot.members)==observed.members
    assert all(m.status=='AVAILABLE' for m in snapshot.members)
    assert snapshot.role=='PILOT'
    with pytest.raises(FrozenInstanceError): snapshot.members=()


def test_late_cycle_does_not_leak_values_ids_or_missingness(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); observed=cycle(tmp_path,monkeypatch,rows()[1:])
    args=(tmp_path/'cycle',tmp_path/'universe')
    early=load_snapshot(*args,as_of=observed.completed_at-timedelta(microseconds=1))
    assert early.cycle_id is None and early.cycle_kind is None
    assert all(m.status=='UNAVAILABLE' and m.evidence is None for m in early.members)
    available=load_snapshot(*args,as_of=observed.completed_at)
    assert available.members[0].status=='MISSING' and available.members[0].evidence is None
    assert sum(m.status=='AVAILABLE' for m in available.members)==4


@pytest.mark.parametrize('cutoff',[T,T.replace(tzinfo=None)])
def test_unavailable_universe_and_naive_cutoff_rejected(tmp_path,monkeypatch,cutoff):
    freeze(tmp_path,monkeypatch); cycle(tmp_path,monkeypatch)
    with pytest.raises((ValueError,TypeError)):
        load_snapshot(tmp_path/'cycle',tmp_path/'universe',as_of=cutoff)
