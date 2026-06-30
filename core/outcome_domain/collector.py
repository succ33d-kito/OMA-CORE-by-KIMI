"""Outcome Collector for deterministic ExecutionResult to Outcome transformation."""

from collections.abc import Mapping
from enum import Enum

from core.outcome_domain.errors import OutcomeValidationError
from core.outcome_domain.outcome import Outcome


class OutcomeCollector:
    """Creates canonical immutable Outcomes from certified ExecutionResults."""

    _DIRECT_FIELDS = (
        "execution_result_id",
        "execution_signal_id",
        "execution_request_id",
        "result_state",
        "created_at",
        "ledger_reference",
        "execution_mode",
        "error_code",
        "error_message",
        "upstream_trace",
    )
    _REQUIRED_FIELDS = (
        "execution_result_id",
        "execution_signal_id",
        "decision_id",
        "approval_id",
        "execution_request_id",
        "execution_order_id",
        "ledger_record_ids",
    )

    def collect(self, execution_result) -> Outcome:
        """Validate an ExecutionResult and create publication-ready Outcome."""

        values = self.validate_execution_result(execution_result)
        outcome_id = f"outcome:{values['execution_result_id']}"
        trace_lineage = self._trace_lineage(values, outcome_id)
        outcome = Outcome(
            outcome_id=outcome_id,
            execution_result_id=values["execution_result_id"],
            execution_signal_id=values["execution_signal_id"],
            execution_request_id=values["execution_request_id"],
            execution_order_id=values["execution_order_id"],
            decision_id=values["decision_id"],
            approval_id=values["approval_id"],
            ledger_record_ids=values["ledger_record_ids"],
            position_ids=values["position_ids"],
            portfolio_snapshot_id=values.get("portfolio_snapshot_id"),
            result_state=values["result_state"],
            result_facts=self._result_facts(values),
            timestamps=(f"created_at:{values['created_at']}",),
            trace_lineage=trace_lineage,
            missing_identifiers=(),
            lifecycle_state="OUTCOME_PUBLISHED",
            publication_ready=True,
        )
        self.verify_completeness(outcome)
        return outcome

    def validate_execution_result(self, execution_result) -> dict[str, object]:
        """Return normalized factual fields or raise a deterministic validation error."""

        raw = self._as_mapping(execution_result)
        trace = self._trace_index(raw.get("upstream_trace", ()))
        values = self._normalized_values(raw, trace)
        self._validate_required(values)
        self._validate_lineage(values, trace)
        return values

    def verify_completeness(self, outcome: Outcome) -> bool:
        """Verify that an Outcome is complete and ready for future bridge consumption."""

        missing = tuple(
            field for field in self._REQUIRED_FIELDS
            if not getattr(outcome, field)
        )
        if missing or not outcome.publication_ready:
            raise OutcomeValidationError(
                self._missing_message(missing or ("publication_ready",)),
                error_code="INCOMPLETE_OUTCOME",
                missing_fields=missing,
            )
        return True

    def _as_mapping(self, execution_result) -> dict[str, object]:
        if isinstance(execution_result, Mapping):
            return dict(execution_result)
        if execution_result is None:
            raise OutcomeValidationError(
                "ExecutionResult must be a mapping or field-bearing object",
                error_code="MALFORMED_EXECUTION_RESULT",
            )
        values = {
            field: getattr(execution_result, field)
            for field in self._DIRECT_FIELDS
            if hasattr(execution_result, field)
        }
        if not values:
            raise OutcomeValidationError(
                "ExecutionResult must be a mapping or field-bearing object",
                error_code="MALFORMED_EXECUTION_RESULT",
            )
        return values

    def _trace_index(self, upstream_trace) -> dict[str, tuple[str, ...]]:
        if upstream_trace is None:
            return {}
        if not isinstance(upstream_trace, tuple):
            try:
                upstream_trace = tuple(upstream_trace)
            except TypeError as exc:
                raise OutcomeValidationError(
                    "ExecutionResult upstream_trace must be iterable",
                    error_code="MALFORMED_EXECUTION_RESULT",
                ) from exc
        indexed: dict[str, list[str]] = {}
        for token in upstream_trace:
            if not isinstance(token, str) or ":" not in token:
                raise OutcomeValidationError(
                    "ExecutionResult upstream_trace contains malformed token",
                    error_code="MALFORMED_EXECUTION_RESULT",
                )
            key, value = token.split(":", 1)
            if value:
                indexed.setdefault(key, []).append(value)
        return {key: tuple(values) for key, values in indexed.items()}

    def _normalized_values(
        self,
        raw: Mapping[str, object],
        trace: Mapping[str, tuple[str, ...]],
    ) -> dict[str, object]:
        execution_result_id = self._string_value(raw.get("execution_result_id"))
        execution_signal_id = self._string_value(raw.get("execution_signal_id"))
        execution_request_id = self._string_value(raw.get("execution_request_id")) or self._first(trace, "execution_request_id")
        execution_mode = self._mode_value(raw.get("execution_mode"))
        values: dict[str, object] = {
            "execution_result_id": execution_result_id,
            "execution_signal_id": execution_signal_id,
            "execution_request_id": execution_request_id,
            "execution_order_id": self._first(trace, "execution_order_id"),
            "decision_id": self._first(trace, "decision_id"),
            "approval_id": self._first(trace, "approval_id"),
            "ledger_record_ids": self._ledger_record_ids(trace),
            "position_ids": self._position_ids(trace),
            "portfolio_snapshot_id": self._first(trace, "portfolio_snapshot_id") or None,
            "state_version": self._first(trace, "state_version") or None,
            "result_state": self._string_value(raw.get("result_state")),
            "created_at": self._string_value(raw.get("created_at")),
            "ledger_reference": self._string_value(raw.get("ledger_reference")),
            "execution_mode": execution_mode,
            "error_code": self._string_value(raw.get("error_code")),
            "error_message": self._string_value(raw.get("error_message")),
            "event_id": self._first(trace, "event_id"),
            "opportunity_id": self._first(trace, "opportunity_id"),
            "evaluation_id": self._first(trace, "evaluation_id"),
            "upstream_trace": tuple(raw.get("upstream_trace") or ()),
        }
        return values

    def _validate_required(self, values: Mapping[str, object]) -> None:
        missing = tuple(
            field for field in self._REQUIRED_FIELDS
            if not values.get(field)
        )
        if missing:
            raise OutcomeValidationError(
                self._missing_message(missing),
                error_code="MISSING_IDENTIFIERS",
                missing_fields=missing,
            )
        required_facts = tuple(
            field for field in ("result_state", "created_at", "ledger_reference", "execution_mode")
            if not values.get(field)
        )
        if required_facts:
            raise OutcomeValidationError(
                self._missing_message(required_facts),
                error_code="INCOMPLETE_EXECUTION_RESULT",
                missing_fields=required_facts,
            )

    def _validate_lineage(
        self,
        values: Mapping[str, object],
        trace: Mapping[str, tuple[str, ...]],
    ) -> None:
        mismatches = []
        for field in ("execution_signal_id", "execution_request_id"):
            traced = self._first(trace, field)
            if traced and values.get(field) != traced:
                mismatches.append(field)
        if mismatches:
            raise OutcomeValidationError(
                f"ExecutionResult lineage mismatch: {', '.join(mismatches)}",
                error_code="INCONSISTENT_LINEAGE",
            )

    def _trace_lineage(self, values: Mapping[str, object], outcome_id: str) -> tuple[str, ...]:
        upstream = tuple(values.get("upstream_trace") or ())
        additions = (
            f"execution_result_id:{values['execution_result_id']}",
            f"outcome_id:{outcome_id}",
        )
        return upstream + tuple(token for token in additions if token not in upstream)

    def _result_facts(self, values: Mapping[str, object]) -> tuple[str, ...]:
        facts = [
            f"result_state:{values['result_state']}",
            f"execution_mode:{values['execution_mode']}",
            f"ledger_reference:{values['ledger_reference']}",
        ]
        if values.get("error_code"):
            facts.append(f"error_code:{values['error_code']}")
        if values.get("error_message"):
            facts.append(f"error_message:{values['error_message']}")
        return tuple(facts)

    def _ledger_record_ids(self, trace: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
        return trace.get("ledger_record_id") or trace.get("execution_ledger_record_id") or ()

    def _position_ids(self, trace: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
        return trace.get("position_id") or trace.get("execution_position_id") or ()

    def _first(self, trace: Mapping[str, tuple[str, ...]], field: str) -> str:
        values = trace.get(field, ())
        return values[0] if values else ""

    def _string_value(self, value) -> str:
        if value is None:
            return ""
        return str(value)

    def _mode_value(self, value) -> str:
        if isinstance(value, Enum):
            return str(value.value)
        return self._string_value(value)

    def _missing_message(self, missing: tuple[str, ...]) -> str:
        if len(missing) == 1:
            return f"Missing required field: {missing[0]}"
        return f"Missing required fields: {', '.join(missing)}"
