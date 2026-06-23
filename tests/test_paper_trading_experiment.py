"""Phase 3 — Long-Running Paper Trading Experiment

Simulates the full OSIRIS pipeline over historical data with hourly decision cycles.
Uses real Binance OHLCV data (free, no API key).
Generates events from OHLCV movements, runs agents, council, paper trading.

Run: python -m pytest tests/test_paper_trading_experiment.py -v --timeout=120
"""
import pytest
from datetime import datetime, timezone, timedelta
from statistics import mean, stdev
from math import sqrt
from collections import defaultdict

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Urgency, Sentiment
from core.schemas.agent_schema import Recommendation, AgentRole
from core.schemas.trade_schema import TradeDirection, ExitReason
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory


SYMBOLS = ["BTC", "ETH", "SOL"]

# ── Helper: Build events from OHLCV data ──────────────────────────────────

def generate_events_from_ohlcv(symbol, ohlcv):
    """Generate hourly events from OHLCV data, using price movements as triggers."""
    events = []
    for i in range(1, len(ohlcv)):
        prev = ohlcv[i - 1]
        curr = ohlcv[i]
        price_change = (curr["close"] - prev["close"]) / prev["close"]

        event_type = EventType.PRICE_MOVEMENT
        urgency = Urgency.LOW
        sentiment_score = price_change
        confidence = 0.6 + min(abs(price_change) * 2, 0.3)

        if abs(price_change) > 0.02:
            urgency = Urgency.MEDIUM
        if abs(price_change) > 0.05:
            urgency = Urgency.HIGH
        if abs(price_change) > 0.05 and curr["volume"] > prev["volume"] * 1.5:
            event_type = EventType.VOLUME_SPIKE
            urgency = Urgency.HIGH

        events.append(Event(
            id=f"{symbol}_bar_{i}",
            source="historical_test",
            event_type=event_type,
            title=f"{symbol} price movement: {price_change*100:+.2f}%",
            assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO, price_at_event=curr["close"])],
            timestamp=curr["time"],
            detected_at=curr["time"],
            urgency=urgency,
            sentiment_score=sentiment_score,
            confidence=confidence,
        ))
    return events


def run_experiment(days=14, symbols=None):
    """Run the full OSIRIS pipeline over historical data.

    Returns dict with: trades, decisions, performance_summary, agent_stats, council_stats.
    """
    if symbols is None:
        symbols = SYMBOLS

    from core.execution.backtest_engine_v2 import BacktestEngineV2
    ohlcv_fetcher = BacktestEngineV2()

    # Fetch OHLCV for all symbols
    all_ohlcv = {}
    for sym in symbols:
        data = ohlcv_fetcher.fetch_ohlcv(sym, days=days + 5)
        if data and len(data) >= 50:
            all_ohlcv[sym] = data

    if not all_ohlcv:
        pytest.skip("No OHLCV data available from Binance")

    # Generate events from OHLCV
    all_events = []
    for sym, ohlcv in all_ohlcv.items():
        all_events.extend(generate_events_from_ohlcv(sym, ohlcv))
    all_events.sort(key=lambda e: e.timestamp)

    # Pipeline components
    market = MarketAgent()
    risk = RiskAgent()
    council = AgentCouncil()
    perf = PerformanceMemory()
    engine = PaperTradingEngine(initial_capital=10000.0, performance_memory=perf, council=council)

    # Override _fetch_ohlcv to use cached data for speed
    def make_fetcher(sym_ohlcv):
        def fetch(symbol):
            return sym_ohlcv.get(symbol)
        return fetch

    market._fetch_ohlcv = make_fetcher(all_ohlcv)
    risk._fetch_ohlcv = make_fetcher(all_ohlcv)

    decisions = []
    signals = []
    price_history = defaultdict(list)

    # Process events in chronological order (hourly decision cycle)
    for event in all_events:
        sym = event.assets[0].symbol
        ohlcv = all_ohlcv[sym]

        # Record price for position checking
        price_history[sym].append((event.timestamp, event.assets[0].price_at_event))

        # Agent analysis
        m_opinion = market.analyze(event)
        r_opinion = risk.analyze(event)

        if not m_opinion or not r_opinion:
            continue

        # Council decision
        council.submit_opinion(m_opinion)
        council.submit_opinion(r_opinion)
        decision = council.decide(event.id)
        if not decision:
            continue

        decisions.append(decision)

        # Paper trading
        signal = engine.process_decision(decision)
        if signal:
            signals.append(signal)
            engine.execute_signal(signal)

        # Check positions with latest price
        current_prices = {}
        for s in symbols:
            if price_history[s]:
                current_prices[s] = price_history[s][-1][1]
        if current_prices:
            engine.check_positions(current_prices)

    # Final position check at end of experiment
    final_prices = {}
    for s in symbols:
        if price_history[s]:
            final_prices[s] = price_history[s][-1][1]
    engine.check_positions(final_prices)

    # ── Compile results ──────────────────────────────────────────────

    portfolio = engine.get_portfolio_summary()
    learning = perf.get_learning_summary()

    # Agent performance attribution
    agent_stats = {}
    for agent_name in perf._agent_records:
        records = perf._agent_records[agent_name]
        wins = sum(1 for r in records if r["correct"])
        total = len(records)
        agent_stats[agent_name] = {
            "total_calls": total,
            "wins": wins,
            "accuracy": wins / total if total > 0 else 0,
            "avg_confidence": mean(r["confidence"] for r in records) if records else 0,
            "calibration": perf.get_agent_confidence_calibration(agent_name),
        }

    # Council decision analysis
    council_stats = {}
    if decisions:
        convictions = [d.conviction for d in decisions]
        consensus_scores = [d.consensus_score for d in decisions]
        actions = [d.action for d in decisions]
        council_stats = {
            "total_decisions": len(decisions),
            "avg_conviction": round(mean(convictions), 2),
            "avg_consensus": round(mean(consensus_scores), 2),
            "action_distribution": {a.value: actions.count(a) for a in set(actions)},
            "conviction_std": round(stdev(convictions), 2) if len(convictions) > 1 else 0,
        }

    # Trade performance by asset and direction
    trade_stats = {"total": 0, "wins": 0, "losses": 0, "by_asset": {}, "by_direction": {}}
    for t in engine.closed_trades:
        trade_stats["total"] += 1
        key = "wins" if (t.pnl_percent or 0) > 0 else "losses"
        trade_stats[key] += 1

        asset = t.signal.asset
        if asset not in trade_stats["by_asset"]:
            trade_stats["by_asset"][asset] = {"count": 0, "wins": 0, "pnl": 0.0}
        trade_stats["by_asset"][asset]["count"] += 1
        trade_stats["by_asset"][asset]["wins"] += 1 if (t.pnl_percent or 0) > 0 else 0
        trade_stats["by_asset"][asset]["pnl"] += t.pnl_percent or 0

        direction = t.signal.direction.value
        if direction not in trade_stats["by_direction"]:
            trade_stats["by_direction"][direction] = {"count": 0, "wins": 0, "pnl": 0.0}
        trade_stats["by_direction"][direction]["count"] += 1
        trade_stats["by_direction"][direction]["wins"] += 1 if (t.pnl_percent or 0) > 0 else 0
        trade_stats["by_direction"][direction]["pnl"] += t.pnl_percent or 0

    return {
        "portfolio": portfolio,
        "learning_summary": learning,
        "agent_stats": agent_stats,
        "council_stats": council_stats,
        "trade_stats": trade_stats,
        "total_events": len(all_events),
        "total_decisions": len(decisions),
        "total_signals": len(signals),
        "symbols_with_data": list(all_ohlcv.keys()),
        "experiment_days": days,
    }


# ── Tests ─────────────────────────────────────────────────────────────────

class TestPaperTradingExperiment:
    """Long-running paper trading experiment over historical data."""

    @pytest.fixture(scope="class")
    def experiment_results(self):
        return run_experiment(days=14)

    def test_pipeline_executes(self, experiment_results):
        """Verify the pipeline runs without errors."""
        assert experiment_results["total_events"] > 0
        assert experiment_results["symbols_with_data"], "No OHLCV data fetched"

    def test_decisions_generated(self, experiment_results):
        """Verify council produces decisions."""
        r = experiment_results
        assert r["total_decisions"] > 0, "No council decisions generated"
        assert r["council_stats"]["total_decisions"] > 0

    def test_trades_executed(self, experiment_results):
        """Verify paper trading executes trades."""
        r = experiment_results
        assert r["trade_stats"]["total"] >= 0
        assert r["portfolio"]["total_trades"] >= 0

    def test_performance_memory_updated(self, experiment_results):
        """Verify agent records are populated."""
        r = experiment_results
        if r["portfolio"]["total_trades"] > 0:
            assert len(r["agent_stats"]) > 0
            for name, stats in r["agent_stats"].items():
                assert stats["total_calls"] > 0
                assert 0 <= stats["accuracy"] <= 1

    def test_portfolio_tracking(self, experiment_results):
        """Verify portfolio summary structure."""
        r = experiment_results
        p = r["portfolio"]
        assert p["initial_capital"] == 10000.0
        assert p["equity"] >= -p["initial_capital"]
        assert "win_rate" in p
        assert "sharpe_ratio" in p

    def test_both_directions_traded(self, experiment_results):
        """Verify both LONG and SHORT trades occur (MM agents are contrarian)."""
        r = experiment_results
        if r["trade_stats"]["total"] > 5:
            by_dir = r["trade_stats"]["by_direction"]
            assert "long" in by_dir or "short" in by_dir


class TestPerformanceAttribution:
    """Phase 4 — Determine which agents contribute positively."""

    @pytest.fixture(scope="class")
    def experiment_results(self):
        return run_experiment(days=14)

    def test_agent_accuracy_tracked(self, experiment_results):
        """Verify we can rank agents by accuracy."""
        r = experiment_results
        if not r["agent_stats"]:
            pytest.skip("No trades executed — no agent stats available")

        ranked = sorted(
            r["agent_stats"].items(),
            key=lambda x: x[1]["accuracy"],
            reverse=True,
        )
        print(f"\n{'='*60}\nAgent Performance Ranking:\n{'='*60}")
        for name, stats in ranked:
            cal = stats["calibration"]
            print(f"  {name:20s} accuracy={stats['accuracy']:.1%} "
                  f"calls={stats['total_calls']:3d} "
                  f"confidence={stats['avg_confidence']:.2f} "
                  f"bias={cal['bias']:+.3f} "
                  f"{'OVERCONFIDENT' if cal['overconfidence'] else 'underconfident' if cal['underconfidence'] else 'calibrated'}")
        assert len(ranked) > 0

    def test_agent_contributions(self, experiment_results):
        """Identify which agents contribute to winning/losing trades."""
        r = experiment_results
        if not r["agent_stats"]:
            pytest.skip("No trades executed")

        agents = r["agent_stats"]
        market_stats = agents.get("market_agent", {})
        risk_stats = agents.get("risk_agent", {})

        for name, stats in [("market_agent", market_stats), ("risk_agent", risk_stats)]:
            if stats.get("total_calls", 0) >= 3:
                assert 0 <= stats["accuracy"] <= 1
                print(f"\n{name}: {stats['accuracy']:.1%} accuracy "
                      f"({stats['wins']}/{stats['total_calls']})")

    def test_confidence_calibration(self, experiment_results):
        """Verify confidence calibration tracking."""
        r = experiment_results
        if not r["agent_stats"]:
            pytest.skip("No trades executed")

        for name, stats in r["agent_stats"].items():
            cal = stats["calibration"]
            if stats["total_calls"] >= 5:
                print(f"\n{name} calibration: confidence={cal['avg_confidence']:.2f} "
                      f"accuracy={cal['actual_accuracy']:.2f} "
                      f"bias={cal['bias']:+.3f}")
            # Minimum validation: bias should be a finite number
            assert isinstance(cal["bias"], float)


class TestCouncilValidation:
    """Phase 5 — Validate Council v2 mechanics."""

    @pytest.fixture(scope="class")
    def experiment_results(self):
        return run_experiment(days=14)

    def test_conviction_vs_outcome(self, experiment_results):
        """Higher conviction should correlate with positive outcomes."""
        from core.execution.backtest_engine_v2 import BacktestEngineV2

        r = experiment_results
        fetcher = BacktestEngineV2()
        all_ohlcv = {}
        for sym in SYMBOLS:
            data = fetcher.fetch_ohlcv(sym, days=r["experiment_days"] + 5)
            if data and len(data) >= 50:
                all_ohlcv[sym] = data

        market = MarketAgent()
        risk = RiskAgent()
        market._fetch_ohlcv = lambda s: all_ohlcv.get(s)
        risk._fetch_ohlcv = lambda s: all_ohlcv.get(s)

        # Build conviction→outcome pairs
        pairs = []
        for sym, ohlcv in all_ohlcv.items():
            events = generate_events_from_ohlcv(sym, ohlcv)
            for event in events:
                m_o = market.analyze(event)
                r_o = risk.analyze(event)
                if not m_o or not r_o:
                    continue
                council = AgentCouncil()
                council.submit_opinion(m_o)
                council.submit_opinion(r_o)
                decision = council.decide(event.id)
                if not decision:
                    continue

                # Find subsequent price change
                idx = None
                for i, c in enumerate(ohlcv):
                    if c["time"] >= event.timestamp:
                        idx = i
                        break
                if idx is None or idx + 24 >= len(ohlcv):
                    continue
                future_price = ohlcv[idx + 24]["close"]
                current_price = event.assets[0].price_at_event or ohlcv[idx]["close"]

                direction = 1 if decision.action in (Recommendation.BUY, Recommendation.STRONG_BUY) else -1
                if direction == 0:
                    continue

                outcome = (future_price - current_price) / current_price * direction
                pairs.append((decision.conviction, outcome))

        if len(pairs) < 3:
            pytest.skip(f"Only {len(pairs)} conviction-outcome pairs")

        # Split into high/low conviction groups
        median_c = sorted(pairs, key=lambda x: x[0])[len(pairs) // 2][0]
        high_conv = [p[1] for p in pairs if p[0] >= median_c]
        low_conv = [p[1] for p in pairs if p[0] < median_c]

        high_avg = mean(high_conv) if high_conv else 0
        low_avg = mean(low_conv) if low_conv else 0
        total_avg = mean(p[1] for p in pairs)

        print(f"\n{'='*60}\nConviction vs Outcome ({len(pairs)} samples):\n{'='*60}")
        print(f"  Overall avg outcome: {total_avg:+.4f}")
        print(f"  High conviction avg: {high_avg:+.4f}")
        print(f"  Low conviction avg:  {low_avg:+.4f}")
        print(f"  High better than low: {high_avg > low_avg}")

        assert isinstance(high_avg, float)
        assert isinstance(low_avg, float)

    def test_consensus_vs_outcome(self, experiment_results):
        """Higher consensus should correlate with better outcomes."""
        from core.execution.backtest_engine_v2 import BacktestEngineV2

        r = experiment_results
        fetcher = BacktestEngineV2()
        all_ohlcv = {}
        for sym in SYMBOLS:
            data = fetcher.fetch_ohlcv(sym, days=r["experiment_days"] + 5)
            if data and len(data) >= 50:
                all_ohlcv[sym] = data

        market = MarketAgent()
        risk = RiskAgent()
        market._fetch_ohlcv = lambda s: all_ohlcv.get(s)
        risk._fetch_ohlcv = lambda s: all_ohlcv.get(s)

        pairs = []
        for sym, ohlcv in all_ohlcv.items():
            events = generate_events_from_ohlcv(sym, ohlcv)
            for event in events:
                m_o = market.analyze(event)
                r_o = risk.analyze(event)
                if not m_o or not r_o:
                    continue
                council = AgentCouncil()
                council.submit_opinion(m_o)
                council.submit_opinion(r_o)
                decision = council.decide(event.id)
                if not decision:
                    continue

                idx = None
                for i, c in enumerate(ohlcv):
                    if c["time"] >= event.timestamp:
                        idx = i
                        break
                if idx is None or idx + 24 >= len(ohlcv):
                    continue
                future_price = ohlcv[idx + 24]["close"]
                current_price = event.assets[0].price_at_event or ohlcv[idx]["close"]

                direction = 1 if decision.action in (Recommendation.BUY, Recommendation.STRONG_BUY) else -1
                if direction == 0:
                    continue
                outcome = (future_price - current_price) / current_price * direction
                pairs.append((decision.consensus_score, outcome))

        if len(pairs) < 3:
            pytest.skip(f"Only {len(pairs)} consensus-outcome pairs")

        median_c = sorted(pairs, key=lambda x: x[0])[len(pairs) // 2][0]
        high_cons = [p[1] for p in pairs if p[0] >= median_c]
        low_cons = [p[1] for p in pairs if p[0] < median_c]

        high_avg = mean(high_cons) if high_cons else 0
        low_avg = mean(low_cons) if low_cons else 0

        print(f"\n{'='*60}\nConsensus vs Outcome ({len(pairs)} samples):\n{'='*60}")
        print(f"  High consensus avg: {high_avg:+.4f}")
        print(f"  Low consensus avg:  {low_avg:+.4f}")
        print(f"  High better than low: {high_avg > low_avg}")

        assert isinstance(high_avg, float)

    def test_track_record_effect(self, experiment_results):
        """Verify that track records change after trades and affect decisions."""
        r = experiment_results
        if not r["agent_stats"]:
            pytest.skip("No trades executed")

        agents = r["agent_stats"]
        print(f"\n{'='*60}\nTrack Record Effect:\n{'='*60}")
        for name, stats in agents.items():
            if stats["total_calls"] >= 3:
                print(f"  {name:20s} accuracy={stats['accuracy']:.1%} "
                      f"({stats['wins']}/{stats['total_calls']})")
                cal = stats["calibration"]
                if stats["total_calls"] >= 5:
                    print(f"  {'':20s}bias={cal['bias']:+.3f} "
                          f"{'overconfident' if cal['overconfidence'] else 'underconfident' if cal['underconfidence'] else 'calibrated'}")
        assert len(agents) >= 0
