from datetime import datetime, timedelta, timezone

import pytest

from core.decision_domain import DecisionJournal, DecisionOutcome, DecisionRecord


T = datetime(2026, 9, 29, 1, tzinfo=timezone.utc)


def test_checkpoint_and_outcome_commit_or_rollback_together(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    journal.record(DecisionRecord("d1", "e1", None, T, T, "paper_long", ("no_action",),
                                  (), (), None, "up", "down", (), ()))
    journal.commit_paper_state({"version": 1, "positions": ["open"]})
    valid = DecisionOutcome("d1", "close:d1", T + timedelta(hours=1), ("closed",))
    missing = DecisionOutcome("d2", "close:d2", T + timedelta(hours=1), ("closed",))
    with pytest.raises(ValueError, match="no recorded decision"):
        journal.commit_paper_state({"version": 2, "positions": []}, (valid, missing))
    assert journal.load_paper_state()["version"] == 1
    assert journal.history("d1")[1] == []
    journal.commit_paper_state({"version": 2, "positions": []}, (valid,))
    assert journal.load_paper_state()["version"] == 2
    assert len(journal.history("d1")[1]) == 1


def test_startup_marks_only_uncommitted_paper_plans(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    for did in ("opened", "lost"):
        journal.record(DecisionRecord(did, "event", None, T, T, "paper_long", (),
                                      (), (), None, "up", "down", (), ()))
    assert journal.reconcile_uncommitted_paper_decisions({"opened"}) == 1
    assert journal.reconcile_uncommitted_paper_decisions({"opened"}) == 0
    assert journal.history("opened")[1] == []
    assert journal.history("lost")[1][0]["facts"] == ["paper_transition_not_committed"]
