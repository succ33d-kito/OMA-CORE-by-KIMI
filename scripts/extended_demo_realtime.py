"""OSIRIS Extended Demo — Real-Time Continuous Validation Harness

Runs OSIRIS continuously in real-time paper/demo mode with full telemetry,
guard audit, and failure classification.

Usage:
  python scripts/extended_demo_realtime.py --smoke          # 7-day smoke test
  python scripts/extended_demo_realtime.py --run            # 30-day validation
  python scripts/extended_demo_realtime.py --extended       # 60-90 day extended
  python scripts/extended_demo_realtime.py --interval 3600  # Custom interval (seconds)
  python scripts/extended_demo_realtime.py --resume         # Resume from saved state
"""
import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, ".")

import requests as req

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Urgency
from core.schemas.agent_schema import AgentOpinion, Recommendation
from core.schemas.trade_schema import TradeDirection, TradeSignal, DIRECTION_MAP
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
from core.monitoring.health import HealthMonitor, HealthStatus
from core.monitoring.telemetry import TelemetryRecorder, GuardAuditRecorder, ExecutionAuditRecorder
from core.monitoring.failure_classifier import FailureClassifier, FailureCategory, FailureSeverity

OUT_DIR = "_extended_demo"
STATE_FILE = os.path.join(OUT_DIR, "run_state.json")
SYMBOLS = ["BTC", "ETH", "SOL"]
TRADE_SYMBOLS = ["BTC", "ETH"]
BNB_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}

INTERVAL_SMOKE = 15 * 60       # 15 min for smoke (quick cycles)
INTERVAL_RUN = 60 * 60         # 1 hour for validation
INTERVAL_EXTENDED = 60 * 60    # 1 hour for extended

DURATION_SMOKE = 7             # days
DURATION_RUN = 30              # days
DURATION_EXTENDED = 90         # days


class DemoHarness:
    """Continuous real-time demo harness with telemetry and monitoring."""

    def __init__(
        self,
        symbols: list[str] = None,
        interval_seconds: int = 3600,
        duration_days: int = 30,
        initial_capital: float = 10000.0,
        resume: bool = False,
    ):
        self.symbols = symbols or TRADE_SYMBOLS
        self.interval = interval_seconds
        self.duration = timedelta(days=duration_days)
        self.initial_capital = initial_capital
        self.resume_mode = resume

        # Pipeline components
        self.market_agent = MarketAgent()
        self.risk_agent = RiskAgent()
        self.council = AgentCouncil()
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

        # Monitoring
        self.health = HealthMonitor()
        self.telemetry = TelemetryRecorder(OUT_DIR)
        self.guard_audit = GuardAuditRecorder(OUT_DIR)
        self.execution_audit = ExecutionAuditRecorder(OUT_DIR)
        self.failures = FailureClassifier(OUT_DIR)

        # State
        self._agent_ohlcv: dict[str, list[dict]] = {}
        self._last_prices: dict[str, float] = {}
        self._start_time: Optional[datetime] = None
        self._cycle_id = 0
        self._events_processed = 0
        self._signals_generated = 0
        self._trades_opened_total = 0
        self._trades_closed_total = 0
        self._runtime_errors = 0
        self._data_failures = 0
        self._guard_blocks = 0
        self._execution_blocks = 0
        self._shutdown_requested = False
        self._last_daily_summary: Optional[str] = None
        self._last_weekly_summary: Optional[str] = None

        # Patch agents to use our OHLCV context
        def _patched_fetch(symbol: str):
            return self._agent_ohlcv.get(symbol)
        self.market_agent._fetch_ohlcv = _patched_fetch
        self.risk_agent._fetch_ohlcv = _patched_fetch

        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self._shutdown_requested = True
        print(f"\n[SHUTDOWN] Signal {signum} received. Completing current cycle...")

    def _load_state(self) -> bool:
        if not self.resume_mode:
            return False
        if not os.path.exists(STATE_FILE):
            print("[RESUME] No saved state found. Starting fresh.")
            return False
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
            self._cycle_id = state.get("cycle_id", 0)
            self._events_processed = state.get("events_processed", 0)
            self._signals_generated = state.get("signals_generated", 0)
            self._trades_opened_total = state.get("trades_opened_total", 0)
            self._trades_closed_total = state.get("trades_closed_total", 0)
            self._runtime_errors = state.get("runtime_errors", 0)
            self._data_failures = state.get("data_failures", 0)
            self._guard_blocks = state.get("guard_blocks", 0)
            self._execution_blocks = state.get("execution_blocks", 0)
            restart = state.get("start_time")
            if restart:
                elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(restart)
                print(f"[RESUME] Restored state. Previously ran {elapsed.days}d {elapsed.seconds//3600}h")
            print(f"[RESUME] Cycle {self._cycle_id}, {self._events_processed} events, "
                  f"{self._trades_opened_total} trades")
            return True
        except Exception as e:
            print(f"[RESUME] Failed to load state: {e}. Starting fresh.")
            return False

    def _save_state(self):
        state = {
            "cycle_id": self._cycle_id,
            "events_processed": self._events_processed,
            "signals_generated": self._signals_generated,
            "trades_opened_total": self._trades_opened_total,
            "trades_closed_total": self._trades_closed_total,
            "runtime_errors": self._runtime_errors,
            "data_failures": self._data_failures,
            "guard_blocks": self._guard_blocks,
            "execution_blocks": self._execution_blocks,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

    # ── Data Layer ────────────────────────────────────────────────────────

    def _fetch_ohlcv(self, symbol: str, days: int = 5) -> Optional[list[dict]]:
        pair = BNB_MAP.get(symbol)
        if not pair:
            return None
        end = int(datetime.now(timezone.utc).timestamp() * 1000)
        start = end - days * 24 * 3600 * 1000
        try:
            params = {"symbol": pair, "interval": "1h", "limit": days * 24,
                      "startTime": start, "endTime": end}
            resp = req.get("https://api.binance.com/api/v3/klines",
                           params=params, timeout=15)
            if resp.status_code != 200:
                return None
            candles = []
            for k in resp.json():
                candles.append({
                    "time": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
                    "open": float(k[1]), "high": float(k[2]),
                    "low": float(k[3]), "close": float(k[4]),
                    "volume": float(k[5]),
                })
            return candles if len(candles) >= 50 else None
        except Exception as e:
            self.failures.record(
                e, cycle_id=self._cycle_id,
                recovery_action="skip_cycle", resolved=False,
                impact="ohlcv_data_unavailable")
            return None

    def _refresh_market_data(self):
        self._agent_ohlcv = {}
        for sym in self.symbols:
            data = self._fetch_ohlcv(sym)
            if data:
                self._agent_ohlcv[sym] = data
                self._last_prices[sym] = data[-1]["close"]
            else:
                self._data_failures += 1

    def _generate_events(self) -> list[Event]:
        events = []
        for sym in self.symbols:
            data = self._agent_ohlcv.get(sym)
            if not data or len(data) < 20:
                continue
            curr = data[-1]
            prev = data[-2]
            change = (curr["close"] - prev["close"]) / prev["close"]
            u = (Urgency.HIGH if abs(change) > 0.05
                 else Urgency.MEDIUM if abs(change) > 0.02
                 else Urgency.LOW)
            et = (EventType.VOLUME_SPIKE
                  if abs(change) > 0.05 and data[-1]["volume"] > data[-2]["volume"] * 1.5
                  else EventType.PRICE_MOVEMENT)
            events.append(Event(
                id=f"{sym}_{self._cycle_id}",
                source="extended_demo",
                event_type=et,
                title=f"{sym} {change * 100:+.2f}%",
                assets=[Asset(
                    symbol=sym, name=sym, asset_class=AssetClass.CRYPTO,
                    price_at_event=curr["close"],
                )],
                timestamp=curr["time"],
                detected_at=datetime.now(timezone.utc),
                urgency=u,
                sentiment_score=change,
                confidence=0.7,
            ))
        return events

    # ── Pipeline ──────────────────────────────────────────────────────────

    def _run_pipeline(self, events: list[Event]) -> dict[str, Any]:
        result = {
            "events_collected": len(events),
            "events_processed": 0,
            "signals_generated": 0,
            "trades_opened": 0,
            "trades_closed": 0,
            "guard_blocks": 0,
            "execution_blocks": 0,
            "runtime_errors": 0,
        }

        if not events:
            return result

        # Check positions first
        closed = self.engine.check_positions(self._last_prices)
        for trade in closed:
            self._trades_closed_total += 1
            result["trades_closed"] += 1

        # Process each event
        for event in events:
            try:
                self._process_event(event, result)
                result["events_processed"] += 1
                self._events_processed += 1
            except Exception as e:
                self._runtime_errors += 1
                result["runtime_errors"] += 1
                self.failures.record(
                    e, cycle_id=self._cycle_id,
                    recovery_action="skip_event", resolved=False,
                    impact=f"event_processing_failed:{event.id}")

        return result

    def _process_event(self, event: Event, result: dict[str, Any]):
        symbol = event.assets[0].symbol if event.assets else None
        if symbol not in TRADE_SYMBOLS:
            return

        price = self._last_prices.get(symbol)
        if price is None:
            return

        # Market agent
        market_opinion = self.market_agent.analyze(event)
        if market_opinion is None:
            return
        market_opinion.metadata["symbol"] = symbol
        market_opinion.metadata["price"] = price

        # Risk agent
        risk_opinion = self.risk_agent.analyze(event)
        if risk_opinion is None:
            return
        risk_opinion.metadata["symbol"] = symbol
        risk_opinion.metadata["price"] = price

        # Merge risk metadata
        for key in ("max_position_pct", "suggested_stop_pct", "atr_pct"):
            if key in risk_opinion.metadata:
                market_opinion.metadata[key] = risk_opinion.metadata[key]

        # Council
        self.council.submit_opinion(market_opinion)
        self.council.submit_opinion(risk_opinion)
        decision = self.council.decide(event.id)
        if decision is None:
            return

        # Create trade signal
        signal = self.engine.process_decision(decision)
        if signal is None:
            self._guard_blocks += 1
            result["guard_blocks"] += 1
            self._record_guard_block(event, decision)
            return

        self._signals_generated += 1
        result["signals_generated"] += 1

        # Execute
        trade = self.engine.execute_signal(signal)
        if trade:
            self._trades_opened_total += 1
            result["trades_opened"] += 1
        else:
            self._execution_blocks += 1
            result["execution_blocks"] += 1
            self._record_execution_block(event, decision, signal)

    def _record_guard_block(self, event: Event, decision):
        symbol = event.assets[0].symbol if event.assets else "unknown"
        direction = None
        try:
            direction = DIRECTION_MAP.get(decision.action).value if decision.action in DIRECTION_MAP else "unknown"
        except Exception:
            direction = "unknown"

        block_reason = "unknown"
        if not self.capital_guard.is_trading_allowed():
            block_reason = "trading_not_allowed"
        elif self.direction_ctrl.should_disable_short() and direction == "SHORT":
            block_reason = "short_disabled"
        elif self.direction_ctrl.should_disable_long() and direction == "LONG":
            block_reason = "long_disabled"
        else:
            guard_mode = self.capital_guard.guard_mode(self.engine.capital)
            if guard_mode in (GuardMode.EMERGENCY, GuardMode.HALT):
                block_reason = f"guard_mode_{guard_mode.value}"
            crash_mode = self.crash_detector.crash_mode(self.engine.capital)
            if crash_mode.value in ("panic", "emergency"):
                block_reason = f"crash_mode_{crash_mode.value}"

        # Record in guard audit
        self.guard_audit.record({
            "timestamp": event.timestamp.isoformat(),
            "cycle_id": self._cycle_id,
            "asset": symbol,
            "direction": direction,
            "signal_type": decision.action.value if decision.action else "unknown",
            "conviction": decision.conviction,
            "risk_score": getattr(decision.metadata, "weighted_risk", None) if hasattr(decision, "metadata") else None,
            "original_size": None,
            "adjusted_size": 0,
            "block_reason": block_reason,
            "guard_source": self._identify_guard_source(block_reason),
            "capital_guard_mode": self.capital_guard.guard_mode(self.engine.capital).value,
            "crash_score": self.crash_detector.crash_score(),
            "gap_risk_score": self.gap_risk.gap_risk_score(),
            "knife_classification": None,
            "direction_controller_decision": direction,
        })

    def _record_execution_block(self, event: Event, decision, signal):
        """Record an execution block (execute_signal returned None) to audit."""
        symbol = event.assets[0].symbol if event.assets else "unknown"
        direction = None
        try:
            direction = DIRECTION_MAP.get(decision.action).value if decision.action in DIRECTION_MAP else "unknown"
        except Exception:
            direction = "unknown"

        portfolio = self.engine.get_portfolio_summary()
        guard_mode = self.capital_guard.guard_mode(self.engine.capital)
        crash_mode = self.crash_detector.crash_mode(self.engine.capital)

        self.execution_audit.record({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_id": self._cycle_id,
            "asset": symbol,
            "direction": direction,
            "signal_type": decision.action.value if decision.action else "unknown",
            "conviction": decision.conviction,
            "risk_score": signal.risk_score if signal else None,
            "block_reason": "execution_capacity_limit",
            "execution_source": "PaperTradingEngine.execute_signal",
            "open_positions": len(self.engine.positions),
            "current_exposure": portfolio.get("exposure", None),
            "capital_guard_mode": guard_mode.value,
            "crash_mode": crash_mode.value,
            "gap_risk_score": self.gap_risk.gap_risk_score(),
            "direction_controller_state": self.direction_ctrl.summary(),
        })

    @staticmethod
    def _identify_guard_source(reason: str) -> str:
        if "crash" in reason: return "CrashDetector"
        if "guard_mode" in reason: return "CapitalGuard"
        if "knife" in reason.lower(): return "KnifeDetector"
        if "short_disabled" in reason or "long_disabled" in reason: return "DirectionController"
        if "trading_not_allowed" in reason: return "CapitalGuard"
        return "Unknown"

    # ── Telemetry ─────────────────────────────────────────────────────────

    def _record_telemetry(self, pipeline_result: dict[str, Any]):
        guard_mode = self.capital_guard.guard_mode(self.engine.capital)
        crash_mode = self.crash_detector.crash_mode(self.engine.capital)
        portfolio = self.engine.get_portfolio_summary()

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_id": self._cycle_id,
            "events_collected": pipeline_result["events_collected"],
            "events_processed": pipeline_result["events_processed"],
            "signals_generated": pipeline_result["signals_generated"],
            "trades_opened": pipeline_result["trades_opened"],
            "trades_closed": pipeline_result["trades_closed"],
            "open_positions": len(self.engine.positions),
            "current_equity": portfolio.get("equity", self.initial_capital),
            "daily_pnl": pipeline_result.get("daily_pnl", 0),
            "weekly_pnl": pipeline_result.get("weekly_pnl", 0),
            "max_drawdown": portfolio.get("max_drawdown_pct", 0),
            "capital_guard_mode": guard_mode.value,
            "crash_mode": crash_mode.value,
            "gap_risk_score": self.gap_risk.gap_risk_score(),
            "direction_controller_state": self.direction_ctrl.summary(),
            "runtime_errors": pipeline_result["runtime_errors"],
            "data_failures": self._data_failures,
            "guard_blocks": pipeline_result["guard_blocks"],
            "execution_blocks": pipeline_result["execution_blocks"],
            # Cumulative counters for cross-reference
            "cumulative_signals": self._signals_generated,
            "cumulative_trades_opened": self._trades_opened_total,
            "cumulative_trades_closed": self._trades_closed_total,
            "cumulative_guard_blocks": self._guard_blocks,
            "cumulative_execution_blocks": self._execution_blocks,
            "cumulative_errors": self._runtime_errors,
        }
        self.telemetry.record(record)

    # ── Health Check ──────────────────────────────────────────────────────

    def _run_health_check(self) -> HealthStatus:
        portfolio = self.engine.get_portfolio_summary()
        equity = portfolio.get("equity", self.initial_capital)
        guard_mode = self.capital_guard.guard_mode(self.engine.capital)
        crash_mode = self.crash_detector.crash_mode(self.engine.capital)
        recent = self.telemetry.read_recent(10)

        results = self.health.run_all(
            equity=equity,
            initial_capital=self.initial_capital,
            guard_mode=guard_mode,
            crash_mode=crash_mode,
            open_trades=list(self.engine.positions),
            all_trades=list(self.engine.closed_trades),
            engine=self.engine,
            symbols=self.symbols,
            recent_telemetry=recent,
        )

        status = self.health.overall_status(results)
        if status == HealthStatus.CRITICAL:
            print(f"[HEALTH] CRITICAL — {[r.message for r in results if r.status == HealthStatus.CRITICAL]}")

        return status

    # ── Summaries ─────────────────────────────────────────────────────────

    def _daily_summary(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._last_daily_summary == today:
            return
        self._last_daily_summary = today

        portfolio = self.engine.get_portfolio_summary()
        fail_summary = self.failures.summary()
        tel_summary = self.telemetry.summary()

        print(f"\n{'='*60}")
        print(f"  END OF DAY {today}")
        print(f"{'='*60}")
        print(f"  Cycles: {self._cycle_id}")
        print(f"  Events processed: {self._events_processed}")
        print(f"  Signals generated: {self._signals_generated}")
        print(f"  Trades opened: {self._trades_opened_total}")
        print(f"  Trades closed: {self._trades_closed_total}")
        print(f"  Open positions: {len(self.engine.positions)}")
        print(f"  Equity: ${portfolio.get('equity', 0):.2f}")
        print(f"  Max DD: {portfolio.get('max_drawdown_pct', 0):.2f}%")
        print(f"  Guard blocks: {self._guard_blocks}")
        print(f"  Runtime errors: {self._runtime_errors}")
        print(f"  Failures: {fail_summary.get('total_failures', 0)}")
        print(f"{'='*60}\n")

    def _weekly_summary(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        week_num = datetime.now(timezone.utc).isocalendar()[1]
        key = f"{today[:7]}-W{week_num}"
        if self._last_weekly_summary == key:
            return
        self._last_weekly_summary = key

        portfolio = self.engine.get_portfolio_summary()
        fail_summary = self.failures.summary()

        print(f"\n{'#'*60}")
        print(f"  END OF WEEK {week_num}")
        print(f"{'#'*60}")
        print(f"  Cumulative cycles: {self._cycle_id}")
        print(f"  Total trades: {self._trades_opened_total}")
        print(f"  Total closed: {self._trades_closed_total}")
        print(f"  Current equity: ${portfolio.get('equity', 0):.2f}")
        print(f"  Total return: {portfolio.get('total_return_pct', 0):.2f}%")
        print(f"  Win rate: {portfolio.get('win_rate', 0):.1f}%")
        print(f"  Max DD: {portfolio.get('max_drawdown_pct', 0):.2f}%")
        print(f"  Sharpe: {portfolio.get('sharpe_ratio', 0):.2f}")
        print(f"  Guard blocks: {self._guard_blocks}")
        print(f"  Runtime errors: {self._runtime_errors}")
        print(f"  Total failures: {fail_summary.get('total_failures', 0)}")
        print(f"  By category: {fail_summary.get('by_category', {})}")
        print(f"  Guard mode: {self.capital_guard.guard_mode(self.engine.capital).value}")
        print(f"  Crash mode: {self.crash_detector.crash_mode(self.engine.capital).value}")
        print(f"{'#'*60}\n")

    # ── Main Loop ─────────────────────────────────────────────────────────

    def run(self):
        self._start_time = datetime.now(timezone.utc)
        end_time = self._start_time + self.duration if self.duration else None

        print(f"\n{'='*60}")
        print(f"OSIRIS Extended Demo — Real-Time Harness")
        print(f"Start: {self._start_time.isoformat()}")
        print(f"Duration: {self.duration}")
        print(f"Interval: {self.interval}s")
        print(f"Symbols: {self.symbols}")
        print(f"Resume: {self.resume_mode}")
        print(f"{'='*60}\n")

        # Resume state
        if self.resume_mode:
            self._load_state()

        # Main loop
        while not self._shutdown_requested:
            now = datetime.now(timezone.utc)
            if end_time and now >= end_time:
                print(f"[DURATION] Reached {self.duration}. Shutting down.")
                break

            self._cycle_id += 1

            # Phase 1: Refresh market data
            try:
                self._refresh_market_data()
            except Exception as e:
                self._runtime_errors += 1
                self.failures.record(
                    e, cycle_id=self._cycle_id,
                    recovery_action="sleep_retry", resolved=False,
                    impact="market_data_refresh_failed")

            # Phase 2: Generate events
            events = self._generate_events()

            # Phase 3: Run pipeline
            pipeline_result = self._run_pipeline(events)

            # Phase 4: Record telemetry
            self._record_telemetry(pipeline_result)

            # Phase 5: Health check
            health = self._run_health_check()

            # Phase 6: Summaries
            self._daily_summary()
            self._weekly_summary()

            # Phase 7: Heartbeat
            if self._cycle_id % 10 == 0:
                portfolio = self.engine.get_portfolio_summary()
                print(f"[HEARTBEAT] Cycle {self._cycle_id} | "
                      f"Equity ${portfolio.get('equity', 0):.2f} | "
                      f"Trades {self._trades_opened_total} | "
                      f"Health {health.value} | "
                      f"Errors {self._runtime_errors}")

            # Save state
            self._save_state()

            # Wait for next cycle
            if self._shutdown_requested:
                break
            try:
                time.sleep(self.interval)
            except KeyboardInterrupt:
                break

        # Shutdown
        self._save_state()
        self._print_final_summary()

    def _print_final_summary(self):
        portfolio = self.engine.get_portfolio_summary()
        fail_summary = self.failures.summary()
        guard_summary = self.guard_audit.summary()

        elapsed = datetime.now(timezone.utc) - self._start_time if self._start_time else timedelta()

        print(f"\n{'='*60}")
        print(f"  OSIRIS Extended Demo — Final Summary")
        print(f"{'='*60}")
        print(f"  Run duration: {elapsed.days}d {elapsed.seconds//3600}h")
        print(f"  Total cycles: {self._cycle_id}")
        print(f"  Events processed: {self._events_processed}")
        print(f"  Total trades: {self._trades_opened_total}")
        print(f"  Closed trades: {self._trades_closed_total}")
        print(f"  Final equity: ${portfolio.get('equity', 0):.2f}")
        print(f"  Total return: {portfolio.get('total_return_pct', 0):.2f}%")
        print(f"  Win rate: {portfolio.get('win_rate', 0):.1f}%")
        print(f"  Max DD: {portfolio.get('max_drawdown_pct', 0):.2f}%")
        print(f"  Sharpe: {portfolio.get('sharpe_ratio', 0):.2f}")
        print(f"  Guard blocks: {self._guard_blocks}")
        print(f"  Guard interventions: {guard_summary.get('total_interventions', 0)}")
        print(f"  Runtime errors: {self._runtime_errors}")
        print(f"  Data failures: {self._data_failures}")
        print(f"  Total failures: {fail_summary.get('total_failures', 0)}")
        print(f"  Critical failures: {fail_summary.get('critical_count', 0)}")
        print(f"  Guard mode (final): {self.capital_guard.guard_mode(self.engine.capital).value}")
        print(f"  Crash mode (final): {self.crash_detector.crash_mode(self.engine.capital).value}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="OSIRIS Extended Demo — Real-Time Harness")
    parser.add_argument("--smoke", action="store_true", help="7-day smoke test")
    parser.add_argument("--run", action="store_true", help="30-day validation")
    parser.add_argument("--extended", action="store_true", help="60-90 day extended")
    parser.add_argument("--interval", type=int, default=0, help="Cycle interval in seconds")
    parser.add_argument("--days", type=int, default=0, help="Duration in days")
    parser.add_argument("--resume", action="store_true", help="Resume from saved state")
    parser.add_argument("--capital", type=float, default=10000.0, help="Initial capital")
    parser.add_argument("--symbols", type=str, default="BTC,ETH", help="Symbols")

    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",")]

    if args.smoke:
        interval = args.interval or INTERVAL_SMOKE
        days = args.days or DURATION_SMOKE
    elif args.extended:
        interval = args.interval or INTERVAL_EXTENDED
        days = args.days or DURATION_EXTENDED
    elif args.run:
        interval = args.interval or INTERVAL_RUN
        days = args.days or DURATION_RUN
    else:
        interval = args.interval or INTERVAL_RUN
        days = args.days or DURATION_RUN

    harness = DemoHarness(
        symbols=symbols,
        interval_seconds=interval,
        duration_days=days,
        initial_capital=args.capital,
        resume=args.resume,
    )
    harness.run()


if __name__ == "__main__":
    main()
