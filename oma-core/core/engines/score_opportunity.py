"""
O.M.A.-C.O.R.E. — Score Engine & Opportunity Engine
======================================================
Motor de puntuación y generación de oportunidades.
V0.1: Reglas heurísticas (sin ML).
V1.0+: Integración con modelos locales (llama.cpp, etc.)

El Score Engine evalúa cada evento según:
- Impacto potencial en mercado
- Urgencia temporal
- Confianza en la fuente
- Relevancia para el perfil de usuario
- Correlación con otros eventos

El Opportunity Engine transforma eventos calificados en oportunidades accionables.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from core.schemas.event_schema import Event, EventType, Sentiment, Urgency, AssetClass
from core.database.db import OMACoreDatabase


class ScoreEngine:
    """
    Motor de puntuación para eventos.
    Asigna scores de 0.0 a 100.0 basados en múltiples factores.
    """

    # Pesos para el cálculo de impacto
    WEIGHTS = {
        "urgency": 0.25,
        "sentiment_magnitude": 0.20,
        "source_confidence": 0.20,
        "asset_relevance": 0.15,
        "recency": 0.10,
        "correlation_boost": 0.10
    }

    # Multiplicadores por tipo de evento
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
        EventType.WHALE_MOVEMENT: 1.3
    }

    # Confianza por fuente
    SOURCE_CONFIDENCE = {
        "coingecko": 0.95,
        "yahoo_finance": 0.95,
        "gdelt": 0.70,
        "rss_reuters_business": 0.85,
        "rss_coindesk": 0.80,
        "rss_cointelegraph": 0.80,
        "rss_forexlive": 0.80,
        "rss_investing": 0.75,
        "rss_marketwatch": 0.80,
        "rss_cnbc": 0.80,
        "rss_bloomberg": 0.90,
        "osiris": 0.75
    }

    def __init__(self, db: OMACoreDatabase):
        self.db = db

    def score_event(self, event: Event) -> Dict[str, Any]:
        """
        Calcula el score completo de un evento.
        Retorna diccionario con scores individuales y score final.
        """
        scores = {}

        # 1. Urgencia (0-100)
        urgency_scores = {
            Urgency.CRITICAL: 100,
            Urgency.HIGH: 80,
            Urgency.MEDIUM: 50,
            Urgency.LOW: 25,
            Urgency.BACKGROUND: 10
        }
        scores["urgency"] = urgency_scores.get(event.urgency, 25)

        # 2. Magnitud de sentimiento (0-100)
        sentiment_mag = abs(event.sentiment_score) * 100
        scores["sentiment_magnitude"] = min(sentiment_mag, 100)

        # 3. Confianza de fuente (0-100)
        source_conf = self.SOURCE_CONFIDENCE.get(event.source, 0.5)
        scores["source_confidence"] = source_conf * 100

        # 4. Relevancia de activo (0-100)
        scores["asset_relevance"] = self._calculate_asset_relevance(event)

        # 5. Recencia (0-100) — más reciente = más alto
        scores["recency"] = self._calculate_recency(event)

        # 6. Boost por correlación con otros eventos
        scores["correlation_boost"] = self._calculate_correlation_boost(event)

        # Calcular score bruto ponderado
        raw_score = sum(
            scores[key] * self.WEIGHTS[key] 
            for key in self.WEIGHTS.keys()
        )

        # Aplicar multiplicador por tipo de evento
        multiplier = self.EVENT_MULTIPLIERS.get(event.event_type, 1.0)
        final_score = min(raw_score * multiplier, 100.0)

        return {
            "raw_score": raw_score,
            "final_score": round(final_score, 2),
            "multiplier": multiplier,
            "component_scores": scores,
            "event_id": event.id
        }

    def _calculate_asset_relevance(self, event: Event) -> float:
        """Calcula relevancia basada en activos mencionados"""
        if not event.assets:
            return 50.0  # Neutral

        # Activos de alto interés para trading
        high_interest = {
            "BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX",
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META",
            "EURUSD", "GBPUSD", "USDJPY", "GC=F", "SI=F", "CL=F"
        }

        relevance_sum = 0
        for asset in event.assets:
            if asset.symbol in high_interest:
                relevance_sum += 100
            elif asset.asset_class in [AssetClass.CRYPTO, AssetClass.STOCK]:
                relevance_sum += 70
            else:
                relevance_sum += 50

        return min(relevance_sum / max(len(event.assets), 1), 100)

    def _calculate_recency(self, event: Event) -> float:
        """Calcula score de recencia"""
        age = (datetime.utcnow() - event.timestamp).total_seconds()

        if age < 3600:      # < 1 hora
            return 100
        elif age < 7200:    # < 2 horas
            return 90
        elif age < 14400:   # < 4 horas
            return 75
        elif age < 28800:   # < 8 horas
            return 60
        elif age < 86400:   # < 24 horas
            return 40
        elif age < 172800:  # < 48 horas
            return 25
        else:
            return 10

    def _calculate_correlation_boost(self, event: Event) -> float:
        """Detecta si hay otros eventos similares recientes (efecto sinergia)"""
        # Simplificado: buscar eventos del mismo tipo en las últimas 6h
        try:
            recent = self.db.get_recent_events(hours=6, limit=100)
            similar = [
                e for e in recent 
                if e.event_type == event.event_type and e.id != event.id
            ]

            if len(similar) >= 5:
                return 100  # Consenso fuerte
            elif len(similar) >= 3:
                return 75
            elif len(similar) >= 1:
                return 50
            else:
                return 25
        except:
            return 25

    def score_batch(self, events: List[Event]) -> List[Dict[str, Any]]:
        """Scorea un lote de eventos"""
        return [self.score_event(e) for e in events]


class OpportunityEngine:
    """
    Motor de oportunidades.
    Transforma eventos calificados en oportunidades accionables para traders.
    """

    # Umbrales para generar oportunidades
    SCORE_THRESHOLDS = {
        "critical": 80,   # Score >= 80: Oportunidad crítica
        "high": 60,       # Score >= 60: Oportunidad alta
        "medium": 40,     # Score >= 40: Oportunidad media
        "low": 20         # Score >= 20: Oportunidad baja
    }

    # Mapeo de tipos de evento a tipos de oportunidad
    OPPORTUNITY_TYPES = {
        EventType.PRICE_MOVEMENT: {
            "bullish": "LONG_SETUP",
            "bearish": "SHORT_SETUP",
            "neutral": "WATCHLIST_ADD"
        },
        EventType.VOLUME_SPIKE: {
            "default": "MOMENTUM_PLAY"
        },
        EventType.HACK_EXPLOIT: {
            "default": "AVOID_OR_SHORT"
        },
        EventType.REGULATORY: {
            "bullish": "REGULATORY_TAILWIND",
            "bearish": "REGULATORY_HEADWIND",
            "neutral": "MONITOR_COMPLIANCE"
        },
        EventType.GEOPOLITICAL: {
            "bullish": "SAFE_HAVEN_FLOW",
            "bearish": "RISK_OFF",
            "neutral": "MONITOR_GEO"
        },
        EventType.MACRO_EVENT: {
            "bullish": "MACRO_TAILWIND",
            "bearish": "MACRO_HEADWIND",
            "neutral": "MONITOR_MACRO"
        },
        EventType.EARNINGS: {
            "bullish": "POST_EARNINGS_RUN",
            "bearish": "POST_EARNINGS_DROP",
            "neutral": "EARNINGS_NEUTRAL"
        },
        EventType.SENTIMENT_SHIFT: {
            "bullish": "SENTIMENT_TURN_BULL",
            "bearish": "SENTIMENT_TURN_BEAR",
            "neutral": "SENTIMENT_WATCH"
        },
        EventType.SOCIAL_TREND: {
            "default": "VIRAL_MOMENTUM"
        },
        EventType.NEWS: {
            "default": "NEWS_DRIVEN"
        },
        EventType.TECHNICAL_SIGNAL: {
            "bullish": "TECHNICAL_BREAKOUT",
            "bearish": "TECHNICAL_BREAKDOWN",
            "neutral": "TECHNICAL_WATCH"
        },
        EventType.WHALE_MOVEMENT: {
            "bullish": "WHALE_ACCUMULATION",
            "bearish": "WHALE_DISTRIBUTION",
            "neutral": "WHALE_WATCH"
        },
        EventType.MERGER_ACQUISITION: {
            "default": "ARB_OPPORTUNITY"
        }
    }

    # Sugerencias de acción por tipo de oportunidad
    ACTION_TEMPLATES = {
        "LONG_SETUP": {
            "action": "Considerar posición larga",
            "timeframe": "Swing (1-5 días)",
            "risk": "Stop-loss bajo soporte reciente",
            "rationale": "Momentum alcista con catalizador fundamental"
        },
        "SHORT_SETUP": {
            "action": "Considerar posición corta",
            "timeframe": "Swing (1-5 días)",
            "risk": "Stop-loss sobre resistencia reciente",
            "rationale": "Momentum bajista con catalizador negativo"
        },
        "MOMENTUM_PLAY": {
            "action": "Entrada en momentum",
            "timeframe": "Day trade / Scalp",
            "risk": "Tight stop, objetivo parcial rápido",
            "rationale": "Volumen anómalo indica interés institucional"
        },
        "AVOID_OR_SHORT": {
            "action": "Evitar o posición corta",
            "timeframe": "Inmediato",
            "risk": "Alto — eventos de seguridad son impredecibles",
            "rationale": "Evento de seguridad compromete valor fundamental"
        },
        "SAFE_HAVEN_FLOW": {
            "action": "Rotación a activos refugio",
            "timeframe": "1-2 semanas",
            "risk": "Reversión rápida si tensiones se calman",
            "rationale": "Tensión geopolítica impulsa demanda de seguridad"
        },
        "RISK_OFF": {
            "action": "Reducir exposición o hedging",
            "timeframe": "Inmediato",
            "risk": "Falso positivo si crisis no materializa",
            "rationale": "Evento geopolítico aumenta aversión al riesgo"
        },
        "WHALE_ACCUMULATION": {
            "action": "Seguimiento de ballenas",
            "timeframe": "Posición acumulativa",
            "risk": "Ballena puede distribuir después",
            "rationale": "Grandes tenedores están comprando"
        },
        "WHALE_DISTRIBUTION": {
            "action": "Precaución — presión vendedora",
            "timeframe": "Corto plazo",
            "risk": "Puede ser reubicación, no venta total",
            "rationale": "Grandes tenedores están vendiendo"
        },
        "VIRAL_MOMENTUM": {
            "action": "Ride the wave (con cuidado)",
            "timeframe": "Muy corto (horas-días)",
            "risk": "Alta volatilidad, pump-and-dump",
            "rationale": "Tendencia social impulsa demanda especulativa"
        },
        "POST_EARNINGS_RUN": {
            "action": "Seguimiento post-earnings",
            "timeframe": "1-3 días",
            "risk": "Profit-taking puede revertir movimiento",
            "rationale": "Resultados positivos no están completamente precificados"
        },
        "MACRO_TAILWIND": {
            "action": "Alineación con tendencia macro",
            "timeframe": "1-4 semanas",
            "risk": "Datos posteriores pueden contradecir",
            "rationale": "Datos macro favorables para el activo/sector"
        },
        "ARB_OPPORTUNITY": {
            "action": "Arbitraje de fusión",
            "timeframe": "Hasta cierre del deal",
            "risk": "Deal puede fracasar",
            "rationale": "Diferencial de precio entre oferta y mercado"
        },
        "WATCHLIST_ADD": {
            "action": "Agregar a watchlist",
            "timeframe": "Monitoreo",
            "risk": "Ninguna — solo observación",
            "rationale": "Activo muestra actividad relevante"
        }
    }

    def __init__(self, db: OMACoreDatabase, score_engine: ScoreEngine):
        self.db = db
        self.score_engine = score_engine

    def generate_opportunities(self, events: List[Event], min_score: float = 40.0) -> List[Dict[str, Any]]:
        """
        Genera oportunidades a partir de eventos calificados.
        Solo genera oportunidades con score >= min_score.
        """
        opportunities = []

        # Scorear todos los eventos
        scored_events = self.score_engine.score_batch(events)

        for score_data in scored_events:
            final_score = score_data["final_score"]

            if final_score < min_score:
                continue

            # Obtener el evento
            event = next((e for e in events if e.id == score_data["event_id"]), None)
            if not event:
                continue

            # Generar oportunidad
            opportunity = self._create_opportunity(event, score_data)
            if opportunity:
                opportunities.append(opportunity)

                # Guardar en base de datos
                self.db.insert_opportunity(opportunity)
                self.db.update_event_scores(event.id, final_score, opportunity.get("relevance", 0))
                self.db.mark_processed(event.id)

        # Ordenar por score
        opportunities.sort(key=lambda x: x["score"], reverse=True)

        return opportunities

    def _create_opportunity(self, event: Event, score_data: Dict) -> Optional[Dict[str, Any]]:
        """Crea una oportunidad a partir de un evento scoreado"""

        # Determinar dirección del sentimiento
        if event.sentiment_score > 0.3:
            direction = "bullish"
        elif event.sentiment_score < -0.3:
            direction = "bearish"
        else:
            direction = "neutral"

        # Obtener tipo de oportunidad
        type_map = self.OPPORTUNITY_TYPES.get(event.event_type, {"default": "NEWS_DRIVEN"})
        opp_type = type_map.get(direction, type_map.get("default", "NEWS_DRIVEN"))

        # Obtener template de acción
        action_template = self.ACTION_TEMPLATES.get(opp_type, self.ACTION_TEMPLATES["WATCHLIST_ADD"])

        # Calcular convicción (0-100)
        conviction = self._calculate_conviction(event, score_data)

        # Determinar prioridad
        priority = self._determine_priority(score_data["final_score"], conviction)

        # Calcular nivel de riesgo
        risk_level = self._calculate_risk(event, opp_type)

        # Construir oportunidad
        assets_str = ", ".join([a.symbol for a in event.assets]) if event.assets else "N/A"

        opportunity = {
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
            "action_details": action_template,
            "risk_level": risk_level,
            "event_type": event.event_type.value,
            "sentiment": event.sentiment.name,
            "source": event.source,
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }

        return opportunity

    def _calculate_conviction(self, event: Event, score_data: Dict) -> float:
        """Calcula nivel de convicción (0-100)"""
        base = score_data["final_score"] * 0.6

        # Boost por confianza de fuente
        source_boost = score_data["component_scores"]["source_confidence"] * 0.2

        # Boost por múltiples activos correlacionados
        asset_boost = min(len(event.assets) * 5, 15)

        # Penalización por sentimiento neutro
        neutral_penalty = 10 if event.sentiment == Sentiment.NEUTRAL else 0

        conviction = base + source_boost + asset_boost - neutral_penalty
        return round(min(max(conviction, 0), 100), 2)

    def _determine_priority(self, score: float, conviction: float) -> str:
        """Determina prioridad de la oportunidad"""
        combined = (score + conviction) / 2

        if combined >= 75:
            return "CRITICAL"
        elif combined >= 60:
            return "HIGH"
        elif combined >= 45:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_risk(self, event: Event, opp_type: str) -> str:
        """Calcula nivel de riesgo"""
        # Eventos de seguridad son de alto riesgo
        if event.event_type == EventType.HACK_EXPLOIT:
            return "VERY_HIGH"

        # Eventos geopolíticos son de riesgo alto
        if event.event_type == EventType.GEOPOLITICAL:
            return "HIGH"

        # Viral momentum es de riesgo alto
        if opp_type == "VIRAL_MOMENTUM":
            return "HIGH"

        # Movimientos de precio extremos
        if event.event_type == EventType.PRICE_MOVEMENT:
            if abs(event.sentiment_score) > 0.8:
                return "HIGH"
            elif abs(event.sentiment_score) > 0.5:
                return "MEDIUM"

        return "MEDIUM"

    def _build_description(self, event: Event, action_template: Dict) -> str:
        """Construye descripción detallada de la oportunidad"""
        parts = [
            f"📊 Evento: {event.event_type.value}",
            f"📰 {event.title}",
            f"💡 Acción: {action_template['action']}",
            f"⏱️ Timeframe: {action_template['timeframe']}",
            f"🎯 Rationale: {action_template['rationale']}",
            f"⚠️ Riesgo: {action_template['risk']}"
        ]

        if event.assets:
            assets_info = ", ".join([f"{a.symbol} (${a.price_at_event:,.2f})" if a.price_at_event else a.symbol for a in event.assets])
            parts.insert(1, f"💰 Activos: {assets_info}")

        if event.summary:
            parts.insert(2, f"📝 Contexto: {event.summary[:200]}...")

        return "\n".join(parts)


class Pipeline:
    """
    Pipeline completo: Collect → Score → Opportunity → Store
    """

    def __init__(self, db_path: str = "oma_core.db"):
        self.db = OMACoreDatabase(db_path)
        self.score_engine = ScoreEngine(self.db)
        self.opportunity_engine = OpportunityEngine(self.db, self.score_engine)

    def run(self, events: List[Event], min_score: float = 40.0) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo.

        Args:
            events: Lista de eventos a procesar
            min_score: Score mínimo para generar oportunidades

        Returns:
            Resumen de ejecución
        """
        print(f"[Pipeline] Procesando {len(events)} eventos...")

        # 1. Guardar eventos en DB
        stored = 0
        for event in events:
            try:
                self.db.insert_event(event)
                stored += 1
            except Exception as e:
                print(f"[Pipeline] Error guardando evento: {e}")

        print(f"[Pipeline] {stored}/{len(events)} eventos almacenados")

        # 2. Generar oportunidades
        opportunities = self.opportunity_engine.generate_opportunities(events, min_score)

        print(f"[Pipeline] {len(opportunities)} oportunidades generadas")

        # 3. Estadísticas
        stats = self.db.get_event_stats()

        return {
            "events_processed": len(events),
            "events_stored": stored,
            "opportunities_generated": len(opportunities),
            "database_stats": stats,
            "top_opportunities": opportunities[:10]
        }
