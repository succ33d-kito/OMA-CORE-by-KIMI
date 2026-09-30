from datetime import timedelta
from core.scientific.probability_calibration import ForecastJournal
from core.scientific.price_forecast import issue_reference, resolve_from_market_state, TARGET, MODEL
from core.market_mechanics import build_market_state
from tests.test_regime_calibration import T


def market(end, price=100):
    bars = [dict(time=end-timedelta(hours=81-i), open=price, high=price+1, low=price-1,
                 close=price, volume=10) for i in range(81)]
    return build_market_state('BTC', bars, source_id='fixture', observed_at=end, as_of=end)


def test_prospective_reference_resolves_once_across_restart(tmp_path):
    path = str(tmp_path/'forecast.db')
    journal = ForecastJournal(path)
    initial = market(T)
    key = issue_reference(journal, initial, 'event1')
    assert issue_reference(journal, initial, 'event2') == key
    assert len(journal.forecasts()) == 1
    assert resolve_from_market_state(journal, market(T+timedelta(hours=23), 110)) == 0
    journal = ForecastJournal(path)
    assert resolve_from_market_state(journal, market(T+timedelta(hours=24), 110)) == 1
    assert resolve_from_market_state(journal, market(T+timedelta(hours=25), 90)) == 0
    report = journal.evaluate(target=TARGET, model_version=MODEL, regime_label='range:unknown')
    assert report['count'] == 1 and report['brier'] == .25


def test_no_substitution_when_exact_horizon_bar_is_missing(tmp_path):
    journal = ForecastJournal(str(tmp_path/'forecast.db'))
    issue_reference(journal, market(T), 'event')
    assert resolve_from_market_state(journal, market(T+timedelta(hours=150), 110)) == 0
    assert len(journal.forecasts(pending_only=True)) == 1


def test_flat_close_is_not_a_positive_outcome(tmp_path):
    journal = ForecastJournal(str(tmp_path/'forecast.db'))
    issue_reference(journal, market(T), 'event')
    resolve_from_market_state(journal, market(T+timedelta(hours=24)))
    result = journal.evaluate(target=TARGET,model_version=MODEL)
    assert result['reliability'][5]['observed_frequency'] == 0
