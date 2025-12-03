"""Custom exception classes for JcQ."""


class JcqError(Exception):
    """Base exception for all JcQ errors."""

    pass


class ConfigurationError(JcqError):
    """Raised when configuration is invalid or missing."""

    pass


class DataError(JcqError):
    """Raised when data operations fail."""

    pass


class ModelError(JcqError):
    """Raised when model operations fail."""

    pass


class RiskError(JcqError):
    """Raised when risk constraints are violated."""

    pass


class ExecutionError(JcqError):
    """Raised when execution operations fail."""

    pass

