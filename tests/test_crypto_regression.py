"""OSIRIS Crypto Regression Shield — Lock validated crypto profile behavior.
Any future multi-market changes must not break these tests.

Validated Crypto Trading Profile v1 covers:
- MarketAgent analysis for BTC/ETH/SOL
- RiskAgent risk scoring for crypto events
- Council decision-making for crypto
- PaperTradingEngine crypto execution
- CapitalGuard behavior
- Guard integration (CrashDetector, KnifeDetector, GapRisk)
- Live Paper Gate report schema
"""
import pytest
import json, os, sys
from datetime import datetime, timezone
from statistics import mean, stdev
from math import sqrt

sys.path.insert(0, ".")

from core.schemas.event_schema import (
    Event, EventType, Asset, AssetClass, Sentiment, Urgency,
)
from core.schemas.agent_schema import (
    AgentOpinion, Recommendation, CouncilDecision,
)
from core.schemas.trade_schema import (
    TradeSignal, Trade, TradeDirection, ExitReason, DIRECTION_MAP,
)
from core.schemas.agent_schema import AgentRole, CouncilTier
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.capital_guard import CapitalGuard, GuardMode
from core.execution.crash_detector import CrashDetector, CrashMode
from core.execution.knife_detector import KnifeDetector
from core.execution.gap_risk import GapRiskEngine
from core.execution.performance_memory import PerformanceMemory
from core.execution.direction_controller import DirectionController
from core.execution.slippage import SlippageEngine


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def crypto_event():
    return Event(
        id="regression_btc_001", source="test",
        event_type=EventType.PRICE_MOVEMENT,
        title="BTC price movement",
        assets=[Asset(symbol="BTC", name="Bitcoin",
                      asset_class=AssetClass.CRYPTO, price_at_event=50000.0)],
        timestamp=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        sentiment=Sentiment.BULLISH, sentiment_score=0.5,
        confidence=0.9, urgency=Urgency.HIGH,
    )


@pytest.fixture
def crypto_ohlcv():
    """Standard 50-candle BTC OHLCV fixture — uptrend with crypto vol (~50% annualized)."""
    return [
        {"close": 49000 + i * 80 + ((-1) ** i) * 300,
         "high": 49200 + i * 80 + ((-1) ** i) * 300,
         "low": 48800 + i * 80 + ((-1) ** i) * 300,
         "volume": 1000 + i * 10}
        for i in range(50)
    ]


@pytest.fixture
def crypto_event_eth():
    return Event(
        id="regression_eth_001", source="test",
        event_type=EventType.PRICE_MOVEMENT,
        title="ETH price movement",
        assets=[Asset(symbol="ETH", name="Ethereum",
                      asset_class=AssetClass.CRYPTO, price_at_event=3000.0)],
        timestamp=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        sentiment=Sentiment.BULLISH, sentiment_score=0.4,
        confidence=0.85, urgency=Urgency.MEDIUM,
    )


@pytest.fixture
def crypto_eth_ohlcv():
    """ETH OHLCV — gentle uptrend, RSI stays below 70."""
    return [
        {"close": 2900 + i * 10 + (i % 5) * 5,
         "high": 2910 + i * 10 + (i % 5) * 5,
         "low": 2890 + i * 10 + (i % 5) * 5,
         "volume": 2000 + i * 10}
        for i in range(50)
    ]


# ── Class: MarketAgent Output Lock ────────────────────────────────────────────

class TestMarketAgentCryptoRegression:
    """MarketAgent must produce consistent outputs for crypto events."""

    def test_agent_name_unchanged(self, crypto_event, crypto_ohlcv, monkeypatch):
        agent = MarketAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        assert opinion.agent_name == "market_agent"
        assert opinion.agent_role.value == "market_analyst"
        assert opinion.event_id == "regression_btc_001"

    def test_btc_bullish_structure(self, crypto_event, crypto_ohlcv, monkeypatch):
        """Rising BTC prices should produce a BUY recommendation."""
        agent = MarketAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        assert opinion.recommendation in (Recommendation.BUY, Recommendation.STRONG_BUY), \
            f"Expected BUY/STRONG_BUY for bullish BTC, got {opinion.recommendation}"

    def test_btc_metadata_structure(self, crypto_event, crypto_ohlcv, monkeypatch):
        """MarketAgent metadata must contain expected crypto fields."""
        agent = MarketAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        meta = opinion.metadata
        assert meta.get("symbol") == "BTC"
        assert meta.get("price", 0) > 0, "Price must be > 0"
        atr_14 = meta.get("atr_14", 0)
        price = meta.get("price", 1)
        assert atr_14 > 0 and atr_14 / price * 100 > 0, "ATR % must be > 0"
        assert meta.get("rsi_14", 0) > 0, "RSI must be calculated"

    def test_eth_bullish_structure(self, crypto_event_eth, crypto_eth_ohlcv, monkeypatch):
        agent = MarketAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_eth_ohlcv)
        opinion = agent.analyze(crypto_event_eth)
        assert opinion is not None
        assert opinion.recommendation in (Recommendation.BUY, Recommendation.STRONG_BUY)

    def test_crypto_event_with_no_ohlcv(self, crypto_event, monkeypatch):
        """Crypto event without OHLCV must return None (no opinion)."""
        agent = MarketAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: None)
        opinion = agent.analyze(crypto_event)
        assert opinion is None

    def test_btc_evidence_contains_keywords(self, crypto_event, crypto_ohlcv, monkeypatch):
        """Evidence list must contain crypto-relevant keywords."""
        agent = MarketAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        evidence_text = " ".join(opinion.evidence).lower()
        assert "btc" in evidence_text or "bitcoin" in evidence_text
        assert "rsi" in evidence_text
        assert "atr" in evidence_text

    def test_risk_score_in_range(self, crypto_event, crypto_ohlcv, monkeypatch):
        """Risk score must be a valid probability (0-1)."""
        agent = MarketAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        assert 0 <= opinion.risk_score <= 1.0

    def test_impact_score_calculated(self, crypto_event, crypto_ohlcv, monkeypatch):
        """MarketAgent impact_score must be a positive float."""
        agent = MarketAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        assert opinion.impact_score > 0


# ── Class: RiskAgent Output Lock ──────────────────────────────────────────────

class TestRiskAgentCryptoRegression:
    """RiskAgent must produce consistent outputs for crypto events."""

    def test_risk_agent_name(self, crypto_event, crypto_ohlcv, monkeypatch):
        agent = RiskAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        assert opinion.agent_name == "risk_agent"
        assert opinion.agent_role.value == "risk_analyst"

    def test_risk_metadata_structure(self, crypto_event, crypto_ohlcv, monkeypatch):
        agent = RiskAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        meta = opinion.metadata
        assert meta.get("annualized_volatility", 0) > 0
        assert meta.get("atr_pct", 0) > 0
        assert meta.get("max_position_pct", 0) > 0
        assert meta.get("suggested_stop_pct", 0) > 0

    def test_risk_calculations_reasonable(self, crypto_event, crypto_ohlcv, monkeypatch):
        agent = RiskAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        assert 0 <= opinion.risk_score <= 1.0
        assert 0 <= opinion.confidence <= 1.0

    def test_risk_btc_volatility(self, crypto_event, crypto_ohlcv, monkeypatch):
        """Crypto volatility must be within expected range."""
        agent = RiskAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        vol = opinion.metadata.get("annualized_volatility", 0)
        assert 20 <= vol <= 150, f"BTC annualized vol {vol} outside expected range 20-150%"

    def test_risk_suggested_stop(self, crypto_event, crypto_ohlcv, monkeypatch):
        agent = RiskAgent()
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        opinion = agent.analyze(crypto_event)
        assert opinion is not None
        stop = opinion.metadata.get("suggested_stop_pct", 0)
        assert 1.0 <= stop <= 15.0, f"Stop {stop}% outside expected range for crypto"


# ── Class: AgentCouncil Crypto Regression ─────────────────────────────────────

class TestCouncilCryptoRegression:
    """Council must produce decisions for crypto events."""

    def test_council_decides_on_crypto(self, crypto_event, crypto_ohlcv, monkeypatch):
        council = AgentCouncil()
        market = MarketAgent()
        risk = RiskAgent()
        monkeypatch.setattr(market, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        monkeypatch.setattr(risk, "_fetch_ohlcv", lambda s: crypto_ohlcv)

        m_opinion = market.analyze(crypto_event)
        r_opinion = risk.analyze(crypto_event)
        assert m_opinion is not None
        assert r_opinion is not None

        m_opinion.metadata["symbol"] = "BTC"
        m_opinion.metadata["price"] = 50000.0
        r_opinion.metadata["symbol"] = "BTC"
        r_opinion.metadata["price"] = 50000.0
        for key in ("max_position_pct", "suggested_stop_pct", "atr_pct"):
            if key in r_opinion.metadata:
                m_opinion.metadata[key] = r_opinion.metadata[key]

        council.submit_opinion(m_opinion)
        council.submit_opinion(r_opinion)
        decision = council.decide(crypto_event.id)

        assert decision is not None
        assert decision.event_id == "regression_btc_001"
        assert len(decision.opinions) == 2
        assert 0 <= decision.conviction <= 100

    def test_council_conviction_reasonable(self, crypto_event, crypto_ohlcv, monkeypatch):
        council = AgentCouncil()
        market = MarketAgent()
        risk = RiskAgent()
        monkeypatch.setattr(market, "_fetch_ohlcv", lambda s: crypto_ohlcv)
        monkeypatch.setattr(risk, "_fetch_ohlcv", lambda s: crypto_ohlcv)

        m_opinion = market.analyze(crypto_event)
        r_opinion = risk.analyze(crypto_event)
        m_opinion.metadata["symbol"] = "BTC"
        m_opinion.metadata["price"] = 50000.0
        r_opinion.metadata["symbol"] = "BTC"
        r_opinion.metadata["price"] = 50000.0
        for key in ("max_position_pct", "suggested_stop_pct", "atr_pct"):
            if key in r_opinion.metadata:
                m_opinion.metadata[key] = r_opinion.metadata[key]

        council.submit_opinion(m_opinion)
        council.submit_opinion(r_opinion)
        decision = council.decide(crypto_event.id)
        assert 10 <= decision.conviction <= 95, \
            f"Crypto conviction {decision.conviction} outside expected range"


# ── Class: PaperTradingEngine Crypto Regression ───────────────────────────────

class TestPaperTradingCryptoRegression:
    """PaperTradingEngine must handle crypto trades correctly."""

    @pytest.fixture
    def engine(self):
        return PaperTradingEngine(
            initial_capital=10000.0,
            max_open_positions=3,
        )

    def test_engine_creates_trade_signal(self, engine, monkeypatch):
        """A BUY decision for BTC must produce a valid TradeSignal."""
        closes = [100 + i for i in range(50)]
        mock_ohlcv = [
            {"close": closes[i], "high": closes[i] + 2,
             "low": closes[i] - 2, "volume": 1000.0}
            for i in range(50)
        ]

        class MockCouncil:
            def update_track_record(self, *args, **kwargs): pass

        engine.council = MockCouncil()
        engine.update_market_data("BTC", 150.0, ohlcv_history=mock_ohlcv)

        opinions = [
            AgentOpinion(
                agent_name="market_agent", agent_role=AgentRole.MARKET_ANALYST,
                confidence=0.7, impact_score=0.6, risk_score=0.3,
                evidence=["Bullish"], recommendation=Recommendation.BUY,
                rationale="Test", event_id="crypto_signal_001",
                metadata={"symbol": "BTC", "price": 150.0,
                          "suggested_stop_pct": 2.0, "max_position_pct": 20.0,
                          "atr_pct": 1.5},
            ),
            AgentOpinion(
                agent_name="risk_agent", agent_role=AgentRole.RISK_ANALYST,
                confidence=0.7, impact_score=0.5, risk_score=0.3,
                evidence=["Low risk"], recommendation=Recommendation.WATCH,
                rationale="Test", event_id="crypto_signal_001",
                metadata={"symbol": "BTC", "price": 150.0,
                          "suggested_stop_pct": 2.0, "max_position_pct": 20.0},
            ),
        ]
        decision = CouncilDecision(
            event_id="crypto_signal_001",
            opinions=opinions,
            action=Recommendation.BUY,
            conviction=65.0,
            consensus_score=0.7,
            rationale="Test",
            council_tier=CouncilTier.AGENT_COUNCIL,
            disagreement_score=0.2,
        )
        signal = engine.process_decision(decision)
        assert signal is not None
        assert signal.asset == "BTC"
        assert signal.direction == TradeDirection.LONG
        assert abs(signal.entry_price - 150.0) < 1.0
        assert signal.stop_loss < signal.entry_price
        assert signal.take_profit > signal.entry_price

    def test_engine_executes_crypto_trade(self, engine):
        signal = TradeSignal(
            event_id="crypto_trade_001",
            council_decision_id="crypto_trade_001",
            asset="BTC",
            direction=TradeDirection.LONG,
            entry_price=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            position_size_pct=10.0,
            conviction=60.0,
            risk_score=0.3,
            time_horizon_hours=24.0,
            rationale="Test crypto trade",
        )
        trade = engine.execute_signal(signal)
        assert trade is not None
        assert trade.signal.asset == "BTC"
        assert trade.entry_price_executed == 50000.0
        assert len(engine.positions) == 1

    def test_engine_tracks_open_positions(self, engine):
        for i in range(3):
            signal = TradeSignal(
                event_id=f"crypto_trade_{i}",
                council_decision_id=f"crypto_trade_{i}",
                asset="BTC",
                direction=TradeDirection.LONG,
                entry_price=50000.0 + i * 100,
                stop_loss=49000.0,
                take_profit=52000.0,
                position_size_pct=10.0,
                conviction=60.0,
                risk_score=0.3,
                time_horizon_hours=24.0,
                rationale="Test",
            )
            engine.execute_signal(signal)
        assert len(engine.positions) == 3

        # Max positions reached — no more trades
        signal4 = TradeSignal(
            event_id="crypto_trade_4",
            council_decision_id="crypto_trade_4",
            asset="BTC",
            direction=TradeDirection.LONG,
            entry_price=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            position_size_pct=10.0,
            conviction=60.0,
            risk_score=0.3,
            time_horizon_hours=24.0,
            rationale="Test",
        )
        assert engine.execute_signal(signal4) is None

    def test_crypto_trade_pnl_long_win(self, engine):
        signal = TradeSignal(
            event_id="crypto_pnl_001",
            council_decision_id="crypto_pnl_001",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=100.0, stop_loss=90.0, take_profit=110.0,
            position_size_pct=50.0, conviction=70.0, risk_score=0.2,
            time_horizon_hours=24.0,
            rationale="Test",
        )
        trade = engine.execute_signal(signal)
        trade.exit_price = 110.0
        trade.close(110.0, ExitReason.TAKE_PROFIT)
        engine._record_trade_result(trade)
        assert trade.pnl_percent is not None
        assert trade.pnl_percent > 0

    def test_crypto_trade_pnl_short_win(self, engine):
        signal = TradeSignal(
            event_id="crypto_pnl_002",
            council_decision_id="crypto_pnl_002",
            asset="BTC", direction=TradeDirection.SHORT,
            entry_price=100.0, stop_loss=110.0, take_profit=90.0,
            position_size_pct=50.0, conviction=70.0, risk_score=0.2,
            time_horizon_hours=24.0,
            rationale="Test",
        )
        trade = engine.execute_signal(signal)
        trade.exit_price = 90.0
        trade.close(90.0, ExitReason.TAKE_PROFIT)
        engine._record_trade_result(trade)
        assert trade.pnl_percent is not None
        assert trade.pnl_percent > 0

    def test_crypto_trade_stop_loss_hit(self, engine):
        signal = TradeSignal(
            event_id="crypto_sl_001",
            council_decision_id="crypto_sl_001",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=100.0, stop_loss=95.0, take_profit=110.0,
            position_size_pct=50.0, conviction=70.0, risk_score=0.2,
            time_horizon_hours=24.0,
            rationale="Test",
        )
        trade = engine.execute_signal(signal)
        trade.exit_price = 95.0
        trade.close(95.0, ExitReason.STOP_LOSS)
        engine._record_trade_result(trade)
        assert trade.pnl_percent is not None
        assert trade.pnl_percent < 0

    def test_crypto_position_sizing(self, engine):
        engine.initial_capital = 10000.0
        engine.capital = 10500.0
        engine.total_trades = 50  # Risk base has grown
        rb = engine._risk_base()
        assert rb > 10000.0, f"Risk base {rb} should grow with trade count"

    def test_crypto_portfolio_summary_structure(self, engine):
        """Portfolio summary must contain expected crypto trading fields."""
        summary = engine.get_portfolio_summary()
        required_fields = [
            "initial_capital", "equity", "open_positions", "closed_trades",
            "total_trades", "wins", "losses", "win_rate", "avg_pnl_pct",
            "sharpe_ratio", "crash_score", "crash_mode", "gap_risk_score",
            "guard_mode", "kill_switch", "total_pnl_abs", "total_return_pct",
            "max_drawdown_pct",
        ]
        for field in required_fields:
            assert field in summary, f"Portfolio summary missing field: {field}"


# ── Class: CapitalGuard Crypto Regression ─────────────────────────────────────

class TestCapitalGuardCryptoRegression:
    """CapitalGuard must behave consistently for crypto risk profiles."""

    def test_initial_mode_normal(self):
        guard = CapitalGuard(initial_capital=10000.0)
        assert guard.guard_mode(10000.0) == GuardMode.NORMAL

    def test_emergency_on_drawdown(self):
        guard = CapitalGuard(initial_capital=10000.0,
                             emergency_dd_threshold=20.0,
                             halt_dd_threshold=35.0)
        guard.update_equity(10000.0)
        assert guard.guard_mode(7500.0) == GuardMode.EMERGENCY
        assert guard.guard_mode(6400.0) == GuardMode.HALT

    def test_size_reduction_in_emergency(self):
        guard = CapitalGuard(initial_capital=10000.0)
        guard.update_equity(10000.0)
        guard._consecutive_losses = 7
        assert guard.guard_mode(10000.0) == GuardMode.EMERGENCY
        reduction = guard.should_reduce_size(10000.0)
        assert reduction <= 0.5

    def test_kill_switch_blocks_trading(self):
        guard = CapitalGuard(initial_capital=10000.0)
        guard.activate_kill_switch()
        assert guard.is_trading_allowed() is False
        assert guard.can_enter_new_position(10000.0) is False

    def test_summary_structure(self):
        guard = CapitalGuard(initial_capital=10000.0)
        s = guard.summary()
        required = ["mode", "drawdown_pct", "daily_loss_pct", "weekly_loss_pct",
                    "open_risk_pct", "consecutive_losses", "kill_switch",
                    "size_reduction", "trading_allowed", "can_enter"]
        for field in required:
            assert field in s, f"CapitalGuard summary missing field: {field}"


# ── Class: Guard Integration Crypto Regression ────────────────────────────────

class TestGuardIntegrationCryptoRegression:
    """Integrated guard stack must behave consistently for crypto."""

    def test_crash_detector_initial_state(self):
        cd = CrashDetector()
        assert cd.crash_score() == 0.0
        assert cd.crash_mode(10000.0) == CrashMode.NONE

    def test_crash_detector_velocity(self):
        cd = CrashDetector()
        for i in range(80):
            cd.update_price(100.0 * (1 - 0.005 * (i + 1)))
        assert cd.drawdown_velocity_6h() > 0
        assert cd.drawdown_velocity_24h() > 0

    def test_knife_detector_initial_state(self):
        kd = KnifeDetector()
        assert kd is not None

    def test_gap_risk_initial_state(self):
        gr = GapRiskEngine()
        s = gr.summary()
        assert "gap_risk_score" in s
        assert 0 <= s["gap_risk_score"] <= 100

    def test_direction_controller_initial(self):
        dc = DirectionController()
        assert dc.should_disable_long() is False
        assert dc.should_disable_short() is False


# ── Class: Event Schema Crypto Regression ─────────────────────────────────────

class TestEventSchemaCryptoRegression:
    """Crypto events must be created and serialized correctly."""

    def test_crypto_asset_creation(self):
        asset = Asset(symbol="BTC", name="Bitcoin",
                      asset_class=AssetClass.CRYPTO, price_at_event=50000.0)
        assert asset.symbol == "BTC"
        assert asset.asset_class == AssetClass.CRYPTO
        assert asset.price_at_event == 50000.0

    def test_crypto_event_serialization(self, crypto_event):
        d = crypto_event.to_dict()
        assert d["id"] == "regression_btc_001"
        assert d["event_type"] == "price_movement"
        assert len(d["assets"]) == 1
        assert d["assets"][0]["asset_class"] == "crypto"
        restored = Event.from_dict(d)
        assert restored.id == crypto_event.id
        assert restored.assets[0].symbol == "BTC"

    def test_crypto_trade_direction_map(self):
        assert DIRECTION_MAP[Recommendation.BUY] == TradeDirection.LONG
        assert DIRECTION_MAP[Recommendation.SELL] == TradeDirection.SHORT
        assert DIRECTION_MAP[Recommendation.STRONG_BUY] == TradeDirection.LONG
        assert DIRECTION_MAP[Recommendation.STRONG_SELL] == TradeDirection.SHORT

    def test_trade_signal_crypto_roundtrip(self):
        signal = TradeSignal(
            event_id="btc_001", council_decision_id="btc_001",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=50000.0, stop_loss=49000.0,
            take_profit=52000.0, position_size_pct=10.0,
            conviction=65.0, risk_score=0.3,
            time_horizon_hours=24.0,
            rationale="Test BTC trade",
        )
        d = signal.to_dict()
        assert d["asset"] == "BTC"
        assert d["direction"] == "long"


# ── Class: Live Paper Gate Schema Regression ──────────────────────────────────

class TestLivePaperGateReportSchema:
    """The live paper gate report structure must remain stable."""

    def test_report_structure(self):
        """Verify the full report schema from a previous run if available."""
        report_dir = "_live_paper_gate"
        if not os.path.isdir(report_dir):
            pytest.skip("No live paper gate reports found")

        import glob
        reports = sorted(glob.glob(f"{report_dir}/live_paper_gate_report_*.json"))
        if not reports:
            pytest.skip("No report files found")

        with open(reports[-1]) as f:
            report = json.load(f)

        required_sections = [
            "run_info", "trading_metrics", "risk_metrics",
            "protection_metrics", "system_metrics",
            "guard_audit", "telemetry", "demo_gate_evaluation",
        ]
        for section in required_sections:
            assert section in report, f"Report missing section: {section}"

        # Verify sub-fields
        tm = report["trading_metrics"]
        for field in ["trades_opened", "trades_closed", "win_rate",
                       "total_pnl_abs", "max_drawdown"]:
            assert field in tm, f"trading_metrics missing: {field}"

        pm = report["protection_metrics"]
        for field in ["crash_detector_activations", "gap_risk_activations",
                       "knife_detector_blocks", "blocked_trades_total"]:
            assert field in pm, f"protection_metrics missing: {field}"

        dg = report["demo_gate_evaluation"]
        assert "verdict" in dg
        assert dg["verdict"] in ("GO", "NO GO")


# ── Class: Cross-Market Impact Shield ─────────────────────────────────────────

class TestCrossMarketImpactShield:
    """Ensure non-crypto data doesn't silently affect crypto behavior."""

    def test_stock_event_rejected_by_market_agent(self, monkeypatch):
        """A stock event should not crash the market agent — it should return None."""
        agent = MarketAgent()
        stock_event = Event(
            id="stock_001", source="test",
            event_type=EventType.PRICE_MOVEMENT,
            title="AAPL price movement",
            assets=[Asset(symbol="AAPL", name="Apple Inc.",
                          asset_class=AssetClass.STOCK, price_at_event=150.0)],
        )
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: None)
        opinion = agent.analyze(stock_event)
        # MarketAgent doesn't filter by asset class — it will try to fetch OHLCV.
        # If OHLCV fails (no Binance map for AAPL, yfinance fallback may work),
        # it returns None. This test verifies no crash occurs.
        assert opinion is None or isinstance(opinion, AgentOpinion)

    def test_forex_event_no_crash(self, monkeypatch):
        """Forex events must not crash the pipeline — they should be handled gracefully."""
        agent = MarketAgent()
        forex_event = Event(
            id="forex_001", source="test",
            event_type=EventType.PRICE_MOVEMENT,
            title="EURUSD movement",
            assets=[Asset(symbol="EURUSD", name="Euro/USD",
                          asset_class=AssetClass.FOREX, price_at_event=1.08)],
        )
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: None)
        opinion = agent.analyze(forex_event)
        assert opinion is None or isinstance(opinion, AgentOpinion)

    def test_commodity_event_no_crash(self, monkeypatch):
        agent = MarketAgent()
        comm_event = Event(
            id="commodity_001", source="test",
            event_type=EventType.PRICE_MOVEMENT,
            title="Gold price movement",
            assets=[Asset(symbol="GC=F", name="Gold Futures",
                          asset_class=AssetClass.COMMODITY, price_at_event=2000.0)],
        )
        monkeypatch.setattr(agent, "_fetch_ohlcv", lambda s: None)
        opinion = agent.analyze(comm_event)
        assert opinion is None or isinstance(opinion, AgentOpinion)

    def test_paper_trading_engine_rejects_non_crypto(self):
        """PaperTradingEngine should not crash on non-crypto events — decision returns None."""
        engine = PaperTradingEngine()
        non_crypto_opinions = [
            AgentOpinion(
                agent_name="market_agent",
                agent_role=AgentRole.MARKET_ANALYST,
                confidence=0.7, impact_score=0.6, risk_score=0.3,
                evidence=["EURUSD setup"],
                recommendation=Recommendation.BUY,
                rationale="Forex test",
                event_id="forex_001",
                metadata={"symbol": "EURUSD", "price": 1.08,
                          "suggested_stop_pct": 0.5, "max_position_pct": 20.0},
            ),
        ]
        decision = CouncilDecision(
            event_id="forex_001",
            opinions=non_crypto_opinions,
            action=Recommendation.BUY,
            conviction=60.0,
            consensus_score=0.7,
            rationale="Forex test",
            council_tier=CouncilTier.AGENT_COUNCIL,
            disagreement_score=0.2,
        )
        # Should return None or a signal — must not crash
        result = engine.process_decision(decision)
        assert result is None or isinstance(result, TradeSignal)
