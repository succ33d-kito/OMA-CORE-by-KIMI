"""KnifeDetector — Distinguishes dip buy opportunity from falling knife.

Analyzes bounce quality, volume profile, momentum, volatility expansion.
No LLM, no generative AI. Pure quantitative logic.
"""
from statistics import mean, stdev
from typing import List, Optional, Dict
from math import sqrt


class KnifeDetector:
    def __init__(self,
                 bounce_quality_window: int = 12,
                 min_bounce_recovery: float = 0.3,
                 volume_decline_threshold: float = 0.7):
        self.bounce_quality_window = bounce_quality_window
        self.min_bounce_recovery = min_bounce_recovery
        self.volume_decline_threshold = volume_decline_threshold
        self._recent_bounces: List[float] = []

    def analyze(self, closes: List[float], volumes: List[float], highs: List[float], lows: List[float]) -> Dict:
        """Analyze if current price action is a dip buy or falling knife.
        Returns dict with score (0=falling knife, 100=safe dip), evidence, recommendation.
        """
        evidence = []
        n = len(closes)
        if n < self.bounce_quality_window + 5:
            return {"score": 50, "verdict": "unknown", "evidence": ["Insufficient data"]}

        recent = closes[-self.bounce_quality_window:]
        recent_volumes = volumes[-self.bounce_quality_window:]
        recent_highs = highs[-self.bounce_quality_window:]
        recent_lows = lows[-self.bounce_quality_window:]

        current_price = closes[-1]
        low_5 = min(closes[-6:-1]) if len(closes) >= 6 else min(recent)
        high_5 = max(closes[-6:-1]) if len(closes) >= 6 else max(recent)

        # 1. Bounce quality: how much has price recovered from recent low?
        recent_low = min(recent_lows)
        recent_high = max(recent_highs)
        bounce_range = recent_high - recent_low
        bounce_recovery = (current_price - recent_low) / bounce_range if bounce_range > 0 else 0
        evidence.append(f"Bounce recovery: {bounce_recovery:.1%} of recent range")

        # 2. Volume profile: is volume declining (good) or accelerating (bad)?
        vol_first_half = mean(recent_volumes[:len(recent_volumes)//2]) if recent_volumes else 0
        vol_second_half = mean(recent_volumes[len(recent_volumes)//2:]) if len(recent_volumes) > 1 else 0
        vol_trend = vol_second_half / vol_first_half if vol_first_half > 0 else 1.0
        evidence.append(f"Volume trend (second/first half): {vol_trend:.2f}x")

        # 3. Momentum: is price recovering?
        if len(closes) >= 6:
            mom_3 = (closes[-1] - closes[-3]) / closes[-3] * 100
            mom_6 = (closes[-1] - closes[-6]) / closes[-6] * 100
        else:
            mom_3 = 0
            mom_6 = 0
        evidence.append(f"3-period momentum: {mom_3:+.2f}%, 6-period: {mom_6:+.2f}%")

        # 4. Volatility: expanding (panic) or contracting (bounce forming)?
        if len(closes) >= 14:
            recent_range = [abs(recent[i] - recent[i-1]) for i in range(1, len(recent))]
            vol = mean(recent_range) if recent_range else 0
            longer_range = [abs(closes[i] - closes[i-1]) for i in range(-14, -1)]
            baseline_vol = mean(longer_range) if longer_range else vol
            vol_ratio = vol / baseline_vol if baseline_vol > 0 else 1.0
        else:
            vol_ratio = 1.0
        evidence.append(f"Volatility ratio (recent/baseline): {vol_ratio:.2f}x")

        # 5. Volume confirmation: is volume declining as price recovers?
        price_up = current_price > closes[-3] if len(closes) >= 3 else True
        vol_down = recent_volumes[-1] < recent_volumes[0] if len(recent_volumes) >= 2 else True
        evidence.append(f"Price rising: {price_up}, Volume declining: {vol_down}")

        score = 50.0

        # Bounce quality scoring
        if bounce_recovery > self.min_bounce_recovery * 2:
            score += 15
            evidence.append("Strong bounce recovery — dip buy signal")
        elif bounce_recovery > self.min_bounce_recovery:
            score += 5
            evidence.append("Moderate bounce recovery")
        else:
            score -= 15
            evidence.append("Weak bounce — falling knife risk")

        # Volume trend scoring
        if vol_trend < self.volume_decline_threshold:
            score += 15
            evidence.append("Volume declining — panic easing")
        elif vol_trend < 1.0:
            score += 5
            evidence.append("Volume slightly declining")
        elif vol_trend < 1.2:
            evidence.append("Volume stable")
        else:
            score -= 10
            evidence.append("Volume accelerating — panic continuing")

        # Momentum scoring
        if mom_3 > 2.0 and mom_6 > 0:
            score += 10
            evidence.append("Positive momentum — recovery underway")
        elif mom_3 > 0 and mom_6 > -5:
            score += 5
            evidence.append("Momentum stabilizing")
        elif mom_3 > -0.3:
            evidence.append("Momentum neutral")
        else:
            score -= 15
            evidence.append("Negative momentum — falling knife")

        # Volatility scoring
        if vol_ratio < 0.8:
            score += 10
            evidence.append("Volatility contracting — bounce forming")
        elif vol_ratio > 1.5:
            score -= 10
            evidence.append("Volatility expanding — panic mode")

        # Volume-price divergence
        if price_up and vol_down:
            score += 5
            evidence.append("Bullish volume-price divergence")

        score = max(0, min(100, score))
        if score >= 65:
            verdict = "dip_buy"
        elif score >= 35:
            verdict = "uncertain"
        else:
            verdict = "falling_knife"

        return {
            "score": round(score, 1),
            "verdict": verdict,
            "bounce_recovery": round(bounce_recovery, 3),
            "volume_trend": round(vol_trend, 2),
            "momentum_3": round(mom_3, 2),
            "volatility_ratio": round(vol_ratio, 2),
            "evidence": evidence,
        }

    def is_safe_to_buy(self, closes: List[float], volumes: List[float],
                       highs: List[float], lows: List[float]) -> bool:
        analysis = self.analyze(closes, volumes, highs, lows)
        return analysis["score"] >= 35

    def position_size_multiplier(self, closes: List[float], volumes: List[float],
                                 highs: List[float], lows: List[float]) -> float:
        analysis = self.analyze(closes, volumes, highs, lows)
        score = analysis["score"]
        if score < 20:
            return 0.0
        if score < 35:
            return 0.25
        if score < 50:
            return 0.5
        if score < 65:
            return 0.75
        return 1.0
