from datetime import datetime, timezone
from types import SimpleNamespace

from core.decision_domain import DecisionJournal
from core.decision_domain.paper_adapter import (
    observe_paper_block, observe_paper_trade, record_paper_signal,
)
from core.execution.paper_trading import PaperTradingEngine
from core.schemas.trade_schema import TradeDirection, TradeSignal


def signal():
    return TradeSignal(event_id="e1", council_decision_id="e1", asset="BTC",
                       direction=TradeDirection.LONG, entry_price=100,
                       stop_loss=98, take_profit=104, position_size_pct=1,
                       conviction=70, risk_score=0.2, time_horizon_hours=24,
                       rationale="observed signal")


def test_paper_lifecycle_freezes_plan_and_appends_outcome(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    engine = PaperTradingEngine()
    s = signal()
    event = SimpleNamespace(id="e1", source="test_feed", source_id=None)
    did = record_paper_signal(journal, event, None, s)
    frozen, outcomes = journal.history(did)
    assert frozen["event_id"] == "e1"
    assert frozen["rationale"] == "observed signal"
    assert "validated_evidence_ids" in frozen["missing_information"]
    assert not outcomes
    trade = engine.execute_signal(s)
    assert trade is not None
    closed = engine.check_positions({"BTC": 104})
    assert closed == [trade]
    assert observe_paper_trade(journal, trade)
    still_frozen, outcomes = journal.history(did)
    assert still_frozen == frozen
    assert any("exit_reason=take_profit" == fact for fact in outcomes[0]["facts"])


def test_blocked_execution_is_factual_outcome(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    s = signal()
    event = SimpleNamespace(id="e1", source="feed", source_id=None)
    did = record_paper_signal(journal, event, None, s)
    observe_paper_block(journal, did, "capacity")
    _, outcomes = journal.history(did)
    assert outcomes[0]["facts"] == ["paper_execution_block=capacity"]
