"""
Domain errors raised by ARWA services.

The API layer maps these to HTTP responses in one place (backend/main.py), so
services never need to know about HTTP and users never see raw database errors.
"""


class ArwaError(Exception):
    """Base class for expected, user-facing errors."""

    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(ArwaError):
    """The record does not exist or does not belong to the current user."""

    status_code = 404


class ConflictError(ArwaError):
    """The request conflicts with existing data."""

    status_code = 409


class DataValidationError(ArwaError):
    """The database rejected the values (constraint violation)."""

    status_code = 422


class RateLimitError(ArwaError):
    """Too many requests in a short window."""

    status_code = 429


class ServiceUnavailableError(ArwaError):
    """A required backing service (database, AI) is not configured or reachable."""

    status_code = 503
