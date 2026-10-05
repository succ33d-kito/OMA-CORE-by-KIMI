from datetime import timedelta
from decimal import Decimal
import pytest
from core.scientific import radar_runner as r
from tests.test_multi_market_capture import freeze,cycle,T
from tests.test_multi_market_premium import premium


def setup(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch)
    monkeypatch.setattr(r.c,'_now',lambda:T+timedelta(seconds=10))
    r.freeze_config(tmp_path/'config',tmp_path/'universe',mark_index_fraction=Decimal('0.005'),
        funding_fraction_difference=Decimal('0.0002'),relative_spread_difference=Decimal('0.001'),max_candidates=2,horizon_seconds=3600)
    cycle(tmp_path,monkeypatch); premium(tmp_path,monkeypatch)
    monkeypatch.setattr(r.c,'_now',lambda:T+timedelta(hours=2))


def run(tmp_path):
    return r.run_once(tmp_path/'universe',tmp_path/'cycle',tmp_path/'config',tmp_path/'ledger',premium_directory=tmp_path/'premium')


def test_end_to_end_replay_without_network(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch)
    monkeypatch.setattr(r.c,'_http',lambda url:pytest.fail('runner must not capture'))
    eid=run(tmp_path); before={str(p):p.read_bytes() for p in (tmp_path/'ledger').rglob('*') if p.is_file()}
    monkeypatch.setattr(r.c,'_now',lambda:T+timedelta(hours=3))
    assert run(tmp_path)==eid
    assert all(__import__('pathlib').Path(p).read_bytes()==data for p,data in before.items())
    entry=r.load_entry(tmp_path/'ledger'/'entries'/(eid+'.json'))
    assert entry['payload']['candidate_count']==2 and entry['payload']['observed_count']==5


def test_corrupt_ledger_stops(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch); eid=run(tmp_path)
    path=tmp_path/'ledger'/'entries'/(eid+'.json'); path.write_bytes(b'{}')
    with pytest.raises(ValueError): run(tmp_path)


def test_future_source_stops(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch)
    monkeypatch.setattr(r.c,'_now',lambda:T+timedelta(minutes=30))
    with pytest.raises(ValueError): run(tmp_path)


def test_late_config_is_not_retroactive(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch)
    r.freeze_config(tmp_path/'late',tmp_path/'universe',mark_index_fraction=Decimal('0.005'),
        funding_fraction_difference=Decimal('0.0002'),relative_spread_difference=Decimal('0.001'),max_candidates=2,horizon_seconds=3600)
    with pytest.raises(ValueError): r.run_once(tmp_path/'universe',tmp_path/'cycle',tmp_path/'late',tmp_path/'unused')


def test_config_parameters_cannot_be_substituted(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch)
    path=tmp_path/'config'/'parameters.json'
    path.write_bytes(path.read_bytes().replace(b'0.005',b'0.999'))
    with pytest.raises(ValueError): run(tmp_path)
