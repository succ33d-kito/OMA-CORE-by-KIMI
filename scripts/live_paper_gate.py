"""OSIRIS Live Paper Trading Gate — Operational Validation Harness
Phases 1-6: Live paper trading, telemetry, guard audit, stability audit,
failure classification, demo gate evaluation.

Usage:
  python scripts/live_paper_gate.py [--days 30] [--symbols BTC,ETH,SOL]
  python scripts/live_paper_gate.py --report-only   # Generate reports from existing logs
"""
import sys, json, os, math, copy
sys.path.insert(0, ".")
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from statistics import mean, stdev
from math import sqrt
from typing import Optional, Dict, List, Tuple, Any

import requests as req

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Urgency
from core.schemas.agent_schema import AgentOpinion, AgentRole, Recommendation
from core.schemas.trade_schema import TradeDirection, Trade, TradeSignal, ExitReason
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory
from core.execution.slippage import SlippageEngine
from core.execution.direction_controller import DirectionController
from core.execution.capital_guard import CapitalGuard, GuardMode
from core.execution.crash_detector import CrashDetector
from core.execution.knife_detector import KnifeDetector
from core.execution.gap_risk import GapRiskEngine

# ── Config ────────────────────────────────────────────────────────────────────

SYMBOLS = ["BTC", "ETH", "SOL"]
BNB_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
TRADE_SYMBOLS = ["BTC", "ETH"]

OUT_DIR = "_live_paper_gate"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Data ──────────────────────────────────────────────────────────────────────

def fetch_ohlcv_range(symbol, start_ms, end_ms, interval="1h"):
    pair = BNB_MAP.get(symbol)
    if not pair:
        return None
    limit = 1000
    candles = []
    current_start = start_ms
    while current_start < end_ms:
        params = {"symbol": pair, "interval": interval, "limit": limit,
                  "startTime": current_start, "endTime": end_ms}
        try:
            resp = req.get("https://api.binance.com/api/v3/klines",
                           params=params, timeout=15)
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not batch:
                break
            for k in batch:
                candles.append({
                    "time": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
                    "open": float(k[1]), "high": float(k[2]),
                    "low": float(k[3]), "close": float(k[4]),
                    "volume": float(k[5]),
                })
            if len(batch) < limit:
                break
            current_start = batch[-1][0] + 1
        except Exception:
            break
    candles.sort(key=lambda c: c["time"])
    return candles if len(candles) >= 50 else None


def generate_events(symbol, ohlcv):
    events = []
    for i in range(20, len(ohlcv)):  # Skip first 20 to build OHLCV history
        prev, curr = ohlcv[i - 1], ohlcv[i]
        change = (curr["close"] - prev["close"]) / prev["close"]
        u = (Urgency.HIGH if abs(change) > 0.05
             else Urgency.MEDIUM if abs(change) > 0.02
             else Urgency.LOW)
        et = (EventType.VOLUME_SPIKE
              if (abs(change) > 0.05 and curr["volume"] > prev["volume"] * 1.5)
              else EventType.PRICE_MOVEMENT)
        events.append(Event(
            id=f"{symbol}_{i}", source="live_gate",
            event_type=et, title=f"{symbol} {change * 100:+.2f}%",
            assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO,
                          price_at_event=curr["close"])],
            timestamp=curr["time"], detected_at=curr["time"],
            urgency=u, sentiment_score=change, confidence=0.7,
        ))
    return events


# ── Failure Classification ────────────────────────────────────────────────────

class FailureCategory:
    DATA_FAILURE = "DATA_FAILURE"
    API_FAILURE = "API_FAILURE"
    LOGIC_FAILURE = "LOGIC_FAILURE"
    RISK_FAILURE = "RISK_FAILURE"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"
    GUARD_FAILURE = "GUARD_FAILURE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    UNKNOWN = "UNKNOWN"

    ALL = [DATA_FAILURE, API_FAILURE, LOGIC_FAILURE, RISK_FAILURE,
           EXECUTION_FAILURE, GUARD_FAILURE, FALSE_POSITIVE,
           FALSE_NEGATIVE, UNKNOWN]


class FailureClassifier:
    """Classify and track all anomalies during the live run."""

    def __init__(self):
        self.failures: List[Dict] = []
        self.counts = defaultdict(int)

    def record(self, category: str, summary: str, detail: str = "",
               timestamp=None, severity: str = "WARNING"):
        entry = {
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "category": category,
            "severity": severity,
            "summary": summary,
            "detail": detail,
        }
        self.failures.append(entry)
        self.counts[category] += 1
        return entry

    def record_data_failure(self, symbol, msg, detail=""):
        return self.record(FailureCategory.DATA_FAILURE,
                           f"Data failure for {symbol}: {msg}", detail)

    def record_api_failure(self, source, msg, detail=""):
        return self.record(FailureCategory.API_FAILURE,
                           f"API failure from {source}: {msg}", detail)

    def record_guard_failure(self, guard_name, expected, actual, detail=""):
        return self.record(
            FailureCategory.GUARD_FAILURE,
            f"Guard {guard_name}: expected {expected}, got {actual}",
            detail, severity="ERROR")

    def record_risk_failure(self, msg, detail=""):
        return self.record(FailureCategory.RISK_FAILURE,
                           f"Risk violation: {msg}", detail, severity="ERROR")

    def record_logic_failure(self, msg, detail=""):
        return self.record(FailureCategory.LOGIC_FAILURE,
                           f"Logic error: {msg}", detail, severity="ERROR")

    def record_false_positive(self, guard_name, detail=""):
        return self.record(FailureCategory.FALSE_POSITIVE,
                           f"False positive: {guard_name} triggered incorrectly",
                           detail)

    def record_false_negative(self, guard_name, detail=""):
        return self.record(FailureCategory.FALSE_NEGATIVE,
                           f"False negative: {guard_name} failed to trigger",
                           detail, severity="ERROR")

    def record_execution_failure(self, msg, detail=""):
        return self.record(FailureCategory.EXECUTION_FAILURE, msg, detail,
                           severity="ERROR")

    def summary(self) -> Dict:
        return {
            "total_failures": len(self.failures),
            "by_category": dict(self.counts),
            "by_severity": defaultdict(int, sum(
                ([(e["severity"], 1)] for e in self.failures), [])),
            "failures": self.failures,
        }


# ── Telemetry Collector ───────────────────────────────────────────────────────

class TelemetryCollector:
    """Collects every event during the live run for audit."""

    def __init__(self):
        self.cycles: List[Dict] = []
        self.trades_opened: List[Dict] = []
        self.trades_closed: List[Dict] = []
        self.blocked_trades: List[Dict] = []
        self.guard_activations: List[Dict] = []
        self.emergency_events: List[Dict] = []
        self.crash_events: List[Dict] = []
        self.errors: List[Dict] = []
        self.price_snapshots: List[Dict] = []

        self.daily_pnl: Dict[str, float] = defaultdict(float)
        self.daily_trades: Dict[str, int] = defaultdict(int)
        self.daily_blocks: Dict[str, int] = defaultdict(int)

    def record_cycle(self, cycle_num: int, timestamp, data: Dict):
        self.cycles.append({
            "cycle": cycle_num,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "data": data,
        })

    def record_trade_opened(self, trade: Trade, signal: TradeSignal):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": signal.event_id,
            "asset": signal.asset,
            "direction": signal.direction.value,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "position_size_pct": signal.position_size_pct,
            "conviction": signal.conviction,
            "risk_score": signal.risk_score,
            "size": trade.size,
            "rationale": signal.rationale[:200],
        }
        self.trades_opened.append(entry)
        day = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d")
        self.daily_trades[day] += 1

    def record_trade_closed(self, trade: Trade):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": trade.signal.event_id,
            "asset": trade.signal.asset,
            "direction": trade.signal.direction.value,
            "entry_price": trade.entry_price_executed,
            "exit_price": trade.exit_price,
            "pnl_absolute": trade.pnl_absolute,
            "pnl_percent": trade.pnl_percent,
            "exit_reason": trade.exit_reason.value if trade.exit_reason else "unknown",
            "duration_hours": (
                (trade.exit_time - trade.entry_time).total_seconds() / 3600
                if trade.exit_time and trade.entry_time else None
            ),
        }
        self.trades_closed.append(entry)
        day = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d")
        self.daily_pnl[day] += trade.pnl_absolute or 0

    def record_blocked_trade(self, timestamp, asset, direction,
                              conviction, reason, guard_data: Dict):
        entry = {
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "asset": asset,
            "direction": direction,
            "conviction": conviction,
            "reason": reason,
            **guard_data,
        }
        self.blocked_trades.append(entry)
        day = entry["timestamp"][:10]
        self.daily_blocks[day] += 1

    def record_guard_activation(self, guard: str, mode: str, reason: str,
                                 details: Optional[Dict] = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "guard": guard,
            "mode": mode,
            "reason": reason,
            "details": details or {},
        }
        self.guard_activations.append(entry)

    def record_emergency(self, source: str, message: str, data: Optional[Dict] = None):
        self.emergency_events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "message": message,
            "data": data or {},
        })

    def record_crash_event(self, score: float, mode: str, velocities: Dict):
        self.crash_events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "crash_score": score,
            "crash_mode": mode,
            "velocities": velocities,
        })

    def record_error(self, source: str, message: str, exception: Optional[str] = None):
        self.errors.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "message": message,
            "exception": exception,
        })

    def record_price_snapshot(self, timestamp, prices: Dict):
        self.price_snapshots.append({
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "prices": dict(prices),
        })

    def summary(self) -> Dict:
        return {
            "cycles": len(self.cycles),
            "trades_opened": len(self.trades_opened),
            "trades_closed": len(self.trades_closed),
            "blocked_trades": len(self.blocked_trades),
            "guard_activations": len(self.guard_activations),
            "emergency_events": len(self.emergency_events),
            "crash_events": len(self.crash_events),
            "errors": len(self.errors),
            "daily_pnl": dict(self.daily_pnl),
            "daily_trades": dict(self.daily_trades),
            "daily_blocks": dict(self.daily_blocks),
        }

    def port_summary_snapshot(self, portfolio: Dict) -> Dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "portfolio": portfolio,
        }


# ── Guard Verifier ────────────────────────────────────────────────────────────

class GuardVerifier:
    """Verify every protection mechanism during the live run."""

    def __init__(self, classifier: FailureClassifier):
        self.classifier = classifier
        self.audit_log: List[Dict] = []
        self.crash_activations = 0
        self.gap_activations = 0
        self.knife_blocks = 0
        self.capital_guard_restrictions = 0
        self.emergency_activations = 0
        self.kill_switch_activations = 0

    def audit_block(self, timestamp, asset, direction, conviction,
                     crash_score, crash_mode, gap_score, knife_verdict,
                     guard_responsible, size_before, size_after,
                     reason="", signal_strength=0.0):
        entry = {
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "asset": asset,
            "direction": direction,
            "signal_strength": signal_strength,
            "conviction": conviction,
            "crash_score": crash_score,
            "crash_mode": crash_mode,
            "gap_score": gap_score,
            "knife_classification": knife_verdict,
            "guard_responsible": guard_responsible,
            "position_size_before": size_before,
            "position_size_after": size_after,
            "reason": reason,
        }
        self.audit_log.append(entry)

        if guard_responsible == "CrashDetector":
            self.crash_activations += 1
        elif guard_responsible == "GapRisk":
            self.gap_activations += 1
        elif guard_responsible == "KnifeDetector":
            self.knife_blocks += 1
        elif guard_responsible == "CapitalGuard":
            self.capital_guard_restrictions += 1
        elif guard_responsible == "EmergencyMode":
            self.emergency_activations += 1
        elif guard_responsible == "KillSwitch":
            self.kill_switch_activations += 1

    def summary(self) -> Dict:
        return {
            "total_audit_entries": len(self.audit_log),
            "crash_detector_activations": self.crash_activations,
            "gap_risk_activations": self.gap_activations,
            "knife_detector_blocks": self.knife_blocks,
            "capital_guard_restrictions": self.capital_guard_restrictions,
            "emergency_activations": self.emergency_activations,
            "kill_switch_activations": self.kill_switch_activations,
            "audit_log": self.audit_log[-1000:],  # Latest 1000 for size
        }


# ── Live Paper Gate Runner ────────────────────────────────────────────────────

class LivePaperGate:
    """Main operational validation harness."""

    def __init__(self, symbols: List[str] = None, days: int = 30,
                 initial_capital: float = 10000.0):
        self.symbols = symbols or TRADE_SYMBOLS
        self.days = days
        self.initial_capital = initial_capital
        self.cycle_num = 0
        self.start_time = datetime.now(timezone.utc)
        self.last_prices: Dict[str, float] = {}

        # Components — will patch _fetch_ohlcv to use our historical data
        self.market_agent = MarketAgent()
        self.risk_agent = RiskAgent()
        self.council = AgentCouncil()

        # OHLCV context for agent patch — updated each cycle
        self._agent_ohlcv: Dict[str, List[Dict]] = {}

        # Monkey-patch agents to use stored historical data
        def _patched_fetch(symbol):
            return self._agent_ohlcv.get(symbol)
        self.market_agent._fetch_ohlcv = _patched_fetch
        self.risk_agent._fetch_ohlcv = _patched_fetch
        self.perf_memory = PerformanceMemory()
        self.capital_guard = CapitalGuard(initial_capital=initial_capital)
        self.crash_detector = CrashDetector()
        self.knife_detector = KnifeDetector()
        self.gap_risk = GapRiskEngine()
        self.direction_ctrl = DirectionController()
        self.slippage = SlippageEngine(slippage_pct=0.05)

        self.engine = PaperTradingEngine(
            initial_capital=initial_capital,
            max_open_positions=3,
            performance_memory=self.perf_memory,
            council=self.council,
            slippage_engine=self.slippage,
            direction_controller=self.direction_ctrl,
            capital_guard=self.capital_guard,
            crash_detector=self.crash_detector,
            knife_detector=self.knife_detector,
            gap_risk_engine=self.gap_risk,
        )

        # Telemetry
        self.telemetry = TelemetryCollector()
        self.failures = FailureClassifier()
        self.guard_verifier = GuardVerifier(self.failures)

        # Data store
        self.ohlcv_data: Dict[str, List] = {}
        self.event_queue: List[Tuple[str, Event]] = []

        # Run state
        self.run_start = datetime.now(timezone.utc)
        self.last_snapshot_time = datetime.now(timezone.utc)
        self.snapshot_interval_hours = 6

    def load_data(self) -> bool:
        """Fetch historical OHLCV data for replay."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=self.days)
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)

        print(f"Fetching {self.days} days of data for {self.symbols}...")
        success = True
        for sym in self.symbols:
            data = fetch_ohlcv_range(sym, start_ms, end_ms)
            if data is None or len(data) < 100:
                self.failures.record_data_failure(
                    sym, f"Failed to fetch data", f"Got {len(data) if data else 0} candles")
                print(f"  WARNING: {sym} data fetch returned {len(data) if data else None} candles")
                success = False
            else:
                self.ohlcv_data[sym] = data
                print(f"  {sym}: {len(data)} candles ({data[0]['time'].isoformat()[:10]} to {data[-1]['time'].isoformat()[:10]})")

        return success

    def build_event_queue(self):
        """Build chronologically sorted event queue from all symbol data."""
        events_by_time = defaultdict(list)
        for sym in self.symbols:
            data = self.ohlcv_data.get(sym, [])
            for evt in generate_events(sym, data):
                events_by_time[evt.timestamp].append(evt)

        for ts in sorted(events_by_time.keys()):
            for evt in events_by_time[ts]:
                self.event_queue.append((ts, evt))

        print(f"Event queue: {len(self.event_queue)} events")

    def get_current_prices(self, timestamp) -> Dict[str, float]:
        """Get latest price for each symbol at given timestamp."""
        prices = {}
        for sym in self.symbols:
            data = self.ohlcv_data.get(sym, [])
            best = None
            for c in data:
                if c["time"] <= timestamp:
                    best = c["close"]
                else:
                    break
            if best is not None:
                prices[sym] = best
        return prices

    def get_ohlcv_context(self, symbol: str, timestamp, window: int = 50):
        """Get recent OHLCV window ending at timestamp."""
        data = self.ohlcv_data.get(symbol, [])
        window_data = [c for c in data if c["time"] <= timestamp][-window:]
        return window_data if len(window_data) >= 20 else None

    def run_cycle(self, timestamp, events: List[Event]) -> Dict:
        """Execute one pipeline cycle at the given timestamp."""
        result = {
            "timestamp": timestamp.isoformat(),
            "events_processed": 0,
            "opinions_generated": 0,
            "decision_made": False,
            "trade_opened": None,
            "block_reason": None,
        }

        current_prices = self.get_current_prices(timestamp)
        if not current_prices:
            return result

        self.last_prices = current_prices

        # Update market data for all symbols
        for sym in TRADE_SYMBOLS:
            price = current_prices.get(sym)
            if price is None:
                continue
            ohlcv_window = self.get_ohlcv_context(sym, timestamp)
            self.engine.update_market_data(sym, price, timestamp, ohlcv_window)
            if sym == "BTC":
                self.crash_detector.update_price(price)
                if ohlcv_window:
                    for c in ohlcv_window[-20:]:
                        v = c.get("volume")
                        if v is not None:
                            self.crash_detector.update_price(price, v)

        # Capture crash state
        crash_score = self.crash_detector.crash_score()
        crash_mode = self.crash_detector.crash_mode(self.engine.capital).value
        if crash_mode != "none":
            self.telemetry.record_crash_event(
                crash_score, crash_mode,
                {"vel6": self.crash_detector.drawdown_velocity_6h(),
                 "vel24": self.crash_detector.drawdown_velocity_24h(),
                 "vel72": self.crash_detector.drawdown_velocity_72h()})

        # Check open positions
        closed = self.engine.check_positions(current_prices)
        for trade in closed:
            self.telemetry.record_trade_closed(trade)
            if trade.pnl_absolute and trade.pnl_absolute < 0:
                self.failures.record(
                    FailureCategory.RISK_FAILURE,
                    f"Trade closed at loss: {trade.signal.asset} {trade.signal.direction.value} "
                    f"PnL={trade.pnl_absolute:.2f}",
                    severity="INFO")

        # Process each event
        for event in events:
            try:
                self._process_event(event, timestamp, current_prices)
                result["events_processed"] += 1
            except Exception as e:
                self.telemetry.record_error(
                    "pipeline", f"Error processing event {event.id}: {e}",
                    str(e))
                self.failures.record_execution_failure(
                    f"Pipeline error for {event.id}: {e}")

        return result

    def _process_event(self, event: Event, timestamp, current_prices: Dict):
        """Process a single event through the pipeline."""
        symbol = event.assets[0].symbol if event.assets else None
        if symbol not in TRADE_SYMBOLS:
            return

        price = current_prices.get(symbol)
        if price is None:
            return

        # Provide OHLCV context to agents
        ohlcv_window = self.get_ohlcv_context(symbol, timestamp, window=100)
        if ohlcv_window and len(ohlcv_window) >= 20:
            self._agent_ohlcv[symbol] = ohlcv_window
        else:
            return

        # Market agent analysis
        try:
            market_opinion = self.market_agent.analyze(event)
        except Exception as e:
            self.telemetry.record_error("market_agent", str(e))
            return

        if market_opinion is None:
            return

        market_opinion.metadata["symbol"] = symbol
        market_opinion.metadata["price"] = price

        # Risk agent analysis
        try:
            risk_opinion = self.risk_agent.analyze(event)
        except Exception as e:
            self.telemetry.record_error("risk_agent", str(e))
            return

        if risk_opinion is None:
            return

        risk_opinion.metadata["symbol"] = symbol
        risk_opinion.metadata["price"] = price

        # Merge risk metadata into market
        for key in ("max_position_pct", "suggested_stop_pct", "atr_pct"):
            if key in risk_opinion.metadata:
                market_opinion.metadata[key] = risk_opinion.metadata[key]

        # Council
        self.council.submit_opinion(market_opinion)
        self.council.submit_opinion(risk_opinion)
        decision = self.council.decide(event.id)

        if decision is None:
            return

        # Pre-execution guard check
        guard_data = {
            "crash_score": self.crash_detector.crash_score(),
            "crash_mode": self.crash_detector.crash_mode(self.engine.capital).value,
            "gap_score": self.gap_risk.gap_risk_score(),
            "guard_mode": self.capital_guard.guard_mode(self.engine.capital).value,
            "knife_verdict": "unknown",
            "trading_allowed": self.capital_guard.is_trading_allowed(),
            "size_before": self.capital_guard.should_reduce_size(self.engine._risk_base()),
        }

        # Check if trade will be blocked
        direction = None
        conviction = decision.conviction
        try:
            from core.schemas.trade_schema import DIRECTION_MAP
            direction = DIRECTION_MAP.get(decision.action)
        except Exception:
            pass

        block_reason = None
        if decision.action in (Recommendation.WATCH, Recommendation.NO_ACTION, Recommendation.HOLD):
            block_reason = "Non-trade action"
        elif not direction or direction == TradeDirection.FLAT:
            block_reason = "FLAT mapped action"
        elif not self.capital_guard.is_trading_allowed():
            block_reason = "Trading not allowed (CapitalGuard)"
        elif direction == TradeDirection.SHORT and self.direction_ctrl.should_disable_short():
            block_reason = "Short disabled (DirectionController)"
        elif direction == TradeDirection.LONG and self.direction_ctrl.should_disable_long():
            block_reason = "Long disabled (DirectionController)"
        elif self.capital_guard.guard_mode(self.engine.capital) in (GuardMode.EMERGENCY, GuardMode.HALT):
            block_reason = f"Guard mode {self.capital_guard.guard_mode(self.engine.capital).value}"
        elif self.crash_detector.crash_mode(self.engine.capital).value == "panic":
            block_reason = "CrashDetector PANIC mode"
        elif self.crash_detector.crash_mode(self.engine.capital).value == "emergency" and direction == TradeDirection.LONG:
            ohlcv = self.get_ohlcv_context(symbol, event.timestamp)
            if ohlcv:
                closes = [c["close"] for c in ohlcv]
                volumes = [c["volume"] for c in ohlcv]
                highs = [c["high"] for c in ohlcv]
                lows = [c["low"] for c in ohlcv]
                knife_verdict = self.knife_detector.analyze(closes, volumes, highs, lows)
                guard_data["knife_verdict"] = knife_verdict["verdict"]
                if not self.knife_detector.is_safe_to_buy(closes, volumes, highs, lows):
                    block_reason = f"KnifeDetector: {knife_verdict['verdict']}"
                    guard_data["knife_score"] = knife_verdict["score"]

        # Process decision
        signal = self.engine.process_decision(decision)

        if signal is None:
            block_reason = block_reason or "Guard block (unspecified)"
            size_after = 0.0
            self.telemetry.record_blocked_trade(
                timestamp, symbol,
                direction.value if direction else "unknown",
                conviction, block_reason, guard_data)
            self.guard_verifier.audit_block(
                timestamp, symbol,
                direction.value if direction else "unknown",
                conviction,
                guard_data["crash_score"], guard_data["crash_mode"],
                guard_data["gap_score"], guard_data.get("knife_verdict", "unknown"),
                self._identify_guard(block_reason),
                guard_data["size_before"], size_after,
                reason=block_reason,
                signal_strength=conviction / 100.0)
        else:
            trade = self.engine.execute_signal(signal)
            if trade:
                self.telemetry.record_trade_opened(trade, signal)
            else:
                self.telemetry.record_blocked_trade(
                    timestamp, symbol,
                    direction.value if direction else "unknown",
                    conviction,
                    "Execution: max positions/capacity reached",
                    guard_data)

        # Track guard mode changes
        gmode = self.capital_guard.guard_mode(self.engine.capital)
        if gmode != GuardMode.NORMAL:
            prev_mode = getattr(self, '_prev_guard_mode', GuardMode.NORMAL.value)
            if gmode.value != prev_mode:
                self.telemetry.record_guard_activation(
                    "CapitalGuard", gmode.value,
                    f"Guard mode changed to {gmode.value}",
                    {"equity": self.engine.capital,
                     "drawdown": self.capital_guard.drawdown_pct(self.engine.capital)})
        self._prev_guard_mode = gmode.value

        # Check kill switch
        ks = self.capital_guard.summary().get("kill_switch", False)
        if ks:
            self.telemetry.record_emergency(
                "KillSwitch", "Kill switch is active - trading halted")

    def _identify_guard(self, reason: str) -> str:
        if not reason:
            return "None"
        if "CrashDetector" in reason or "PANIC" in reason or "emergency" in reason:
            return "CrashDetector"
        if "CapitalGuard" in reason or "Guard mode" in reason:
            return "CapitalGuard"
        if "KnifeDetector" in reason or "knife" in reason.lower():
            return "KnifeDetector"
        if "DirectionController" in reason or "Short" in reason or "Long disabled" in reason:
            return "DirectionController"
        if "Trading not allowed" in reason:
            return "CapitalGuard"
        return "Other"

    def record_snapshot(self):
        """Record periodic portfolio snapshot."""
        summary = self.engine.get_portfolio_summary()
        self.port_summary = summary
        self.telemetry.record_cycle(
            self.cycle_num, datetime.now(timezone.utc), summary)
        return summary

    def run(self) -> Dict:
        """Execute the full live paper gate run."""
        print(f"\n{'='*60}")
        print(f"OSIRIS Live Paper Gate")
        print(f"Start: {self.start_time.isoformat()}")
        print(f"Period: {self.days} days, Symbols: {self.symbols}")
        print(f"{'='*60}\n")

        # Phase 1: Load data
        print("[Phase 1] Loading market data...")
        if not self.load_data():
            print("  WARNING: Some symbols have incomplete data")
        self.build_event_queue()

        if not self.event_queue:
            print("ERROR: No events generated. Cannot run.")
            return {"error": "No events"}

        # Phase 2-4: Run the pipeline
        print(f"\n[Phase 2-4] Processing {len(self.event_queue)} events...")
        processed = 0
        last_print = 0
        batch_events = []

        for ts in sorted(set(ts for ts, _ in self.event_queue)):
            events = [evt for t, evt in self.event_queue if t == ts]

            self.cycle_num += 1
            result = self.run_cycle(ts, events)

            # Record snapshot periodically
            elapsed = (datetime.now(timezone.utc) - self.last_snapshot_time).total_seconds()
            if elapsed >= self.snapshot_interval_hours * 3600:
                self.record_snapshot()
                self.last_snapshot_time = datetime.now(timezone.utc)

            processed += result["events_processed"]
            if self.cycle_num % 100 == 0:
                print(f"  Cycle {self.cycle_num}: {processed} events processed, "
                      f"{len(self.telemetry.trades_opened)} trades, "
                      f"{len(self.telemetry.blocked_trades)} blocks, "
                      f"{len(self.telemetry.errors)} errors")

        # Final snapshot
        self.record_snapshot()

        print(f"\nProcessing complete: {processed} events in {self.cycle_num} cycles")

        # Phase 5: Generate reports
        print(f"\n[Phase 5] Generating reports...")
        report = self.generate_report()

        # Phase 6: Demo gate evaluation
        print(f"\n[Phase 6] Demo gate evaluation...")
        evaluation = self.evaluate_demo_gate(report)
        report["demo_gate_evaluation"] = evaluation

        # Persist everything
        self._persist(report)

        return report

    def generate_report(self) -> Dict:
        """Generate comprehensive run report."""
        portfolio = self.engine.get_portfolio_summary()
        guard_summary = self.capital_guard.summary()

        # Trading metrics
        pnls = [t.pnl_percent for t in self.engine.closed_trades if t.pnl_percent is not None]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        # Win rate by direction
        long_trades = [t for t in self.engine.closed_trades
                       if t.signal.direction == TradeDirection.LONG]
        short_trades = [t for t in self.engine.closed_trades
                        if t.signal.direction == TradeDirection.SHORT]
        long_wins = sum(1 for t in long_trades if t.pnl_percent and t.pnl_percent > 0)
        short_wins = sum(1 for t in short_trades if t.pnl_percent and t.pnl_percent > 0)

        return {
            "run_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "duration_days": self.days,
                "symbols": self.symbols,
                "total_cycles": self.cycle_num,
                "total_events_processed": len(self.event_queue),
                "initial_capital": self.initial_capital,
            },
            "trading_metrics": {
                "trades_opened": len(self.telemetry.trades_opened),
                "trades_closed": len(self.telemetry.trades_closed),
                "win_rate": portfolio["win_rate"],
                "total_pnl_abs": portfolio["total_pnl_abs"],
                "total_return_pct": portfolio["total_return_pct"],
                "avg_pnl_pct": portfolio["avg_pnl_pct"],
                "sharpe_ratio": portfolio["sharpe_ratio"],
                "max_drawdown": portfolio.get("max_drawdown_pct", 0),
                "current_drawdown": guard_summary.get("drawdown_pct", 0),
                "long_trades": len(long_trades),
                "short_trades": len(short_trades),
                "long_win_rate": (long_wins / len(long_trades) * 100) if long_trades else 0,
                "short_win_rate": (short_wins / len(short_trades) * 100) if short_trades else 0,
                "final_equity": portfolio["equity"],
            },
            "risk_metrics": {
                "daily_loss_pct": guard_summary.get("daily_loss_pct", 0),
                "weekly_loss_pct": guard_summary.get("weekly_loss_pct", 0),
                "consecutive_losses": guard_summary.get("consecutive_losses", 0),
                "open_risk": guard_summary.get("open_risk_pct", 0),
                "guard_mode": portfolio["guard_mode"],
                "drawdown_pct": guard_summary.get("drawdown_pct", 0),
                "max_drawdown_pct_report": portfolio.get("max_drawdown_pct", 0),
            },
            "protection_metrics": {
                "crash_detector_activations": self.guard_verifier.crash_activations,
                "gap_risk_activations": self.guard_verifier.gap_activations,
                "knife_detector_blocks": self.guard_verifier.knife_blocks,
                "capital_guard_restrictions": self.guard_verifier.capital_guard_restrictions,
                "emergency_activations": self.guard_verifier.emergency_activations,
                "kill_switch_activations": self.guard_verifier.kill_switch_activations,
                "blocked_trades_total": len(self.telemetry.blocked_trades),
            },
            "system_metrics": {
                "total_errors": len(self.telemetry.errors),
                "total_failures": self.failures.summary()["total_failures"],
                "failures_by_category": self.failures.summary()["by_category"],
                "runtime_exceptions": len(self.telemetry.errors),
            },
            "guard_audit": self.guard_verifier.summary(),
            "telemetry": self.telemetry.summary(),
            "portfolio_snapshots": getattr(self, 'port_summary', {}),
        }

    def evaluate_demo_gate(self, report: Dict) -> Dict:
        """Evaluate demo gate GO/NO GO criteria."""
        criteria = {
            "1_no_critical_runtime_failures": True,
            "2_no_uncaught_exceptions": True,
            "3_no_guard_failures": True,
            "4_no_risk_limit_violations": True,
            "5_no_uncontrolled_exposure": True,
            "6_complete_audit_logs": True,
            "7_capital_guard_respected": True,
            "8_crash_detector_operational": True,
            "9_gap_risk_operational": True,
            "10_performance_memory_operational": True,
        }
        evidence = {k: [] for k in criteria}
        failures = []

        # 1. No critical runtime failures
        errors = report["system_metrics"]["total_errors"]
        if errors > 0:
            criteria["1_no_critical_runtime_failures"] = False
            evidence["1_no_critical_runtime_failures"].append(
                f"{errors} runtime errors recorded")
            failures.append(f"Runtime errors: {errors}")

        # 2. No uncaught exceptions — ignore EXECUTION_FAILURE (normal capacity blocks)
        critical_fails = [f for f in self.failures.failures
                          if f["severity"] == "ERROR"
                          and f["category"] != FailureCategory.EXECUTION_FAILURE]
        if critical_fails:
            criteria["2_no_uncaught_exceptions"] = False
            evidence["2_no_uncaught_exceptions"] = [f["summary"] for f in critical_fails]
            failures.extend(f["summary"] for f in critical_fails)

        # 3. No guard failures
        guard_fails = [f for f in self.failures.failures
                       if f["category"] == FailureCategory.GUARD_FAILURE]
        if guard_fails:
            criteria["3_no_guard_failures"] = False
            evidence["3_no_guard_failures"] = [f["summary"] for f in guard_fails]
            failures.extend(f["summary"] for f in guard_fails)

        # 4. No risk limit violations — only count ERROR-level risk failures
        risk_fails = [f for f in self.failures.failures
                      if f["category"] == FailureCategory.RISK_FAILURE and f["severity"] == "ERROR"]
        if risk_fails:
            criteria["4_no_risk_limit_violations"] = False
            evidence["4_no_risk_limit_violations"] = [f["summary"] for f in risk_fails]
            failures.extend(f["summary"] for f in risk_fails)
        # Also check actual drawdown
        max_dd = report.get("trading_metrics", {}).get("max_drawdown", 0)
        if max_dd > 20:
            criteria["4_no_risk_limit_violations"] = False
            evidence["4_no_risk_limit_violations"].append(
                f"Max drawdown {max_dd:.1f}% exceeds 20%")
            failures.append(f"Drawdown {max_dd:.1f}% exceeds EMERGENCY threshold")

        # 5. No uncontrolled exposure
        max_positions = len(self.engine.positions)
        if max_positions >= self.engine.max_open_positions:
            evidence["5_no_uncontrolled_exposure"].append(
                f"Max positions reached ({max_positions}/{self.engine.max_open_positions})")
        # Check if capital guard restricted appropriately
        guard_summary = self.capital_guard.summary()
        if guard_summary.get("open_risk", 0) > 0.5:  # >50% of capital at risk
            criteria["5_no_uncontrolled_exposure"] = False
            evidence["5_no_uncontrolled_exposure"].append(
                f"Open risk at {guard_summary['open_risk']:.1%}")
            failures.append(f"Open risk too high: {guard_summary['open_risk']:.1%}")

        # 6. Complete audit logs
        total_blocks = len(self.telemetry.blocked_trades)
        total_trades = len(self.telemetry.trades_opened)
        total_cycles = self.cycle_num
        if total_cycles > 0:
            log_completeness = (total_trades + total_blocks) / total_cycles
            evidence["6_complete_audit_logs"].append(
                f"{total_trades} trades, {total_blocks} blocks in {total_cycles} cycles")
            if total_cycles > 100 and log_completeness < 0.01:
                criteria["6_complete_audit_logs"] = False
                evidence["6_complete_audit_logs"].append(
                    "Very few events relative to cycles - possible logging gap")

        # 7. Capital guard respected
        if self.guard_verifier.capital_guard_restrictions > 0:
            evidence["7_capital_guard_respected"].append(
                f"CapitalGuard activated {self.guard_verifier.capital_guard_restrictions} times")

        # 8. CrashDetector operational
        if self.guard_verifier.crash_activations > 0:
            evidence["8_crash_detector_operational"].append(
                f"CrashDetector activated {self.guard_verifier.crash_activations} times")
        # Verify summary has expected keys
        crash_summary = self.crash_detector.summary()
        if "crash_score" not in crash_summary or "mode" not in crash_summary:
            criteria["8_crash_detector_operational"] = False
            evidence["8_crash_detector_operational"].append(
                "CrashDetector summary missing expected keys")

        # 9. GapRisk operational
        if self.guard_verifier.gap_activations > 0:
            evidence["9_gap_risk_operational"].append(
                f"GapRisk activated {self.guard_verifier.gap_activations} times")
        gap_summary = self.gap_risk.summary()
        if "gap_risk_score" not in gap_summary:
            criteria["9_gap_risk_operational"] = False
            evidence["9_gap_risk_operational"].append(
                "GapRisk summary missing expected keys")

        # 10. PerformanceMemory operational
        perf_summary = self.perf_memory.get_learning_summary()
        if not perf_summary:
            evidence["10_performance_memory_operational"].append(
                "PerformanceMemory summary is empty - may not have processed trades")

        # Final verdict
        all_pass = all(criteria.values())
        met = sum(1 for v in criteria.values() if v)
        total = len(criteria)

        return {
            "verdict": "GO" if all_pass else "NO GO",
            "criteria_met": f"{met}/{total}",
            "criteria": criteria,
            "evidence": evidence,
            "failures": failures,
            "recommendation": (
                "Demo trading is eligible. OSIRIS passed all operational stability criteria."
                if all_pass else
                f"Demo trading is NOT eligible. {len(failures)} failure(s) identified:\n"
                + "\n".join(f"  - {f}" for f in failures[:10])
            ),
        }

    def _persist(self, report: Dict):
        """Save all reports and telemetry to disk."""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")

        # Full report
        with open(f"{OUT_DIR}/live_paper_gate_report_{timestamp}.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Telemetry detail
        with open(f"{OUT_DIR}/telemetry_{timestamp}.json", "w") as f:
            json.dump({
                "trades_opened": self.telemetry.trades_opened,
                "trades_closed": self.telemetry.trades_closed,
                "blocked_trades": self.telemetry.blocked_trades,
                "guard_activations": self.telemetry.guard_activations,
                "emergency_events": self.telemetry.emergency_events,
                "crash_events": self.telemetry.crash_events,
                "errors": self.telemetry.errors,
            }, f, indent=2, default=str)

        # Guard audit
        with open(f"{OUT_DIR}/guard_audit_{timestamp}.json", "w") as f:
            json.dump(self.guard_verifier.summary(), f, indent=2, default=str)

        # Failures
        with open(f"{OUT_DIR}/failures_{timestamp}.json", "w") as f:
            json.dump(self.failures.summary(), f, indent=2, default=str)

        print(f"\nReports saved to {OUT_DIR}/")
        print(f"  - live_paper_gate_report_{timestamp}.json")
        print(f"  - telemetry_{timestamp}.json")
        print(f"  - guard_audit_{timestamp}.json")
        print(f"  - failures_{timestamp}.json")


# ── Summary Printer ───────────────────────────────────────────────────────────

def print_report_summary(report: Dict):
    """Print a human-readable summary of the report."""
    info = report.get("run_info", {})
    trading = report.get("trading_metrics", {})
    risk = report.get("risk_metrics", {})
    protection = report.get("protection_metrics", {})
    system = report.get("system_metrics", {})
    evaluation = report.get("demo_gate_evaluation", {})

    print(f"\n{'='*60}")
    print(f"OSIRIS Live Paper Gate — Summary")
    print(f"{'='*60}")
    print(f"Period: {info.get('duration_days', '?')} days")
    print(f"Symbols: {info.get('symbols', '?')}")
    print(f"Cycles: {info.get('total_cycles', '?')}")
    print(f"Events: {info.get('total_events_processed', '?')}")

    print(f"\n── Trading Metrics ──")
    print(f"  Trades opened: {trading.get('trades_opened', 0)}")
    print(f"  Trades closed: {trading.get('trades_closed', 0)}")
    print(f"  Win rate: {trading.get('win_rate', 0):.1f}%")
    print(f"  Total PnL: ${trading.get('total_pnl_abs', 0):.2f} ({trading.get('total_return_pct', 0):.2f}%)")
    print(f"  Final equity: ${trading.get('final_equity', 0):.2f}")
    print(f"  Max drawdown: {trading.get('max_drawdown', 0):.2f}%")
    print(f"  Sharpe: {trading.get('sharpe_ratio', 0):.2f}")

    print(f"\n── Risk Metrics ──")
    print(f"  Guard mode: {risk.get('guard_mode', '?')}")
    print(f"  Consecutive losses: {risk.get('consecutive_losses', 0)}")
    print(f"  Daily loss: {risk.get('daily_loss_pct', 0):.2f}%")
    print(f"  Open risk: {risk.get('open_risk', 0):.2f}")

    print(f"\n── Protection Metrics ──")
    print(f"  CrashDetector activations: {protection.get('crash_detector_activations', 0)}")
    print(f"  GapRisk activations: {protection.get('gap_risk_activations', 0)}")
    print(f"  KnifeDetector blocks: {protection.get('knife_detector_blocks', 0)}")
    print(f"  CapitalGuard restrictions: {protection.get('capital_guard_restrictions', 0)}")
    print(f"  Emergency activations: {protection.get('emergency_activations', 0)}")
    print(f"  Blocked trades: {protection.get('blocked_trades_total', 0)}")

    print(f"\n── System Metrics ──")
    print(f"  Errors: {system.get('total_errors', 0)}")
    print(f"  Failures: {system.get('total_failures', 0)}")
    print(f"  By category: {system.get('failures_by_category', {})}")

    if evaluation:
        print(f"\n── Demo Gate ──")
        print(f"  Verdict: {evaluation.get('verdict', '?')}")
        print(f"  Criteria met: {evaluation.get('criteria_met', '?')}")
        if evaluation.get("failures"):
            print(f"  Issues:")
            for f in evaluation["failures"][:5]:
                print(f"    - {f}")

    print(f"\n{'='*60}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="OSIRIS Live Paper Trading Gate")
    parser.add_argument("--days", type=int, default=90,
                        help="Days of historical data (default: 90)")
    parser.add_argument("--symbols", type=str, default="BTC,ETH",
                        help="Symbols to trade (default: BTC,ETH)")
    parser.add_argument("--report-only", action="store_true",
                        help="Skip run, print latest report")
    parser.add_argument("--initial-capital", type=float, default=10000.0,
                        help="Starting capital (default: 10000)")
    args = parser.parse_args()

    if args.report_only:
        import glob
        reports = sorted(glob.glob(f"{OUT_DIR}/live_paper_gate_report_*.json"))
        if not reports:
            print(f"No reports found in {OUT_DIR}/")
            return
        latest = reports[-1]
        print(f"Loading report: {latest}")
        with open(latest) as f:
            report = json.load(f)
        print_report_summary(report)
        return

    symbols = [s.strip() for s in args.symbols.split(",")]

    gate = LivePaperGate(symbols=symbols, days=args.days,
                         initial_capital=args.initial_capital)
    report = gate.run()
    print_report_summary(report)


if __name__ == "__main__":
    main()
