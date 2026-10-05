"""Transactional append-only API for shadow decisions; trusted local custody."""
from dataclasses import replace
from datetime import datetime
from pathlib import Path
import json
import sqlite3
from . import multi_market_capture as c
from .trading_decision_plane import ShadowCapitalDecision,_plain

SCHEMA='shadow-decisions-v0'


def _schema(db):
    tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    if tables!={'shadow_metadata','shadow_entries'} or db.execute('SELECT schema FROM shadow_metadata').fetchall()!=[(SCHEMA,)]:
        raise ValueError('not a shadow decision ledger')


def _verify(db):
    _schema(db); previous='0'*64; last_at=None; identities=[]
    for expected,row in enumerate(db.execute('SELECT seq,decision_id,body,recorded_at,previous_hash,entry_hash FROM shadow_entries ORDER BY seq'),1):
        seq,identity,body,at,prior,entry=row
        data=json.loads(body); cid=data.pop('decision_id')
        recorded=datetime.fromisoformat(at); available=datetime.fromisoformat(data['available_at']); c.utc(recorded); c.utc(available)
        if body!=c._json(dict(data,decision_id=cid)).decode() or cid!=identity or c.commitment(data)!=identity:
            raise ValueError('shadow decision content mismatch')
        if seq!=expected or prior!=previous or entry!=c.commitment((seq,identity,body,at,prior)):
            raise ValueError('shadow ledger chain mismatch')
        if recorded<available or (last_at is not None and recorded<last_at): raise ValueError('noncausal ledger clock')
        previous=entry; last_at=recorded; identities.append(identity)
    return tuple(identities),previous,last_at


def verify_shadow_ledger(path):
    path=Path(path).resolve()
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
        return _verify(db)[0]


def append_shadow_decision(path,decision):
    if type(decision) is not ShadowCapitalDecision: raise TypeError('finalized shadow decision required')
    if replace(decision)!=decision: raise ValueError('decision verification failed')
    path=Path(path).resolve(); path.parent.mkdir(parents=True,exist_ok=True)
    # Refuse unrelated existing SQLite files before any writable connection.
    if path.exists(): verify_shadow_ledger(path)
    else:
        path.touch(exist_ok=False)
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE shadow_metadata (schema TEXT NOT NULL)')
            db.execute('INSERT INTO shadow_metadata VALUES (?)',(SCHEMA,))
            db.execute('CREATE TABLE shadow_entries (seq INTEGER PRIMARY KEY, decision_id TEXT UNIQUE NOT NULL, body TEXT NOT NULL, recorded_at TEXT NOT NULL, previous_hash TEXT NOT NULL, entry_hash TEXT UNIQUE NOT NULL)')
    body=c._json(_plain(decision)).decode()
    with sqlite3.connect(path,isolation_level=None,timeout=5) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        try:
            ids,previous,last_at=_verify(db)
            old=db.execute('SELECT body,entry_hash FROM shadow_entries WHERE decision_id=?',(decision.decision_id,)).fetchone()
            if old is not None:
                if old[0]!=body: raise ValueError('conflicting shadow replay')
                db.execute('COMMIT'); return old[1]
            at=c._now(); c.utc(at)
            if at<decision.available_at or (last_at is not None and at<last_at): raise ValueError('ledger clock reversed/future decision')
            seq=len(ids)+1; entry=c.commitment((seq,decision.decision_id,body,at.isoformat(),previous))
            db.execute('INSERT INTO shadow_entries VALUES (?,?,?,?,?,?)',(seq,decision.decision_id,body,at.isoformat(),previous,entry))
            db.execute('COMMIT'); return entry
        except Exception:
            db.execute('ROLLBACK'); raise
