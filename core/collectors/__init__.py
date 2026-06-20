"""O.M.A.-C.O.R.E. Collectors Module"""
from core.collectors.base_collector import BaseCollector
from core.collectors.world_monitor import WorldMonitor
from core.collectors.coingecko_collector import CoinGeckoCollector
from core.collectors.yahoo_finance_collector import YahooFinanceCollector
from core.collectors.fred_collector import FREDCollector
from core.collectors.polymarket_collector import PolymarketCollector
from core.collectors.rss_collector import RSSCollector
from core.collectors.sentiment_collector import SentimentCollector

__all__ = [
    "BaseCollector",
    "WorldMonitor",
    "CoinGeckoCollector",
    "YahooFinanceCollector",
    "FREDCollector",
    "PolymarketCollector",
    "RSSCollector",
    "SentimentCollector",
]
