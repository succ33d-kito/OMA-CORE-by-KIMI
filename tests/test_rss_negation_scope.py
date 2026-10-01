import pytest
from core.collectors.rss_collector import RSSCollector
from core.schemas.event_schema import EventType, Sentiment


@pytest.mark.parametrize('title,summary,kind,sentiment', [
    ('Bitcoin wallet was not hacked; no funds were stolen','',EventType.NEWS,Sentiment.NEUTRAL),
    ("Ethereum wallet wasn't hacked",'',EventType.NEWS,Sentiment.NEUTRAL),
    ('Hospital confirms no ransomware incident occurred','',EventType.NEWS,Sentiment.NEUTRAL),
    ('Bitcoin did not surge; price unchanged','',EventType.NEWS,Sentiment.NEUTRAL),
    ('Ethereum did not crash; price unchanged','',EventType.NEWS,Sentiment.NEUTRAL),
    ('Bitcoin is not bullish: outlook remains bearish','',EventType.NEWS,Sentiment.BEARISH),
    ('Bitcoin did not surge, but Ethereum rally continues','',EventType.NEWS,Sentiment.BULLISH),
    ('Bitcoin wallet not only hacked but also emptied','',EventType.HACK_EXPLOIT,Sentiment.NEUTRAL),
    ('Bitcoin wallet: hacked','',EventType.HACK_EXPLOIT,Sentiment.NEUTRAL),
    ('Pilot injured in attack; Bitcoin wallet updated','',EventType.NEWS,Sentiment.NEUTRAL),
    ('Pilot injured in attack','Bitcoin wallet updated',EventType.NEWS,Sentiment.NEUTRAL),
    ('President gives strong speech; Bitcoin price unchanged','',EventType.GEOPOLITICAL,Sentiment.NEUTRAL),
    ('Bitcoin shows strong momentum','',EventType.NEWS,Sentiment.BULLISH),
    ('SEC did not approve Bitcoin ETF; application pending','',EventType.REGULATORY,Sentiment.NEUTRAL),
])
def test_negation_and_local_context(title,summary,kind,sentiment):
    actual = RSSCollector()._classify_news(title,summary,[])
    assert (actual[0],actual[1]) == (kind,sentiment)
