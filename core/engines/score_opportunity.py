"""O.M.A.-C.O.R.E. Score & Opportunity Engine — Sprint 13 Score Calibration"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
import json
import math
from core.schemas.event_schema import Event, EventType, Sentiment, Urgency, AssetClass
from core.database.db import OMACoreDatabase
from core.collectors.yahoo_data_guard import detect_data_quality_issue, should_downgrade_opportunity

class ScoreEngine:
    WEIGHTS = {
        "urgency": 0.25, "sentiment_magnitude": 0.20, "source_confidence": 0.20,
        "asset_relevance": 0.15, "recency": 0.10, "correlation_boost": 0.10
    }
    
    # Sprint 13: reduced multipliers to avoid premature clipping
    EVENT_MULTIPLIERS = {
        EventType.PRICE_MOVEMENT: 1.05, EventType.VOLUME_SPIKE: 1.05, EventType.HACK_EXPLOIT: 1.20,
        EventType.REGULATORY: 1.15, EventType.GEOPOLITICAL: 1.15, EventType.MACRO_EVENT: 1.15,
        EventType.EARNINGS: 1.05, EventType.MERGER_ACQUISITION: 1.05, EventType.SENTIMENT_SHIFT: 0.95,
        EventType.SOCIAL_TREND: 0.85, EventType.NEWS: 0.80, EventType.TECHNICAL_SIGNAL: 0.90,
        EventType.WHALE_MOVEMENT: 1.10
    }
    
    # Sprint 13: reduced urgency dominance — more room above CRITICAL
    URGENCY_SCORES = {
        Urgency.CRITICAL: 85, Urgency.HIGH: 60, Urgency.MEDIUM: 40,
        Urgency.LOW: 20, Urgency.BACKGROUND: 10
    }
    
    SOURCE_CONFIDENCE = {
        "coingecko": 0.95, "yahoo_finance": 0.95, "gdelt": 0.70,
        "rss_reuters_business": 0.85, "rss_coindesk": 0.80, "rss_cointelegraph": 0.80,
        "rss_forexlive": 0.80, "rss_investing": 0.75, "rss_marketwatch": 0.80,
        "rss_cnbc": 0.80, "rss_bloomberg": 0.90, "osiris": 0.75
    }
    
    # Sprint 13: logarithmic compression to prevent score clipping at 100
    # Threshold 60: scores below 60 pass through linearly
    # Above 60: each additional raw point adds diminishing returns
    # Asymptotically approaches 100 (never reaches 100 except for extreme scores)
    COMPRESSION_THRESHOLD = 60.0
    COMPRESSION_RANGE = 40.0  # 100 - threshold
    COMPRESSION_HALF_LIFE = 25.0  # how fast compression kicks in
    
    def __init__(self, db):
        self.db = db
    
    def _apply_scoring_curve(self, scaled_score):
        if scaled_score <= self.COMPRESSION_THRESHOLD:
            return round(scaled_score, 2)
        excess = scaled_score - self.COMPRESSION_THRESHOLD
        compressed = self.COMPRESSION_THRESHOLD + (excess * self.COMPRESSION_RANGE) / (excess + self.COMPRESSION_HALF_LIFE)
        return round(min(compressed, 100), 2)
    
    def score_event(self, event):
        scores = {}
        scores["urgency"] = self.URGENCY_SCORES.get(event.urgency, 20)
        scores["sentiment_magnitude"] = min(abs(event.sentiment_score) * 100, 100)
        source_conf = self.SOURCE_CONFIDENCE.get(event.source, 0.5)
        scores["source_confidence"] = source_conf * 100
        scores["asset_relevance"] = self._calculate_asset_relevance(event)
        scores["recency"] = self._calculate_recency(event)
        scores["correlation_boost"] = self._calculate_correlation_boost(event)
        
        raw_score = sum(scores[key] * self.WEIGHTS[key] for key in self.WEIGHTS.keys())
        multiplier = self.EVENT_MULTIPLIERS.get(event.event_type, 1.0)
        scaled_score = raw_score * multiplier
        final_score = self._apply_scoring_curve(scaled_score)
        
        return {
            "raw_score": raw_score, "scaled_score": round(scaled_score, 2),
            "final_score": final_score,
            "multiplier": multiplier, "component_scores": scores, "event_id": event.id
        }
    
    def _calculate_asset_relevance(self, event):
        if not event.assets:
            return 50.0
        high_interest = {"BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "EURUSD", "GBPUSD", "USDJPY", "GC=F", "SI=F", "CL=F"}
        relevance_sum = sum(100 if a.symbol in high_interest else 70 if a.asset_class in [AssetClass.CRYPTO, AssetClass.STOCK] else 50 for a in event.assets)
        return min(relevance_sum / max(len(event.assets), 1), 100)
    
    def _calculate_recency(self, event):
        age = (datetime.now(timezone.utc) - event.timestamp).total_seconds()
        if age < 3600: return 100
        elif age < 7200: return 90
        elif age < 14400: return 75
        elif age < 28800: return 60
        elif age < 86400: return 40
        elif age < 172800: return 25
        else: return 10
    
    def _calculate_correlation_boost(self, event):
        try:
            recent = self.db.get_recent_events(hours=6, limit=100)
            similar = [e for e in recent if e.event_type == event.event_type and e.id != event.id]
            if len(similar) >= 5: return 100
            elif len(similar) >= 3: return 75
            elif len(similar) >= 1: return 50
            else: return 25
        except:
            return 25
    
    def score_batch(self, events):
        return [self.score_event(e) for e in events]

class OpportunityEngine:
    OPPORTUNITY_TYPES = {
        EventType.PRICE_MOVEMENT: {"bullish": "LONG_SETUP", "bearish": "SHORT_SETUP", "neutral": "WATCHLIST_ADD"},
        EventType.VOLUME_SPIKE: {"default": "MOMENTUM_PLAY"},
        EventType.HACK_EXPLOIT: {"default": "AVOID_OR_SHORT"},
        EventType.REGULATORY: {"bullish": "REGULATORY_TAILWIND", "bearish": "REGULATORY_HEADWIND", "neutral": "MONITOR_COMPLIANCE"},
        EventType.GEOPOLITICAL: {"bullish": "SAFE_HAVEN_FLOW", "bearish": "RISK_OFF", "neutral": "MONITOR_GEO"},
        EventType.MACRO_EVENT: {"bullish": "MACRO_TAILWIND", "bearish": "MACRO_HEADWIND", "neutral": "MONITOR_MACRO"},
        EventType.EARNINGS: {"bullish": "POST_EARNINGS_RUN", "bearish": "POST_EARNINGS_DROP", "neutral": "EARNINGS_NEUTRAL"},
        EventType.SENTIMENT_SHIFT: {"bullish": "SENTIMENT_TURN_BULL", "bearish": "SENTIMENT_TURN_BEAR", "neutral": "SENTIMENT_WATCH"},
        EventType.SOCIAL_TREND: {"default": "VIRAL_MOMENTUM"},
        EventType.NEWS: {"default": "NEWS_DRIVEN"},
        EventType.TECHNICAL_SIGNAL: {"bullish": "TECHNICAL_BREAKOUT", "bearish": "TECHNICAL_BREAKDOWN", "neutral": "TECHNICAL_WATCH"},
        EventType.WHALE_MOVEMENT: {"bullish": "WHALE_ACCUMULATION", "bearish": "WHALE_DISTRIBUTION", "neutral": "WHALE_WATCH"},
        EventType.MERGER_ACQUISITION: {"default": "ARB_OPPORTUNITY"}
    }
    
    ACTION_TEMPLATES = {
        "LONG_SETUP": {"action": "Considerar posicion larga", "timeframe": "Swing (1-5 dias)", "risk": "Stop-loss bajo soporte reciente", "rationale": "Momentum alcista con catalizador fundamental"},
        "SHORT_SETUP": {"action": "Considerar posicion corta", "timeframe": "Swing (1-5 dias)", "risk": "Stop-loss sobre resistencia reciente", "rationale": "Momentum bajista con catalizador negativo"},
        "MOMENTUM_PLAY": {"action": "Entrada en momentum", "timeframe": "Day trade / Scalp", "risk": "Tight stop, objetivo parcial rapido", "rationale": "Volumen anomalo indica interes institucional"},
        "AVOID_OR_SHORT": {"action": "Evitar o posicion corta", "timeframe": "Inmediato", "risk": "Alto — eventos de seguridad son impredecibles", "rationale": "Evento de seguridad compromete valor fundamental"},
        "SAFE_HAVEN_FLOW": {"action": "Rotacion a activos refugio", "timeframe": "1-2 semanas", "risk": "Reversion rapida si tensiones se calman", "rationale": "Tension geopolitica impulsa demanda de seguridad"},
        "RISK_OFF": {"action": "Reducir exposicion o hedging", "timeframe": "Inmediato", "risk": "Falso positivo si crisis no materializa", "rationale": "Evento geopolitico aumenta aversion al riesgo"},
        "WHALE_ACCUMULATION": {"action": "Seguimiento de ballenas", "timeframe": "Posicion acumulativa", "risk": "Ballena puede distribuir despues", "rationale": "Grandes tenedores estan comprando"},
        "WHALE_DISTRIBUTION": {"action": "Precaucion — presion vendedora", "timeframe": "Corto plazo", "risk": "Puede ser reubicacion, no venta total", "rationale": "Grandes tenedores estan vendiendo"},
        "VIRAL_MOMENTUM": {"action": "Ride the wave (con cuidado)", "timeframe": "Muy corto (horas-dias)", "risk": "Alta volatilidad, pump-and-dump", "rationale": "Tendencia social impulsa demanda especulativa"},
        "POST_EARNINGS_RUN": {"action": "Seguimiento post-earnings", "timeframe": "1-3 dias", "risk": "Profit-taking puede revertir movimiento", "rationale": "Resultados positivos no estan completamente precificados"},
        "MACRO_TAILWIND": {"action": "Alineacion con tendencia macro", "timeframe": "1-4 semanas", "risk": "Datos posteriores pueden contradecir", "rationale": "Datos macro favorables para el activo/sector"},
        "ARB_OPPORTUNITY": {"action": "Arbitraje de fusion", "timeframe": "Hasta cierre del deal", "risk": "Deal puede fracasar", "rationale": "Diferencial de precio entre oferta y mercado"},
        "WATCHLIST_ADD": {"action": "Agregar a watchlist", "timeframe": "Monitoreo", "risk": "Ninguna — solo observacion", "rationale": "Activo muestra actividad relevante"}
    }
    
    def __init__(self, db, score_engine):
        self.db = db
        self.score_engine = score_engine
    
    def generate_opportunities(self, events, min_score=40.0):
        # Filtrar fuentes que no aportan valor (Polymarket sin sentimiento real)
        events = [e for e in events if e.sentiment_score != 0.0 or e.source in ["fred", "yahoo_finance"]]
        print(f"[Pipeline] {len(events)} eventos con sentimiento real despues de filtrar")
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
                # Apply data quality guardrail — downgrade suspicious opportunities
                should_downgrade, downgrade = should_downgrade_opportunity(event)
                if should_downgrade:
                    old_score = opportunity["score"]
                    opportunity["score"] = min(old_score, downgrade.get("max_score", 30.0))
                    opportunity["priority"] = downgrade.get("max_priority", "MEDIUM")
                    opportunity["conviction"] = min(opportunity.get("conviction", 0), downgrade.get("max_conviction", 30.0))
                    opportunity["action_suggested"] = downgrade.get("action_suggested", opportunity["action_suggested"])
                    opportunity["risk_level"] = downgrade.get("risk_level", opportunity["risk_level"])
                    opportunity["data_quality_reason"] = downgrade.get("data_quality_reason", "")
                    opportunity["title"] = f"[DATA_QUALITY] {opportunity.get('title', '')}"
                    opportunity["opportunity_type"] = "WATCHLIST_ADD"
                    print(f"[Pipeline] Data guard downgraded {getattr(event, 'id', '')}: {downgrade.get('data_quality_reason', '')} "
                          f"(score {old_score} -> {opportunity['score']})")
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
        priority = self._determine_priority(score_data["final_score"], conviction, event, score_data)
        risk_level = self._calculate_risk(event, opp_type)
        
        return {
            "id": f"opp_{event.id[:8]}", "event_id": event.id,
            "title": f"[{opp_type}] {event.title[:80]}",
            "description": self._build_description(event, action_template),
            "opportunity_type": opp_type,
            "asset_class": event.assets[0].asset_class.value if event.assets else "unknown",
            "assets": [a.symbol for a in event.assets],
            "score": score_data["final_score"], "conviction": conviction,
            "priority": priority, "action_suggested": action_template["action"],
            "action_details": action_template, "risk_level": risk_level,
            "event_type": event.event_type.value, "sentiment": event.sentiment.name,
            "source": event.source, "timestamp": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }
    
    def _calculate_conviction(self, event, score_data):
        # Sprint 13: conviction is fully decoupled from score.
        # It measures data quality, source reliability, evidence completeness,
        # event freshness, asset specificity, and rationale strength.
        
        # Source reliability (0-25)
        source_reliability = score_data["component_scores"]["source_confidence"] * 0.25
        
        # Evidence completeness (0-25)
        has_price = any(
            a.price_at_event is not None and a.price_at_event > 0
            for a in (event.assets or [])
        )
        evidence = 25 if has_price else 10
        if event.summary:
            evidence = min(evidence + 5, 25)
        
        # Event freshness (0-20)
        age_hours = (datetime.now(timezone.utc) - event.timestamp).total_seconds() / 3600
        if age_hours < 1:
            freshness = 20
        elif age_hours < 6:
            freshness = 16
        elif age_hours < 12:
            freshness = 12
        elif age_hours < 24:
            freshness = 8
        elif age_hours < 48:
            freshness = 4
        else:
            freshness = 2
        
        # Asset specificity (0-15)
        specificity = min(len(event.assets) * 5, 15) if event.assets else 0
        
        # Rationale strength (0-15)
        rationale = 10 if event.summary else 0
        if event.source_url:
            rationale += 5
        rationale = min(rationale, 15)
        
        conviction = source_reliability + evidence + freshness + specificity + rationale
        
        # Data quality penalty (multiplicative — halves conviction for bad data)
        is_dq, _ = detect_data_quality_issue(event)
        if is_dq:
            conviction = conviction * 0.5
        
        return round(min(max(conviction, 1), 100), 2)
    
    def _passes_critical_gate(self, event, score_data):
        """Strong evidence gate: at least 4 of 7 conditions must be met."""
        conditions = 0
        
        # 1. Validated source quality
        if score_data["component_scores"]["source_confidence"] >= 85:
            conditions += 1
        
        # 2. High urgency
        if event.urgency in (Urgency.CRITICAL, Urgency.HIGH):
            conditions += 1
        
        # 3. High sentiment magnitude with real data
        if abs(event.sentiment_score) >= 0.5:
            conditions += 1
        
        # 4. Relevant asset mapping (trading-relevant classes)
        if event.assets and event.assets[0].asset_class in (
            AssetClass.CRYPTO, AssetClass.STOCK, AssetClass.FOREX
        ):
            conditions += 1
        
        # 5. Non-data-quality issue
        is_dq, _ = detect_data_quality_issue(event)
        if not is_dq:
            conditions += 1
        
        # 6. Fresh event
        if score_data["component_scores"]["recency"] >= 75:
            conditions += 1
        
        # 7. Corroborating context
        if score_data["component_scores"]["correlation_boost"] >= 50:
            conditions += 1
        
        return conditions >= 4
    
    def _determine_priority(self, score, conviction, event=None, score_data=None):
        # Sprint 13: stricter CRITICAL threshold with evidence gate
        combined = (score + conviction) / 2
        if combined >= 80 and event is not None and score_data is not None:
            if self._passes_critical_gate(event, score_data):
                return "CRITICAL"
        if combined >= 65:
            return "HIGH"
        elif combined >= 45:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_risk(self, event, opp_type):
        if event.event_type == EventType.HACK_EXPLOIT: return "VERY_HIGH"
        if event.event_type == EventType.GEOPOLITICAL: return "HIGH"
        if opp_type == "VIRAL_MOMENTUM": return "HIGH"
        if event.event_type == EventType.PRICE_MOVEMENT:
            if abs(event.sentiment_score) > 0.8: return "HIGH"
            elif abs(event.sentiment_score) > 0.5: return "MEDIUM"
        return "MEDIUM"
    
    def _build_description(self, event, action_template):
        parts = [f"Evento: {event.event_type.value}", event.title,
                 f"Accion: {action_template['action']}", f"Timeframe: {action_template['timeframe']}",
                 f"Rationale: {action_template['rationale']}", f"Riesgo: {action_template['risk']}"]
        if event.assets:
            assets_info = ", ".join([f"{a.symbol} (${a.price_at_event:,.2f})" if a.price_at_event else a.symbol for a in event.assets])
            parts.insert(1, f"Activos: {assets_info}")
        if event.summary:
            parts.insert(2, f"Contexto: {event.summary[:200]}...")
        return "\n".join(parts)

class Pipeline:
    def __init__(self, db_path="oma_core.db"):
        self.db = OMACoreDatabase(db_path)
        self.score_engine = ScoreEngine(self.db)
        self.opportunity_engine = OpportunityEngine(self.db, self.score_engine)
    
    def run(self, events, min_score=40.0):
        print(f"[Pipeline] Procesando {len(events)} eventos...")
        stored = 0
        for event in events:
            try:
                self.db.insert_event(event)
                stored += 1
            except Exception as e:
                print(f"[Pipeline] Error: {e}")
        print(f"[Pipeline] {stored}/{len(events)} eventos almacenados")
        
        opportunities = self.opportunity_engine.generate_opportunities(events, min_score)
        print(f"[Pipeline] {len(opportunities)} oportunidades generadas")
        
        stats = self.db.get_event_stats()
        return {
            "events_processed": len(events), "events_stored": stored,
            "opportunities_generated": len(opportunities),
            "database_stats": stats, "top_opportunities": opportunities[:10]
        }
