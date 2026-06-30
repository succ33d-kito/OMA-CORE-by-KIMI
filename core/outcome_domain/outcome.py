"""Canonical Outcome object owned by the Outcome Collector."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Outcome:
    """Immutable factual Outcome produced from a certified ExecutionResult."""

    outcome_id: str
    execution_result_id: str
    execution_signal_id: str
    execution_request_id: str
    execution_order_id: str
    decision_id: str
    approval_id: str
    ledger_record_ids: tuple[str, ...]
    position_ids: tuple[str, ...]
    portfolio_snapshot_id: str | None
    result_state: str
    result_facts: tuple[str, ...]
    timestamps: tuple[str, ...]
    trace_lineage: tuple[str, ...]
    missing_identifiers: tuple[str, ...]
    lifecycle_state: str
    publication_ready: bool
    creator: str = "Outcome Collector"
    owner: str = "Outcome Collector"
    domain: str = "Outcome Domain"
