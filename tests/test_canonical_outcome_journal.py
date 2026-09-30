from datetime import datetime, timezone

import pytest

from core.decision_domain import DecisionJournal, DecisionRecord
from core.decision_domain.paper_adapter import observe_canonical_outcome
from core.outcome_domain import OutcomeCollector
from tests.test_outcome_collector_15e import _certified_execution_result


def test_real_collector_outcome_linked_once_without_fabricating_lineage(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    t = datetime(2026, 6, 30, 1, tzinfo=timezone.utc)
    journal.record(DecisionRecord(
        decision_id="decision-15e-001", event_id="event-15e-001", hypothesis_id=None,
        decided_at=t, available_at=t, action="simulation", alternative_actions=("no_action",),
        evidence_ids=(), source_ids=(), market_state_id=None,
        expected_outcome="execution accepted", invalidation_condition="execution rejected",
        risk_constraints=("simulation only",), missing_information=("hypothesis_id",),
    ))
    published = OutcomeCollector().collect(_certified_execution_result())
    observe_canonical_outcome(journal, published)
    observe_canonical_outcome(journal, published)
    frozen, outcomes = journal.history("decision-15e-001")
    assert frozen["event_id"] == "event-15e-001"
    assert len(outcomes) == 1
    assert outcomes[0]["outcome_id"] == published.outcome_id
    assert "result_state:FILLED" in outcomes[0]["facts"]


def test_canonical_outcome_without_decision_is_rejected(tmp_path):
    journal = DecisionJournal(str(tmp_path / "decisions.db"))
    with pytest.raises(ValueError, match="no recorded decision"):
        observe_canonical_outcome(journal, OutcomeCollector().collect(_certified_execution_result()))
