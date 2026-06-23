"""OSIRIS Trend Agent — Minimal trend-following using EMA crossovers
Designed to break Council symmetry: provides a third independent directional vote.
"""
from typing import Optional, List, Dict, Any
from statistics import mean
from core.schemas.agent_schema import AgentOpinion, AgentRole, Recommendation
from core.schemas.event_schema import Event


class TrendAgent:
    def __init__(self, name: str = "trend_agent"):
        self.name = name
        self.processed_count = 0

    def analyze(self, event: Event, ohlcv: Optional[List[Dict]] = None) -> Optional[AgentOpinion]:
        if not event.assets or not ohlcv or len(ohlcv) < 50:
            return None

        closes = [c["close"] for c in ohlcv]
        price = closes[-1]
        symbol = event.assets[0].symbol

        ema20 = mean(closes[-20:])
        ema50 = mean(closes[-50:])
        ema200 = mean(closes[-200:]) if len(closes) >= 200 else ema50

        price_above_20 = price > ema20
        price_above_50 = price > ema50
        price_above_200 = price > ema200

        ema20_above_50 = ema20 > ema50
        ema20_above_200 = ema20 > ema200
        ema50_above_200 = ema50 > ema200

        bullish_count = sum([price_above_20, price_above_50, price_above_200,
                             ema20_above_50, ema20_above_200, ema50_above_200])
        bearish_count = 6 - bullish_count

        trend_strength = abs(price / ema50 - 1) * 100
        momentum = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0

        if bullish_count >= 5:
            rec = Recommendation.BUY
            confidence = min(0.75, 0.50 + trend_strength * 1.5)
            evidence = f"Strong bullish alignment ({bullish_count}/6)"
        elif bearish_count >= 5:
            rec = Recommendation.SELL
            confidence = min(0.75, 0.50 + trend_strength * 1.5)
            evidence = f"Strong bearish alignment ({bearish_count}/6)"
        elif bullish_count >= 4:
            rec = Recommendation.BUY
            confidence = 0.55
            evidence = f"Mild bullish alignment ({bullish_count}/6)"
        elif bearish_count >= 4:
            rec = Recommendation.SELL
            confidence = 0.55
            evidence = f"Mild bearish alignment ({bearish_count}/6)"
        elif momentum > 1.0:
            rec = Recommendation.BUY
            confidence = 0.50
            evidence = f"No clear alignment but upward momentum ({momentum:+.2f}%)"
        elif momentum < -1.0:
            rec = Recommendation.SELL
            confidence = 0.50
            evidence = f"No clear alignment but downward momentum ({momentum:+.2f}%)"
        else:
            rec = Recommendation.WATCH
            confidence = 0.40
            evidence = "No clear trend or momentum"

        evidence_str = (
            f"Price={price:.2f} EMA20={ema20:.2f} EMA50={ema50:.2f} "
            f"EMA200={ema200:.2f} alignment={bullish_count}/{bearish_count}(B/E). {evidence}"
        )

        return AgentOpinion(
            agent_name=self.name,
            agent_role=AgentRole.MARKET_ANALYST,
            confidence=round(confidence, 3),
            impact_score=0.5,
            risk_score=0.3,
            evidence=[evidence_str],
            recommendation=rec,
            rationale=f"Trend analysis for {symbol}: {evidence}",
            event_id=event.id,
            metadata={
                "symbol": symbol,
                "price": price,
                "ema20": round(ema20, 2),
                "ema50": round(ema50, 2),
                "trend_strength": round(trend_strength, 2),
                "bullish_count": bullish_count,
            },
        )

    def analyze_batch(self, events, ohlcv_cache):
        opinions = []
        for event in events:
            sym = event.assets[0].symbol
            op = self.analyze(event, ohlcv_cache.get(sym))
            if op:
                opinions.append(op)
                self.processed_count += 1
        return opinions
