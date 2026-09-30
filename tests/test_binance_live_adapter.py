from datetime import datetime,timezone
import pytest
from core.market_mechanics.binance_live_adapter import normalize_bundle,latest_closed_kline,fetch_once

def bundle():
    end=int(datetime(2026,10,1,1,tzinfo=timezone.utc).timestamp()*1000)
    return {'oi':{'timestamp':end,'sumOpenInterest':'100','sumOpenInterestValue':'10000'},
      'top_account':{'timestamp':end,'longShortRatio':'1.1'},
      'top_position':{'timestamp':end,'longShortRatio':'1.2'},
      'global':{'timestamp':end,'longShortRatio':'1.3'},
      'taker':{'timestamp':end-300000,'buySellRatio':'1.4'}}

def test_start_end_alignment_and_no_mixed_period():
    x=normalize_bundle(bundle());assert x['timestamp']=='2026-10-01T00:59:59.999999+00:00'
    y=bundle();y['taker']['timestamp']-=300000
    with pytest.raises(ValueError,match='mixed'):normalize_bundle(y)

def test_bar_must_be_closed():
    start=int(datetime(2026,10,1,0,tzinfo=timezone.utc).timestamp()*1000)
    row=[start,'100','101','99','100','1']
    with pytest.raises(ValueError,match='fully closed'):latest_closed_kline([row],datetime(2026,10,1,0,59,tzinfo=timezone.utc))
    assert latest_closed_kline([row],datetime(2026,10,1,1,tzinfo=timezone.utc))['close']==100

def test_restricted_location_fails_closed():
    class Response:
        status_code=451
    class Session:
        def get(self,*a,**kw):return Response()
    with pytest.raises(RuntimeError,match='451'):fetch_once(Session(),clock=lambda:datetime(2026,10,1,1,tzinfo=timezone.utc))
