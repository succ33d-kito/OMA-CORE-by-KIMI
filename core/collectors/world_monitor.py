"""O.M.A.-C.O.R.E. World Monitor"""
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from core.collectors.base_collector import BaseCollector
from core.collectors.coingecko_collector import CoinGeckoCollector
from core.collectors.yahoo_finance_collector import YahooFinanceCollector
from core.collectors.fred_collector import FREDCollector
from core.collectors.polymarket_collector import PolymarketCollector
from core.collectors.rss_collector import RSSCollector
from core.collectors.sentiment_collector import SentimentCollector
from core.collectors.binance_collector import BinanceCollector
from core.engines.data_quality_engine import DataQualityEngine

class WorldMonitor:
    """
    Orquestador central de collectors para OMA-CORE.
    Integra múltiples fuentes de datos y aplica validación de calidad.
    """
    
    def __init__(self, enable_quality_check: bool = True, fred_api_key: Optional[str] = None):
        self.collectors: List[BaseCollector] = [
            CoinGeckoCollector(),
            BinanceCollector(),  # NUEVO: Validación cruzada crypto
            YahooFinanceCollector(),
            FREDCollector(api_key=fred_api_key),
            PolymarketCollector(),
            RSSCollector(),
            SentimentCollector(),
        ]
        self.quality_engine = DataQualityEngine() if enable_quality_check else None
        self.enable_quality_check = enable_quality_check
        self.stats = {
            "total_events_collected": 0,
            "total_events_validated": 0,
            "total_events_rejected": 0,
            "last_run": None,
            "collector_stats": {},
        }

    def collect_all(self) -> List:
        all_events = []
        collector_stats = {}
        for collector in self.collectors:
            try:
                print(f"[WorldMonitor] Ejecutando {collector.name}...")
                events = collector.collect()
                print(f"[WorldMonitor] {collector.name}: {len(events)} eventos recolectados")
                all_events.extend(events)
                collector_stats[collector.name] = {
                    "events": len(events),
                    "stats": collector.get_stats(),
                }
            except Exception as e:
                print(f"[WorldMonitor] Error en {collector.name}: {e}")
                collector_stats[collector.name] = {"events": 0, "error": str(e)}
                continue
        self.stats["total_events_collected"] += len(all_events)
        self.stats["last_run"] = datetime.now(timezone.utc).isoformat()
        if self.enable_quality_check and self.quality_engine:
            print(f"[WorldMonitor] Validando {len(all_events)} eventos...")
            valid_events, rejected = self.quality_engine.validate_batch(all_events)
            print(f"[WorldMonitor] {len(valid_events)} válidos, {len(rejected)} rechazados")
            self.stats["total_events_validated"] += len(valid_events)
            self.stats["total_events_rejected"] += len(rejected)
            self.stats["rejected_details"] = rejected[:10]
            all_events = valid_events
        self.stats["collector_stats"] = collector_stats
        return all_events

    def collect_by_source(self, source_name: str) -> List:
        for collector in self.collectors:
            if collector.name == source_name:
                try:
                    events = collector.collect()
                    if self.enable_quality_check and self.quality_engine:
                        valid_events, _ = self.quality_engine.validate_batch(events)
                        return valid_events
                    return events
                except Exception as e:
                    print(f"[WorldMonitor] Error en {source_name}: {e}")
                    return []
        print(f"[WorldMonitor] Collector '{source_name}' no encontrado")
        return []

    def get_available_sources(self) -> List[Dict]:
        return [
            {"name": c.name, "confidence": c.source_confidence, "stats": c.get_stats()}
            for c in self.collectors
        ]

    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "sources_active": len(self.collectors),
            "quality_check_enabled": self.enable_quality_check,
        }

    def add_collector(self, collector: BaseCollector):
        self.collectors.append(collector)
        print(f"[WorldMonitor] Collector '{collector.name}' añadido")

    def remove_collector(self, source_name: str):
        self.collectors = [c for c in self.collectors if c.name != source_name]
        print(f"[WorldMonitor] Collector '{source_name}' eliminado")
