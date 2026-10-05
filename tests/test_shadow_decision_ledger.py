from dataclasses import replace
from datetime import timedelta
import sqlite3
import pytest
from core.scientific import shadow_decision_ledger as l
from tests.test_trading_decision_plane import shadow


def test_transactional_append_reopen_exact_replay(tmp_path,monkeypatch):
    d=shadow(tmp_path,monkeypatch)
    monkeypatch.setattr(l.c,'_now',lambda:d.available_at+timedelta(seconds=1))
    path=tmp_path/'ledger.sqlite'
    first=l.append_shadow_decision(path,d)
    assert l.append_shadow_decision(path,d)==first
    changed=replace(d,configuration_commitment='e'*64)
    assert l.append_shadow_decision(path,changed)!=first
    assert l.verify_shadow_ledger(path)==(d.decision_id,changed.decision_id)


def test_corruption_and_unrelated_database_fail_closed(tmp_path,monkeypatch):
    d=shadow(tmp_path,monkeypatch); monkeypatch.setattr(l.c,'_now',lambda:d.available_at)
    path=tmp_path/'ledger.sqlite'; l.append_shadow_decision(path,d)
    with sqlite3.connect(path) as db: db.execute("UPDATE shadow_entries SET previous_hash='bad' WHERE seq=1")
    with pytest.raises(ValueError): l.append_shadow_decision(path,d)
    other=tmp_path/'other.sqlite'
    with sqlite3.connect(other) as db: db.execute('CREATE TABLE other (value TEXT)')
    with pytest.raises(ValueError): l.append_shadow_decision(other,d)
    with sqlite3.connect(other) as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()==[('other',)]


def test_future_recording_rejected(tmp_path,monkeypatch):
    d=shadow(tmp_path,monkeypatch); monkeypatch.setattr(l.c,'_now',lambda:d.available_at-timedelta(seconds=1))
    with pytest.raises(ValueError): l.append_shadow_decision(tmp_path/'ledger.sqlite',d)
    assert l.verify_shadow_ledger(tmp_path/'ledger.sqlite')==()
