import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from core.decision_domain import DecisionJournal
from core.decision_domain.paper_adapter import observe_paper_trade, record_paper_signal
from core.execution.paper_checkpoint import restore, snapshot
from core.execution.paper_trading import PaperTradingEngine
from core.schemas.trade_schema import TradeDirection, TradeSignal


def _signal():
    return TradeSignal(event_id="e1", council_decision_id="e1", asset="BTC",
                       direction=TradeDirection.LONG, entry_price=100,
                       stop_loss=98, take_profit=104, position_size_pct=2,
                       conviction=70, risk_score=0.2, time_horizon_hours=24,
                       rationale="paper test")


def test_restart_restores_open_trade_risk_and_outcome_link(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    before = PaperTradingEngine()
    before.capital_guard.record_trade_result(-20)
    before.direction_ctrl.record_trade("short", -1)
    signal = _signal()
    did = record_paper_signal(journal, SimpleNamespace(id="e1", source="feed", source_id=None), None, signal)
    before.execute_signal(signal)
    saved = json.loads(json.dumps(snapshot(before)))
    after = PaperTradingEngine()
    restore(after, saved)
    assert after.positions[0].signal.metadata["decision_record_id"] == did
    assert after.capital_guard._consecutive_losses == 1
    assert after.direction_ctrl.short_wr() == 0
    assert after.get_portfolio_summary()["open_positions"] == 1
    closed = after.check_positions({"BTC": 104})
    assert observe_paper_trade(journal, closed[0])
    assert journal.history(did)[1][0]["decision_id"] == did


def test_incompatible_or_incomplete_checkpoint_cannot_reset_portfolio():
    engine = PaperTradingEngine()
    with pytest.raises(ValueError):
        restore(engine, {"version": 1, "initial_capital": 10000})
    with pytest.raises(ValueError):
        restore(engine, snapshot(engine) | {"initial_capital": 20000})
    assert engine.positions == []


def test_harness_persists_snapshot_and_rejects_legacy_resume(tmp_path, monkeypatch):
    import scripts.extended_demo_realtime as demo
    monkeypatch.setattr(demo, "OUT_DIR", str(tmp_path))
    monkeypatch.setattr(demo, "STATE_FILE", str(tmp_path / "run_state.json"))
    first = demo.DemoHarness(resume=False)
    first.engine.execute_signal(_signal())
    first.council._track_record["market_agent"] = 0.73
    first.perf_memory._agent_records["market_agent"].append({"correct": True})
    first._save_state()
    second = demo.DemoHarness(resume=True)
    assert second._load_state()
    assert len(second.engine.positions) == 1
    assert second.council.get_track_record("market_agent") == 0.73
    assert second.perf_memory._agent_records["market_agent"] == [{"correct": True}]
    assert second.decision_journal.load_paper_state()["paper_checkpoint"]["positions"]
    (tmp_path / "run_state.json").unlink()
    third = demo.DemoHarness(resume=True)
    assert third._load_state()
    assert len(third.engine.positions) == 1
    monkeypatch.setattr(demo, "OUT_DIR", str(tmp_path / "legacy"))
    monkeypatch.setattr(demo, "STATE_FILE", str(tmp_path / "legacy" / "run_state.json"))
    (tmp_path / "legacy").mkdir()
    (tmp_path / "legacy" / "run_state.json").write_text('{"cycle_id": 12}')
    with pytest.raises(RuntimeError, match="Unsafe state"):
        demo.DemoHarness(resume=True)._load_state()
