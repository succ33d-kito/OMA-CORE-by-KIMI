"""Sprint 15E certification tests for OUTCOME.COLLECTOR."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
OUTCOME_DOMAIN = ROOT / "core" / "outcome_domain"


FORBIDDEN_IMPORT_PREFIXES = (
    "core.collectors",
    "core.council",
    "core.database",
    "core.engines",
    "core.event_bus",
    "core.integration",
    "core.scientific",
    "core.cli",
    "core.execution.",
)


def _certified_execution_result():
    from core.execution_engine.config import ExecutionMode
    from core.execution_engine.schemas import ExecutionResult

    return ExecutionResult(
        execution_result_id="result:sig-15e-001",
        execution_signal_id="sig-15e-001",
        execution_request_id="request:sig-15e-001",
        result_state="FILLED",
        created_at="2026-06-30T02:00:00Z",
        ledger_reference="ledger:order:request:sig-15e-001:0003",
        execution_mode=ExecutionMode.SIMULATION,
        upstream_trace=(
            "event_id:event-15e-001",
            "opportunity_id:opp-15e-001",
            "evaluation_id:eval-15e-001",
            "decision_id:decision-15e-001",
            "approval_id:approval-15e-001",
            "execution_signal_id:sig-15e-001",
            "execution_request_id:request:sig-15e-001",
            "execution_order_id:order:request:sig-15e-001",
            "ledger_record_id:ledger:order:request:sig-15e-001:0001",
            "ledger_record_id:ledger:order:request:sig-15e-001:0002",
            "ledger_record_id:ledger:order:request:sig-15e-001:0003",
            "position_id:position:order:request:sig-15e-001",
            "portfolio_snapshot_id:portfolio:snapshot:3",
            "state_version:3",
        ),
    )


def _imported_modules(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return modules


def test_outcome_domain_package_exists_and_is_isolated():
    assert OUTCOME_DOMAIN.exists()
    assert (OUTCOME_DOMAIN / "__init__.py").exists()
    assert (OUTCOME_DOMAIN / "collector.py").exists()
    assert (OUTCOME_DOMAIN / "outcome.py").exists()
    assert (OUTCOME_DOMAIN / "errors.py").exists()

    violations = []
    for path in OUTCOME_DOMAIN.rglob("*.py"):
        for module in _imported_modules(path):
            if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                violations.append((str(path.relative_to(ROOT)), module))
    assert violations == []


def test_public_imports_expose_only_outcome_domain_objects():
    from core.outcome_domain import Outcome, OutcomeCollector, OutcomeValidationError

    assert Outcome.__name__ == "Outcome"
    assert OutcomeCollector.__name__ == "OutcomeCollector"
    assert OutcomeValidationError.__name__ == "OutcomeValidationError"


def test_outcome_is_frozen_canonical_object_with_unique_ownership():
    from core.outcome_domain import OutcomeCollector

    outcome = OutcomeCollector().collect(_certified_execution_result())

    assert is_dataclass(outcome)
    assert outcome.creator == "Outcome Collector"
    assert outcome.owner == "Outcome Collector"
    assert outcome.domain == "Outcome Domain"
    assert outcome.lifecycle_state == "OUTCOME_PUBLISHED"
    assert outcome.publication_ready is True
    with pytest.raises(FrozenInstanceError):
        outcome.result_state = "CHANGED"


def test_execution_result_transforms_to_deterministic_outcome():
    from core.outcome_domain import OutcomeCollector

    result = _certified_execution_result()
    collector = OutcomeCollector()

    first = collector.collect(result)
    second = collector.collect(result)

    assert first == second
    assert first.outcome_id == "outcome:result:sig-15e-001"
    assert first.execution_result_id == result.execution_result_id
    assert first.execution_signal_id == result.execution_signal_id
    assert first.execution_request_id == result.execution_request_id
    assert first.execution_order_id == "order:request:sig-15e-001"
    assert first.decision_id == "decision-15e-001"
    assert first.approval_id == "approval-15e-001"
    assert first.ledger_record_ids == (
        "ledger:order:request:sig-15e-001:0001",
        "ledger:order:request:sig-15e-001:0002",
        "ledger:order:request:sig-15e-001:0003",
    )
    assert first.position_ids == ("position:order:request:sig-15e-001",)
    assert first.portfolio_snapshot_id == "portfolio:snapshot:3"
    assert first.timestamps == ("created_at:2026-06-30T02:00:00Z",)


def test_outcome_preserves_complete_trace_lineage_without_regenerating_identifiers():
    from core.outcome_domain import OutcomeCollector

    result = _certified_execution_result()
    outcome = OutcomeCollector().collect(result)

    required_trace_tokens = {
        "event_id:event-15e-001",
        "opportunity_id:opp-15e-001",
        "evaluation_id:eval-15e-001",
        "decision_id:decision-15e-001",
        "approval_id:approval-15e-001",
        "execution_signal_id:sig-15e-001",
        "execution_request_id:request:sig-15e-001",
        "execution_order_id:order:request:sig-15e-001",
        "execution_result_id:result:sig-15e-001",
        "outcome_id:outcome:result:sig-15e-001",
    }

    assert required_trace_tokens.issubset(set(outcome.trace_lineage))
    assert outcome.missing_identifiers == ()


def test_outcome_contains_facts_not_interpretation_or_scientific_conclusions():
    from core.outcome_domain import OutcomeCollector

    outcome = OutcomeCollector().collect(_certified_execution_result())

    assert outcome.result_facts == (
        "result_state:FILLED",
        "execution_mode:SIMULATION",
        "ledger_reference:ledger:order:request:sig-15e-001:0003",
    )
    forbidden_attribute_names = {
        "evidence_id",
        "knowledge_id",
        "criterion_id",
        "hypothesis_verdict",
        "decision_quality",
        "profitability_score",
        "prediction",
    }
    assert forbidden_attribute_names.isdisjoint(set(outcome.__dataclass_fields__))


def test_completeness_verification_marks_publication_ready_only_after_required_trace():
    from core.outcome_domain import OutcomeCollector

    collector = OutcomeCollector()
    outcome = collector.collect(_certified_execution_result())

    assert collector.verify_completeness(outcome) is True
    assert outcome.publication_ready is True


@pytest.mark.parametrize(
    "field_name",
    (
        "execution_result_id",
        "execution_signal_id",
        "decision_id",
        "approval_id",
        "execution_request_id",
        "execution_order_id",
        "ledger_record_ids",
    ),
)
def test_missing_required_identifiers_are_rejected_deterministically(field_name):
    from core.outcome_domain import OutcomeCollector, OutcomeValidationError

    result = _certified_execution_result()
    data = {
        "execution_result_id": result.execution_result_id,
        "execution_signal_id": result.execution_signal_id,
        "execution_request_id": result.execution_request_id,
        "result_state": result.result_state,
        "created_at": result.created_at,
        "ledger_reference": result.ledger_reference,
        "execution_mode": result.execution_mode,
        "upstream_trace": tuple(
            token for token in result.upstream_trace if not token.startswith(f"{field_name.rstrip('s')}:")
        ),
    }
    if field_name in data:
        data[field_name] = ""
    if field_name == "ledger_record_ids":
        data["upstream_trace"] = tuple(
            token for token in data["upstream_trace"] if not token.startswith("ledger_record_id:")
        )

    with pytest.raises(OutcomeValidationError) as error:
        OutcomeCollector().collect(data)

    assert error.value.error_code == "MISSING_IDENTIFIERS"
    assert field_name in error.value.missing_fields


def test_inconsistent_lineage_is_rejected_without_outcome_generation():
    from core.outcome_domain import OutcomeCollector, OutcomeValidationError

    result = _certified_execution_result()
    data = {
        "execution_result_id": result.execution_result_id,
        "execution_signal_id": "sig-15e-CHANGED",
        "execution_request_id": result.execution_request_id,
        "result_state": result.result_state,
        "created_at": result.created_at,
        "ledger_reference": result.ledger_reference,
        "execution_mode": result.execution_mode,
        "upstream_trace": result.upstream_trace,
    }

    with pytest.raises(OutcomeValidationError) as error:
        OutcomeCollector().collect(data)

    assert error.value.error_code == "INCONSISTENT_LINEAGE"


def test_malformed_execution_result_is_rejected():
    from core.outcome_domain import OutcomeCollector, OutcomeValidationError

    with pytest.raises(OutcomeValidationError) as error:
        OutcomeCollector().collect(object())

    assert error.value.error_code == "MALFORMED_EXECUTION_RESULT"
