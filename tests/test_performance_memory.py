"""Tests for OSIRIS Performance Memory"""
import pytest
from datetime import datetime, timezone
from core.execution.performance_memory import PerformanceMemory
from core.schemas.trade_schema import (
    TradeSignal, Trade, TradeDirection, ExitReason,
)


class TestPerformanceMemory:
    def test_record_trade(self):
        pm = PerformanceMemory()
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
        pm.record_trade(trade)
        assert len(pm._trades) == 1

    def test_agent_accuracy_tracking(self):
        pm = PerformanceMemory()
        for _ in range(5):
            pm.record_opinion_outcome("good_agent", {"agent_name": "good_agent", "event_id": f"evt_{_}", "recommendation": "buy", "confidence": 0.8}, 5.0, True)
        for _ in range(3):
            pm.record_opinion_outcome("bad_agent", {"agent_name": "bad_agent", "event_id": f"evt_{_}", "recommendation": "sell", "confidence": 0.8}, -3.0, False)

        good_acc = pm.get_agent_accuracy("good_agent")
        bad_acc = pm.get_agent_accuracy("bad_agent")
        assert good_acc == 1.0
        assert bad_acc == 0.0

    def test_accuracy_min_records(self):
        pm = PerformanceMemory()
        pm.record_opinion_outcome("new_agent", {"agent_name": "new", "event_id": "evt_1", "recommendation": "buy", "confidence": 0.8}, 2.0, True)
        acc = pm.get_agent_accuracy("new_agent", min_records=5)
        assert acc == 0.5

    def test_confidence_calibration(self):
        pm = PerformanceMemory()
        for _ in range(10):
            pm.record_opinion_outcome("overconfident", {"agent_name": "oc", "event_id": f"evt_{_}", "recommendation": "buy", "confidence": 0.95}, 2.0, True)

        cal = pm.get_agent_confidence_calibration("overconfident")
        assert cal["avg_confidence"] > 0.9
        assert cal["actual_accuracy"] > 0.9

    def test_recommendation_success_rate(self):
        pm = PerformanceMemory()
        pm.record_opinion_outcome("a1", {"agent_name": "a1", "event_id": "e1", "recommendation": "buy", "confidence": 0.8}, 2.0, True)
        pm.record_opinion_outcome("a1", {"agent_name": "a1", "event_id": "e2", "recommendation": "buy", "confidence": 0.8}, -1.0, False)
        pm.record_opinion_outcome("a2", {"agent_name": "a2", "event_id": "e3", "recommendation": "sell", "confidence": 0.7}, 3.0, True)

        rates = pm.get_recommendation_success_rate()
        assert "buy" in rates
        assert "sell" in rates
        assert rates["buy"] == 50.0
        assert rates["sell"] == 100.0

    def test_learning_summary_structure(self):
        pm = PerformanceMemory()
        signal = TradeSignal(
            event_id="evt_sum", council_decision_id="dec_sum",
            asset="ETH", direction=TradeDirection.LONG,
            entry_price=3000.0, stop_loss=2900.0,
            take_profit=3300.0, position_size_pct=5.0,
            conviction=60.0, risk_score=0.4,
            time_horizon_hours=12.0, rationale="Test",
        )
        trade = Trade(signal=signal, entry_time=datetime.now(timezone.utc), entry_price_executed=3000.0, size=500.0)
        trade.close(3300.0, ExitReason.TAKE_PROFIT)
        pm.record_trade(trade)
        pm.record_opinion_outcome("agent_x", {"agent_name": "agent_x", "event_id": "evt_sum", "recommendation": "buy", "confidence": 0.8}, 10.0, True)

        summary = pm.get_learning_summary()
        assert summary["total_trades_recorded"] == 1
        assert summary["total_agent_records"] == 1
        assert "agent_x" in summary["agent_accuracies"]
