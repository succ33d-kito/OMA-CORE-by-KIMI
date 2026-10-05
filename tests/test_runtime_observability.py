from dataclasses import FrozenInstanceError, replace
import pytest
from core.runtime.contracts import *

AT='2026-10-05T12:00:00+00:00'


def test_contract_unknowns_immutable_no_scientific_promotions():
    source=DataSourceStatus('price')
    snap=SystemSnapshot(AT,NodeStatus('test'),(source,),DecisionStatus('shadow'),ExecutionStatus('execution'),PositionStatus('positions'),ScientificStatus(source))
    data=snap.to_dict()
    assert data['sources'][0]['details']=={} and data['mode']=='UNKNOWN'
    assert data['science']['edge']=='NOT DEMONSTRATED'
    assert replace(snap)==snap
    with pytest.raises(FrozenInstanceError): snap.mode='LIVE'
    with pytest.raises(ValueError): replace(snap.science,edge='VALIDATED')
    with pytest.raises(ValueError): replace(source,source_at='2026-10-05T12:00:00')
    with pytest.raises(ValueError): replace(source,state=State.AVAILABLE)


def test_reader_missing_corrupt_stale_provenance_and_no_writes(tmp_path):
    from core.runtime.readers import Source,read_source
    from core.scientific.multi_market_capture import commitment
    path=tmp_path/'health.json'
    source=Source('collector','collector',str(path),'laptop',max_age_seconds=1)
    assert read_source(source,snapshot_at=AT).state is State.UNAVAILABLE
    assert not path.exists()
    path.write_text('{broken')
    assert read_source(source,snapshot_at=AT).state is State.INVALID
    payload=dict(pid=123,status='RUNNING',next_expected_cycle=AT,observed_at='2026-10-05T11:00:00+00:00',integrity='PASS')
    path.write_text(canonical(dict(payload=payload,commitment=commitment(payload))))
    before=path.read_bytes(),path.stat().st_mtime_ns
    result=read_source(source,snapshot_at=AT)
    assert result.state is State.STALE and result.source=='laptop/collector'
    assert json.loads(result.details_json)['process_liveness']=='UNVERIFIED'
    assert (path.read_bytes(),path.stat().st_mtime_ns)==before
    assert read_source(replace(source,max_age_seconds=3600),snapshot_at=AT).state is State.AVAILABLE
    payload['pid']=124
    path.write_text(canonical(dict(payload=payload,commitment='f'*64)))
    assert read_source(source,snapshot_at=AT).state is State.INVALID


def test_price_inspection_never_initializes_sqlite(tmp_path):
    import sqlite3
    from core.runtime.readers import Source,read_source
    path=tmp_path/'price.sqlite'
    source=Source('price','price',str(path),'laptop',str(tmp_path))
    assert read_source(source,snapshot_at=AT).state is State.UNAVAILABLE
    assert not path.exists()
    with sqlite3.connect(path) as db: db.execute('CREATE TABLE unrelated (x)')
    before=path.read_bytes()
    assert read_source(source,snapshot_at=AT).state is State.INVALID
    assert path.read_bytes()==before
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()==[('unrelated',)]


def test_shadow_reader_real_schema_no_write(tmp_path,monkeypatch):
    from tests.test_trading_decision_plane import shadow
    from core.scientific.shadow_decision_ledger import append_shadow_decision
    from core.runtime.readers import Source,read_source
    from core.scientific import multi_market_capture as c
    d=shadow(tmp_path/'fixture',monkeypatch)
    monkeypatch.setattr(c,'_now',lambda:d.available_at)
    path=tmp_path/'shadow.sqlite'
    append_shadow_decision(path,d)
    before=path.read_bytes()
    result=read_source(Source('shadow','shadow',str(path),'node'),snapshot_at=d.available_at.isoformat())
    assert result.state is State.AVAILABLE
    assert json.loads(result.details_json)['decision_id']==d.decision_id
    assert json.loads(result.details_json)['mode']=='SHADOW'
    assert path.read_bytes()==before
