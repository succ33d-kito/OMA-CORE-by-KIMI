from datetime import timedelta
from dataclasses import FrozenInstanceError
from decimal import Decimal
import pytest
from core.scientific import multi_market_premium as p
from core.scientific import multi_market_capture as c
from tests.test_multi_market_capture import freeze,transport,T


def premium_rows():
    return [dict(symbol=s,markPrice='101',indexPrice='100',lastFundingRate='0.0001',
                 interestRate='0.0001',estimatedSettlePrice='100',time=1577840400000,nextFundingTime=1577865600000) for s in c.SYMBOLS]


def premium(tmp_path,monkeypatch,body=None):
    transport(monkeypatch,premium_rows() if body is None else body,T+timedelta(hours=1))
    return p.capture_premium_cycle(tmp_path/'premium',tmp_path/'universe')


def test_preservation_causal_times_and_reopen(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); result=premium(tmp_path,monkeypatch)
    assert p.load_premium_cycle(tmp_path/'premium',tmp_path/'universe')==result
    assert result.completeness=='COMPLETE' and len(result.members)==5
    for m in result.members:
        assert m.mark==101 and m.index==100 and m.funding_rate==Decimal('0.0001')
        assert m.received_at<=m.available_at<m.next_funding_at
        assert m.exchange_at==T+timedelta(hours=1) and m.role=='PILOT'
        assert not hasattr(m,'funding_payment') and not hasattr(m,'pnl')
    with pytest.raises(FrozenInstanceError): result.members=()
    with pytest.raises(FileExistsError): p.capture_premium_cycle(tmp_path/'premium',tmp_path/'universe')


def test_missing_member(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); result=premium(tmp_path,monkeypatch,premium_rows()[1:])
    assert result.completeness=='INCOMPLETE' and result.missing==(c.SYMBOLS[0],)


@pytest.mark.parametrize('change',[{'unknown':1},{'time':True},{'time':2577836800000},{'markPrice':'NaN'},{'lastFundingRate':None}])
def test_closed_wire(tmp_path,monkeypatch,change):
    freeze(tmp_path,monkeypatch); body=premium_rows(); body[0].update(change)
    with pytest.raises((ValueError,TypeError)): premium(tmp_path,monkeypatch,body)
    assert not (tmp_path/'premium'/'premium.json').exists()


def test_no_factual_overrides(tmp_path):
    with pytest.raises(TypeError): p.capture_premium_cycle(tmp_path,tmp_path,available_at=T)
