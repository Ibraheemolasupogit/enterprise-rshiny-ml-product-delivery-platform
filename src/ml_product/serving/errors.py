"""Serving-specific errors."""


class ServiceNotReadyError(RuntimeError):
    """Raised when prediction is requested before an approved active model is available."""
