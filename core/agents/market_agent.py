"""OSIRIS Market Agent — Price action, momentum, volatility, trend analysis"""
from typing import List, Optional, Dict, Any
from statistics import mean, stdev
from math import sqrt
from core.schemas.agent_schema import (
    AgentOpinion, AgentRole, Recommendation
)
from core.schemas.event_schema import Event, EventType
from core.event_bus import EventBus, EventTopic, bus as default_bus


class MarketAgent:
    def __init__(
        self,
        name: str = "market_agent",
        event_bus: Optional[EventBus] = None,
        signal_mode: str = "both",
        short_style: str = "mom_break",
    ):
        self.name = name
        self.bus = event_bus or default_bus
        self.processed_count = 0
        self.signal_mode = signal_mode
        self.short_style = short_style
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
        price = asset.price_at_event or 0

        ohlcv = self._fetch_ohlcv(symbol)
        if not ohlcv or len(ohlcv) < 20:
            return None

        closes = [c["close"] for c in ohlcv]
        highs = [c["high"] for c in ohlcv]
        lows = [c["low"] for c in ohlcv]
        volumes = [c["volume"] for c in ohlcv]
        current_price = closes[-1]

        sma_20 = mean(closes[-20:])
        sma_50 = mean(closes[-50:]) if len(closes) >= 50 else sma_20

        rsi = self._calculate_rsi(closes, 14)
        atr = self._calculate_atr(highs, lows, closes, 14)

        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = stdev(returns) * sqrt(24) if len(returns) > 1 else 0.1

        volume_sma = mean(volumes[-20:])
        volume_ratio = volumes[-1] / volume_sma if volume_sma > 0 else 1.0

        trend = "uptrend" if sma_20 > sma_50 else "downtrend" if sma_20 < sma_50 else "neutral"

        momentum = (closes[-1] - closes[-10]) / closes[-10] * 100 if len(closes) >= 10 else 0
        short_momentum = (closes[-1] - closes[-3]) / closes[-3] * 100 if len(closes) >= 3 else 0

        evidence.append(f"Asset: {symbol} @ ${current_price:.4f}")
        evidence.append(f"Trend: SMA20={sma_20:.4f} / SMA50={sma_50:.4f} ({trend})")
        evidence.append(f"Momentum: {momentum:+.2f}% (short: {short_momentum:+.2f}%)")
        evidence.append(f"RSI(14): {rsi:.1f}")
        evidence.append(f"ATR(14): {atr:.4f} ({atr/current_price*100:.2f}% of price)")
        evidence.append(f"Volatility (24h): {volatility*100:.2f}%")
        evidence.append(f"Volume ratio: {volume_ratio:.2f}x avg")

        event_price_change = abs(event.sentiment_score) if event.sentiment_score else 0

        impact_score = 0.4
        risk_score = 0.3
        n = len(closes)

        rsi_extreme = abs(rsi - 50) / 50
        trend_strength = abs(sma_20 / sma_50 - 1) * 100 if sma_50 > 0 else 0
        momentum_strength = abs(momentum)
        vol_regime = "calm" if volatility < 0.02 else "normal" if volatility < 0.05 else "high"

        base_recommendation = Recommendation.WATCH

        if trend == "uptrend" and momentum > 0 and rsi < 70:
            base_recommendation = Recommendation.BUY
            impact_score = 0.6 + trend_strength * 2
            evidence.append("Bullish structure: uptrend with room to run")
        elif trend == "downtrend" and momentum < 0 and rsi > 30:
            base_recommendation = Recommendation.SELL
            impact_score = 0.6 + trend_strength * 2
            evidence.append("Bearish structure: downtrend with room to fall")
        elif rsi > 70 and self.short_style in ("rsi", "combined"):
            base_recommendation = Recommendation.SELL
            impact_score = 0.5 + (rsi - 70) / 60
            risk_score = 0.5 if rsi > 75 else 0.4
            evidence.append(f"RSI overbought ({rsi:.1f}) — potential reversal")
        elif len(closes) >= 6 and closes[-1] < min(closes[-6:-1]) and self.short_style in ("mom_break", "combined"):
            base_recommendation = Recommendation.SELL
            impact_score = 0.5 + trend_strength * 2
            risk_score = 0.4
            evidence.append(f"Momentum breakdown — price below 5-period low ({min(closes[-6:-1]):.4f})")
        elif rsi < 30:
            base_recommendation = Recommendation.BUY
            impact_score = 0.5 + (30 - rsi) / 60
            risk_score = 0.5 if rsi < 25 else 0.4
            evidence.append(f"RSI oversold ({rsi:.1f}) — potential bounce")
        elif volatility > 0.05:
            base_recommendation = Recommendation.HEDGE
            risk_score = 0.7
            evidence.append(f"High volatility ({volatility*100:.1f}%) — reduce exposure")
        elif momentum_strength > 1.0:
            if momentum > 0:
                base_recommendation = Recommendation.BUY
                evidence.append(f"Momentum positive ({momentum:+.2f}%) — follow trend")
            else:
                base_recommendation = Recommendation.SELL
                evidence.append(f"Momentum negative ({momentum:+.2f}%) — follow trend")
        else:
            evidence.append("No clear directional signal")

        if self.signal_mode == "short_only" and base_recommendation == Recommendation.BUY:
            base_recommendation = Recommendation.WATCH
            evidence.append("Signal mode: short_only — suppressing BUY")
        elif self.signal_mode == "long_only" and base_recommendation == Recommendation.SELL:
            base_recommendation = Recommendation.WATCH
            evidence.append("Signal mode: long_only — suppressing SELL")

        position_size_factor = 1.0
        if atr / current_price > 0.03:
            risk_score = min(1.0, risk_score + 0.15)
            evidence.append(f"Wide ATR ({atr/current_price*100:.1f}%) — tight stops advised")
            position_size_factor = 0.5

        if volume_ratio > 2.0:
            evidence.append(f"Volume spike ({volume_ratio:.1f}x) — confirms signal")
        elif volume_ratio < 0.5:
            evidence.append(f"Low volume ({volume_ratio:.1f}x) — weak signal")

        confidence = 0.45
        if base_recommendation in (Recommendation.BUY, Recommendation.SELL):
            confidence += rsi_extreme * 0.15
            confidence += min(trend_strength / 5, 0.1)
            if momentum_strength > 0.5:
                confidence += 0.05
            if vol_regime == "calm":
                confidence += 0.05
            confidence = min(0.85, confidence)
        elif base_recommendation == Recommendation.HEDGE:
            confidence = 0.65

        confidence = min(1.0, confidence + event.confidence * 0.05)

        metadata = {
            "symbol": symbol,
            "price": current_price,
            "sma_20": round(sma_20, 4),
            "sma_50": round(sma_50, 4),
            "trend": trend,
            "rsi_14": round(rsi, 1),
            "atr_14": round(atr, 4),
            "volatility_24h": round(volatility * 100, 2),
            "momentum_10d": round(momentum, 2),
            "volume_ratio": round(volume_ratio, 2),
            "position_size_factor": position_size_factor,
            "event_price_change_pct": round(event_price_change * 100, 2),
        }

        return AgentOpinion(
            agent_name=self.name,
            agent_role=AgentRole.MARKET_ANALYST,
            confidence=round(confidence, 3),
            impact_score=round(impact_score, 3),
            risk_score=round(risk_score, 3),
            evidence=evidence,
            recommendation=base_recommendation,
            rationale=f"Market analysis for {symbol}: {trend}, RSI={rsi:.1f}, "
                      f"volatility={volatility*100:.1f}%. "
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
                url = f"https://api.binance.com/api/v3/klines"
                params = {"symbol": pair, "interval": "1h", "limit": 100}
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "time": k[0],
                            "open": float(k[1]),
                            "high": float(k[2]),
                            "low": float(k[3]),
                            "close": float(k[4]),
                            "volume": float(k[5]),
                        }
                        for k in data
                    ]
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d", interval="1h")
            if not hist.empty:
                return [
                    {
                        "time": int(idx.timestamp() * 1000),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": float(row["Volume"]),
                    }
                    for idx, row in hist.iterrows()
                ]
        except Exception as e:
            pass
        return None

    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(len(closes) - period, len(closes)):
            change = closes[i] - closes[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        avg_gain = mean(gains)
        avg_loss = mean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100.0 - (100.0 / (1.0 + rs)), 1)

    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(highs) < period + 1:
            return 0.0
        trs = []
        for i in range(-period, 0):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1]),
            )
            trs.append(tr)
        return mean(trs)
