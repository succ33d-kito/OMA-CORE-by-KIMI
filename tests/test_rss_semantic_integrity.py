"""Lexical regressions from operational headlines; no outcomes or trading tests."""
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from core.collectors.rss_collector import RSSCollector
from core.schemas.event_schema import EventType, Sentiment, Urgency
from core.engines.score_opportunity import Pipeline
from core.collectors.yahoo_finance_collector import YahooFinanceCollector


@pytest.fixture
def collector():
    return RSSCollector(sources=['rss_bloomberg'])


@pytest.mark.parametrize('title,expected', [
    ("FlyDubai Pilot Attack, Trump Calls For Powell's Resignation", EventType.NEWS),
    ('President touts a $54 billion pipeline', EventType.GEOPOLITICAL),
    ('Standard Chartered sees Ethena reaching $40B', EventType.NEWS),
    ('Bank of Japan calendar for Thursday', EventType.NEWS),
    ('President announces national security strategy', EventType.GEOPOLITICAL),
    ('Bitcoin wallet hacked: funds stolen', EventType.HACK_EXPLOIT),
    ('DeFi protocol exploited through smart contract vulnerability', EventType.HACK_EXPLOIT),
    ('Hospital hit by ransomware', EventType.HACK_EXPLOIT),
    ('SEC approves Bitcoin ETF', EventType.REGULATORY),
    ('New regulatory compliance rules', EventType.REGULATORY),
    ('Fed interest rate decision', EventType.MACRO_EVENT),
    ('Company announces earnings', EventType.EARNINGS),
])
def test_types(collector, title, expected):
    kind, _, _, urgency = collector._classify_news(title, '', [])
    assert kind == expected
    assert (urgency == Urgency.CRITICAL) == (expected == EventType.HACK_EXPLOIT)


def test_markup_and_substrings_are_not_evidence(collector):
    text = 'Together, Canada reviews its Golden Week calendar and metadata.'
    markup = '<img src="https://host/ETH/ban/attack" alt="hack"><script>BTC surge</script>'
    assert collector._extract_assets(text+markup) == []
    assert collector._extract_keywords(text+markup) == []
    kind, sentiment, score, urgency = collector._classify_news(text, markup, [])
    assert (kind, sentiment, score, urgency) == (EventType.NEWS, Sentiment.NEUTRAL, 0, Urgency.LOW)


def test_aliases_are_canonical_and_deduplicated(collector):
    assert [a.symbol for a in collector._extract_assets('Bitcoin BTC and Ethereum ETH')] == ['BTC', 'ETH']
    assert [a.symbol for a in collector._extract_assets('$SOL, AAPL and oil')] == ['SOL', 'AAPL', 'OIL']


def test_sentiment_token_boundaries(collector):
    assert collector._classify_news('Commission reviews fallout at stronghold', '', [])[1] == Sentiment.NEUTRAL
    assert collector._classify_news('Bitcoin surge to record high', '', [])[1] == Sentiment.BULLISH
    assert collector._classify_news('Bitcoin plunge to record low', '', [])[1] == Sentiment.BEARISH


def test_controlled_feed_to_database_to_opportunities(collector, tmp_path):
    # Synthetic local feed reproduces the observed error mechanism, without network.
    titles = ['Ethena surge: bank expects record high',
              'President touts strong $54 billion pipeline',
              'SEC approves Bitcoin ETF amid rally']
    collector.feedparser = SimpleNamespace(parse=lambda _:SimpleNamespace(
        entries=[dict(title=t, summary='', link='https://example.test/news') for t in titles],
        feed={'title':'controlled semantic regression'}))
    events = collector.collect()
    assert len(events) == 3
    assert all(e.metadata['classification_rule_version'] == 'rss-clause-negation-v1.1' for e in events)
    pipeline = Pipeline(tmp_path/'controlled.db')
    result = pipeline.run(events, min_score=0)
    assert result['events_stored'] == 3
    opportunities = {o['event_id']:o for o in result['top_opportunities']}
    assert opportunities[events[0].id]['opportunity_type'] != 'REGULATORY_TAILWIND'
    # 'strong' describes political prose, not a directional financial signal.
    assert events[1].sentiment == Sentiment.NEUTRAL
    assert events[1].id not in opportunities
    assert opportunities[events[2].id]['opportunity_type'] == 'REGULATORY_TAILWIND'
    assert pipeline.db.get_recent_events(hours=1, limit=10)


@pytest.mark.parametrize('error,expected', [
    (ModuleNotFoundError("No module named 'yfinance'", name='yfinance'), 'no instalado'),
    (ImportError('DLL load failed: application control'), 'Fallo al importar'),
    (ModuleNotFoundError("No module named 'pandas'", name='pandas'), 'Fallo al importar'),
])
def test_yahoo_import_diagnostic(error, expected, capsys):
    with patch('builtins.__import__', side_effect=error):
        assert YahooFinanceCollector()._get_yf() is None
    assert expected in capsys.readouterr().out
