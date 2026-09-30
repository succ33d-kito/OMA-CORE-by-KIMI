from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import json
import pytest

from core.market_mechanics import build_market_state
from core.market_mechanics.regime import classify_regime
from core.scientific.probability_calibration import ForecastJournal
from core.decision_domain import DecisionJournal
from core.decision_domain.paper_adapter import record_paper_signal
from tests.test_paper_decision_adapter import signal


T = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)


def market(closes):
    bars = [dict(time=T-timedelta(hours=len(closes)-i), open=c, close=c, high=c*1.001,
                 low=c*.999, volume=1) for i,c in enumerate(closes)]
    return build_market_state("BTC", bars, source_id="fixture", observed_at=T, as_of=T)


def test_regime_axes_flat_trend_and_short_history():
    flat = classify_regime(market([100]*81))
    assert flat.structure == "range" and flat.direction == "flat"
    assert flat.volatility == "unknown"
    up = classify_regime(market([100+i for i in range(21)]))
    assert up.structure == "trend" and up.direction == "up"
    assert up.volatility == "unknown"
    assert "liquidity" in up.unknown_axes


def test_volatility_baseline_excludes_recent_window():
    prices = [100]
    for i in range(80):
        amplitude = .001 if i < 60 else .01
        prices.append(prices[-1]*(1 + amplitude*(1 if i%2 else -1)))
    regime = classify_regime(market(prices))
    assert regime.volatility == "high"
    assert regime.volatility_ratio > 9
    assert regime.structure == "range"


def test_regime_persisted_with_decision(tmp_path):
    journal = DecisionJournal(str(tmp_path/'journal.db'))
    m = market([100+i for i in range(81)])
    did = record_paper_signal(journal, SimpleNamespace(id="event",source="fixture",source_id=None),
                              None, signal(), market_state=m)
    saved, _ = journal.history(did)
    r = json.loads(saved['regime_snapshot'])
    assert r['market_state_id'] == saved['market_state_id']
    assert r['structure'] == 'trend'


def test_calibration_known_scores_and_immutable_resolutions(tmp_path):
    journal = ForecastJournal(str(tmp_path/'forecast.db'))
    params = dict(target="BTC close above initial close after 24h", issued_at=T,
                  available_at=T, horizon_end=T+timedelta(hours=24), model_version="test-v1")
    for i, (p,y) in enumerate(((.8,True),(.2,False))):
        journal.record(forecast_id=str(i), probability=p, **params)
        journal.resolve(str(i), outcome=y, observed_at=T+timedelta(hours=24),source_id="fixture")
    result = journal.evaluate(target=params['target'],model_version='test-v1')
    assert result['count'] == 2
    assert result['brier'] == pytest.approx(.04)
    assert result['log_loss'] == pytest.approx(.2231435513)
    with pytest.raises(ValueError,match="immutable"):
        journal.record(forecast_id='0',probability=.9,**params)
    with pytest.raises(ValueError,match="immutable"):
        journal.resolve('0',outcome=False,observed_at=T+timedelta(hours=24),source_id='fixture')
    assert journal.evaluate(target='other',model_version='test-v1')['brier'] is None


def test_probability_and_horizon_guards(tmp_path):
    j = ForecastJournal(str(tmp_path/'forecast.db'))
    params=dict(forecast_id='f',target='defined target',issued_at=T,available_at=T,
                horizon_end=T+timedelta(hours=1),model_version='v1')
    for p in (float('nan'),-1,2,True):
        with pytest.raises(ValueError):
            j.record(probability=p,**params)
    j.record(probability=1,**params)
    with pytest.raises(ValueError):
        j.resolve('f',outcome=True,observed_at=T,source_id='source')
    with pytest.raises(ValueError):
        j.record(probability=.5,**(params|{'forecast_id':'g','available_at':T+timedelta(minutes=1)}))
