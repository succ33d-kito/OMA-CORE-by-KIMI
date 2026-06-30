"""Outcome Domain public interface for OUTCOME.COLLECTOR."""

from core.outcome_domain.collector import OutcomeCollector
from core.outcome_domain.errors import OutcomeValidationError
from core.outcome_domain.outcome import Outcome

__all__ = ["Outcome", "OutcomeCollector", "OutcomeValidationError"]
