"""Transport fixtures only; funding observation is not a payment."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.message import Message
import json
import pytest
from core.scientific import premium_index_capture as c
from core.scientific.execution_observation import Measure
from core.scientific.nuisance_pilot_contracts import InputStatus

T = datetime(2020, 1, 1, tzinfo=timezone.utc)
BODY = dict(symbol="BTCUSDT", markPrice="100.1", indexPrice="100", estimatedSettlePrice="100",
            lastFundingRate="-0.0001", interestRate="0.0001", nextFundingTime=1577865600000, time=1577836800000)


def capture(tmp_path, monkeypatch, body=None):
    raw = json.dumps(BODY if body is None else body).encode()
    class Response:
        status = 200
        headers = Message()
        headers['Content-Type'] = 'application/json'
        headers['Content-Length'] = str(len(raw))
        def read(self, limit): return raw[:limit]
        def geturl(self): return c.URL
        def __enter__(self): return self
        def __exit__(self, *args): pass
    times = iter((T, T+timedelta(seconds=1), T+timedelta(seconds=2)))
    ticks = iter((10., 11.))
    monkeypatch.setattr(c, '_now', lambda: next(times))
    monkeypatch.setattr(c, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(c, '_open', lambda: Response())
    return c.capture_premium(tmp_path/'capture')


def test_preserves_wire_fields_times_units_and_reopens(tmp_path, monkeypatch):
    obs = capture(tmp_path, monkeypatch)
    r = obs.receipts[0]
    assert json.loads(r.response_json) == BODY
    assert obs.value(Measure.LATEST_FUNDING_RATE_FRACTION) == Decimal('-0.0001')
    assert obs.value(Measure.MARK_USDT_PER_BTC) == Decimal('100.1')
    assert obs.value(Measure.INDEX_USDT_PER_BTC) == Decimal('100')
    assert r.exchange_at == T
    assert r.received_at == T+timedelta(seconds=1)
    assert r.available_at == T+timedelta(seconds=2)
    assert c.load_premium(tmp_path/'capture') == obs
    assert c.load_premium(tmp_path/'capture', decision_at=T).status(Measure.MARK_USDT_PER_BTC) is InputStatus.LATE
    assert obs.value(Measure.MAKER_FEE_RATE_FRACTION) is None and obs.slippage is None
    assert not hasattr(obs, 'funding_payment') and not hasattr(obs, 'total_cost')
    with pytest.raises(FileExistsError): c.capture_premium(tmp_path/'capture')


@pytest.mark.parametrize('extra', [{'unknown':1}, {'symbol':'ETHUSDT'}, {'markPrice':None}, {'lastFundingRate':'NaN'}])
def test_fail_closed_retains_raw_without_availability(tmp_path, monkeypatch, extra):
    with pytest.raises((ValueError, TypeError)):
        capture(tmp_path, monkeypatch, {**BODY, **extra})
    assert (tmp_path/'capture'/'response.raw').exists()
    assert not (tmp_path/'capture'/'available.json').exists()
    with pytest.raises(FileNotFoundError): c.load_premium(tmp_path/'capture')


@pytest.mark.parametrize('field', ['available_at', 'received_at', 'markPrice', 'lastFundingRate', 'outcome'])
def test_no_caller_facts(tmp_path, field):
    with pytest.raises(TypeError): c.capture_premium(tmp_path, **{field:1})
    with pytest.raises(TypeError): c.load_premium(tmp_path, **{field:1})


def test_commitment_tampering(tmp_path, monkeypatch):
    capture(tmp_path, monkeypatch)
    p=tmp_path/'capture'/'response.raw'
    p.write_bytes(p.read_bytes().replace(b'100.1',b'999.1'))
    with pytest.raises(ValueError): c.load_premium(tmp_path/'capture')
