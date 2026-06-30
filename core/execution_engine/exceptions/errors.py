"""Custom exceptions owned by the internal Execution Engine."""


class ExecutionError(Exception):
    """Base exception for Execution Engine structural failures."""


class OrderError(ExecutionError):
    """Order-domain exception for Engine-owned order structures."""


class PortfolioError(ExecutionError):
    """Portfolio-domain exception for Engine-owned portfolio structures."""


class PositionError(ExecutionError):
    """Position-domain exception for Engine-owned position structures."""


class LedgerError(ExecutionError):
    """Ledger-domain exception for Engine-owned ledger structures."""


class ConfigurationError(ExecutionError):
    """Configuration-domain exception for Engine-owned settings."""


class ExecutionSignalValidationError(ExecutionError):
    """Validation failure for an incoming canonical ExecutionSignal."""

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
