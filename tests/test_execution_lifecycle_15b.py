"""Sprint 15B certification tests for the Execution Lifecycle capability."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "core" / "execution_engine"


VALID_SIGNAL = {
    "execution_signal_id": "sig-cert-001",
    "approval_id": "approval-cert-001",
    "decision_id": "decision-cert-001",
    "intended_action": "CERTIFY_SIMULATED_INTENT",
    "created_at": "2026-06-29T00:00:00Z",
    "event_id": "event-cert-001",
    "opportunity_id": "opportunity-cert-001",
}

FORBIDDEN_IMPORT_ROOTS = {
    "core.collectors",
    "core.council",
    "core.database",
    "core.engines",
    "core.event_bus",
    "core.scientific",
    "core.cli",
    "core.integration",
    "core.execution",
}

FORBIDDEN_TEXT = (
    "TradingView",
    "broker_order",
    "Broker",
    "paper_trading",
    "scientific_store",
    "sqlite3",
)


def test_layer_1_architecture_integrity_execution_engine_remains_isolated():
    assert ENGINE_ROOT.is_dir()

    for path in ENGINE_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TEXT:
            assert token not in source, f"Forbidden token {token!r} found in {path}"

        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported_names = [node.module or ""]
            else:
                continue

            for imported in imported_names:
                assert imported not in FORBIDDEN_IMPORT_ROOTS
                assert not any(imported.startswith(root + ".") for root in FORBIDDEN_IMPORT_ROOTS)


def test_layer_1_ownership_boundaries_are_explicit():
    from core.execution_engine.engine import ExecutionEngine
    from core.execution_engine.schemas import ExecutionRequest, ExecutionResult

    assert ExecutionEngine.__name__ == "ExecutionEngine"
    assert is_dataclass(ExecutionRequest)
    assert is_dataclass(ExecutionResult)

    engine = ExecutionEngine()
    signal = dict(VALID_SIGNAL)
    request = engine.create_execution_request(signal)
    result = engine.create_execution_result(request)

    assert request.execution_signal_id == signal["execution_signal_id"]
    assert result.execution_signal_id == signal["execution_signal_id"]
    assert result.execution_request_id == request.execution_request_id

    with pytest.raises(FrozenInstanceError):
        request.requested_action = "MUTATED"
    with pytest.raises(FrozenInstanceError):
        result.result_state = "MUTATED"


def test_layer_2_capability_behaviour_is_deterministic_and_traceable():
    from core.execution_engine.config import ExecutionMode
    from core.execution_engine.engine import ExecutionEngine

    engine = ExecutionEngine()

    first = engine.execute(dict(VALID_SIGNAL))
    second = engine.execute(dict(VALID_SIGNAL))

    assert first == second
    assert first.result_state == "ACCEPTED"
    assert first.execution_result_id == "result:sig-cert-001"
    assert first.execution_signal_id == "sig-cert-001"
    assert first.execution_request_id == "request:sig-cert-001"
    assert first.execution_mode is ExecutionMode.SIMULATION
    assert first.created_at == VALID_SIGNAL["created_at"]
    assert first.error_code is None
    assert first.error_message is None
    assert first.upstream_trace == (
        "event_id:event-cert-001",
        "opportunity_id:opportunity-cert-001",
        "decision_id:decision-cert-001",
        "approval_id:approval-cert-001",
        "execution_signal_id:sig-cert-001",
        "execution_request_id:request:sig-cert-001",
    )


def test_layer_2_request_creation_preserves_approved_intent_without_side_effects():
    from core.execution_engine.config import ExecutionMode
    from core.execution_engine.engine import ExecutionEngine

    engine = ExecutionEngine()
    signal = dict(VALID_SIGNAL)
    request = engine.create_execution_request(signal)

    assert request.execution_request_id == "request:sig-cert-001"
    assert request.execution_signal_id == "sig-cert-001"
    assert request.requested_action == "CERTIFY_SIMULATED_INTENT"
    assert request.execution_mode is ExecutionMode.SIMULATION
    assert request.created_at == VALID_SIGNAL["created_at"]
    assert signal == VALID_SIGNAL


def test_layer_3_invalid_signal_is_rejected_deterministically_with_error_traceability():
    from core.execution_engine.engine import ExecutionEngine
    from core.execution_engine.exceptions import ExecutionSignalValidationError

    engine = ExecutionEngine()
    invalid_signal = dict(VALID_SIGNAL)
    invalid_signal["intended_action"] = ""

    first = engine.reject_execution_signal(invalid_signal)
    second = engine.reject_execution_signal(invalid_signal)

    assert first == second
    assert first.result_state == "REJECTED"
    assert first.execution_result_id == "rejected:sig-cert-001"
    assert first.execution_signal_id == "sig-cert-001"
    assert first.execution_request_id is None
    assert first.error_code == "INVALID_SIGNAL"
    assert first.error_message == "Missing required field: intended_action"
    assert first.upstream_trace == (
        "event_id:event-cert-001",
        "opportunity_id:opportunity-cert-001",
        "decision_id:decision-cert-001",
        "approval_id:approval-cert-001",
        "execution_signal_id:sig-cert-001",
    )

    with pytest.raises(ExecutionSignalValidationError) as excinfo:
        engine.create_execution_request(invalid_signal)
    assert excinfo.value.error_code == "INVALID_SIGNAL"
    assert excinfo.value.missing_fields == ("intended_action",)


def test_layer_3_missing_identifiers_are_rejected_without_generating_upstream_ids():
    from core.execution_engine.engine import ExecutionEngine

    engine = ExecutionEngine()
    malformed_signal = {
        "execution_signal_id": "sig-missing-ids",
        "intended_action": "CERTIFY_SIMULATED_INTENT",
        "created_at": "2026-06-29T00:00:00Z",
    }

    result = engine.reject_execution_signal(malformed_signal)

    assert result.result_state == "REJECTED"
    assert result.execution_result_id == "rejected:sig-missing-ids"
    assert result.execution_signal_id == "sig-missing-ids"
    assert result.execution_request_id is None
    assert result.error_code == "MISSING_IDENTIFIERS"
    assert result.error_message == "Missing required fields: approval_id, decision_id"
    assert result.upstream_trace == ("execution_signal_id:sig-missing-ids",)


def test_layer_3_malformed_input_is_rejected_deterministically():
    from core.execution_engine.engine import ExecutionEngine
    from core.execution_engine.exceptions import ExecutionSignalValidationError

    engine = ExecutionEngine()

    with pytest.raises(ExecutionSignalValidationError) as excinfo:
        engine.validate_execution_signal(None)

    assert excinfo.value.error_code == "MALFORMED_SIGNAL"
    assert excinfo.value.missing_fields == ()
    assert str(excinfo.value) == "ExecutionSignal must be a mapping or field-bearing object"
