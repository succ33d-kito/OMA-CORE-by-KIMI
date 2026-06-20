"""O.M.A.-C.O.R.E. Score & Opportunity Engine v2.0"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
import math
from core.schemas.event_schema import Event, EventType, Sentiment, Urgency, AssetClass
from core.database.db import OMACoreDatabase
from core.engines.data_quality_engine import DataQualityEngine
from core.engines.telegram_notifier import TelegramNotifier


class ScoreEngine:
    """Motor de puntuacion de eventos para OMA-CORE v2.0"""
    
    BASE_WEIGHTS = {
        "urgency": 0.25,
        "sentiment_magnitude": 0.20,
        "source_confidence": 0.20,
        "asset_relevance": 0.15,
        "recency": 0.10,
        "correlation_boost": 0.10,
    }
    
    DYNAMIC_WEIGHTS = {
        EventType.MACRO_EVENT: {
            "source_confidence": 0.30, "urgency": 0.20,
            "sentiment_magnitude": 0.15, "asset_relevance": 0.15,
            "recency": 0.10, "correlation_boost": 0.10,
        },
        EventType.GEOPOLITICAL: {
            "source_confidence": 0.25, "correlation_boost": 0.20,
            "urgency": 0.20, "sentiment_magnitude": 0.15,
            "asset_relevance": 0.10, "recency": 0.10,
        },
        EventType.REGULATORY: {
            "source_confidence": 0.30, "urgency": 0.25,
            "sentiment_magnitude": 0.15, "asset_relevance": 0.15,
            "recency": 0.10, "correlation_boost": 0.05,
        },
        EventType.PRICE_MOVEMENT: {
            "recency": 0.25, "sentiment_magnitude": 0.25,
            "source_confidence": 0.15, "asset_relevance": 0.15,
            "urgency": 0.10, "correlation_boost": 0.10,
        },
        EventType.VOLUME_SPIKE: {
            "recency": 0.20, "sentiment_magnitude": 0.20,
            "source_confidence": 0.15, "asset_relevance": 0.20,
            "urgency": 0.15, "correlation_boost": 0.10,
        },
        EventType.HACK_EXPLOIT: {
            "urgency": 0.35, "source_confidence": 0.25,
            "recency": 0.20, "sentiment_magnitude": 0.10,
            "asset_relevance": 0.05, "correlation_boost": 0.05,
        },
        EventType.EARNINGS: {
            "source_confidence": 0.25, "sentiment_magnitude": 0.25,
            "asset_relevance": 0.20, "urgency": 0.15,
            "recency": 0.10, "correlation_boost": 0.05,
        },
    }
    
    EVENT_MULTIPLIERS = {
        EventType.PRICE_MOVEMENT: 1.2,
        EventType.VOLUME_SPIKE: 1.1,
        EventType.HACK_EXPLOIT: 1.5,
        EventType.REGULATORY: 1.4,
        EventType.GEOPOLITICAL: 1.3,
        EventType.MACRO_EVENT: 1.3,
        EventType.EARNINGS: 1.2,
        EventType.MERGER_ACQUISITION: 1.1,
        EventType.SENTIMENT_SHIFT: 1.0,
        EventType.SOCIAL_TREND: 0.8,
        EventType.NEWS: 0.7,
        EventType.TECHNICAL_SIGNAL: 0.9,
        EventType.WHALE_MOVEMENT: 1.3,
    }
    
    SOURCE_CONFIDENCE = {
        "fred": 0.98,
        "coingecko": 0.95,
        "yahoo_finance": 0.95,
        "polymarket": 0.88,
        "rss_reuters_business": 0.90,
        "rss_bloomberg": 0.90,
        "rss_coindesk": 0.80,
        "rss_cointelegraph": 0.80,
        "rss_forexlive": 0.80,
        "rss_cnbc": 0.80,
        "rss_marketwatch": 0.80,
        "rss_investing": 0.75,
        "sentiment_fng_crypto": 0.85,
        "gdelt": 0.70,
        "osiris": 0.75,
    }
    
    SOURCE_TIER = {
        "fred": "official",
        "coingecko": "primary",
        "yahoo_finance": "primary",
        "polymarket": "primary",
        "rss_reuters_business": "aggregator",
        "rss_bloomberg": "aggregator",
        "rss_coindesk": "aggregator",
        "rss_cointelegraph": "aggregator",
        "rss_forexlive": "aggregator",
        "rss_cnbc": "aggregator",
        "rss_marketwatch": "aggregator",
        "sentiment_fng_crypto": "aggregator",
        "gdelt": "aggregator",
        "osiris": "social",
    }
    
    TIER_BONUS = {
        "official": 1.10,
        "primary": 1.05,
        "aggregator": 1.00,
        "social": 0.95,
    }
    
    HIGH_INTEREST_ASSETS = {
        "BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX",
        "LINK", "MATIC", "DOT", "UNI", "LTC", "BCH", "ATOM",
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META",
        "NFLX", "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER",
        "COIN", "PLTR", "ARKK", "QQQ", "SPY", "IWM", "DIA",
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD",
        "GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "ZW=F", "ZC=F",
        "^GSPC", "^IXIC", "^DJI", "^VIX", "^RUT",
    }

    def __init__(self, db):
        self.db = db
        self.quality_engine = DataQualityEngine(db)

    def score_event(self, event):
        weights = self.DYNAMIC_WEIGHTS.get(event.event_type, self.BASE_WEIGHTS)
        scores = {}
        
        urgency_scores = {
            Urgency.CRITICAL: 100, Urgency.HIGH: 80,
            Urgency.MEDIUM: 50, Urgency.LOW: 25, Urgency.BACKGROUND: 10,
        }
        scores["urgency"] = urgency_scores.get(event.urgency, 25)
        scores["sentiment_magnitude"] = min(abs(event.sentiment_score) * 100, 100)
        
        source_conf = self.SOURCE_CONFIDENCE.get(event.source, 0.5)
        tier = self.SOURCE_TIER.get(event.source, "aggregator")
        tier_bonus = self.TIER_BONUS.get(tier, 1.0)
        
        validation_score = 1.0
        if "validation" in event.metadata:
            validation_score = event.metadata["validation"].get("score", 1.0)
        
        final_source_conf = source_conf * tier_bonus * validation_score
        scores["source_confidence"] = final_source_conf * 100
        scores["asset_relevance"] = self._calculate_asset_relevance(event)
        scores["recency"] = self._calculate_recency_exponential(event)
        scores["correlation_boost"] = self._calculate_correlation_boost(event)
        
        raw_score = sum(scores[key] * weights[key] for key in weights.keys())
        multiplier = self.EVENT_MULTIPLIERS.get(event.event_type, 1.0)
        final_score = min(raw_score * multiplier, 100.0)
        
        metadata = {
            "weights_used": weights,
            "multiplier": multiplier,
            "source_tier": tier,
            "tier_bonus": tier_bonus,
            "validation_score": validation_score,
        }
        
        return {
            "raw_score": round(raw_score, 2),
            "final_score": round(final_score, 2),
            "multiplier": multiplier,
            "component_scores": scores,
            "event_id": event.id,
            "metadata": metadata,
        }

    def score_batch(self, events):
        return [self.score_event(e) for e in events]

    def _calculate_asset_relevance(self, event):
        if not event.assets:
            return 50.0
        relevance_scores = []
        for asset in event.assets:
            if asset.symbol in self.HIGH_INTEREST_ASSETS:
                relevance_scores.append(100)
            elif asset.asset_class in [AssetClass.CRYPTO, AssetClass.STOCK]:
                relevance_scores.append(70)
            elif asset.asset_class in [AssetClass.FOREX, AssetClass.COMMODITY]:
                relevance_scores.append(60)
            elif asset.asset_class == AssetClass.INDEX:
                relevance_scores.append(75)
            elif asset.asset_class == AssetClass.BOND:
                relevance_scores.append(55)
            else:
                relevance_scores.append(40)
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        if len(event.assets) >= 3:
            avg_relevance *= 1.1
        return min(avg_relevance, 100)

    def _calculate_recency_exponential(self, event):
        age_seconds = (datetime.now(timezone.utc) - event.timestamp).total_seconds()
        age_hours = age_seconds / 3600
        if event.assets and event.assets[0].asset_class == AssetClass.CRYPTO:
            half_life = 2.0
        elif event.event_type in [EventType.MACRO_EVENT, EventType.GEOPOLITICAL]:
            half_life = 8.0
        else:
            half_life = 4.0
        score = 100 * math.pow(0.5, age_hours / half_life)
        return max(score, 5.0)

    def _calculate_correlation_boost(self, event):
        try:
            recent = self.db.get_recent_events(hours=6, limit=100)
            similar = [e for e in recent if e.event_type == event.event_type and e.id != event.id]
            if len(similar) >= 10:
                return 100
            elif len(similar) >= 5:
                return 85
            elif len(similar) >= 3:
                return 70
            elif len(similar) >= 1:
                return 50
            else:
                return 25
        except:
            return 25

    def get_source_stats(self):
        return {
            source: {
                "confidence": conf,
                "tier": self.SOURCE_TIER.get(source, "unknown"),
                "tier_bonus": self.TIER_BONUS.get(self.SOURCE_TIER.get(source, "aggregator"), 1.0),
            }
            for source, conf in self.SOURCE_CONFIDENCE.items()
        }


class OpportunityEngine:
    """Motor de generacion de oportunidades de trading v2.0"""
    
    OPPORTUNITY_TYPES = {
        EventType.PRICE_MOVEMENT: {
            "bullish": "LONG_SETUP", "bearish": "SHORT_SETUP", "neutral": "WATCHLIST_ADD"
        },
        EventType.VOLUME_SPIKE: {"default": "MOMENTUM_PLAY"},
        EventType.HACK_EXPLOIT: {"default": "AVOID_OR_SHORT"},
        EventType.REGULATORY: {
            "bullish": "REGULATORY_TAILWIND", "bearish": "REGULATORY_HEADWIND", "neutral": "MONITOR_COMPLIANCE"
        },
        EventType.GEOPOLITICAL: {
            "bullish": "SAFE_HAVEN_FLOW", "bearish": "RISK_OFF", "neutral": "MONITOR_GEO"
        },
        EventType.MACRO_EVENT: {
            "bullish": "MACRO_TAILWIND", "bearish": "MACRO_HEADWIND", "neutral": "MONITOR_MACRO"
        },
        EventType.EARNINGS: {
            "bullish": "POST_EARNINGS_RUN", "bearish": "POST_EARNINGS_DROP", "neutral": "EARNINGS_NEUTRAL"
        },
        EventType.SENTIMENT_SHIFT: {
            "bullish": "SENTIMENT_TURN_BULL", "bearish": "SENTIMENT_TURN_BEAR", "neutral": "SENTIMENT_WATCH"
        },
        EventType.SOCIAL_TREND: {"default": "VIRAL_MOMENTUM"},
        EventType.NEWS: {"default": "NEWS_DRIVEN"},
        EventType.TECHNICAL_SIGNAL: {
            "bullish": "TECHNICAL_BREAKOUT", "bearish": "TECHNICAL_BREAKDOWN", "neutral": "TECHNICAL_WATCH"
        },
        EventType.WHALE_MOVEMENT: {
            "bullish": "WHALE_ACCUMULATION", "bearish": "WHALE_DISTRIBUTION", "neutral": "WHALE_WATCH"
        },
        EventType.MERGER_ACQUISITION: {"default": "ARB_OPPORTUNITY"},
    }
    
    ACTION_TEMPLATES = {
        "LONG_SETUP": {
            "action": "Considerar posicion larga",
            "timeframe": "Swing (1-5 dias)",
            "risk": "Stop-loss bajo soporte reciente",
            "rationale": "Momentum alcista con catalizador fundamental",
            "position_size": "Moderada (2-3% del portfolio)",
        },
        "SHORT_SETUP": {
            "action": "Considerar posicion corta",
            "timeframe": "Swing (1-5 dias)",
            "risk": "Stop-loss sobre resistencia reciente",
            "rationale": "Momentum bajista con catalizador negativo",
            "position_size": "Pequena (1-2% del portfolio)",
        },
        "MOMENTUM_PLAY": {
            "action": "Entrada en momentum",
            "timeframe": "Day trade / Scalp (horas)",
            "risk": "Tight stop, objetivo parcial rapido",
            "rationale": "Volumen anomalo indica interes institucional",
            "position_size": "Pequena (1-2% del portfolio)",
        },
        "AVOID_OR_SHORT": {
            "action": "Evitar o posicion corta",
            "timeframe": "Inmediato",
            "risk": "Alto -- eventos de seguridad son impredecibles",
            "rationale": "Evento de seguridad compromete valor fundamental",
            "position_size": "Muy pequena o evitar",
        },
        "SAFE_HAVEN_FLOW": {
            "action": "Rotacion a activos refugio",
            "timeframe": "1-2 semanas",
            "risk": "Reversion rapida si tensiones se calman",
            "rationale": "Tension geopolitica impulsa demanda de seguridad",
            "position_size": "Moderada (2-3% del portfolio)",
        },
        "RISK_OFF": {
            "action": "Reducir exposicion o hedging",
            "timeframe": "Inmediato",
            "risk": "Falso positivo si crisis no materializa",
            "rationale": "Evento geopolitico aumenta aversion al riesgo",
            "position_size": "Reducir 20-30% exposicion",
        },
        "WHALE_ACCUMULATION": {
            "action": "Seguimiento de ballenas",
            "timeframe": "Posicion acumulativa (1-4 semanas)",
            "risk": "Ballena puede distribuir despues",
            "rationale": "Grandes tenedores estan comprando",
            "position_size": "Moderada (2-3% del portfolio)",
        },
        "WHALE_DISTRIBUTION": {
            "action": "Precaucion -- presion vendedora",
            "timeframe": "Corto plazo (1-3 dias)",
            "risk": "Puede ser reubicacion, no venta total",
            "rationale": "Grandes tenedores estan vendiendo",
            "position_size": "Reducir o salir",
        },
        "VIRAL_MOMENTUM": {
            "action": "Ride the wave (con cuidado)",
            "timeframe": "Muy corto (horas-dias)",
            "risk": "Alta volatilidad, pump-and-dump",
            "rationale": "Tendencia social impulsa demanda especulativa",
            "position_size": "Muy pequena (0.5-1% del portfolio)",
        },
        "POST_EARNINGS_RUN": {
            "action": "Seguimiento post-earnings",
            "timeframe": "1-3 dias",
            "risk": "Profit-taking puede revertir movimiento",
            "rationale": "Resultados positivos no estan completamente precificados",
            "position_size": "Moderada (2-3% del portfolio)",
        },
        "MACRO_TAILWIND": {
            "action": "Alineacion con tendencia macro",
            "timeframe": "1-4 semanas",
            "risk": "Datos posteriores pueden contradecir",
            "rationale": "Datos macro favorables para el activo/sector",
            "position_size": "Moderada (2-4% del portfolio)",
        },
        "MACRO_HEADWIND": {
            "action": "Reducir exposicion al sector",
            "timeframe": "1-2 semanas",
            "risk": "Datos posteriores pueden contradecir",
            "rationale": "Datos macro desfavorables para el activo/sector",
            "position_size": "Reducir 20-30%",
        },
        "REGULATORY_TAILWIND": {
            "action": "Aprovechar claridad regulatoria",
            "timeframe": "1-3 semanas",
            "risk": "Regulacion puede cambiar",
            "rationale": "Regulacion favorable reduce incertidumbre",
            "position_size": "Moderada (2-3% del portfolio)",
        },
        "REGULATORY_HEADWIND": {
            "action": "Reducir exposicion o salir",
            "timeframe": "Inmediato a 1 semana",
            "risk": "Sanciones o prohibiciones",
            "rationale": "Regulacion adversa afecta operaciones",
            "position_size": "Reducir o salir",
        },
        "SENTIMENT_TURN_BULL": {
            "action": "Aprovechar cambio de sentimiento",
            "timeframe": "1-2 semanas",
            "risk": "Puede ser falso breakout",
            "rationale": "Sentimiento del mercado giro a positivo",
            "position_size": "Moderada (2-3% del portfolio)",
        },
        "SENTIMENT_TURN_BEAR": {
            "action": "Reducir exposicion o hedging",
            "timeframe": "1-2 semanas",
            "risk": "Puede ser falso breakdown",
            "rationale": "Sentimiento del mercado giro a negativo",
            "position_size": "Reducir 20-30%",
        },
        "ARB_OPPORTUNITY": {
            "action": "Arbitraje de fusion",
            "timeframe": "Hasta cierre del deal",
            "risk": "Deal puede fracasar",
            "rationale": "Diferencial de precio entre oferta y mercado",
            "position_size": "Pequena (1-2% del portfolio)",
        },
        "WATCHLIST_ADD": {
            "action": "Agregar a watchlist",
            "timeframe": "Monitoreo",
            "risk": "Ninguna -- solo observacion",
            "rationale": "Activo muestra actividad relevante",
            "position_size": "Ninguna",
        },
        "NEWS_DRIVEN": {
            "action": "Evaluar impacto de la noticia",
            "timeframe": "1-3 dias",
            "risk": "Noticia puede ser desmentida",
            "rationale": "Catalizador de noticias afecta al activo",
            "position_size": "Pequena (1-2% del portfolio)",
        },
    }

    def __init__(self, db, score_engine):
        self.db = db
        self.score_engine = score_engine

    def generate_opportunities(self, events, min_score=40.0):
        opportunities = []
        scored_events = self.score_engine.score_batch(events)
        for score_data in scored_events:
            if score_data["final_score"] < min_score:
                continue
            event = next((e for e in events if e.id == score_data["event_id"]), None)
            if not event:
                continue
            opportunity = self._create_opportunity(event, score_data)
            if opportunity:
                opportunities.append(opportunity)
                self.db.insert_opportunity(opportunity)
                self.db.update_event_scores(event.id, score_data["final_score"], opportunity.get("relevance", 0))
                self.db.mark_processed(event.id)
        opportunities.sort(key=lambda x: x["score"], reverse=True)
        return opportunities

    def _create_opportunity(self, event, score_data):
        if event.sentiment_score > 0.3:
            direction = "bullish"
        elif event.sentiment_score < -0.3:
            direction = "bearish"
        else:
            direction = "neutral"
        type_map = self.OPPORTUNITY_TYPES.get(event.event_type, {"default": "NEWS_DRIVEN"})
        opp_type = type_map.get(direction, type_map.get("default", "NEWS_DRIVEN"))
        action_template = self.ACTION_TEMPLATES.get(opp_type, self.ACTION_TEMPLATES["WATCHLIST_ADD"])
        conviction = self._calculate_conviction(event, score_data)
        priority = self._determine_priority(score_data["final_score"], conviction)
        risk_level = self._calculate_risk(event, opp_type)
        timeframe = self._adjust_timeframe(event, action_template["timeframe"])
        metadata = {
            "score_metadata": score_data.get("metadata", {}),
            "validation": event.metadata.get("validation", {}),
            "source_tier": score_data.get("metadata", {}).get("source_tier", "unknown"),
        }
        return {
            "id": f"opp_{event.id[:8]}",
            "event_id": event.id,
            "title": f"[{opp_type}] {event.title[:80]}",
            "description": self._build_description(event, action_template),
            "opportunity_type": opp_type,
            "asset_class": event.assets[0].asset_class.value if event.assets else "unknown",
            "assets": [a.symbol for a in event.assets],
            "score": score_data["final_score"],
            "conviction": conviction,
            "priority": priority,
            "action_suggested": action_template["action"],
            "action_details": {**action_template, "timeframe": timeframe},
            "risk_level": risk_level,
            "position_size": action_template.get("position_size", "Evaluar"),
            "event_type": event.event_type.value,
            "sentiment": event.sentiment.name,
            "source": event.source,
            "source_confidence": self.score_engine.SOURCE_CONFIDENCE.get(event.source, 0.5),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "metadata": metadata,
        }

    def _calculate_conviction(self, event, score_data):
        base = score_data["final_score"] * 0.5
        source_boost = score_data["component_scores"]["source_confidence"] * 0.2
        asset_boost = min(len(event.assets) * 5, 15)
        neutral_penalty = 10 if event.sentiment == Sentiment.NEUTRAL else 0
        validation_bonus = 0
        if "validation" in event.metadata:
            val_score = event.metadata["validation"].get("score", 0)
            validation_bonus = val_score * 10
        conviction = base + source_boost + asset_boost - neutral_penalty + validation_bonus
        return round(min(max(conviction, 0), 100), 2)

    def _determine_priority(self, score, conviction):
        combined = (score * 0.6 + conviction * 0.4)
        if combined >= 80:
            return "CRITICAL"
        elif combined >= 65:
            return "HIGH"
        elif combined >= 45:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_risk(self, event, opp_type):
        if event.event_type == EventType.HACK_EXPLOIT:
            return "VERY_HIGH"
        if event.event_type == EventType.GEOPOLITICAL:
            return "HIGH"
        if opp_type in ["VIRAL_MOMENTUM", "AVOID_OR_SHORT"]:
            return "HIGH"
        if event.event_type == EventType.PRICE_MOVEMENT:
            if abs(event.sentiment_score) > 0.8:
                return "HIGH"
            elif abs(event.sentiment_score) > 0.5:
                return "MEDIUM"
        if event.source in ["rss_coindesk", "rss_cointelegraph", "sentiment_fng_crypto"]:
            return "MEDIUM"
        return "MEDIUM"

    def _adjust_timeframe(self, event, base_timeframe):
        if not event.assets:
            return base_timeframe
        asset_class = event.assets[0].asset_class
        if asset_class == AssetClass.CRYPTO:
            if "semana" in base_timeframe:
                return base_timeframe.replace("semanas", "dias").replace("1-4", "1-3")
        elif asset_class in [AssetClass.BOND, AssetClass.INDEX]:
            if "dias" in base_timeframe:
                return base_timeframe.replace("dias", "semanas")
        return base_timeframe

    def _build_description(self, event, action_template):
        parts = [
            f"Evento: {event.event_type.value}",
            event.title,
            f"Accion: {action_template['action']}",
            f"Timeframe: {action_template['timeframe']}",
            f"Rationale: {action_template['rationale']}",
            f"Riesgo: {action_template['risk']}",
            f"Tamano sugerido: {action_template.get('position_size', 'Evaluar')}",
        ]
        if event.assets:
            assets_info = ", ".join([f"{a.symbol} (${a.price_at_event:,.2f})" if a.price_at_event else a.symbol for a in event.assets])
            parts.insert(1, f"Activos: {assets_info}")
        if event.summary:
            parts.insert(2, f"Contexto: {event.summary[:200]}...")
        if "validation" in event.metadata:
            val_score = event.metadata["validation"].get("score", 0)
            parts.append(f"Validacion: {val_score:.0%} confiable")
        return "\\n".join(parts)


class Pipeline:
    """Pipeline completo: collect -> validate -> score -> opportunities -> notify."""
    
    def __init__(self, db_path="oma_core.db", enable_quality=True, fred_api_key=None, enable_telegram=True):
        self.db = OMACoreDatabase(db_path)
        self.score_engine = ScoreEngine(self.db)
        self.opportunity_engine = OpportunityEngine(self.db, self.score_engine)
        self.quality_engine = DataQualityEngine(self.db) if enable_quality else None
        self.telegram = TelegramNotifier() if enable_telegram else None
        self.telegram_enabled = enable_telegram and self.telegram.enabled if self.telegram else False
        
        if self.telegram_enabled:
            print("[Pipeline] 🔔 Notificaciones de Telegram activadas")
            self.telegram.test_connection()
        else:
            print("[Pipeline] 🔔 Notificaciones de Telegram desactivadas")

    def run(self, events, min_score=40.0, cycle_number=0):
        print(f"[Pipeline] Procesando {len(events)} eventos...")
        if self.quality_engine:
            print(f"[Pipeline] Validando calidad de datos...")
            events, rejected = self.quality_engine.validate_batch(events)
            print(f"[Pipeline] {len(events)} validos, {len(rejected)} rechazados")
        stored = 0
        for event in events:
            try:
                self.db.insert_event(event)
                stored += 1
            except Exception as e:
                print(f"[Pipeline] Error almacenando evento: {e}")
        print(f"[Pipeline] {stored}/{len(events)} eventos almacenados")
        opportunities = self.opportunity_engine.generate_opportunities(events, min_score)
        print(f"[Pipeline] {len(opportunities)} oportunidades generadas")
        
        # Enviar resumen de CRITICAL a Telegram (con cooldown de 4 horas)
        if self.telegram_enabled and opportunities:
            critical_opps = [o for o in opportunities if o.get("priority") == "CRITICAL"]
            if critical_opps:
                print(f"[Pipeline] 🚨 {len(critical_opps)} oportunidades CRITICAL detectadas")
                cycle_info = {"cycle": cycle_number}
                self.telegram.send_critical_summary(critical_opps, cycle_info)
            else:
                print("[Pipeline] 🟢 Sin oportunidades CRITICAL")
        
        stats = self.db.get_event_stats()
        return {
            "events_processed": len(events),
            "events_stored": stored,
            "opportunities_generated": len(opportunities),
            "database_stats": stats,
            "top_opportunities": opportunities[:10],
            "source_stats": self.score_engine.get_source_stats(),
            "telegram_enabled": self.telegram_enabled,
            "critical_count": len([o for o in opportunities if o.get("priority") == "CRITICAL"]),
        }
