"""Adapter regression tests with isolated transport; live capture is separate."""
from datetime import datetime, timedelta, timezone
from dataclasses import FrozenInstanceError
from decimal import Decimal
from email.message import Message
from pathlib import Path
import json
import pytest

from core.scientific import book_ticker_capture as c
from core.scientific.execution_observation import Measure
from core.scientific.nuisance_pilot_contracts import InputStatus, DatasetRole

T = datetime(2020, 1, 1, tzinfo=timezone.utc)


def capture(tmp_path, monkeypatch, body=None, clock_hook=None):
    raw = json.dumps(body if body is not None else dict(symbol="BTCUSDT", bidPrice="100", askPrice="101", time=1577836800000)).encode()
    class Response:
        status = 200
        headers = Message()
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(raw))
        def read(self, limit): return raw[:limit]
        def geturl(self): return c.URL
        def __enter__(self): return self
        def __exit__(self, *args): pass
    times = iter((T, T+timedelta(seconds=1), T+timedelta(seconds=2)))
    ticks = iter((10., 11.))
    def now():
        at = next(times)
        if clock_hook is not None:
            clock_hook(at)
        return at
    monkeypatch.setattr(c, "_now", now)
    monkeypatch.setattr(c, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(c, "_open", lambda: Response())
    return c.capture_book(tmp_path / "capture")


def test_update_id_and_persistence_before_availability(tmp_path, monkeypatch):
    events = []
    write, project = c._write, c._project
    def tracked_write(path, content):
        write(path, content)
        events.append(path.name)
    def tracked_project(*args):
        result = project(*args)
        if args[2] is None:
            events.append("validated_without_availability")
        return result
    def clock_hook(at):
        if at == T + timedelta(seconds=2):
            assert events == ["response.raw", "receipt.json", "validated_without_availability"]
            assert not (tmp_path / "capture" / "available.json").exists()
    monkeypatch.setattr(c, "_write", tracked_write)
    monkeypatch.setattr(c, "_project", tracked_project)
    body = dict(symbol="BTCUSDT", bidPrice="85309.50", bidQty="12.743",
                askPrice="85309.60", askQty="5.537", time=1577836800000, lastUpdateId=11733694562833)
    obs = capture(tmp_path, monkeypatch, body, clock_hook)
    assert obs.receipts[0].source_update_id == body["lastUpdateId"]
    assert json.loads(obs.receipts[0].response_json) == body
    assert obs.receipts[0].exchange_at == T
    assert events[-1] == "available.json"


def test_incomplete_capture_cannot_be_finalized_retrospectively(tmp_path, monkeypatch):
    write = c._write
    def interrupted_write(path, content):
        if path.name == "available.json":
            raise OSError("simulated interrupted persistence")
        write(path, content)
    monkeypatch.setattr(c, "_write", interrupted_write)
    with pytest.raises(OSError):
        capture(tmp_path, monkeypatch, dict(symbol="BTCUSDT", bidPrice="100", askPrice="101", lastUpdateId=123))
    root = tmp_path / "capture"
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    monkeypatch.setattr(c, "_write", write)
    def forbidden_http():
        pytest.fail("must not recapture an existing directory")
    monkeypatch.setattr(c, "_open", forbidden_http)
    with pytest.raises(FileNotFoundError):
        c.load_book(root)
    with pytest.raises(TypeError):
        c.load_book(root, available_at=T)
    with pytest.raises(FileExistsError):
        c.capture_book(root)
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}


def test_unknown_wire_field_not_stripped(tmp_path, monkeypatch):
    body = dict(symbol="BTCUSDT", bidPrice="100", askPrice="101", lastUpdateId=123, unexplained=1)
    with pytest.raises(ValueError):
        capture(tmp_path, monkeypatch, body)
    assert json.loads((tmp_path / "capture" / "response.raw").read_bytes()) == body
    assert not (tmp_path / "capture" / "available.json").exists()


def test_capture_reopen_projection_and_unknowns(tmp_path, monkeypatch):
    obs = capture(tmp_path, monkeypatch)
    again = c.load_book(tmp_path / "capture")
    assert obs == again and obs.observation_id == again.observation_id
    assert obs.dataset_role is DatasetRole.PILOT
    assert obs.value(Measure.BID_USDT_PER_BTC) == 100
    assert obs.value(Measure.ASK_USDT_PER_BTC) == 101
    assert obs.mid_usdt_per_btc == Decimal("100.5") and obs.spread_usdt_per_btc == 1
    receipt = obs.receipts[0]
    assert receipt.request_started_at == receipt.exchange_at == T
    assert receipt.received_at == T + timedelta(seconds=1)
    assert receipt.available_at == T + timedelta(seconds=2)
    assert obs.slippage is None and not hasattr(obs, "total_cost")
    for measure in (Measure.MAKER_FEE_RATE_FRACTION, Measure.LATEST_FUNDING_RATE_FRACTION):
        assert obs.value(measure) is None
    early = c.load_book(tmp_path / "capture", decision_at=T)
    assert early.status(Measure.BID_USDT_PER_BTC) is InputStatus.LATE
    assert early.mid_usdt_per_btc is None
    with pytest.raises(FrozenInstanceError):
        receipt.received_at = T
    with pytest.raises(FileExistsError):
        c.capture_book(tmp_path / "capture")


@pytest.mark.parametrize("body", [{"symbol":"ETHUSDT","bidPrice":"100","askPrice":"101"},
    {"symbol":"BTCUSDT","bidPrice":"102","askPrice":"101"}, {"symbol":"BTCUSDT"},
    [1,2], {"symbol":"BTCUSDT","bidPrice":"NaN","askPrice":"101"}])
def test_invalid_response_preserved_without_availability(tmp_path, monkeypatch, body):
    with pytest.raises((ValueError,TypeError)):
        capture(tmp_path, monkeypatch, body)
    assert (tmp_path / "capture" / "response.raw").exists()
    assert not (tmp_path / "capture" / "available.json").exists()


@pytest.mark.parametrize("field,value", [("received_at","2020-01-01T00:00:00+00:00"),
    ("venue","Spot"), ("product","inverse"), ("role","DISCOVERY")])
def test_metadata_substitution_fails(tmp_path, monkeypatch, field, value):
    capture(tmp_path, monkeypatch)
    path=tmp_path / "capture" / "receipt.json"
    meta=json.loads(path.read_bytes()); meta[field]=value; path.write_bytes(c._json(meta))
    with pytest.raises(ValueError): c.load_book(tmp_path / "capture")


def test_raw_and_availability_substitution_fail(tmp_path, monkeypatch):
    capture(tmp_path, monkeypatch)
    root=tmp_path / "capture"
    original=(root / "response.raw").read_bytes()
    (root / "response.raw").write_bytes(original.replace(b'100', b'999'))
    with pytest.raises(ValueError): c.load_book(root)
    (root / "response.raw").write_bytes(original)
    ready=json.loads((root / "available.json").read_bytes())
    ready["available_at"] = T.isoformat()
    (root / "available.json").write_bytes(c._json(ready))
    with pytest.raises(ValueError): c.load_book(root)


@pytest.mark.parametrize("key", ["bid", "ask", "received_at", "available_at", "pnl", "outcome"])
def test_caller_cannot_supply_factual_values(tmp_path, key):
    with pytest.raises(TypeError): c.capture_book(tmp_path / "unused", **{key: 1})
    with pytest.raises(TypeError): c.load_book(tmp_path / "unused", **{key: 1})


def test_changed_raw_changes_commitment_and_compile(tmp_path, monkeypatch):
    first=capture(tmp_path / "a",monkeypatch)
    second=capture(tmp_path / "b",monkeypatch,dict(symbol="BTCUSDT",bidPrice="100",askPrice="102",time=1577836800000))
    assert first.receipts[0].receipt_id != second.receipts[0].receipt_id
    assert first.observation_id != second.observation_id
    compile(Path(c.__file__).read_text(encoding="utf-8"),c.__file__,"exec")
