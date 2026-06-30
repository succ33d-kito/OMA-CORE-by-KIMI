"""Execution Engine lifecycle coordinator for Sprint 15B certification."""

from collections.abc import Mapping

from core.execution_engine.config import DEFAULT_EXECUTION_MODE
from core.execution_engine.exceptions import ExecutionSignalValidationError
from core.execution_engine.schemas import ExecutionRequest, ExecutionResult


class ExecutionEngine:
    """Owner of the minimal internal ExecutionSignal lifecycle."""

    _REQUIRED_SIGNAL_FIELDS = (
        "execution_signal_id",
        "approval_id",
        "decision_id",
        "intended_action",
        "created_at",
    )
    _TRACE_FIELDS = (
        "event_id",
        "opportunity_id",
        "decision_id",
        "approval_id",
        "execution_signal_id",
    )

    def validate_execution_signal(self, execution_signal):
        """Validate the incoming canonical ExecutionSignal representation."""

        signal = self._as_signal_mapping(execution_signal)
        missing = tuple(
            field for field in self._REQUIRED_SIGNAL_FIELDS if not signal.get(field)
        )
        if missing:
            error_code = "MISSING_IDENTIFIERS" if self._missing_only_identifiers(missing) else "INVALID_SIGNAL"
            raise ExecutionSignalValidationError(
                self._missing_message(missing),
                error_code=error_code,
                missing_fields=missing,
            )
        return signal

    def create_execution_request(self, execution_signal):
        """Create the Engine-owned ExecutionRequest from a valid signal."""

        signal = self.validate_execution_signal(execution_signal)
        execution_signal_id = signal["execution_signal_id"]
        execution_request_id = f"request:{execution_signal_id}"
        return ExecutionRequest(
            execution_request_id=execution_request_id,
            execution_signal_id=execution_signal_id,
            requested_action=signal["intended_action"],
            execution_mode=DEFAULT_EXECUTION_MODE,
            created_at=signal["created_at"],
            upstream_trace=self._trace_tuple(signal) + (f"execution_request_id:{execution_request_id}",),
        )

    def create_execution_result(self, execution_request):
        """Create the canonical ExecutionResult from an internal request."""

        execution_signal_id = execution_request.execution_signal_id
        execution_request_id = execution_request.execution_request_id
        return ExecutionResult(
            execution_result_id=f"result:{execution_signal_id}",
            execution_signal_id=execution_signal_id,
            execution_request_id=execution_request_id,
            result_state="ACCEPTED",
            created_at=execution_request.created_at,
            ledger_reference=f"not-applicable:sprint-15b:{execution_request_id}",
            execution_mode=execution_request.execution_mode,
            upstream_trace=execution_request.upstream_trace,
        )

    def execute(self, execution_signal):
        """Run the minimal deterministic Sprint 15B lifecycle."""

        request = self.create_execution_request(execution_signal)
        return self.create_execution_result(request)

    def reject_execution_signal(self, execution_signal):
        """Return a deterministic rejected ExecutionResult for invalid input."""

        try:
            self.validate_execution_signal(execution_signal)
        except ExecutionSignalValidationError as error:
            signal = self._safe_signal_mapping(execution_signal)
            execution_signal_id = signal.get("execution_signal_id") or "unidentified"
            created_at = signal.get("created_at") or "unavailable"
            return ExecutionResult(
                execution_result_id=f"rejected:{execution_signal_id}",
                execution_signal_id=execution_signal_id,
                execution_request_id=None,
                result_state="REJECTED",
                created_at=created_at,
                ledger_reference=f"not-applicable:sprint-15b:{execution_signal_id}",
                execution_mode=DEFAULT_EXECUTION_MODE,
                error_code=error.error_code,
                error_message=str(error),
                upstream_trace=self._trace_tuple(signal),
            )
        request = self.create_execution_request(execution_signal)
        return self.create_execution_result(request)

    def _as_signal_mapping(self, execution_signal):
        if isinstance(execution_signal, Mapping):
            return dict(execution_signal)
        if execution_signal is None:
            raise ExecutionSignalValidationError(
                "ExecutionSignal must be a mapping or field-bearing object",
                error_code="MALFORMED_SIGNAL",
            )
        values = {
            field: getattr(execution_signal, field)
            for field in self._REQUIRED_SIGNAL_FIELDS + self._TRACE_FIELDS
            if hasattr(execution_signal, field)
        }
        if not values:
            raise ExecutionSignalValidationError(
                "ExecutionSignal must be a mapping or field-bearing object",
                error_code="MALFORMED_SIGNAL",
            )
        return values

    def _safe_signal_mapping(self, execution_signal):
        if isinstance(execution_signal, Mapping):
            return dict(execution_signal)
        if execution_signal is None:
            return {}
        return {
            field: getattr(execution_signal, field)
            for field in self._REQUIRED_SIGNAL_FIELDS + self._TRACE_FIELDS
            if hasattr(execution_signal, field)
        }

    def _trace_tuple(self, signal):
        return tuple(
            f"{field}:{signal[field]}"
            for field in self._TRACE_FIELDS
            if signal.get(field)
        )

    def _missing_only_identifiers(self, missing):
        identifier_fields = {"execution_signal_id", "approval_id", "decision_id"}
        return set(missing).issubset(identifier_fields)

    def _missing_message(self, missing):
        if len(missing) == 1:
            return f"Missing required field: {missing[0]}"
        return f"Missing required fields: {', '.join(missing)}"
