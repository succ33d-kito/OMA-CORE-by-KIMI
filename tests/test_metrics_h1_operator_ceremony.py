from datetime import datetime, timedelta, timezone
import copy
import pytest
from scripts import activate_metrics_h1 as ceremony

NOW=datetime(2026,10,10,12,40,tzinfo=timezone.utc)


@pytest.fixture
def setup(tmp_path,monkeypatch):
    repo=tmp_path/'repo'; repo.mkdir()
    monkeypatch.setattr(ceremony,'REPO_ROOT',repo)
    monkeypatch.setattr(ceremony,'_now',lambda:NOW)
    monkeypatch.setattr(ceremony,'_repository',lambda:{'head':'fixture','dirty':False})
    return tmp_path/'metrics-h1-v1'


def test_plan_is_read_only(setup):
    plan=ceremony.prepare(setup,'PILOT')
    assert not setup.exists()
    assert plan['activation_slot']=='2026-10-10T13:00:00+00:00'
    assert plan['network_executed'] is False


def test_exact_plan_creates_only_config_and_cannot_replay(setup):
    plan=ceremony.prepare(setup,'PILOT'); token=ceremony.confirmation(plan)
    result=ceremony.execute(plan,token)
    assert result['dataset_role']=='PILOT'
    assert [p.name for p in setup.iterdir()]==['config.json']
    before=(setup/'config.json').read_bytes()
    with pytest.raises(ValueError): ceremony.execute(plan,token)
    assert (setup/'config.json').read_bytes()==before


@pytest.mark.parametrize('offset',[-1,61])
def test_expiry_and_regression(setup,monkeypatch,offset):
    plan=ceremony.prepare(setup,'PILOT')
    monkeypatch.setattr(ceremony,'_now',lambda:NOW+timedelta(seconds=offset))
    with pytest.raises(ValueError): ceremony.execute(plan,ceremony.confirmation(plan))
    assert not setup.exists()


@pytest.mark.parametrize('field,value',[('activation_slot','2020-01-01T00:00:00+00:00'),
                                       ('network_executed',0),('extra',True)])
def test_tampered_plan_even_rehashed_rejected(setup,field,value):
    plan=ceremony.prepare(setup,'PILOT'); plan[field]=value
    with pytest.raises(ValueError): ceremony.execute(plan,ceremony.confirmation(plan))
    assert not setup.exists()


def test_role_change_requires_new_confirmation(setup):
    plan=ceremony.prepare(setup,'PILOT'); token=ceremony.confirmation(plan)
    plan['dataset_role']='DISCOVERY'
    with pytest.raises(ValueError): ceremony.execute(plan,token)


def test_dirty_or_changed_repository(setup,monkeypatch):
    plan=ceremony.prepare(setup,'PILOT')
    monkeypatch.setattr(ceremony,'_repository',lambda:{'head':'other','dirty':False})
    with pytest.raises(ValueError): ceremony.execute(plan,ceremony.confirmation(plan))
    monkeypatch.setattr(ceremony,'_repository',lambda:{'head':'fixture','dirty':True})
    plan=ceremony.prepare(setup,'PILOT')
    with pytest.raises(ValueError,match='clean'): ceremony.execute(plan,ceremony.confirmation(plan))


def test_slow_preflight_crosses_boundary(setup,monkeypatch):
    start=NOW.replace(minute=50)
    monkeypatch.setattr(ceremony,'_now',lambda:start)
    plan=ceremony.prepare(setup,'PILOT')
    ticks=iter([start,start+timedelta(microseconds=1)])
    monkeypatch.setattr(ceremony,'_now',lambda:next(ticks))
    with pytest.raises(ValueError,match='boundary'): ceremony.execute(plan,ceremony.confirmation(plan))


def test_second_sample_regression(setup,monkeypatch):
    plan=ceremony.prepare(setup,'PILOT')
    ticks=iter([NOW+timedelta(seconds=2),NOW+timedelta(seconds=1)])
    monkeypatch.setattr(ceremony,'_now',lambda:next(ticks))
    with pytest.raises(ValueError,match='regression'): ceremony.execute(plan,ceremony.confirmation(plan))


def test_residue_blocks_activation(setup):
    (setup.parent/('.'+setup.name+'.activating-fixture')).mkdir()
    plan=ceremony.prepare(setup,'PILOT')
    with pytest.raises(FileExistsError): ceremony.execute(plan,ceremony.confirmation(plan))
