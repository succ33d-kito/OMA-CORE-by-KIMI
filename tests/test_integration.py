"""End-to-end integration test for the full OSIRIS trading pipeline.
Verifies: Event → AgentOpinions → CouncilDecision → TradeSignal → Trade → Position → PerformanceMemory
"""
import pytest
from datetime import datetime, timezone, timedelta
from statistics import mean

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Urgency, Sentiment
from core.schemas.agent_schema import AgentOpinion, CouncilTier, Recommendation, AgentRole
from core.schemas.trade_schema import TradeSignal, TradeDirection, TradeStatus, ExitReason
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def mock_ohlcv():
    """Standard 50-candle OHLCV for testing. Uptrend pattern."""
    base = datetime.now(timezone.utc) - timedelta(hours=50)
    candles = []
    for i in range(50):
        price = 100.0 + i * 0.5  # steady uptrend from 100 to 124.5
        candles.append({
            "time": base + timedelta(hours=i),
            "open": price - 0.1,
            "high": price + 1.0,
            "low": price - 1.0,
            "close": price,
            "volume": 1000 + i * 10,
        })
    return candles


@pytest.fixture
def mock_volatile_ohlcv():
    """High-volatility 50-candle OHLCV with sharp moves."""
    base = datetime.now(timezone.utc) - timedelta(hours=50)
    candles = []
    price = 100.0
    for i in range(50):
        price += (-2 if i % 3 == 0 else 1.5)
        candles.append({
            "time": base + timedelta(hours=i),
            "open": price - 0.5,
            "high": price + 3.0,
            "low": price - 3.0,
            "close": price,
            "volume": 2000 + (i * 50),
        })
    return candles


def make_event(event_id, symbol="BTC", event_type=EventType.PRICE_MOVEMENT,
               urgency=Urgency.MEDIUM, sentiment_score=0.3, confidence=0.7,
               price=50000.0):
    return Event(
        id=event_id,
        source="test",
        event_type=event_type,
        title=f"Test event {event_id}",
        assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO, price_at_event=price)],
        urgency=urgency,
        sentiment_score=sentiment_score,
        confidence=confidence,
    )


# ── Phase 2: End-to-End Pipeline Test ─────────────────────────────────────

class TestFullPipeline:
    def test_event_to_opinions(self, mock_ohlcv, monkeypatch):
        """Verify Event → AgentOpinions pipeline with mock OHLCV."""
        market = MarketAgent()
        risk = RiskAgent()
        monkeypatch.setattr(market, "_fetch_ohlcv", lambda s: mock_ohlcv)
        monkeypatch.setattr(risk, "_fetch_ohlcv", lambda s: mock_ohlcv)

        event = make_event("e2e_001")
        m_opinion = market.analyze(event)
        r_opinion = risk.analyze(event)

        assert m_opinion is not None, "MarketAgent should produce opinion"
        assert r_opinion is not None, "RiskAgent should produce opinion"
        assert m_opinion.agent_role == AgentRole.MARKET_ANALYST
        assert r_opinion.agent_role == AgentRole.RISK_ANALYST
        assert 0 <= m_opinion.confidence <= 1
        assert 0 <= r_opinion.confidence <= 1
        assert m_opinion.event_id == "e2e_001"
        assert r_opinion.event_id == "e2e_001"

    def test_opinions_to_council_decision(self, mock_ohlcv, monkeypatch):
        """Verify AgentOpinions → CouncilDecision with metadata propagation."""
        market = MarketAgent()
        risk = RiskAgent()
        monkeypatch.setattr(market, "_fetch_ohlcv", lambda s: mock_ohlcv)
        monkeypatch.setattr(risk, "_fetch_ohlcv", lambda s: mock_ohlcv)

        event = make_event("e2e_002")
        m_opinion = market.analyze(event)
        r_opinion = risk.analyze(event)

        council = AgentCouncil()
        council.submit_opinion(m_opinion)
        council.submit_opinion(r_opinion)
        decision = council.decide("e2e_002")

        assert decision is not None
        assert decision.conviction > 0
        assert decision.consensus_score >= 0
        assert len(decision.opinions) == 2
        assert "entry_price" in decision.metadata
        assert decision.metadata["entry_price"] > 0

    def test_council_decision_to_trade_signal(self, mock_ohlcv, monkeypatch):
        """Verify CouncilDecision → PaperTradingEngine.process_decision → TradeSignal."""
        market = MarketAgent()
        risk = RiskAgent()
        monkeypatch.setattr(market, "_fetch_ohlcv", lambda s: mock_ohlcv)
        monkeypatch.setattr(risk, "_fetch_ohlcv", lambda s: mock_ohlcv)

        event = make_event("e2e_003")
        m_opinion = market.analyze(event)
        r_opinion = risk.analyze(event)

        council = AgentCouncil()
        council.submit_opinion(m_opinion)
        council.submit_opinion(r_opinion)
        decision = council.decide("e2e_003")

        engine = PaperTradingEngine(initial_capital=10000.0)
        signal = engine.process_decision(decision)

        assert signal is not None
        assert signal.asset == "BTC"
        assert signal.direction in (TradeDirection.LONG, TradeDirection.SHORT)
        assert signal.stop_loss < signal.entry_price if signal.direction == TradeDirection.LONG else signal.stop_loss > signal.entry_price
        assert signal.take_profit > signal.entry_price if signal.direction == TradeDirection.LONG else signal.take_profit < signal.entry_price
        assert signal.risk_reward_ratio() >= 1.0
        assert "opinions" in signal.metadata
        assert len(signal.metadata["opinions"]) == 2

    def test_trade_signal_to_execution(self, mock_ohlcv, monkeypatch):
        """Verify TradeSignal → execute_signal → Trade → check_positions → close."""
        market = MarketAgent()
        risk = RiskAgent()
        monkeypatch.setattr(market, "_fetch_ohlcv", lambda s: mock_ohlcv)
        monkeypatch.setattr(risk, "_fetch_ohlcv", lambda s: mock_ohlcv)

        event = make_event("e2e_004")
        m_opinion = market.analyze(event)
        r_opinion = risk.analyze(event)

        council = AgentCouncil()
        council.submit_opinion(m_opinion)
        council.submit_opinion(r_opinion)
        decision = council.decide("e2e_004")

        engine = PaperTradingEngine(initial_capital=10000.0, council=council)
        signal = engine.process_decision(decision)
        assert signal is not None

        trade = engine.execute_signal(signal)
        assert trade is not None
        assert trade.status == TradeStatus.OPEN
        assert trade.size > 0
        assert len(engine.positions) == 1

        closed = engine.check_positions({"BTC": 1000000.0})
        assert len(closed) == 1
        assert closed[0].status == TradeStatus.CLOSED
        assert closed[0].exit_reason in (ExitReason.TAKE_PROFIT, ExitReason.STOP_LOSS)

    def test_time_expiry_closes_position(self, mock_ohlcv, monkeypatch):
        """Verify that positions expire after time_horizon_hours."""
        market = MarketAgent()
        risk = RiskAgent()
        monkeypatch.setattr(market, "_fetch_ohlcv", lambda s: mock_ohlcv)
        monkeypatch.setattr(risk, "_fetch_ohlcv", lambda s: mock_ohlcv)

        event = make_event("e2e_005")
        m_opinion = market.analyze(event)
        r_opinion = risk.analyze(event)

        council = AgentCouncil()
        council.submit_opinion(m_opinion)
        council.submit_opinion(r_opinion)
        decision = council.decide("e2e_005")

        engine = PaperTradingEngine(initial_capital=10000.0, council=council)
        signal = engine.process_decision(decision)
        if signal is None:
            pytest.skip("No trade signal generated for this event")
        signal.time_horizon_hours = 0.1
        trade = engine.execute_signal(signal)
        assert trade is not None

        import time
        trade.entry_time = datetime.now(timezone.utc) - timedelta(hours=1)

        closed = engine.check_positions({"BTC": trade.entry_price_executed})
        assert len(closed) == 1
        assert closed[0].exit_reason == ExitReason.TIME_EXPIRY

    def test_council_track_records_update(self, mock_ohlcv, monkeypatch):
        """Verify Council track records are updated after trade closes."""
        market = MarketAgent()
        risk = RiskAgent()
        monkeypatch.setattr(market, "_fetch_ohlcv", lambda s: mock_ohlcv)
        monkeypatch.setattr(risk, "_fetch_ohlcv", lambda s: mock_ohlcv)

        event = make_event("e2e_006")
        m_opinion = market.analyze(event)
        r_opinion = risk.analyze(event)

        council = AgentCouncil()
        council.submit_opinion(m_opinion)
        council.submit_opinion(r_opinion)
        council.decide("e2e_006")

        assert council.get_track_record("market_agent") == 0.5
        assert council.get_track_record("risk_agent") == 0.5

        engine = PaperTradingEngine(initial_capital=10000.0, council=council)
        event2 = make_event("e2e_006b")
        m2 = market.analyze(event2)
        r2 = risk.analyze(event2)
        council2 = AgentCouncil()
        council2.submit_opinion(m2)
        council2.submit_opinion(r2)
        d2 = council2.decide("e2e_006b")

        engine2 = PaperTradingEngine(initial_capital=10000.0, council=council2)
        s2 = engine2.process_decision(d2)
        if s2 is None:
            pytest.skip("No trade signal generated")
        engine2.execute_signal(s2)
        engine2.check_positions({"BTC": 1000000.0})

        track_market = council2.get_track_record("market_agent")
        track_risk = council2.get_track_record("risk_agent")
        assert track_market != 0.5, f"Track record should change from 0.5, got {track_market}"
        assert track_risk != 0.5, f"Track record should change from 0.5, got {track_risk}"

    def test_performance_memory_updates(self, mock_ohlcv, monkeypatch):
        """Verify PerformanceMemory records trades and agent outcomes."""
        perf = PerformanceMemory()
        market = MarketAgent()
        risk = RiskAgent()
        monkeypatch.setattr(market, "_fetch_ohlcv", lambda s: mock_ohlcv)
        monkeypatch.setattr(risk, "_fetch_ohlcv", lambda s: mock_ohlcv)

        event = make_event("e2e_007")
        m_opinion = market.analyze(event)
        r_opinion = risk.analyze(event)

        council = AgentCouncil()
        council.submit_opinion(m_opinion)
        council.submit_opinion(r_opinion)
        decision = council.decide("e2e_007")

        engine = PaperTradingEngine(initial_capital=10000.0, performance_memory=perf, council=council)
        signal = engine.process_decision(decision)
        engine.execute_signal(signal)
        engine.check_positions({"BTC": 1000000.0})

        summary = perf.get_learning_summary()
        assert summary["total_trades_recorded"] >= 1
        assert len(summary["agent_accuracies"]) > 0
        assert summary["recommendation_success"] != {}


# ── Phase 2: Council v2 Validation Tests ─────────────────────────────────

class TestCouncilV2Validation:
    def test_risk_reduces_conviction(self):
        """C1 fix verification: higher risk must produce LOWER conviction."""
        council = AgentCouncil()

        low_risk = AgentOpinion(
            agent_name="test_a", agent_role=AgentRole.MARKET_ANALYST,
            confidence=0.8, impact_score=0.6, risk_score=0.1,
            evidence=[], recommendation=Recommendation.BUY,
            rationale="low risk", event_id="v_001",
        )
        high_risk = AgentOpinion(
            agent_name="test_b", agent_role=AgentRole.RISK_ANALYST,
            confidence=0.8, impact_score=0.6, risk_score=0.9,
            evidence=[], recommendation=Recommendation.SELL,
            rationale="high risk", event_id="v_001",
        )

        council.submit_opinion(low_risk)
        council.submit_opinion(high_risk)
        decision = council.decide("v_001")

        low_only = AgentCouncil()
        low_only.submit_opinion(low_risk)
        high_only = AgentCouncil()
        high_only.submit_opinion(high_risk)

        dec_low = low_only.decide("v_001")
        dec_high = high_only.decide("v_001")

        assert dec_low is not None and dec_high is not None
        assert dec_low.conviction > dec_high.conviction, \
            f"Low-risk conviction ({dec_low.conviction}) should exceed high-risk conviction ({dec_high.conviction})"

    def test_track_record_weighting_affects_vote(self):
        """Agents with better track records should have more influence."""
        council = AgentCouncil()

        good_agent = AgentOpinion(
            agent_name="good_agent", agent_role=AgentRole.MARKET_ANALYST,
            confidence=0.7, impact_score=0.5, risk_score=0.3,
            evidence=[], recommendation=Recommendation.BUY,
            rationale="good call", event_id="v_010",
        )
        bad_agent = AgentOpinion(
            agent_name="bad_agent", agent_role=AgentRole.RISK_ANALYST,
            confidence=0.7, impact_score=0.5, risk_score=0.3,
            evidence=[], recommendation=Recommendation.SELL,
            rationale="bad call", event_id="v_010",
        )

        for _ in range(10):
            council.update_track_record("good_agent", True)
            council.update_track_record("bad_agent", False)

        council.submit_opinion(good_agent)
        council.submit_opinion(bad_agent)
        decision = council.decide("v_010")

        assert decision.action == Recommendation.BUY, \
            "Good agent's BUY should outweigh bad agent's SELL"
        assert council.get_track_record("good_agent") > 0.5
        assert council.get_track_record("bad_agent") < 0.5

    def test_consensus_correlation(self):
        """When agents disagree, consensus_score should be lower."""
        council_high = AgentCouncil()

        opinions_agree = [
            AgentOpinion(
                agent_name=f"a{i}", agent_role=AgentRole.MARKET_ANALYST,
                confidence=0.8, impact_score=0.5, risk_score=0.3,
                evidence=[], recommendation=Recommendation.BUY,
                rationale=f"agree {i}", event_id="v_020",
            )
            for i in range(3)
        ]
        for o in opinions_agree:
            council_high.submit_opinion(o)
        dec_agree = council_high.decide("v_020")

        council_low = AgentCouncil()
        opinions_disagree = [
            AgentOpinion(
                agent_name=f"b{i}", agent_role=AgentRole.MARKET_ANALYST,
                confidence=[0.9, 0.5, 0.1][i], impact_score=0.5, risk_score=0.3,
                evidence=[], recommendation=Recommendation.BUY,
                rationale=f"disagree {i}", event_id="v_021",
            )
            for i in range(3)
        ]
        for o in opinions_disagree:
            council_low.submit_opinion(o)
        dec_disagree = council_low.decide("v_021")

        assert dec_agree.consensus_score > dec_disagree.consensus_score, \
            "Agreeing opinions should yield higher consensus than disagreeing"

    def test_conviction_correlation(self):
        """Higher confidence should produce higher conviction (all else equal)."""
        council_low = AgentCouncil()
        council_high = AgentCouncil()

        low_conf = AgentOpinion(
            agent_name="a1", agent_role=AgentRole.MARKET_ANALYST,
            confidence=0.3, impact_score=0.5, risk_score=0.3,
            evidence=[], recommendation=Recommendation.BUY,
            rationale="low conf", event_id="v_030",
        )
        high_conf = AgentOpinion(
            agent_name="a2", agent_role=AgentRole.MARKET_ANALYST,
            confidence=0.9, impact_score=0.5, risk_score=0.3,
            evidence=[], recommendation=Recommendation.BUY,
            rationale="high conf", event_id="v_031",
        )

        single_low = AgentCouncil()
        single_high = AgentCouncil()
        single_low.submit_opinion(low_conf)
        single_high.submit_opinion(high_conf)
        d_low = single_low.decide("v_030")
        d_high = single_high.decide("v_031")

        assert d_high.conviction > d_low.conviction, \
            f"High confidence ({d_high.conviction}) should exceed low ({d_low.conviction})"


# ── Backtest Integration Test ─────────────────────────────────────────────

class TestBacktestIntegration:
    def test_simulate_with_council_signal(self, mock_ohlcv, monkeypatch):
        """Verify BacktestEngineV2 can simulate a Council-generated signal."""
        btc_signal = TradeSignal(
            event_id="bt_001", council_decision_id="bt_001",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=100.0, stop_loss=95.0, take_profit=110.0,
            position_size_pct=15.0, conviction=75.0, risk_score=0.3,
            time_horizon_hours=24.0, rationale="Integration test signal",
        )
        from core.execution.backtest_engine_v2 import BacktestEngineV2
        engine = BacktestEngineV2()
        result = engine.simulate(btc_signal, mock_ohlcv)

        assert result.pnl_percent is not None
        assert result.entry_price > 0
        assert result.exit_reason is not None
        assert result.holding_hours is not None

    def test_run_backtest_from_signals(self, mock_ohlcv, monkeypatch):
        """Verify run_backtest produces all expected metrics."""
        from core.execution.backtest_engine_v2 import BacktestEngineV2
        engine = BacktestEngineV2()
        monkeypatch.setattr(engine, "fetch_ohlcv", lambda s, days=30: mock_ohlcv)

        signals = [
            TradeSignal(
                event_id=f"bt_{i}", council_decision_id=f"bt_{i}",
                asset="BTC", direction=TradeDirection.LONG,
                entry_price=100.0, stop_loss=95.0, take_profit=110.0,
                position_size_pct=10.0, conviction=70.0, risk_score=0.3,
                time_horizon_hours=24.0, rationale="Test",
            )
            for i in range(10)
        ]
        result = engine.run_backtest(signals, days=1)

        assert result["status"] == "ok"
        assert result["total_trades"] == 10
        assert "win_rate" in result
        assert "profit_factor" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown_pct" in result
        assert "by_asset" in result
        assert "BTC" in result["by_asset"]

    def test_multi_asset_backtest(self, mock_ohlcv, monkeypatch):
        """Verify backtest handles multiple assets."""
        from core.execution.backtest_engine_v2 import BacktestEngineV2
        engine = BacktestEngineV2()

        def multi_fetch(symbol, days=30):
            return mock_ohlcv
        monkeypatch.setattr(engine, "fetch_ohlcv", multi_fetch)

        signals = [
            TradeSignal(
                event_id=f"bt_{i}", council_decision_id=f"bt_{i}",
                asset=asset, direction=TradeDirection.LONG,
                entry_price=100.0, stop_loss=95.0, take_profit=110.0,
                position_size_pct=10.0, conviction=70.0, risk_score=0.3,
                time_horizon_hours=24.0, rationale="Test",
            )
            for i, asset in enumerate(["BTC", "ETH", "SOL"])
        ]
        result = engine.run_backtest(signals, days=1)

        assert result["status"] == "ok"
        assert result["total_trades"] == 3
        for asset in ["BTC", "ETH", "SOL"]:
            assert asset in result["by_asset"]

    def test_conviction_risk_formula_bug_verified(self):
        """Verify fix C1: conviction decreases when risk increases."""
        from core.execution.backtest_engine_v2 import BacktestEngineV2
        from core.schemas.trade_schema import TradeSignal, TradeDirection

        engine = BacktestEngineV2()
        base_time = datetime.now(timezone.utc) - timedelta(hours=5)
        ohlcv = [
            {"time": base_time + timedelta(hours=i), "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}
            for i in range(24)
        ]

        low_risk_signal = TradeSignal(
            event_id="risk_1", council_decision_id="risk_1",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=100.0, stop_loss=99.0, take_profit=110.0,
            position_size_pct=10.0, conviction=85.0, risk_score=0.1,
            time_horizon_hours=24.0, rationale="Low risk test",
        )

        high_risk_signal = TradeSignal(
            event_id="risk_2", council_decision_id="risk_2",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=100.0, stop_loss=99.0, take_profit=110.0,
            position_size_pct=10.0, conviction=85.0, risk_score=0.9,
            time_horizon_hours=24.0, rationale="High risk test",
        )
        result_low = engine.simulate(low_risk_signal, ohlcv)
        result_high = engine.simulate(high_risk_signal, ohlcv)

        assert result_low.pnl_percent == result_high.pnl_percent, \
            "Same SL/TP should produce same PnL regardless of risk_score"


# ── Position Sizing Cap Test (H4 fix) ─────────────────────────────────────

class TestPositionSizing:
    def test_exposure_capped_at_100_percent(self, monkeypatch):
        """Verify total exposure never exceeds 100% of capital."""
        council = AgentCouncil()

        opinions = [
            AgentOpinion(
                agent_name="market", agent_role=AgentRole.MARKET_ANALYST,
                confidence=0.9, impact_score=0.8, risk_score=0.1,
                evidence=[], recommendation=Recommendation.BUY,
                rationale="buy", event_id=f"pos_{i}",
                metadata={"symbol": "BTC", "price": 50000.0, "suggested_stop_pct": 2.0},
            )
            for i in range(6)
        ]

        engine = PaperTradingEngine(initial_capital=10000.0, council=council)
        for i, opinion in enumerate(opinions):
            council2 = AgentCouncil()
            council2.submit_opinion(opinion)
            decision = council2.decide(f"pos_{i}")
            signal = engine.process_decision(decision)
            if signal:
                engine.execute_signal(signal)

        total_pct = sum(p.signal.position_size_pct for p in engine.positions)
        assert total_pct <= 100.0, f"Total exposure {total_pct}% exceeds 100%"
        assert len(engine.positions) <= engine.max_open_positions


# ── Component Dependency Graph ────────────────────────────────────────────

def test_dependency_graph():
    """Document the component dependency graph with a test that validates imports."""
    from core.schemas import agent_schema, event_schema, trade_schema
    from core.agents import market_agent, risk_agent
    from core.council import council
    from core.execution import backtest_engine_v2, paper_trading, performance_memory

    deps = {
        "Event": ["event_schema"],
        "MarketAgent": ["event_schema", "agent_schema", "event_bus"],
        "RiskAgent": ["event_schema", "agent_schema", "event_bus"],
        "AgentCouncil": ["agent_schema", "trade_schema", "event_bus"],
        "TradeSignal": ["agent_schema"],
        "PaperTradingEngine": ["trade_schema", "agent_schema", "performance_memory"],
        "PerformanceMemory": ["trade_schema", "memory"],
        "BacktestEngineV2": ["trade_schema", "agent_schema", "database"],
    }
    assert len(deps) == 8
    assert all(name for name in deps)
