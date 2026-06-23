"""OSIRIS World Monitor v2 — Unified collector orchestrator"""
from typing import List, Optional
from datetime import datetime, timezone

from core.collectors.base_collector import BaseCollector
from core.collectors.coingecko_collector import CoinGeckoCollector
from core.collectors.yahoo_finance_collector import YahooFinanceCollector
from core.collectors.binance_collector import BinanceCollector
from core.collectors.fred_collector import FREDCollector
from core.collectors.rss_collector import RSSCollector
from core.collectors.sentiment_collector import SentimentCollector
from core.collectors.polymarket_collector import PolymarketCollector
from core.schemas.event_schema import Event
from core.event_bus import EventBus, EventTopic, bus as default_bus


class WorldMonitorV2:
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.bus = event_bus or default_bus
        self.collectors: List[BaseCollector] = [
            CoinGeckoCollector(),
            YahooFinanceCollector(),
            BinanceCollector(),
            FREDCollector(),
            RSSCollector(),
            SentimentCollector(),
            PolymarketCollector(),
        ]
        self.stats = {
            "total_runs": 0,
            "total_events_collected": 0,
            "last_run": None,
            "collector_stats": {},
        }

    def collect_all(self) -> List[Event]:
        all_events = []
        self.stats["total_runs"] += 1
        self.stats["last_run"] = datetime.now(timezone.utc).isoformat()

        for collector in self.collectors:
            try:
                events = collector.collect()
                if events:
                    all_events.extend(events)
                    if self.bus:
                        for event in events:
                            self.bus.publish(
                                EventTopic.EVENTS_RAW,
                                event.to_dict(),
                                source=collector.name,
                            )
                self.stats["collector_stats"][collector.name] = {
                    "events": len(events) if events else 0,
                    "success": True,
                }
            except Exception as e:
                print(f"[WorldMonitorV2] Error in {collector.name}: {e}")
                self.stats["collector_stats"][collector.name] = {
                    "events": 0,
                    "success": False,
                    "error": str(e),
                }

        self.stats["total_events_collected"] += len(all_events)
        print(f"[WorldMonitorV2] Collected {len(all_events)} events from {len(self.collectors)} collectors")
        return all_events

    def collect_by_source(self, source_name: str) -> List[Event]:
        for collector in self.collectors:
            if collector.name == source_name:
                events = collector.collect() or []
                if events and self.bus:
                    for event in events:
                        self.bus.publish(
                            EventTopic.EVENTS_RAW,
                            event.to_dict(),
                            source=collector.name,
                        )
                return events
        return []

    def get_stats(self) -> dict:
        return self.stats
