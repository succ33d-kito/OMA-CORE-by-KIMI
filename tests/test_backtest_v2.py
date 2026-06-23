"""Tests for OSIRIS Backtest Engine v2"""
import pytest
from datetime import datetime, timezone, timedelta
from core.execution.backtest_engine_v2 import BacktestEngineV2, BacktestTrade
from core.schemas.trade_schema import TradeSignal, TradeDirection, ExitReason


class TestBacktestTrade:
    def test_trade_creation(self):
        signal = TradeSignal(
            event_id="evt_1", council_decision_id="dec_1",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=50000.0, stop_loss=48000.0,
            take_profit=54000.0, position_size_pct=10.0,
            conviction=75.0, risk_score=0.3,
            time_horizon_hours=24.0, rationale="Test",
        )
        trade = BacktestTrade(
            signal=signal,
            entry_time=datetime.now(timezone.utc),
            entry_price=50000.0,
        )
        assert trade.signal.asset == "BTC"
        assert trade.pnl_percent is None

    def test_winning_long(self):
        signal = TradeSignal(
            event_id="evt_1", council_decision_id="dec_1",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=100.0, stop_loss=95.0,
            take_profit=110.0, position_size_pct=10.0,
            conviction=75.0, risk_score=0.3,
            time_horizon_hours=24.0, rationale="Test",
        )
        ohlcv = [
            {"time": datetime.now(timezone.utc) + timedelta(hours=i), "open": 100.0, "high": 105.0, "low": 99.0, "close": 102.0, "volume": 1000}
            for i in range(30)
        ]
        ohlcv[5] = {"time": datetime.now(timezone.utc) + timedelta(hours=5), "open": 108.0, "high": 112.0, "low": 107.0, "close": 110.0, "volume": 2000}

        engine = BacktestEngineV2()
        result = engine.simulate(signal, ohlcv)
        assert result.pnl_percent is not None
        assert result.pnl_percent > 0

    def test_stop_loss_hit(self):
        signal = TradeSignal(
            event_id="evt_2", council_decision_id="dec_2",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=100.0, stop_loss=95.0,
            take_profit=110.0, position_size_pct=10.0,
            conviction=75.0, risk_score=0.3,
            time_horizon_hours=24.0, rationale="Test",
        )
        ohlcv = [
            {"time": datetime.now(timezone.utc) + timedelta(hours=i), "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}
            for i in range(30)
        ]
        ohlcv[3] = {"time": datetime.now(timezone.utc) + timedelta(hours=3), "open": 94.0, "high": 94.5, "low": 93.0, "close": 93.5, "volume": 1500}

        engine = BacktestEngineV2()
        result = engine.simulate(signal, ohlcv)
        assert result.met_stop_loss
        assert result.exit_reason == ExitReason.STOP_LOSS
        assert result.pnl_percent < 0

    def test_take_profit_hit(self):
        signal = TradeSignal(
            event_id="evt_3", council_decision_id="dec_3",
            asset="BTC", direction=TradeDirection.SHORT,
            entry_price=100.0, stop_loss=105.0,
            take_profit=90.0, position_size_pct=10.0,
            conviction=75.0, risk_score=0.3,
            time_horizon_hours=24.0, rationale="Test",
        )
        ohlcv = [
            {"time": datetime.now(timezone.utc) + timedelta(hours=i), "open": 100.0, "high": 102.0, "low": 99.0, "close": 100.0, "volume": 1000}
            for i in range(5)
        ] + [
            {"time": datetime.now(timezone.utc) + timedelta(hours=i+5), "open": 88.0, "high": 89.0, "low": 85.0, "close": 87.0, "volume": 2000}
            for i in range(5, 30)
        ]

        engine = BacktestEngineV2()
        result = engine.simulate(signal, ohlcv)
        assert result.met_take_profit
        assert result.pnl_percent > 0

    def test_no_valid_entry(self):
        signal = TradeSignal(
            event_id="evt_4", council_decision_id="dec_4",
            asset="BTC", direction=TradeDirection.LONG,
            entry_price=100.0, stop_loss=95.0,
            take_profit=110.0, position_size_pct=10.0,
            conviction=75.0, risk_score=0.3,
            time_horizon_hours=24.0, rationale="Test",
            timestamp=datetime.now(timezone.utc) + timedelta(days=365),
        )
        ohlcv = [
            {"time": datetime.now(timezone.utc) + timedelta(hours=i), "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}
            for i in range(10)
        ]
        engine = BacktestEngineV2()
        result = engine.simulate(signal, ohlcv)
        assert result.pnl_percent == 0.0

    def test_run_backtest_empty_signals(self):
        engine = BacktestEngineV2()
        result = engine.run_backtest([], days=1)
        assert result["status"] == "no_data"
        assert result["total_trades"] == 0

    def test_run_backtest_metrics(self, monkeypatch):
        engine = BacktestEngineV2()

        def mock_fetch(*args, **kwargs):
            return [
                {"time": datetime.now(timezone.utc) + timedelta(hours=i), "open": 100.0, "high": 105.0, "low": 95.0, "close": 102.0, "volume": 1000}
                for i in range(50)
            ]
        monkeypatch.setattr(engine, "fetch_ohlcv", mock_fetch)

        signals = [
            TradeSignal(
                event_id=f"evt_{i}", council_decision_id=f"dec_{i}",
                asset="BTC", direction=TradeDirection.LONG,
                entry_price=100.0, stop_loss=95.0,
                take_profit=110.0, position_size_pct=10.0,
                conviction=70.0, risk_score=0.3,
                time_horizon_hours=24.0, rationale="Test",
            )
            for i in range(5)
        ]
        result = engine.run_backtest(signals, days=1)
        assert result["status"] == "ok"
        assert result["total_trades"] >= 0
        assert "win_rate" in result
        assert "sharpe_ratio" in result
        assert "profit_factor" in result
        assert "max_drawdown_pct" in result
