"""OSIRIS Risk Agent — Volatility, drawdown, correlation, systemic risk"""
from typing import List, Optional, Dict, Any
from statistics import mean, stdev
from math import sqrt
from core.schemas.agent_schema import (
    AgentOpinion, AgentRole, Recommendation
)
from core.schemas.event_schema import Event, EventType
from core.event_bus import EventBus, EventTopic, bus as default_bus


class RiskAgent:
    def __init__(
        self,
        name: str = "risk_agent",
        event_bus: Optional[EventBus] = None,
    ):
        self.name = name
        self.bus = event_bus or default_bus
        self.processed_count = 0
        self.bus.subscribe(EventTopic.EVENTS_RAW, self.on_event)

    def on_event(self, event_data: dict) -> None:
        event = Event.from_dict(event_data)
        opinion = self.analyze(event)
        if opinion:
            self.bus.publish(EventTopic.OPINIONS_AGENT, opinion.to_dict(), source=self.name)
            self.processed_count += 1

    def analyze(self, event: Event) -> Optional[AgentOpinion]:
        if not event.assets:
            return None

        evidence = []
        asset = event.assets[0]
        symbol = asset.symbol

        ohlcv = self._fetch_ohlcv(symbol)
        risk_score = 0.3
        impact_score = 0.5

        scenario_risk = self._assess_scenario_risk(event)

        if ohlcv and len(ohlcv) >= 20:
            closes = [c["close"] for c in ohlcv]
            highs = [c["high"] for c in ohlcv]
            lows = [c["low"] for c in ohlcv]
            volumes = [c["volume"] for c in ohlcv]
            current_price = closes[-1]

            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            daily_vol = stdev(returns) if len(returns) > 1 else 0.02
            annualized_vol = daily_vol * sqrt(365) * 100

            expected_drawdown = daily_vol * 2 * 100

            atr_values = []
            for i in range(1, len(highs)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1]),
                )
                atr_values.append(tr)
            atr = mean(atr_values[-14:]) if len(atr_values) >= 14 else mean(atr_values) if atr_values else 0
            atr_pct = (atr / current_price * 100) if current_price > 0 else 0

            volume_sma = mean(volumes[-20:]) if len(volumes) >= 20 else mean(volumes)
            volume_ratio = volumes[-1] / volume_sma if volume_sma > 0 else 1.0

            sma20 = mean(closes[-20:])
            sma50 = mean(closes[-50:]) if len(closes) >= 50 else sma20
            trend_dir = "bullish" if sma20 > sma50 else "bearish" if sma20 < sma50 else "neutral"

            evidence.append(f"Asset: {symbol} @ ${current_price:.4f}")
            evidence.append(f"Annualized volatility: {annualized_vol:.1f}%")
            evidence.append(f"Expected drawdown (2σ): {expected_drawdown:.1f}%")
            evidence.append(f"ATR %: {atr_pct:.2f}%")
            evidence.append(f"Volume ratio: {volume_ratio:.2f}x")

            if annualized_vol > 80:
                risk_score = max(risk_score, 0.8)
                evidence.append(f"CRITICAL: Extreme volatility ({annualized_vol:.0f}% annualized)")
            elif annualized_vol > 50:
                risk_score = max(risk_score, 0.6)
                evidence.append(f"HIGH: High volatility ({annualized_vol:.0f}% annualized)")
            elif annualized_vol > 30:
                risk_score = max(risk_score, 0.4)
                evidence.append(f"MODERATE: Elevated volatility ({annualized_vol:.0f}% annualized)")
            else:
                evidence.append(f"LOW: Normal volatility ({annualized_vol:.0f}% annualized)")

            if atr_pct > 5:
                risk_score = min(1.0, risk_score + 0.15)
                evidence.append(f"Wide ATR ({atr_pct:.1f}%) — wide stops needed")
            elif atr_pct > 3:
                risk_score = min(1.0, risk_score + 0.05)

            if volume_ratio < 0.3:
                risk_score = min(1.0, risk_score + 0.1)
                evidence.append(f"Low liquidity — slippage risk")
        else:
            evidence.append(f"No OHLCV data for {symbol} — defaulting to event-based risk")
            annualized_vol = 40.0
            expected_drawdown = 5.0
            atr_pct = 2.0

        scenario_weight = scenario_risk.get("weight", 0)
        risk_score = min(1.0, risk_score + scenario_weight)
        if scenario_weight > 0:
            evidence.append(f"Scenario risk: {scenario_risk['label']}")
            impact_score = max(impact_score, scenario_risk.get("impact", 0.5))

        if risk_score >= 0.7:
            base_recommendation = Recommendation.AVOID
            risk_score = 0.8
            evidence.append("Risk threshold exceeded — AVOID")
        elif risk_score >= 0.5:
            base_recommendation = Recommendation.HEDGE
            evidence.append("Elevated risk — HEDGE or reduce size")
        elif annualized_vol > 60:
            base_recommendation = Recommendation.WATCH
            evidence.append("High volatility but manageable — WATCH")
        else:
            base_recommendation = Recommendation.WATCH
            evidence.append("Risk profile acceptable — no directional bias")

        event_risk = event.urgency.value / 4.0
        if event_risk > 0.75:
            risk_score = min(1.0, risk_score + 0.15)
            evidence.append(f"Event urgency amplifies risk")
        elif event_risk > 0.5:
            risk_score = min(1.0, risk_score + 0.05)

        n_candles = len(ohlcv) if ohlcv else 0
        if n_candles >= 100:
            data_quality = 0.25
        elif n_candles >= 50:
            data_quality = 0.20
        elif n_candles >= 20:
            data_quality = 0.15
        else:
            data_quality = 0.10

        event_clarity = 1.0 - event.urgency.value / 4.0
        stress_level = risk_score
        confidence = round(0.30 + data_quality * 0.6 + event_clarity * 0.2 + (1 - stress_level) * 0.2, 3)
        confidence = max(0.30, min(0.85, confidence))

        max_position_pct = max(1.0, 20.0 * (1.0 - risk_score))
        suggested_stop_pct = max(atr_pct * 1.5, 2.0)

        metadata = {
            "symbol": symbol,
            "annualized_volatility": round(annualized_vol, 1),
            "expected_drawdown_2sigma": round(expected_drawdown, 1),
            "atr_pct": round(atr_pct, 2),
            "risk_score_raw": round(risk_score, 3),
            "max_position_pct": round(max_position_pct, 1),
            "suggested_stop_pct": round(suggested_stop_pct, 1),
            "scenario": scenario_risk.get("label", "normal"),
        }

        return AgentOpinion(
            agent_name=self.name,
            agent_role=AgentRole.RISK_ANALYST,
            confidence=round(confidence, 3),
            impact_score=round(impact_score, 3),
            risk_score=round(risk_score, 3),
            evidence=evidence,
            recommendation=base_recommendation,
            rationale=f"Risk assessment for {symbol}: vol={annualized_vol:.0f}%, "
                      f"ATR={atr_pct:.1f}%, scenario={scenario_risk['label']}. "
                      f"Max position: {max_position_pct:.0f}%. "
                      f"Recommendation: {base_recommendation.value}.",
            event_id=event.id,
            metadata=metadata,
        )

    def analyze_batch(self, events: List[Event]) -> List[AgentOpinion]:
        opinions = []
        for event in events:
            opinion = self.analyze(event)
            if opinion:
                opinions.append(opinion)
                self.processed_count += 1
        return opinions

    def _fetch_ohlcv(self, symbol: str) -> Optional[List[Dict[str, float]]]:
        try:
            import requests
            binance_symbols = {
                "BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT",
                "XRP": "XRPUSDT", "BNB": "BNBUSDT", "ADA": "ADAUSDT",
                "DOGE": "DOGEUSDT", "AVAX": "AVAXUSDT", "LINK": "LINKUSDT",
                "MATIC": "MATICUSDT", "DOT": "DOTUSDT", "UNI": "UNIUSDT",
                "LTC": "LTCUSDT", "BCH": "BCHUSDT", "ATOM": "ATOMUSDT",
            }
            if symbol in binance_symbols:
                pair = binance_symbols[symbol]
                url = "https://api.binance.com/api/v3/klines"
                resp = requests.get(url, params={"symbol": pair, "interval": "1h", "limit": 100}, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return [{"close": float(k[4]), "high": float(k[2]), "low": float(k[3]), "volume": float(k[5])} for k in data]
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d", interval="1h")
            if not hist.empty:
                return [{"close": float(r["Close"]), "high": float(r["High"]), "low": float(r["Low"]), "volume": float(r["Volume"])} for _, r in hist.iterrows()]
        except Exception:
            pass
        return None

    def _assess_scenario_risk(self, event: Event) -> Dict[str, Any]:
        scenarios = {
            EventType.HACK_EXPLOIT: {"weight": 0.35, "label": "security_breach", "impact": 0.8},
            EventType.GEOPOLITICAL: {"weight": 0.25, "label": "geopolitical_crisis", "impact": 0.7},
            EventType.REGULATORY: {"weight": 0.15, "label": "regulatory_event", "impact": 0.6},
            EventType.MACRO_EVENT: {"weight": 0.10, "label": "macro_shock", "impact": 0.6},
            EventType.WHALE_MOVEMENT: {"weight": 0.15, "label": "whale_activity", "impact": 0.5},
            EventType.MERGER_ACQUISITION: {"weight": 0.05, "label": "mna_event", "impact": 0.4},
            EventType.EARNINGS: {"weight": 0.10, "label": "earnings_event", "impact": 0.5},
            EventType.PRICE_MOVEMENT: {"weight": 0.05, "label": "price_movement", "impact": 0.3},
            EventType.VOLUME_SPIKE: {"weight": 0.05, "label": "volume_anomaly", "impact": 0.3},
            EventType.SENTIMENT_SHIFT: {"weight": 0.05, "label": "sentiment_shift", "impact": 0.3},
            EventType.SOCIAL_TREND: {"weight": 0.02, "label": "social_trend", "impact": 0.2},
            EventType.TECHNICAL_SIGNAL: {"weight": 0.03, "label": "technical_signal", "impact": 0.3},
        }
        base = scenarios.get(event.event_type, {"weight": 0.02, "label": "unknown", "impact": 0.2})
        urgency_modifier = event.urgency.value / 4.0
        return {
            "weight": base["weight"] * urgency_modifier,
            "label": base["label"],
            "impact": base["impact"] * urgency_modifier,
        }
