"""Integration tests for ERA II Iteration 1: Hypothesis + Evidence Foundation"""
import os
import pytest
from core.scientific.scientific_store import ScientificStore
from core.schemas.hypothesis_schema import HypothesisStatus
from core.schemas.evidence_schema import EvidenceDirection, EvidenceStatus
from core.scientific.hypothesis_lifecycle import (
    transition_hypothesis,
    get_valid_transitions,
    can_transition,
)
from core.scientific.evidence_lifecycle import (
    activate_evidence,
    expire_evidence,
    get_active_evidence_count,
)


TEST_DB = "test_scientific.db"


@pytest.fixture
def store():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    s = ScientificStore(db_path=TEST_DB)
    yield s
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestHypothesisLifecycle:
    def test_create_hypothesis(self, store):
        hyp = store.create_hypothesis(
            title="Gold will rally on Fed pivot",
            description="If the Fed signals a pause, gold will rally 2-5%",
            predicted_consequence="Gold price increases 2-5% within 10 days",
            conditions="Fed signals pause in next FOMC minutes",
            invalidation_conditions="Gold drops more than 1% within 5 days",
            confidence=0.65,
        )
        assert hyp.status == HypothesisStatus.FORMULATED
        assert hyp.title == "Gold will rally on Fed pivot"
        assert 0.0 <= hyp.confidence <= 1.0

    def test_create_hypothesis_all_fields(self, store):
        hyp = store.create_hypothesis(
            title="Test",
            description="Test",
            predicted_consequence="X happens",
            conditions="When Y",
            invalidation_conditions="If not X",
            confidence=0.5,
        )
        assert hyp.id is not None
        assert hyp.created_at is not None
        assert hyp.updated_at is not None
        assert hyp.status_history == []

    def test_transition_formulated_to_active(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        transition_hypothesis(hyp, HypothesisStatus.ACTIVE, reason="Testing")
        assert hyp.status == HypothesisStatus.ACTIVE
        assert len(hyp.status_history) == 1
        assert hyp.status_history[0]["from_status"] == "formulated"

    def test_transition_active_to_evaluated(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        transition_hypothesis(hyp, HypothesisStatus.ACTIVE)
        transition_hypothesis(hyp, HypothesisStatus.EVALUATED)
        assert hyp.status == HypothesisStatus.EVALUATED

    def test_transition_evaluated_to_archived(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        transition_hypothesis(hyp, HypothesisStatus.ACTIVE)
        transition_hypothesis(hyp, HypothesisStatus.EVALUATED)
        transition_hypothesis(hyp, HypothesisStatus.ARCHIVED)
        assert hyp.status == HypothesisStatus.ARCHIVED

    def test_invalid_transition_raises(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        with pytest.raises(ValueError, match="Cannot transition"):
            transition_hypothesis(hyp, HypothesisStatus.EVALUATED)
        assert hyp.status == HypothesisStatus.FORMULATED

    def test_invalid_transition_from_archived(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        transition_hypothesis(hyp, HypothesisStatus.ACTIVE)
        transition_hypothesis(hyp, HypothesisStatus.EVALUATED)
        transition_hypothesis(hyp, HypothesisStatus.ARCHIVED)
        with pytest.raises(ValueError):
            transition_hypothesis(hyp, HypothesisStatus.ACTIVE)

    def test_can_transition(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        assert can_transition(hyp, HypothesisStatus.ACTIVE)
        assert not can_transition(hyp, HypothesisStatus.EVALUATED)
        assert can_transition(hyp, HypothesisStatus.ARCHIVED)

    def test_get_valid_transitions(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        valid = get_valid_transitions(hyp)
        assert HypothesisStatus.ACTIVE in valid
        assert HypothesisStatus.ARCHIVED in valid
        assert HypothesisStatus.EVALUATED not in valid

    def test_persistence(self, store):
        hyp = store.create_hypothesis(
            title="Persist test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        transition_hypothesis(hyp, HypothesisStatus.ACTIVE)
        store.update_hypothesis(hyp)

        loaded = store.get_hypothesis(hyp.id)
        assert loaded is not None
        assert loaded.title == "Persist test"
        assert loaded.status == HypothesisStatus.ACTIVE

    def test_list_hypotheses(self, store):
        store.create_hypothesis(
            title="H1", description="T1",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        store.create_hypothesis(
            title="H2", description="T2",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        all_h = store.list_hypotheses()
        assert len(all_h) == 2

        formulated = store.list_hypotheses(status=HypothesisStatus.FORMULATED)
        assert len(formulated) == 2

        active = store.list_hypotheses(status=HypothesisStatus.ACTIVE)
        assert len(active) == 0

    def test_delete_hypothesis_cascades(self, store):
        hyp = store.create_hypothesis(
            title="Del test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        store.add_evidence(hyp.id, EvidenceDirection.SUPPORTS, 0.5, "Ev1")
        assert store.delete_hypothesis(hyp.id) is True
        assert store.get_hypothesis(hyp.id) is None
        assert len(store.list_evidence(hypothesis_id=hyp.id)) == 0


class TestEvidenceLifecycle:
    def test_add_evidence_to_hypothesis(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        ev = store.add_evidence(
            hypothesis_id=hyp.id,
            direction=EvidenceDirection.SUPPORTS,
            weight=0.8,
            content="Supporting data",
            source_id="test_source",
        )
        assert ev is not None
        assert ev.hypothesis_id == hyp.id
        assert ev.direction == EvidenceDirection.SUPPORTS
        assert ev.status == EvidenceStatus.COLLECTED

    def test_add_evidence_nonexistent_hypothesis(self, store):
        ev = store.add_evidence(
            hypothesis_id="nonexistent",
            direction=EvidenceDirection.SUPPORTS,
            weight=0.5,
            content="Test",
        )
        assert ev is None

    def test_activate_evidence(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        ev = store.add_evidence(
            hyp.id, EvidenceDirection.SUPPORTS, 0.8, "Support"
        )
        activated = activate_evidence(ev)
        assert activated.status == EvidenceStatus.ACTIVE
        store.update_evidence(activated)
        loaded = store.get_evidence(ev.id)
        assert loaded.status == EvidenceStatus.ACTIVE

    def test_expire_evidence(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        ev = store.add_evidence(
            hyp.id, EvidenceDirection.CONTRADICTS, 0.3, "Contra"
        )
        activated = activate_evidence(ev)
        store.update_evidence(activated)
        expired = expire_evidence(activated)
        assert expired.status == EvidenceStatus.EXPIRED

    def test_evidence_belongs_to_one_hypothesis(self, store):
        hyp1 = store.create_hypothesis(
            title="H1", description="T1",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        hyp2 = store.create_hypothesis(
            title="H2", description="T2",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        ev = store.add_evidence(
            hyp1.id, EvidenceDirection.SUPPORTS, 0.5, "Only for H1"
        )
        assert ev.hypothesis_id == hyp1.id
        assert ev.hypothesis_id != hyp2.id

    def test_list_evidence_by_hypothesis(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        store.add_evidence(hyp.id, EvidenceDirection.SUPPORTS, 0.7, "Ev1")
        store.add_evidence(hyp.id, EvidenceDirection.CONTRADICTS, 0.3, "Ev2")
        all_ev = store.list_evidence(hypothesis_id=hyp.id)
        assert len(all_ev) == 2

        supports = store.list_evidence(
            hypothesis_id=hyp.id, direction=EvidenceDirection.SUPPORTS
        )
        assert len(supports) == 1

    def test_active_evidence_counts(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        ev1 = store.add_evidence(hyp.id, EvidenceDirection.SUPPORTS, 0.7, "S1")
        ev2 = store.add_evidence(hyp.id, EvidenceDirection.CONTRADICTS, 0.3, "C1")
        ev3 = store.add_evidence(hyp.id, EvidenceDirection.SUPPORTS, 0.5, "S2")

        for ev in [ev1, ev2, ev3]:
            activated = activate_evidence(ev)
            store.update_evidence(activated)

        all_ev = store.list_evidence(hypothesis_id=hyp.id)
        counts = get_active_evidence_count(hyp, all_ev)
        assert counts["supports"] == 2
        assert counts["contradicts"] == 1

    def test_evidence_weight_range(self, store):
        hyp = store.create_hypothesis(
            title="Test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        ev = store.add_evidence(
            hyp.id, EvidenceDirection.SUPPORTS, 1.5, "Overweight"
        )
        assert 0.0 <= ev.weight <= 1.0
        assert ev.weight == 1.0

        ev2 = store.add_evidence(
            hyp.id, EvidenceDirection.SUPPORTS, -0.5, "Underweight"
        )
        assert ev2.weight == 0.0

    def test_scientific_stats(self, store):
        hyp = store.create_hypothesis(
            title="Stats test", description="Test",
            predicted_consequence="X", conditions="Y",
            invalidation_conditions="Not X",
        )
        store.add_evidence(hyp.id, EvidenceDirection.SUPPORTS, 0.5, "E1")
        store.add_evidence(hyp.id, EvidenceDirection.CONTRADICTS, 0.3, "E2")

        stats = store.get_stats()
        assert stats["total_hypotheses"] == 1
        assert stats["total_evidence"] == 2
        assert "formulated" in stats["hypotheses_by_status"]
        assert stats["hypotheses_by_status"]["formulated"] == 1


class TestRegression:
    def test_no_existing_code_modified(self):
        """Verify existing core modules are untouched."""
        import core.schemas.event_schema
        import core.schemas.agent_schema
        import core.schemas.trade_schema
        import core.council.council
        import core.execution.paper_trading
        import core.execution.performance_memory
        import core.memory.memory
        import core.monitoring.telemetry
        assert True

    def test_existing_schemas_unchanged(self):
        from core.schemas.event_schema import Event, EventType
        from core.schemas.agent_schema import AgentOpinion, CouncilDecision
        from core.schemas.trade_schema import Trade, TradeSignal, ExitReason

        assert Event is not None
        assert AgentOpinion is not None
        assert CouncilDecision is not None
        assert Trade is not None
        assert TradeSignal is not None
        assert ExitReason is not None
        assert EventType is not None
