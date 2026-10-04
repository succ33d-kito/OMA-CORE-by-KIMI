"""HTTP transport fixtures exercise the real capture API; no live source claims."""
from dataclasses import replace, FrozenInstanceError
from datetime import datetime, timedelta, timezone
from email.message import Message
from pathlib import Path
import os
import subprocess
import sys
import sqlite3
import pytest

from core.scientific import real_event_receipt as r
from core.scientific.nuisance_pilot_contracts import DatasetRole
from core.scientific.nuisance_pilot_sampling import Relation, ShockEvidence, decision_slot

T = datetime(2020, 1, 1, 10, tzinfo=timezone.utc)
URL = "https://example.test/document"


class Response:
    status = 200
    def __init__(self, raw):
        self.raw = raw
        self.headers = Message()
        self.headers["Content-Type"] = "text/plain"
        self.headers["Content-Length"] = str(len(raw))
    def geturl(self):
        return URL
    def read(self, limit):
        return self.raw[:limit]
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


def setup_store(tmp_path, monkeypatch, kind=r.ContentKind.FULL_DOCUMENT):
    state = {"now": T, "raw": b"Bitcoin announcement. Full experimental document body."}
    monkeypatch.setattr(r, "_now", lambda: state["now"])
    monkeypatch.setattr(r, "urlopen", lambda *args, **kwargs: Response(state["raw"]))
    store = r.RealEventStore(tmp_path / "events.sqlite")
    store.authorize_source("official", "v1", URL, kind)
    state["now"] = T + timedelta(minutes=23)
    return store, state


def evidence(relation=Relation.NEW_EVENT, prior=None):
    return r.AdmissionEvidence("Bitcoin announcement", 1,
        ShockEvidence.OFFICIAL_ANNOUNCEMENT if prior is None else ShockEvidence.EXPLICIT_RELATION,
        "authority", "shock-1", relation, prior)


def test_full_receipt_to_real_opportunity_and_reopen(tmp_path, monkeypatch):
    store, state = setup_store(tmp_path, monkeypatch)
    receipt = store.capture("official", "r1", DatasetRole.PILOT)
    candidate = store.admit(receipt.receipt_id, evidence())
    assert candidate.reservation_id and not candidate.reasons
    assert receipt.received_at <= receipt.available_at
    state["now"] = T + timedelta(hours=1)
    population = store.close(state["now"])
    assert len(population) == 1
    assert population[0].event_id == candidate.envelope.event_id
    assert population[0].inputs[0].validator_version == r.REAL_VERSION
    assert population == r.RealEventStore(tmp_path / "events.sqlite").population()
    assert all(i.value_hash is None for i in population[0].inputs[1:])
    with pytest.raises(FrozenInstanceError):
        receipt.content = "changed"


@pytest.mark.parametrize("kind", [r.ContentKind.HEADLINE_ONLY, r.ContentKind.SNIPPET_ONLY, r.ContentKind.METADATA_ONLY])
def test_incomplete_content_not_admissible(tmp_path, monkeypatch, kind):
    store, _ = setup_store(tmp_path, monkeypatch, kind)
    receipt = store.capture("official", "r1", DatasetRole.PILOT)
    with pytest.raises(ValueError, match="full-content"):
        store.admit(receipt.receipt_id, evidence())


def test_unknown_availability_after_interrupted_ready_is_not_repaired(tmp_path, monkeypatch):
    store, _ = setup_store(tmp_path, monkeypatch)
    original = store._append
    def interrupted(kind, *args):
        if kind == "ready":
            raise OSError("interrupted")
        return original(kind, *args)
    monkeypatch.setattr(store, "_append", interrupted)
    with pytest.raises(OSError):
        store.capture("official", "r1", DatasetRole.PILOT)
    monkeypatch.setattr(store, "_append", original)
    receipt = store.capture("official", "r1", DatasetRole.PILOT)
    assert receipt.available_at is None
    with pytest.raises(ValueError, match="known availability"):
        store.admit(receipt.receipt_id, evidence())


@pytest.mark.parametrize("minute,second,expected", [(23, 0, 11), (59, 59, 11), (60, 0, 12)])
def test_slot_boundaries(tmp_path, monkeypatch, minute, second, expected):
    store, state = setup_store(tmp_path, monkeypatch)
    state["now"] = T + timedelta(minutes=minute, seconds=second)
    receipt = store.capture("official", "r1", DatasetRole.PILOT)
    candidate = store.admit(receipt.receipt_id, evidence())
    assert decision_slot(receipt.received_at)[0].hour == expected
    state["now"] = T.replace(hour=expected)
    assert store.close(state["now"])[0].decision_at == state["now"]


def test_late_processing_no_rollover(tmp_path, monkeypatch):
    store, state = setup_store(tmp_path, monkeypatch)
    receipt = store.capture("official", "r1", DatasetRole.PILOT)
    state["now"] = T + timedelta(hours=1, seconds=1)
    store.admit(receipt.receipt_id, evidence())
    assert store.close(T + timedelta(hours=1)) == ()
    state["now"] = T + timedelta(hours=2)
    assert store.close(state["now"]) == ()


def test_duplicate_idempotence_revision_conflict_and_no_mutation(tmp_path, monkeypatch):
    store, state = setup_store(tmp_path, monkeypatch)
    original = store.capture("official", "r1", DatasetRole.PILOT)
    candidate = store.admit(original.receipt_id, evidence())
    state["now"] += timedelta(seconds=1)
    assert store.capture("official", "r1", DatasetRole.PILOT) == original
    with pytest.raises(ValueError, match="already frozen"):
        store.admit(original.receipt_id, evidence(Relation.DUPLICATE, candidate.envelope.event_id))
    state["raw"] += b" Revision changed."
    with pytest.raises(ValueError, match="revision/role conflict"):
        store.capture("official", "r1", DatasetRole.PILOT)
    assert store.receipt(original.receipt_id) == original


@pytest.mark.parametrize("relation", [Relation.UPDATE, Relation.CORRECTION, Relation.SAME_CLUSTER_NEW_REPORT, Relation.NEW_EVENT])
def test_later_revision_cannot_replace_winner(tmp_path, monkeypatch, relation):
    store, state = setup_store(tmp_path, monkeypatch)
    first = store.capture("official", "r1", DatasetRole.PILOT)
    candidate = store.admit(first.receipt_id, evidence())
    state["now"] = T + timedelta(hours=1)
    before = store.close(state["now"])
    state["now"] += timedelta(seconds=1)
    state["raw"] += b" Later revision."
    second = store.capture("official", "r2", DatasetRole.PILOT)
    proof = evidence(relation, None if relation is Relation.NEW_EVENT else candidate.envelope.event_id)
    later = store.admit(second.receipt_id, proof)
    assert later.reservation_id == candidate.reservation_id
    assert second.content_hash != first.content_hash and second.receipt_id != first.receipt_id
    state["now"] += timedelta(hours=1)
    assert store.close(T + timedelta(hours=2)) == before


def test_correction_known_at_cutoff_invalidates_admission(tmp_path, monkeypatch):
    store, state = setup_store(tmp_path, monkeypatch)
    first = store.capture("official", "r1", DatasetRole.PILOT)
    candidate = store.admit(first.receipt_id, evidence())
    state["now"] += timedelta(minutes=1)
    second = store.capture("official", "r2", DatasetRole.PILOT)
    store.admit(second.receipt_id, evidence(Relation.CORRECTION, candidate.envelope.event_id))
    state["now"] = T + timedelta(hours=1)
    assert store.close(state["now"]) == ()


def test_source_authorization_roles_and_btc_binding(tmp_path, monkeypatch):
    store, state = setup_store(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="unauthorized"):
        store.capture("unknown", "r1", DatasetRole.PILOT)
    first = store.capture("official", "r1", DatasetRole.PILOT)
    with pytest.raises(ValueError, match="frozen"):
        store.authorize_source("later", "v1", URL, r.ContentKind.FULL_DOCUMENT)
    with pytest.raises(ValueError, match="role"):
        store.capture("official", "r2", DatasetRole.CONFIRMATION)
    with pytest.raises(ValueError, match="BTC"):
        store.admit(first.receipt_id, replace(evidence(), btc_quote="generic crypto"))
    state["raw"] = b"Generic crypto announcement."
    second = store.capture("official", "r2", DatasetRole.PILOT)
    with pytest.raises(ValueError, match="BTC"):
        store.admit(second.receipt_id, evidence())


@pytest.mark.parametrize("name", ["received_at", "available_at", "published_at", "updated_at", "outcome", "pnl", "metadata"])
def test_no_backdating_or_outcome_inputs(tmp_path, monkeypatch, name):
    store, _ = setup_store(tmp_path, monkeypatch)
    with pytest.raises(TypeError):
        store.capture("official", "r1", DatasetRole.PILOT, **{name: T})


def test_clock_reversal_and_tamper_fail_closed(tmp_path, monkeypatch):
    store, state = setup_store(tmp_path, monkeypatch)
    first = store.capture("official", "r1", DatasetRole.PILOT)
    state["now"] = T - timedelta(seconds=1)
    with pytest.raises(ValueError, match="clock"):
        store.admit(first.receipt_id, evidence())
    with sqlite3.connect(tmp_path / "events.sqlite") as con:
        con.execute("UPDATE event_journal SET body='{}' WHERE seq=2")
    with pytest.raises(ValueError, match="integrity"):
        store.receipt(first.receipt_id)


def test_ready_cannot_precede_received_at(tmp_path, monkeypatch):
    store, _ = setup_store(tmp_path, monkeypatch)
    times = iter((T + timedelta(minutes=23), T + timedelta(minutes=23), T + timedelta(minutes=22)))
    monkeypatch.setattr(r, "_now", lambda: next(times))
    with pytest.raises(ValueError, match="clock"):
        store.capture("official", "r1", DatasetRole.PILOT)
    rows = store._rows()
    receipt_id = next(x["data"]["receipt_id"] for x in rows if x["kind"] == "receipt")
    assert store.receipt(receipt_id).available_at is None


@pytest.mark.parametrize("defect", ["redirect", "truncated"])
def test_wrong_source_or_incomplete_http_body_rejected(tmp_path, monkeypatch, defect):
    store, state = setup_store(tmp_path, monkeypatch)
    response = Response(state["raw"])
    if defect == "redirect":
        response.geturl = lambda: "https://other.test/document"
    else:
        response.headers.replace_header("Content-Length", str(len(state["raw"]) + 1))
    monkeypatch.setattr(r, "urlopen", lambda *args, **kwargs: response)
    with pytest.raises(ValueError):
        store.capture("official", "r1", DatasetRole.PILOT)
    assert not any(x["kind"] == "receipt" for x in store._rows())


def test_reproducibility_and_compile(tmp_path):
    script = ("import sys;sys.path.insert(0,'tests');import test_real_event_receipt as t;from pytest import MonkeyPatch;"
              "m=MonkeyPatch();s,state=t.setup_store(t.Path(sys.argv[1]),m);"
              "x=s.capture('official','r1',t.DatasetRole.PILOT);c=s.admit(x.receipt_id,t.evidence());"
              "print((x.receipt_id,x.content_hash,x.provenance_hash,c.reservation_id))")
    values = [subprocess.check_output([sys.executable, "-B", "-c", script, str(tmp_path / seed)], text=True,
        cwd=Path(__file__).resolve().parents[1], env={**os.environ, "PYTHONHASHSEED": seed,
        "PYTHONDONTWRITEBYTECODE": "1"}) for seed in ("13", "79")]
    assert values[0] == values[1]
    compile(Path(r.__file__).read_text(encoding="utf-8"), r.__file__, "exec")
