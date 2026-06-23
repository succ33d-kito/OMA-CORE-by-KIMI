"""Tests for OSIRIS Trade Schema"""
import pytest
from datetime import datetime, timezone
from core.schemas.trade_schema import (
    TradeSignal, Trade, TradeDirection, TradeStatus, ExitReason,
    DIRECTION_MAP,
)
from core.schemas.agent_schema import Recommendation


class TestTradeSignal:
    def test_create_signal(self):
        signal = TradeSignal(
            event_id="evt_1",
            council_decision_id="dec_1",
            asset="BTC",
            direction=TradeDirection.LONG,
            entry_price=50000.0,
            stop_loss=48000.0,
            take_profit=54000.0,
            position_size_pct=10.0,
            conviction=75.0,
            risk_score=0.3,
            time_horizon_hours=24.0,
            rationale="Bullish breakout",
        )
        assert signal.asset == "BTC"
        assert signal.risk_reward_ratio() == 2.0
        assert signal.direction == TradeDirection.LONG

    def test_risk_reward_short(self):
        signal = TradeSignal(
            event_id="evt_2", council_decision_id="dec_2",
            asset="ETH", direction=TradeDirection.SHORT,
            entry_price=3000.0, stop_loss=3200.0,
            take_profit=2700.0, position_size_pct=5.0,
            conviction=60.0, risk_score=0.4,
            time_horizon_hours=12.0, rationale="Bearish",
        )
        assert signal.risk_reward_ratio() == 1.5

    def test_serialization(self):
        signal = TradeSignal(
            event_id="evt_3", council_decision_id="dec_3",
            asset="SOL", direction=TradeDirection.LONG,
            entry_price=100.0, stop_loss=95.0,
            take_profit=110.0, position_size_pct=15.0,
            conviction=80.0, risk_score=0.2,
            time_horizon_hours=48.0, rationale="Test",
        )
        data = signal.to_dict()
        assert data["asset"] == "SOL"
        assert data["risk_reward_ratio"] == 2.0


class TestTrade:
    def test_trade_long_win(self):
        signal = TradeSignal(
            event_id="evt_1", council_decision_id="dec_1",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=50000.0, stop_loss=48000.0,
            take_profit=54000.0, position_size_pct=10.0,
            conviction=75.0, risk_score=0.3,
            time_horizon_hours=24.0, rationale="Test",
        )
        trade = Trade(
            signal=signal,
            entry_time=datetime.now(timezone.utc),
            entry_price_executed=50000.0,
            size=1000.0,
        )
        trade.close(54000.0, ExitReason.TAKE_PROFIT)
        assert trade.status == TradeStatus.CLOSED
        assert trade.pnl_percent == 8.0
        assert trade.exit_reason == ExitReason.TAKE_PROFIT

    def test_trade_short_loss(self):
        signal = TradeSignal(
            event_id="evt_2", council_decision_id="dec_2",
            asset="ETH", direction=TradeDirection.SHORT,
            entry_price=3000.0, stop_loss=3200.0,
            take_profit=2700.0, position_size_pct=5.0,
            conviction=60.0, risk_score=0.4,
            time_horizon_hours=12.0, rationale="Test",
        )
        trade = Trade(
            signal=signal,
            entry_time=datetime.now(timezone.utc),
            entry_price_executed=3000.0,
            size=500.0,
        )
        trade.close(3200.0, ExitReason.STOP_LOSS)
        assert trade.status == TradeStatus.CLOSED
        assert trade.pnl_percent == -6.67  # (3000-3200)/3000*100
        assert trade.exit_reason == ExitReason.STOP_LOSS

    def test_direction_map(self):
        assert DIRECTION_MAP[Recommendation.STRONG_BUY].value == "long"
        assert DIRECTION_MAP[Recommendation.SELL].value == "short"
        assert DIRECTION_MAP[Recommendation.WATCH].value == "flat"
        assert DIRECTION_MAP[Recommendation.HOLD].value == "flat"
