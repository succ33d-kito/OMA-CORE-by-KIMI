from datetime import datetime, timedelta, timezone

import pytest

from core.decision_domain import DecisionJournal, DecisionOutcome, DecisionRecord


T = datetime(2026, 9, 29, 12, tzinfo=timezone.utc)


def decision(**changes):
    values = dict(decision_id="d1", event_id="event1", hypothesis_id=None,
                  decided_at=T, available_at=T - timedelta(minutes=1),
                  action="WATCH", alternative_actions=("NO_ACTION",),
                  evidence_ids=(), source_ids=("feed1",), market_state_id=None,
                  expected_outcome="price moves up within 1h",
                  invalidation_condition="price falls 2%", risk_constraints=("paper only",),
                  missing_information=("order flow",))
    values.update(changes)
    return DecisionRecord(**values)


def test_ex_ante_information_and_append_only_history(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    d = decision()
    journal.record(d)
    journal.record(d)
    with pytest.raises(ValueError):
        journal.record(decision(action="BUY"))
    observation = DecisionOutcome("d1", "o1", T + timedelta(hours=1), ("price rose 1%",))
    journal.observe(observation)
    journal.observe(observation)
    frozen, outcomes = journal.history("d1")
    assert frozen["missing_information"] == ["order flow"]
    assert frozen["action"] == "WATCH"
    assert outcomes == [observation.to_dict() | {"facts": ["price rose 1%"]}]


def test_temporal_guards_and_foreign_key(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    with pytest.raises(ValueError):
        decision(available_at=T + timedelta(seconds=1))
    with pytest.raises(ValueError):
        decision(decided_at=T.replace(tzinfo=None))
    with pytest.raises(ValueError):
        journal.observe(DecisionOutcome("missing", "o1", T, ("fact",)))
    journal.record(decision())
    with pytest.raises(ValueError):
        journal.observe(DecisionOutcome("d1", "o1", T - timedelta(seconds=1), ("fact",)))
