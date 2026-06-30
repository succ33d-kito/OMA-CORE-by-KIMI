"""Outcome Domain validation errors."""


class OutcomeValidationError(Exception):
    """Validation failure while transforming ExecutionResult into Outcome."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str,
        missing_fields: tuple[str, ...] = (),
    ):
        super().__init__(message)
        self.error_code = error_code
        self.missing_fields = missing_fields
