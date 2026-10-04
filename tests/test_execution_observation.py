"""Synthetic receipt-shaped fixtures, not a claim of live capture."""
from dataclasses import replace, FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
import json
import os
import subprocess
import sys
import pytest

from core.scientific import execution_observation as e
from core.scientific.nuisance_pilot_contracts import DatasetRole, InputStatus

T = datetime(2020, 1, 1, tzinfo=timezone.utc)


def receipt(kind=e.EvidenceKind.BOOK, payload=None, **changes):
    body = payload if payload is not None else {"symbol": "BTCUSDT", "bidPrice": "100.10", "askPrice": "100.30", "time": 1577836800000}
    return e.ExecutionReceipt(**{**dict(kind=kind, source=kind.value, receipt_id=kind.name,
        provenance_sha256="a" * 64, response_json=json.dumps(body), dataset_role=DatasetRole.PILOT,
        request_started_at=T - timedelta(seconds=1), received_at=T, available_at=T,
        fee_account_reference="test-account-scope" if kind is e.EvidenceKind.USER_FEES else None), **changes})


def observation(receipts=None, **changes):
    return e.ExecutionObservation(**{**dict(instrument="BTCUSDT", venue="Binance USDⓈ-M", product="linear perpetual",
        dataset_role=DatasetRole.PILOT, decision_at=T, receipts=(receipt(),) if receipts is None else receipts), **changes})


def test_quotes_mid_spread_and_unknown_components():
    item = observation()
    assert item.value(e.Measure.BID_USDT_PER_BTC) == Decimal("100.10")
    assert item.mid_usdt_per_btc == Decimal("100.20")
    assert item.spread_usdt_per_btc == Decimal("0.20")
    assert item.slippage is None
    for measure in (e.Measure.MAKER_FEE_RATE_FRACTION, e.Measure.TAKER_FEE_RATE_FRACTION,
                    e.Measure.LATEST_FUNDING_RATE_FRACTION, e.Measure.MARK_USDT_PER_BTC):
        assert item.value(measure) is None
        assert item.status(measure) is InputStatus.UNKNOWN
    assert not hasattr(item, "total_cost")


def test_missing_quotes_unknown_not_zero():
    item = observation(())
    assert item.mid_usdt_per_btc is None and item.spread_usdt_per_btc is None
    partial = observation((receipt(payload={"symbol":"BTCUSDT", "bidPrice":"100"}),))
    assert partial.value(e.Measure.BID_USDT_PER_BTC) == 100
    assert partial.value(e.Measure.ASK_USDT_PER_BTC) is None
    assert partial.spread_usdt_per_btc is None
    zero_spread = observation((receipt(payload={"symbol":"BTCUSDT", "bidPrice":"100", "askPrice":"100"}),))
    assert zero_spread.spread_usdt_per_btc == 0


@pytest.mark.parametrize("changes", [dict(bidPrice="101",askPrice="100"), dict(bidPrice="0"),
    dict(askPrice="NaN"), dict(bidPrice=100.1), dict(symbol="ETHUSDT"), dict(pnl="1"), dict(metadata={"future":1})])
def test_invalid_payload_rejected(changes):
    with pytest.raises((ValueError, TypeError)):
        receipt(payload={"symbol":"BTCUSDT","bidPrice":"100","askPrice":"101", **changes})


@pytest.mark.parametrize("changes,status", [
    ({"available_at":T+timedelta(microseconds=1)}, InputStatus.LATE),
    ({"available_at":None}, InputStatus.UNKNOWN),
    ({"received_at":None}, InputStatus.UNKNOWN),
])
def test_late_and_unknown_never_expose_causal_values(changes, status):
    item = observation((receipt(**changes),))
    assert item.status(e.Measure.BID_USDT_PER_BTC) is status
    assert item.value(e.Measure.BID_USDT_PER_BTC) is None
    assert item.mid_usdt_per_btc is None


def test_time_evidence_not_interchangeable():
    item = receipt(received_at=None, available_at=None)
    assert item.exchange_at == T
    assert item.received_at is None and item.status_at(T) is InputStatus.UNKNOWN
    with pytest.raises(ValueError, match="exchange"):
        receipt(received_at=T-timedelta(seconds=1))
    with pytest.raises(ValueError, match="availability"):
        receipt(available_at=T-timedelta(seconds=1))
    with pytest.raises(ValueError):
        receipt(available_at=T.replace(tzinfo=None))
    with pytest.raises(ValueError, match="request"):
        receipt(request_started_at=T+timedelta(seconds=1))


@pytest.mark.parametrize("changes", [{"instrument":"ETHUSDT"}, {"venue":"spot"}, {"product":"inverse"},
                                       {"dataset_role":DatasetRole.CONFIRMATION}])
def test_universe_and_role_mismatch(changes):
    with pytest.raises(ValueError):
        observation(**changes)


def test_fee_and_funding_fraction_units_and_distinct_sources():
    fees = receipt(e.EvidenceKind.USER_FEES, {"symbol":"BTCUSDT","makerCommissionRate":"0.0002","takerCommissionRate":"0.0005"})
    funding = receipt(e.EvidenceKind.MARK_FUNDING, {"symbol":"BTCUSDT","lastFundingRate":"-0.001", "markPrice":"100.2", "indexPrice":"100.1", "time":1577836800000,"nextFundingTime":1577865600000})
    item = observation((receipt(), fees, funding))
    assert item.value(e.Measure.TAKER_FEE_RATE_FRACTION) == Decimal("0.0005")
    assert item.value(e.Measure.LATEST_FUNDING_RATE_FRACTION) == Decimal("-0.001")
    assert item.value(e.Measure.MARK_USDT_PER_BTC) == Decimal("100.2")
    assert funding.exchange_at == T  # Next scheduled time is not availability/payment.
    assert fees.exchange_at is None
    assert item.slippage is None and not hasattr(item, "funding_payment")
    with pytest.raises(TypeError):
        replace(fees, fee_account_reference=None)
    with pytest.raises(ValueError):
        replace(fees, source="assumed-5-bps")
    for invalid in ("5", "5 bps", "0.05%", 0.0005):
        with pytest.raises((ValueError, TypeError, InvalidOperation)):
            receipt(e.EvidenceKind.USER_FEES, {"symbol":"BTCUSDT","takerCommissionRate":invalid})
    zero = receipt(e.EvidenceKind.USER_FEES, {"symbol":"BTCUSDT","takerCommissionRate":"0"})
    assert observation((zero,)).value(e.Measure.TAKER_FEE_RATE_FRACTION) == 0


def test_identity_input_order_precision_and_immutability():
    source = {"symbol":"BTCUSDT","bidPrice":"100.10","askPrice":"100.30"}
    first = receipt(payload=source)
    same = receipt(payload=dict(reversed(tuple(source.items()))))
    assert first.identity == same.identity
    source["askPrice"] = "999"
    item = observation((first,))
    identity = item.observation_id
    assert item.spread_usdt_per_btc == Decimal("0.20")
    with localcontext() as context:
        context.prec = 2
        assert observation((same,)).observation_id == identity
        assert item.mid_usdt_per_btc == Decimal("100.20")
    with pytest.raises(FrozenInstanceError):
        first.response_json = "{}"
    with pytest.raises(TypeError):
        observation([first])
    with pytest.raises(TypeError):
        receipt(response_json=source)
    with pytest.raises(ValueError):
        observation((first, same))
    fees = receipt(e.EvidenceKind.USER_FEES, {"symbol":"BTCUSDT"})
    assert observation((first,fees)).observation_id == observation((fees,first)).observation_id
    assert replace(item, decision_at=T+timedelta(seconds=1)).observation_id != identity


@pytest.mark.parametrize("name", ["pnl", "outcome", "future_price", "slippage", "total_cost", "assumed_fee_bps"])
def test_no_cost_assumptions_or_outcome_api(name):
    with pytest.raises(TypeError):
        observation(**{name: 5})
    assert name not in {f.name for f in fields(e.ExecutionObservation)}


def test_duplicate_json_fields_and_unproven_provenance_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        receipt(response_json='{"symbol":"BTCUSDT","bidPrice":"1","bidPrice":"2"}')
    with pytest.raises((ValueError,TypeError)):
        receipt(provenance_sha256="")


def test_global_decimal_context_cannot_round_invalid_rate_into_range():
    with localcontext() as context:
        context.prec = 2
        with pytest.raises(ValueError, match="decimal fraction"):
            receipt(e.EvidenceKind.USER_FEES, {"symbol":"BTCUSDT","takerCommissionRate":"1.001"})


def test_cross_process_identity_and_compile():
    script = ("import sys;sys.path.insert(0,'tests');import test_execution_observation as t;"
              "body={'symbol':'BTCUSDT','bidPrice':'100','askPrice':'101'};"
              "body=dict(reversed(tuple(body.items()))) if sys.argv[1]=='reverse' else body;"
              "print(t.observation((t.receipt(payload=body),)).observation_id)")
    values = [subprocess.check_output([sys.executable,"-B","-c",script,order],text=True,
        cwd=Path(__file__).resolve().parents[1], env={**os.environ,"PYTHONHASHSEED":seed,
        "PYTHONDONTWRITEBYTECODE":"1"}) for order,seed in (("forward","13"),("reverse","79"))]
    assert values[0] == values[1]
    compile(Path(e.__file__).read_text(encoding="utf-8"), e.__file__, "exec")
